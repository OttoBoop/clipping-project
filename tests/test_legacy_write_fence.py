"""Cutover safety checks only: no ingestion, benchmark, or remote writes."""
import asyncio
from copy import deepcopy
import importlib
import json
import sqlite3
import threading
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from test_admin_viewers import login_and_csrf, reload_app


@pytest.fixture
def fenced_site(monkeypatch, tmp_path):
    monkeypatch.delenv("CLIPPING_LEGACY_WRITE_FENCE", raising=False)
    _, module, _, _ = reload_app(monkeypatch, tmp_path)
    admin = importlib.import_module("web_app.db_admin")
    admin.ensure_app_tables(module.db_path())
    monkeypatch.setenv("CLIPPING_LEGACY_WRITE_FENCE", "1")
    return module, admin, TestClient(module.app)


@pytest.mark.parametrize("method,path", [
    ("post", "/api/update/start"), ("post", "/api/update/resume"),
    ("post", "/api/export"), ("post", "/api/manual-story"),
    ("post", "/api/classifications"), ("post", "/api/categories"),
    ("post", "/api/targets"), ("post", "/api/targets/primary"),
    ("patch", "/api/targets/flavio_valle"), ("post", "/api/targets/flavio_valle/archive"),
    ("post", "/api/targets/flavio_valle/restore"), ("post", "/api/targets/flavio_valle/promote"),
    ("post", "/api/targets/flavio_valle/demote"), ("post", "/api/admin/viewers"),
    ("post", "/api/admin/debug/sqlite"), ("post", "/api/admin/targets/gc-smoke-residue"),
    ("post", "/api/admin/rio-economico/cleanup-urls"), ("post", "/api/change-password"),
])
def test_fence_rejects_legacy_http_mutations(fenced_site, method, path):
    module, _, client = fenced_site
    csrf = login_and_csrf(client, "test-password")
    response = getattr(client, method)(path, json={}, headers={"X-CSRF-Token": csrf})
    assert response.status_code == 503, response.text
    assert response.json()["detail"] == "legacy_write_fenced"
    assert module.legacy_writer_status()["activeLegacyWriters"] == 0


def test_authenticated_reads_and_login_do_not_change_legacy_data(fenced_site):
    module, admin, client = fenced_site
    rows = json.loads(admin.TARGETS_PATH.read_text())
    rows.append({"key": "smoke_fence_test", "label": "Smoke fence test", "keywords": ["Smoke fence test"],
                 "primary": False, "archived": False})
    admin.TARGETS_PATH.write_text(json.dumps(rows))
    before_targets = admin.TARGETS_PATH.read_bytes()
    before_db = module.db_path().read_bytes()
    csrf = login_and_csrf(client, "test-password")
    for path in ["/", "/healthz", "/api/targets?include_archived=true", "/api/categories", "/api/classifications", "/api/update/status"]:
        assert client.get(path).status_code == 200, path
    assert client.post("/api/logout", headers={"X-CSRF-Token": csrf}).status_code == 200
    assert admin.TARGETS_PATH.read_bytes() == before_targets
    assert module.db_path().read_bytes() == before_db
    with sqlite3.connect(module.db_path()) as conn:
        assert conn.execute("SELECT COUNT(*) FROM activity_log").fetchone()[0] == 0


def test_fenced_startup_restores_but_skips_every_normalization_write(fenced_site, monkeypatch):
    module, admin, _ = fenced_site
    restored = []
    def forbidden(*args, **kwargs):
        raise AssertionError("startup attempted a legacy write")
    monkeypatch.setattr(module, "artifact_store", SimpleNamespace(download_current_artifacts=lambda: restored.append("artifacts")))
    monkeypatch.setattr(module, "restore_remote_sqlite_if_local_empty", lambda: restored.append("sqlite") or {})
    for name in ["archive_known_test_targets", "normalize_targets_file", "ensure_app_tables", "mark_orphaned_active_jobs_interrupted", "ClippingDB"]:
        monkeypatch.setattr(module, name, forbidden)
    monkeypatch.setattr(admin, "merge_political_roster", forbidden)
    monkeypatch.setattr(module.activity, "purge_older_than", forbidden)
    monkeypatch.setattr(module.job_manager, "resume_startup_jobs", forbidden)
    monkeypatch.setenv("CLIPPING_AUTO_RESUME_JOBS", "1")
    async def run():
        async with module.lifespan(module.app):
            assert restored == ["artifacts", "sqlite"]
    asyncio.run(run())


def test_job_manager_and_direct_helpers_refuse_new_legacy_work(fenced_site, monkeypatch):
    module, admin, _ = fenced_site
    jobs = importlib.import_module("web_app.jobs")
    manager = jobs.JobManager(SimpleNamespace(writes_available=True))
    calls = [lambda: manager.start_update({}, started_by="test"),
             lambda: manager.resume_update("legacy", started_by="test"),
             lambda: manager.start_export(started_by="test"),
             lambda: manager.record_completed_manual(result={}, uploaded=[], started_by="test"),
             lambda: jobs.record_target_sync("flavio_valle", reason="test"),
             lambda: jobs.run_export_snapshot(),
             lambda: jobs.backfill_all_target_mentions(module.db_path(), ["flavio_valle"]),
             lambda: admin.write_targets_atomic([])]
    def forbidden(*args, **kwargs):
        raise AssertionError("fenced writer accessed persistence")
    monkeypatch.setattr(jobs, "ensure_app_tables", forbidden)
    monkeypatch.setattr(jobs, "build_update_spec", forbidden)
    for call in calls:
        with pytest.raises(RuntimeError, match="legacy_write_fenced"):
            call()
    assert manager.resume_startup_jobs() == 0
    assert manager.writer_status()["jobManagerThreadsAlive"] == 0


def test_cancelled_job_remains_an_active_writer_until_thread_exits(fenced_site, monkeypatch):
    _, _, _ = fenced_site
    jobs = importlib.import_module("web_app.jobs")
    manager = jobs.JobManager(SimpleNamespace(writes_available=True))
    started, finish, cancel = threading.Event(), threading.Event(), threading.Event()
    job = {"id": "legacy-drain", "status": "running"}
    def writer():
        started.set()
        finish.wait(5)
    thread = threading.Thread(target=writer, name="drain-safety-test")
    manager._threads[job["id"]] = thread
    manager._cancel_events[job["id"]] = cancel
    manager._active_job_id = job["id"]
    monkeypatch.setattr(jobs, "get_job", lambda *_: deepcopy(job))
    monkeypatch.setattr(jobs, "update_job", lambda _, **values: job.update(values))
    monkeypatch.setattr(jobs, "append_event", lambda *args: None)
    thread.start()
    try:
        assert started.wait(1)
        assert manager.cancel_active()["status"] == "cancelled"
        assert cancel.is_set()
        status = manager.writer_status()
        assert status["jobManagerThreadsAlive"] == 1
        assert status["cancelRequestedJobIds"] == [job["id"]]
    finally:
        finish.set()
        thread.join(timeout=2)
    assert manager.writer_status()["jobManagerThreadsAlive"] == 0


def test_fence_keeps_pg_routes_and_shared_political_dispatch_available(fenced_site, monkeypatch):
    module, _, client = fenced_site
    csrf = login_and_csrf(client, "test-password")
    calls = []
    async def political_start(request):
        module.political_routes.access(request, mutation=True, admin=True)
        calls.append("political")
        return {"accepted": True}
    monkeypatch.setattr(module.political_routes, "start", political_start)
    # Shared compatibility route must dispatch before the legacy fence.
    response = client.post("/api/update/start", json={"scope": module.political_routes.SCOPE}, headers={"X-CSRF-Token": csrf})
    assert response.status_code == 200 and calls == ["political"]
    # Direct route uses its registered handler; replace only persistence.
    monkeypatch.setattr(module.political_routes.political_corpus, "start_job", lambda *args, **kwargs: {"accepted": True})
    response = client.post("/api/political/jobs", json={"target_keys": ["flavio_valle"]}, headers={"X-CSRF-Token": csrf})
    assert response.status_code == 200
    assert client.get("/api/political/meta").status_code == 200
    assert module.legacy_writer_status()["activeLegacyWriters"] == 0


def test_fence_defaults_off_and_status_is_explicitly_process_local(fenced_site, monkeypatch):
    module, _, _ = fenced_site
    monkeypatch.delenv("CLIPPING_LEGACY_WRITE_FENCE")
    module.legacy_fence.require_legacy_writes()
    module.legacy_fence.begin_request()
    try:
        status = module.legacy_writer_status()
        assert status["enabled"] is False
        assert status["scope"] == "this_web_process_only" and status["processId"] > 0
        assert status["inFlightLegacyMutationRequests"] == status["activeLegacyWriters"] == 1
    finally:
        module.legacy_fence.end_request()
