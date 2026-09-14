"""Recovery integration against a disposable DB and preserved real publisher HTML.

The test archive and classifications are local test state, never collection
totals. No publisher requests or production database connections are permitted.
"""
from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
import os
import re
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse
import uuid

import pytest

from web_app.political_corpus import PoliticalCorpusService, match_targets, parse_date
from web_app.political_editorial_extraction import extract_for_publisher
from web_app import political_source_catalog as catalog
from pipeline.http_utils import canonicalize_url

DATABASE_URL = os.environ.get("POLITICAL_RECOVERY_TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="Dedicated disposable POLITICAL_RECOVERY_TEST_DATABASE_URL required")
ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/political_editorial_real"
CASES = json.loads((FIXTURES / "manifest.json").read_text())["cases"]
CASE_BY_ID = {case["id"]: case for case in CASES}
KEYS = json.loads((ROOT / "data/psd_rj_2026_profile.json").read_text())["target_keys"]
TARGETS = [row for row in json.loads((ROOT / "data/political_targets_v1.json").read_text())["targets"] if row["key"] in KEYS]
# Actual discovery URL from production task125485, preserved by the read-only
# audit. This fixture is only replayed locally; Google is never requested.
GOOGLE_EXAME = "https://news.google.com/rss/articles/CBMisgFBVV95cUxNVXg5cG9uRUlQNk9xcVJialBZbFc1S3B4ZVdueHlpVHlUUzc5VTdndWhQTnIxYXBwN0o4Q2RVNWhTXzhUck5GQkRJMzZvNlVSV2FISk9hMWZkMjVKSEZkbUdOY2VfYU1TdjBJcnVOU0NaTUtNRG8wM3RmSklzeG9ORl9kX2p5N29YamdzT2E5M2tHbHBJQnRsb29LSkRiamVmZUc2eXFpYk9kVFZxWlR5dUhR?oc=5"


class MemoryStore:
    enabled, prefix = True, "local-recovery-test"

    def __init__(self):
        self.objects = {}

    def upload_bytes(self, data, key, content_type):
        self.objects[key] = data
        return True

    def read_political_object(self, key):
        return self.objects[key]


@pytest.fixture
def corpus(monkeypatch):
    parsed = urlparse(DATABASE_URL)
    if parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.path != "/clipping_recovery_tests":
        pytest.fail("Recovery tests only accept the dedicated local clipping_recovery_tests database")
    service = PoliticalCorpusService(store=MemoryStore(), database_url=DATABASE_URL)
    service.ensure_schema()
    with service._connect() as conn:
        conn.execute("""TRUNCATE political_jobs,political_articles,political_stories,political_source_leases,
            political_domain_limits,political_workers,political_resolved_urls RESTART IDENTITY CASCADE""")
    monkeypatch.setattr(service, "fetch", lambda *a, **k: pytest.fail("Preserved real HTML must not trigger publisher/Google requests"))
    yield service
    service.close()


def case_data(ident):
    case = CASE_BY_ID[str(ident)]
    raw = gzip.decompress((FIXTURES / case["fixture"]).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == case["fixture_html_sha256"]
    extracted = extract_for_publisher(raw.decode(), case["url"])
    assert extracted and case["expected_extracted"]
    source = next(row for row in catalog.catalog_sources()
                  if row.get("domain", "").removeprefix("www.") == urlparse(case["url"]).hostname.removeprefix("www."))
    return case, raw.decode(), extracted, source


def seed_failure(corpus, ident, *, metadata_article=False, original_url=None,
                 original_targets=None, original_period=("2026-06-01", "2026-09-10"),
                 failure="body_missing", with_html=True, legacy_associations=False):
    case, html, extracted, source = case_data(ident)
    hits = match_targets(TARGETS, extracted["title"], extracted["full_text"])
    if legacy_associations:
        previous_rules = json.loads((ROOT / "data/targets.json").read_text())
        hits = match_targets([row for row in previous_rules if row["key"] in KEYS],
                             extracted["title"], extracted["full_text"])
    if metadata_article:
        assert hits, "A seeded association must really occur under the approved rules"
    observed = original_url or case["url"]
    original_source = "google_news" if original_url else source["key"]
    digest, html_key = corpus._store_html(html)
    metadata = {"html_hash": digest, "html_object_key": html_key} if with_html else {}
    payload = {"url": observed, "title": extracted["title"], "snippet": "", "source_key": original_source,
               "source_name": source["name"], "published_at": case["expected_publication"], "metadata": {}}
    cursor = {"resolved_url": case["url"], "empty_body_responses": 2} if original_url else {"empty_body_responses": 2}
    old_id, article_id = "historical-local-" + uuid.uuid4().hex, None
    with corpus._connect() as conn:
        conn.execute("""INSERT INTO political_jobs(id,kind,status,target_keys,target_snapshots,date_from,date_to,requested_by)
            VALUES(%s,'collect','completed_with_gaps',%s,%s::jsonb,%s,%s,'local-test-setup')""",
            (old_id, original_targets or KEYS, json.dumps(TARGETS), *original_period))
        task = conn.execute("""INSERT INTO political_tasks(job_id,kind,source_key,dedupe_key,payload,cursor,status,error_type)
            VALUES(%s,'fetch',%s,%s,%s::jsonb,%s::jsonb,'gap',%s) RETURNING id""",
            (old_id, original_source, observed, json.dumps(payload), json.dumps(cursor), failure)).fetchone()["id"]
        if metadata_article:
            article_id = conn.execute("""INSERT INTO political_articles(canonical_url,title,source_key,source_name,published_at,
                date_status,body_status,html_hash,html_object_key,metadata)
                VALUES(%s,%s,%s,%s,%s,'source_reported','metadata_only',%s,%s,'{"local_test_state":true}') RETURNING id""",
                (observed, extracted["title"], original_source, source["name"], case["expected_publication"], digest, html_key)).fetchone()["id"]
            for hit in hits:
                conn.execute("INSERT INTO political_mentions(article_id,target_key,target_name,keyword_matched) VALUES(%s,%s,%s,%s)",
                             (article_id, hit["target_key"], hit["target_name"], hit["keyword_matched"]))
            conn.execute("INSERT INTO political_url_aliases(url,article_id) VALUES(%s,%s)", (observed, article_id))
            conn.execute("""INSERT INTO political_classifications(article_id,target_key,payload,updated_by)
                VALUES(%s,%s,'{"annotation":"local human-classification preservation check"}','local-test-operator')""",
                (article_id, hits[0]["target_key"]))
        observation = conn.execute("""INSERT INTO political_observations(job_id,source_task_id,observed_url,source_key,title,metadata,article_id,disposition)
            VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s,'metadata_only') RETURNING id""",
            (old_id, task, observed, original_source, extracted["title"], json.dumps(metadata), article_id)).fetchone()["id"]
    return {"article_id": article_id, "observation_id": observation, "source": source,
            "case": case, "extracted": extracted, "hits": hits, "html_key": html_key}


def recover(corpus, source_keys, **updates):
    payload = {"target_keys": KEYS, "target_snapshots": TARGETS, "date_from": "2026-06-01",
               "date_to": "2026-09-10", "collection_profile": "psd_rj_2026", "kind": "recover",
               "source_keys": source_keys, **updates}
    return corpus.start_job(payload, started_by="local-test-operator", allowed_target_keys=KEYS)


def test_real_sitemap_cache_cursor_survives_service_restart_without_repeated_download(corpus, monkeypatch, tmp_path):
    from web_app import political_discovery
    from web_app import political_expanded_discovery as expanded
    import requests
    fixtures = ROOT / 'tests/fixtures/political_expanded'
    evidence = next(r for r in json.loads((fixtures / 'provenance.json').read_text()) if r['name'] == 'istoe_603')
    raw = gzip.decompress((fixtures / 'istoe_603.gz').read_bytes())
    assert hashlib.sha256(raw).hexdigest() == evidence['sha256']
    source = next(s for s in expanded.load_expanded_sources() if s['key'] == 'istoe')
    leaf = expanded.build_expanded_tasks(source, '2026-08-09', '2026-08-09', TARGETS)[0]
    leaf.update(url=evidence['url'], depth=1)
    monkeypatch.setattr(political_discovery, 'build_tasks', lambda *a, **kw: [leaf])
    monkeypatch.setenv('POLITICAL_PAGED_SITEMAP_CACHE_DIR', str(tmp_path))
    calls = []
    def fetch(url):
        calls.append(url)
        response = requests.Response();response.status_code = 200
        response._content = raw;response.url = url
        return response
    monkeypatch.setattr(corpus, 'fetch', fetch)
    job = recover(corpus, ['istoe'], kind='collect', date_from='2026-08-09', date_to='2026-08-09')
    first = corpus.claim_task('discovery', worker_id='local-before-restart')
    assert corpus.process_task(first)['status'] == 'continue'
    with corpus._connect() as c:
        cursor = c.execute('SELECT cursor FROM political_tasks WHERE id=%s', (first['id'],)).fetchone()['cursor']
    assert cursor['offset'] == 500 and cursor['response_cache']['sha256'] == evidence['sha256']
    restarted = PoliticalCorpusService(store=corpus.store, database_url=DATABASE_URL)
    monkeypatch.setattr(restarted, 'fetch', fetch)
    try:
        second = restarted.claim_task('discovery', worker_id='local-after-restart')
        assert second['id'] == first['id'] and second['cursor'] == cursor
        assert restarted.process_task(second)['status'] == 'continue'
        with restarted._connect() as c:
            row = c.execute('SELECT cursor FROM political_tasks WHERE id=%s', (first['id'],)).fetchone()
            assert row['cursor']['offset'] == 1000
            assert c.execute('SELECT COUNT(*) AS n FROM political_observations WHERE job_id=%s', (job['id'],)).fetchone()['n'] > 900
        assert len(calls) == 1
    finally:
        restarted.close()


def test_real_http_200_challenge_ends_as_access_gap_without_empty_body_retry(corpus, monkeypatch):
    import requests
    folder=ROOT/'tests/fixtures/political_expanded_editorial_real'
    case=next(c for c in json.loads((folder/'manifest.json').read_text())['cases'] if c['taskId']==232335)
    raw=gzip.decompress((folder/case['fixture']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==case['htmlHash']
    job=recover(corpus,['tv_zoom'])
    payload={'url':case['url'],'source_key':'tv_zoom','title':'','source_name':'TV Zoom'}
    with corpus._connect() as conn:
        discovery=conn.execute("UPDATE political_tasks SET status='complete' WHERE job_id=%s RETURNING id",(job['id'],)).fetchone()['id']
        corpus._insert_task(conn,job['id'],'fetch',payload)
        conn.execute("INSERT INTO political_observations(job_id,source_task_id,observed_url,source_key) VALUES(%s,%s,%s,'tv_zoom')",(job['id'],discovery,case['url']))
    response=requests.Response();response.status_code=200;response.url=case['url'];response._content=raw;response.encoding='utf-8'
    monkeypatch.setattr(corpus,'fetch',lambda *a,**k:response)
    task=corpus.claim_task('fetch',worker_id='real-challenge-test')
    result=corpus.process_task(task)
    assert result['status']=='gap' and result['errorType']=='publisher_access_challenge'
    with corpus._connect() as conn:
        saved=conn.execute('SELECT status,attempts,cursor FROM political_tasks WHERE id=%s',(task['id'],)).fetchone()
        evidence=conn.execute('SELECT metadata FROM political_observations WHERE job_id=%s',(job['id'],)).fetchone()['metadata']['access_failure']
    assert saved['attempts']==1 and 'empty_body_responses' not in saved['cursor']
    assert evidence['status']==200 and evidence['kind']=='challenge'
    assert evidence['html_hash']==case['htmlHash']


@pytest.mark.parametrize('last,expected',[('2026-08-09','outside_window'),('2026-09-10','duplicate')])
def test_rediscovered_undated_body_gets_real_date_without_replacing_text(corpus,monkeypatch,last,expected):
    import requests
    from web_app.political_discovery import extract_article
    folder=ROOT/'tests/fixtures/political_new_dates_real'
    case=next(c for c in json.loads((folder/'manifest.json').read_text()) if c['id']==16221)
    raw=gzip.decompress((folder/case['fixture']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==case['sha256']
    extracted=extract_article(raw.decode(),case['url'])
    hits=match_targets(TARGETS,extracted['title'],extracted['full_text']);assert hits
    digest,key=corpus._store_text(extracted['full_text'])
    source='noticias_de_belford_roxo'
    job=recover(corpus,[source],date_from='2026-08-09',date_to=last)
    payload={'url':case['url'],'title':extracted['title'],'source_key':source,'source_name':'Notícias de Belford Roxo'}
    with corpus._connect() as conn:
        article=corpus._persist_article(conn,payload,hits,published=None,date_status='unknown',
            body_chars=len(extracted['full_text']),digest=digest,object_key=key)
        conn.execute("INSERT INTO political_classifications(article_id,target_key,payload,updated_by) VALUES(%s,%s,'{\"keep\":true}','local-test-operator')",(article,hits[0]['target_key']))
        discovery=conn.execute("UPDATE political_tasks SET status='complete' WHERE job_id=%s RETURNING id",(job['id'],)).fetchone()['id']
        corpus._insert_task(conn,job['id'],'fetch',payload)
        conn.execute("INSERT INTO political_observations(job_id,source_task_id,observed_url,source_key) VALUES(%s,%s,%s,%s)",(job['id'],discovery,case['url'],source))
    response=requests.Response();response.status_code=200;response.url=case['url'];response._content=raw;response.encoding='utf-8'
    monkeypatch.setattr(corpus,'fetch',lambda *a,**k:response)
    task=corpus.claim_task('fetch',worker_id='real-date-test');corpus.process_task(task)
    with corpus._connect() as conn:
        saved=conn.execute('SELECT * FROM political_articles WHERE id=%s',(article,)).fetchone()
        outcome=conn.execute('SELECT result FROM political_tasks WHERE id=%s',(task['id'],)).fetchone()['result']
        classification=conn.execute('SELECT payload FROM political_classifications WHERE article_id=%s',(article,)).fetchone()['payload']
        assert conn.execute('SELECT COUNT(*) AS n FROM political_articles').fetchone()['n']==1
        assert conn.execute('SELECT COUNT(*) AS n FROM political_article_revisions WHERE article_id=%s',(article,)).fetchone()['n']==1
    assert saved['published_at']==parse_date(case['expected_date']) and saved['date_status']=='page_verified'
    assert saved['content_hash']==digest and saved['text_object_key']==key and classification=={'keep':True}
    assert outcome['disposition']==expected


def test_historical_selection_does_not_block_other_task_commits(corpus, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from contextlib import contextmanager
    from threading import Event
    item = seed_failure(corpus, "125485")
    job = recover(corpus, [item["source"]["key"]])
    task = corpus.claim_task("discovery", worker_id="local-selection-worker")
    entered, release = Event(), Event()
    original_connect = corpus._connect

    class ObservedConnection:
        def __init__(self, connection):
            self.connection = connection

        def execute(self, sql, *args, **kwargs):
            if sql.startswith("SELECT o.id,o.observed_url"):
                entered.set()
                assert release.wait(10), "The selection test was not released"
            return self.connection.execute(sql, *args, **kwargs)

    @contextmanager
    def observed_connect():
        with original_connect() as conn:
            yield ObservedConnection(conn)

    monkeypatch.setattr(corpus, "_connect", observed_connect)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(corpus._recover_discovery, task, item["source"])
        try:
            assert entered.wait(5)
            with original_connect() as conn:
                conn.execute("SET LOCAL lock_timeout='500ms'")
                assert conn.execute("SELECT id FROM political_jobs WHERE id=%s FOR UPDATE", (job["id"],)).fetchone()["id"] == job["id"]
        finally:
            release.set()
        result = pending.result(timeout=10)
    assert [row["url"].rstrip("/") for row in result["candidates"]] == [item["case"]["url"].rstrip("/")]


def drain(corpus):
    results = []
    for _ in range(250):
        task = corpus.claim_task("discovery", worker_id="local-recovery-discovery")
        if task is None:
            task = corpus.claim_task("fetch", worker_id="local-recovery-fetch")
        if task is None:
            break
        result = corpus.process_task(task)
        assert result.get("status") not in {"gap", "retryable", "failed"}, result
        results.append(result)
    else:
        pytest.fail("Recovery did not terminate within the finite test task bound")
    return results


def test_eighteen_real_historical_htmls_are_recovered_without_network(corpus):
    seeded = [seed_failure(corpus, case["id"]) for case in CASES if case["expected_extracted"]]
    assert len(seeded) == 18 and len(TARGETS) == 35
    job = recover(corpus, sorted({row["source"]["key"] for row in seeded}))
    drain(corpus)
    with corpus._connect() as conn:
        rows = conn.execute("SELECT * FROM political_articles ORDER BY id").fetchall()
        # The Wladimir Garotinho page is not an Anthony match under the existing
        # approved rule. Recovery must not broaden matching to reach a quota.
        assert len(rows) == 17
        assert conn.execute("SELECT COUNT(*) AS n FROM political_observations WHERE job_id=%s AND disposition='no_match'", (job["id"],)).fetchone()["n"] == 1
        assert conn.execute("SELECT fetch_attempted FROM political_jobs WHERE id=%s", (job["id"],)).fetchone()["fetch_attempted"] == 0
        assert conn.execute("SELECT COUNT(*) AS n FROM political_tasks WHERE kind='review'").fetchone()["n"] == 0
    by_url = {row["canonical_url"].rstrip("/"): row for row in rows}
    for expected in seeded:
        if not expected["hits"]:
            assert expected["case"]["id"] == "219363"
            assert expected["case"]["url"].rstrip("/") not in by_url
            continue
        row = by_url[expected["case"]["url"].rstrip("/")]
        assert row["published_at"] == parse_date(expected["case"]["expected_publication"])
        text = corpus._read_text(row["text_object_key"], row["content_hash"])
        assert text == expected["extracted"]["full_text"]
        assert row["metadata"]["body_origin"] == "historical_html"


def test_metadata_upgrade_preserves_classification_id_and_historical_observation(corpus):
    old = seed_failure(corpus, "125485", metadata_article=True, original_url=GOOGLE_EXAME)
    with corpus._connect() as conn:
        classification = dict(conn.execute("SELECT * FROM political_classifications").fetchone())
        observed = dict(conn.execute("SELECT * FROM political_observations WHERE id=%s", (old["observation_id"],)).fetchone())
    first = recover(corpus, [old["source"]["key"]])
    drain(corpus)
    with corpus._connect() as conn:
        articles = conn.execute("SELECT * FROM political_articles").fetchall()
        assert len(articles) == 1 and articles[0]["id"] == old["article_id"]
        assert articles[0]["canonical_url"].rstrip("/") == old["case"]["url"].rstrip("/")
        assert articles[0]["text_object_key"]
        assert dict(conn.execute("SELECT * FROM political_classifications").fetchone()) == classification
        assert dict(conn.execute("SELECT * FROM political_observations WHERE id=%s", (old["observation_id"],)).fetchone()) == observed
        assert conn.execute("SELECT article_id FROM political_url_aliases WHERE url=%s", (GOOGLE_EXAME,)).fetchone()["article_id"] == old["article_id"]
        mentions = conn.execute("SELECT COUNT(*) AS n FROM political_mentions").fetchone()["n"]
    recover(corpus, [old["source"]["key"]])
    drain(corpus)
    with corpus._connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM political_articles").fetchone()["n"] == 1
        assert conn.execute("SELECT COUNT(*) AS n FROM political_mentions").fetchone()["n"] == mentions
        assert dict(conn.execute("SELECT * FROM political_classifications").fetchone()) == classification


def test_recovery_selection_freezes_ceiling_source_scope_and_date_window(corpus):
    inside = seed_failure(corpus, "125485")
    seed_failure(corpus, "118257")  # Other publisher.
    seed_failure(corpus, "170568", original_period=("2026-07-01", "2026-07-31"))
    seed_failure(corpus, "218383", original_targets=["shakira"])
    job = recover(corpus, [inside["source"]["key"]], date_from="2026-06-01", date_to="2026-06-30")
    seed_failure(corpus, "218383")  # Created after the recovery's frozen ceiling.
    drain(corpus)
    with corpus._connect() as conn:
        rows = conn.execute("SELECT canonical_url FROM political_articles").fetchall()
        assert [row["canonical_url"].rstrip("/") for row in rows] == [inside["case"]["url"].rstrip("/")]
        row = conn.execute("SELECT metadata,target_snapshots FROM political_jobs WHERE id=%s", (job["id"],)).fetchone()
        assert len(row["target_snapshots"]) == 35
        assert row["metadata"]["source_keys"] == [inside["source"]["key"]]
        assert row["metadata"]["source_snapshots"][0]["domain"] == inside["source"]["domain"]


def test_source_permissions_and_idempotency_do_not_silently_broaden_work(corpus):
    source = case_data("125485")[3]["key"]
    with pytest.raises(ValueError, match="source_access_denied"):
        recover(corpus, [source], collection_profile="")
    with pytest.raises(ValueError, match="select_allowed_sources"):
        recover(corpus, [])
    first = recover(corpus, [source], request_key="same-approved-recovery")
    assert recover(corpus, [source], request_key="same-approved-recovery")["id"] == first["id"]
    with pytest.raises(ValueError, match="request_key_conflict"):
        recover(corpus, [case_data("118257")[3]["key"]], request_key="same-approved-recovery")
    with pytest.raises(ValueError, match="request_key_conflict"):
        recover(corpus, [source], recovery_gap_types=["http_403"], request_key="same-approved-recovery")
    with pytest.raises(ValueError, match="request_key_conflict"):
        recover(corpus, [source], kind="collect", request_key="same-approved-recovery")


def test_source_snapshot_remains_usable_when_catalog_is_reloaded(corpus, monkeypatch):
    item = seed_failure(corpus, "125485")
    job = recover(corpus, [item["source"]["key"]])
    monkeypatch.setattr(catalog, "catalog_sources", lambda: [])
    drain(corpus)
    with corpus._connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM political_articles").fetchone()["n"] == 1
        assert conn.execute("SELECT metadata FROM political_jobs WHERE id=%s", (job["id"],)).fetchone()["metadata"]["source_snapshots"][0]["domain"] == item["source"]["domain"]


def test_recovery_preserves_preexisting_associations_even_when_current_match_is_empty(corpus):
    # The earlier checked-in matcher associates this real page. This test does
    # not reassess that classification; recovery must preserve established work.
    item = seed_failure(corpus, "219363", metadata_article=True, legacy_associations=True)
    assert not match_targets(TARGETS, item["extracted"]["title"], item["extracted"]["full_text"])
    with corpus._connect() as conn:
        mentions = conn.execute("SELECT * FROM political_mentions ORDER BY target_key").fetchall()
        classifications = conn.execute("SELECT * FROM political_classifications").fetchall()
    recover(corpus, [item["source"]["key"]])
    drain(corpus)
    with corpus._connect() as conn:
        article = conn.execute("SELECT * FROM political_articles WHERE id=%s", (item["article_id"],)).fetchone()
        assert article["text_object_key"] and article["metadata"]["body_origin"] == "historical_html"
        assert conn.execute("SELECT * FROM political_mentions ORDER BY target_key").fetchall() == mentions
        assert conn.execute("SELECT * FROM political_classifications").fetchall() == classifications


def test_object_failure_does_not_overwrite_metadata_and_healthy_source_can_finish(corpus, monkeypatch):
    item = seed_failure(corpus, "125485", metadata_article=True)
    healthy = seed_failure(corpus, "118257")
    job = recover(corpus, [item["source"]["key"], healthy["source"]["key"]])
    failed_hash = hashlib.sha256(item["extracted"]["full_text"].encode()).hexdigest()
    original = corpus.store.upload_bytes
    failed = []
    def upload(data, key, content_type):
        if failed_hash in key and not failed:
            failed.append(key)
            return False
        return original(data, key, content_type)
    monkeypatch.setattr(corpus.store, "upload_bytes", upload)
    results = []
    for _ in range(10):
        task = corpus.claim_task("discovery", worker_id="recovery-storage-discovery") or corpus.claim_task("fetch", worker_id="recovery-storage-fetch")
        if task is None:
            break
        results.append(corpus.process_task(task))
    assert failed and any(result["status"] == "retryable" for result in results)
    assert any(result["status"] == "saved" for result in results)
    with corpus._connect() as conn:
        existing = conn.execute("SELECT * FROM political_articles WHERE id=%s", (item["article_id"],)).fetchone()
        assert existing["body_status"] == "metadata_only" and existing["text_object_key"] == ""
        assert conn.execute("SELECT COUNT(*) AS n FROM political_classifications").fetchone()["n"] == 1
        conn.execute("UPDATE political_tasks SET next_attempt_at=NOW() WHERE job_id=%s AND status='retryable'", (job["id"],))
    drain(corpus)
    with corpus._connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM political_articles WHERE text_object_key<>''").fetchone()["n"] == 2
        assert conn.execute("SELECT COUNT(*) AS n FROM political_classifications").fetchone()["n"] == 1


def test_route_replaces_forged_profile_and_matching_snapshots(monkeypatch):
    from web_app import political_routes as routes
    payload = {"target_keys": KEYS, "kind": "recover", "collection_profile": "another_client",
               "target_snapshots": [{"key": "unapproved", "keywords": ["anything"]}]}
    captured = {}
    async def body(request):
        return payload
    def start(value, **kwargs):
        captured.update(value)
        return {"id": "route-contract-only"}
    monkeypatch.setattr(routes, "access", lambda *a, **k: ({"profile": "psd_rj_2026", "sub": "operator"}, KEYS, TARGETS))
    monkeypatch.setattr(routes, "json_body", body)
    monkeypatch.setattr(routes.political_corpus, "start_job", start)
    asyncio.run(routes.start(SimpleNamespace(query_params={})))
    assert captured["collection_profile"] == "psd_rj_2026"
    assert {row["key"]: row for row in captured["target_snapshots"]} == {row["key"]: row for row in TARGETS}
    assert len(captured["target_snapshots"]) == 35


def seed_real_partial(corpus, ident="125485", *, extent="partial", original_url=None):
    """Local partial state contains a literal prefix of real editorial text."""
    item = seed_failure(corpus, ident, metadata_article=True, original_url=original_url)
    full = item["extracted"]["full_text"]
    partial = full[:len(full) // 2]
    digest, key = corpus._store_text(partial)
    with corpus._connect() as conn:
        conn.execute("""UPDATE political_articles SET canonical_url=%s,body_status='body_extracted',body_chars=%s,
            content_hash=%s,text_object_key=%s,metadata=metadata || %s::jsonb WHERE id=%s""",
            (original_url or canonicalize_url(item["case"]["url"]), len(partial), digest, key, json.dumps({"text_extent": extent}), item["article_id"]))
        classification = dict(conn.execute("SELECT * FROM political_classifications WHERE article_id=%s", (item["article_id"],)).fetchone())
    return {**item, "partial": partial, "previous_hash": digest, "previous_key": key, "classification": classification}


@pytest.mark.parametrize("original_url", [None, GOOGLE_EXAME], ids=["publisher", "historical-google-wrapper"])
def test_explicit_partial_recovery_reextracts_real_html_and_preserves_classification(corpus, original_url):
    item = seed_real_partial(corpus, original_url=original_url)
    unknown = seed_real_partial(corpus, "170568", extent="unknown")
    available = seed_real_partial(corpus, "218383", extent="available")
    job = recover(corpus, [item["source"]["key"]], recovery_gap_types=["partial_text"])
    drain(corpus)
    with corpus._connect() as conn:
        row = conn.execute("SELECT * FROM political_articles WHERE id=%s", (item["article_id"],)).fetchone()
        assert row["id"] == item["article_id"] and row["metadata"]["text_extent"] == "available"
        assert corpus._read_text(row["text_object_key"], row["content_hash"]) == item["extracted"]["full_text"]
        assert corpus._read_text(item["previous_key"], item["previous_hash"]) == item["partial"]
        assert dict(conn.execute("SELECT * FROM political_classifications WHERE article_id=%s", (row["id"],)).fetchone()) == item["classification"]
        revisions = conn.execute("SELECT previous FROM political_article_revisions WHERE article_id=%s", (row["id"],)).fetchall()
        assert any(r["previous"]["content_hash"] == item["previous_hash"] for r in revisions)
        tasks = conn.execute("SELECT payload,result FROM political_tasks WHERE job_id=%s AND kind='fetch'", (job["id"],)).fetchall()
        assert len(tasks) == 1 and tasks[0]["payload"]["recover_partial_text"] is True
        assert tasks[0]["result"]["bodyEnriched"] and tasks[0]["result"]["partialTextRecovered"]
        assert conn.execute("SELECT content_hash FROM political_articles WHERE id=%s", (unknown["article_id"],)).fetchone()["content_hash"] == unknown["previous_hash"]
        assert conn.execute("SELECT content_hash FROM political_articles WHERE id=%s", (available["article_id"],)).fetchone()["content_hash"] == available["previous_hash"]
        assert corpus._metrics(conn, job["id"])["articlesEnriched"] == 1
        assert corpus._metrics(conn, job["id"])["articlesInserted"] == 0


def test_partial_recovery_rejects_shorter_real_excerpt_and_keeps_original(corpus, monkeypatch):
    item = seed_real_partial(corpus)
    _, html, _, _ = case_data("125485")
    # Keep the real response's metadata and its exact first editorial paragraph;
    # emulate a shorter public response without inventing any article sentence.
    body_start = re.search(r'<div[^>]+id="news-body"[^>]*>', html).end()
    first_end = html.index('</p>', body_start) + len('</p>')
    shortened = html[:first_end] + '</div></body></html>'
    assert 0 < len(extract_for_publisher(shortened, item["case"]["url"])["full_text"]) < len(item["partial"])
    digest, key = corpus._store_html(shortened)
    with corpus._connect() as conn:
        conn.execute("UPDATE political_observations SET metadata=%s::jsonb WHERE id=%s",
            (json.dumps({"html_hash": digest, "html_object_key": key}), item["observation_id"]))
    requests_seen = []
    def public_response(url, **kwargs):
        requests_seen.append(url)
        return SimpleNamespace(url=url, text=shortened, status_code=200, headers={})
    monkeypatch.setattr(corpus, "fetch", public_response)
    job = recover(corpus, [item["source"]["key"]], recovery_gap_types=["partial_text"])
    discovery = corpus.claim_task("discovery", worker_id="local-discovery")
    corpus.process_task(discovery)
    first = corpus.claim_task("fetch", worker_id="local-partial-worker")
    result = corpus.process_task(first)
    assert result["status"] == "retryable" and result["errorType"] == "partial_text_not_improved"
    with corpus._connect() as conn:
        conn.execute("UPDATE political_tasks SET next_attempt_at=NOW() WHERE id=%s", (first["id"],))
    second = corpus.claim_task("fetch", worker_id="local-partial-worker")
    result = corpus.process_task(second)
    assert result["status"] == "gap" and result["errorType"] == "partial_text_not_improved"
    assert len(requests_seen) == 1
    with corpus._connect() as conn:
        row = conn.execute("SELECT * FROM political_articles WHERE id=%s", (item["article_id"],)).fetchone()
        assert row["content_hash"] == item["previous_hash"] and row["text_object_key"] == item["previous_key"]
        assert row["metadata"]["text_extent"] == "partial"
        assert dict(conn.execute("SELECT * FROM political_classifications WHERE article_id=%s", (row["id"],)).fetchone()) == item["classification"]
        assert corpus._metrics(conn, job["id"])["articlesEnriched"] == 0
        assert corpus._metrics(conn, job["id"])["unresolvedGaps"] == 1


def test_partial_recovery_storage_failure_keeps_existing_text_and_classification(corpus, monkeypatch):
    item = seed_real_partial(corpus)
    expected_hash = hashlib.sha256(item["extracted"]["full_text"].encode()).hexdigest()
    original_upload = corpus.store.upload_bytes
    monkeypatch.setattr(corpus.store, "upload_bytes", lambda raw, key, mime: False if expected_hash in key else original_upload(raw, key, mime))
    job = recover(corpus, [item["source"]["key"]], recovery_gap_types=["partial_text"])
    corpus.process_task(corpus.claim_task("discovery", worker_id="local-discovery"))
    result = corpus.process_task(corpus.claim_task("fetch", worker_id="local-partial-worker"))
    assert result["status"] == "retryable"
    with corpus._connect() as conn:
        row = conn.execute("SELECT * FROM political_articles WHERE id=%s", (item["article_id"],)).fetchone()
        assert row["content_hash"] == item["previous_hash"] and row["text_object_key"] == item["previous_key"]
        assert corpus._read_text(row["text_object_key"], row["content_hash"]) == item["partial"]
        assert dict(conn.execute("SELECT * FROM political_classifications WHERE article_id=%s", (row["id"],)).fetchone()) == item["classification"]
        assert corpus._metrics(conn, job["id"])["articlesEnriched"] == 0


def test_longer_restricted_excerpt_is_committed_but_public_attempt_and_gap_remain(corpus, monkeypatch):
    from web_app import political_discovery
    item = seed_real_partial(corpus)
    _, html, _, _ = case_data("125485")
    extract = political_discovery.extract_article
    def restricted_state(raw, url):
        # Controlled restriction state around an unchanged real article body;
        # the scenario tests persistence, not whether Exame restricts this URL.
        return {**extract(raw, url), "text_extent": "partial"}
    monkeypatch.setattr(political_discovery, "extract_article", restricted_state)
    requested = []
    def public_response(url, **kwargs):
        requested.append(url)
        return SimpleNamespace(url=url, text=html, status_code=200, headers={})
    monkeypatch.setattr(corpus, "fetch", public_response)
    job = recover(corpus, [item["source"]["key"]], recovery_gap_types=["partial_text"])
    corpus.process_task(corpus.claim_task("discovery", worker_id="local-discovery"))
    first = corpus.process_task(corpus.claim_task("fetch", worker_id="local-partial-worker"))
    assert first["status"] == "continue" and not requested
    with corpus._connect() as conn:
        row = conn.execute("SELECT * FROM political_articles WHERE id=%s", (item["article_id"],)).fetchone()
        assert corpus._read_text(row["text_object_key"], row["content_hash"]) == item["extracted"]["full_text"]
        assert row["metadata"]["text_extent"] == "partial"
        assert corpus._metrics(conn, job["id"])["articlesEnriched"] == 1
    second = corpus.process_task(corpus.claim_task("fetch", worker_id="local-partial-worker"))
    assert len(requested) == 1 and second["status"] == "gap"
    with corpus._connect() as conn:
        assert corpus._metrics(conn, job["id"])["articlesEnriched"] == 1
        assert conn.execute("SELECT status FROM political_jobs WHERE id=%s", (job["id"],)).fetchone()["status"] == "completed_with_gaps"
        assert dict(conn.execute("SELECT * FROM political_classifications WHERE article_id=%s", (item["article_id"],)).fetchone()) == item["classification"]


def test_enrichment_counts_distinct_articles_across_google_and_publisher_tasks(corpus):
    item = seed_real_partial(corpus)
    job = recover(corpus, [item["source"]["key"]], recovery_gap_types=["partial_text"])
    drain(corpus)
    with corpus._connect() as conn:
        assert corpus._metrics(conn, job["id"])["articlesEnriched"] == 1
        # The Google wrapper and publisher URL are both genuine preserved URLs
        # for this article. Simulate a second completed enrichment whose final
        # failure replaced result, while the committed cursor evidence remains.
        task = conn.execute("""INSERT INTO political_tasks(job_id,kind,source_key,dedupe_key,payload,cursor,status,error_type)
            VALUES(%s,'fetch','google_news',%s,%s::jsonb,'{"partial_body_enriched":true}','gap','partial_text_not_improved') RETURNING id""",
            (job["id"], GOOGLE_EXAME, json.dumps({"url": GOOGLE_EXAME, "source_key": "google_news"}))).fetchone()
        conn.execute("""INSERT INTO political_observations(job_id,source_task_id,observed_url,source_key,title,article_id,disposition)
            VALUES(%s,%s,%s,'google_news',%s,%s,'duplicate')""",
            (job["id"], task["id"], GOOGLE_EXAME, item["extracted"]["title"], item["article_id"]))
        assert conn.execute("""SELECT COUNT(*) AS n FROM political_tasks WHERE job_id=%s
            AND (result->>'bodyEnriched'='true' OR cursor->>'partial_body_enriched'='true')""", (job["id"],)).fetchone()["n"] == 2
        assert corpus._metrics(conn, job["id"])["articlesEnriched"] == 1
        # The remaining qualifying cursor must still count after the other
        # observation no longer points to an article.
        conn.execute("UPDATE political_observations SET article_id=NULL WHERE job_id=%s AND observed_url<>%s", (job["id"], GOOGLE_EXAME))
        assert corpus._metrics(conn, job["id"])["articlesEnriched"] == 1
