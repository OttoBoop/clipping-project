"""Tests for the activity log capture + GET /api/admin/activity endpoint.

Covers Goal 1 (admin onboarding) + Goal 4 (regressão-zero) — activity
logging never blocks the operation, and is admin-only to read."""

from __future__ import annotations

import importlib
import json
import sys

from fastapi.testclient import TestClient

from pipeline.database import ClippingDB


def reload_app(monkeypatch, tmp_path):
    db_file = tmp_path / "clipping.db"
    ClippingDB(db_file)
    monkeypatch.setenv("CLIPPING_DB_PATH", str(db_file))
    monkeypatch.setenv("CLIPPING_ADMIN_PASSWORD", "test-pass")
    monkeypatch.setenv("CLIPPING_SESSION_SECRET", "test-secret")
    monkeypatch.setenv(
        "CLIPPING_VIEWER_PASSWORDS",
        json.dumps({"flavio": "v-flavio"}),
    )
    monkeypatch.setenv("CLIPPING_ALLOW_LOCAL_WRITES", "1")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
    monkeypatch.delenv("CLIPPING_VIEWER_PROFILES", raising=False)

    profiles_path = tmp_path / "viewer_profiles.json"
    profiles_path.write_text(
        json.dumps({"profiles": {"flavio": {"label": "Flavio", "target_keys": ["flavio_valle"], "default_targets": ["flavio_valle"]}}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("CLIPPING_VIEWER_PROFILES_PATH", str(profiles_path))

    for name in list(sys.modules):
        if name == "web_app" or name.startswith("web_app."):
            del sys.modules[name]
    auth = importlib.import_module("web_app.auth")
    config = importlib.import_module("web_app.config")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(auth, "CREDENTIALS_PATH", tmp_path / "clipping_credentials.json")
    db_admin = importlib.import_module("web_app.db_admin")
    db_admin.ensure_app_tables(db_file)  # create activity_log + others
    app_module = importlib.import_module("web_app.app")
    return app_module


def test_login_success_records_activity(monkeypatch, tmp_path):
    app_module = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    client.post("/api/login", json={"password": "test-pass"})
    # Read activity as admin
    rows = client.get("/api/admin/activity").json()["activity"]
    actions = [r["action"] for r in rows]
    assert "login.success" in actions
    login_row = next(r for r in rows if r["action"] == "login.success")
    assert login_row["userRole"] == "admin"
    assert login_row["userProfile"] == "admin"


def test_login_failure_records_activity(monkeypatch, tmp_path):
    app_module = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    resp = client.post("/api/login", json={"password": "wrong"})
    assert resp.status_code == 401
    # Log admin in to read activity
    client.post("/api/login", json={"password": "test-pass"})
    rows = client.get("/api/admin/activity").json()["activity"]
    actions = [r["action"] for r in rows]
    assert "login.fail" in actions
    fail_row = next(r for r in rows if r["action"] == "login.fail")
    assert fail_row["userRole"] == "anonymous"


def test_viewer_creates_target_emits_activity(monkeypatch, tmp_path):
    app_module = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    client.post("/api/login", json={"password": "v-flavio"})
    csrf = client.get("/api/csrf").json()["csrf"]
    # Seed minimal targets.json so create_secondary_target can run
    db_admin = importlib.import_module("web_app.db_admin")
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps([{"key": "flavio_valle", "label": "Flavio Valle", "display_name": "Flavio Valle", "primary": False, "className": "", "keywords": ["x"]}]),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)
    resp = client.post(
        "/api/targets",
        headers={"X-CSRF-Token": csrf},
        json={"display_name": "Audit Created", "keywords": ["a"]},
    )
    assert resp.status_code == 200, resp.text

    # Switch to admin and read activity
    client.post("/api/logout", headers={"X-CSRF-Token": csrf})
    client.post("/api/login", json={"password": "test-pass"})
    rows = client.get("/api/admin/activity").json()["activity"]
    actions = [r["action"] for r in rows]
    assert "target.create" in actions
    create_row = next(r for r in rows if r["action"] == "target.create")
    assert create_row["userRole"] == "viewer"
    assert create_row["userProfile"] == "flavio"
    assert create_row["targetKey"]
    assert create_row["details"]["assignedTo"] == "flavio"


def test_activity_endpoint_requires_admin(monkeypatch, tmp_path):
    app_module = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    # Anonymous
    resp = client.get("/api/admin/activity")
    assert resp.status_code == 401
    # Viewer
    client.post("/api/login", json={"password": "v-flavio"})
    resp = client.get("/api/admin/activity")
    assert resp.status_code == 401
    assert "admin_login_required" in resp.text


def test_activity_filter_by_action_prefix(monkeypatch, tmp_path):
    app_module = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    # Generate mixed events
    client.post("/api/login", json={"password": "wrong"})  # login.fail
    client.post("/api/login", json={"password": "v-flavio"})  # login.success viewer
    csrf_v = client.get("/api/csrf").json()["csrf"]
    client.post("/api/logout", headers={"X-CSRF-Token": csrf_v})  # logout viewer
    client.post("/api/login", json={"password": "test-pass"})  # login.success admin
    rows = client.get("/api/admin/activity?action=login.").json()["activity"]
    actions = [r["action"] for r in rows]
    assert all(a.startswith("login.") for a in actions)
    assert "login.fail" in actions
    assert "login.success" in actions
    assert "logout" not in actions


def test_activity_filter_by_profile(monkeypatch, tmp_path):
    app_module = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    client.post("/api/login", json={"password": "v-flavio"})
    csrf = client.get("/api/csrf").json()["csrf"]
    client.post("/api/logout", headers={"X-CSRF-Token": csrf})
    client.post("/api/login", json={"password": "test-pass"})
    rows = client.get("/api/admin/activity?profile=flavio").json()["activity"]
    # All rows mention flavio either as user_profile or target_key
    for r in rows:
        assert r["userProfile"] == "flavio" or r["targetKey"] == "flavio"
