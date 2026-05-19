from __future__ import annotations

import importlib
import json
import sys

import pytest
from fastapi.testclient import TestClient

from pipeline.database import ClippingDB


def reload_auth_and_app(monkeypatch, tmp_path, *, admin_password="test-password", session_secret="test-session-secret"):
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
    for name in list(sys.modules):
        if name == "web_app" or name.startswith("web_app."):
            del sys.modules[name]
    auth = importlib.import_module("web_app.auth")
    app_module = importlib.import_module("web_app.app")
    credentials_path = tmp_path / "clipping_credentials.json"
    monkeypatch.setattr(auth, "CREDENTIALS_PATH", credentials_path)
    return auth, app_module, credentials_path


def login_and_csrf(client: TestClient, password: str) -> str:
    resp = client.post("/api/login", json={"password": password})
    assert resp.status_code == 200, resp.text
    csrf = client.get("/api/csrf")
    assert csrf.status_code == 200
    return csrf.json()["csrf"]


def test_file_admin_password_wins_over_env(monkeypatch, tmp_path):
    auth, _, creds_path = reload_auth_and_app(monkeypatch, tmp_path)
    creds_path.write_text(json.dumps({"admin_password": "file-admin"}), encoding="utf-8")
    assert auth.check_password("file-admin") is True
    assert auth.check_password("test-password") is False, "env var must not match when file is present"
    assert auth.credentials_source() == "file"


def test_file_admin_password_accepts_hash(monkeypatch, tmp_path):
    auth, _, creds_path = reload_auth_and_app(monkeypatch, tmp_path)
    hashed = auth._hash_password("super-segredo")
    assert hashed.startswith("pbkdf2_sha256$310000$")
    creds_path.write_text(json.dumps({"admin_password": hashed}), encoding="utf-8")
    assert auth.check_password("super-segredo") is True
    assert auth.check_password("WRONG") is False
    # Each hash uses a fresh random salt, so calling _hash_password again gives a different string.
    hashed_again = auth._hash_password("super-segredo")
    assert hashed_again != hashed
    assert auth._verify_password("super-segredo", hashed_again) is True


def test_file_viewer_passwords_win_over_env(monkeypatch, tmp_path):
    auth, _, creds_path = reload_auth_and_app(monkeypatch, tmp_path)
    creds_path.write_text(
        json.dumps({"viewer_passwords": {"flavio": "from-file"}}),
        encoding="utf-8",
    )
    viewers = auth.viewer_passwords()
    assert viewers == {"flavio": "from-file"}, "file passwords replace env-defined viewers entirely"


def test_fallback_to_env_when_file_missing(monkeypatch, tmp_path):
    auth, _, _ = reload_auth_and_app(monkeypatch, tmp_path)
    assert auth.check_password("test-password") is True
    viewers = auth.viewer_passwords()
    assert viewers["flavio"] == "viewer-flavio"
    assert auth.credentials_source() == "env"


def test_set_admin_password_persists_and_migrates_viewers(monkeypatch, tmp_path):
    auth, _, creds_path = reload_auth_and_app(monkeypatch, tmp_path)
    auth.set_admin_password("nova-senha-admin")
    data = json.loads(creds_path.read_text(encoding="utf-8"))
    # Password is hashed at rest (not plaintext) yet verifies against the plaintext input.
    assert data["admin_password"].startswith("pbkdf2_sha256$")
    assert auth._verify_password("nova-senha-admin", data["admin_password"]) is True
    # Viewers migrated from env on first write are also hashed.
    assert data["viewer_passwords"]["flavio"].startswith("pbkdf2_sha256$")
    assert auth._verify_password("viewer-flavio", data["viewer_passwords"]["flavio"]) is True
    assert auth.check_password("nova-senha-admin") is True


def test_set_viewer_password_persists_and_migrates_admin(monkeypatch, tmp_path):
    auth, _, creds_path = reload_auth_and_app(monkeypatch, tmp_path)
    auth.set_viewer_password("flavio", "nova-flavio")
    data = json.loads(creds_path.read_text(encoding="utf-8"))
    assert auth._verify_password("nova-flavio", data["viewer_passwords"]["flavio"]) is True
    assert auth._verify_password("viewer-shakira", data["viewer_passwords"]["shakira"]) is True, "other viewers preserved"
    assert auth._verify_password("test-password", data["admin_password"]) is True, "admin migrated from env on first viewer write"


def test_set_password_rejects_too_short(monkeypatch, tmp_path):
    auth, _, _ = reload_auth_and_app(monkeypatch, tmp_path)
    with pytest.raises(ValueError, match="3 caracteres"):
        auth.set_admin_password("ab")
    with pytest.raises(ValueError, match="3 caracteres"):
        auth.set_viewer_password("flavio", "xy")


def test_change_password_endpoint_rejects_wrong_old(monkeypatch, tmp_path):
    _, app_module, _ = reload_auth_and_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    csrf = login_and_csrf(client, "test-password")
    resp = client.post(
        "/api/change-password",
        headers={"X-CSRF-Token": csrf},
        json={"old_password": "WRONG", "new_password": "nova-pass"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "password_change_invalid"
    assert body["field"] == "old_password"
    assert "Senha atual incorreta" in body["message"]


def test_change_password_endpoint_rejects_too_short_new(monkeypatch, tmp_path):
    _, app_module, _ = reload_auth_and_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    csrf = login_and_csrf(client, "test-password")
    resp = client.post(
        "/api/change-password",
        headers={"X-CSRF-Token": csrf},
        json={"old_password": "test-password", "new_password": "ab"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["field"] == "new_password"


def test_change_password_endpoint_admin_happy_path(monkeypatch, tmp_path):
    auth, app_module, creds_path = reload_auth_and_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    csrf = login_and_csrf(client, "test-password")
    resp = client.post(
        "/api/change-password",
        headers={"X-CSRF-Token": csrf},
        json={"old_password": "test-password", "new_password": "nova-admin-2026"},
    )
    assert resp.status_code == 200, resp.text
    # File written with hash.
    data = json.loads(creds_path.read_text(encoding="utf-8"))
    assert data["admin_password"].startswith("pbkdf2_sha256$")
    assert auth._verify_password("nova-admin-2026", data["admin_password"]) is True
    # New password authenticates; old does not.
    assert auth.check_password("nova-admin-2026") is True
    assert auth.check_password("test-password") is False
    # New session cookie set so admin stays logged in.
    assert "clipping_admin" in resp.cookies, "new session must be issued"


def test_change_password_endpoint_viewer_happy_path(monkeypatch, tmp_path):
    auth, app_module, creds_path = reload_auth_and_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    csrf = login_and_csrf(client, "viewer-flavio")
    resp = client.post(
        "/api/change-password",
        headers={"X-CSRF-Token": csrf},
        json={"old_password": "viewer-flavio", "new_password": "nova-flavio-2026"},
    )
    assert resp.status_code == 200, resp.text
    data = json.loads(creds_path.read_text(encoding="utf-8"))
    assert auth._verify_password("nova-flavio-2026", data["viewer_passwords"]["flavio"]) is True
    assert auth._verify_password("nova-flavio-2026", auth.viewer_passwords()["flavio"]) is True
    # Other viewers still present (from env migration), now stored as hashes.
    assert auth._verify_password("viewer-shakira", auth.viewer_passwords()["shakira"]) is True
