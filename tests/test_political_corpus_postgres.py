"""Integration tests run only on an explicitly supplied disposable PostgreSQL DB."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import os
import selectors
import sqlite3
import subprocess
import sys
import threading
import time

import pytest
import requests

from pipeline.database import SCHEMA_SQL
from web_app.political_corpus import (
    FetchProblem, LeaseLost, PoliticalAccessDenied, PoliticalCorpusService, PoliticalNotFound,
)

DATABASE_URL = os.environ.get("POLITICAL_TEST_DATABASE_URL", "").strip()
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="POLITICAL_TEST_DATABASE_URL must point to a disposable database")

TARGETS = [{"key": "paes", "display_name": "Eduardo Paes", "keywords": ["Eduardo Paes"]},
           {"key": "duarte", "display_name": "Pedro Duarte", "keywords": ["Pedro Duarte"]},
           {"key": "private", "display_name": "Pessoa Privada", "keywords": ["Pessoa Privada"]}]
BODY = "Eduardo Paes e Pedro Duarte participaram do encontro político. " + "A reportagem detalha propostas para o governo estadual e os municípios fluminenses. " * 10


class MemoryStore:
    enabled = True
    prefix = "political-test"
    def __init__(self): self.objects = {}
    def upload_bytes(self, data, key, content_type):
        self.objects[key] = data
        return True
    def read_political_object(self, key): return self.objects[key]


@pytest.fixture()
def service():
    corpus = PoliticalCorpusService(store=MemoryStore(), database_url=DATABASE_URL)
    corpus.ensure_schema()
    with corpus._connect() as conn:
        conn.execute("""TRUNCATE political_jobs,political_articles,political_stories,political_source_leases,
            political_domain_limits,political_workers,political_import_progress,political_legacy_ids,political_legacy_records RESTART IDENTITY CASCADE""")
    yield corpus
    corpus.close()


def start(service, monkeypatch, targets=("paes", "duarte"), tasks=None, kind="collect"):
    from web_app import political_discovery
    tasks = tasks or [{"source_key": "example", "strategy": "sitemap", "date_from": "2026-06-01", "date_to": "2026-06-02", "cursor": {}}]
    monkeypatch.setattr(political_discovery, "build_tasks", lambda *a, **k: tasks)
    return service.start_job({"target_keys": list(targets), "target_snapshots": TARGETS,
        "date_from": "2026-06-01", "date_to": "2026-06-02", "kind": kind}, started_by="test", allowed_target_keys=list(targets))


def enqueue(service, monkeypatch, candidate=None):
    from web_app import political_discovery
    candidate = candidate or {"url": "https://example.com/story", "title": "Encontro político", "source_name": "Example",
        "source_key": "example", "published_at": "2026-06-01T12:00:00-03:00", "snippet": "", "metadata": {}}
    monkeypatch.setattr(political_discovery, "discover", lambda task, fetch: {
        "candidates": [candidate, candidate], "outcome": "complete", "raw_count": 2,
        "next_cursor": None, "child_tasks": [], "gap_reason": ""})
    task = service.claim_task("discovery", worker_id="discovery")
    assert service.process_task(task)["status"] == "complete"
    return candidate


def fake_response(url, body=BODY, status=200):
    response = requests.Response()
    response.status_code = status
    response.url = url
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response._content = ("<html><head><title>Encontro político</title>"
        '<meta property="article:published_time" content="2026-06-01T15:00:00Z"></head>'
        f"<body><article><p>{body}</p></article></body></html>").encode()
    response.encoding = "utf-8"
    return response


@pytest.mark.parametrize("raises", [True, False])
def test_direct_source_gaps_enqueue_deduplicated_google_fallback_with_job_scope(service, monkeypatch, raises):
    from web_app import political_discovery
    direct = {"source_key": "g1", "strategy": "daily_sitemap", "day": "2026-06-01",
              "date_from": "2026-06-01", "date_to": "2026-06-02", "cursor": {"page": 1}}
    job = start(service, monkeypatch, tasks=[direct, {**direct, "cursor": {"page": 2}}])
    def fail(task, fetch):
        if raises:
            raise political_discovery.DiscoveryError("HTTP 403 at publisher", retryable=False, status_code=403)
        return {"outcome": "gap", "gap_reason": "sitemap_page_cap", "candidates": [], "child_tasks": [], "raw_count": 0}
    monkeypatch.setattr(political_discovery, "discover", fail)
    for _ in range(2):
        task = service.claim_task("discovery", worker_id="direct-fallback-check")
        assert task["payload"]["strategy"] == "daily_sitemap"
        assert service.process_task(task)["status"] == "gap"
    with service._connect() as conn:
        rows = conn.execute("SELECT payload FROM political_tasks WHERE job_id=%s AND payload->>'strategy'='google_news'", (job["id"],)).fetchall()
        gaps = conn.execute("SELECT COUNT(*) AS n FROM political_tasks WHERE job_id=%s AND status='gap'", (job["id"],)).fetchone()["n"]
    assert gaps == 2 and len(rows) == 2
    assert {row["payload"]["query"] for row in rows} == {'"Eduardo Paes" site:g1.globo.com', '"Pedro Duarte" site:g1.globo.com'}
    assert all(row["payload"]["date_from"] == row["payload"]["date_to"] == "2026-06-01" for row in rows)
    assert all("private" not in row["payload"]["target_ids"] for row in rows)


def test_complete_flow_deduplicates_matches_body_and_keeps_scope(service, monkeypatch):
    job = start(service, monkeypatch)
    enqueue(service, monkeypatch)
    monkeypatch.setattr(service, "fetch", lambda url, **kwargs: fake_response(url))
    task = service.claim_task("fetch", worker_id="fetch")
    result = service.process_task(task)
    assert result["status"] == "saved"
    rows = service.list_articles(allowed_target_keys=["paes"])
    assert len(rows["items"]) == 1
    article = rows["items"][0]
    assert article["targetKeys"] == ["paes"]
    assert article["dateStatus"] == "page_verified"
    assert article["bodyStatus"] == "body_extracted"
    assert "Pedro Duarte" in service.article_text(article["id"], allowed_target_keys=["paes"])["text"]
    with pytest.raises(PoliticalNotFound):
        service.article(article["id"], allowed_target_keys=["private"])
    status = service.status(job["id"], allowed_target_keys=["paes", "duarte"])["current"]
    assert status["status"] == "succeeded"
    assert status["metrics"]["uniqueCandidates"] == 1
    assert status["metrics"]["articlesInserted"] == 1
    assert status["metrics"]["mentionsInserted"] == 2
    assert status["metrics"]["fetchAttempted"] == 1
    with pytest.raises(PoliticalNotFound):
        service.status(job["id"], allowed_target_keys=["paes"])


def test_same_source_cannot_be_claimed_twice_and_global_capacity_enforced(service, monkeypatch):
    tasks = [{"source_key": "one", "strategy": "sitemap", "cursor": {"page": i}} for i in range(3)]
    tasks += [{"source_key": "two", "strategy": "sitemap", "cursor": {}}]
    start(service, monkeypatch, tasks=tasks)
    with ThreadPoolExecutor(max_workers=3) as pool:
        claims = list(pool.map(lambda i: service.claim_task("discovery", worker_id=f"d{i}"), range(3)))
    assert len([row for row in claims if row]) == 2
    assert {row["source_key"] for row in claims if row} == {"one", "two"}


def test_source_rotation_prevents_large_discovery_cursor_starvation(service, monkeypatch):
    tasks = [{"source_key": key, "strategy": "sitemap", "cursor": {}}
             for key in ("large", "second", "third")]
    start(service, monkeypatch, tasks=tasks)
    first = service.claim_task("discovery", worker_id="first")
    assert first["source_key"] == "large"
    with service._connect() as conn:
        service._finish(conn, first, "queued", cursor={"page": 2})
    second = service.claim_task("discovery", worker_id="second")
    assert second["source_key"] == "second"
    third = service.claim_task("discovery", worker_id="third")
    assert third["source_key"] == "third"


def test_google_wrappers_cannot_occupy_all_fetch_slots(service, monkeypatch):
    job = start(service, monkeypatch)
    with service._connect() as conn:
        for number in range(5):
            service._insert_task(conn, job["id"], "fetch", {
                "source_key": "google_news", "url": f"https://news.google.com/rss/articles/{number}"})
        service._insert_task(conn, job["id"], "fetch", {
            "source_key": "direct", "url": "https://publisher.example/story"})
    first = service.claim_task("fetch", worker_id="one")
    second = service.claim_task("fetch", worker_id="two")
    assert first["source_key"] == "google_news"
    assert second["source_key"] == "direct"
    assert service.claim_task("fetch", worker_id="three") is None


def test_six_fetch_claims_are_global_and_keep_google_single_slot(service, monkeypatch):
    monkeypatch.setenv("POLITICAL_FETCH_CONCURRENCY", "6")
    job = start(service, monkeypatch)
    with service._connect() as conn:
        for number in range(8):
            service._insert_task(conn, job["id"], "fetch", {"source_key": "google_news",
                "url": f"https://news.google.com/rss/articles/{number}"})
            service._insert_task(conn, job["id"], "fetch", {"source_key": f"direct{number}",
                "url": f"https://publisher{number}.example/story"})
    with ThreadPoolExecutor(max_workers=8) as pool:
        tasks=list(pool.map(lambda n:service.claim_task("fetch",worker_id=f"six-capacity-{n}"),range(8)))
    claimed=[task for task in tasks if task]
    assert len(claimed)==6
    assert sum(task["source_key"]=="google_news" for task in claimed)==1
    assert service.claim_task("fetch",worker_id="seventh") is None


def wait_for_claim_job_lock(conn):
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        conn.execute("SELECT pg_stat_clear_snapshot()")
        if conn.execute("""SELECT 1 FROM pg_stat_activity WHERE datname=current_database()
            AND pid<>pg_backend_pid() AND wait_event_type='Lock'
            AND query LIKE '%%SELECT id FROM political_jobs%%' LIMIT 1""").fetchone():
            return
        time.sleep(.01)
    pytest.fail("claim did not reach the expected job-row wait")


@pytest.mark.parametrize("kind", ["fetch", "discovery"])
def test_claim_waits_for_busy_job_without_locking_task_or_source(service, monkeypatch, kind):
    job = start(service, monkeypatch)
    with service._connect() as conn:
        service._insert_task(conn, job["id"], "fetch", {
            "source_key": "example", "url": "https://example.com/queued-story"})
    with ThreadPoolExecutor(max_workers=1) as pool:
        with service._connect() as finishing:
            finishing.execute("SELECT id FROM political_jobs WHERE id=%s FOR UPDATE", (job["id"],))
            pending = pool.submit(service.claim_task, kind, worker_id="concurrent-claim")
            try:
                # Previously the claim held the source row while waiting for
                # this job. Inserting the next discovery page then deadlocked.
                wait_for_claim_job_lock(finishing)
                assert not pending.done()
                finishing.execute("SET LOCAL lock_timeout='500ms'")
                service._insert_task(finishing, job["id"], "fetch", {
                    "source_key": "example", "url": "https://example.com/next-page-story"})
                assert finishing.execute("SELECT COUNT(*) AS n FROM political_tasks WHERE attempts>0").fetchone()["n"] == 0
                finishing.commit()
                claimed = pending.result(timeout=2)
                assert claimed and claimed["job_id"] == job["id"] and claimed["kind"] == kind
            finally:
                finishing.rollback()


def test_claim_rechecks_cancellation_after_waiting_for_job_lock(service, monkeypatch):
    job = start(service, monkeypatch)
    with ThreadPoolExecutor(max_workers=1) as pool:
        with service._connect() as cancelling:
            cancelling.execute("SELECT id FROM political_jobs WHERE id=%s FOR UPDATE", (job["id"],))
            pending = pool.submit(service.claim_task, "discovery", worker_id="cancel-race")
            try:
                wait_for_claim_job_lock(cancelling)
                cancelling.execute("UPDATE political_jobs SET status='cancelled' WHERE id=%s", (job["id"],))
                cancelling.commit()
                assert pending.result(timeout=2) is None
                assert cancelling.execute("SELECT COUNT(*) AS n FROM political_tasks WHERE attempts>0").fetchone()["n"] == 0
            finally:
                cancelling.rollback()


def test_claim_keeps_skip_locked_for_busy_candidate_task(service, monkeypatch):
    start(service, monkeypatch)
    with ThreadPoolExecutor(max_workers=1) as pool:
        with service._connect() as renewing:
            renewing.execute("SELECT id FROM political_tasks FOR UPDATE")
            pending = pool.submit(service.claim_task, "discovery", worker_id="while-renewing")
            try:
                assert pending.result(timeout=2) is None
            finally:
                renewing.rollback()
    assert service.claim_task("discovery", worker_id="after-renewal") is not None


def test_full_fetch_backlog_does_not_lease_or_churn_discovery_tasks(service, monkeypatch):
    job = start(service, monkeypatch)
    with service._connect() as conn:
        conn.execute("""INSERT INTO political_tasks(job_id,kind,source_key,dedupe_key,payload)
            SELECT %s,'fetch','example','backlog-' || n,'{}'::jsonb FROM generate_series(1,2000) AS n""", (job['id'],))
    for _ in range(3):
        assert service.claim_task('discovery', worker_id='d') is None
    with service._connect() as conn:
        discovery = conn.execute("SELECT status,attempts FROM political_tasks WHERE kind='discovery'").fetchone()
        assert discovery['status'] == 'queued' and discovery['attempts'] == 0
        conn.execute("UPDATE political_tasks SET status='complete' WHERE dedupe_key='backlog-1'")
    assert service.claim_task('discovery', worker_id='d') is not None


def _queue_pending_fetches(conn, job_id, source_key, count):
    conn.execute("""INSERT INTO political_tasks(job_id,kind,source_key,dedupe_key,payload)
        SELECT %s,'fetch',%s,%s || n,'{}'::jsonb FROM generate_series(1,%s) AS n""",
        (job_id, source_key, source_key + '-pending-', count))


@pytest.mark.parametrize("source_backlog,total_backlog,admitted", [
    (99, 2000, True), (100, 2000, False), (0, 4000, False), (100, 1999, True),
])
def test_discovery_admission_uses_source_backlog_across_active_jobs(
        service, monkeypatch, source_backlog, total_backlog, admitted):
    from web_app import political_discovery
    older = start(service, monkeypatch, tasks=[
        {"source_key": "g1", "strategy": "daily_sitemap", "cursor": {}},
        {"source_key": "agenda_do_poder", "strategy": "wordpress", "cursor": {}},
    ])
    current = start(service, monkeypatch, tasks=[{"source_key": "cbn", "strategy": "daily_sitemap", "cursor": {}}])
    with service._connect() as conn:
        _queue_pending_fetches(conn, older["id"], "g1", 1000)
        _queue_pending_fetches(conn, older["id"], "agenda_do_poder", total_backlog - source_backlog - 1000)
        # Both runs contribute to the same source budget. Counting only the
        # current job would incorrectly admit the 100-task boundary case.
        _queue_pending_fetches(conn, older["id"], "cbn", source_backlog // 2)
        _queue_pending_fetches(conn, current["id"], "cbn", source_backlog - source_backlog // 2)
    task = service.claim_task("discovery", worker_id="source-budget")
    if not admitted:
        assert task is None
        with service._connect() as conn:
            assert conn.execute("SELECT SUM(attempts) AS n FROM political_tasks WHERE kind='discovery'").fetchone()["n"] == 0
        return
    # Below the global threshold all sources qualify, preserving source rotation.
    if total_backlog < 2000:
        assert task["source_key"] == "g1"
        return
    assert task["source_key"] == "cbn" and task["job_id"] == current["id"]
    monkeypatch.setattr(political_discovery, "discover", lambda *a: {
        "outcome": "complete", "candidates": [{"url": "https://cbn.globo.com/rio-de-janeiro/new-story",
            "title": "Eduardo Paes", "published_at": "2026-06-01T12:00:00-03:00"}],
        "raw_count": 1, "next_cursor": None, "child_tasks": [], "gap_reason": ""})
    # The execution-time check must admit the same low-backlog source.
    assert service.process_task(task)["status"] == "complete"
    with service._connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM political_tasks WHERE job_id=%s AND kind='fetch' AND payload->>'title'='Eduardo Paes'",
                            (current["id"],)).fetchone()["n"] == 1


@pytest.mark.parametrize("source_backlog,total_backlog", [(100, 2000), (0, 4000)])
def test_discovery_rechecks_source_and_global_admission_before_network(service, monkeypatch, source_backlog, total_backlog):
    from web_app import political_discovery
    job = start(service, monkeypatch, tasks=[{"source_key": "cbn", "strategy": "daily_sitemap", "cursor": {"page": 7}}])
    task = service.claim_task("discovery", worker_id="admission-race")
    with service._connect() as conn:
        _queue_pending_fetches(conn, job["id"], "g1", total_backlog - source_backlog)
        _queue_pending_fetches(conn, job["id"], "cbn", source_backlog)
    monkeypatch.setattr(political_discovery, "discover", lambda *a: pytest.fail("blocked discovery must not request HTTP"))
    assert service.process_task(task)["status"] == "backpressure"
    with service._connect() as conn:
        row = conn.execute("SELECT status,cursor,lease_token,next_attempt_at FROM political_tasks WHERE id=%s", (task["id"],)).fetchone()
        assert row["status"] == "queued" and row["cursor"] == {"page": 7}
        assert row["lease_token"] is None and row["next_attempt_at"] is not None


def test_direct_discovery_precedes_google_for_same_source_without_removing_google(service, monkeypatch):
    job = start(service, monkeypatch, tasks=[
        {"source_key": "j3news", "strategy": "google_news", "query": '"Eduardo Paes"', "cursor": {}},
        {"source_key": "j3news", "strategy": "wordpress", "cursor": {}},
        {"source_key": "metropoles", "strategy": "sitemap", "cursor": {}},
    ])
    first = service.claim_task("discovery", worker_id="direct-first")
    assert first["source_key"] == "j3news" and first["payload"]["strategy"] == "wordpress" and first["priority"] == 10
    with service._connect() as conn:
        service._finish(conn, first, "complete")
    second = service.claim_task("discovery", worker_id="other-source")
    assert second["source_key"] == "metropoles"
    with service._connect() as conn:
        service._finish(conn, second, "complete")
    third = service.claim_task("discovery", worker_id="google-after-direct")
    assert third["source_key"] == "j3news" and third["payload"]["strategy"] == "google_news" and third["priority"] == 0
    with service._connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM political_tasks WHERE job_id=%s", (job["id"],)).fetchone()["n"] == 3


def test_lease_expiry_recovery_fences_old_worker(service, monkeypatch):
    start(service, monkeypatch)
    old = service.claim_task("discovery", worker_id="old")
    with service._connect() as conn:
        conn.execute("UPDATE political_tasks SET leased_until=NOW()-INTERVAL '1 second' WHERE id=%s", (old["id"],))
        conn.execute("UPDATE political_source_leases SET leased_until=NOW()-INTERVAL '1 second'")
    new = service.claim_task("discovery", worker_id="new")
    assert old["id"] == new["id"] and old["lease_token"] != new["lease_token"]
    assert service.renew_lease(old) is False
    with service._connect() as conn:
        with pytest.raises(LeaseLost):
            service._finish(conn, old, "complete")
    assert service.renew_lease(new) is True


def test_cancel_fences_inflight_and_resume_keeps_discovery_cursor(service, monkeypatch):
    job = start(service, monkeypatch)
    task = service.claim_task("discovery", worker_id="d")
    with service._connect() as conn:
        conn.execute("UPDATE political_tasks SET cursor='{" + '"page": 12' + "}'::jsonb WHERE id=%s", (task["id"],))
    service.cancel_job(job["id"], allowed_target_keys=["paes", "duarte"])
    assert service.renew_lease(task) is False
    service.resume_job(job["id"], allowed_target_keys=["paes", "duarte"])
    resumed = service.claim_task("discovery", worker_id="d")
    assert resumed["cursor"] == {"page": 12}


def test_metadata_only_is_saved_but_retry_and_gap_remain_visible(service, monkeypatch):
    job = start(service, monkeypatch, targets=("paes",))
    enqueue(service, monkeypatch, {"url": "https://example.com/paes", "title": "Eduardo Paes apresentou propostas",
                                 "source_name": "Example", "published_at": "2026-06-01T12:00:00-03:00"})
    monkeypatch.setattr(service, "fetch", lambda url, **kwargs: fake_response(url, status=429))
    task = service.claim_task("fetch", worker_id="f")
    assert service.process_task(task)["status"] == "retryable"
    item = service.list_articles(allowed_target_keys=["paes"])["items"][0]
    assert item["bodyStatus"] == "metadata_only"
    assert service.article_text(item["id"], allowed_target_keys=["paes"])["text"] == ""
    with service._connect() as conn:
        conn.execute("UPDATE political_tasks SET next_attempt_at=NULL,attempts=5 WHERE id=%s", (task["id"],))
    retried = service.claim_task("fetch", worker_id="f")
    assert service.process_task(retried)["status"] == "gap"
    current = service.status(job["id"], allowed_target_keys=["paes"])["current"]
    assert current["status"] == "completed_with_gaps"
    assert current["metrics"]["articlesInserted"] == 1
    assert service.coverage(job["id"], allowed_target_keys=["paes"])["gaps"]


def test_storage_failure_does_not_advance_task_or_create_full_body_record(service, monkeypatch):
    start(service, monkeypatch)
    enqueue(service, monkeypatch)
    monkeypatch.setattr(service, "fetch", lambda url, **kwargs: fake_response(url))
    monkeypatch.setattr(service.store, "upload_bytes", lambda *a, **k: False)
    task = service.claim_task("fetch", worker_id="f")
    assert service.process_task(task)["status"] == "retryable"
    assert service.list_articles(allowed_target_keys=["paes"])["items"] == []


def test_classification_is_target_scoped_and_not_rewritten_by_review(service, monkeypatch):
    item = service.insert_manual_story({"url": "https://example.com/manual", "title": "Eduardo Paes", "full_text": BODY,
        "target_keys": ["paes"], "target_snapshots": TARGETS, "published_at": "2026-06-01T15:00:00Z"},
        allowed_target_keys=["paes", "duarte"], created_by="test")
    service.upsert_classification(item["id"], {"targetKey": "paes", "target_sentiment": "negative", "categories": ["transport"]},
                                  allowed_target_keys=["paes"], updated_by="human")
    with pytest.raises(PoliticalAccessDenied):
        service.upsert_classification(item["id"], {"targetKey": "private"}, allowed_target_keys=["paes"], updated_by="x")
    start(service, monkeypatch, kind="review")
    task = service.claim_task("discovery", worker_id="review")
    assert service.process_task(task)["mentionsAdded"] == 1
    assert service.article(item["id"], allowed_target_keys=["duarte"])["targetKeys"] == ["duarte"]
    assert service.classifications(item["id"], allowed_target_keys=["duarte"])["items"] == []
    saved = service.classifications(item["id"], allowed_target_keys=["paes"])["items"][0]
    assert saved["payload"]["target_sentiment"] == "negative" and saved["updatedBy"] == "human"


def test_stable_cursor_and_story_preview_apply_same_filters(service):
    with service._connect() as conn:
        for i in range(5):
            service._persist_article(conn, {"url": f"https://example.com/{i}", "title": f"Story {i}", "source_key": "one" if i < 4 else "two"},
                [{"target_key": "paes", "target_name": "Eduardo Paes", "keyword_matched": "Eduardo Paes"}],
                published=datetime(2026, 6, 1, tzinfo=timezone.utc), story_key="shared")
    first = service.list_articles(allowed_target_keys=["paes"], page_size=2)
    second = service.list_articles(allowed_target_keys=["paes"], page_size=2, cursor=first["nextCursor"])
    assert {item["id"] for item in first["items"]}.isdisjoint(item["id"] for item in second["items"])
    stories = service.list_stories(allowed_target_keys=["paes"], source_key="one")
    story = stories["items"][0]
    assert story["articleCount"] == 4 and story["articles"][0]["sourceKey"] == "one"
    assert story["hasMoreArticles"] is True
    assert len(service.list_articles(allowed_target_keys=["paes"], story_id=story["id"])["items"]) == 5


def test_live_results_only_include_job_observations_and_require_full_job_scope(service, monkeypatch):
    first = start(service, monkeypatch)
    second = start(service, monkeypatch, targets=("paes",))
    with service._connect() as conn:
        ids = [service._persist_article(conn, {"url": f"https://example.com/job-{i}", "title": f"Job {i}"},
            [{"target_key": "paes", "target_name": "Eduardo Paes", "keyword_matched": "Eduardo Paes"}]) for i in range(3)]
        for job, index in [(first, 0), (second, 1)]:
            source_task = conn.execute("SELECT id FROM political_tasks WHERE job_id=%s LIMIT 1", (job["id"],)).fetchone()["id"]
            for alias in ("direct", "wrapper"):
                conn.execute("""INSERT INTO political_observations(job_id,source_task_id,observed_url,source_key,article_id)
                    VALUES (%s,%s,%s,'example',%s)""", (job["id"], source_task, f"https://example.com/{alias}-{index}", ids[index]))
    assert len(service.list_articles(allowed_target_keys=["paes", "duarte"])["items"]) == 3
    result = service.list_articles(job_id=first["id"], allowed_target_keys=["paes", "duarte"], target_keys=["paes"])
    assert [item["id"] for item in result["items"]] == [ids[0]]
    assert service.list_articles(job_id=first["id"], allowed_target_keys=["paes", "duarte"], q="Job 1")["items"] == []
    with pytest.raises(PoliticalNotFound):
        service.list_articles(job_id=first["id"], allowed_target_keys=["paes"])
    with pytest.raises(PoliticalNotFound):
        service.list_articles(job_id="political-missing", allowed_target_keys=["paes", "duarte"])


def test_domain_rate_limit_is_shared_across_connections(service):
    with ThreadPoolExecutor(max_workers=4) as pool:
        waits = sorted(pool.map(service.reserve_domain, ["example.com", "www.example.com", "WWW.EXAMPLE.COM.", "EXAMPLE.COM."]))
    assert waits[0] < 0.1
    assert waits[-1] >= 2.5
    with service._connect() as conn:
        assert conn.execute("SELECT domain FROM political_domain_limits").fetchall() == [{"domain": "example.com"}]


def legacy_database(path):
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.execute("""INSERT INTO articles(id,url,title,source_name,source_type,published_at,discovered_at,snippet,full_text,raw_html,summary)
            VALUES (7,'https://example.com/legacy','Eduardo Paes','Example','rss','2026-06-01T15:00:00Z','2026-06-01','','body text','<html>original</html>','Human summary')""")
        conn.execute("INSERT INTO mentions(id,article_id,target_key,target_name,keyword_matched) VALUES(17,7,'paes','Eduardo Paes','Eduardo Paes')")
        conn.execute("INSERT INTO stories(id,title,summary,created_at,updated_at) VALUES(27,'Original story','Original story summary','2026-06-01','2026-06-01')")
        conn.execute("INSERT INTO story_articles(story_id,article_id) VALUES(27,7)")
        conn.execute("INSERT INTO categories(id,name,created_by,created_at) VALUES(37,'Transport','human','2026-06-01')")
        conn.execute("INSERT INTO classifications(id,mention_id,article_sentiment,target_sentiment,classified_by,classified_at) VALUES(47,17,'neutral','negative','human','2026-06-01')")
        conn.execute("INSERT INTO classification_categories VALUES(47,37)")


def test_migration_preserves_ids_categories_and_human_data_idempotently(service, tmp_path):
    path = tmp_path / "legacy.db"
    legacy_database(path)
    before = path.read_bytes()
    result = service.import_sqlite(path, allowed_target_keys=["paes"], batch_size=1)
    assert result["validation"]["ok"] is True
    item = service.list_articles(allowed_target_keys=["paes"])["items"][0]
    assert item["legacyId"] == 7 and item["summary"] == "Human summary"
    assert item["bodyStatus"] == "legacy_body"
    saved = service.classifications(item["id"], allowed_target_keys=["paes"])["items"][0]
    assert saved["legacyId"] == 47 and saved["payload"]["categories"] == ["Transport"]
    assert saved["payload"]["legacy_records"][0]["categories"][0]["id"] == 37
    assert saved["payload"]["target_sentiment"] == "negative"
    assert service.import_sqlite(path, allowed_target_keys=["paes"])["imported"] == 0
    assert service.health(check_database=True)["migrationReady"] is True
    assert path.read_bytes() == before
    with service._connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM political_articles").fetchone()["n"] == 1


def legacy_duplicate_with_another_story(path):
    legacy_database(path)
    with sqlite3.connect(path) as conn:
        conn.execute("""INSERT INTO articles(id,url,title,source_name,source_type,published_at,discovered_at,snippet,full_text,raw_html,summary)
            SELECT 8,url || '?utm_source=mirror',title,source_name,source_type,published_at,discovered_at,snippet,full_text,raw_html,summary FROM articles WHERE id=7""")
        conn.execute("INSERT INTO mentions(id,article_id,target_key,target_name,keyword_matched) VALUES(18,8,'duarte','Pedro Duarte','Pedro Duarte')")
        conn.execute("INSERT INTO stories(id,title,summary,created_at,updated_at) VALUES(28,'Second story','Second summary','2026-06-01','2026-06-01')")
        conn.execute("INSERT INTO story_articles(story_id,article_id) VALUES(28,8)")
        conn.execute("ALTER TABLE story_articles ADD COLUMN legacy_note TEXT")
        conn.execute("UPDATE story_articles SET legacy_note='original relationship'")
        conn.execute("INSERT INTO classifications(id,mention_id,article_sentiment,target_sentiment,classified_by,classified_at) VALUES(48,18,'positive','neutral','second_editor','2026-06-01')")


def test_migration_preserves_all_stories_when_canonical_articles_merge(service, tmp_path):
    path = tmp_path / "legacy_stories.db"
    legacy_duplicate_with_another_story(path)
    result = service.import_sqlite(path, allowed_target_keys=["paes", "duarte"], batch_size=1)
    assert result["hasMore"] is True and result["validation"]["ok"] is False
    result = service.import_sqlite(path, allowed_target_keys=["paes", "duarte"], batch_size=1)
    assert result["validation"]["ok"] is True
    validation = result["validation"]
    assert validation["expectedStories"] == validation["counts"]["story"] == 2
    assert validation["expectedStoryArticles"] == validation["counts"]["story_article"] == 2
    assert validation["expectedStoryIdsHash"] == validation["actualStoryIdsHash"]
    assert validation["expectedStoryLinksHash"] == validation["actualStoryLinksHash"]
    articles = service.list_articles(allowed_target_keys=["paes", "duarte"])["items"]
    assert len(articles) == 1 and articles[0]["targetKeys"] == ["duarte", "paes"]
    stories = service.list_stories(allowed_target_keys=["paes", "duarte"])["items"]
    assert {item["legacyId"] for item in stories} == {27, 28}
    assert all(item["articles"][0]["id"] == articles[0]["id"] for item in stories)
    with service._connect() as conn:
        originals = conn.execute("SELECT payload FROM political_legacy_story_articles ORDER BY legacy_story_id").fetchall()
    assert [row["payload"] for row in originals] == [
        {"story_id": 27, "article_id": 7, "legacy_note": "original relationship"},
        {"story_id": 28, "article_id": 8, "legacy_note": "original relationship"},
    ]
    assert len(service.classifications(articles[0]["id"], allowed_target_keys=["paes", "duarte"])["items"]) == 2
    assert service.import_sqlite(path, allowed_target_keys=["paes", "duarte"])["imported"] == 0


@pytest.mark.parametrize("damage,field", [
    ("DELETE FROM political_story_articles", "danglingStoryArticles"),
    ("DELETE FROM political_mentions", "danglingMentions"),
    ("DELETE FROM political_classifications", "danglingClassifications"),
    ("UPDATE political_legacy_ids SET legacy_id=999 WHERE entity_type='story'", "danglingStoryArticles"),
])
def test_migration_validation_detects_broken_resolved_relations(service, tmp_path, damage, field):
    path = tmp_path / "legacy.db"
    legacy_database(path)
    assert service.import_sqlite(path, allowed_target_keys=["paes"])["validation"]["ok"] is True
    with service._connect() as conn:
        conn.execute(damage)
    result = service.import_sqlite(path, allowed_target_keys=["paes"])
    assert result["validation"]["ok"] is False
    assert result["validation"][field] == 1
    assert service.health(check_database=True)["migrationReady"] is False


def test_concurrent_import_does_not_replay_a_stale_batch_or_checkpoint(service, monkeypatch, tmp_path):
    path = tmp_path / "legacy.db"
    legacy_duplicate_with_another_story(path)
    barrier = threading.Barrier(2)
    original_store = service._store_text

    def prepare_together(text):
        value = original_store(text)
        barrier.wait(timeout=10)
        return value

    monkeypatch.setattr(service, "_store_text", prepare_together)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: service.import_sqlite(path, allowed_target_keys=["paes", "duarte"], batch_size=1), range(2)))
    assert sorted(result["imported"] for result in results) == [0, 1]
    assert all(result["cursor"] == 7 and result["hasMore"] for result in results)
    monkeypatch.setattr(service, "_store_text", original_store)
    final = service.import_sqlite(path, allowed_target_keys=["paes", "duarte"], batch_size=1)
    assert final["cursor"] == 8 and final["validation"]["ok"] is True


def test_import_resume_is_bound_to_the_original_snapshot(service, monkeypatch, tmp_path):
    path = tmp_path / "legacy.db"
    legacy_duplicate_with_another_story(path)
    digest = "a" * 64
    first = service.import_sqlite(path, allowed_target_keys=["paes", "duarte"], batch_size=1,
                                  snapshot_sha256=digest, remote_backup="immutable/original.db.gz")
    assert first["hasMore"] is True
    with pytest.raises(ValueError, match="snapshot_changed"):
        service.import_sqlite(path, allowed_target_keys=["paes", "duarte"], snapshot_sha256="b" * 64)
    with service._connect() as conn:
        progress = conn.execute("SELECT * FROM political_import_progress").fetchone()
    assert progress["last_article_id"] == 7 and progress["validation"]["snapshotSha256"] == digest
    final = service.import_sqlite(path, allowed_target_keys=["paes", "duarte"], snapshot_sha256=digest)
    assert final["validation"]["ok"] is True
    assert final["validation"]["remoteBackup"] == "immutable/original.db.gz"
    replay = service.import_sqlite(path, allowed_target_keys=["paes", "duarte"])
    assert replay["validation"]["snapshotSha256"] == digest and replay["imported"] == 0


def test_migration_storage_failure_does_not_advance_checkpoint(service, monkeypatch, tmp_path):
    path = tmp_path / "legacy.db"
    legacy_database(path)
    monkeypatch.setattr(service.store, "upload_bytes", lambda *a, **k: False)
    with pytest.raises(FetchProblem):
        service.import_sqlite(path, allowed_target_keys=["paes"])
    with service._connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM political_import_progress").fetchone()["n"] == 0


def test_failed_extraction_retains_html_and_does_not_claim_a_real_body(service, monkeypatch):
    start(service, monkeypatch, targets=("paes",))
    enqueue(service, monkeypatch, {"url": "https://example.com/short", "title": "Eduardo Paes", "source_name": "Example"})
    monkeypatch.setattr(service, "fetch", lambda url, **kwargs: fake_response(url, "Eduardo Paes falou."))
    task = service.claim_task("fetch", worker_id="f")
    assert service.process_task(task)["status"] == "retryable"
    article = service.list_articles(allowed_target_keys=["paes"])["items"][0]
    assert article["bodyStatus"] == "metadata_only"
    with service._connect() as conn:
        row = conn.execute("SELECT html_hash,html_object_key FROM political_articles WHERE id=%s", (article["id"],)).fetchone()
    assert row["html_object_key"].endswith(".html.gz")
    assert row["html_object_key"] in service.store.objects


def test_review_refetches_legacy_content_and_preserves_classification_history(service, monkeypatch, tmp_path):
    path = tmp_path / "legacy.db"
    legacy_database(path)
    service.import_sqlite(path, allowed_target_keys=["paes"])
    item = service.list_articles(allowed_target_keys=["paes"])["items"][0]
    service.upsert_classification(item["id"], {"targetKey": "paes", "target_sentiment": "positive", "categories": ["Education"]},
                                  allowed_target_keys=["paes"], updated_by="editor")
    start(service, monkeypatch, kind="review", targets=("paes",))
    review = service.claim_task("discovery", worker_id="review")
    assert service.process_task(review)["status"] == "complete"
    fetch = service.claim_task("fetch", worker_id="fetch")
    assert fetch["payload"]["force_refresh"] is True
    monkeypatch.setattr(service, "fetch", lambda url, **kwargs: fake_response(url))
    assert service.process_task(fetch)["status"] == "duplicate"
    updated = service.article(item["id"], allowed_target_keys=["paes"])
    assert updated["dateStatus"] == "page_verified" and updated["bodyStatus"] == "body_extracted"
    revisions = service.revision_history(item["id"], allowed_target_keys=["paes"])
    assert revisions["articles"][0]["previous"]["title"] == "Eduardo Paes"
    assert revisions["classifications"][0]["previous"]["payload"]["target_sentiment"] == "negative"
    saved = service.classifications(item["id"], allowed_target_keys=["paes"])["items"][0]
    assert saved["payload"]["target_sentiment"] == "positive" and saved["updatedBy"] == "editor"


def test_forced_shorter_correction_keeps_pointer_size_consistent_and_old_revision(service):
    first, second = BODY, "Eduardo Paes " + "A notícia corrigida preserva os fatos apurados. " * 6
    d1, k1 = service._store_text(first)
    d2, k2 = service._store_text(second)
    candidate = {"url": "https://example.com/corrected", "title": "Eduardo Paes", "source_name": "Example"}
    hits = [{"target_key": "paes", "target_name": "Eduardo Paes", "keyword_matched": "Eduardo Paes"}]
    with service._connect() as conn:
        article_id = service._persist_article(conn, candidate, hits, body_chars=len(first), digest=d1, object_key=k1)
        service._persist_article(conn, candidate, hits, body_chars=len(second), digest=d2, object_key=k2)
    assert service.article_text(article_id, allowed_target_keys=["paes"])["text"] == first
    with service._connect() as conn:
        service._persist_article(conn, candidate, hits, body_chars=len(second), digest=d2, object_key=k2, force_correction=True)
    assert service.article(article_id, allowed_target_keys=["paes"])["bodyChars"] == len(second)
    assert service.article_text(article_id, allowed_target_keys=["paes"])["text"] == second
    assert service.revision_history(article_id, allowed_target_keys=["paes"])["articles"][0]["previous"]["text_object_key"] == k1


def test_canonical_wrapper_merges_into_outlet_article_without_losing_classifications(service):
    hits = [{"target_key": "paes", "target_name": "Eduardo Paes", "keyword_matched": "Eduardo Paes"}]
    with service._connect() as conn:
        wrapper_id = service._persist_article(conn, {"url": "https://news.google.com/articles/wrapper", "title": "Eduardo Paes"}, hits)
        final_id = service._persist_article(conn, {"url": "https://example.com/final", "title": "Eduardo Paes"}, hits)
    service.upsert_classification(wrapper_id, {"targetKey": "paes", "target_sentiment": "negative"},
                                  allowed_target_keys=["paes"], updated_by="editor")
    with service._connect() as conn:
        merged_id = service._persist_article(conn, {"url": "https://example.com/final", "observed_url": "https://news.google.com/articles/wrapper",
                                                   "title": "Eduardo Paes"}, hits)
    assert merged_id == final_id
    assert len(service.list_articles(allowed_target_keys=["paes"])["items"]) == 1
    assert service.classifications(final_id, allowed_target_keys=["paes"])["items"][0]["payload"]["target_sentiment"] == "negative"


def test_canonical_merge_waits_for_committed_editor_and_preserves_latest_classification(service, monkeypatch):
    hits = [{"target_key": "paes", "target_name": "Eduardo Paes", "keyword_matched": "Eduardo Paes"}]
    wrapper, canonical = "https://news.google.com/articles/concurrent-edit", "https://example.com/concurrent-edit"
    with service._connect() as conn:
        old_id = service._persist_article(conn, {"url": wrapper, "title": "Eduardo Paes"}, hits)
        new_id = service._persist_article(conn, {"url": canonical, "title": "Eduardo Paes"}, hits)
    service.upsert_classification(old_id, {"targetKey": "paes", "target_sentiment": "negative"},
                                  allowed_target_keys=["paes"], updated_by="first-editor")
    original_connect = service._connect
    role = threading.local()
    editor_locked, release_editor = threading.Event(), threading.Event()
    merge_attempted, merge_acquired, release_merge = threading.Event(), threading.Event(), threading.Event()
    merge_pid = []
    lock_key = f"political-classification:{old_id}:paes"

    class ObservedConnection:
        def __init__(self, conn): self.conn = conn
        def __getattr__(self, name): return getattr(self.conn, name)
        def execute(self, query, params=None, **kwargs):
            matching_lock = "pg_advisory_xact_lock" in str(query) and params == (lock_key,)
            actor = getattr(role, "actor", "")
            if actor == "merge" and matching_lock:
                merge_pid.append(self.conn.info.backend_pid)
                merge_attempted.set()
            result = self.conn.execute(query, params, **kwargs)
            if actor == "editor" and matching_lock:
                editor_locked.set()
                assert release_editor.wait(5), "test did not release editor"
            if actor == "merge" and matching_lock:
                merge_acquired.set()
                assert release_merge.wait(5), "test did not release merge"
            return result

    @contextmanager
    def observed_connect():
        with original_connect() as conn:
            conn.execute("SET LOCAL lock_timeout='5s'")
            yield ObservedConnection(conn)

    monkeypatch.setattr(service, "_connect", observed_connect)
    def edit():
        role.actor = "editor"
        return service.upsert_classification(old_id, {"targetKey": "paes", "target_sentiment": "positive"},
                                              allowed_target_keys=["paes"], updated_by="concurrent-editor")
    def merge():
        role.actor = "merge"
        with service._connect() as conn:
            return service._persist_article(conn, {"url": canonical, "observed_url": wrapper, "title": "Eduardo Paes"}, hits)

    with ThreadPoolExecutor(max_workers=2) as pool:
        editor_future = pool.submit(edit)
        try:
            assert editor_locked.wait(5)
            merge_future = pool.submit(merge)
            assert merge_attempted.wait(5), "merge must acquire the editor's classification lock"
            # Observe PostgreSQL's actual advisory-lock wait, not a sleep-based
            # assumption about which Python thread has run first.
            deadline = time.monotonic() + 3
            waiting = False
            while time.monotonic() < deadline:
                with original_connect() as conn:
                    row = conn.execute("SELECT wait_event_type,wait_event FROM pg_stat_activity WHERE pid=%s", (merge_pid[0],)).fetchone()
                if row and row["wait_event_type"] == "Lock" and row["wait_event"] == "advisory":
                    waiting = True
                    break
                time.sleep(.01)
            assert waiting and not merge_acquired.is_set()
            release_editor.set()
            edited = editor_future.result(timeout=5)
            assert edited["items"][0]["payload"]["target_sentiment"] == "positive"
            assert merge_acquired.wait(5)
            release_merge.set()
            assert merge_future.result(timeout=5) == new_id
        finally:
            release_editor.set()
            release_merge.set()
    result = service.classifications(new_id, allowed_target_keys=["paes"])["items"][0]
    assert result["payload"]["target_sentiment"] == "positive" and result["updatedBy"] == "concurrent-editor"
    revisions = service.revision_history(new_id, allowed_target_keys=["paes"])["classifications"]
    assert any(row["previous"]["payload"]["target_sentiment"] == "negative" for row in revisions)
    assert any(row["previous"]["payload"]["target_sentiment"] == "positive" for row in revisions)


def test_editor_authorized_before_merge_gets_not_found_when_old_mention_is_gone(service, monkeypatch):
    hits = [{"target_key": "paes", "target_name": "Eduardo Paes", "keyword_matched": "Eduardo Paes"}]
    wrapper, canonical = "https://news.google.com/articles/stale-edit", "https://example.com/stale-edit"
    with service._connect() as conn:
        old_id = service._persist_article(conn, {"url": wrapper, "title": "Eduardo Paes"}, hits)
        new_id = service._persist_article(conn, {"url": canonical, "title": "Eduardo Paes"}, hits)
    service.upsert_classification(old_id, {"targetKey": "paes", "target_sentiment": "positive"},
                                  allowed_target_keys=["paes"], updated_by="committed-editor")
    original_article = service.article
    authorized, release_editor = threading.Event(), threading.Event()
    role = threading.local()
    def gated_article(article_id, **kwargs):
        result = original_article(article_id, **kwargs)
        if article_id == old_id and getattr(role, "stale_editor", False):
            authorized.set()
            assert release_editor.wait(5), "test did not release stale editor"
        return result
    monkeypatch.setattr(service, "article", gated_article)
    def edit():
        role.stale_editor = True
        return service.upsert_classification(old_id, {"targetKey": "paes", "target_sentiment": "negative"},
                                              allowed_target_keys=["paes"], updated_by="stale-editor")
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(edit)
        try:
            assert authorized.wait(5)
            with service._connect() as conn:
                assert service._persist_article(conn, {"url": canonical, "observed_url": wrapper, "title": "Eduardo Paes"}, hits) == new_id
            release_editor.set()
            with pytest.raises(PoliticalNotFound):
                future.result(timeout=5)
        finally:
            release_editor.set()
    result = service.classifications(new_id, allowed_target_keys=["paes"])["items"][0]
    assert result["payload"]["target_sentiment"] == "positive" and result["updatedBy"] == "committed-editor"
    with service._connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM political_classifications WHERE article_id=%s", (old_id,)).fetchone()["n"] == 0


@pytest.mark.parametrize("existing_generic,wrapped", [(False, True), (True, True), (True, False)])
def test_google_discovery_is_attributed_to_resolved_publisher_without_losing_provenance(service, monkeypatch, existing_generic, wrapped):
    from web_app import political_discovery
    canonical = "https://www.g1.globo.com/rj/rio-de-janeiro/noticia/2026/06/01/fixture.ghtml"
    original_id = None
    if existing_generic:
        digest, object_key = service._store_text(BODY)
        with service._connect() as conn:
            original_id = service._persist_article(conn, {"url": canonical, "title": "Encontro político",
                "source_key": "google_news", "source_name": "Google News", "metadata": {"original": "kept"}},
                [{"target_key": "paes", "target_name": "Eduardo Paes", "keyword_matched": "Eduardo Paes"}],
                published=datetime(2026, 6, 1, 15, tzinfo=timezone.utc), date_status="page_verified",
                body_chars=len(BODY), digest=digest, object_key=object_key)
    job = start(service, monkeypatch, targets=("paes",), tasks=[{"source_key": "google_news", "strategy": "google_news", "cursor": {}}])
    candidate = {"url": "https://news.google.com/articles/publisher-fixture" if wrapped else canonical, "title": "Eduardo Paes",
                 "source_key": "google_news", "source_name": "Google News", "metadata": {"google_redirect": wrapped}}
    enqueue(service, monkeypatch, candidate)
    monkeypatch.setattr(political_discovery, "resolve_google_redirect", lambda url, fetch, **kwargs: canonical)
    monkeypatch.setattr(service, "fetch", lambda url, **kwargs: fake_response(url))
    task = service.claim_task("fetch", worker_id="publisher-worker")
    result = service.process_task(task)
    assert result["status"] == ("duplicate" if existing_generic else "saved")
    items = service.list_articles(allowed_target_keys=["paes"], source_key="g1")["items"]
    assert len(items) == 1 and items[0]["sourceName"] == "G1"
    assert service.list_articles(allowed_target_keys=["paes"], source_key="google_news")["items"] == []
    if original_id:
        assert items[0]["id"] == original_id
        revisions = service.revision_history(original_id, allowed_target_keys=["paes"])["articles"]
        assert revisions[0]["reason"] == "publisher_correction"
        assert revisions[0]["previous"]["source_key"] == "google_news"
        assert revisions[0]["previous"]["metadata"] == {"original": "kept"}
    with service._connect() as conn:
        observation = conn.execute("SELECT source_key,observed_url,article_id FROM political_observations WHERE job_id=%s", (job["id"],)).fetchone()
        metadata = conn.execute("SELECT metadata FROM political_articles WHERE id=%s", (items[0]["id"],)).fetchone()["metadata"]
        persisted_task = conn.execute("SELECT source_key,payload FROM political_tasks WHERE id=%s", (task["id"],)).fetchone()
    assert observation == {"source_key": "google_news", "observed_url": candidate["url"], "article_id": items[0]["id"]}
    assert persisted_task["source_key"] == persisted_task["payload"]["source_key"] == "google_news"
    assert metadata["publisher_provenance"]["method"] == "resolved_fetch_registry"
    assert metadata["publisher_provenance"]["discovery_source_key"] == "google_news"


@pytest.mark.parametrize("source_key", ["manual", "legacy:Original newspaper"])
def test_cached_article_keeps_manual_or_legacy_publisher_without_a_confirmed_fetch(service, monkeypatch, source_key):
    url = "https://g1.globo.com/rj/fixture.ghtml"
    digest, key = service._store_text(BODY)
    with service._connect() as conn:
        article_id = service._persist_article(conn, {"url": url, "title": "Eduardo Paes", "source_key": source_key,
            "source_name": "Original newspaper"}, [{"target_key": "paes", "target_name": "Eduardo Paes", "keyword_matched": "Eduardo Paes"}],
            body_chars=len(BODY), digest=digest, object_key=key)
    start(service, monkeypatch, targets=("paes",))
    enqueue(service, monkeypatch, {"url": url, "title": "Eduardo Paes", "source_key": "google_news", "source_name": "Google News"})
    monkeypatch.setattr(service, "fetch", lambda *args, **kwargs: pytest.fail("cached body should not fetch"))
    assert service.process_task(service.claim_task("fetch", worker_id="cached"))["status"] == "duplicate"
    assert service.article(article_id, allowed_target_keys=["paes"])["sourceKey"] == source_key
    assert service.article(article_id, allowed_target_keys=["paes"])["sourceName"] == "Original newspaper"


def test_successful_discovery_pages_do_not_exhaust_retry_budget(service, monkeypatch):
    from web_app import political_discovery
    start(service, monkeypatch)
    monkeypatch.setattr(political_discovery, "discover", lambda task, fetch: {"candidates": [], "outcome": "continue",
        "raw_count": 1, "next_cursor": {"page": int(task["cursor"].get("page", 0)) + 1}, "child_tasks": []})
    for _ in range(8):
        task = service.claim_task("discovery", worker_id="d")
        assert task["attempts"] == 1
        service.process_task(task)
    task = service.claim_task("discovery", worker_id="d")
    assert task["cursor"]["page"] == 8
    monkeypatch.setattr(political_discovery, "discover", lambda *args: (_ for _ in ()).throw(political_discovery.DiscoveryError("limited", status_code=429)))
    assert service.process_task(task)["status"] == "retryable"


def test_killed_worker_process_leaves_committed_data_and_recoverable_task(service, monkeypatch):
    job = start(service, monkeypatch, targets=("paes",))
    script = '''
import os, time
from web_app.political_corpus import PoliticalCorpusService
s = PoliticalCorpusService(database_url=os.environ["POLITICAL_TEST_DATABASE_URL"])
t = s.claim_task("discovery", worker_id="doomed-process", lease_seconds=1)
with s._connect() as c:
    s._persist_article(c, {"url":"https://example.com/committed-before-kill", "title":"Eduardo Paes"},
        [{"target_key":"paes", "target_name":"Eduardo Paes", "keyword_matched":"Eduardo Paes"}])
print("committed", flush=True)
time.sleep(60)
'''
    process = subprocess.Popen([sys.executable, "-c", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            assert selector.select(timeout=10), "worker subprocess never committed"
            assert process.stdout.readline().strip() == "committed"
        process.kill()
        process.wait(timeout=5)
        assert process.returncode < 0
        assert len(service.list_articles(allowed_target_keys=["paes"])["items"]) == 1
        reclaimed = None
        deadline = time.monotonic() + 5
        while reclaimed is None and time.monotonic() < deadline:
            reclaimed = service.claim_task("discovery", worker_id="replacement-process")
            if reclaimed is None:
                time.sleep(0.1)
        assert reclaimed and reclaimed["job_id"] == job["id"]
        assert reclaimed["lease_owner"] == "replacement-process"
        with service._connect() as conn:
            service._finish(conn, reclaimed, "complete")
        assert service.status(job["id"], allowed_target_keys=["paes"])["current"]["status"] == "succeeded"
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=5)


@pytest.mark.parametrize("page_date,expected_status,expected_date", [
    ("2026-06-01T15:00:00Z", "retryable", "2026-06-01"),
    ("2026-06-03T15:00:00Z", "outside_window", None),
    ("", "retryable", None),
])
def test_metadata_only_preserves_verified_page_date_and_window(service, monkeypatch, page_date, expected_status, expected_date):
    start(service, monkeypatch)
    candidate = {"url": "https://example.com/limited-story", "title": "Eduardo Paes anuncia proposta",
                 "source_key": "example", "source_name": "Example", "snippet": "",
                 "published_at": "2026-06-02T12:00:00-03:00" if page_date else "", "metadata": {}}
    enqueue(service, monkeypatch, candidate)
    response = fake_response(candidate["url"], body="Conteúdo indisponível.")
    response._content = response._content.replace(b"2026-06-01T15:00:00Z", page_date.encode())
    monkeypatch.setattr(service, "fetch", lambda *args, **kwargs: response)
    result = service.process_task(service.claim_task("fetch", worker_id="date-check"))
    assert result["status"] == expected_status
    items = service.list_articles(allowed_target_keys=["paes"])["items"]
    if expected_status == "outside_window":
        assert items == []
    else:
        assert len(items) == 1 and items[0]["bodyStatus"] == "metadata_only"
        assert items[0]["dateStatus"] == ("page_verified" if expected_date else "unknown")
        assert (items[0]["publishedAt"][:10] if items[0]["publishedAt"] else None) == expected_date


@pytest.mark.parametrize("stage", ["landing", "resolver", "publisher_redirect"])
def test_google_challenge_is_unresolved_metadata_never_a_publisher_or_article(service, monkeypatch, stage):
    from web_app import political_discovery
    start(service, monkeypatch, targets=("paes",), tasks=[{"source_key": "google_news", "strategy": "google_news", "cursor": {}}])
    wrapper = "https://news.google.com/rss/articles/unresolved-public-story"
    challenge = "https://www.google.com/sorry/index?continue=https%3A%2F%2Fexample.com%2Fstory"
    publisher = "https://example.com/story"
    candidate = {"url": wrapper, "title": "Eduardo Paes anuncia proposta", "source_key": "google_news",
                 "source_name": "Google News", "published_at": "2026-06-01T12:00:00-03:00"}
    enqueue(service, monkeypatch, candidate)
    requests_made = []
    def fetch(url, **kwargs):
        requests_made.append(url)
        return fake_response(challenge if stage == "landing" or url == publisher else url)
    monkeypatch.setattr(service, "fetch", fetch)
    if stage != "landing":
        monkeypatch.setattr(political_discovery, "resolve_google_redirect", lambda *a, **k: challenge if stage == "resolver" else publisher)
    monkeypatch.setattr(political_discovery, "extract_article", lambda *a: pytest.fail("must never extract a Google challenge"))
    result = service.process_task(service.claim_task("fetch", worker_id="google-challenge"))
    assert result["status"] == "retryable" and result["errorType"] == "google_url_unresolved"
    assert len(requests_made) == (2 if stage == "publisher_redirect" else 1)
    items = service.list_articles(allowed_target_keys=["paes"])["items"]
    assert len(items) == 1 and items[0]["url"] == wrapper
    assert items[0]["sourceKey"] == "google_news" and items[0]["bodyStatus"] == "metadata_only"
    with service._connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM political_articles WHERE canonical_url LIKE '%%/sorry/%%'").fetchone()["n"] == 0
    assert service.store.objects == {}


def test_resolved_google_forbidden_publisher_is_terminal_and_metadata_only(service, monkeypatch):
    from web_app import political_discovery
    start(service, monkeypatch)
    candidate = {"url": "https://news.google.com/rss/articles/real-format-token", "title": "Eduardo Paes anuncia proposta",
                 "source_key": "google_news", "source_name": "Google News", "snippet": "",
                 "published_at": "2026-06-01T12:00:00-03:00", "metadata": {"google_redirect": True}}
    enqueue(service, monkeypatch, candidate)
    destination = "https://www.metropoles.com/brasil/reportagem"
    monkeypatch.setattr(political_discovery, "resolve_google_redirect", lambda *a, **k: destination)
    monkeypatch.setattr(service, "fetch", lambda url, **kwargs: fake_response(url, status=403 if url==destination else 200))
    result = service.process_task(service.claim_task("fetch", worker_id="google-publisher-check"))
    assert result["status"] == "gap" and "403" in result["errorType"]
    items = service.list_articles(allowed_target_keys=["paes"])["items"]
    assert len(items) == 1 and items[0]["bodyStatus"] == "metadata_only"
    assert items[0]["sourceKey"] == "metropoles" and items[0]["url"] == destination
    with service._connect() as conn:
        alias = conn.execute("SELECT article_id FROM political_url_aliases WHERE url=%s", (candidate["url"],)).fetchone()
    assert alias["article_id"] == items[0]["id"]


@pytest.mark.parametrize("wrapper_alias_already_points_to_canonical", [False, True])
def test_google_forbidden_publisher_alias_merges_wrapper_and_preserves_classification(
        service, monkeypatch, wrapper_alias_already_points_to_canonical):
    from web_app import political_discovery
    canonical = "https://www.metropoles.com/brasil/canonical-reportagem"
    publisher_alias = "https://www.metropoles.com/brasil/previous-reportagem"
    wrapper = "https://news.google.com/rss/articles/previously-unresolved-wrapper"
    hits = [{"target_key": "paes", "target_name": "Eduardo Paes", "keyword_matched": "Eduardo Paes"}]
    digest, object_key = service._store_text(BODY)
    with service._connect() as conn:
        # The destination is deliberately older: selecting only ORDER BY id
        # would miss the newer exact wrapper row when both claim its alias.
        canonical_id = service._persist_article(conn, {"url": canonical, "title": "Eduardo Paes anuncia proposta",
            "source_key": "metropoles", "source_name": "Metrópoles"}, hits,
            published=datetime(2026, 6, 1, 15, tzinfo=timezone.utc), date_status="page_verified",
            body_chars=len(BODY), digest=digest, object_key=object_key)
        wrapper_id = service._persist_article(conn, {"url": wrapper, "title": "Eduardo Paes anuncia proposta",
            "source_key": "google_news", "source_name": "Google News"}, hits)
        conn.execute("INSERT INTO political_url_aliases(url,article_id) VALUES (%s,%s)", (publisher_alias, canonical_id))
        if wrapper_alias_already_points_to_canonical:
            conn.execute("UPDATE political_url_aliases SET article_id=%s WHERE url=%s", (canonical_id, wrapper))
    service.upsert_classification(wrapper_id, {"targetKey": "paes", "target_sentiment": "negative"},
                                  allowed_target_keys=["paes"], updated_by="editor")
    job = start(service, monkeypatch, targets=("paes",))
    candidate = {"url": wrapper, "title": "Eduardo Paes anuncia proposta", "source_key": "google_news",
        "source_name": "Google News", "published_at": "2026-06-01T12:00:00-03:00",
        "force_refresh": True, "metadata": {"google_redirect": True}}
    enqueue(service, monkeypatch, candidate)
    monkeypatch.setattr(political_discovery, "resolve_google_redirect", lambda *a, **k: publisher_alias)
    monkeypatch.setattr(service, "fetch", lambda url, **kwargs: fake_response(url, status=403 if url == publisher_alias else 200))
    result = service.process_task(service.claim_task("fetch", worker_id="alias-merge-check"))
    assert result["status"] == "gap" and result["errorType"] == "http_403"
    articles = service.list_articles(allowed_target_keys=["paes"])["items"]
    assert len(articles) == 1 and articles[0]["id"] == canonical_id
    assert articles[0]["bodyStatus"] == "body_extracted"
    assert service.article_text(canonical_id, allowed_target_keys=["paes"])["text"] == BODY
    classification = service.classifications(canonical_id, allowed_target_keys=["paes"])["items"][0]
    assert classification["payload"]["target_sentiment"] == "negative"
    with service._connect() as conn:
        aliases = conn.execute("SELECT url,article_id FROM political_url_aliases WHERE url=ANY(%s)",
                               ([wrapper, publisher_alias, canonical],)).fetchall()
        observation = conn.execute("SELECT article_id,disposition FROM political_observations WHERE job_id=%s", (job["id"],)).fetchone()
        revision = conn.execute("SELECT previous FROM political_article_revisions WHERE article_id=%s AND reason='canonical_duplicate_merge'",
                                (canonical_id,)).fetchone()
        inserted = conn.execute("SELECT articles_inserted FROM political_jobs WHERE id=%s", (job["id"],)).fetchone()["articles_inserted"]
    assert {row["url"]: row["article_id"] for row in aliases} == dict.fromkeys([wrapper, publisher_alias, canonical], canonical_id)
    assert observation == {"article_id": canonical_id, "disposition": "metadata_only"}
    assert revision["previous"]["id"] == wrapper_id and inserted == 0


@pytest.mark.parametrize("canonical_already_exists", [False, True])
def test_google_body_missing_resolves_prior_wrapper_without_duplicate_or_lost_classification(
        service, monkeypatch, canonical_already_exists):
    from web_app import political_discovery
    canonical = "https://www.metropoles.com/brasil/resolved-short-body"
    wrapper = "https://news.google.com/rss/articles/short-body-original-wrapper"
    hits = [{"target_key": "paes", "target_name": "Eduardo Paes", "keyword_matched": "Eduardo Paes"}]
    with service._connect() as conn:
        canonical_id = None
        if canonical_already_exists:
            canonical_id = service._persist_article(conn, {"url": canonical, "title": "Eduardo Paes anuncia proposta",
                "source_key": "metropoles", "source_name": "Metrópoles"}, hits)
        wrapper_id = service._persist_article(conn, {"url": wrapper, "title": "Eduardo Paes anuncia proposta",
            "source_key": "google_news", "source_name": "Google News"}, hits,
            published=datetime(2026, 6, 2, 15, tzinfo=timezone.utc), date_status="source_reported")
    service.upsert_classification(wrapper_id, {"targetKey": "paes", "target_sentiment": "positive"},
                                  allowed_target_keys=["paes"], updated_by="editor")
    job = start(service, monkeypatch, targets=("paes",))
    enqueue(service, monkeypatch, {"url": wrapper, "title": "Eduardo Paes anuncia proposta",
        "source_key": "google_news", "source_name": "Google News", "published_at": "2026-06-02T15:00:00Z",
        "metadata": {"google_redirect": True, "query": '"Eduardo Paes"'}})
    monkeypatch.setattr(political_discovery, "resolve_google_redirect", lambda *a, **k: canonical)
    monkeypatch.setattr(service, "fetch", lambda url, **kwargs: fake_response(url, body="Conteúdo indisponível."))
    result = service.process_task(service.claim_task("fetch", worker_id="body-missing-merge-check"))
    assert result["status"] == "retryable" and result["errorType"] == "body_missing"
    expected_id = canonical_id if canonical_already_exists else wrapper_id
    items = service.list_articles(allowed_target_keys=["paes"])["items"]
    assert len(items) == 1 and items[0]["id"] == expected_id and items[0]["url"] == canonical
    assert items[0]["bodyStatus"] == "metadata_only" and items[0]["sourceKey"] == "metropoles"
    assert items[0]["dateStatus"] == "page_verified" and items[0]["publishedAt"].startswith("2026-06-01")
    classification = service.classifications(expected_id, allowed_target_keys=["paes"])["items"][0]
    assert classification["payload"]["target_sentiment"] == "positive"
    with service._connect() as conn:
        aliases = conn.execute("SELECT url,article_id FROM political_url_aliases WHERE url=ANY(%s)", ([wrapper, canonical],)).fetchall()
        observation = conn.execute("SELECT article_id,disposition,observed_url,metadata FROM political_observations WHERE job_id=%s", (job["id"],)).fetchone()
        reasons = conn.execute("SELECT reason,previous->>'id' old_id FROM political_article_revisions WHERE article_id=%s", (expected_id,)).fetchall()
        inserted = conn.execute("SELECT articles_inserted FROM political_jobs WHERE id=%s", (job["id"],)).fetchone()["articles_inserted"]
    assert {row["url"]: row["article_id"] for row in aliases} == dict.fromkeys([wrapper, canonical], expected_id)
    assert observation["article_id"] == expected_id and observation["disposition"] == "metadata_only"
    assert observation["observed_url"] == wrapper and observation["metadata"]["query"] == '"Eduardo Paes"'
    expected_reason = "canonical_duplicate_merge" if canonical_already_exists else "canonical_url_resolved"
    assert any(row["reason"] == expected_reason and row["old_id"] == str(wrapper_id) for row in reasons)
    assert inserted == 0


def test_failed_force_refresh_of_existing_alias_preserves_article_and_human_classification(service, monkeypatch):
    canonical, alias = "https://example.com/canonical-story", "https://example.com/old-story"
    digest, object_key = service._store_text(BODY)
    with service._connect() as conn:
        article_id = service._persist_article(conn, {"url": canonical, "title": "Eduardo Paes anuncia proposta",
            "source_key": "example", "source_name": "Example"},
            [{"target_key": "paes", "target_name": "Eduardo Paes", "keyword_matched": "Eduardo Paes"}],
            published=datetime(2026, 6, 1, 15, tzinfo=timezone.utc), date_status="page_verified",
            body_chars=len(BODY), digest=digest, object_key=object_key)
        conn.execute("INSERT INTO political_url_aliases(url,article_id) VALUES (%s,%s)", (alias, article_id))
    service.upsert_classification(article_id, {"targetKey": "paes", "target_sentiment": "positive"},
                                  allowed_target_keys=["paes"], updated_by="editor")
    job = start(service, monkeypatch, targets=("paes",))
    enqueue(service, monkeypatch, {"url": alias, "title": "Eduardo Paes anuncia proposta", "source_key": "example",
        "source_name": "Example", "published_at": "2026-06-02T12:00:00-03:00", "force_refresh": True})
    monkeypatch.setattr(service, "fetch", lambda url, **kwargs: fake_response(url, status=403))
    result = service.process_task(service.claim_task("fetch", worker_id="alias-refresh-check"))
    assert result["status"] == "gap" and result["errorType"] == "http_403"
    articles = service.list_articles(allowed_target_keys=["paes"])["items"]
    assert len(articles) == 1 and articles[0]["id"] == article_id and articles[0]["url"] == canonical
    assert articles[0]["publishedAt"][:10] == "2026-06-01" and articles[0]["dateStatus"] == "page_verified"
    assert service.article_text(article_id, allowed_target_keys=["paes"])["text"] == BODY
    assert service.classifications(article_id, allowed_target_keys=["paes"])["items"][0]["payload"]["target_sentiment"] == "positive"
    with service._connect() as conn:
        observation = conn.execute("SELECT article_id FROM political_observations WHERE job_id=%s", (job["id"],)).fetchone()
        inserted = conn.execute("SELECT articles_inserted FROM political_jobs WHERE id=%s", (job["id"],)).fetchone()["articles_inserted"]
    assert observation["article_id"] == article_id and inserted == 0


def test_retry_corrects_prior_metadata_date_and_detaches_outside_window_observation(service, monkeypatch):
    job=start(service, monkeypatch)
    candidate={"url":"https://example.com/reported-date", "title":"Eduardo Paes anuncia proposta",
               "source_key":"example", "published_at":"2026-06-01T12:00:00-03:00", "snippet":""}
    enqueue(service, monkeypatch, candidate)
    monkeypatch.setattr(service,"fetch",lambda url,**kwargs:fake_response(url,status=503))
    assert service.process_task(service.claim_task("fetch",worker_id="date-first"))["status"]=="retryable"
    article=service.list_articles(allowed_target_keys=["paes"])["items"][0]
    with service._connect() as conn:
        conn.execute("UPDATE political_tasks SET next_attempt_at=NULL WHERE job_id=%s AND kind='fetch'",(job["id"],))
    response=fake_response(candidate["url"],body="Conteúdo indisponível.")
    response._content=response._content.replace(b"2026-06-01T15:00:00Z",b"2026-06-03T15:00:00Z")
    monkeypatch.setattr(service,"fetch",lambda *args,**kwargs:response)
    assert service.process_task(service.claim_task("fetch",worker_id="date-second"))["status"]=="outside_window"
    corrected=service.article(article["id"],allowed_target_keys=["paes"])
    assert corrected["publishedAt"].startswith("2026-06-03") and corrected["dateStatus"]=="page_verified"
    assert service.list_articles(allowed_target_keys=["paes"],date_from="2026-06-01",date_to="2026-06-02")["items"]==[]
    with service._connect() as conn:
        observation=conn.execute("SELECT article_id,disposition FROM political_observations WHERE job_id=%s",(job["id"],)).fetchone()
        revision=conn.execute("SELECT reason FROM political_article_revisions WHERE article_id=%s",(article["id"],)).fetchone()
    assert observation=={"article_id":None,"disposition":"outside_window"}
    assert revision["reason"]=="publication_date_verification"


def test_object_upload_failure_keeps_verified_date_in_metadata_fallback(service, monkeypatch):
    start(service, monkeypatch)
    candidate={"url":"https://example.com/upload-date", "title":"Eduardo Paes anuncia proposta",
               "source_key":"example", "published_at":"2026-06-02T12:00:00-03:00", "snippet":""}
    enqueue(service,monkeypatch,candidate)
    monkeypatch.setattr(service,"fetch",lambda url,**kwargs:fake_response(url))
    monkeypatch.setattr(service.store,"upload_bytes",lambda *args,**kwargs:False)
    assert service.process_task(service.claim_task("fetch",worker_id="upload-date"))["status"]=="retryable"
    article=service.list_articles(allowed_target_keys=["paes"])["items"][0]
    assert article["bodyStatus"]=="metadata_only" and article["publishedAt"].startswith("2026-06-01")
    assert article["dateStatus"]=="page_verified"
