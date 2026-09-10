"""PSD integration: real auth/config files, with no collection or archive backfill."""
from __future__ import annotations

import importlib
import json

from fastapi.testclient import TestClient
import pytest

from test_admin_viewers import login_and_csrf, reload_app
from test_political_routes import FakePoliticalCorpus

PSD = "psd_rj_2026"


def test_approved_35_presets_and_incremental_scope_preserve_clients(psd_site):
    client, app, auth, segmentation, service, _, uploads, full_uploads, syncs = psd_site
    from pathlib import Path
    admin = importlib.import_module("web_app.db_admin")
    root = Path(__file__).resolve().parents[1]
    seed = json.loads((root / "data/psd_rj_2026_profile.json").read_text())
    manifest = json.loads((root / "data/political_targets_v1.json").read_text())
    rows = json.loads(admin.TARGETS_PATH.read_text())
    existing = {r["key"] for r in rows}
    rows.extend(r for r in manifest["targets"] if r["key"] not in existing)
    admin.TARGETS_PATH.write_text(json.dumps(rows))
    others_before = {k: v for k, v in segmentation.viewer_profiles().items() if k != PSD}
    csrf = login_and_csrf(client, "test-password")
    response = client.patch(f"/api/admin/viewers/{PSD}", headers={"X-CSRF-Token": csrf}, json={
        "target_keys": seed["target_keys"], "default_targets": seed["target_keys"],
    })
    assert response.status_code == 200
    meta = client.get(f"/api/political/meta?client={PSD}").json()
    assert len(meta["targets"]) == 35 and len(meta["newDiscoveryTargets"]) == 11
    assert [len(p["target_keys"]) for p in meta["selectionPresets"]] == [24, 5, 8]
    response = client.post(f"/api/political/jobs?client={PSD}", headers={"X-CSRF-Token": csrf}, json={
        "target_keys": seed["target_keys"], "discovery_target_keys": seed["new_target_keys"],
    })
    assert response.status_code == 200
    call = next(c for c in service.calls if c["method"] == "start_job")
    assert len(call["payload"]["target_snapshots"]) == 35
    assert call["payload"]["discovery_target_keys"] == seed["new_target_keys"]
    assert {k: v for k, v in segmentation.viewer_profiles().items() if k != PSD} == others_before
    assert auth.login_identity("psd-test-password")["profile"] == PSD
    assert not full_uploads and not syncs


@pytest.fixture
def psd_site(monkeypatch, tmp_path):
    monkeypatch.setenv("CLIPPING_LEGACY_WRITE_FENCE", "0")
    monkeypatch.setenv("POLITICAL_DASHBOARD_DEFAULT", "0")
    auth, app, profiles_path, credentials_path = reload_app(monkeypatch, tmp_path)
    admin = importlib.import_module("web_app.db_admin")
    segmentation = importlib.import_module("web_app.segmentation")
    routes = importlib.import_module("web_app.political_routes")
    rows = json.loads(admin.TARGETS_PATH.read_text())
    keys = [f"psd_person_{i}" for i in range(24)]
    rows.extend({"key": key, "label": f"Pessoa PSD {i}", "display_name": f"Pessoa PSD {i}",
                 "keywords": [f"Pessoa PSD {i}"], "primary": False} for i, key in enumerate(keys))
    admin.TARGETS_PATH.write_text(json.dumps(rows))
    service = FakePoliticalCorpus()
    monkeypatch.setattr(app, "political_corpus", service)
    monkeypatch.setattr(routes, "political_corpus", service)
    uploads = []
    full_uploads = []
    monkeypatch.setattr(app.artifact_store, "enabled", True)
    monkeypatch.setattr(app.artifact_store, "upload_file", lambda path, remote: uploads.append((str(path), remote)) or True)
    monkeypatch.setattr(app.artifact_store, "upload_bytes", lambda *args: True)
    monkeypatch.setattr(app.artifact_store, "upload_current_artifacts", lambda **kw: full_uploads.append(kw) or [])
    monkeypatch.setattr(app.artifact_store, "upload_sqlite_snapshot", lambda *a: pytest.fail("PSD must not upload the archive"))
    syncs = []
    monkeypatch.setattr(app, "record_target_sync", lambda *a, **kw: syncs.append((a, kw)) or {"updatedCount": 0})
    client = TestClient(app.app)
    csrf = login_and_csrf(client, "test-password")
    response = client.post("/api/admin/viewers", headers={"X-CSRF-Token": csrf}, json={
        "profile": PSD, "label": "PSD RJ 2026", "password": "psd-test-password", "target_keys": keys})
    assert response.status_code == 200, response.text
    return client, app, auth, segmentation, service, keys, uploads, full_uploads, syncs


def test_psd_creation_defaults_and_landing_preserve_other_clients(psd_site):
    client, app, auth, segmentation, service, keys, uploads, full_uploads, syncs = psd_site
    assert {remote.split("/current/")[-1] for _, remote in uploads} == {
        "data/targets.json", "data/viewer_profiles.json", "data/clipping_credentials.json"}
    assert full_uploads == []
    assert segmentation.viewer_profiles()[PSD]["default_targets"] == keys
    csrf = login_and_csrf(client, "psd-test-password")
    landing = client.get("/", follow_redirects=False)
    assert landing.status_code == 307 and landing.headers["location"] == "/politica"
    meta = client.get("/api/political/meta").json()
    assert meta["defaultTargets"] == keys
    assert {row["key"] for row in meta["targets"]} == set(keys)
    assert meta["canRun"] is False
    assert client.get("/?view=legacy").status_code == 200
    assert client.get("/api/admin/viewers").status_code == 401
    login_and_csrf(client, "viewer-flavio")
    assert client.get("/", follow_redirects=False).status_code == 200
    assert syncs == []


def test_psd_manages_names_without_archive_sync_and_custom_names_are_political(psd_site):
    client, app, auth, segmentation, service, keys, uploads, full_uploads, syncs = psd_site
    csrf = login_and_csrf(client, "psd-test-password")
    headers = {"X-CSRF-Token": csrf}
    created = client.post("/api/targets", headers=headers, json={"display_name": "Nova Pessoa PSD", "keywords": ["Nova Pessoa PSD"]})
    assert created.status_code == 200, created.text
    key = created.json()["key"]
    assert created.json()["futureCollectionOnly"] is True
    assert key in segmentation.psd_target_keys()
    assert key in {row["key"] for row in client.get("/api/political/meta").json()["targets"]}
    for method, suffix, body in [
        ("patch", "", {"display_name": "Nova Pessoa PSD Atualizada"}),
        ("post", "/promote", {}), ("post", "/demote", {}),
        ("post", "/archive", {"reason": "Teste"}), ("post", "/restore", {})]:
        response = getattr(client, method)(f"/api/targets/{key}{suffix}", headers=headers, json=body)
        assert response.status_code == 200, response.text
        assert response.json()["futureCollectionOnly"] is True
    primary = client.post("/api/targets/primary", headers=headers, json={"display_name": "Outra Pessoa PSD"})
    assert primary.status_code == 200, primary.text
    denied = client.patch("/api/targets/shakira", headers=headers, json={"display_name": "Nao permitida"})
    assert denied.status_code == 403
    assert syncs == []
    assert full_uploads == []


def test_admin_operating_context_limits_job_to_psd_without_simulation(psd_site):
    client, app, auth, segmentation, service, keys, uploads, full_uploads, syncs = psd_site
    csrf = login_and_csrf(client, "test-password")
    meta = client.get(f"/api/political/meta?client={PSD}").json()
    assert meta["canRun"] is True and meta["defaultTargets"] == keys
    assert {row["key"] for row in meta["targets"]} == set(keys)
    payload = {"kind": "collect", "target_keys": keys, "date_from": "2026-06-01", "date_to": "2026-06-02"}
    response = client.post(f"/api/political/jobs?client={PSD}", headers={"X-CSRF-Token": csrf}, json=payload)
    assert response.status_code == 200, response.text
    call = next(c for c in service.calls if c["method"] == "start_job")
    assert set(call["allowed_target_keys"]) == set(keys)
    assert call["started_by"] == "admin"
    assert {row["key"] for row in call["payload"]["target_snapshots"]} == set(keys)
    response = client.post(f"/api/political/jobs?client={PSD}", headers={"X-CSRF-Token": csrf}, json={**payload, "target_keys": ["flavio_valle"]})
    assert response.status_code == 400
    assert client.post(f"/api/political/jobs?as_profile={PSD}", headers={"X-CSRF-Token": csrf}, json=payload).status_code == 403
    csrf = login_and_csrf(client, "psd-test-password")
    assert client.get(f"/api/political/meta?client={PSD}").status_code == 403
    assert client.post("/api/political/jobs", headers={"X-CSRF-Token": csrf}, json=payload).status_code == 401


def test_psd_password_changes_and_admin_edits_upload_only_configuration(psd_site, monkeypatch):
    client, app, auth, segmentation, service, keys, uploads, full_uploads, syncs = psd_site
    csrf = login_and_csrf(client, "psd-test-password")
    response = client.post("/api/change-password", headers={"X-CSRF-Token": csrf}, json={"old_password": "psd-test-password", "new_password": "psd-new-test-password"})
    assert response.status_code == 200, response.text
    login_and_csrf(client, "psd-new-test-password")
    csrf = login_and_csrf(client, "test-password")
    response = client.patch(f"/api/admin/viewers/{PSD}", headers={"X-CSRF-Token": csrf}, json={"label": "PSD Rio", "default_targets": keys[:3]})
    assert response.status_code == 200, response.text
    csrf = login_and_csrf(client, "psd-new-test-password")
    assert client.get("/api/political/meta").json()["defaultTargets"] == keys[:3]
    monkeypatch.setattr(app.artifact_store, "upload_file", lambda *args: False)
    response = client.post("/api/change-password", headers={"X-CSRF-Token": csrf}, json={"old_password": "psd-new-test-password", "new_password": "not-persisted"})
    assert response.status_code == 503
    assert auth.login_identity("psd-new-test-password")["profile"] == PSD
    assert full_uploads == []


def test_other_client_target_and_account_behavior_is_preserved(psd_site):
    client, app, auth, segmentation, service, keys, uploads, full_uploads, syncs = psd_site
    csrf = login_and_csrf(client, "viewer-flavio")
    response = client.post("/api/targets", headers={"X-CSRF-Token": csrf}, json={"display_name": "Pessoa Cliente Anterior"})
    assert response.status_code == 200, response.text
    assert "futureCollectionOnly" not in response.json()
    assert len(syncs) == 1 and len(full_uploads) == 1
    csrf = login_and_csrf(client, "test-password")
    response = client.patch("/api/admin/viewers/flavio", headers={"X-CSRF-Token": csrf}, json={"label": "Flavio atualizado"})
    assert response.status_code == 200
    assert len(full_uploads) == 2


def test_psd_configuration_backup_failure_is_not_reported_as_success(psd_site, monkeypatch):
    client, app, auth, segmentation, service, keys, uploads, full_uploads, syncs = psd_site
    csrf = login_and_csrf(client, "test-password")
    monkeypatch.setattr(app.artifact_store, "upload_file", lambda *args: False)
    response = client.patch(f"/api/admin/viewers/{PSD}", headers={"X-CSRF-Token": csrf}, json={"label": "PSD backup pendente"})
    assert response.status_code == 503
    assert response.json()["error"] == "profile_configuration_not_persisted"
    assert full_uploads == []


def test_admin_simulation_offers_authenticated_psd_collection_shortcut(psd_site):
    client, app, auth, segmentation, service, keys, uploads, full_uploads, syncs = psd_site
    login_and_csrf(client, "test-password")
    meta = client.get(f"/api/political/meta?as_profile={PSD}").json()
    assert meta["canRun"] is False
    assert meta["psdClientAvailable"] is True
    page = client.get(f"/politica?as_profile={PSD}").text
    assert 'href="/politica?client=psd_rj_2026"' in page
    assert 'id="manage-account"' in page
