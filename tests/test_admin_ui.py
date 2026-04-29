from __future__ import annotations

import importlib
import re
import sqlite3
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from pipeline.database import ClippingDB


def load_test_app(monkeypatch, tmp_path):
    db_file = tmp_path / "clipping.db"
    ClippingDB(db_file)
    monkeypatch.setenv("CLIPPING_DB_PATH", str(db_file))
    monkeypatch.setenv("CLIPPING_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("CLIPPING_SESSION_SECRET", "test-session-secret")
    monkeypatch.setenv("CLIPPING_ALLOW_LOCAL_WRITES", "1")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)

    for name in list(sys.modules):
        if name == "web_app" or name.startswith("web_app."):
            del sys.modules[name]
    module = importlib.import_module("web_app.app")
    return module.app, db_file


def login(client: TestClient) -> str:
    response = client.post("/api/login", json={"password": "test-password"})
    assert response.status_code == 200
    page = client.get("/admin")
    assert page.status_code == 200
    match = re.search(r'name="csrf-token" content="([^"]+)"', page.text)
    assert match
    return match.group(1)


def db_counts(db_file):
    with sqlite3.connect(db_file) as conn:
        return {
            "articles": conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0],
            "stories": conn.execute("SELECT COUNT(*) FROM stories").fetchone()[0],
            "story_articles": conn.execute("SELECT COUNT(*) FROM story_articles").fetchone()[0],
            "story_targets": conn.execute("SELECT COUNT(*) FROM story_targets").fetchone()[0],
        }


def test_admin_ui_serves_manual_story_form(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        login(client)
        response = client.get("/admin")
    assert response.status_code == 200
    assert "Adicionar materia manualmente" in response.text
    assert "manualTitle" in response.text
    assert "manualUrl" in response.text
    assert "manualSource" in response.text
    assert "manualSummary" in response.text
    assert "Comecar atualizacao" in response.text


def test_manual_story_insert_creates_unique_story_graph(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        csrf = login(client)
        response = client.post(
            "/api/manual-story",
            headers={"X-CSRF-Token": csrf},
            json={
                "title": "Flavio Valle anuncia agenda de fiscalizacao",
                "url": "https://example.com/noticia?utm_source=test",
                "source_name": "Jornal Teste",
                "summary": "Materia cita Flavio Valle em agenda de fiscalizacao municipal.",
                "target_keys": ["flavio_valle"],
                "export": False,
            },
        )
    assert response.status_code == 200
    assert response.json()["status"] == "created"
    assert db_counts(db_file) == {"articles": 1, "stories": 1, "story_articles": 1, "story_targets": 1}


def test_manual_story_insert_is_idempotent_for_duplicate_url(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path)
    payload = {
        "title": "Flavio Valle anuncia agenda de fiscalizacao",
        "url": "https://example.com/noticia?utm_source=test",
        "source_name": "Jornal Teste",
        "summary": "Materia cita Flavio Valle em agenda de fiscalizacao municipal.",
        "target_keys": ["flavio_valle"],
        "export": False,
    }
    with TestClient(app) as client:
        csrf = login(client)
        first = client.post("/api/manual-story", headers={"X-CSRF-Token": csrf}, json=payload)
        second = client.post("/api/manual-story", headers={"X-CSRF-Token": csrf}, json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"
    assert db_counts(db_file)["articles"] == 1


def test_manual_story_validation_rejects_partial_payload_without_db_write(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        csrf = login(client)
        response = client.post(
            "/api/manual-story",
            headers={"X-CSRF-Token": csrf},
            json={"title": "", "url": "", "target_keys": []},
        )
    assert response.status_code == 400
    assert db_counts(db_file) == {"articles": 0, "stories": 0, "story_articles": 0, "story_targets": 0}


def test_public_dashboard_wording_contract():
    html = Path("index.html").read_text(encoding="utf-8")
    assert "Clipping institucional" in html
    assert "Materias encontradas" in html
    assert "Com texto completo" in html
    assert "DOM" not in html
    assert "RAM" not in html
    assert "API local" not in html
