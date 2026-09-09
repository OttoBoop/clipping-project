"""API boundary tests with an explicitly simulated persistence service.

PostgreSQL persistence is covered by test_political_corpus; this module checks
real authentication, scope/CSRF rules, payload construction, and HTTP routing.
"""
from copy import deepcopy
import importlib
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from test_admin_viewers import login_and_csrf, reload_app


class FakePoliticalCorpus:
    """Deterministic browser fixture using the production DTO field shapes."""

    configured = True

    def __init__(self):
        self.calls = []
        self.job = None
        self.records = [
            {"id": 101, "title": "Eduardo Paes e Flávio Valle discutem mobilidade no Rio",
             "url": "https://example.com/politica/101", "sourceName": "Fonte simulada RJ",
             "sourceKey": "fixture_rj", "publishedAt": "2026-09-08T12:00:00+00:00",
             "summary": "Registro fictício para testar o site; nenhuma notícia real foi coletada.",
             "targetKeys": ["flavio_valle", "eduardo_paes"], "bodyStatus": "body_extracted", "storyId": 11},
            {"id": 102, "title": "Paes apresenta proposta em encontro no estado",
             "url": "https://example.com/politica/102", "sourceName": "Fonte simulada RJ",
             "sourceKey": "fixture_rj", "publishedAt": "2026-09-07T12:00:00+00:00",
             "snippet": "Referência simulada, sem texto integral.",
             "targetKeys": ["eduardo_paes"], "bodyStatus": "metadata_only", "storyId": 11},
            {"id": 103, "title": "Flávio Valle participa de audiência na Câmara do Rio",
             "url": "https://example.com/politica/103", "sourceName": "Fonte simulada Câmara",
             "sourceKey": "fixture_camara", "publishedAt": "2026-06-20T12:00:00+00:00",
             "summary": "Segunda página de resultados simulados.",
             "targetKeys": ["flavio_valle"], "bodyStatus": "body_extracted", "storyId": 12},
        ]
        self.classified = {(101, "flavio_valle"): {
            "article_sentiment": "positive", "target_sentiment": "neutral",
            "categories": ["Mobilidade"], "centimetragem": 12.5, "ai_generated": False,
        }}

    def record(self, method, **kwargs):
        self.calls.append({"method": method, **deepcopy(kwargs)})

    def article(self, article_id, allowed_target_keys):
        row = next((r for r in self.records if r["id"] == article_id), None)
        if row is None or not set(row["targetKeys"]).intersection(allowed_target_keys):
            raise LookupError("not_found")
        return {**row, "targetKeys": [k for k in row["targetKeys"] if k in allowed_target_keys]}

    def status(self, job_id="", *, allowed_target_keys):
        self.record("status", job_id=job_id, allowed_target_keys=allowed_target_keys)
        if job_id and self.job and job_id != self.job["id"]:
            raise LookupError("unknown_job")
        return {"current": deepcopy(self.job), "recent": [], "workers": []}

    def list_articles(self, **kwargs):
        self.record("list_articles", **kwargs)
        allowed = kwargs["allowed_target_keys"]
        selected = kwargs.get("target_keys") or allowed
        rows = [self.article(r["id"], allowed) for r in self.records
                if set(r["targetKeys"]).intersection(selected) and set(r["targetKeys"]).intersection(allowed)]
        if kwargs.get("body_status"):
            rows = [r for r in rows if r["bodyStatus"] == kwargs["body_status"]]
        if kwargs.get("story_id"):
            rows = [r for r in rows if r["storyId"] == int(kwargs["story_id"])]
        start = 2 if kwargs.get("cursor") == "fixture-next" else 0
        items = rows[start:start + min(kwargs.get("page_size", 50), 2)]
        more = start + len(items) < len(rows)
        return {"items": items, "hasMore": more, "nextCursor": "fixture-next" if more else ""}

    def list_stories(self, **kwargs):
        self.record("list_stories", **kwargs)
        articles = self.list_articles(**kwargs)["items"]
        return {"items": [{"id": 11, "title": "História simulada",
                           "articles": articles, "articleCount": 3, "hasMoreArticles": True}],
                "hasMore": False, "nextCursor": ""}

    def article_text(self, article_id, *, allowed_target_keys):
        self.record("article_text", article_id=article_id, allowed_target_keys=allowed_target_keys)
        row = self.article(article_id, allowed_target_keys)
        return {"id": article_id, "bodyStatus": row["bodyStatus"],
                "text": "Texto integral simulado para verificar leitura sob demanda. " * 8}

    def classifications(self, article_id, *, allowed_target_keys):
        self.record("classifications", article_id=article_id, allowed_target_keys=allowed_target_keys)
        row = self.article(article_id, allowed_target_keys)
        return {"articleId": article_id, "items": [
            {"targetKey": key, "payload": deepcopy(payload), "updatedBy": "fixture_editor",
             "updatedAt": "2026-09-09T12:00:00+00:00", "legacyId": None}
            for (aid, key), payload in self.classified.items()
            if aid == article_id and key in row["targetKeys"]
        ]}

    def upsert_classification(self, article_id, payload, *, allowed_target_keys, updated_by):
        self.record("upsert_classification", article_id=article_id, payload=payload,
                    allowed_target_keys=allowed_target_keys, updated_by=updated_by)
        key = payload.get("target_key") or payload.get("targetKey")
        if key not in allowed_target_keys:
            raise PermissionError("target_scope")
        self.article(article_id, [key])
        content = payload.get("payload") if isinstance(payload.get("payload"), dict) else {
            k: v for k, v in payload.items() if k not in {"target_key", "targetKey"}
        }
        self.classified[(article_id, key)] = deepcopy(content)
        return self.classifications(article_id, allowed_target_keys=allowed_target_keys)

    def coverage(self, job_id="", *, allowed_target_keys):
        self.record("coverage", job_id=job_id, allowed_target_keys=allowed_target_keys)
        return {"items": [{"sourceKey": "fixture_rj", "sourceName": "Fonte simulada RJ",
                           "dateFrom": "2026-06-01", "dateTo": "2026-09-09", "status": "gap",
                           "error_type": "google_daily_result_cap"}]}

    def start_job(self, payload, *, started_by, allowed_target_keys):
        self.record("start_job", payload=payload, started_by=started_by, allowed_target_keys=allowed_target_keys)
        self.job = {"id": "fixture-job", "status": "queued", "dateFrom": payload["date_from"],
                    "dateTo": payload.get("date_to", "2026-09-09"), "metrics": {
                        "uniqueCandidates": 17, "articlesInserted": 3, "duplicates": 2,
                        "mentionsInserted": 5, "bodyExtracted": 4, "fetchPending": 1, "unknownDates": 2,
                        "tasks": [{"kind": "discovery", "status": "gap", "count": 1}],
                    }}
        return deepcopy(self.job)

    def cancel_job(self, job_id, *, allowed_target_keys):
        self.record("cancel_job", job_id=job_id, allowed_target_keys=allowed_target_keys)
        if self.job:
            self.job["status"] = "cancelled"
        return deepcopy(self.job)

    def resume_job(self, job_id, *, allowed_target_keys):
        self.record("resume_job", job_id=job_id, allowed_target_keys=allowed_target_keys)
        if self.job:
            self.job["status"] = "queued"
        return deepcopy(self.job)

    def insert_manual_story(self, payload, *, allowed_target_keys, created_by):
        self.record("insert_manual_story", payload=payload, allowed_target_keys=allowed_target_keys, created_by=created_by)
        return {"id": 104, "storyId": 13, "title": payload["title"], "url": payload["url"],
                "targetKeys": payload["target_keys"], "bodyStatus": "body_extracted"}


def configure_fixture(monkeypatch, tmp_path):
    _, app_module, _, _ = reload_app(monkeypatch, tmp_path)
    routes = importlib.import_module("web_app.political_routes")
    admin = importlib.import_module("web_app.db_admin")
    manifest = json.loads((Path(__file__).resolve().parents[1] / "data/political_targets_v1.json").read_text())
    rows = manifest["targets"]
    next(r for r in rows if r["key"] == "otto_alencar")["archived"] = True
    rows.append({"key": "shakira", "label": "Shakira", "display_name": "Shakira", "keywords": ["Shakira"], "primary": False})
    admin.TARGETS_PATH.write_text(json.dumps(rows), encoding="utf-8")
    service = FakePoliticalCorpus()
    monkeypatch.setattr(routes, "political_corpus", service)
    monkeypatch.setattr(app_module, "political_corpus", service)
    return app_module, routes, service


@pytest.fixture
def site(monkeypatch, tmp_path):
    app, routes, service = configure_fixture(monkeypatch, tmp_path)
    return TestClient(app.app), routes, service


READ_PATHS = ["/politica", "/api/political/meta", "/api/political/sources", "/api/political/status",
              "/api/political/articles", "/api/political/stories", "/api/political/coverage",
              "/api/political/articles/101/text", "/api/political/articles/101/classifications"]


@pytest.mark.parametrize("path", READ_PATHS)
def test_logged_out_political_endpoints_require_authentication(site, path):
    client, _, fake = site
    assert client.get(path).status_code == 401
    assert not fake.calls


@pytest.mark.parametrize("path", READ_PATHS)
def test_other_profile_cannot_read_political_data(site, path):
    client, _, fake = site
    login_and_csrf(client, "viewer-shakira")
    assert client.get(path).status_code == 403
    assert not fake.calls


def test_profile_scope_is_forwarded_and_cannot_be_widened_by_query(site):
    client, _, fake = site
    login_and_csrf(client, "viewer-flavio")
    meta = client.get("/api/political/meta").json()
    assert [r["key"] for r in meta["targets"]] == ["flavio_valle"]
    assert meta["canRun"] is False
    response = client.get("/api/political/articles?as_profile=admin&page_size=99999")
    assert response.status_code == 200
    assert all(r["targetKeys"] == ["flavio_valle"] for r in response.json()["items"])
    call = fake.calls[-1]
    assert call["allowed_target_keys"] == ["flavio_valle"] and call["page_size"] == 200
    assert client.get("/api/political/articles?target_key=eduardo_paes").status_code == 403


def test_admin_simulation_is_scoped_and_all_mutations_read_only(site):
    client, _, fake = site
    csrf = login_and_csrf(client, "test-password")
    response = client.get("/api/political/meta?as_profile=flavio")
    assert response.status_code == 200 and response.json()["canRun"] is False
    assert [r["key"] for r in response.json()["targets"]] == ["flavio_valle"]
    for path in ["/api/political/jobs", "/api/political/manual-story", "/api/political/articles/101/classifications",
                 "/api/political/jobs/example/resume", "/api/political/jobs/example/cancel"]:
        response = client.post(path + "?as_profile=flavio", headers={"X-CSRF-Token": csrf}, json={"target_keys": ["flavio_valle"]})
        assert response.status_code == 403 and response.json()["detail"] == "simulation_is_read_only"
    assert not fake.calls


@pytest.mark.parametrize("path", ["/api/political/jobs", "/api/political/manual-story",
    "/api/political/articles/101/classifications", "/api/political/jobs/example/resume", "/api/political/jobs/example/cancel"])
def test_mutations_require_csrf_and_do_not_call_service_when_missing(site, path):
    client, _, fake = site
    login_and_csrf(client, "test-password")
    response = client.post(path, json={"target_keys": ["flavio_valle"]})
    assert response.status_code == 403 and response.json()["detail"] == "csrf_check_failed"
    assert not fake.calls


def test_start_job_uses_server_snapshots_and_only_explicit_actions_start_jobs(site):
    client, _, fake = site
    csrf = login_and_csrf(client, "test-password")
    for path in READ_PATHS:
        assert client.get(path).status_code == 200
    assert not any(c["method"] == "start_job" for c in fake.calls)
    response = client.post("/api/political/jobs", headers={"X-CSRF-Token": csrf}, json={
        "target_keys": ["flavio_valle", "flavio_valle"], "kind": "collect", "scope": "shakira",
        "target_snapshots": [{"key": "shakira", "keywords": ["everything"]}],
    })
    assert response.status_code == 200
    payload = next(c for c in fake.calls if c["method"] == "start_job")["payload"]
    assert payload["scope"] == "politica_rj_2026" and payload["date_from"] == "2026-06-01"
    assert [r["key"] for r in payload["target_snapshots"]] == ["flavio_valle"]
    assert payload["target_snapshots"][0]["keywords"] != ["everything"]
    assert client.post("/api/political/jobs", headers={"X-CSRF-Token": csrf}, json={"target_keys": ["otto_alencar"]}).status_code == 400


def test_viewer_can_classify_only_accessible_articles_and_read_text_on_demand(site):
    client, _, fake = site
    csrf = login_and_csrf(client, "viewer-flavio")
    assert client.get("/api/political/articles").status_code == 200
    assert not any(c["method"] == "article_text" for c in fake.calls)
    assert client.get("/api/political/articles/101/text").status_code == 200
    assert client.get("/api/political/articles/102/text").status_code == 404
    response = client.get("/api/political/articles/101/classifications")
    assert response.json()["items"][0]["payload"]["categories"] == ["Mobilidade"]
    response = client.post("/api/political/articles/101/classifications", headers={"X-CSRF-Token": csrf}, json={
        "target_key": "flavio_valle", "article_sentiment": "negative", "ai_generated": True,
    })
    assert response.status_code == 200
    call = next(c for c in fake.calls if c["method"] == "upsert_classification")
    assert call["allowed_target_keys"] == ["flavio_valle"] and call["payload"]["ai_generated"] is False
    assert client.post("/api/political/articles/101/classifications", headers={"X-CSRF-Token": csrf}, json={"target_key": "eduardo_paes"}).status_code == 403
    assert client.post("/api/political/jobs", headers={"X-CSRF-Token": csrf}, json={"target_keys": ["flavio_valle"]}).status_code == 401


def test_invalid_payloads_and_errors_have_bounded_sanitized_responses(site, monkeypatch):
    client, _, fake = site
    csrf = login_and_csrf(client, "test-password")
    assert client.get("/api/political/articles?page_size=bad").status_code == 400
    for payload in [[], "text", 7]:
        assert client.post("/api/political/jobs", headers={"X-CSRF-Token": csrf}, json=payload).status_code == 400
    def fail(**_):
        raise Exception("postgresql://secret-user:secret-password@database")
    monkeypatch.setattr(fake, "list_articles", fail)
    response = client.get("/api/political/articles")
    assert response.status_code == 503
    assert "secret" not in response.text and response.json()["detail"] == "political_service_unavailable"


def test_political_page_and_script_do_not_reference_global_archive_bundles(site):
    client, _, _ = site
    login_and_csrf(client, "test-password")
    for path in ["/politica", "/assets/political.js"]:
        response = client.get(path)
        assert response.status_code == 200
        assert "clipping-data.json" not in response.text
        assert "clipping-raw-texts.json" not in response.text


def test_oversized_json_is_rejected_before_service_write(site):
    client, _, fake = site
    csrf = login_and_csrf(client, "test-password")
    response = client.post("/api/political/manual-story", headers={"X-CSRF-Token": csrf}, json={
        "target_keys": ["flavio_valle"], "title": "Simulated", "url": "https://example.com/oversized",
        "full_text": "a" * (2 * 1024 * 1024),
    })
    assert response.status_code == 413
    assert response.json()["detail"] == "political_request_too_large"
    assert not fake.calls


def test_nested_classification_is_always_marked_as_human(site):
    client, _, fake = site
    csrf = login_and_csrf(client, "viewer-flavio")
    response = client.post("/api/political/articles/101/classifications", headers={"X-CSRF-Token": csrf}, json={
        "target_key": "flavio_valle", "ai_generated": True,
        "payload": {"article_sentiment": "positive", "ai_generated": True},
    })
    assert response.status_code == 200
    assert fake.classified[(101, "flavio_valle")]["ai_generated"] is False


def test_manual_story_uses_server_snapshots_and_rejects_archived_targets(site):
    client, _, fake = site
    csrf = login_and_csrf(client, "test-password")
    payload = {"target_keys": ["flavio_valle"], "title": "Simulated manual news",
               "url": "https://example.com/manual", "target_snapshots": [{"key": "flavio_valle", "label": "Forged"}]}
    response = client.post("/api/political/manual-story", headers={"X-CSRF-Token": csrf}, json=payload)
    assert response.status_code == 200
    saved = fake.calls[-1]["payload"]
    assert saved["target_snapshots"][0]["label"] != "Forged"
    assert saved["target_snapshots"][0]["key"] == "flavio_valle"
    payload["target_keys"] = ["otto_alencar"]
    assert client.post("/api/political/manual-story", headers={"X-CSRF-Token": csrf}, json=payload).status_code == 400
    assert len(fake.calls) == 1


@pytest.mark.parametrize("error_name,status", [("PoliticalAccessDenied", 403), ("PoliticalNotFound", 404)])
def test_backend_scope_errors_are_mapped_to_http_status(site, monkeypatch, error_name, status):
    client, routes, fake = site
    login_and_csrf(client, "test-password")
    def fail(*args, **kwargs):
        raise getattr(routes, error_name)("scoped_backend_error")
    monkeypatch.setattr(fake, "article_text", fail)
    assert client.get("/api/political/articles/101/text").status_code == status


@pytest.mark.parametrize("path,method", [
    ("/api/political/jobs", "start_job"),
    ("/api/political/manual-story", "insert_manual_story"),
    ("/api/political/articles/101/classifications", "upsert_classification"),
    ("/api/update/start", "start_job"),
    ("/api/manual-story", "insert_manual_story"),
    ("/api/update/resume", "resume_job"),
    ("/api/update/cancel", "cancel_job"),
])
def test_async_mutations_execute_sync_service_off_the_event_loop(site, monkeypatch, path, method):
    import asyncio
    import threading
    client, routes, fake = site
    app_module = importlib.import_module("web_app.app")
    original_pool = routes.run_in_threadpool
    pool_threads = []
    service_threads = []

    async def observed_pool(func, *args, **kwargs):
        asyncio.get_running_loop()
        pool_threads.append(threading.get_ident())
        return await original_pool(func, *args, **kwargs)

    original_method = getattr(fake, method)

    def observed_service(*args, **kwargs):
        with pytest.raises(RuntimeError, match="no running event loop"):
            asyncio.get_running_loop()
        service_threads.append(threading.get_ident())
        return original_method(*args, **kwargs)

    monkeypatch.setattr(routes, "run_in_threadpool", observed_pool)
    monkeypatch.setattr(app_module, "run_in_threadpool", observed_pool)
    monkeypatch.setattr(fake, method, observed_service)
    csrf = login_and_csrf(client, "test-password")
    response = client.post(path, headers={"X-CSRF-Token": csrf}, json={
        "scope": routes.SCOPE, "target_keys": ["flavio_valle"], "target_key": "flavio_valle",
        "job_id": "political-fixture", "title": "Fixture manual article", "url": "https://example.com/fixture",
    })
    assert response.status_code == 200, response.text
    assert len(pool_threads) == len(service_threads) == 1
    assert pool_threads[0] != service_threads[0]


@pytest.mark.parametrize("path", ["/api/update/start", "/api/update/resume", "/api/update/cancel", "/api/manual-story"])
def test_legacy_political_aliases_bound_json_before_dispatch(site, path):
    client, routes, fake = site
    csrf = login_and_csrf(client, "test-password")
    response = client.post(path, headers={"X-CSRF-Token": csrf}, json={
        "scope": routes.SCOPE, "job_id": "political-fixture", "target_keys": ["flavio_valle"],
        "full_text": "a" * (2 * 1024 * 1024),
    })
    assert response.status_code == 413
    assert response.json()["detail"] == "political_request_too_large"
    assert not fake.calls


def test_live_results_pass_job_filter_and_surface_hidden_or_missing_job(site, monkeypatch):
    client, routes, fake = site
    login_and_csrf(client, "viewer-flavio")
    base_list = fake.list_articles

    def observed_list(**kwargs):
        if kwargs.get("job_id") != "political-visible":
            raise routes.PoliticalNotFound("hidden_or_missing_job")
        return base_list(**kwargs)

    monkeypatch.setattr(fake, "list_articles", observed_list)
    response = client.get("/api/update/live-results?job_id=political-visible&limit=99999")
    assert response.status_code == 200
    assert response.json()["jobId"] == "political-visible" and response.json()["mode"] == "job"
    assert fake.calls[-1]["job_id"] == "political-visible"
    assert fake.calls[-1]["allowed_target_keys"] == ["flavio_valle"]
    assert fake.calls[-1]["page_size"] == 200
    for job_id in ["political-private", "political-missing"]:
        assert client.get("/api/update/live-results", params={"job_id": job_id}).status_code == 404


def test_live_results_without_a_job_is_explicitly_base_mode(site):
    client, routes, fake = site
    login_and_csrf(client, "viewer-flavio")
    response = client.get("/api/update/live-results", params={"scope": routes.SCOPE})
    assert response.status_code == 200 and response.json()["mode"] == "base"
    assert response.json()["jobId"] == "" and fake.calls[-1]["job_id"] == ""
