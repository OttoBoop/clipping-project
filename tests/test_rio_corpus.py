from __future__ import annotations

import importlib

from fastapi.testclient import TestClient

from pipeline.rio_geography import RioGazetteer
from tests.test_admin_ui import csrf_header, load_test_app, login, login_viewer
from web_app.rio_corpus import SCHEMA_STATEMENTS, SourceRegistry


class FakeRioCorpus:
    configured = True

    def __init__(self) -> None:
        self.started: list[tuple[dict, str]] = []
        self.scheduled = 0

    def health(self, *, check_database: bool = False):
        return {"configured": True, "database": "ok" if check_database else "unchecked"}

    def start_job(self, payload, *, started_by):
        self.started.append((dict(payload), started_by))
        return {"id": "corpus-job", "jobId": "corpus-job", "status": "queued", "batchId": "batch", "metrics": {"windows_total": 3}}

    def status(self, job_id=""):
        return {"id": job_id or "corpus-job", "status": "running", "metrics": {"observation_events": 12}}

    def list_articles(self, **_kwargs):
        return {"page": 1, "pageSize": 50, "total": 1, "items": [{"id": 7, "title": "Rio"}]}

    def sources(self):
        return {"version": "v1", "count": 1, "items": [{"key": "g1", "registryState": "active"}]}

    def coverage(self, **_kwargs):
        return {"page": 1, "pageSize": 100, "total": 1, "items": [{"status": "exhausted"}]}

    def audit_samples(self, **_kwargs):
        return {"count": 1, "items": [{"observation_id": 9, "body_chars": 500}]}

    def schedule_realtime(self, *, started_by):
        self.scheduled += 1
        return {"id": "cron-job", "status": "queued", "startedBy": started_by}


def test_source_registry_separates_historical_realtime_and_blocked_inventory():
    registry = SourceRegistry.load()
    assert registry.version == "rio_corpus_sources_v1"
    assert registry.get("vejario_sitemap").geography_prior == "city_focused"
    assert registry.get("g1_rio_sitemap").config["allowed_path_prefixes"] == ["/rio-de-janeiro/", "/rj/"]
    assert registry.get("g1_rio_rss").config["historical_role"] == "realtime_only"
    assert registry.get("prefeitura_rio_sitemap").enabled is False
    assert registry.get("prefeitura_rio_sitemap").config["registry_state"] == "blocked"


def test_geography_uses_coevidence_and_other_city_is_not_a_blacklist():
    gazetteer = RioGazetteer.load()
    ambiguous = gazetteer.classify(title="Flamengo vence em São Paulo", body="Campeonato nacional")
    mixed = gazetteer.classify(
        title="Niterói e Rio assinam acordo",
        body="A Prefeitura do Rio anunciou o projeto para o Centro do Rio.",
        geography_prior="state_section",
    )
    state_only = gazetteer.classify(title="Governo do Estado anuncia obra em Niterói", body="Alerj debate a medida")

    assert ambiguous.status == "unknown"
    assert any(row["kind"] == "ambiguous_without_coevidence" for row in ambiguous.evidence)
    assert mixed.status in {"confirmed", "probable"}
    assert any(row["kind"] == "other_municipality" for row in mixed.evidence)
    assert state_only.status == "other_city"


def test_queue_schema_claim_contract_uses_skip_locked_and_leases():
    schema = "\n".join(SCHEMA_STATEMENTS).lower()
    assert "leased_until" in schema
    assert "next_attempt_at" in schema
    assert "attempts integer" in schema
    from inspect import getsource
    from web_app.rio_corpus import RioCorpusService

    claim_source = getsource(RioCorpusService.claim_run).lower()
    assert "for update skip locked" in claim_source
    assert "leased_until" in claim_source


def test_rio_city_start_routes_to_corpus_backend(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")
    fake = FakeRioCorpus()
    monkeypatch.setattr(app_module, "rio_corpus", fake)

    with TestClient(app) as client:
        csrf = login(client)
        response = client.post(
            "/api/update/start",
            headers=csrf_header(csrf),
            json={
                "scope": "rio_economico",
                "topic": "rio_city_corpus",
                "date_from": "2011-01-01",
                "date_to": "2011-01-31",
                "collector": "all",
            },
        )

    assert response.status_code == 200
    assert response.json()["jobId"] == "corpus-job"
    assert fake.started[0][0]["scope"] == "rio_economico"
    assert fake.started[0][1] == "admin"


def test_rio_corpus_apis_are_profile_scoped(monkeypatch, tmp_path):
    app, _ = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")
    monkeypatch.setattr(app_module, "rio_corpus", FakeRioCorpus())

    with TestClient(app) as client:
        logged_out = client.get("/api/rio/corpus")
        login_viewer(client, "viewer-shakira")
        shakira = client.get("/api/rio/corpus")
        forced_status = client.get("/api/update/status?scope=rio_economico")
        login_viewer(client, "viewer-rio")
        rio = client.get("/api/rio/corpus")
        sources = client.get("/api/rio/sources")
        coverage = client.get("/api/rio/coverage")
        audit = client.get("/api/rio/audit")

    assert logged_out.status_code == 401
    assert shakira.status_code == 403
    assert forced_status.status_code == 403
    assert rio.status_code == 200 and rio.json()["total"] == 1
    assert sources.status_code == 200 and sources.json()["items"][0]["registryState"] == "active"
    assert coverage.status_code == 200 and coverage.json()["items"][0]["status"] == "exhausted"
    assert audit.status_code == 200 and audit.json()["items"][0]["body_chars"] == 500


def test_realtime_scheduler_requires_shared_bearer(monkeypatch, tmp_path):
    monkeypatch.setenv("RIO_CORPUS_CRON_TOKEN", "cron-secret")
    app, _ = load_test_app(monkeypatch, tmp_path)
    app_module = importlib.import_module("web_app.app")
    fake = FakeRioCorpus()
    monkeypatch.setattr(app_module, "rio_corpus", fake)

    with TestClient(app) as client:
        missing = client.post("/api/rio/schedule")
        bad = client.post("/api/rio/schedule", headers={"Authorization": "Bearer wrong"})
        good = client.post("/api/rio/schedule", headers={"Authorization": "Bearer cron-secret"})

    assert missing.status_code == 401
    assert bad.status_code == 401
    assert good.status_code == 200
    assert good.json()["id"] == "cron-job"
    assert fake.scheduled == 1
