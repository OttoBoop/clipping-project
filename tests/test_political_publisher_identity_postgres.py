"""Preserve legacy identities when publisher host aliases are rediscovered."""
from datetime import datetime, timezone

import pytest

from test_political_corpus_postgres import DATABASE_URL, BODY, service, start, enqueue, fake_response
from web_app import political_corpus, political_discovery

pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="Requires disposable PostgreSQL")
WWW = "https://www.diariodorio.com/politica/2026/06/story.html"
BARE = WWW.replace("www.", "", 1)
GOOGLE = "https://news.google.com/rss/articles/new-wrapper"
DAY = datetime(2026, 6, 1, 15, tzinfo=timezone.utc)


def save(service, conn, url, target, body=BODY):
    digest, key = service._store_text(body)
    return service._persist_article(conn, {"url": url, "title": "Encontro político",
        "source_key": "diario_do_rio", "source_name": "Diário do Rio"},
        [{"target_key": target, "target_name": target, "keyword_matched": target}],
        published=DAY, date_status="page_verified", body_chars=len(body), digest=digest, object_key=key)


@pytest.mark.parametrize("origin", [BARE, GOOGLE])
def test_new_host_or_google_wrapper_reuses_legacy_text_and_identifier(service, monkeypatch, origin):
    with service._connect() as conn:
        old_id = save(service, conn, WWW, "paes")
        conn.execute("DELETE FROM political_url_aliases WHERE url=%s", (BARE,))
    start(service, monkeypatch, targets=("duarte",))
    enqueue(service, monkeypatch, {"url": origin, "title": "Encontro político",
        "source_key": "google_news" if origin == GOOGLE else "diario_do_rio", "metadata": {}})
    calls = []
    def fetch(url):
        calls.append(url)
        assert url == GOOGLE, "Stored publisher text must not be fetched again"
        return fake_response(GOOGLE, body="")
    monkeypatch.setattr(service, "fetch", fetch)
    monkeypatch.setattr(political_discovery, "resolve_google_redirect", lambda *a, **k: BARE)
    task = service.claim_task("fetch", worker_id="identity")
    result = service.process_task(task)
    assert result["articleId"] == old_id
    assert result["bodyOrigin"] == "saved_object"
    assert calls == ([GOOGLE] if origin == GOOGLE else [])
    with service._connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM political_articles").fetchone()["n"] == 1
        assert conn.execute("SELECT canonical_url FROM political_articles WHERE id=%s", (old_id,)).fetchone()["canonical_url"] == WWW
        assert conn.execute("SELECT COUNT(*) AS n FROM political_mentions").fetchone()["n"] == 2
        for url in (WWW, BARE, origin):
            assert conn.execute("SELECT article_id FROM political_url_aliases WHERE url=%s", (url,)).fetchone()["article_id"] == old_id
        if origin == GOOGLE:
            assert conn.execute("SELECT cursor FROM political_tasks WHERE id=%s", (task["id"],)).fetchone()["cursor"]["resolved_url"] == BARE


def test_existing_host_duplicates_merge_into_old_id_and_keep_times_text_and_classifications(service, monkeypatch):
    with monkeypatch.context() as legacy:
        legacy.setattr(political_corpus, "publisher_article_identity_urls", lambda url: (url,))
        with service._connect() as conn:
            old_id = save(service, conn, WWW, "paes")
            duplicate_id = save(service, conn, BARE, "duarte", BODY + " Mais detalhes publicados.")
            conn.execute("UPDATE political_mentions SET created_at=%s", (DAY,))
            duplicate = conn.execute("SELECT * FROM political_articles WHERE id=%s", (duplicate_id,)).fetchone()
    service.upsert_classification(old_id, {"targetKey": "paes", "target_sentiment": "negative"},
        allowed_target_keys=["paes"], updated_by="editor")
    service.upsert_classification(duplicate_id, {"targetKey": "duarte", "target_sentiment": "positive"},
        allowed_target_keys=["duarte"], updated_by="editor")
    with service._connect() as conn:
        kept = service._persist_article(conn, {"url": BARE, "title": duplicate["title"],
            "source_key": "diario_do_rio", "source_name": "Diário do Rio"}, [],
            published=DAY, date_status="page_verified", body_chars=duplicate["body_chars"],
            digest=duplicate["content_hash"], object_key=duplicate["text_object_key"])
        assert kept == old_id
        assert conn.execute("SELECT COUNT(*) AS n FROM political_articles").fetchone()["n"] == 1
        mentions = conn.execute("SELECT target_key,created_at FROM political_mentions ORDER BY target_key").fetchall()
        assert [r["target_key"] for r in mentions] == ["duarte", "paes"]
        assert all(r["created_at"] == DAY for r in mentions)
        assert conn.execute("SELECT COUNT(*) AS n FROM political_article_revisions WHERE reason='canonical_duplicate_merge'").fetchone()["n"] == 1
    assert service.article_text(old_id, allowed_target_keys=["duarte"])["text"].endswith("Mais detalhes publicados.")
    classifications = service.classifications(old_id, allowed_target_keys=["paes", "duarte"])["items"]
    assert {r["payload"]["target_sentiment"] for r in classifications} == {"negative", "positive"}
