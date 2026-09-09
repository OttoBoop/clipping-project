"""Publisher cooldown regressions; PG tests require an explicit disposable DB."""
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import os
from types import SimpleNamespace

import pytest
import requests

from web_app.political_corpus import PoliticalCorpusService
from web_app.political_rate_limits import (
    DomainCooldown, domain_deferral, normalize_domain, record_response_cooldown,
    retry_after_deadline, task_request_domain,
)


NOW = datetime(2026, 9, 9, 15, tzinfo=timezone.utc)


@pytest.mark.parametrize("header,seconds", [
    ("120", 120), (" 1.5 ", 1.5), ("7200", 7200),
    ("Wed, 09 Sep 2026 17:00:00 GMT", 7200),
    ("Wed, 09 Sep 2026 14:00:00 GMT", 0), ("0", 0),
])
def test_retry_after_delta_and_http_dates(header, seconds):
    assert retry_after_deadline(header, now=NOW) == NOW + timedelta(seconds=seconds)


@pytest.mark.parametrize("header", [None, "", "not a date", "nan", "inf", "-1", "x" * 257])
def test_invalid_retry_after_is_not_an_early_deadline(header):
    assert retry_after_deadline(header, now=NOW) is None


def test_normalized_hosts_and_actual_discovery_request_domain():
    assert normalize_domain(" WWW.AgendaDoPoder.com.br. ") == "agendadopoder.com.br"
    assert normalize_domain("www.bücher.example") == "xn--bcher-kva.example"
    registry = {"agenda_do_poder": "agendadopoder.com.br"}
    assert task_request_domain("fetch", {"url": "https://WWW.AgendaDoPoder.com.br.:443/a"}, registry) == "agendadopoder.com.br"
    assert task_request_domain("discovery", {"strategy": "wordpress", "source_key": "agenda_do_poder"}, registry) == "agendadopoder.com.br"
    assert task_request_domain("discovery", {"strategy": "google_news", "source_key": "agenda_do_poder"}, registry) == "news.google.com"
    assert task_request_domain("review", {}, registry) == ""


def test_discovery_wrapper_retains_scheduling_deferral():
    deferred = DomainCooldown("www.example.com", NOW + timedelta(minutes=5))
    try:
        try:
            raise deferred
        except DomainCooldown as exc:
            raise RuntimeError("discovery wrapper") from exc
    except RuntimeError as wrapped:
        assert domain_deferral(wrapped) is deferred


@pytest.fixture
def service(monkeypatch):
    database_url = os.environ.get("POLITICAL_TEST_DATABASE_URL", "").strip()
    if not database_url:
        pytest.skip("POLITICAL_TEST_DATABASE_URL must point to a disposable database")
    corpus = PoliticalCorpusService(store=SimpleNamespace(enabled=True), database_url=database_url)
    corpus.ensure_schema()
    with corpus._connect() as conn:
        conn.execute("""TRUNCATE political_jobs,political_articles,political_stories,
            political_source_leases,political_domain_limits,political_workers RESTART IDENTITY CASCADE""")
    monkeypatch.setattr(corpus, "_public_url", lambda url: None)
    yield corpus
    corpus.close()


def start(service, monkeypatch, *, discovery=None):
    from web_app import political_discovery

    monkeypatch.setattr(political_discovery, "build_tasks", lambda *a, **kw: discovery or [
        {"source_key": "agenda_do_poder", "strategy": "wordpress", "cursor": {}},
    ])
    return service.start_job({
        "target_keys": ["paes"], "target_snapshots": [{"key": "paes", "display_name": "Eduardo Paes", "keywords": ["Eduardo Paes"]}],
        "date_from": "2026-08-09", "date_to": "2026-08-09",
    }, started_by="cooldown-test", allowed_target_keys=["paes"])


def candidate(host="agendadopoder.com.br", source="agenda_do_poder", suffix="a"):
    return {"url": f"https://{host}/{suffix}", "source_key": source,
            "title": "Eduardo Paes", "published_at": "2026-08-09T12:00:00-03:00"}


@pytest.mark.parametrize("kind", ["fetch", "discovery"])
def test_existing_queue_skips_cooled_domain_before_claim_and_keeps_other_sources(service, monkeypatch, kind):
    job = start(service, monkeypatch, discovery=[
        {"source_key": "agenda_do_poder", "strategy": "wordpress", "cursor": {}},
        {"source_key": "tupi", "strategy": "sitemap", "url": "https://www.tupi.fm/sitemap.xml", "cursor": {}},
    ])
    with service._connect() as conn:
        if kind == "fetch":
            service._insert_task(conn, job["id"], kind, candidate("WWW.AgendaDoPoder.com.br.:443"))
            service._insert_task(conn, job["id"], kind, candidate("www.tupi.fm", "tupi"))
        # Simulate already queued tasks created before this schema addition.
        conn.execute("UPDATE political_tasks SET request_domain=NULL")
        record_response_cooldown(conn, "www.agendadopoder.com.br", 429, "120")
    claimed = service.claim_task(kind, worker_id="healthy-source")
    assert claimed["source_key"] == "tupi"
    assert claimed["request_domain"] == "tupi.fm"
    with service._connect() as conn:
        blocked = conn.execute("SELECT attempts,lease_token FROM political_tasks WHERE kind=%s AND source_key='agenda_do_poder'", (kind,)).fetchone()
    assert blocked == {"attempts": 0, "lease_token": None}


def test_cooldown_race_releases_fetch_slot_without_attempt_or_false_metadata(service, monkeypatch):
    job = start(service, monkeypatch)
    with service._connect() as conn:
        service._insert_task(conn, job["id"], "fetch", candidate())
        conn.execute("UPDATE political_tasks SET attempts=5 WHERE kind='fetch'")
    task = service.claim_task("fetch", worker_id="caught-race")
    assert task["attempts"] == 6
    with service._connect() as conn:
        deadline = record_response_cooldown(conn, "agendadopoder.com.br", 429, "7200")
    monkeypatch.setattr("web_app.political_corpus.time.sleep", lambda seconds: pytest.fail("cooldown must not sleep in a worker"))
    service._http_local.session = SimpleNamespace(request=lambda *a, **kw: pytest.fail("cooldown must not request HTTP"))
    result = service.process_task(task)
    assert result["status"] == "deferred"
    with service._connect() as conn:
        row = conn.execute("SELECT status,attempts,next_attempt_at,lease_token,leased_until FROM political_tasks WHERE id=%s", (task["id"],)).fetchone()
        assert conn.execute("SELECT COUNT(*) AS n FROM political_articles").fetchone()["n"] == 0
        assert conn.execute("SELECT COUNT(*) AS n FROM political_observations").fetchone()["n"] == 0
        assert conn.execute("SELECT fetch_attempted FROM political_jobs WHERE id=%s", (job["id"],)).fetchone()["fetch_attempted"] == 0
        service._insert_task(conn, job["id"], "fetch", candidate("tupi.fm", "tupi"))
    assert row == {"status": "retryable", "attempts": 5, "next_attempt_at": deadline, "lease_token": None, "leased_until": None}
    assert service.claim_task("fetch", worker_id="free-slot")["source_key"] == "tupi"


def test_discovery_deferral_preserves_cursor_and_does_not_enqueue_fallback(service, monkeypatch):
    from web_app import political_discovery

    start(service, monkeypatch)
    task = service.claim_task("discovery", worker_id="d")
    task["cursor"] = {"page": 9}
    deadline = datetime.now(timezone.utc) + timedelta(minutes=2)

    def defer(payload, fetch):
        try:
            raise DomainCooldown("agendadopoder.com.br", deadline)
        except DomainCooldown as exc:
            raise political_discovery.DiscoveryError("wrapped scheduling deferral") from exc

    monkeypatch.setattr(political_discovery, "discover", defer)
    assert service.process_task(task)["status"] == "deferred"
    with service._connect() as conn:
        row = conn.execute("SELECT attempts,cursor,lease_token FROM political_tasks WHERE id=%s", (task["id"],)).fetchone()
        assert conn.execute("SELECT COUNT(*) AS n FROM political_tasks").fetchone()["n"] == 1
        assert conn.execute("SELECT lease_token FROM political_source_leases WHERE source_key='agenda_do_poder'").fetchone()["lease_token"] is None
    assert row == {"attempts": 0, "cursor": {"page": 9}, "lease_token": None}


@pytest.mark.parametrize("header", ["7200", "http-date"])
def test_http_response_installs_durable_cooldown_without_shortening_it(service, monkeypatch, header):
    until = datetime.now(timezone.utc) + timedelta(hours=2)
    value = format_datetime(until, usegmt=True) if header == "http-date" else header
    response = requests.Response()
    response.status_code, response.url = 429, "https://agendadopoder.com.br/a"
    response.headers["Retry-After"] = value
    response._content, response._content_consumed = b"rate limited", True
    requests_made = []
    checked_urls = []
    monkeypatch.setattr(service, "_public_url", checked_urls.append)
    service._http_local.session = SimpleNamespace(request=lambda *a, **kw: requests_made.append(a) or response)
    assert service.fetch(response.url).status_code == 429
    with service._connect() as conn:
        first = conn.execute("SELECT cooldown_until FROM political_domain_limits WHERE domain='agendadopoder.com.br'").fetchone()["cooldown_until"]
        later = record_response_cooldown(conn, "WWW.AGENDAdoPODER.com.br.", 429, "5")
    assert (first - datetime.now(timezone.utc)).total_seconds() > 7190
    assert later == first
    monkeypatch.setattr("web_app.political_corpus.time.sleep", lambda seconds: pytest.fail("cooldown must not sleep"))
    with pytest.raises(DomainCooldown):
        service.fetch("https://www.agendadopoder.com.br/b")
    assert len(requests_made) == 1
    assert checked_urls == [response.url, "https://www.agendadopoder.com.br/b"]


def test_403_does_not_create_cooldown_and_missing_429_header_uses_explicit_policy(service):
    with service._connect() as conn:
        assert record_response_cooldown(conn, "blocked.example", 403, "120") is None
        assert record_response_cooldown(conn, "unauthorized.example", 401, "120") is None
        assert conn.execute("SELECT COUNT(*) AS n FROM political_domain_limits").fetchone()["n"] == 0
        deadline = record_response_cooldown(conn, "busy.example", 429, None)
    assert 55 < (deadline - datetime.now(timezone.utc)).total_seconds() <= 60


@pytest.mark.parametrize("header", [None, "", "malformed", "nan", "-1"])
def test_503_default_cooldown_preserves_longer_shared_deadlines(service, header):
    with service._connect() as conn:
        deadline = record_response_cooldown(conn, "news.google.com", 503, header)
        assert 25 < (deadline - datetime.now(timezone.utc)).total_seconds() <= 30
        longer = record_response_cooldown(conn, "news.google.com", 503, "7200")
        assert (longer - datetime.now(timezone.utc)).total_seconds() > 7190
        assert record_response_cooldown(conn, "news.google.com", 503, header) == longer


def test_503_blocks_shared_google_queue_without_attempts_and_healthy_publisher_finishes(service, monkeypatch):
    window = {"date_from": "2026-08-09", "date_to": "2026-08-09", "cursor": {}}
    job = start(service, monkeypatch, discovery=[
        {**window, "source_key": source, "strategy": "google_news", "query": '"Eduardo Paes"'}
        for source in ["google_news", "rc24h", "metropoles"]
    ] + [{**window, "source_key": "tupi", "strategy": "wordpress"}])
    requests_made = []
    def request(method, url, **kwargs):
        requests_made.append(url)
        response = requests.Response()
        response.url = url
        response.status_code = 503 if "news.google.com" in url else 200
        response._content = b"temporarily unavailable" if response.status_code == 503 else b"[]"
        response._content_consumed = True
        return response
    service._http_local.session = SimpleNamespace(request=request)
    assert service.fetch("https://news.google.com/rss/search?q=outage").status_code == 503
    healthy = service.claim_task("discovery", worker_id="healthy-after-503")
    assert healthy["source_key"] == "tupi"
    assert service.process_task(healthy)["status"] == "complete"
    assert service.claim_task("discovery", worker_id="cooled-google") is None
    with pytest.raises(DomainCooldown):
        service.fetch("https://news.google.com/rss/search?q=another-name")
    with service._connect() as conn:
        rows = conn.execute("""SELECT status,attempts,lease_token FROM political_tasks
            WHERE job_id=%s AND payload->>'strategy'='google_news'""", (job["id"],)).fetchall()
    assert len(rows) == 3
    assert all(row == {"status": "queued", "attempts": 0, "lease_token": None} for row in rows)
    assert len(requests_made) == 2 and "tupi.fm" in requests_made[-1]


def test_503_race_defers_claimed_google_discovery_without_exhausting_retry_budget(service, monkeypatch):
    job = start(service, monkeypatch, discovery=[{
        "source_key": "rc24h", "strategy": "google_news", "query": '"Eduardo Paes"',
        "date_from": "2026-08-09", "date_to": "2026-08-09", "cursor": {},
    }])
    with service._connect() as conn:
        conn.execute("UPDATE political_tasks SET attempts=5 WHERE job_id=%s", (job["id"],))
    task = service.claim_task("discovery", worker_id="google-race")
    assert task["attempts"] == 6
    with service._connect() as conn:
        deadline = record_response_cooldown(conn, "news.google.com", 503, None)
    monkeypatch.setattr("web_app.political_corpus.time.sleep", lambda seconds: pytest.fail("cooldown must not occupy worker slots"))
    service._http_local.session = SimpleNamespace(request=lambda *a, **kw: pytest.fail("cooldown must not issue HTTP"))
    assert service.process_task(task)["status"] == "deferred"
    with service._connect() as conn:
        row = conn.execute("SELECT status,attempts,next_attempt_at,lease_token FROM political_tasks WHERE id=%s", (task["id"],)).fetchone()
        assert conn.execute("SELECT COUNT(*) AS n FROM political_tasks WHERE job_id=%s", (job["id"],)).fetchone()["n"] == 1
    assert row == {"status": "retryable", "attempts": 5, "next_attempt_at": deadline, "lease_token": None}


def test_global_four_fetch_slots_remain_enforced(service, monkeypatch):
    job = start(service, monkeypatch)
    with service._connect() as conn:
        for number in range(5):
            service._insert_task(conn, job["id"], "fetch", candidate(f"host{number}.example", f"source{number}"))
    assert all(service.claim_task("fetch", worker_id=f"f{i}") for i in range(4))
    assert service.claim_task("fetch", worker_id="f4") is None
