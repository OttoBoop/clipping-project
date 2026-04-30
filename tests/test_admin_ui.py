from __future__ import annotations

import argparse
import json
import importlib
import sqlite3
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from pipeline.database import ClippingDB


OBSERVED_UPLOAD_PATHS = [
    "data/clipping.db",
    "data/targets.json",
    "assets/clipping-data.json",
    "assets/clipping-raw-texts.json",
    "runs/manual-story.json",
]

SECRET_SENTINELS = [
    "test-password",
    "test-session-secret",
    "supabase-secret-token-value",
    "SUPABASE_SERVICE_KEY",
    "Authorization",
    "Bearer ",
]


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
    module.ensure_app_tables(db_file)
    return module.app, db_file


def login(client: TestClient) -> str:
    response = client.post("/api/login", json={"password": "test-password"})
    assert response.status_code == 200
    csrf = client.get("/api/csrf")
    assert csrf.status_code == 200
    return csrf.json()["csrf"]


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


def mock_artifact_upload(monkeypatch, tmp_path, uploaded_paths=None):
    app_module = importlib.import_module("web_app.app")
    uploaded_paths = list(uploaded_paths or OBSERVED_UPLOAD_PATHS)
    calls = []

    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "supabase-secret-token-value")
    monkeypatch.setattr(app_module.artifact_store, "enabled", True)
    monkeypatch.setattr(
        app_module.artifact_store,
        "backup_current_artifacts",
        lambda label: tmp_path / f"{label}-backup",
    )
    monkeypatch.setattr(app_module, "run_export_snapshot", lambda *args, **kwargs: None)

    def fake_upload_current_artifacts(*, manifest=None, job_id=None):
        calls.append({"manifest": manifest, "job_id": job_id})
        return list(uploaded_paths)

    monkeypatch.setattr(app_module.artifact_store, "upload_current_artifacts", fake_upload_current_artifacts)
    return calls, uploaded_paths


def status_jobs(payload):
    current = payload.get("current")
    if isinstance(current, dict):
        yield "current", current
    recent = payload.get("recent")
    if isinstance(recent, list):
        for index, job in enumerate(recent):
            if isinstance(job, dict):
                yield f"recent[{index}]", job


def assert_no_secret_material(value):
    serialized = json.dumps(value, sort_keys=True)
    for sentinel in SECRET_SENTINELS:
        assert sentinel not in serialized


def assert_status_exposes_artifact_upload(payload, uploaded_paths, *, job_id=None):
    matches = []
    for location, job in status_jobs(payload):
        if job_id and job.get("id") != job_id:
            continue
        if {"artifactUpload", "uploadedArtifacts", "uploadedArtifactCount"} <= set(job):
            matches.append((location, job))

    assert matches, json.dumps(payload, indent=2, sort_keys=True)
    location, job = matches[0]
    assert job["uploadedArtifactCount"] == len(uploaded_paths), location
    assert job["uploadedArtifacts"] == uploaded_paths, location
    assert job["artifactUpload"]["count"] == len(uploaded_paths), location
    assert job["artifactUpload"]["items"] == uploaded_paths, location
    return location, job


def assert_db_artifact_event(db_file, job_id, uploaded_paths):
    with sqlite3.connect(db_file) as conn:
        conn.row_factory = sqlite3.Row
        job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        event = conn.execute(
            """
            SELECT * FROM job_events
            WHERE job_id = ? AND event = 'artifacts_uploaded'
            ORDER BY id DESC
            LIMIT 1
            """,
            (job_id,),
        ).fetchone()

    assert job is not None
    assert event is not None
    payload = json.loads(event["payload_json"])
    assert payload["count"] == len(uploaded_paths)
    assert payload["items"] == uploaded_paths
    assert_no_secret_material({"job": dict(job), "event": payload})


def assert_empty_db(db_file):
    assert db_counts(db_file) == {
        "articles": 0,
        "mentions": 0,
        "stories": 0,
        "story_articles": 0,
        "story_targets": 0,
        "manual_entries": 0,
    }


def test_admin_route_is_retired_and_status_is_public(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        admin_page = client.get("/admin", follow_redirects=False)
        bad_login = client.post("/api/login", json={"password": "wrong-password"})
        status = client.get("/api/update/status")
        manual_without_login = client.post("/api/manual-story", json=manual_story_payload())

    assert admin_page.status_code == 307
    assert admin_page.headers["location"] == "/"
    assert bad_login.status_code == 401
    assert "clipping_admin" not in bad_login.cookies
    assert status.status_code == 200
    assert manual_without_login.status_code == 401
    assert_empty_db(db_file)


def test_admin_auth_fails_closed_when_env_values_are_blank(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path, admin_password="   ", session_secret="\t ")
    with TestClient(app) as client:
        admin_page = client.get("/admin", follow_redirects=False)
        login_attempt = client.post("/api/login", json={"password": "   "})
        status = client.get("/api/update/status")
        manual_without_login = client.post("/api/manual-story", json=manual_story_payload())

    assert admin_page.status_code == 307
    assert admin_page.headers["location"] == "/"
    assert login_attempt.status_code == 503
    assert status.status_code == 200
    assert manual_without_login.status_code == 503
    assert_empty_db(db_file)


def test_admin_write_apis_reject_missing_or_bad_csrf(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        csrf = login(client)
        responses = [
            client.post("/api/logout"),
            client.post("/api/manual-story", json=manual_story_payload()),
            client.post(
                "/api/manual-story",
                headers={"X-CSRF-Token": f"{csrf}-tampered"},
                json=manual_story_payload(),
            ),
        ]

    assert [response.status_code for response in responses] == [403, 403, 403]
    assert [response.json()["detail"] for response in responses] == ["csrf_check_failed"] * 3
    assert_empty_db(db_file)


def test_update_and_export_workflows_are_public_coworker_endpoints(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")
    calls = []

    def fake_start_update(payload, *, started_by):
        calls.append(("update", payload, started_by))
        return {"id": "update-public", "kind": "update", "started_by": started_by}

    def fake_start_export(*, started_by):
        calls.append(("export", {}, started_by))
        return {"id": "export-public", "kind": "export", "started_by": started_by}

    monkeypatch.setattr(app_module.job_manager, "start_update", fake_start_update)
    monkeypatch.setattr(app_module.job_manager, "start_export", fake_start_export)

    with TestClient(app) as client:
        status = client.get("/api/update/status")
        update = client.post("/api/update/start", json={"preset": "rapido", "export": False})
        export = client.post("/api/export")

    assert status.status_code == 200
    assert update.status_code == 200
    assert export.status_code == 200
    assert calls == [
        ("update", {"preset": "rapido", "export": False}, "coworker"),
        ("export", {}, "coworker"),
    ]


def test_targets_api_is_public_and_uploads_target_manifest(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")
    upload_calls = []

    monkeypatch.setattr(app_module, "public_targets", lambda: [{"key": "flavio_valle", "label": "Flavio Valle"}])
    monkeypatch.setattr(
        app_module,
        "create_secondary_target",
        lambda payload: {"key": "ana_teste", "label": payload["label"], "primary": False},
    )
    monkeypatch.setattr(app_module.artifact_store, "enabled", True)

    def fake_upload_current_artifacts(*, manifest=None, job_id=None):
        upload_calls.append({"manifest": manifest, "job_id": job_id})
        return ["data/targets.json", "runs/targets-ana_teste.json"]

    monkeypatch.setattr(app_module.artifact_store, "upload_current_artifacts", fake_upload_current_artifacts)

    with TestClient(app) as client:
        listed = client.get("/api/targets")
        created = client.post("/api/targets", json={"label": "Ana Teste"})

    assert listed.status_code == 200
    assert listed.json() == {
        "targets": [{"key": "flavio_valle", "label": "Flavio Valle"}],
        "primaryKeys": [],
    }
    assert created.status_code == 200
    assert created.json()["key"] == "ana_teste"
    assert created.json()["uploadedArtifactCount"] == 2
    assert upload_calls == [
        {
            "manifest": {"kind": "targets", "result": {"key": "ana_teste", "label": "Ana Teste", "primary": False}},
            "job_id": "targets-ana_teste",
        }
    ]
    assert_no_secret_material({"created": created.json(), "upload_calls": upload_calls})


def test_targets_api_returns_real_public_targets_contract(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)

    with TestClient(app) as client:
        response = client.get("/api/targets")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["targets"], list)
    assert payload["primaryKeys"] == ["flavio_valle", "pedro_angelito", "bernardo_rubiao"]

    by_key = {target["key"]: target for target in payload["targets"]}
    for key in payload["primaryKeys"]:
        assert by_key[key]["primary"] is True
        assert by_key[key]["className"] == "primary"


def test_targets_api_validation_errors_are_public_400s(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")

    def fail_create(_payload):
        raise app_module.ValidationError("Nome acompanhado invalido.")

    monkeypatch.setattr(app_module, "create_secondary_target", fail_create)

    with TestClient(app) as client:
        response = client.post("/api/targets", json={"label": ""})

    assert response.status_code == 400
    assert response.json()["detail"] == "Nome acompanhado invalido."


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


def test_storage_current_files_are_runtime_mutable_only(monkeypatch, tmp_path):
    load_test_app(monkeypatch, tmp_path)
    storage_bridge = importlib.import_module("web_app.storage_bridge")
    requested = []

    paths = [relative for relative, _ in storage_bridge.CURRENT_FILES]
    assert paths == [
        "data/clipping.db",
        "data/targets.json",
        "assets/clipping-data.json",
        "assets/clipping-raw-texts.json",
    ]
    assert "index.html" not in paths
    assert "assets/clipping.css" not in paths
    assert "assets/clipping.js" not in paths

    monkeypatch.setattr(storage_bridge.artifact_store, "enabled", True)
    monkeypatch.setattr(storage_bridge.artifact_store, "prefix", "clipping-project")

    def fake_download(remote_path, local_path):
        requested.append(remote_path)
        return True

    monkeypatch.setattr(storage_bridge.artifact_store, "download_file", fake_download)
    assert storage_bridge.artifact_store.download_current_artifacts() == paths
    assert requested == [f"clipping-project/current/{path}" for path in paths]


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


def test_update_status_exposes_artifact_upload_contract_for_completed_jobs(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    jobs = importlib.import_module("web_app.jobs")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "supabase-secret-token-value")

    for kind in ("update", "export"):
        job_id = f"{kind}-observed"
        jobs.create_job(
            job_id,
            kind,
            {
                "preset": kind,
                "collector": kind,
                "target_keys": ["flavio_valle"] if kind == "update" else [],
                "date_from": "2026-04-29" if kind == "update" else "",
                "date_to": "2026-04-30" if kind == "update" else "",
            },
            started_by="admin",
        )
        jobs.append_event(job_id, "artifacts_uploaded", {"count": len(OBSERVED_UPLOAD_PATHS), "items": OBSERVED_UPLOAD_PATHS})
        jobs.update_job(job_id, status="succeeded", articles_inserted=1, stories_touched=1)

        with TestClient(app) as client:
            status = client.get("/api/update/status")

        assert status.status_code == 200
        _, observed = assert_status_exposes_artifact_upload(status.json(), OBSERVED_UPLOAD_PATHS, job_id=job_id)
        assert observed["kind"] == kind
        assert_no_secret_material(status.json())


def test_admin_route_does_not_serve_password_or_admin_copy(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        response = client.get("/admin", follow_redirects=False)
    assert response.status_code == 307
    assert response.text == ""
    assert "password" not in response.text.lower()
    assert "admin" not in response.text.lower()


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


def test_manual_story_records_uploaded_artifact_observability(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path)
    upload_calls, uploaded_paths = mock_artifact_upload(monkeypatch, tmp_path)

    with TestClient(app) as client:
        csrf = login(client)
        response = client.post(
            "/api/manual-story",
            headers={"X-CSRF-Token": csrf},
            json=manual_story_payload(export=True, note="Observability contract check."),
        )
        status = client.get("/api/update/status")

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "created"
    assert len(upload_calls) == 1
    assert upload_calls[0]["manifest"]["kind"] == "manual-story"
    assert upload_calls[0]["manifest"]["result"]["articleId"] == result["articleId"]

    assert status.status_code == 200
    _, observed = assert_status_exposes_artifact_upload(status.json(), uploaded_paths)
    assert observed["kind"] == "manual"
    assert observed["status"] == "succeeded"
    assert_db_artifact_event(db_file, observed["id"], uploaded_paths)
    assert_no_secret_material({"response": result, "status": status.json(), "upload_calls": upload_calls})


def test_manual_story_duplicate_with_artifact_upload_stays_polite(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path)
    upload_calls, uploaded_paths = mock_artifact_upload(monkeypatch, tmp_path)

    with TestClient(app) as client:
        csrf = login(client)
        first = client.post("/api/manual-story", headers={"X-CSRF-Token": csrf}, json=manual_story_payload(export=True))
        second = client.post(
            "/api/manual-story",
            headers={"X-CSRF-Token": csrf},
            json=manual_story_payload(
                export=True,
                title="Titulo alterado nao deve criar nova materia",
                url="HTTPS://EXAMPLE.COM/noticia/?utm_campaign=outra-campanha#fragmento",
            ),
        )
        status = client.get("/api/update/status")

    assert first.status_code == 200
    assert second.status_code == 200, second.text
    assert second.json()["status"] == "duplicate"
    assert second.json()["message"] == "Esta materia ja estava na base."
    assert second.json()["articleId"] == first.json()["articleId"]
    assert len(upload_calls) == 2
    assert db_counts(db_file) == {
        "articles": 1,
        "mentions": 1,
        "stories": 1,
        "story_articles": 1,
        "story_targets": 1,
        "manual_entries": 1,
    }

    assert status.status_code == 200
    _, observed = assert_status_exposes_artifact_upload(status.json(), uploaded_paths)
    assert observed["kind"] == "manual"
    assert observed["status"] == "succeeded"
    assert_db_artifact_event(db_file, observed["id"], uploaded_paths)
    assert_no_secret_material({"response": second.json(), "status": status.json(), "upload_calls": upload_calls})


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
    assert "Clipping do gabinete" in html
    assert "Rodar atualizacao" in html
    assert "Noticias disponiveis para consulta" in html
    assert "Com texto para leitura" in html
    assert "DOM" not in html
    assert "RAM" not in html
    assert "API local" not in html
