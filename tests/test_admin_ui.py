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


def load_test_app(
    monkeypatch,
    tmp_path,
    *,
    admin_password="test-password",
    session_secret="test-session-secret",
    viewer_profiles_path: Path | None = None,
):
    db_file = tmp_path / "clipping.db"
    ClippingDB(db_file)
    monkeypatch.setenv("CLIPPING_DB_PATH", str(db_file))
    monkeypatch.setenv("CLIPPING_ADMIN_PASSWORD", admin_password)
    monkeypatch.setenv("CLIPPING_SESSION_SECRET", session_secret)
    monkeypatch.setenv(
        "CLIPPING_VIEWER_PASSWORDS",
        json.dumps(
            {
                "flavio": "viewer-flavio",
                "shakira": "viewer-shakira",
                "rio_economico": "viewer-rio",
            }
        ),
    )
    monkeypatch.delenv("CLIPPING_VIEWER_PROFILES", raising=False)
    if viewer_profiles_path is None:
        monkeypatch.delenv("CLIPPING_VIEWER_PROFILES_PATH", raising=False)
    else:
        monkeypatch.setenv("CLIPPING_VIEWER_PROFILES_PATH", str(viewer_profiles_path))
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


def test_hosted_dashboard_enables_same_origin_api_polling(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")
    index_path = tmp_path / "index.html"
    index_path.write_text(
        """
        <!doctype html>
        <main id="app" data-clipping-api-url="" data-clipping-static="1"></main>
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr(app_module, "ROOT", tmp_path)

    with TestClient(app) as client:
        login(client)
        response = client.get("/")

    assert response.status_code == 200
    assert 'data-clipping-static="1"' not in response.text
    assert 'data-clipping-static="0"' in response.text
    assert 'data-clipping-session-role="admin"' in response.text


def csrf_header(token: str) -> dict[str, str]:
    return {"X-CSRF-Token": token}


def login_viewer(client: TestClient, password: str = "viewer-shakira") -> None:
    response = client.post("/api/login", json={"password": password})
    assert response.status_code == 200
    assert response.json()["role"] == "viewer"


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


def action_upload_calls(calls):
    return [call for call in calls if not str(call.get("job_id") or "").startswith(("seed-", "startup-"))]


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


def write_scoped_asset_fixture(asset_dir: Path) -> None:
    asset_dir.mkdir(parents=True, exist_ok=True)
    (asset_dir / "clipping-data.json").write_text(
        json.dumps(
            {
                "meta": {"pageTitle": "Fixture", "generatedAt": "2026-05-18", "totalStories": 2, "totalArticles": 2, "totalAi": 0, "totalRaw": 2},
                "targets": [
                    {"key": "flavio_valle", "label": "Flavio Valle", "primary": True},
                    {"key": "shakira", "label": "Shakira", "primary": False},
                ],
                "defaultTargets": ["flavio_valle"],
                "stories": [
                    {
                        "storyIdInt": 1,
                        "title": "Flavio em pauta",
                        "targetKeys": ["flavio_valle"],
                        "articles": [
                            {
                                "articleId": 10,
                                "title": "Flavio em pauta",
                                "targetKeys": ["flavio_valle"],
                                "rawTextKey": "article-10",
                                "summarySource": "raw",
                            }
                        ],
                    },
                    {
                        "storyIdInt": 2,
                        "title": "Shakira no Rio",
                        "targetKeys": ["shakira"],
                        "articles": [
                            {
                                "articleId": 20,
                                "title": "Shakira no Rio",
                                "targetKeys": ["shakira"],
                                "rawTextKey": "article-20",
                                "summarySource": "raw",
                                "classifications": [{"target_key": "shakira", "target_sentiment": "neutral"}],
                            }
                        ],
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (asset_dir / "clipping-raw-texts.json").write_text(
        json.dumps({"article-10": "Texto Flavio", "article-20": "Texto Shakira"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (asset_dir / "clipping.js").write_text("// fixture", encoding="utf-8")


def test_dashboard_payload_and_raw_text_are_password_scoped(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")
    asset_dir = tmp_path / "assets"
    write_scoped_asset_fixture(asset_dir)
    monkeypatch.setattr(app_module, "ASSETS_DIR", asset_dir)

    with TestClient(app) as client:
        assert client.get("/assets/clipping-data.json").status_code == 401
        assert client.get("/assets/clipping-raw-texts.json").status_code == 401
        login_viewer(client, "viewer-shakira")
        data = client.get("/assets/clipping-data.json")
        raw = client.get("/assets/clipping-raw-texts.json")

    assert data.status_code == 200
    payload = data.json()
    assert payload["meta"]["viewerRole"] == "viewer"
    assert payload["meta"]["viewerProfile"] == "shakira"
    assert [target["key"] for target in payload["targets"]] == ["shakira"]
    assert payload["defaultTargets"] == ["shakira"]
    assert [story["title"] for story in payload["stories"]] == ["Shakira no Rio"]
    assert payload["stories"][0]["articles"][0]["targetKeys"] == ["shakira"]
    assert raw.status_code == 200
    assert raw.json() == {"article-20": "Texto Shakira"}


def test_viewer_profile_scope_can_come_from_reviewable_config_file(monkeypatch, tmp_path):
    profiles_path = tmp_path / "viewer_profiles.json"
    profiles_path.write_text(
        json.dumps(
            {
                "profiles": {
                    "shakira": {
                        "label": "Temporary Review Profile",
                        "target_keys": ["flavio_valle"],
                        "default_targets": ["flavio_valle"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    app, _ = load_test_app(monkeypatch, tmp_path, viewer_profiles_path=profiles_path)
    app_module = importlib.import_module("web_app.app")
    asset_dir = tmp_path / "assets"
    write_scoped_asset_fixture(asset_dir)
    monkeypatch.setattr(app_module, "ASSETS_DIR", asset_dir)

    with TestClient(app) as client:
        login_viewer(client, "viewer-shakira")
        data = client.get("/assets/clipping-data.json")

    assert data.status_code == 200
    payload = data.json()
    assert payload["meta"]["viewerProfile"] == "shakira"
    assert payload["meta"]["viewerLabel"] == "Temporary Review Profile"
    assert [target["key"] for target in payload["targets"]] == ["flavio_valle"]
    assert [story["title"] for story in payload["stories"]] == ["Flavio em pauta"]


def test_dashboard_shell_marks_viewer_session_before_payload_load(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        login_viewer(client, "viewer-shakira")
        response = client.get("/")

    assert response.status_code == 200
    assert 'class="viewer-readonly"' in response.text
    assert 'data-clipping-session-role="viewer"' in response.text
    assert 'data-clipping-session-profile="shakira"' in response.text


def test_viewer_cannot_widen_live_results_or_write_admin_actions(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")

    def fake_live_results(*_args, **_kwargs):
        return {
            "jobId": "job",
            "status": "running",
            "items": [
                {"articleId": 1, "targetKeys": ["flavio_valle"], "targetLabels": {"flavio_valle": "Flavio Valle"}},
                {"articleId": 2, "targetKeys": ["shakira"], "targetLabels": {"shakira": "Shakira"}},
            ],
            "count": 2,
        }

    monkeypatch.setattr(app_module, "live_results_for_job", fake_live_results)

    with TestClient(app) as client:
        login_viewer(client, "viewer-shakira")
        all_results = client.get("/api/update/live-results")
        widened = client.get("/api/update/live-results?target_key=flavio_valle")
        write_attempt = client.post("/api/update/start", json={"preset": "rapido"})

    assert all_results.status_code == 200
    assert [item["articleId"] for item in all_results.json()["items"]] == [2]
    assert widened.status_code == 200
    assert widened.json()["items"] == []
    assert write_attempt.status_code == 401


def test_admin_route_is_retired_and_status_requires_login(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        admin_page = client.get("/admin", follow_redirects=False)
        bad_login = client.post("/api/login", json={"password": "wrong-password"})
        status_without_login = client.get("/api/update/status")
        manual_without_login = client.post("/api/manual-story", json=manual_story_payload())
        login(client)
        status = client.get("/api/update/status")

    assert admin_page.status_code == 307
    assert admin_page.headers["location"] == "/"
    assert bad_login.status_code == 401
    assert "clipping_admin" not in bad_login.cookies
    assert status_without_login.status_code == 401
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
    assert status.status_code == 503
    assert manual_without_login.status_code == 503
    assert_empty_db(db_file)


def test_admin_write_apis_reject_missing_or_bad_csrf(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        csrf = login(client)
        responses = [
            client.post("/api/logout"),
            client.post("/api/update/start", json={"preset": "rapido"}),
            client.post("/api/export"),
            client.post("/api/targets", json={"display_name": "Ana Teste"}),
            client.post("/api/categories", json={"name": "Teste"}),
            client.post("/api/classifications", json={"article_id": 1, "target_key": "flavio_valle"}),
            client.post("/api/manual-story", json=manual_story_payload()),
            client.post(
                "/api/manual-story",
                headers={"X-CSRF-Token": f"{csrf}-tampered"},
                json=manual_story_payload(),
            ),
        ]

    assert [response.status_code for response in responses] == [403] * len(responses)
    assert [response.json()["detail"] for response in responses] == ["csrf_check_failed"] * len(responses)
    assert_empty_db(db_file)


def test_update_and_export_workflows_are_admin_endpoints(monkeypatch, tmp_path):
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
        unauth_update = client.post("/api/update/start", json={"preset": "rapido", "export": False})
        csrf = login(client)
        status = client.get("/api/update/status")
        update = client.post("/api/update/start", headers=csrf_header(csrf), json={"preset": "rapido", "export": False})
        export = client.post("/api/export", headers=csrf_header(csrf))

    assert unauth_update.status_code == 401
    assert status.status_code == 200
    assert update.status_code == 200
    assert export.status_code == 200
    assert calls == [
        ("update", {"preset": "rapido", "export": False}, "admin"),
        ("export", {}, "admin"),
    ]


def test_cancel_update_is_admin_and_returns_cancelled_job(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")

    def fake_cancel_active():
        return {"id": "cancelled-job", "status": "cancelled"}

    monkeypatch.setattr(app_module.job_manager, "cancel_active", fake_cancel_active)

    with TestClient(app) as client:
        csrf = login(client)
        response = client.post("/api/update/cancel", headers=csrf_header(csrf))

    assert response.status_code == 200
    assert response.json() == {"id": "cancelled-job", "status": "cancelled"}


def test_cancel_update_returns_409_when_no_active_job(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")

    def fake_cancel_active():
        raise app_module.JobConflict("no_active_job")

    monkeypatch.setattr(app_module.job_manager, "cancel_active", fake_cancel_active)

    with TestClient(app) as client:
        csrf = login(client)
        response = client.post("/api/update/cancel", headers=csrf_header(csrf))

    assert response.status_code == 409
    assert response.json()["detail"] == "no_active_job"


def test_resume_update_is_admin_endpoint(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")
    calls = []

    def fake_resume_update(job_id="", *, started_by):
        calls.append((job_id, started_by))
        return {"id": job_id or "latest-resumable", "status": "queued"}

    monkeypatch.setattr(app_module.job_manager, "resume_update", fake_resume_update)

    with TestClient(app) as client:
        csrf = login(client)
        response = client.post("/api/update/resume", headers=csrf_header(csrf), json={"job_id": "durable-job"})

    assert response.status_code == 200
    assert response.json() == {"id": "durable-job", "status": "queued"}
    assert calls == [("durable-job", "admin")]


def test_targets_api_is_login_scoped_and_admin_uploads_target_manifest(monkeypatch, tmp_path):
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
        unauth_listed = client.get("/api/targets")
        csrf = login(client)
        listed = client.get("/api/targets")
        created = client.post("/api/targets", headers=csrf_header(csrf), json={"label": "Ana Teste"})

    assert unauth_listed.status_code == 401
    assert listed.status_code == 200
    assert listed.json() == {
        "targets": [{"key": "flavio_valle", "label": "Flavio Valle"}],
        "primaryKeys": [],
    }
    assert created.status_code == 200
    assert created.json()["key"] == "ana_teste"
    assert created.json()["uploadedArtifactCount"] == 2
    target_upload_calls = action_upload_calls(upload_calls)
    assert target_upload_calls == [
        {
            "manifest": {"kind": "targets-created", "result": {"key": "ana_teste", "label": "Ana Teste", "primary": False}},
            "job_id": "targets-created-ana_teste",
        }
    ]
    assert_no_secret_material({"created": created.json(), "upload_calls": target_upload_calls})


def test_targets_api_lists_archived_and_uploads_management_manifests(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")
    upload_calls = []
    all_targets = [
        {"key": "flavio_valle", "label": "Flavio Valle", "primary": True, "archived": False},
        {"key": "ana_teste", "label": "Ana Teste", "primary": False, "archived": False},
        {"key": "beta_antigo", "label": "Beta Antigo", "primary": False, "archived": True},
    ]

    def fake_public_targets(*, include_archived=False):
        rows = all_targets if include_archived else [row for row in all_targets if not row.get("archived")]
        return {"targets": rows, "primaryKeys": ["flavio_valle"]}

    monkeypatch.setattr(app_module, "public_targets", fake_public_targets)
    monkeypatch.setattr(
        app_module,
        "update_secondary_target",
        lambda key, payload: {"key": key, "label": payload["display_name"], "primary": False, "archived": False},
    )
    monkeypatch.setattr(
        app_module,
        "archive_secondary_target",
        lambda key, reason="": {"key": key, "label": "Ana Teste", "primary": False, "archived": True, "archive_reason": reason},
    )
    monkeypatch.setattr(
        app_module,
        "restore_secondary_target",
        lambda key: {"key": key, "label": "Beta Antigo", "primary": False, "archived": False},
    )
    monkeypatch.setattr(app_module.artifact_store, "enabled", True)

    def fake_upload_current_artifacts(*, manifest=None, job_id=None):
        upload_calls.append({"manifest": manifest, "job_id": job_id})
        return ["data/targets.json", "assets/clipping-data.json"]

    monkeypatch.setattr(app_module.artifact_store, "upload_current_artifacts", fake_upload_current_artifacts)

    with TestClient(app) as client:
        csrf = login(client)
        active = client.get("/api/targets")
        with_archived = client.get("/api/targets?include_archived=1")
        updated = client.patch("/api/targets/ana_teste", headers=csrf_header(csrf), json={"display_name": "Ana Nova"})
        archived = client.post(
            "/api/targets/ana_teste/archive",
            headers=csrf_header(csrf),
            json={"reason": "Duplicado."},
        )
        restored = client.post("/api/targets/beta_antigo/restore", headers=csrf_header(csrf))

    assert [row["key"] for row in active.json()["targets"]] == ["flavio_valle", "ana_teste"]
    assert [row["key"] for row in with_archived.json()["targets"]] == ["flavio_valle", "ana_teste", "beta_antigo"]
    assert updated.status_code == 200
    assert archived.status_code == 200
    assert restored.status_code == 200
    target_upload_calls = [
        call for call in upload_calls if str((call.get("manifest") or {}).get("kind") or "").startswith("targets-")
    ]
    assert [call["manifest"]["kind"] for call in target_upload_calls] == [
        "targets-updated",
        "targets-archived",
        "targets-restored",
    ]


def test_target_mutations_remain_available_while_update_is_active(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")
    monkeypatch.setattr(app_module.job_manager, "current_status", lambda: {"id": "update-running", "status": "running"})
    monkeypatch.setattr(
        app_module,
        "create_secondary_target",
        lambda payload: {"key": "ana_teste", "label": payload["display_name"], "primary": False},
    )
    monkeypatch.setattr(
        app_module,
        "update_secondary_target",
        lambda key, payload: {"key": key, "label": payload["display_name"], "primary": False, "archived": False},
    )
    monkeypatch.setattr(
        app_module,
        "archive_secondary_target",
        lambda key, reason="": {"key": key, "label": "Ana Teste", "primary": False, "archived": True, "archive_reason": reason},
    )
    monkeypatch.setattr(
        app_module,
        "restore_secondary_target",
        lambda key: {"key": key, "label": "Ana Teste", "primary": False, "archived": False},
    )
    monkeypatch.setattr(
        app_module,
        "record_target_sync",
        lambda key, **_kwargs: {
            "jobId": f"sync-{key}",
            "targetKey": key,
            "updatedCount": 0,
            "mentionsInserted": 0,
            "storiesTouched": 0,
            "cleanup": {},
        },
    )
    monkeypatch.setattr(app_module.artifact_store, "enabled", False)

    with TestClient(app) as client:
        csrf = login(client)
        responses = [
            client.post("/api/targets", headers=csrf_header(csrf), json={"display_name": "Ana Teste"}),
            client.patch("/api/targets/ana_teste", headers=csrf_header(csrf), json={"display_name": "Ana Nova"}),
            client.post(
                "/api/targets/ana_teste/archive",
                headers=csrf_header(csrf),
                json={"reason": "Duplicado."},
            ),
            client.post("/api/targets/ana_teste/restore", headers=csrf_header(csrf)),
        ]

    assert [response.status_code for response in responses] == [200, 200, 200, 200]
    payloads = [response.json() for response in responses]
    assert all(payload["activeJob"]["status"] == "running" for payload in payloads)
    assert all("continua com os nomes congelados" in payload["activeJobNotice"] for payload in payloads)
    assert payloads[0]["targetSync"]["targetKey"] == "ana_teste"
    assert payloads[1]["targetSync"]["targetKey"] == "ana_teste"
    assert "targetSync" not in payloads[2]
    assert payloads[3]["targetSync"]["targetKey"] == "ana_teste"


def test_targets_api_returns_real_public_targets_contract(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)

    with TestClient(app) as client:
        login(client)
        response = client.get("/api/targets")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["targets"], list)
    assert payload["primaryKeys"] == ["flavio_valle", "pedro_angelito"]

    by_key = {target["key"]: target for target in payload["targets"]}
    for key in payload["primaryKeys"]:
        assert by_key[key]["primary"] is True
        assert by_key[key]["className"] == "primary"
    assert by_key["bernardo_rubiao"]["primary"] is False
    assert by_key["bernardo_rubiao"]["className"] == ""


def test_targets_api_validation_errors_are_public_400s(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")

    def fail_create(_payload):
        raise app_module.ValidationError("Nome acompanhado invalido.")

    monkeypatch.setattr(app_module, "create_secondary_target", fail_create)

    with TestClient(app) as client:
        csrf = login(client)
        response = client.post("/api/targets", headers=csrf_header(csrf), json={"label": ""})

    assert response.status_code == 400
    payload = response.json()
    assert payload["message"] == "Nome acompanhado invalido."
    assert payload["detail"]["message"] == "Nome acompanhado invalido."
    assert payload["detail"]["field"] == "display_name"
    assert "Revise" in payload["detail"]["suggestion"]


def test_targets_api_short_name_error_explains_field_and_fix(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    db_admin = importlib.import_module("web_app.db_admin")
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {
                    "key": "flavio_valle",
                    "label": "Flavio Valle",
                    "display_name": "Flavio Valle",
                    "primary": True,
                    "keywords": ["Flavio Valle"],
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)

    with TestClient(app) as client:
        csrf = login(client)
        response = client.post("/api/targets", headers=csrf_header(csrf), json={"display_name": "ab"})

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"] == "target_validation_error"
    assert payload["message"] == "Informe um nome de exibicao com pelo menos 3 caracteres."
    assert payload["field"] == "display_name"
    assert payload["suggestion"] == "Digite um nome de exibicao com 3 caracteres ou mais."
    assert payload["detail"] == {
        "code": "target_validation_error",
        "message": "Informe um nome de exibicao com pelo menos 3 caracteres.",
        "field": "display_name",
        "suggestion": "Digite um nome de exibicao com 3 caracteres ou mais.",
    }
    assert "Não foi possível" not in json.dumps(payload, ensure_ascii=False)


def test_targets_api_operation_errors_are_structured(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")

    def fail_create(_payload):
        raise RuntimeError("targets file is not writable")

    monkeypatch.setattr(app_module, "create_secondary_target", fail_create)

    with TestClient(app) as client:
        csrf = login(client)
        response = client.post("/api/targets", headers=csrf_header(csrf), json={"display_name": "Ana Teste"})

    assert response.status_code == 500
    payload = response.json()
    assert payload["error"] == "target_operation_failed"
    assert payload["message"] == "Não foi possível salvar este nome."
    assert "targets.json" in payload["suggestion"]
    assert "RuntimeError" in payload["detail"]["cause"]


def test_healthz_exposes_safe_operational_fields(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "ok",
        "dbExists",
        "authConfigured",
        "loginConfigured",
        "viewerAuthConfigured",
        "demoViewerConfigured",
        "viewerProfilesConfigured",
        "missingConfig",
        "storage",
        "localWritesAllowed",
        "job",
        "shakiraLoopVersion",
    }
    assert payload["ok"] is True
    assert payload["dbExists"] is True
    assert payload["authConfigured"] is True
    assert payload["loginConfigured"] is True
    assert payload["viewerAuthConfigured"] is True
    assert payload["demoViewerConfigured"] is False
    assert payload["viewerProfilesConfigured"] is True
    assert payload["missingConfig"] == []
    assert payload["localWritesAllowed"] is True
    assert set(payload["storage"]) == {"enabled", "bucket", "prefix", "localWritesAllowed"}
    assert payload["storage"]["enabled"] is False
    assert payload["storage"]["localWritesAllowed"] is True
    serialized = json.dumps(payload, sort_keys=True)
    assert "test-password" not in serialized
    assert "test-session-secret" not in serialized
    assert "SUPABASE_SERVICE_KEY" not in serialized


def test_healthz_lists_missing_viewer_password_config(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    monkeypatch.delenv("CLIPPING_VIEWER_PASSWORDS", raising=False)
    with TestClient(app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    payload = response.json()
    assert payload["loginConfigured"] is True
    assert payload["viewerAuthConfigured"] is False
    assert payload["demoViewerConfigured"] is True
    assert payload["missingConfig"] == ["CLIPPING_VIEWER_PASSWORDS"]
    assert "test-password" not in json.dumps(payload, sort_keys=True)


def test_empty_demo_viewer_login_works_without_viewer_password_env(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    monkeypatch.delenv("CLIPPING_VIEWER_PASSWORDS", raising=False)

    with TestClient(app) as client:
        login_response = client.post("/api/login", json={"password": "demo-cliente"})
        payload_response = client.get("/assets/clipping-data.json")
        raw_response = client.get("/assets/clipping-raw-texts.json")
        targets_response = client.get("/api/targets")
        write_response = client.post("/api/targets", json={"display_name": "Nao Pode"})

    assert login_response.status_code == 200
    assert login_response.json() == {"ok": True, "role": "viewer", "profile": "demo_cliente"}
    assert payload_response.status_code == 200
    payload = payload_response.json()
    assert payload["meta"]["viewerRole"] == "viewer"
    assert payload["meta"]["viewerProfile"] == "demo_cliente"
    assert payload["targets"] == []
    assert payload["stories"] == []
    assert raw_response.status_code == 200
    assert raw_response.json() == {}
    assert targets_response.status_code == 200
    assert targets_response.json()["targets"] == []
    assert write_response.status_code == 401


def test_empty_demo_password_disabled_when_real_viewer_passwords_exist(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)

    with TestClient(app) as client:
        response = client.post("/api/login", json={"password": "demo-cliente"})

    assert response.status_code == 401


def test_empty_demo_password_disabled_if_demo_profile_has_targets(monkeypatch, tmp_path):
    profiles_path = tmp_path / "viewer_profiles.json"
    profiles_path.write_text(
        json.dumps({"profiles": {"demo_cliente": {"label": "Demo", "target_keys": ["flavio_valle"]}}}),
        encoding="utf-8",
    )
    app, _ = load_test_app(monkeypatch, tmp_path, viewer_profiles_path=profiles_path)
    monkeypatch.delenv("CLIPPING_VIEWER_PASSWORDS", raising=False)

    with TestClient(app) as client:
        login_response = client.post("/api/login", json={"password": "demo-cliente"})
        health_response = client.get("/healthz")

    assert login_response.status_code == 401
    assert health_response.status_code == 200
    assert health_response.json()["demoViewerConfigured"] is False


def test_storage_current_files_are_runtime_mutable_only(monkeypatch, tmp_path):
    load_test_app(monkeypatch, tmp_path)
    storage_bridge = importlib.import_module("web_app.storage_bridge")
    requested = []
    gzip_requested = []

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

    def fake_download_gzip(remote_path, local_path):
        gzip_requested.append(remote_path)
        return remote_path.endswith("data/clipping.db.gz")

    def fake_download(remote_path, local_path):
        requested.append(remote_path)
        return True

    monkeypatch.setattr(storage_bridge.artifact_store, "download_gzip_file", fake_download_gzip)
    monkeypatch.setattr(storage_bridge.artifact_store, "download_file", fake_download)
    assert storage_bridge.artifact_store.download_current_artifacts() == paths
    assert gzip_requested == ["clipping-project/current/data/clipping.db.gz"]
    assert requested == [f"clipping-project/current/{path}" for path in paths[1:]]


def test_fastapi_app_does_not_serve_report_exports_as_private_surface(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        response = client.get("/data/reports/clipping_mobile_snapshot_all_stories.html")

    assert response.status_code == 404


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
            login(client)
            status = client.get("/api/update/status")

        assert status.status_code == 200
        _, observed = assert_status_exposes_artifact_upload(status.json(), OBSERVED_UPLOAD_PATHS, job_id=job_id)
        assert observed["kind"] == kind
        assert_no_secret_material(status.json())


def test_live_results_endpoint_returns_saved_articles_before_export(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path)
    jobs = importlib.import_module("web_app.jobs")
    monkeypatch.setattr(jobs, "target_labels", lambda include_archived=False: {"shakira": "shakira"})
    job_id = "live-api-job"
    jobs.create_job(
        job_id,
        "update",
        {
            "preset": "custom",
            "collector": "all",
            "target_keys": ["shakira"],
            "date_from": "2026-04-01",
            "date_to": "2026-05-04",
        },
        started_by="coworker",
    )
    jobs.update_job(job_id, status="running")
    with ClippingDB(db_file) as db:
        article_id = db.insert_article(
            url="https://example.com/shakira-live-api",
            title="Shakira tem notícia salva durante a rodada",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-05-01T12:00:00+00:00",
            snippet="Shakira aparece antes do export.",
            full_text="Shakira aparece antes do export.",
        )
        assert article_id is not None
        db.insert_mention(article_id, "shakira", "shakira", "shakira")
        story_id = db.create_story(
            title="Shakira tem notícia salva durante a rodada",
            summary="Resumo sobre Shakira.",
            temperature=34.0,
            target_keys=["shakira"],
        )
        db.attach_article_to_story(story_id, article_id)

    jobs.record_progress(
        job_id,
        "article_saved",
        {
            "article_id": article_id,
            "story_id": story_id,
            "title": "Shakira tem notícia salva durante a rodada",
            "url": "https://example.com/shakira-live-api",
            "published_at": "2026-05-01T12:00:00+00:00",
            "source_name": "Fonte Teste",
            "source_type": "test",
            "target_keys": ["shakira"],
            "articles_inserted_delta": 1,
            "mentions_inserted_delta": 1,
            "stories_touched_delta": 1,
            "publication_state": "saved",
        },
        target_key="shakira",
        target_label="shakira",
    )

    with TestClient(app) as client:
        login_viewer(client, "viewer-shakira")
        response = client.get(f"/api/update/live-results?job_id={job_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["items"][0]["title"] == "Shakira tem notícia salva durante a rodada"
    assert payload["items"][0]["publicationState"] == "saved"


def test_target_create_syncs_live_base_and_export_filter(monkeypatch, tmp_path):
    app, db_file = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")
    db_admin = importlib.import_module("web_app.db_admin")
    jobs = importlib.import_module("web_app.jobs")
    settings = importlib.import_module("pipeline.settings")
    export_mobile_snapshot = importlib.import_module("tools.export_mobile_snapshot")
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {
                    "key": "flavio_valle",
                    "label": "Flavio Valle",
                    "display_name": "Flavio Valle",
                    "primary": True,
                    "keywords": ["Flavio Valle"],
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(db_admin, "TARGETS_PATH", targets_path)
    monkeypatch.setattr(settings, "TARGETS_JSON_PATH", targets_path)
    monkeypatch.setattr(export_mobile_snapshot, "TARGETS_PATH", targets_path)
    monkeypatch.setattr(app_module.artifact_store, "enabled", False)
    monkeypatch.setattr(jobs.artifact_store, "enabled", False)
    with ClippingDB(db_file) as db:
        article_id = db.insert_article(
            url="https://example.com/shakira-integrada",
            title="Shakira entra no clipping integrado",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-05-17T12:00:00+00:00",
            snippet="Shakira aparece na base antes do cadastro do nome.",
            full_text="Shakira aparece na base antes do cadastro do nome.",
        )
        assert article_id is not None

    with TestClient(app) as client:
        csrf = login(client)
        created = client.post("/api/targets", headers=csrf_header(csrf), json={"display_name": "Shakira"})
        live = client.get("/api/update/live-results?scope=base&target_key=shakira&limit=20")

    assert created.status_code == 200, created.text
    created_payload = created.json()
    assert created_payload["key"] == "shakira"
    assert created_payload["targetSync"]["updatedCount"] == 1
    assert created_payload["targetSync"]["mentionsInserted"] == 1
    assert live.status_code == 200
    live_payload = live.json()
    assert live_payload["count"] == 1
    assert live_payload["items"][0]["title"] == "Shakira entra no clipping integrado"
    assert live_payload["items"][0]["targetKeys"] == ["shakira"]

    with sqlite3.connect(db_file) as conn:
        mention_targets = {
            row[0]
            for row in conn.execute("SELECT target_key FROM mentions WHERE article_id = ?", (article_id,)).fetchall()
        }
        story_targets = {
            row[0]
            for row in conn.execute(
                """
                SELECT st.target_key
                FROM story_targets st
                JOIN story_articles sa ON sa.story_id = st.story_id
                WHERE sa.article_id = ?
                """,
                (article_id,),
            ).fetchall()
        }
    assert mention_targets == {"shakira"}
    assert story_targets == {"shakira"}

    artifact = export_mobile_snapshot.build_snapshot_artifact(
        argparse.Namespace(
            db=str(db_file),
            date_from="",
            date_to="",
            all_stories=True,
            default_target="shakira",
            output=str(tmp_path / "index.html"),
            merge_from="",
            remap_incoming_ids_on_merge=False,
            api_url="",
        )
    )
    payload = artifact["data_payload"]
    by_target = {row["key"]: row for row in payload["targets"]}
    assert by_target["shakira"]["storyCount"] == 1
    assert by_target["shakira"]["articleCount"] == 1
    assert payload["defaultTargets"] == ["shakira"]
    assert payload["meta"]["initialArticleCount"] == 1
    assert payload["stories"][0]["targetKeys"] == ["shakira"]
    assert payload["stories"][0]["articles"][0]["targetKeys"] == ["shakira"]


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
    manual_upload_calls = action_upload_calls(upload_calls)
    assert len(manual_upload_calls) == 1
    assert manual_upload_calls[0]["manifest"]["kind"] == "manual-story"
    assert manual_upload_calls[0]["manifest"]["result"]["articleId"] == result["articleId"]

    assert status.status_code == 200
    _, observed = assert_status_exposes_artifact_upload(status.json(), uploaded_paths)
    assert observed["kind"] == "manual"
    assert observed["status"] == "succeeded"
    assert_db_artifact_event(db_file, observed["id"], uploaded_paths)
    assert_no_secret_material({"response": result, "status": status.json(), "upload_calls": manual_upload_calls})


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
    manual_upload_calls = action_upload_calls(upload_calls)
    assert len(manual_upload_calls) == 2
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
    assert_no_secret_material({"response": second.json(), "status": status.json(), "upload_calls": manual_upload_calls})


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
    assert "Rodar atualização" in html
    assert "Notícias disponíveis para consulta" in html
    assert "Textos completos" in html
    assert "Com texto para leitura" not in html
    assert "Cancelar atualização" not in html
    assert '<details class="advanced-search-box">' in html
    assert "Ajustar busca" in html
    assert "Termos relacionados" in html
    assert "Correspondências exatas" in html
    assert "Gerenciar nomes secundários" in html
    assert 'type="date"' not in html
    assert "Data inicial (DD/MM/AAAA)" in html
    assert "Data final (DD/MM/AAAA)" in html
    assert 'placeholder="DD/MM/AAAA"' in html
    assert 'inputmode="numeric"' in html
    assert "build:" not in html
    assert "DOM" not in html
    assert "RAM" not in html
    assert "API local" not in html


def test_public_runner_javascript_contract():
    script = Path("assets/clipping.js").read_text(encoding="utf-8")
    assert "console.log" not in script
    assert "classification editor ENABLED" not in script
    assert "normalizeTargetsResponse(data, options)" in script
    assert "mergeRuntimeTargetsIntoPayload" in script
    assert "payloadCountsForTarget" in script
    assert "brDateToIso" in script
    assert "isoToBrDate" in script
    assert "Histórias salvas nesta rodada" in script
    assert "refreshManageTargets" in script
    assert "disabled = target.primary" not in script
    assert "+ checked + disabled" not in script
