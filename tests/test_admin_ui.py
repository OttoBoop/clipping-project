from __future__ import annotations

import argparse
import json
import importlib
import re
import sqlite3
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from pipeline.database import ClippingDB


def load_test_app(monkeypatch, tmp_path, *, admin_password="test-password", session_secret="test-session-secret"):
    db_file = tmp_path / "clipping.db"
    ClippingDB(db_file)
    monkeypatch.setenv("CLIPPING_DB_PATH", str(db_file))
    monkeypatch.setenv("CLIPPING_ADMIN_PASSWORD", admin_password)
    monkeypatch.setenv("CLIPPING_SESSION_SECRET", session_secret)
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
            "mentions": conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0],
            "stories": conn.execute("SELECT COUNT(*) FROM stories").fetchone()[0],
            "story_articles": conn.execute("SELECT COUNT(*) FROM story_articles").fetchone()[0],
            "story_targets": conn.execute("SELECT COUNT(*) FROM story_targets").fetchone()[0],
            "manual_entries": conn.execute("SELECT COUNT(*) FROM manual_entries").fetchone()[0],
        }


def manual_story_payload(**overrides):
    payload = {
        "title": "Flavio Valle anuncia agenda de fiscalizacao",
        "url": "https://example.com/noticia?utm_source=test",
        "source_name": "Jornal Teste",
        "summary": "Materia cita Flavio Valle em agenda de fiscalizacao municipal.",
        "target_keys": ["flavio_valle"],
        "export": False,
    }
    payload.update(overrides)
    return payload


def assert_empty_db(db_file):
    assert db_counts(db_file) == {
        "articles": 0,
        "mentions": 0,
        "stories": 0,
        "story_articles": 0,
        "story_targets": 0,
        "manual_entries": 0,
    }


def test_admin_auth_requires_login(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        login_page = client.get("/admin")
        bad_login = client.post("/api/login", json={"password": "wrong-password"})
        status = client.get("/api/update/status")
        manual_without_login = client.post("/api/manual-story", json=manual_story_payload())

    assert login_page.status_code == 200
    assert "Senha de acesso" in login_page.text
    assert 'name="csrf-token"' not in login_page.text
    assert bad_login.status_code == 401
    assert "clipping_admin" not in bad_login.cookies
    assert status.status_code == 401
    assert manual_without_login.status_code == 401
    assert_empty_db(db_file)


def test_admin_auth_fails_closed_when_env_values_are_blank(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path, admin_password="   ", session_secret="\t ")
    with TestClient(app) as client:
        login_page = client.get("/admin")
        login_attempt = client.post("/api/login", json={"password": "   "})
        status = client.get("/api/update/status")
        manual_without_login = client.post("/api/manual-story", json=manual_story_payload())

    assert login_page.status_code == 200
    assert "Acesso administrativo ainda nao configurado no Render." in login_page.text
    assert 'name="csrf-token"' not in login_page.text
    assert login_attempt.status_code == 503
    assert status.status_code == 503
    assert manual_without_login.status_code == 503
    assert_empty_db(db_file)


def test_admin_write_apis_reject_missing_or_bad_csrf(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        csrf = login(client)
        responses = [
            client.post("/api/logout"),
            client.post("/api/update/start", json={"preset": "rapido", "export": False}),
            client.post("/api/export"),
            client.post("/api/manual-story", json=manual_story_payload()),
            client.post(
                "/api/manual-story",
                headers={"X-CSRF-Token": f"{csrf}-tampered"},
                json=manual_story_payload(),
            ),
        ]

    assert [response.status_code for response in responses] == [403, 403, 403, 403, 403]
    assert [response.json()["detail"] for response in responses] == ["csrf_check_failed"] * 5
    assert_empty_db(db_file)


def test_healthz_exposes_safe_operational_fields(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"ok", "dbExists", "authConfigured", "storage", "localWritesAllowed", "job"}
    assert payload["ok"] is True
    assert payload["dbExists"] is True
    assert payload["authConfigured"] is True
    assert payload["localWritesAllowed"] is True
    assert set(payload["storage"]) == {"enabled", "bucket", "prefix", "localWritesAllowed"}
    assert payload["storage"]["enabled"] is False
    assert payload["storage"]["localWritesAllowed"] is True
    serialized = json.dumps(payload, sort_keys=True)
    assert "test-password" not in serialized
    assert "test-session-secret" not in serialized
    assert "SUPABASE_SERVICE_KEY" not in serialized


def test_job_error_sanitizer_redacts_secret_material(monkeypatch, tmp_path):
    load_test_app(monkeypatch, tmp_path)
    jobs = importlib.import_module("web_app.jobs")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "supabase-secret-token-value")

    message = jobs.sanitize_error(
        RuntimeError(
            "request failed Authorization: Bearer supabase-secret-token-value "
            "apikey=supabase-secret-token-value "
            "https://example.test/callback?access_token=visible-token"
        )
    )

    assert "supabase-secret-token-value" not in message
    assert "visible-token" not in message
    assert "[redacted]" in message


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
            json=manual_story_payload(note="Inserida durante QA."),
        )
    assert response.status_code == 200
    assert response.json()["status"] == "created"
    assert db_counts(db_file) == {
        "articles": 1,
        "mentions": 1,
        "stories": 1,
        "story_articles": 1,
        "story_targets": 1,
        "manual_entries": 1,
    }
    with sqlite3.connect(db_file) as conn:
        conn.row_factory = sqlite3.Row
        article = conn.execute("SELECT * FROM articles").fetchone()
        mention = conn.execute("SELECT * FROM mentions").fetchone()
        manual_entry = conn.execute("SELECT * FROM manual_entries").fetchone()
    assert article["url"] == "https://example.com/noticia"
    assert article["source_type"] == "manual"
    assert article["source_name"] == "Jornal Teste"
    assert json.loads(article["metadata"]) == {"manual": True, "created_by": "admin"}
    assert mention["target_key"] == "flavio_valle"
    assert mention["sentiment_reason"] == "manual_entry"
    assert manual_entry["note"] == "Inserida durante QA."


def test_manual_story_insert_is_idempotent_for_duplicate_url(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        csrf = login(client)
        first = client.post("/api/manual-story", headers={"X-CSRF-Token": csrf}, json=manual_story_payload())
        second = client.post(
            "/api/manual-story",
            headers={"X-CSRF-Token": csrf},
            json=manual_story_payload(
                title="Titulo alterado nao deve criar nova materia",
                url="HTTPS://EXAMPLE.COM/noticia/?utm_campaign=outra-campanha#fragmento",
            ),
        )
    assert first.status_code == 200
    assert second.status_code == 200, second.text
    assert second.json()["status"] == "duplicate"
    assert second.json()["articleId"] == first.json()["articleId"]
    assert db_counts(db_file) == {
        "articles": 1,
        "mentions": 1,
        "stories": 1,
        "story_articles": 1,
        "story_targets": 1,
        "manual_entries": 1,
    }


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
    assert_empty_db(db_file)


def test_manual_story_validation_rejects_unknown_target_without_db_write(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        csrf = login(client)
        response = client.post(
            "/api/manual-story",
            headers={"X-CSRF-Token": csrf},
            json=manual_story_payload(target_keys=["flavio_valle", "nao_existe"]),
        )
    assert response.status_code == 400
    assert response.json()["detail"] == "Nome acompanhado desconhecido."
    assert_empty_db(db_file)


def test_manual_story_export_bundle_can_be_parsed_for_merge_compatibility(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        csrf = login(client)
        response = client.post(
            "/api/manual-story",
            headers={"X-CSRF-Token": csrf},
            json=manual_story_payload(full_text="Texto bruto completo da materia manual. " * 8),
        )
    assert response.status_code == 200

    from tools import export_mobile_snapshot

    args = argparse.Namespace(
        db=str(db_file),
        date_from="",
        date_to="",
        all_stories=True,
        default_target="flavio_valle",
        output=str(tmp_path / "manual-export.html"),
        merge_from="",
        remap_incoming_ids_on_merge=False,
    )
    artifact = export_mobile_snapshot.build_snapshot_artifact(args)
    export_mobile_snapshot.write_bundle_assets(artifact, artifact["asset_paths"])
    export_mobile_snapshot.write_shell_html(Path(args.output), artifact["data_payload"], artifact["asset_paths"])

    merge_meta, stories, raw_texts = export_mobile_snapshot.parse_source_snapshot(args.output)

    assert merge_meta["storyTargets"] == {"1": ["flavio_valle"]}
    assert len(stories) == 1
    assert stories[0]["title"] == "Flavio Valle anuncia agenda de fiscalizacao"
    assert stories[0]["articles"][0]["url"] == "https://example.com/noticia"
    assert stories[0]["articles"][0]["sourceName"] == "Jornal Teste"
    assert stories[0]["articles"][0]["rawTextKey"] == "article-1"
    assert raw_texts["article-1"].startswith("Texto bruto completo da materia manual.")


def test_public_dashboard_wording_contract():
    html = Path("index.html").read_text(encoding="utf-8")
    assert "Clipping institucional" in html
    assert "Materias encontradas" in html
    assert "Com texto completo" in html
    assert "DOM" not in html
    assert "RAM" not in html
    assert "API local" not in html
