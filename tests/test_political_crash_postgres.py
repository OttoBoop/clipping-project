"""Exercise real process death and PostgreSQL transaction rollback at save boundaries."""
import os
import selectors
import subprocess
import sys

import pytest

from test_political_corpus_postgres import DATABASE_URL, enqueue, fake_response, service, start

pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="Disposable POLITICAL_TEST_DATABASE_URL required")


@pytest.mark.parametrize("stage", ["fetch", "transaction"])
def test_sigkill_during_fetch_or_uncommitted_save_recovers_without_partial_records(service, monkeypatch, stage):
    job = start(service, monkeypatch)
    enqueue(service, monkeypatch)
    with service._connect() as conn:
        committed_id = service._persist_article(conn, {"url": "https://example.com/older-saved", "title": "Eduardo Paes"},
            [{"target_key": "paes", "target_name": "Eduardo Paes", "keyword_matched": "Eduardo Paes"}])
    script = '''
import os, signal, sys
sys.path.insert(0, "tests")
from test_political_corpus_postgres import MemoryStore, fake_response
from web_app.political_corpus import PoliticalCorpusService
s = PoliticalCorpusService(store=MemoryStore(), database_url=os.environ["POLITICAL_TEST_DATABASE_URL"])
task = s.claim_task("fetch", worker_id="doomed-fetch")
def pause():
    print("at-boundary", flush=True)
    signal.pause()
if os.environ["POLITICAL_CRASH_STAGE"] == "fetch":
    def fetch(url, **kwargs):
        pause()
        return fake_response(url)
    s.fetch = fetch
else:
    s.fetch = fake_response
    finish = s._finish
    def before_commit(conn, task, status, **kwargs):
        pause()
        return finish(conn, task, status, **kwargs)
    s._finish = before_commit
s.process_task(task)
'''
    process = subprocess.Popen([sys.executable, "-c", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, env={**os.environ, "POLITICAL_CRASH_STAGE": stage})
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            assert selector.select(timeout=10), "worker did not reach the selected failure boundary"
            assert process.stdout.readline().strip() == "at-boundary"
        # An unrelated reader sees committed data only, even while a save is open.
        assert [r["id"] for r in service.list_articles(allowed_target_keys=["paes"])["items"]] == [committed_id]
        process.kill()
        process.wait(timeout=5)
        assert process.returncode < 0
        with service._connect() as conn:
            assert conn.execute("SELECT COUNT(*) AS n FROM political_articles").fetchone()["n"] == 1
            assert conn.execute("SELECT COUNT(*) AS n FROM political_mentions").fetchone()["n"] == 1
            assert conn.execute("SELECT COUNT(*) AS n FROM political_story_articles").fetchone()["n"] == 1
            assert conn.execute("SELECT articles_inserted FROM political_jobs WHERE id=%s", (job["id"],)).fetchone()["articles_inserted"] == 0
            conn.execute("UPDATE political_tasks SET leased_until=NOW()-INTERVAL '1 second' WHERE kind='fetch'")
        replacement = service.claim_task("fetch", worker_id="replacement")
        assert replacement and replacement["lease_owner"] == "replacement"
        monkeypatch.setattr(service, "fetch", fake_response)
        assert service.process_task(replacement)["status"] == "saved"
        assert len(service.list_articles(allowed_target_keys=["paes"])["items"]) == 2
        status = service.status(job["id"], allowed_target_keys=["paes", "duarte"])["current"]
        assert status["status"] == "succeeded"
        assert status["metrics"]["articlesInserted"] == 1
        assert status["metrics"]["mentionsInserted"] == 2
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=5)


def test_database_error_rolls_back_article_and_healthy_source_continues(service, monkeypatch):
    job = start(service, monkeypatch)
    enqueue(service, monkeypatch)
    with service._connect() as conn:
        service._insert_task(conn, job["id"], "fetch", {"url": "https://healthy.example.com/story", "source_key": "healthy"})
    monkeypatch.setattr(service, "fetch", fake_response)
    broken = service.claim_task("fetch", worker_id="first")
    finish = service._finish

    def fail_one_commit(conn, task, status, **kwargs):
        if task["id"] == broken["id"] and status == "complete":
            conn.execute("SELECT 1 / 0")
        return finish(conn, task, status, **kwargs)

    monkeypatch.setattr(service, "_finish", fail_one_commit)
    assert service.process_task(broken)["status"] == "retryable"
    assert service.list_articles(allowed_target_keys=["paes"])["items"] == []
    healthy = service.claim_task("fetch", worker_id="healthy")
    assert healthy["source_key"] == "healthy"
    assert service.process_task(healthy)["status"] == "saved"
    with service._connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM political_mentions").fetchone()["n"] == 2
        conn.execute("UPDATE political_tasks SET next_attempt_at=NULL WHERE id=%s", (broken["id"],))
    monkeypatch.setattr(service, "_finish", finish)
    assert service.process_task(service.claim_task("fetch", worker_id="retry"))["status"] == "saved"
    assert len(service.list_articles(allowed_target_keys=["paes"])["items"]) == 2
