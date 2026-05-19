from __future__ import annotations

import importlib
import json
import sys

from fastapi.testclient import TestClient

from pipeline.database import ClippingDB


def reload_app(monkeypatch, tmp_path, *, admin_password="test-password", session_secret="test-session-secret"):
    db_file = tmp_path / "clipping.db"
    ClippingDB(db_file)
    monkeypatch.setenv("CLIPPING_DB_PATH", str(db_file))
    monkeypatch.setenv("CLIPPING_ADMIN_PASSWORD", admin_password)
    monkeypatch.setenv("CLIPPING_SESSION_SECRET", session_secret)
    monkeypatch.setenv(
        "CLIPPING_VIEWER_PASSWORDS",
        json.dumps({"flavio": "viewer-flavio", "shakira": "viewer-shakira"}),
    )
    monkeypatch.setenv("CLIPPING_ALLOW_LOCAL_WRITES", "1")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
    monkeypatch.delenv("CLIPPING_VIEWER_PROFILES", raising=False)

    profiles_path = tmp_path / "viewer_profiles.json"
    profiles_path.write_text(
        json.dumps(
            {
                "profiles": {
                    "flavio": {
                        "label": "Flavio Valle",
                        "target_keys": ["flavio_valle"],
                        "default_targets": ["flavio_valle"],
                    },
                    "shakira": {
                        "label": "Show da Shakira",
                        "target_keys": ["shakira"],
                        "default_targets": ["shakira"],
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("CLIPPING_VIEWER_PROFILES_PATH", str(profiles_path))

    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {"key": "flavio_valle", "label": "Flavio Valle", "display_name": "Flavio Valle", "primary": True, "archived": False, "keywords": ["Flavio"], "exact_aliases": []},
                {"key": "shakira", "label": "Shakira", "display_name": "Shakira", "primary": False, "archived": False, "keywords": ["Shakira"], "exact_aliases": []},
                {"key": "pedro_angelito", "label": "Pedro Angelito", "display_name": "Pedro Angelito", "primary": True, "archived": False, "keywords": ["Pedro"], "exact_aliases": []},
            ]
        ),
        encoding="utf-8",
    )

    for name in list(sys.modules):
        if name == "web_app" or name.startswith("web_app."):
            del sys.modules[name]
    auth = importlib.import_module("web_app.auth")
    db_admin = importlib.import_module("web_app.db_admin")
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)
    app_module = importlib.import_module("web_app.app")
    credentials_path = tmp_path / "clipping_credentials.json"
    monkeypatch.setattr(auth, "CREDENTIALS_PATH", credentials_path)
    return auth, app_module, profiles_path, credentials_path


def login_and_csrf(client: TestClient, password: str) -> str:
    resp = client.post("/api/login", json={"password": password})
    assert resp.status_code == 200, resp.text
    csrf = client.get("/api/csrf")
    assert csrf.status_code == 200
    return csrf.json()["csrf"]


def test_list_viewers_returns_label_targets_and_password_flag(monkeypatch, tmp_path):
    _, app_module, _, _ = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    csrf = login_and_csrf(client, "test-password")
    resp = client.get("/api/admin/viewers", headers={"X-CSRF-Token": csrf})
    assert resp.status_code == 200, resp.text
    viewers = resp.json()["viewers"]
    by_profile = {row["profile"]: row for row in viewers}
    assert by_profile["flavio"]["label"] == "Flavio Valle"
    assert by_profile["flavio"]["target_keys"] == ["flavio_valle"]
    assert by_profile["flavio"]["has_password"] is True
    assert by_profile["shakira"]["has_password"] is True


def test_create_viewer_writes_profile_and_password(monkeypatch, tmp_path):
    auth, app_module, profiles_path, creds_path = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    csrf = login_and_csrf(client, "test-password")
    resp = client.post(
        "/api/admin/viewers",
        headers={"X-CSRF-Token": csrf},
        json={
            "profile": "novo_cliente",
            "label": "Novo Cliente",
            "target_keys": ["shakira"],
            "password": "novo-cliente-2026",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["viewer"]["profile"] == "novo_cliente"
    assert body["viewer"]["target_keys"] == ["shakira"]
    assert body["viewer"]["has_password"] is True

    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))["profiles"]
    assert "novo_cliente" in profiles
    assert profiles["novo_cliente"]["label"] == "Novo Cliente"

    creds = json.loads(creds_path.read_text(encoding="utf-8"))
    assert creds["viewer_passwords"]["novo_cliente"].startswith("pbkdf2_sha256$")

    login = client.post("/api/login", json={"password": "novo-cliente-2026"})
    assert login.status_code == 200, login.text
    assert login.json()["profile"] == "novo_cliente"


def test_create_viewer_rejects_invalid_profile_key(monkeypatch, tmp_path):
    _, app_module, _, _ = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    csrf = login_and_csrf(client, "test-password")
    resp = client.post(
        "/api/admin/viewers",
        headers={"X-CSRF-Token": csrf},
        json={
            "profile": "Cliente Espaço",
            "label": "Cliente Espaço",
            "target_keys": ["shakira"],
            "password": "abc123",
        },
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "viewer_profile_invalid"
    assert body["field"] == "profile"


def test_create_viewer_rejects_duplicate_profile(monkeypatch, tmp_path):
    _, app_module, _, _ = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    csrf = login_and_csrf(client, "test-password")
    resp = client.post(
        "/api/admin/viewers",
        headers={"X-CSRF-Token": csrf},
        json={
            "profile": "flavio",
            "label": "Outro Flavio",
            "target_keys": ["flavio_valle"],
            "password": "outra-senha",
        },
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "viewer_profile_conflict"
    assert body["field"] == "profile"


def test_create_viewer_rejects_unknown_target_key(monkeypatch, tmp_path):
    _, app_module, _, _ = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    csrf = login_and_csrf(client, "test-password")
    resp = client.post(
        "/api/admin/viewers",
        headers={"X-CSRF-Token": csrf},
        json={
            "profile": "fantasma",
            "label": "Cliente Fantasma",
            "target_keys": ["nao_existe"],
            "password": "abc123",
        },
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "viewer_profile_invalid"
    assert body["field"] == "target_keys"
    assert "nao_existe" in body["message"]


def test_update_viewer_changes_label_and_targets(monkeypatch, tmp_path):
    _, app_module, profiles_path, _ = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    csrf = login_and_csrf(client, "test-password")
    resp = client.patch(
        "/api/admin/viewers/shakira",
        headers={"X-CSRF-Token": csrf},
        json={
            "label": "Shakira FGV (renomeado)",
            "target_keys": ["shakira", "pedro_angelito"],
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()["viewer"]
    assert body["label"] == "Shakira FGV (renomeado)"
    assert "pedro_angelito" in body["target_keys"]

    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))["profiles"]
    assert profiles["shakira"]["label"] == "Shakira FGV (renomeado)"


def test_update_viewer_password_changes_login(monkeypatch, tmp_path):
    auth, app_module, _, _ = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    csrf = login_and_csrf(client, "test-password")
    resp = client.patch(
        "/api/admin/viewers/shakira",
        headers={"X-CSRF-Token": csrf},
        json={"password": "shakira-nova-2026"},
    )
    assert resp.status_code == 200, resp.text

    fresh = TestClient(app_module.app)
    bad = fresh.post("/api/login", json={"password": "viewer-shakira"})
    assert bad.status_code == 401
    good = fresh.post("/api/login", json={"password": "shakira-nova-2026"})
    assert good.status_code == 200
    assert good.json()["profile"] == "shakira"


def test_update_viewer_404_when_missing(monkeypatch, tmp_path):
    _, app_module, _, _ = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    csrf = login_and_csrf(client, "test-password")
    resp = client.patch(
        "/api/admin/viewers/fantasma",
        headers={"X-CSRF-Token": csrf},
        json={"label": "Fantasma"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "viewer_profile_not_found"


def test_archive_viewer_removes_profile_and_password(monkeypatch, tmp_path):
    auth, app_module, profiles_path, creds_path = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    csrf = login_and_csrf(client, "test-password")
    # Seed credentials file by writing the viewer password explicitly so we
    # can verify it gets cleared on archive.
    auth.set_viewer_password("shakira", "viewer-shakira")
    resp = client.post(
        "/api/admin/viewers/shakira/archive",
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["archived"] == "shakira"

    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))["profiles"]
    assert "shakira" not in profiles

    creds = json.loads(creds_path.read_text(encoding="utf-8"))
    assert "shakira" not in creds.get("viewer_passwords", {})

    # Login as ex-viewer must now fail.
    fresh = TestClient(app_module.app)
    assert fresh.post("/api/login", json={"password": "viewer-shakira"}).status_code == 401


def test_archive_viewer_404_when_missing(monkeypatch, tmp_path):
    _, app_module, _, _ = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    csrf = login_and_csrf(client, "test-password")
    resp = client.post(
        "/api/admin/viewers/fantasma/archive",
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "viewer_profile_not_found"


def test_archive_admin_pseudo_profile_is_blocked(monkeypatch, tmp_path):
    _, app_module, _, _ = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    csrf = login_and_csrf(client, "test-password")
    resp = client.post(
        "/api/admin/viewers/admin/archive",
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "viewer_profile_invalid"


def test_admin_viewer_endpoints_require_admin(monkeypatch, tmp_path):
    _, app_module, _, _ = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    # Log in as viewer, not admin.
    csrf = login_and_csrf(client, "viewer-flavio")
    resp = client.get("/api/admin/viewers", headers={"X-CSRF-Token": csrf})
    assert resp.status_code == 401

    resp = client.post(
        "/api/admin/viewers",
        headers={"X-CSRF-Token": csrf},
        json={"profile": "x", "label": "X", "target_keys": [], "password": "abc"},
    )
    assert resp.status_code == 401
