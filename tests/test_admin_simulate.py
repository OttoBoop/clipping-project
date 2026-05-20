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

    # Seed a small assets/clipping-data.json so dashboard_asset has data to scope.
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    clipping_data = {
        "targets": [
            {"key": "flavio_valle", "label": "Flavio Valle", "primary": True, "archived": False},
            {"key": "shakira", "label": "Shakira", "primary": False, "archived": False},
        ],
        "defaultTargets": ["flavio_valle"],
        "stories": [
            {
                "id": "s1",
                "targetKeys": ["flavio_valle"],
                "articles": [{"id": 1, "targetKeys": ["flavio_valle"], "summarySource": "raw"}],
            },
            {
                "id": "s2",
                "targetKeys": ["shakira"],
                "articles": [{"id": 2, "targetKeys": ["shakira"], "summarySource": "raw"}],
            },
        ],
        "meta": {},
    }
    (assets_dir / "clipping-data.json").write_text(json.dumps(clipping_data), encoding="utf-8")
    (assets_dir / "clipping-raw-texts.json").write_text(json.dumps({}), encoding="utf-8")
    monkeypatch.setenv("CLIPPING_ASSETS_DIR", str(assets_dir))

    for name in list(sys.modules):
        if name == "web_app" or name.startswith("web_app."):
            del sys.modules[name]
    auth = importlib.import_module("web_app.auth")
    config = importlib.import_module("web_app.config")
    monkeypatch.setattr(config, "ASSETS_DIR", assets_dir)
    app_module = importlib.import_module("web_app.app")
    monkeypatch.setattr(app_module, "ASSETS_DIR", assets_dir)
    credentials_path = tmp_path / "clipping_credentials.json"
    monkeypatch.setattr(auth, "CREDENTIALS_PATH", credentials_path)
    return auth, app_module


def login(client: TestClient, password: str) -> None:
    resp = client.post("/api/login", json={"password": password})
    assert resp.status_code == 200, resp.text


def test_admin_simulating_flavio_sees_filtered_payload(monkeypatch, tmp_path):
    _, app_module = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    login(client, "test-password")
    resp = client.get("/assets/clipping-data.json?as_profile=flavio")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    meta = body.get("meta", {})
    assert meta.get("viewerRole") == "viewer"
    assert meta.get("viewerProfile") == "flavio"
    target_keys = [t["key"] for t in body.get("targets", [])]
    assert target_keys == ["flavio_valle"]
    # Stories filtered: shakira story must be excluded.
    story_ids = [s["id"] for s in body.get("stories", [])]
    assert story_ids == ["s1"]


def test_admin_simulating_invalid_profile_400(monkeypatch, tmp_path):
    _, app_module = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    login(client, "test-password")
    resp = client.get("/assets/clipping-data.json?as_profile=nao_existe")
    assert resp.status_code == 400
    assert "viewer_profile_not_found" in resp.text


def test_viewer_query_param_ignored(monkeypatch, tmp_path):
    """Viewer with ?as_profile=X param should still see their own scope —
    the simulate param is admin-only."""
    _, app_module = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    login(client, "viewer-shakira")
    # Viewer shakira tries to simulate flavio — must be ignored, sees shakira.
    resp = client.get("/assets/clipping-data.json?as_profile=flavio")
    assert resp.status_code == 200
    body = resp.json()
    meta = body.get("meta", {})
    assert meta.get("viewerProfile") == "shakira"
    target_keys = [t["key"] for t in body.get("targets", [])]
    assert target_keys == ["shakira"]


def test_admin_without_param_sees_full_payload(monkeypatch, tmp_path):
    _, app_module = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    login(client, "test-password")
    resp = client.get("/assets/clipping-data.json")
    assert resp.status_code == 200
    body = resp.json()
    meta = body.get("meta", {})
    assert meta.get("viewerRole") == "admin"
    target_keys = sorted(t["key"] for t in body.get("targets", []))
    assert target_keys == ["flavio_valle", "shakira"]
    story_ids = sorted(s["id"] for s in body.get("stories", []))
    assert story_ids == ["s1", "s2"]


def test_admin_simulating_cannot_mutate_targets(monkeypatch, tmp_path):
    """Admin in simulation mode is still admin in the cookie — but a fake
    viewer session must NOT grant the simulated viewer admin powers. POST
    /api/targets goes through require_admin which reads the real cookie,
    so admin keeps the ability to mutate. This test asserts the inverse:
    a viewer logged in with ?as_profile=admin cannot escalate."""
    _, app_module = reload_app(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    login(client, "viewer-flavio")
    csrf = client.get("/api/csrf").json()["csrf"]
    # Viewer tries to use ?as_profile=admin to escalate — backend ignores
    # the param (viewer cannot simulate), require_admin still rejects.
    resp = client.post(
        "/api/targets?as_profile=admin",
        headers={"X-CSRF-Token": csrf},
        json={"display_name": "Should Not Create", "keywords": []},
    )
    assert resp.status_code == 401
    assert "admin_login_required" in resp.text


def test_dashboard_html_marks_simulation(monkeypatch, tmp_path):
    _, app_module = reload_app(monkeypatch, tmp_path)
    # Make sure index.html exists in ROOT for dashboard_html_for_session
    # to read. The test repo has one already, but if not, skip the body check.
    from web_app.config import ROOT
    index_path = ROOT / "index.html"
    if not index_path.is_file():
        return
    client = TestClient(app_module.app)
    login(client, "test-password")
    resp = client.get("/?as_profile=flavio")
    assert resp.status_code == 200
    html = resp.text
    assert 'data-clipping-simulating="flavio"' in html, "missing simulating marker"
    assert 'data-clipping-simulating-label="Flavio Valle"' in html, "missing pretty label attr"
    assert 'data-clipping-session-role="viewer"' in html, "public role should be viewer"
    assert 'data-clipping-session-profile="flavio"' in html
    assert 'data-clipping-real-role="admin"' in html, "real role tracked separately"
    assert '<body class="viewer-readonly">' in html, "viewer-readonly applied in simulation"


def test_dashboard_html_admin_normal_has_no_simulating_attr(monkeypatch, tmp_path):
    _, app_module = reload_app(monkeypatch, tmp_path)
    from web_app.config import ROOT
    if not (ROOT / "index.html").is_file():
        return
    client = TestClient(app_module.app)
    login(client, "test-password")
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "data-clipping-simulating" not in html, "no simulation attr when no param"
    assert 'data-clipping-session-role="admin"' in html
    assert 'viewer-readonly' not in html, "admin body not viewer-readonly"
