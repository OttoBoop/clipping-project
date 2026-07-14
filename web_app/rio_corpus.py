from __future__ import annotations

import calendar
import gzip
import hashlib
import json
import os
import socket
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import requests

from pipeline.collectors import CandidateArticle, _parse_sitemap_entries, parse_rss_or_atom
from pipeline.http_utils import (
    canonicalize_url,
    extract_html_title,
    extract_published_at,
    fetch_url,
    html_to_article_text,
    try_resolve_google_redirect,
)
from pipeline.rio_geography import RioGazetteer, rio_gazetteer
from pipeline.settings import USER_AGENT, google_news_rss_url

from .config import ROOT, db_path
from .rio_topics import RIO_CITY_TOPIC, RIO_ECONOMICO_SCOPE, load_rio_topic_config
from .storage_bridge import ArtifactStore, artifact_store


SOURCE_REGISTRY_PATH = ROOT / "data" / "rio_corpus_sources_v1.json"
CORPUS_SCHEMA_VERSION = "rio_corpus_v1"
RUN_TERMINAL_STATES = {"exhausted", "empty_verified", "capped", "blocked", "failed"}
RUN_CLAIMABLE_STATES = {"queued", "retryable"}
RUN_SUCCESS_STATES = {"exhausted", "empty_verified"}
GOOGLE_HOST = "news.google.com"
REAL_BODY_MIN_CHARS = 200
DEFAULT_FETCH_WORKERS = 8
DEFAULT_LEASE_SECONDS = 20 * 60
STALE_PROGRESS_SECONDS = 15 * 60


class RioCorpusError(RuntimeError):
    pass


class RioCorpusNotConfigured(RioCorpusError):
    pass


class SourceRetryable(RioCorpusError):
    pass


class SourceBlocked(RioCorpusError):
    pass


class SourceFailed(RioCorpusError):
    pass


@dataclass(frozen=True)
class SourceDefinition:
    key: str
    name: str
    domain: str
    strategy: str
    geography_prior: str
    start_date: str
    window: str
    enabled: bool
    config: dict[str, Any]


class SourceRegistry:
    def __init__(self, *, version: str, sources: Iterable[SourceDefinition]) -> None:
        self.version = version
        self.sources = tuple(sources)
        self._by_key = {source.key: source for source in self.sources}

    @classmethod
    def load(cls, path: Path = SOURCE_REGISTRY_PATH) -> "SourceRegistry":
        payload = json.loads(path.read_text(encoding="utf-8"))
        sources: list[SourceDefinition] = []
        for row in payload.get("sources") or []:
            if not isinstance(row, dict):
                continue
            key = str(row.get("key") or "").strip()
            if not key:
                continue
            sources.append(
                SourceDefinition(
                    key=key,
                    name=str(row.get("name") or key).strip(),
                    domain=str(row.get("domain") or "").strip().lower(),
                    strategy=str(row.get("strategy") or "").strip(),
                    geography_prior=str(row.get("geography_prior") or "neutral").strip(),
                    start_date=str(row.get("start_date") or "2011-01-01").strip(),
                    window=str(row.get("window") or "month").strip(),
                    enabled=bool(row.get("enabled")),
                    config=dict(row),
                )
            )
        return cls(version=str(payload.get("version") or path.stem), sources=sources)

    def get(self, key: str) -> SourceDefinition:
        try:
            return self._by_key[key]
        except KeyError as exc:
            raise SourceFailed(f"unknown_source:{key}") from exc


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def _safe_host(url: str) -> str:
    return (urlparse(str(url or "")).hostname or "").lower()


def _is_vehicle_url(url: str) -> bool:
    host = _safe_host(url)
    return bool(host and GOOGLE_HOST not in host and host not in {"localhost", "127.0.0.1"})


def _url_hash(url: str) -> str:
    return hashlib.sha256(canonicalize_url(url).encode("utf-8")).hexdigest()


def _month_windows(start: date, end: date) -> list[tuple[date, date]]:
    windows: list[tuple[date, date]] = []
    cursor = start.replace(day=1)
    while cursor <= end:
        month_end = date(cursor.year, cursor.month, calendar.monthrange(cursor.year, cursor.month)[1])
        windows.append((max(start, cursor), min(end, month_end)))
        cursor = (month_end + timedelta(days=1)).replace(day=1)
    return windows


def _day_windows(start: date, end: date) -> list[tuple[date, date]]:
    return [(start + timedelta(days=offset), start + timedelta(days=offset)) for offset in range((end - start).days + 1)]


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS rio_corpus_meta (
        key TEXT PRIMARY KEY,
        value JSONB NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rio_corpus_jobs (
        id TEXT PRIMARY KEY,
        batch_id TEXT NOT NULL,
        idempotency_key TEXT UNIQUE,
        scope TEXT NOT NULL,
        topic TEXT NOT NULL,
        status TEXT NOT NULL,
        collector TEXT NOT NULL,
        priority INTEGER NOT NULL DEFAULT 0,
        date_from DATE NOT NULL,
        date_to DATE NOT NULL,
        requested_by TEXT NOT NULL,
        requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        started_at TIMESTAMPTZ,
        finished_at TIMESTAMPTZ,
        last_progress_at TIMESTAMPTZ,
        total_windows INTEGER NOT NULL DEFAULT 0,
        metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
        error_message TEXT NOT NULL DEFAULT ''
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rio_source_runs (
        id BIGSERIAL PRIMARY KEY,
        job_id TEXT NOT NULL REFERENCES rio_corpus_jobs(id) ON DELETE CASCADE,
        source_key TEXT NOT NULL,
        source_name TEXT NOT NULL,
        strategy TEXT NOT NULL,
        window_start DATE NOT NULL,
        window_end DATE NOT NULL,
        query TEXT NOT NULL DEFAULT '',
        query_hash TEXT NOT NULL DEFAULT '',
        priority INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'queued',
        attempts INTEGER NOT NULL DEFAULT 0,
        max_attempts INTEGER NOT NULL DEFAULT 5,
        lease_owner TEXT,
        leased_until TIMESTAMPTZ,
        next_attempt_at TIMESTAMPTZ,
        started_at TIMESTAMPTZ,
        finished_at TIMESTAMPTZ,
        last_checkpoint_at TIMESTAMPTZ,
        checkpoint JSONB NOT NULL DEFAULT '{}'::jsonb,
        observation_events INTEGER NOT NULL DEFAULT 0,
        unique_candidates INTEGER NOT NULL DEFAULT 0,
        fetch_attempted INTEGER NOT NULL DEFAULT 0,
        fetch_succeeded INTEGER NOT NULL DEFAULT 0,
        body_extracted INTEGER NOT NULL DEFAULT 0,
        final_url_resolved INTEGER NOT NULL DEFAULT 0,
        page_date_verified INTEGER NOT NULL DEFAULT 0,
        city_confirmed INTEGER NOT NULL DEFAULT 0,
        city_probable INTEGER NOT NULL DEFAULT 0,
        state_only INTEGER NOT NULL DEFAULT 0,
        other_city INTEGER NOT NULL DEFAULT 0,
        duplicate_urls INTEGER NOT NULL DEFAULT 0,
        error_count INTEGER NOT NULL DEFAULT 0,
        error_message TEXT NOT NULL DEFAULT '',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(job_id, source_key, window_start, window_end, query_hash)
    )
    """,
    "CREATE INDEX IF NOT EXISTS rio_source_runs_queue_idx ON rio_source_runs(status, priority DESC, next_attempt_at, id)",
    "CREATE INDEX IF NOT EXISTS rio_source_runs_job_idx ON rio_source_runs(job_id, status)",
    """
    CREATE TABLE IF NOT EXISTS rio_articles (
        id BIGSERIAL PRIMARY KEY,
        canonical_url TEXT NOT NULL,
        url_hash TEXT NOT NULL UNIQUE,
        final_url TEXT NOT NULL,
        source_domain TEXT NOT NULL DEFAULT '',
        title TEXT NOT NULL DEFAULT '',
        published_at TIMESTAMPTZ,
        date_status TEXT NOT NULL DEFAULT 'missing',
        body_chars INTEGER NOT NULL DEFAULT 0,
        content_hash TEXT,
        text_object_key TEXT,
        html_object_key TEXT,
        download_status TEXT NOT NULL DEFAULT 'pending',
        geography_status TEXT NOT NULL DEFAULT 'unknown',
        geography_score DOUBLE PRECISION NOT NULL DEFAULT 0,
        first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        legacy_sqlite_id INTEGER,
        metadata JSONB NOT NULL DEFAULT '{}'::jsonb
    )
    """,
    "CREATE INDEX IF NOT EXISTS rio_articles_published_idx ON rio_articles(published_at DESC, id DESC)",
    "CREATE INDEX IF NOT EXISTS rio_articles_geo_idx ON rio_articles(geography_status, published_at DESC)",
    """
    CREATE TABLE IF NOT EXISTS rio_url_aliases (
        observed_url_hash TEXT PRIMARY KEY,
        observed_url TEXT NOT NULL,
        article_id BIGINT NOT NULL REFERENCES rio_articles(id) ON DELETE CASCADE,
        first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rio_observations (
        id BIGSERIAL PRIMARY KEY,
        source_run_id BIGINT NOT NULL REFERENCES rio_source_runs(id) ON DELETE CASCADE,
        article_id BIGINT REFERENCES rio_articles(id) ON DELETE SET NULL,
        source_key TEXT NOT NULL,
        source_name TEXT NOT NULL,
        query TEXT NOT NULL DEFAULT '',
        observed_url TEXT NOT NULL,
        observed_url_hash TEXT NOT NULL,
        title TEXT NOT NULL DEFAULT '',
        snippet TEXT NOT NULL DEFAULT '',
        observed_date TIMESTAMPTZ,
        observed_date_status TEXT NOT NULL DEFAULT 'missing',
        decision TEXT NOT NULL DEFAULT 'observed',
        metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
        observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(source_run_id, observed_url_hash, query)
    )
    """,
    "CREATE INDEX IF NOT EXISTS rio_observations_article_idx ON rio_observations(article_id)",
    """
    CREATE TABLE IF NOT EXISTS rio_fetch_attempts (
        id BIGSERIAL PRIMARY KEY,
        observation_id BIGINT NOT NULL REFERENCES rio_observations(id) ON DELETE CASCADE,
        attempted_url TEXT NOT NULL,
        final_url TEXT NOT NULL DEFAULT '',
        method TEXT NOT NULL,
        status TEXT NOT NULL,
        http_status INTEGER,
        body_chars INTEGER NOT NULL DEFAULT 0,
        error_type TEXT NOT NULL DEFAULT '',
        error_message TEXT NOT NULL DEFAULT '',
        attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        duration_ms INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rio_geography_evidence (
        id BIGSERIAL PRIMARY KEY,
        article_id BIGINT NOT NULL REFERENCES rio_articles(id) ON DELETE CASCADE,
        gazetteer_version TEXT NOT NULL,
        evidence_kind TEXT NOT NULL,
        evidence_value TEXT NOT NULL,
        evidence_location TEXT NOT NULL,
        weight DOUBLE PRECISION NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(article_id, gazetteer_version, evidence_kind, evidence_value, evidence_location)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rio_article_dimensions (
        article_id BIGINT NOT NULL REFERENCES rio_articles(id) ON DELETE CASCADE,
        dimension TEXT NOT NULL,
        evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
        assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY(article_id, dimension)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rio_content_objects (
        content_hash TEXT PRIMARY KEY,
        text_object_key TEXT,
        html_object_key TEXT,
        body_chars INTEGER NOT NULL,
        html_bytes INTEGER NOT NULL DEFAULT 0,
        storage_status TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
)


class RioCorpusService:
    def __init__(self, *, store: ArtifactStore | None = None) -> None:
        self.store = store or artifact_store
        self.registry = SourceRegistry.load()
        self.gazetteer: RioGazetteer = rio_gazetteer()
        self._schema_lock = threading.Lock()
        self._schema_ready = False
        self._rate_lock = threading.Lock()
        self._next_request_at: dict[str, float] = {}

    @property
    def database_url(self) -> str:
        return str(os.environ.get("RIO_CORPUS_DATABASE_URL") or os.environ.get("DATABASE_URL") or "").strip()

    @property
    def configured(self) -> bool:
        return bool(self.database_url)

    def _connect(self):
        if not self.configured:
            raise RioCorpusNotConfigured("rio_corpus_database_not_configured")
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RioCorpusNotConfigured("psycopg_not_installed") from exc
        return psycopg.connect(self.database_url, row_factory=dict_row, connect_timeout=10)

    def ensure_schema(self) -> None:
        if self._schema_ready:
            return
        with self._schema_lock:
            if self._schema_ready:
                return
            with self._connect() as conn:
                for statement in SCHEMA_STATEMENTS:
                    conn.execute(statement)
                conn.execute(
                    """
                    INSERT INTO rio_corpus_meta(key, value) VALUES ('schema_version', %s::jsonb)
                    ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value, updated_at=NOW()
                    """,
                    (_json({"version": CORPUS_SCHEMA_VERSION, "sourceRegistry": self.registry.version}),),
                )
            self._schema_ready = True

    def health(self, *, check_database: bool = False) -> dict[str, Any]:
        result = {
            "configured": self.configured,
            "schemaVersion": CORPUS_SCHEMA_VERSION,
            "sourceRegistryVersion": self.registry.version,
            "enabledSources": sum(1 for source in self.registry.sources if source.enabled),
        }
        if check_database and self.configured:
            try:
                self.ensure_schema()
                with self._connect() as conn:
                    result["database"] = "ok" if conn.execute("SELECT 1 AS ok").fetchone()["ok"] == 1 else "error"
            except Exception as exc:
                result["database"] = "error"
                result["errorType"] = type(exc).__name__
        return result

    def _throttle(self, source: SourceDefinition, *, article_fetch: bool = False) -> None:
        configured = float(source.config.get("rate_limit_per_second") or 1.0)
        rate = max(configured, 4.0) if article_fetch else configured
        rate = max(0.1, rate)
        key = f"{source.domain}:{'article' if article_fetch else 'index'}"
        with self._rate_lock:
            now = time.monotonic()
            ready = self._next_request_at.get(key, now)
            if ready > now:
                time.sleep(ready - now)
                now = time.monotonic()
            self._next_request_at[key] = now + (1.0 / rate)

    def _selected_sources(self, collector: str, source_keys: set[str]) -> list[SourceDefinition]:
        collector = collector or "all"
        selected: list[SourceDefinition] = []
        strategy_aliases = {
            "sitemap_daily": {"sitemap_daily"},
            "wordpress_api": {"wordpress_date"},
            "google_news": {"google_news_query"},
            "rss": {"rss_realtime"},
            "realtime": {"rss_realtime", "google_news_query"},
        }
        allowed = strategy_aliases.get(collector)
        for source in self.registry.sources:
            if not source.enabled:
                continue
            if source_keys and source.key not in source_keys:
                continue
            if collector != "all" and allowed is not None and source.strategy not in allowed:
                continue
            if collector != "all" and allowed is None and source.key != collector:
                continue
            if collector == "all" and source.strategy == "rss_realtime":
                continue
            selected.append(source)
        return selected

    def _source_windows(self, source: SourceDefinition, start: date, end: date) -> list[tuple[date, date]]:
        source_start = date.fromisoformat(source.start_date)
        start = max(start, source_start)
        if start > end:
            return []
        if source.window == "day":
            return _day_windows(start, end)
        if source.window == "realtime":
            return [(end, end)]
        return _month_windows(start, end)

    def start_job(self, payload: dict[str, Any], *, started_by: str) -> dict[str, Any]:
        self.ensure_schema()
        today = date.today()
        start = date.fromisoformat(str(payload.get("date_from") or payload.get("dateFrom") or today.isoformat()))
        end = date.fromisoformat(str(payload.get("date_to") or payload.get("dateTo") or today.isoformat()))
        if start > end:
            raise ValueError("periodo_invalido")
        if end > today:
            raise ValueError("data_futura")
        collector = str(payload.get("collector") or "all").strip() or "all"
        priority = int(payload.get("priority") or (100 if collector == "realtime" else 10))
        source_keys = {str(item).strip() for item in payload.get("source_keys", []) if str(item).strip()}
        sources = self._selected_sources(collector, source_keys)
        if not sources:
            raise ValueError("rio_corpus_no_sources_selected")

        topic = load_rio_topic_config(RIO_CITY_TOPIC)
        google_queries = [str(row.get("query") or "").strip() for row in topic.queries if str(row.get("query") or "").strip()]
        job_id = uuid.uuid4().hex
        batch_id = str(payload.get("batch_id") or f"rio-{start.isoformat()}-{end.isoformat()}-{job_id[:8]}")
        idempotency_key = str(payload.get("idempotency_key") or "").strip() or None
        run_rows: list[tuple[Any, ...]] = []
        for source in sources:
            for window_start, window_end in self._source_windows(source, start, end):
                queries = google_queries if source.strategy == "google_news_query" else [""]
                for query in queries:
                    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest() if query else ""
                    run_rows.append(
                        (
                            job_id,
                            source.key,
                            source.name,
                            source.strategy,
                            window_start,
                            window_end,
                            query,
                            query_hash,
                            priority,
                        )
                    )

        with self._connect() as conn:
            if idempotency_key:
                existing = conn.execute(
                    "SELECT * FROM rio_corpus_jobs WHERE idempotency_key=%s",
                    (idempotency_key,),
                ).fetchone()
                if existing:
                    return self._job_payload(conn, existing)
            conn.execute(
                """
                INSERT INTO rio_corpus_jobs(
                    id, batch_id, idempotency_key, scope, topic, status, collector,
                    priority, date_from, date_to, requested_by, total_windows, metadata
                ) VALUES (%s,%s,%s,%s,%s,'queued',%s,%s,%s,%s,%s,%s,%s::jsonb)
                """,
                (
                    job_id,
                    batch_id,
                    idempotency_key,
                    RIO_ECONOMICO_SCOPE,
                    RIO_CITY_TOPIC,
                    collector,
                    priority,
                    start,
                    end,
                    started_by,
                    len(run_rows),
                    _json(
                        {
                            "sourceRegistryVersion": self.registry.version,
                            "gazetteerVersion": self.gazetteer.version,
                            "sourceKeys": [source.key for source in sources],
                        }
                    ),
                ),
            )
            conn.executemany(
                """
                INSERT INTO rio_source_runs(
                    job_id, source_key, source_name, strategy, window_start,
                    window_end, query, query_hash, priority
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING
                """,
                run_rows,
            )
            job = conn.execute("SELECT * FROM rio_corpus_jobs WHERE id=%s", (job_id,)).fetchone()
            return self._job_payload(conn, job)

    def _job_payload(self, conn, job: dict[str, Any]) -> dict[str, Any]:
        metrics = conn.execute(
            """
            SELECT
                COUNT(*)::int AS windows_total,
                COUNT(*) FILTER (WHERE status='queued')::int AS windows_queued,
                COUNT(*) FILTER (WHERE status='running')::int AS windows_running,
                COUNT(*) FILTER (WHERE status='exhausted')::int AS windows_exhausted,
                COUNT(*) FILTER (WHERE status='empty_verified')::int AS windows_empty_verified,
                COUNT(*) FILTER (WHERE status='capped')::int AS windows_capped,
                COUNT(*) FILTER (WHERE status='retryable')::int AS windows_retryable,
                COUNT(*) FILTER (WHERE status='blocked')::int AS windows_blocked,
                COUNT(*) FILTER (WHERE status='failed')::int AS windows_failed,
                COALESCE(SUM(observation_events),0)::bigint AS observation_events,
                COALESCE(SUM(unique_candidates),0)::bigint AS unique_candidates,
                COALESCE(SUM(fetch_attempted),0)::bigint AS fetch_attempted,
                COALESCE(SUM(fetch_succeeded),0)::bigint AS fetch_succeeded,
                COALESCE(SUM(body_extracted),0)::bigint AS body_extracted,
                COALESCE(SUM(final_url_resolved),0)::bigint AS final_url_resolved,
                COALESCE(SUM(page_date_verified),0)::bigint AS page_date_verified,
                COALESCE(SUM(city_confirmed),0)::bigint AS city_confirmed,
                COALESCE(SUM(city_probable),0)::bigint AS city_probable,
                COALESCE(SUM(state_only),0)::bigint AS state_only,
                COALESCE(SUM(other_city),0)::bigint AS other_city,
                COALESCE(SUM(duplicate_urls),0)::bigint AS duplicate_urls,
                COALESCE(SUM(error_count),0)::bigint AS error_count,
                MAX(last_checkpoint_at) AS last_activity
            FROM rio_source_runs WHERE job_id=%s
            """,
            (job["id"],),
        ).fetchone()
        article_counts = conn.execute(
            """
            SELECT
                COUNT(*)::bigint AS corpus_articles,
                COUNT(*) FILTER (WHERE geography_status='confirmed')::bigint AS corpus_city_confirmed,
                COUNT(*) FILTER (WHERE geography_status='probable')::bigint AS corpus_city_probable
            FROM rio_articles
            """
        ).fetchone()
        requested_at = job.get("requested_at")
        last_activity = metrics.get("last_activity")
        elapsed = max(0.001, (_utcnow() - (job.get("started_at") or requested_at or _utcnow())).total_seconds())
        processed = int(metrics["windows_exhausted"]) + int(metrics["windows_empty_verified"]) + int(metrics["windows_capped"]) + int(metrics["windows_blocked"]) + int(metrics["windows_failed"])
        rate = float(metrics["observation_events"]) / (elapsed / 3600.0)
        stale = bool(job.get("status") in {"queued", "running"} and last_activity and (_utcnow() - last_activity).total_seconds() > STALE_PROGRESS_SECONDS)
        return {
            "id": job["id"],
            "jobId": job["id"],
            "batchId": job["batch_id"],
            "scope": job["scope"],
            "topic": job["topic"],
            "status": job["status"],
            "collector": job["collector"],
            "dateFrom": str(job["date_from"]),
            "dateTo": str(job["date_to"]),
            "requestedAt": job.get("requested_at"),
            "startedAt": job.get("started_at"),
            "finishedAt": job.get("finished_at"),
            "lastActivity": last_activity,
            "staleAlert": stale,
            "throughputPerHour": round(rate, 2),
            "etaSeconds": round(((int(metrics["windows_total"]) - processed) / max(processed / elapsed, 0.000001)), 0) if processed else None,
            "metrics": {**dict(metrics), **dict(article_counts)},
        }

    def status(self, job_id: str = "") -> dict[str, Any]:
        if not self.configured:
            return {"status": "not_configured", **self.health()}
        self.ensure_schema()
        with self._connect() as conn:
            if job_id:
                job = conn.execute("SELECT * FROM rio_corpus_jobs WHERE id=%s", (job_id,)).fetchone()
            else:
                job = conn.execute(
                    """
                    SELECT * FROM rio_corpus_jobs
                    ORDER BY (status IN ('running','queued')) DESC, requested_at DESC LIMIT 1
                    """
                ).fetchone()
            if not job:
                return {"status": "idle", **self.health()}
            return self._job_payload(conn, job)

    def claim_run(self, *, worker_id: str, lease_seconds: int = DEFAULT_LEASE_SECONDS) -> dict[str, Any] | None:
        self.ensure_schema()
        with self._connect() as conn:
            row = conn.execute(
                """
                WITH candidate AS (
                    SELECT id FROM rio_source_runs
                    WHERE (
                        status IN ('queued','retryable')
                        OR (status='running' AND leased_until < NOW())
                    )
                    AND (next_attempt_at IS NULL OR next_attempt_at <= NOW())
                    ORDER BY priority DESC, id
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE rio_source_runs AS run
                SET status='running', lease_owner=%s,
                    leased_until=NOW() + (%s * INTERVAL '1 second'),
                    attempts=attempts+1,
                    started_at=COALESCE(started_at, NOW()),
                    last_checkpoint_at=NOW(), updated_at=NOW()
                FROM candidate WHERE run.id=candidate.id
                RETURNING run.*
                """,
                (worker_id, lease_seconds),
            ).fetchone()
            if row:
                conn.execute(
                    """
                    UPDATE rio_corpus_jobs SET status='running',
                        started_at=COALESCE(started_at,NOW()), last_progress_at=NOW()
                    WHERE id=%s AND status='queued'
                    """,
                    (row["job_id"],),
                )
            return dict(row) if row else None

    def checkpoint(self, run_id: int, worker_id: str, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE rio_source_runs SET checkpoint=%s::jsonb, last_checkpoint_at=NOW(),
                    leased_until=NOW() + (%s * INTERVAL '1 second'), updated_at=NOW()
                WHERE id=%s AND lease_owner=%s AND status='running'
                """,
                (_json(payload), DEFAULT_LEASE_SECONDS, run_id, worker_id),
            )
            conn.execute(
                """
                UPDATE rio_corpus_jobs SET last_progress_at=NOW()
                WHERE id=(SELECT job_id FROM rio_source_runs WHERE id=%s)
                """,
                (run_id,),
            )

    def _collect_sitemap(self, run: dict[str, Any], source: SourceDefinition, worker_id: str) -> tuple[list[CandidateArticle], bool]:
        day = run["window_start"]
        template = str(source.config.get("sitemap_url_template") or "")
        max_pages = max(1, int(source.config.get("max_pages") or 10))
        prefixes = tuple(str(item) for item in source.config.get("allowed_path_prefixes") or [])
        candidates: list[CandidateArticle] = []
        last_page_full = False
        verified_response = False
        for page in range(1, max_pages + 1):
            sitemap_url = template.format(yyyy=f"{day.year:04d}", mm=f"{day.month:02d}", dd=f"{day.day:02d}", page=page)
            try:
                self._throttle(source)
                _, xml_text = fetch_url(sitemap_url, timeout=15)
            except Exception as exc:
                code = int(getattr(exc, "code", 0) or 0)
                if code == 404 and (page > 1 or not verified_response):
                    break
                if code in {401, 403}:
                    raise SourceBlocked(f"sitemap_http_{code}:{sitemap_url}") from exc
                raise SourceRetryable(f"sitemap_fetch:{type(exc).__name__}:{sitemap_url}") from exc
            verified_response = True
            entries = list(_parse_sitemap_entries(xml_text))
            if not entries:
                last_page_full = False
                break
            last_page_full = True
            for entry in entries:
                url = canonicalize_url(str(entry.get("loc") or "").strip())
                path = urlparse(url).path or "/"
                if not url or (prefixes and not any(path.startswith(prefix) for prefix in prefixes)):
                    continue
                candidates.append(
                    CandidateArticle(
                        title=str(entry.get("title") or "").strip(),
                        url=url,
                        source_name=source.name,
                        source_type="sitemap_daily",
                        published_at=str(entry.get("published_at") or "") or f"{day.isoformat()}T12:00:00+00:00",
                        snippet="",
                        metadata={"sitemap_url": sitemap_url, "source_key": source.key, "date_origin": "sitemap"},
                    )
                )
            self.checkpoint(int(run["id"]), worker_id, {"page": page, "candidates": len(candidates)})
        return candidates, bool(last_page_full and page >= max_pages)

    def _collect_wordpress(self, run: dict[str, Any], source: SourceDefinition, worker_id: str) -> tuple[list[CandidateArticle], bool]:
        endpoint = f"{str(source.config.get('base_url') or '').rstrip('/')}/wp-json/wp/v2/posts"
        max_pages = max(1, int(source.config.get("max_pages") or 120))
        candidates: list[CandidateArticle] = []
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        capped = False
        for page in range(1, max_pages + 1):
            params = {
                "per_page": 100,
                "page": page,
                "orderby": "date",
                "order": "asc",
                "after": f"{run['window_start'].isoformat()}T00:00:00Z",
                "before": f"{run['window_end'].isoformat()}T23:59:59Z",
                "_fields": "link,title,excerpt,content,date_gmt,date",
            }
            try:
                self._throttle(source)
                response = session.get(endpoint, params=params, timeout=25)
            except requests.RequestException as exc:
                raise SourceRetryable(f"wordpress_request:{type(exc).__name__}") from exc
            if response.status_code in {401, 403}:
                raise SourceBlocked(f"wordpress_http_{response.status_code}:{endpoint}")
            if response.status_code == 400 and page > 1:
                break
            if response.status_code == 429 or response.status_code >= 500:
                raise SourceRetryable(f"wordpress_http_{response.status_code}:{endpoint}")
            if not response.ok:
                raise SourceFailed(f"wordpress_http_{response.status_code}:{endpoint}")
            try:
                payload = response.json()
            except ValueError as exc:
                raise SourceRetryable(f"wordpress_invalid_json:{endpoint}") from exc
            if not isinstance(payload, list):
                raise SourceFailed(f"wordpress_unexpected_payload:{endpoint}")
            if not payload:
                break
            for item in payload:
                title_raw = item.get("title") if isinstance(item.get("title"), dict) else {}
                excerpt_raw = item.get("excerpt") if isinstance(item.get("excerpt"), dict) else {}
                content_raw = item.get("content") if isinstance(item.get("content"), dict) else {}
                raw_html = str(content_raw.get("rendered") or "")
                link = canonicalize_url(str(item.get("link") or "").strip())
                if not link:
                    continue
                candidates.append(
                    CandidateArticle(
                        title=html_to_article_text(str(title_raw.get("rendered") or "")),
                        url=link,
                        source_name=source.name,
                        source_type="wordpress_api",
                        published_at=str(item.get("date_gmt") or item.get("date") or ""),
                        snippet=html_to_article_text(str(excerpt_raw.get("rendered") or "")),
                        metadata={"endpoint": endpoint, "source_key": source.key, "date_origin": "wordpress_api"},
                        full_text=html_to_article_text(raw_html),
                        raw_html=raw_html,
                        resolved_url=link,
                    )
                )
            self.checkpoint(int(run["id"]), worker_id, {"page": page, "candidates": len(candidates)})
            total_pages = int(response.headers.get("X-WP-TotalPages") or 0)
            if total_pages and page >= total_pages:
                break
            if len(payload) < 100:
                break
            if page == max_pages:
                capped = True
        return candidates, capped

    def _collect_google(self, run: dict[str, Any], source: SourceDefinition) -> tuple[list[CandidateArticle], bool]:
        query = str(run.get("query") or "").strip()
        end_exclusive = run["window_end"] + timedelta(days=1)
        compiled = f"{query} after:{run['window_start'].isoformat()} before:{end_exclusive.isoformat()}"
        try:
            self._throttle(source)
            _, xml_text = fetch_url(google_news_rss_url(compiled), timeout=20)
        except Exception as exc:
            raise SourceRetryable(f"google_news_fetch:{type(exc).__name__}") from exc
        candidates = parse_rss_or_atom(
            xml_text,
            source_name=source.name,
            source_type="google_news",
            metadata={"query": query, "compiled_query": compiled, "source_key": source.key, "date_origin": "feed"},
        )
        cap = int(source.config.get("result_cap") or 100)
        return candidates[:cap], len(candidates) >= cap

    def _collect_rss(self, run: dict[str, Any], source: SourceDefinition) -> tuple[list[CandidateArticle], bool]:
        try:
            self._throttle(source)
            _, xml_text = fetch_url(str(source.config.get("feed_url") or ""), timeout=15)
        except Exception as exc:
            raise SourceRetryable(f"rss_fetch:{type(exc).__name__}") from exc
        candidates = parse_rss_or_atom(
            xml_text,
            source_name=source.name,
            source_type="rss",
            metadata={"feed_url": source.config.get("feed_url"), "source_key": source.key, "date_origin": "feed"},
        )
        return candidates, False

    def collect_run(self, run: dict[str, Any], source: SourceDefinition, worker_id: str) -> tuple[list[CandidateArticle], bool]:
        if source.strategy == "sitemap_daily":
            return self._collect_sitemap(run, source, worker_id)
        if source.strategy == "wordpress_date":
            return self._collect_wordpress(run, source, worker_id)
        if source.strategy == "google_news_query":
            return self._collect_google(run, source)
        if source.strategy == "rss_realtime":
            return self._collect_rss(run, source)
        raise SourceFailed(f"unsupported_strategy:{source.strategy}")

    def _insert_observation(self, run: dict[str, Any], source: SourceDefinition, candidate: CandidateArticle) -> tuple[int, bool]:
        observed_url = canonicalize_url(candidate.url)
        observed_hash = _url_hash(observed_url)
        date_status = "feed_only" if candidate.published_at else "missing"
        if str((candidate.metadata or {}).get("date_origin") or "") == "wordpress_api":
            date_status = "api_verified"
        with self._connect() as conn:
            row = conn.execute(
                """
                INSERT INTO rio_observations(
                    source_run_id, source_key, source_name, query, observed_url,
                    observed_url_hash, title, snippet, observed_date,
                    observed_date_status, metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NULLIF(%s,'')::timestamptz,%s,%s::jsonb)
                ON CONFLICT(source_run_id, observed_url_hash, query)
                DO UPDATE SET observed_at=NOW(), metadata=EXCLUDED.metadata
                RETURNING id, (xmax = 0) AS inserted
                """,
                (
                    run["id"],
                    source.key,
                    source.name,
                    str(run.get("query") or ""),
                    observed_url,
                    observed_hash,
                    candidate.title,
                    candidate.snippet,
                    candidate.published_at,
                    date_status,
                    _json(candidate.metadata or {}),
                ),
            ).fetchone()
            return int(row["id"]), bool(row["inserted"])

    def _existing_article(self, observed_url: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT article.* FROM rio_url_aliases alias
                JOIN rio_articles article ON article.id=alias.article_id
                WHERE alias.observed_url_hash=%s
                """,
                (_url_hash(observed_url),),
            ).fetchone()

    def _record_fetch(
        self,
        observation_id: int,
        *,
        attempted_url: str,
        final_url: str,
        method: str,
        status: str,
        http_status: int | None = None,
        body_chars: int = 0,
        error: Exception | None = None,
        duration_ms: int = 0,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO rio_fetch_attempts(
                    observation_id, attempted_url, final_url, method, status,
                    http_status, body_chars, error_type, error_message, duration_ms
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    observation_id,
                    attempted_url,
                    final_url,
                    method,
                    status,
                    http_status,
                    body_chars,
                    type(error).__name__ if error else "",
                    str(error)[:500] if error else "",
                    duration_ms,
                ),
            )

    def _store_content(self, *, body: str, raw_html: str) -> tuple[str, str, str, str]:
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        text_key = f"{self.store.prefix}/corpus/objects/{digest[:2]}/{digest}.txt.gz"
        html_key = f"{self.store.prefix}/corpus/objects/{digest[:2]}/{digest}.html.gz" if raw_html else ""
        with self._connect() as conn:
            existing = conn.execute("SELECT * FROM rio_content_objects WHERE content_hash=%s", (digest,)).fetchone()
            if existing and existing["storage_status"] == "stored":
                return digest, str(existing.get("text_object_key") or ""), str(existing.get("html_object_key") or ""), "stored"
        if not self.store.enabled:
            storage_status = "storage_not_configured"
        else:
            text_ok = self.store.upload_bytes(gzip.compress(body.encode("utf-8")), text_key, "application/gzip")
            html_ok = True
            if raw_html:
                html_ok = self.store.upload_bytes(gzip.compress(raw_html.encode("utf-8")), html_key, "application/gzip")
            storage_status = "stored" if text_ok and html_ok else "storage_failed"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO rio_content_objects(
                    content_hash, text_object_key, html_object_key, body_chars,
                    html_bytes, storage_status
                ) VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT(content_hash) DO UPDATE SET
                    text_object_key=EXCLUDED.text_object_key,
                    html_object_key=EXCLUDED.html_object_key,
                    body_chars=EXCLUDED.body_chars,
                    html_bytes=EXCLUDED.html_bytes,
                    storage_status=EXCLUDED.storage_status,
                    updated_at=NOW()
                """,
                (digest, text_key, html_key or None, len(body), len(raw_html.encode("utf-8")), storage_status),
            )
        return digest, text_key, html_key, storage_status

    def _upsert_article(
        self,
        *,
        observation_id: int,
        observed_url: str,
        final_url: str,
        title: str,
        published_at: str,
        date_status: str,
        body: str,
        raw_html: str,
        download_status: str,
        source: SourceDefinition,
    ) -> tuple[int, str, dict[str, list[str]], bool, str]:
        canonical = canonicalize_url(final_url or observed_url)
        canonical_hash = _url_hash(canonical)
        content_hash = text_key = html_key = ""
        storage_status = "not_attempted"
        if len(body) >= REAL_BODY_MIN_CHARS:
            content_hash, text_key, html_key, storage_status = self._store_content(body=body, raw_html=raw_html)
            if storage_status != "stored":
                download_status = storage_status
        geo = self.gazetteer.classify(
            title=title,
            body=body,
            final_url=canonical,
            geography_prior=source.geography_prior,
        )
        dimensions = self.gazetteer.classify_dimensions(title=title, body=body)
        with self._connect() as conn:
            row = conn.execute(
                """
                INSERT INTO rio_articles(
                    canonical_url, url_hash, final_url, source_domain, title,
                    published_at, date_status, body_chars, content_hash,
                    text_object_key, html_object_key, download_status,
                    geography_status, geography_score, metadata
                ) VALUES (%s,%s,%s,%s,%s,NULLIF(%s,'')::timestamptz,%s,%s,NULLIF(%s,''),NULLIF(%s,''),NULLIF(%s,''),%s,%s,%s,%s::jsonb)
                ON CONFLICT(url_hash) DO UPDATE SET
                    final_url=EXCLUDED.final_url,
                    title=CASE WHEN length(EXCLUDED.title)>length(rio_articles.title) THEN EXCLUDED.title ELSE rio_articles.title END,
                    published_at=COALESCE(EXCLUDED.published_at,rio_articles.published_at),
                    date_status=CASE WHEN EXCLUDED.date_status IN ('page_verified','api_verified') THEN EXCLUDED.date_status ELSE rio_articles.date_status END,
                    body_chars=GREATEST(EXCLUDED.body_chars,rio_articles.body_chars),
                    content_hash=COALESCE(EXCLUDED.content_hash,rio_articles.content_hash),
                    text_object_key=COALESCE(EXCLUDED.text_object_key,rio_articles.text_object_key),
                    html_object_key=COALESCE(EXCLUDED.html_object_key,rio_articles.html_object_key),
                    download_status=EXCLUDED.download_status,
                    geography_status=EXCLUDED.geography_status,
                    geography_score=EXCLUDED.geography_score,
                    last_seen_at=NOW()
                RETURNING id, (xmax = 0) AS inserted
                """,
                (
                    canonical,
                    canonical_hash,
                    canonical,
                    _safe_host(canonical),
                    title,
                    published_at,
                    date_status,
                    len(body),
                    content_hash,
                    text_key,
                    html_key,
                    download_status,
                    geo.status,
                    geo.score,
                    _json({"storageStatus": storage_status}),
                ),
            ).fetchone()
            article_id = int(row["id"])
            inserted = bool(row["inserted"])
            for alias_url in {observed_url, canonical}:
                conn.execute(
                    """
                    INSERT INTO rio_url_aliases(observed_url_hash, observed_url, article_id)
                    VALUES (%s,%s,%s) ON CONFLICT(observed_url_hash) DO UPDATE SET article_id=EXCLUDED.article_id
                    """,
                    (_url_hash(alias_url), alias_url, article_id),
                )
            conn.execute(
                "UPDATE rio_observations SET article_id=%s, decision=%s WHERE id=%s",
                (article_id, geo.status, observation_id),
            )
            for evidence in geo.evidence:
                conn.execute(
                    """
                    INSERT INTO rio_geography_evidence(
                        article_id, gazetteer_version, evidence_kind,
                        evidence_value, evidence_location, weight
                    ) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
                    """,
                    (
                        article_id,
                        self.gazetteer.version,
                        evidence["kind"],
                        str(evidence["value"])[:500],
                        evidence["location"],
                        evidence["weight"],
                    ),
                )
            for dimension, hits in dimensions.items():
                conn.execute(
                    """
                    INSERT INTO rio_article_dimensions(article_id, dimension, evidence)
                    VALUES (%s,%s,%s::jsonb)
                    ON CONFLICT(article_id, dimension) DO UPDATE SET evidence=EXCLUDED.evidence, assigned_at=NOW()
                    """,
                    (article_id, dimension, _json(hits)),
                )
        return article_id, geo.status, dimensions, inserted, storage_status

    def _process_candidate(self, run: dict[str, Any], source: SourceDefinition, candidate: CandidateArticle) -> dict[str, int]:
        counters = {
            "observation_events": 1,
            "unique_candidates": 0,
            "fetch_attempted": 0,
            "fetch_succeeded": 0,
            "body_extracted": 0,
            "final_url_resolved": 0,
            "page_date_verified": 0,
            "city_confirmed": 0,
            "city_probable": 0,
            "state_only": 0,
            "other_city": 0,
            "duplicate_urls": 0,
            "error_count": 0,
        }
        observation_id, inserted_observation = self._insert_observation(run, source, candidate)
        counters["unique_candidates"] = int(inserted_observation)
        observed_url = canonicalize_url(candidate.url)
        existing = self._existing_article(observed_url)
        if (
            existing
            and int(existing.get("body_chars") or 0) >= REAL_BODY_MIN_CHARS
            and str(existing.get("download_status") or "") not in {"storage_not_configured", "storage_failed"}
            and bool(existing.get("text_object_key"))
        ):
            counters["duplicate_urls"] = 1
            geo_status = str(existing.get("geography_status") or "unknown")
            if geo_status in counters:
                counters[geo_status] = 1
            with self._connect() as conn:
                conn.execute(
                    "UPDATE rio_observations SET article_id=%s, decision='duplicate' WHERE id=%s",
                    (existing["id"], observation_id),
                )
            return counters

        final_url = str(candidate.resolved_url or observed_url)
        body = str(candidate.full_text or "").strip()
        raw_html = str(candidate.raw_html or "")
        title = str(candidate.title or "").strip()
        published_at = str(candidate.published_at or "").strip()
        date_status = "api_verified" if str((candidate.metadata or {}).get("date_origin") or "") == "wordpress_api" else ("feed_only" if published_at else "missing")
        http_status: int | None = None
        download_status = "pending"
        started = time.monotonic()
        counters["fetch_attempted"] = 1

        if GOOGLE_HOST in _safe_host(final_url):
            resolved = try_resolve_google_redirect(final_url, timeout=10)
            if not _is_vehicle_url(resolved):
                error = SourceRetryable("google_redirect_unresolved")
                self._record_fetch(
                    observation_id,
                    attempted_url=observed_url,
                    final_url=resolved,
                    method="google_resolve",
                    status="retryable",
                    error=error,
                    duration_ms=int((time.monotonic() - started) * 1000),
                )
                with self._connect() as conn:
                    conn.execute("UPDATE rio_observations SET decision='pending_resolution' WHERE id=%s", (observation_id,))
                counters["error_count"] = 1
                return counters
            final_url = canonicalize_url(resolved)

        if candidate.source_type == "wordpress_api" and body:
            http_status = 200
            download_status = "api_body"
            counters["fetch_succeeded"] = 1
        else:
            try:
                self._throttle(source, article_fetch=True)
                response = requests.get(final_url, headers={"User-Agent": USER_AGENT}, timeout=25, allow_redirects=True)
                http_status = response.status_code
                if response.status_code in {401, 403}:
                    raise SourceBlocked(f"article_http_{response.status_code}")
                if response.status_code == 429 or response.status_code >= 500:
                    raise SourceRetryable(f"article_http_{response.status_code}")
                response.raise_for_status()
                final_url = canonicalize_url(response.url)
                raw_html = response.text
                body = html_to_article_text(raw_html).strip()
                title = extract_html_title(raw_html) or title
                page_date = extract_published_at(raw_html)
                if page_date:
                    published_at = page_date
                    date_status = "page_verified"
                download_status = "fetched"
                counters["fetch_succeeded"] = 1
            except Exception as exc:
                status = "blocked" if isinstance(exc, SourceBlocked) else "retryable"
                self._record_fetch(
                    observation_id,
                    attempted_url=observed_url,
                    final_url=final_url,
                    method="article_get",
                    status=status,
                    http_status=http_status,
                    error=exc,
                    duration_ms=int((time.monotonic() - started) * 1000),
                )
                with self._connect() as conn:
                    conn.execute("UPDATE rio_observations SET decision=%s WHERE id=%s", (status, observation_id))
                counters["error_count"] = 1
                return counters

        if _is_vehicle_url(final_url):
            counters["final_url_resolved"] = 1
        if len(body) >= REAL_BODY_MIN_CHARS:
            counters["body_extracted"] = 1
        if date_status in {"page_verified", "api_verified"}:
            counters["page_date_verified"] = 1

        self._record_fetch(
            observation_id,
            attempted_url=observed_url,
            final_url=final_url,
            method="wordpress_api_body" if candidate.source_type == "wordpress_api" else "article_get",
            status="succeeded",
            http_status=http_status,
            body_chars=len(body),
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        _, geo_status, _, inserted_article, storage_status = self._upsert_article(
            observation_id=observation_id,
            observed_url=observed_url,
            final_url=final_url,
            title=title,
            published_at=published_at,
            date_status=date_status,
            body=body,
            raw_html=raw_html,
            download_status=download_status,
            source=source,
        )
        if not inserted_article:
            counters["duplicate_urls"] = 1
        if len(body) >= REAL_BODY_MIN_CHARS and storage_status != "stored":
            counters["error_count"] += 1
        if geo_status in counters:
            counters[geo_status] = 1
        return counters

    def _apply_counters(self, run_id: int, counters: dict[str, int]) -> None:
        fields = [
            "observation_events",
            "unique_candidates",
            "fetch_attempted",
            "fetch_succeeded",
            "body_extracted",
            "final_url_resolved",
            "page_date_verified",
            "city_confirmed",
            "city_probable",
            "state_only",
            "other_city",
            "duplicate_urls",
            "error_count",
        ]
        assignments = ", ".join(f"{field}={field}+%s" for field in fields)
        with self._connect() as conn:
            conn.execute(
                f"UPDATE rio_source_runs SET {assignments}, last_checkpoint_at=NOW(), updated_at=NOW() WHERE id=%s",
                tuple(int(counters.get(field) or 0) for field in fields) + (run_id,),
            )

    def _split_capped_google_run(self, run: dict[str, Any]) -> int:
        start = run["window_start"]
        end = run["window_end"]
        if start >= end:
            return 0
        midpoint = start + timedelta(days=(end - start).days // 2)
        children = ((start, midpoint), (midpoint + timedelta(days=1), end))
        inserted = 0
        with self._connect() as conn:
            for child_start, child_end in children:
                row = conn.execute(
                    """
                    INSERT INTO rio_source_runs(
                        job_id, source_key, source_name, strategy, window_start,
                        window_end, query, query_hash, priority
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT DO NOTHING RETURNING id
                    """,
                    (
                        run["job_id"],
                        run["source_key"],
                        run["source_name"],
                        run["strategy"],
                        child_start,
                        child_end,
                        run["query"],
                        run["query_hash"],
                        run["priority"],
                    ),
                ).fetchone()
                inserted += int(bool(row))
            if inserted:
                conn.execute(
                    "UPDATE rio_corpus_jobs SET total_windows=total_windows+%s WHERE id=%s",
                    (inserted, run["job_id"]),
                )
        return inserted

    def finish_run(self, run: dict[str, Any], *, status: str, error_message: str = "") -> None:
        if status not in RUN_TERMINAL_STATES | {"retryable"}:
            raise ValueError(f"invalid_source_run_status:{status}")
        next_attempt = None
        if status == "retryable" and int(run.get("attempts") or 0) < int(run.get("max_attempts") or 5):
            next_attempt = _utcnow() + timedelta(seconds=min(1800, 30 * (2 ** max(0, int(run.get("attempts") or 1) - 1))))
        elif status == "retryable":
            status = "failed"
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE rio_source_runs SET status=%s, error_message=%s,
                    next_attempt_at=%s, finished_at=CASE WHEN %s='retryable' THEN NULL ELSE NOW() END,
                    lease_owner=NULL, leased_until=NULL, last_checkpoint_at=NOW(), updated_at=NOW()
                WHERE id=%s
                """,
                (status, error_message[:1000], next_attempt, status, run["id"]),
            )
            remaining = conn.execute(
                "SELECT COUNT(*)::int AS count FROM rio_source_runs WHERE job_id=%s AND status IN ('queued','running','retryable')",
                (run["job_id"],),
            ).fetchone()["count"]
            job_state = conn.execute("SELECT status FROM rio_corpus_jobs WHERE id=%s", (run["job_id"],)).fetchone()
            if job_state and job_state["status"] in {"cancelled", "canceled"}:
                return
            if remaining == 0:
                bad = conn.execute(
                    "SELECT COUNT(*)::int AS count FROM rio_source_runs WHERE job_id=%s AND status NOT IN ('exhausted','empty_verified')",
                    (run["job_id"],),
                ).fetchone()["count"]
                job_status = "succeeded" if bad == 0 else "completed_with_gaps"
                conn.execute(
                    "UPDATE rio_corpus_jobs SET status=%s, finished_at=NOW(), last_progress_at=NOW() WHERE id=%s",
                    (job_status, run["job_id"]),
                )
            else:
                conn.execute("UPDATE rio_corpus_jobs SET last_progress_at=NOW() WHERE id=%s", (run["job_id"],))

    def process_claimed_run(self, run: dict[str, Any], *, worker_id: str) -> dict[str, Any]:
        source = self.registry.get(str(run["source_key"]))
        try:
            candidates, capped = self.collect_run(run, source, worker_id)
            counters_total = {key: 0 for key in (
                "observation_events", "unique_candidates", "fetch_attempted", "fetch_succeeded",
                "body_extracted", "final_url_resolved", "page_date_verified", "city_confirmed",
                "city_probable", "state_only", "other_city", "duplicate_urls", "error_count",
            )}
            cumulative = dict(counters_total)
            workers = max(1, min(32, int(os.environ.get("RIO_CORPUS_FETCH_WORKERS") or DEFAULT_FETCH_WORKERS)))
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(self._process_candidate, run, source, candidate) for candidate in candidates]
                for index, future in enumerate(as_completed(futures), start=1):
                    result = future.result()
                    for key, value in result.items():
                        counters_total[key] += int(value)
                        cumulative[key] += int(value)
                    if index % 20 == 0:
                        self._apply_counters(int(run["id"]), counters_total)
                        counters_total = {key: 0 for key in counters_total}
                        self.checkpoint(int(run["id"]), worker_id, {"processed": index, "candidates": len(candidates)})
            self._apply_counters(int(run["id"]), counters_total)
            if capped:
                split_count = self._split_capped_google_run(run) if source.strategy == "google_news_query" else 0
                if split_count:
                    self.finish_run(run, status="capped", error_message="google_result_cap_split_into_child_windows")
                elif cumulative["error_count"]:
                    self.finish_run(run, status="retryable", error_message=f"{cumulative['error_count']}_candidate_errors_at_source_cap")
                    return {"runId": run["id"], "status": "retryable", "candidates": len(candidates)}
                else:
                    self.finish_run(run, status="capped", error_message="source_limit_reached")
                final_state = "capped"
            elif cumulative["error_count"]:
                self.finish_run(run, status="retryable", error_message=f"{cumulative['error_count']}_candidate_errors")
                final_state = "retryable"
            else:
                final_state = "exhausted" if candidates else "empty_verified"
                self.finish_run(run, status=final_state)
            return {"runId": run["id"], "status": final_state, "candidates": len(candidates)}
        except SourceBlocked as exc:
            self.finish_run(run, status="blocked", error_message=str(exc))
            return {"runId": run["id"], "status": "blocked", "error": str(exc)}
        except SourceFailed as exc:
            self.finish_run(run, status="failed", error_message=str(exc))
            return {"runId": run["id"], "status": "failed", "error": str(exc)}
        except Exception as exc:
            self.finish_run(run, status="retryable", error_message=f"{type(exc).__name__}:{exc}")
            return {"runId": run["id"], "status": "retryable", "error": str(exc)}

    def run_worker_once(self, *, worker_id: str = "") -> dict[str, Any]:
        worker = worker_id or f"{socket.gethostname()}:{os.getpid()}"
        run = self.claim_run(worker_id=worker)
        if not run:
            return {"status": "idle", "workerId": worker}
        return {"workerId": worker, **self.process_claimed_run(run, worker_id=worker)}

    def has_job(self, job_id: str) -> bool:
        if not self.configured or not job_id:
            return False
        self.ensure_schema()
        with self._connect() as conn:
            return bool(conn.execute("SELECT 1 AS ok FROM rio_corpus_jobs WHERE id=%s", (job_id,)).fetchone())

    def resume_job(self, job_id: str) -> dict[str, Any]:
        self.ensure_schema()
        with self._connect() as conn:
            job = conn.execute("SELECT * FROM rio_corpus_jobs WHERE id=%s FOR UPDATE", (job_id,)).fetchone()
            if not job:
                raise ValueError("rio_corpus_job_not_found")
            reset = conn.execute(
                """
                UPDATE rio_source_runs SET status='queued', next_attempt_at=NULL,
                    lease_owner=NULL, leased_until=NULL, finished_at=NULL,
                    error_message='', updated_at=NOW()
                WHERE job_id=%s AND status IN ('retryable','failed')
                RETURNING id
                """,
                (job_id,),
            ).fetchall()
            if not reset:
                raise ValueError("rio_corpus_no_resumable_windows")
            conn.execute(
                "UPDATE rio_corpus_jobs SET status='queued', finished_at=NULL, error_message='' WHERE id=%s",
                (job_id,),
            )
            updated = conn.execute("SELECT * FROM rio_corpus_jobs WHERE id=%s", (job_id,)).fetchone()
            return self._job_payload(conn, updated)

    def cancel_job(self, job_id: str = "") -> dict[str, Any]:
        self.ensure_schema()
        with self._connect() as conn:
            if job_id:
                job = conn.execute("SELECT * FROM rio_corpus_jobs WHERE id=%s FOR UPDATE", (job_id,)).fetchone()
            else:
                job = conn.execute(
                    "SELECT * FROM rio_corpus_jobs WHERE status IN ('queued','running') ORDER BY requested_at DESC LIMIT 1 FOR UPDATE"
                ).fetchone()
            if not job:
                raise ValueError("rio_corpus_no_active_job")
            conn.execute(
                """
                UPDATE rio_source_runs SET status='failed', error_message='operator_cancelled',
                    finished_at=NOW(), lease_owner=NULL, leased_until=NULL, updated_at=NOW()
                WHERE job_id=%s AND status IN ('queued','running','retryable')
                """,
                (job["id"],),
            )
            conn.execute(
                "UPDATE rio_corpus_jobs SET status='cancelled', finished_at=NOW(), error_message='operator_cancelled' WHERE id=%s",
                (job["id"],),
            )
            updated = conn.execute("SELECT * FROM rio_corpus_jobs WHERE id=%s", (job["id"],)).fetchone()
            return self._job_payload(conn, updated)

    def source_run_events(self, job_id: str, *, limit: int = 100) -> dict[str, Any]:
        coverage = self.coverage(job_id=job_id, page=1, page_size=max(1, min(limit, 500)))
        events = []
        for run in coverage["items"]:
            events.append(
                {
                    "created_at": run.get("last_checkpoint_at") or run.get("updated_at"),
                    "event": f"source_run_{run.get('status') or 'unknown'}",
                    "payload": {
                        "source_run_id": run.get("id"),
                        "source_key": run.get("source_key"),
                        "source_name": run.get("source_name"),
                        "window_start": run.get("window_start"),
                        "window_end": run.get("window_end"),
                        "query": run.get("query"),
                        "status": run.get("status"),
                        "attempts": run.get("attempts"),
                        "checkpoint": run.get("checkpoint") or {},
                        "observation_events": run.get("observation_events"),
                        "body_extracted": run.get("body_extracted"),
                        "error_message": run.get("error_message"),
                    },
                }
            )
        return {"job_id": job_id, "events": events, "count": len(events), "limit": limit, "backend": "rio_corpus"}

    def list_articles(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        year: int | None = None,
        source: str = "",
        geography: str = "",
        download_status: str = "",
        dimension: str = "",
    ) -> dict[str, Any]:
        self.ensure_schema()
        page = max(1, page)
        page_size = max(1, min(200, page_size))
        clauses = ["1=1"]
        params: list[Any] = []
        if year:
            clauses.append("EXTRACT(YEAR FROM article.published_at)=%s")
            params.append(year)
        if source:
            clauses.append("article.source_domain=%s")
            params.append(source)
        if geography:
            clauses.append("article.geography_status=%s")
            params.append(geography)
        if download_status:
            clauses.append("article.download_status=%s")
            params.append(download_status)
        if dimension:
            clauses.append("EXISTS (SELECT 1 FROM rio_article_dimensions d WHERE d.article_id=article.id AND d.dimension=%s)")
            params.append(dimension)
        where = " AND ".join(clauses)
        with self._connect() as conn:
            total = conn.execute(f"SELECT COUNT(*)::bigint AS count FROM rio_articles article WHERE {where}", tuple(params)).fetchone()["count"]
            rows = conn.execute(
                f"""
                SELECT article.*,
                    COALESCE((SELECT jsonb_object_agg(d.dimension,d.evidence) FROM rio_article_dimensions d WHERE d.article_id=article.id),'{{}}'::jsonb) AS dimensions
                FROM rio_articles article WHERE {where}
                ORDER BY article.published_at DESC NULLS LAST, article.id DESC
                LIMIT %s OFFSET %s
                """,
                tuple(params) + (page_size, (page - 1) * page_size),
            ).fetchall()
        return {"page": page, "pageSize": page_size, "total": int(total), "items": [self._public_article(row) for row in rows]}

    def sources(self) -> dict[str, Any]:
        items = []
        for source in self.registry.sources:
            config = source.config
            items.append(
                {
                    "key": source.key,
                    "name": source.name,
                    "domain": source.domain,
                    "strategy": source.strategy,
                    "historicalRole": config.get("historical_role") or "",
                    "geographyPrior": source.geography_prior,
                    "startDate": source.start_date,
                    "window": source.window,
                    "enabled": source.enabled,
                    "registryState": "active" if source.enabled else str(config.get("registry_state") or "blocked"),
                    "knownConstraint": str(config.get("known_constraint") or ""),
                    "allowedPathPrefixes": list(config.get("allowed_path_prefixes") or []),
                    "rateLimitPerSecond": float(config.get("rate_limit_per_second") or 0),
                }
            )
        return {"version": self.registry.version, "count": len(items), "items": items}

    def _public_article(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "title": row.get("title") or "",
            "url": row.get("final_url") or row.get("canonical_url") or "",
            "source": row.get("source_domain") or "",
            "publishedAt": row.get("published_at"),
            "dateStatus": row.get("date_status"),
            "bodyChars": row.get("body_chars"),
            "downloadStatus": row.get("download_status"),
            "geographyStatus": row.get("geography_status"),
            "geographyScore": row.get("geography_score"),
            "dimensions": row.get("dimensions") or {},
        }

    def coverage(
        self,
        *,
        job_id: str = "",
        page: int = 1,
        page_size: int = 100,
        year: int | None = None,
        source_key: str = "",
        status: str = "",
    ) -> dict[str, Any]:
        self.ensure_schema()
        page = max(1, page)
        page_size = max(1, min(500, page_size))
        clauses: list[str] = []
        values: list[Any] = []
        if job_id:
            clauses.append("job_id=%s")
            values.append(job_id)
        if year:
            clauses.append("EXTRACT(YEAR FROM window_start)=%s")
            values.append(year)
        if source_key:
            clauses.append("source_key=%s")
            values.append(source_key)
        if status:
            clauses.append("status=%s")
            values.append(status)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params: tuple[Any, ...] = tuple(values)
        with self._connect() as conn:
            total = conn.execute(f"SELECT COUNT(*)::bigint AS count FROM rio_source_runs {where}", params).fetchone()["count"]
            rows = conn.execute(
                f"""
                SELECT * FROM rio_source_runs {where}
                ORDER BY id DESC LIMIT %s OFFSET %s
                """,
                params + (page_size, (page - 1) * page_size),
            ).fetchall()
        return {"page": page, "pageSize": page_size, "total": int(total), "items": [dict(row) for row in rows]}

    def audit_samples(self, *, job_id: str = "", limit: int = 50) -> dict[str, Any]:
        self.ensure_schema()
        limit = max(1, min(200, limit))
        where = "WHERE run.job_id=%s" if job_id else ""
        params: tuple[Any, ...] = (job_id,) if job_id else ()
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT observation.id AS observation_id, observation.source_name,
                    observation.query, observation.observed_url, observation.decision,
                    observation.observed_date_status, article.id AS article_id,
                    article.final_url, article.title, article.body_chars,
                    article.date_status, article.download_status,
                    article.geography_status, article.geography_score,
                    fetch.status AS fetch_status, fetch.http_status,
                    fetch.error_type, fetch.error_message
                FROM rio_observations observation
                JOIN rio_source_runs run ON run.id=observation.source_run_id
                LEFT JOIN rio_articles article ON article.id=observation.article_id
                LEFT JOIN LATERAL (
                    SELECT * FROM rio_fetch_attempts f
                    WHERE f.observation_id=observation.id ORDER BY f.id DESC LIMIT 1
                ) fetch ON TRUE
                {where}
                ORDER BY observation.id DESC LIMIT %s
                """,
                params + (limit,),
            ).fetchall()
        return {"count": len(rows), "items": [dict(row) for row in rows]}

    def schedule_realtime(self, *, started_by: str = "cron") -> dict[str, Any]:
        now = _utcnow()
        bucket = now.replace(minute=(now.minute // 5) * 5, second=0, microsecond=0)
        return self.start_job(
            {
                "date_from": now.date().isoformat(),
                "date_to": now.date().isoformat(),
                "collector": "realtime",
                "priority": 100,
                "idempotency_key": f"rio-realtime-{bucket.isoformat()}",
            },
            started_by=started_by,
        )

    def import_legacy_sqlite(self, *, limit: int = 0) -> dict[str, Any]:
        import sqlite3

        self.ensure_schema()
        sqlite_path = db_path()
        if not sqlite_path.is_file():
            return {"scanned": 0, "imported": 0, "reason": "sqlite_missing"}
        query = """
            SELECT DISTINCT a.id, a.url, a.title, a.published_at, a.source_name,
                COALESCE(a.full_text,'') AS full_text,
                COALESCE(a.raw_html,'') AS raw_html
            FROM articles a
            JOIN mentions m ON m.article_id=a.id
            WHERE m.target_key='rio_economico'
            ORDER BY a.id
        """
        if limit:
            query += f" LIMIT {max(1, int(limit))}"
        scanned = imported = storage_pending = 0
        with sqlite3.connect(sqlite_path) as sqlite_conn:
            sqlite_conn.row_factory = sqlite3.Row
            rows = sqlite_conn.execute(query).fetchall()
        legacy_source = SourceDefinition(
            key="legacy_sqlite",
            name="Legacy SQLite",
            domain="",
            strategy="legacy_sqlite",
            geography_prior="neutral",
            start_date="2011-01-01",
            window="legacy",
            enabled=True,
            config={},
        )
        job_id = "legacy-sqlite-import"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO rio_corpus_jobs(
                    id,batch_id,idempotency_key,scope,topic,status,collector,
                    priority,date_from,date_to,requested_by,total_windows,metadata
                ) VALUES (%s,%s,%s,%s,%s,'running','legacy_sqlite',1,%s,%s,'migration',1,%s::jsonb)
                ON CONFLICT(id) DO UPDATE SET status='running', finished_at=NULL, last_progress_at=NOW()
                """,
                (
                    job_id,
                    job_id,
                    job_id,
                    RIO_ECONOMICO_SCOPE,
                    RIO_CITY_TOPIC,
                    date(2011, 1, 1),
                    date.today(),
                    _json({"provenance": "legacy_sqlite"}),
                ),
            )
            run_row = conn.execute(
                """
                INSERT INTO rio_source_runs(
                    job_id,source_key,source_name,strategy,window_start,window_end,
                    query,query_hash,priority,status,lease_owner,leased_until
                ) VALUES (%s,'legacy_sqlite','Legacy SQLite','legacy_sqlite',%s,%s,'','',1,'running','migration',NOW()+INTERVAL '1 hour')
                ON CONFLICT(job_id,source_key,window_start,window_end,query_hash)
                DO UPDATE SET status='running', lease_owner='migration', leased_until=NOW()+INTERVAL '1 hour'
                RETURNING *
                """,
                (job_id, date(2011, 1, 1), date.today()),
            ).fetchone()
        run = dict(run_row)
        for row in rows:
            scanned += 1
            url = canonicalize_url(str(row["url"] or ""))
            if not url:
                continue
            candidate = CandidateArticle(
                title=str(row["title"] or ""),
                url=url,
                source_name=str(row["source_name"] or "Legacy SQLite"),
                source_type="legacy_sqlite",
                published_at=str(row["published_at"] or ""),
                snippet="",
                metadata={"provenance": "legacy_sqlite", "legacy_sqlite_id": int(row["id"])},
                full_text=str(row["full_text"] or ""),
                raw_html=str(row["raw_html"] or ""),
                resolved_url=url,
            )
            observation_id, _ = self._insert_observation(run, legacy_source, candidate)
            _, _, _, was_inserted, storage_status = self._upsert_article(
                observation_id=observation_id,
                observed_url=url,
                final_url=url,
                title=candidate.title,
                published_at=candidate.published_at,
                date_status="legacy_unknown",
                body=candidate.full_text,
                raw_html=candidate.raw_html,
                download_status="legacy_sqlite",
                source=legacy_source,
            )
            imported += int(was_inserted)
            storage_pending += int(len(candidate.full_text) >= REAL_BODY_MIN_CHARS and storage_status != "stored")
            with self._connect() as conn:
                conn.execute(
                    "UPDATE rio_articles SET legacy_sqlite_id=%s WHERE url_hash=%s",
                    (int(row["id"]), _url_hash(url)),
                )
        final_status = "exhausted" if storage_pending == 0 else "retryable"
        self.finish_run(run, status=final_status, error_message=f"{storage_pending}_storage_objects_pending" if storage_pending else "")
        return {"scanned": scanned, "imported": imported, "storagePending": storage_pending, "status": final_status}


rio_corpus = RioCorpusService()
