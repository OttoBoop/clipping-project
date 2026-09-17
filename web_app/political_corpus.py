"""Durable, manually requested political clipping, separate from the Rio city corpus.

The web process only enqueues and reads. Workers own bounded discovery/fetch/review
tasks. Authorization always uses an explicit target allowlist, including for admin.
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import ipaddress
import json
import os
import re
import socket
import tempfile
import threading
import time
import uuid
from dataclasses import fields
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

import requests

from pipeline.matcher import CitationMatcher, Target
from pipeline.normalization import canonicalize_url, clean_title
from .config import DATA_DIR
from .political_schema import SCHEMA_SQL, SCHEMA_UPGRADES, SCHEMA_VERSION
from .political_metrics import record_timing, timed_operation, set_publisher_source
from .political_rate_limits import (
    DomainCooldown, TASK_DOMAIN_FALLBACK_SQL, active_cooldown, domain_deferral,
    normalize_domain, record_response_cooldown, remaining_seconds,
    retry_after_deadline, task_request_domain,
)
from .publisher_tls import publisher_verify
from .storage_bridge import ArtifactStore, artifact_store
from .political_body_batches import BatchBodyUnavailable, WordPressBodyBatches
from .political_record_types import non_news_reason
from .political_worker_limits import fetch_concurrency
from .political_source_catalog import catalog_sources, select_sources, source_snapshot, source_aliases, source_for_task
from .political_recovery import PoliticalRecoveryMixin, recovery_filters
from .political_document_tasks import PoliticalDocumentMixin, DOCUMENT_SCHEMA_SQL
from .political_documents import DocumentProblem
from .political_request_urls import (
    is_google_access_challenge, is_google_block_response, is_publisher_access_challenge,
    publisher_article_identity_urls, publisher_article_request_url,
)

START_DATE = date(2026, 6, 1)
ZONE = ZoneInfo("America/Sao_Paulo")
LEASE_SECONDS = 180
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_SITEMAP_RESPONSE_BYTES = 128 * 1024 * 1024
MAX_SITEMAP_RESPONSE_SECONDS = 120
BODY_MIN_CHARS = 200
TERMINAL = {"complete", "gap", "failed", "cancelled", "split"}
ACTIVE = {"queued", "running", "retryable"}
SITEMAP_INDEX_TASK_SQL = """(t.payload->>'strategy' IN ('expanded_sitemap','expanded_daily_sitemap')
    AND t.cursor ? 'invalid_children' AND COALESCE(t.cursor->>'document_fingerprint','')<>'')"""


def _known_sitemap_index(payload: dict, cursor: dict) -> bool:
    # These cursor fields are committed only after parsing a sitemapindex.
    # The adapter rejects a changed document kind before emitting candidates.
    return (payload.get("strategy") in {"expanded_sitemap", "expanded_daily_sitemap"}
            and "invalid_children" in cursor and bool(cursor.get("document_fingerprint")))


def _page_google_result(result: dict, *, limit: int = 100) -> dict:
    """Persist any excess RSS candidates before admitting a smaller fetch batch.

    Normal Google feeds fit in 100 entries. Larger responses retain all parsed
    candidates and the final split/gap decision in the task's durable cursor;
    subsequent batches never repeat the HTTP request. Raw entries count once.
    """
    candidates = result.get("candidates") or []
    if len(candidates) <= limit:
        return result
    pending = {**result, "candidates": candidates[limit:], "raw_count": 0}
    return {"candidates": candidates[:limit], "outcome": "continue",
            "raw_count": result.get("raw_count", 0), "child_tasks": [],
            "next_cursor": {"google_pending_result": pending}}


def _publisher_host(hostname: str) -> str:
    hostname = str(hostname).strip().lower().rstrip(".")
    return hostname[4:] if hostname.startswith("www.") else hostname


@lru_cache(maxsize=1)
def _publisher_registry() -> dict[str, tuple[str, str]]:
    return {_publisher_host(domain): (row["key"], row["name"])
            for row in catalog_sources() for domain in [row.get("domain", ""), *row.get("domains", [])]
            if domain}


def _source_domains() -> dict[str, str]:
    return {source_key: normalize_domain(domain)
            for domain, (source_key, _) in _publisher_registry().items()}


def _confirmed_publisher(candidate: dict, resolved_url: str) -> dict:
    """Attribute a successfully fetched outlet while retaining discovery provenance."""
    hostname = _publisher_host(urlparse(resolved_url).hostname or "")
    publisher = _publisher_registry().get(hostname)
    source_key, source_name = publisher or ("publisher:" + hostname, hostname)
    provenance = {"method": "resolved_fetch_registry" if publisher else "resolved_fetch_hostname",
                  "hostname": hostname, "resolved_url": resolved_url,
                  "discovery_source_key": str(candidate.get("source_key") or ""),
                  "discovery_source_name": str(candidate.get("source_name") or "")}
    return {**candidate, "source_key": source_key, "source_name": source_name, "_publisher_confirmed": True,
            "metadata": {**(candidate.get("metadata") or {}), "publisher_provenance": provenance}}


class PoliticalCorpusError(RuntimeError):
    pass


class PoliticalCorpusNotConfigured(PoliticalCorpusError):
    pass


class PoliticalAccessDenied(PoliticalCorpusError):
    pass


class PoliticalNotFound(PoliticalCorpusError):
    pass


class LeaseLost(PoliticalCorpusError):
    pass


class FetchProblem(PoliticalCorpusError):
    def __init__(self, code: str, *, retryable: bool = True, status_code: int = 0, retry_after: int = 0):
        super().__init__(code)
        self.retryable, self.status_code, self.retry_after = retryable, status_code, retry_after


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str, sort_keys=True)


def _keys(values: Any) -> list[str]:
    if not isinstance(values, (list, tuple, set)):
        raise ValueError("target_keys_required")
    return list(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))


def _scope(allowed_target_keys: list[str], requested: list[str] | None = None) -> list[str]:
    allowed = _keys(allowed_target_keys)
    if not allowed:
        raise PoliticalAccessDenied("political_target_access_required")
    selected = _keys(requested) if requested is not None else allowed
    if not selected or not set(selected).issubset(allowed):
        raise PoliticalAccessDenied("political_target_access_denied")
    return selected


def parse_date(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=ZONE)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=ZONE)
    except (ValueError, TypeError):
        return None


def _date_window(payload: dict) -> tuple[date, date]:
    start = date.fromisoformat(str(payload.get("date_from") or payload.get("dateFrom") or START_DATE))
    end = date.fromisoformat(str(payload.get("date_to") or payload.get("dateTo") or datetime.now(ZONE).date()))
    if start < START_DATE or end < start or end > datetime.now(ZONE).date():
        raise ValueError("invalid_political_date_window")
    return start, end


def _target(row: dict) -> Target:
    supported = {field.name for field in fields(Target)}
    return Target(**{key: value for key, value in row.items() if key in supported})


def match_targets(snapshots: list[dict], title: str, body: str) -> list[dict]:
    matcher = CitationMatcher([_target(row) for row in snapshots], exact_names_only=True)
    hits = matcher.find_hits(f"{title}\n{body}")
    unique = {}
    for hit in hits:
        unique.setdefault(hit.target_key, {"target_key": hit.target_key, "target_name": hit.target_name,
                                          "keyword_matched": hit.keyword_matched})
    return list(unique.values())


def encode_cursor(stamp: Any, article_id: int) -> str:
    return base64.urlsafe_b64encode(_json([str(stamp), int(article_id)]).encode()).decode().rstrip("=")


def decode_cursor(value: str) -> tuple[datetime, int]:
    try:
        if len(value) > 512:
            raise ValueError()
        stamp, article_id = json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)))
        parsed = parse_date(stamp)
        if not parsed or int(article_id) < 1:
            raise ValueError()
        return parsed, int(article_id)
    except Exception as exc:
        raise ValueError("invalid_cursor") from exc


class PoliticalCorpusService(PoliticalRecoveryMixin, PoliticalDocumentMixin):
    def __init__(self, *, store: ArtifactStore | None = None, database_url: str = ""):
        self.store = store or artifact_store
        self._database_url = database_url
        self._pool = None
        self._pool_lock = threading.Lock()
        self._schema_lock = threading.Lock()
        self._schema_ready = False
        self._http_local = threading.local()
        self._body_batches = WordPressBodyBatches(self.store)

    @property
    def database_url(self) -> str:
        return self._database_url or str(os.environ.get("POLITICAL_DATABASE_URL") or os.environ.get("RIO_CORPUS_DATABASE_URL") or "").strip()

    @property
    def configured(self) -> bool:
        return bool(self.database_url)

    def _connect(self):
        if not self.configured:
            raise PoliticalCorpusNotConfigured("political_database_not_configured")
        if self._pool is None:
            with self._pool_lock:
                if self._pool is None:
                    from psycopg.rows import dict_row
                    from psycopg_pool import ConnectionPool
                    self._pool = ConnectionPool(self.database_url, min_size=1, max_size=12,
                                                kwargs={"row_factory": dict_row, "connect_timeout": 10}, open=True)
        return self._pool.connection(timeout=15)

    def close(self) -> None:
        if self._pool is not None:
            self._pool.close()

    def ensure_schema(self) -> None:
        if self._schema_ready:
            return
        with self._schema_lock:
            if self._schema_ready:
                return
            with self._connect() as conn:
                conn.execute("SELECT pg_advisory_xact_lock(734892101)")
                for statement in SCHEMA_SQL.split(";"):
                    if statement.strip():
                        conn.execute(statement)
                for statement in SCHEMA_UPGRADES:
                    conn.execute(statement)
                from .political_istoe_inventory import SCHEMA as ISTOE_SCHEMA
                from .political_istoe_monitor import SCHEMA as ISTOE_MONITOR_SCHEMA
                ISTOE_SCHEMA += ISTOE_MONITOR_SCHEMA
                for statement in ISTOE_SCHEMA.split(";"):
                    if statement.strip():
                        conn.execute(statement)
                for statement in DOCUMENT_SCHEMA_SQL.split(";"):
                    if statement.strip():
                        conn.execute(statement)
            self._schema_ready = True

    def health(self, check_database: bool = False) -> dict:
        result = {"backend": SCHEMA_VERSION, "configured": self.configured,
                  "bodyStorageConfigured": bool(self.store.enabled), "manualOnly": True}
        if check_database and self.configured:
            self.ensure_schema()
            with self._connect() as conn:
                result["databaseOk"] = bool(conn.execute("SELECT 1 AS ok").fetchone()["ok"])
                result["workers"] = self._workers(conn)
                imports = conn.execute("SELECT source_key,completed,validation FROM political_import_progress ORDER BY source_key").fetchall()
                result["migrationReady"] = bool(imports) and all(row["completed"] and row["validation"].get("ok") for row in imports)
                result["imports"] = [dict(row) for row in imports]
        return result

    def _snapshots(self, payload: dict, selected: list[str]) -> list[dict]:
        snapshots = payload.get("target_snapshots") or payload.get("targetSnapshots")
        if not snapshots:
            raw = json.loads((DATA_DIR / "targets.json").read_text(encoding="utf-8"))
            snapshots = raw.get("targets", []) if isinstance(raw, dict) else raw
        by_key = {str(row.get("key") or ""): row for row in snapshots if isinstance(row, dict)}
        if any(key not in by_key for key in selected):
            raise ValueError("unknown_political_target")
        return [by_key[key] for key in selected]

    def start_job(self, payload: dict, *, started_by: str, allowed_target_keys: list[str]) -> dict:
        selected = _scope(allowed_target_keys, payload.get("target_keys") or payload.get("targetKeys"))
        start, end = _date_window(payload)
        snapshots = self._snapshots(payload, selected)
        discovery_keys = selected
        if "discovery_target_keys" in payload:
            raw = payload["discovery_target_keys"]
            if not isinstance(raw, list) or not raw or any(not isinstance(k, str) or k not in selected for k in raw):
                raise ValueError("invalid_discovery_targets")
            discovery_keys = list(dict.fromkeys(raw))
        discovery_snapshots = [s for s in snapshots if s["key"] in discovery_keys]
        kind = str(payload.get("kind") or "collect")
        if kind not in {"collect", "review", "recover"}:
            raise ValueError("invalid_political_job_kind")
        profile = str(payload.get("collection_profile") or "")
        requested_sources = payload.get("source_keys", payload.get("sourceKeys"))
        sources = select_sources(requested_sources, profile)
        configuration = {**source_snapshot(sources), "collection_profile": profile,
                         "discovery_target_keys": discovery_keys}
        if kind == "recover":
            configuration["recovery_gap_types"] = recovery_filters(payload)
            if 'istoe_deferred_dates' in configuration['recovery_gap_types'] and (configuration['source_keys'] != ['istoe'] or configuration['recovery_gap_types'] != ['istoe_deferred_dates']):
                raise ValueError('istoe_recovery_source_required')
        if not self.store.enabled:
            raise PoliticalCorpusNotConfigured("political_body_storage_not_configured")
        self.ensure_schema()
        if kind == "recover":
            tasks = [{"source_key": row["key"], "source_snapshot": row, "strategy": "recover",
                      "date_from": start.isoformat(), "date_to": end.isoformat(), "cursor": {"after_id": 0}}
                     for row in sources if row.get("domain")]
        elif kind == "review":
            tasks = [{"source_key": "_review", "strategy": "review", "cursor": {"after_id": 0}}]
        else:
            from .political_discovery import build_tasks
            tasks = build_tasks(discovery_snapshots, start.isoformat(), end.isoformat(),
                                source_keys=configuration["source_keys"], source_snapshots=sources)
        if not tasks:
            raise ValueError("no_political_sources")
        job_id = "political-" + uuid.uuid4().hex
        request_key = str(payload.get("request_key") or payload.get("requestKey") or "").strip()[:128] or None
        with self._connect() as conn:
            if request_key:
                conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", ("political-request:" + request_key,))
                existing = conn.execute("SELECT * FROM political_jobs WHERE request_key=%s", (request_key,)).fetchone()
                if existing:
                    self._authorize_job(existing, selected)
                    if existing["target_keys"] != selected or existing["date_from"] != start or existing["date_to"] != end or existing["kind"] != kind:
                        raise ValueError("request_key_conflict")
                    if (existing.get("metadata") or {}).get("discovery_target_keys", existing["target_keys"]) != discovery_keys:
                        raise ValueError("request_key_conflict")
                    old_meta = existing.get("metadata") or {}
                    for key in ("source_keys", "collection_profile", "recovery_gap_types"):
                        if old_meta.get(key) != configuration.get(key):
                            raise ValueError("request_key_conflict")
                    return self._job_dto(existing)
            if kind == "recover":
                configuration["recovery_max_observation_id"] = conn.execute(
                    "SELECT COALESCE(MAX(id),0) AS n FROM political_observations").fetchone()["n"]
            conn.execute("""INSERT INTO political_jobs(id,kind,target_keys,target_snapshots,date_from,date_to,requested_by,request_key)
                            VALUES (%s,%s,%s,%s::jsonb,%s,%s,%s,%s)""",
                         (job_id, kind, selected, _json(snapshots), start, end, started_by, request_key))
            conn.execute("UPDATE political_jobs SET metadata=metadata || %s::jsonb WHERE id=%s",
                         (_json(configuration), job_id))
            for task in tasks:
                self._insert_task(conn, job_id, "review" if kind == "review" else "discovery", task)
            row = conn.execute("SELECT * FROM political_jobs WHERE id=%s", (job_id,)).fetchone()
        return self._job_dto(row)

    def _insert_task(self, conn, job_id: str, kind: str, payload: dict) -> None:
        source_key = str(payload.get("source_key") or "unknown")
        dedupe = canonicalize_url(str(payload.get("url") or "")) if kind == "fetch" else hashlib.sha256(_json(payload).encode()).hexdigest()
        if kind == "discovery" and payload.get("strategy") == "expanded_edition_archive":
            identity = {k: payload.get(k) for k in ("source_key", "date_from", "date_to", "mechanism")}
            identity["url"] = canonicalize_url(str(payload.get("url") or ""))
            dedupe = "edition-index:" + hashlib.sha256(_json(identity).encode()).hexdigest()
        # Source rotation still comes first when claiming. Within each source,
        # finish its direct publisher discovery before optional Google queries.
        priority = 0 if kind == "discovery" and payload.get("strategy") == "google_news" else 10
        if kind == "fetch" and source_key == "g1" and re.match(r"^/(?:rj|politica|eleicoes)(?:/|$)", urlparse(str(payload.get("url") or "")).path):
            priority = 20
        if kind == "fetch" and source_key == "estadao" and re.match(r"^/(?:politica|opiniao)(?:/|$)", urlparse(str(payload.get("url") or "")).path):
            # Prioritize useful editorial sections without filtering out any
            # other section or requiring a name in a headline/URL.
            priority = 20
        if kind == "fetch" and (payload.get("metadata") or {}).get("partition_status") == "requested_calendar_partition":
            priority = 20
        conn.execute("""INSERT INTO political_tasks(job_id,kind,source_key,dedupe_key,payload,cursor,request_domain,priority)
                        VALUES (%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s) ON CONFLICT(job_id,kind,dedupe_key) DO NOTHING""",
                     (job_id, kind, source_key, dedupe, _json(payload), _json(payload.get("cursor") or {}),
                      task_request_domain(kind, payload, _source_domains()), priority))
        conn.execute("INSERT INTO political_source_leases(source_key) VALUES (%s) ON CONFLICT DO NOTHING", (source_key,))

    @staticmethod
    def _authorize_job(row: dict | None, allowed: list[str]) -> None:
        if not row or not set(row["target_keys"]).issubset(allowed):
            raise PoliticalNotFound("political_job_not_found")

    @staticmethod
    def _job_dto(row: dict) -> dict:
        return {"id": row["id"], "kind": row["kind"], "status": row["status"],
                "discoveryTargetKeys": (row.get("metadata") or {}).get("discovery_target_keys", row["target_keys"]),
                "targetKeys": row["target_keys"], "dateFrom": str(row["date_from"]), "dateTo": str(row["date_to"]),
                "sourceKeys": (row.get("metadata") or {}).get("source_keys", []),
                "sourceCatalogVersion": (row.get("metadata") or {}).get("source_catalog_version", ""),
                "createdAt": str(row["created_at"]), "updatedAt": str(row["updated_at"]),
                "finishedAt": str(row["finished_at"]) if row.get("finished_at") else None}

    def list_jobs(self, *, allowed_target_keys: list[str], limit: int = 20) -> list[dict]:
        allowed = _scope(allowed_target_keys)
        self.ensure_schema()
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM political_jobs WHERE target_keys <@ %s ORDER BY created_at DESC LIMIT %s",
                                (allowed, max(1, min(int(limit), 50)))).fetchall()
        return [self._job_dto(row) for row in rows]

    def status(self, job_id: str = "", *, allowed_target_keys: list[str]) -> dict:
        allowed = _scope(allowed_target_keys)
        if not self.configured:
            return {**self.health(), "current": None, "recent": [], "workers": []}
        recent = self.list_jobs(allowed_target_keys=allowed)
        current = None
        self.ensure_schema()
        with self._connect() as conn:
            selected_id = job_id or (recent[0]["id"] if recent else "")
            if selected_id:
                row = conn.execute("SELECT * FROM political_jobs WHERE id=%s", (selected_id,)).fetchone()
                self._authorize_job(row, allowed)
                current = self._job_dto(row)
                current["metrics"] = self._metrics(conn, selected_id)
            workers = self._workers(conn)
        return {**self.health(), "current": current, "recent": recent, "workers": workers}

    def _metrics(self, conn, job_id: str) -> dict:
        counters = conn.execute("SELECT articles_inserted,mentions_inserted,fetch_attempted FROM political_jobs WHERE id=%s", (job_id,)).fetchone()
        tasks = conn.execute("""SELECT kind,status,COUNT(*) AS count,COALESCE(SUM(raw_count),0) AS raw_count
                                FROM political_tasks WHERE job_id=%s GROUP BY kind,status""", (job_id,)).fetchall()
        # Resolve authorized article IDs once. Carrying the job's full target
        # array through every observation spilled the status aggregate to disk.
        observed = conn.execute("""WITH visible AS MATERIALIZED (
            SELECT DISTINCT m.article_id FROM political_mentions m JOIN political_jobs j
            ON j.id=%s AND m.target_key=ANY(j.target_keys))
            SELECT COUNT(*) AS unique_candidates,
            COUNT(DISTINCT o.article_id) FILTER(WHERE v.article_id IS NOT NULL) AS articles_saved,
            COUNT(*) FILTER (WHERE disposition='duplicate') AS duplicates,
            COUNT(DISTINCT o.article_id) FILTER (WHERE disposition='duplicate'
                AND v.article_id IS NOT NULL) AS articles_reused,
            COUNT(*) FILTER (WHERE disposition='no_match') AS no_match,
            COUNT(*) FILTER (WHERE disposition='outside_window') AS outside_window,
            COUNT(*) FILTER (WHERE disposition='outside_window'
                AND metadata->>'date_reused_in_discovery'='true') AS discovery_dates_reused
            FROM political_observations o LEFT JOIN visible v ON v.article_id=o.article_id
            WHERE o.job_id=%s""", (job_id, job_id)).fetchone()
        quality = conn.execute("""WITH visible AS MATERIALIZED (
            SELECT DISTINCT m.article_id FROM political_mentions m JOIN political_jobs j
            ON j.id=%s AND m.target_key=ANY(j.target_keys))
            SELECT COUNT(*) FILTER (WHERE a.body_status='body_extracted') AS body_extracted,
            COUNT(*) FILTER (WHERE a.text_object_key<>'') AS text_available,
            COUNT(*) FILTER (WHERE a.metadata->>'text_extent'='partial') AS partial_text,
            COUNT(*) FILTER (WHERE a.text_object_key='') AS metadata_only,
            COUNT(*) FILTER (WHERE a.published_at IS NULL) AS unknown_dates,
            COUNT(*) FILTER (WHERE a.body_status<>'body_extracted' OR a.date_status NOT IN ('page_verified','api_verified')) AS needs_review,
            COUNT(*) FILTER (WHERE a.date_status IN ('page_verified','api_verified')) AS dates_verified
            FROM political_articles a JOIN visible v ON v.article_id=a.id WHERE EXISTS
            (SELECT 1 FROM political_observations o
             WHERE o.job_id=%s AND o.article_id=a.id)""", (job_id, job_id)).fetchone()
        document_results = conn.execute("""SELECT
            COALESCE(SUM((result->>'documentsNew')::int),0) AS documents_new,
            COALESCE(SUM((result->>'editionPagesNew')::int),0) AS pages_new,
            COALESCE(SUM((result->>'editionPagesReused')::int),0) AS pages_reused,
            COALESCE(SUM((result->>'editionAssociationsNew')::int),0) AS mentions_new,
            COALESCE(SUM((result->>'editionTextAvailable')::int),0) AS texts
            FROM political_tasks WHERE job_id=%s AND payload->>'document_task' IS NOT NULL""", (job_id,)).fetchone()
        istoe = conn.execute("""SELECT COUNT(*) FILTER(WHERE result ? 'istoeInventory' AND result->'istoeInventory' IS NOT NULL AND payload->>'inventory_part' IS NOT NULL AND status IN ('complete','gap')) AS parts_read,
            MAX((result->'istoeInventory'->>'partsTotal')::int) AS parts_total,
            MAX((result->'istoeInventory'->>'partsRemaining')::int) AS parts_remaining,
            COUNT(*) FILTER(WHERE result->>'istoeSnapshotReused'='true') AS snapshots_reused
            FROM political_tasks WHERE job_id=%s AND source_key='istoe'""",(job_id,)).fetchone()
        deferred_dates = conn.execute("SELECT COUNT(*) AS n FROM political_observations WHERE job_id=%s AND disposition='deferred_date'",(job_id,)).fetchone()['n']
        sample = conn.execute("SELECT sampled_at,payload FROM political_istoe_samples WHERE job_id=%s ORDER BY id DESC LIMIT 1",(job_id,)).fetchone()
        return {"istoeWorkerSample": {"sampledAt": sample["sampled_at"].isoformat(), **sample["payload"]} if sample else None,
                "istoePartsRead": int(istoe['parts_read'] or 0), "istoePartsTotal": int(istoe['parts_total'] or 0),
                "istoePartsRemaining": int(istoe['parts_remaining'] or 0), "istoeSnapshotsReused": int(istoe['snapshots_reused'] or 0),
                "istoeDeferredDates": int(deferred_dates),
                "uniqueCandidates": int(observed["unique_candidates"]), "articlesSaved": int(observed["articles_saved"]),
                "documentsNew": int(document_results["documents_new"]), "editionPagesNew": int(document_results["pages_new"]),
                "editionPagesReused": int(document_results["pages_reused"]), "editionAssociationsNew": int(document_results["mentions_new"]),
                "editionTextAvailable": int(document_results["texts"]),
                "articlesInserted": int(counters["articles_inserted"]), "mentionsInserted": int(counters["mentions_inserted"]),
                "fetchAttempted": int(counters["fetch_attempted"]),
                "articlesReused": int(observed["articles_reused"]), "metadataOnly": int(quality["metadata_only"]),
                "fetchPending": sum(int(row["count"]) for row in tasks if row["kind"] == "fetch" and row["status"] in ACTIVE),
                "unresolvedGaps": sum(int(row["count"]) for row in tasks if row["status"] in {"gap", "failed"}),
                "duplicates": int(observed["duplicates"]), "noMatch": int(observed["no_match"]),
                "outsideWindow": int(observed["outside_window"]),
                "discoveryDatesReused": int(observed["discovery_dates_reused"]), "bodyExtracted": int(quality["body_extracted"]),
                "textAvailable": int(quality["text_available"]), "partialText": int(quality["partial_text"]),
                # Filtering before this join is essential on discovery-heavy
                # jobs: the planner otherwise probes large task payloads for
                # every observation even when no text was enriched.
                "articlesEnriched": int(conn.execute("""WITH enriched_tasks AS MATERIALIZED (
                    SELECT job_id,payload->>'url' AS url FROM political_tasks
                    WHERE job_id=%s AND (result->>'bodyEnriched'='true'
                        OR cursor->>'partial_body_enriched'='true'))
                    SELECT COUNT(DISTINCT o.article_id) AS n FROM enriched_tasks t
                    JOIN political_observations o ON o.job_id=t.job_id AND o.observed_url=t.url""", (job_id,)).fetchone()["n"]),
                "datesVerified": int(quality["dates_verified"]),
                "unknownDates": int(quality["unknown_dates"]), "needsReview": int(quality["needs_review"]),
                "rawEntries": sum(int(row["raw_count"]) for row in tasks if row["kind"] == "discovery"),
                "tasks": [{"kind": row["kind"], "status": row["status"], "count": int(row["count"])} for row in tasks]}

    @staticmethod
    def _workers(conn) -> list[dict]:
        rows = conn.execute("""SELECT id,kind,heartbeat_at,error_type,(heartbeat_at>NOW()-INTERVAL '60 seconds') AS healthy
                               FROM political_workers WHERE heartbeat_at>NOW()-INTERVAL '1 day' ORDER BY kind,id""").fetchall()
        return [{"id": row["id"], "kind": row["kind"], "heartbeatAt": str(row["heartbeat_at"]),
                 "healthy": row["healthy"], "errorType": row["error_type"]} for row in rows]

    def cancel_job(self, job_id: str, *, allowed_target_keys: list[str]) -> dict:
        allowed = _scope(allowed_target_keys)
        self.ensure_schema()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM political_jobs WHERE id=%s FOR UPDATE", (job_id,)).fetchone()
            self._authorize_job(row, allowed)
            conn.execute("UPDATE political_jobs SET status='cancelled',finished_at=NOW(),updated_at=NOW() WHERE id=%s", (job_id,))
            conn.execute("""UPDATE political_tasks SET status='cancelled',lease_token=NULL,lease_owner=NULL,leased_until=NULL,
                            updated_at=NOW() WHERE job_id=%s AND status=ANY(%s)""", (job_id, list(ACTIVE)))
            conn.execute("""UPDATE political_source_leases SET leased_until=NULL,lease_token=NULL,task_id=NULL
                            WHERE task_id IN (SELECT id FROM political_tasks WHERE job_id=%s)""", (job_id,))
        return self.status(job_id, allowed_target_keys=allowed)["current"]

    def resume_job(self, job_id: str, *, allowed_target_keys: list[str]) -> dict:
        allowed = _scope(allowed_target_keys)
        self.ensure_schema()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM political_jobs WHERE id=%s FOR UPDATE", (job_id,)).fetchone()
            self._authorize_job(row, allowed)
            conn.execute("""UPDATE political_tasks SET status='queued',attempts=0,next_attempt_at=NULL,
                            lease_owner=NULL,lease_token=NULL,leased_until=NULL,error_type='',updated_at=NOW()
                            WHERE job_id=%s AND status IN ('gap','failed','cancelled','retryable')""", (job_id,))
            conn.execute("UPDATE political_jobs SET status='queued',finished_at=NULL,updated_at=NOW() WHERE id=%s", (job_id,))
            self._refresh_job(conn, job_id)
        return self.status(job_id, allowed_target_keys=allowed)["current"]

    def source_catalog(self, *, profile: str, allowed_target_keys: list[str]) -> dict:
        from .political_source_catalog import allowed_sources
        allowed = _scope(allowed_target_keys)
        sources = allowed_sources(profile)
        publishers = {s["key"]: {"key": s["key"], "name": s["name"], "articles": 0,
                      "collectable": bool(s.get("enabled", True))} for s in sources if s.get("domain")}
        if self.configured:
            self.ensure_schema()
            with self._connect() as conn:
                rows = conn.execute("""SELECT source_key,MAX(source_name) AS name,COUNT(*) AS articles,
                    COUNT(*) FILTER(WHERE text_object_key<>'') AS text_available FROM political_articles a
                    WHERE EXISTS(SELECT 1 FROM political_mentions m WHERE m.article_id=a.id AND m.target_key=ANY(%s))
                    GROUP BY source_key""", (allowed,)).fetchall()
            for row in rows:
                source = next((s for s in sources if row["source_key"] in source_aliases(s["key"], sources)), None)
                key = source["key"] if source else row["source_key"]
                item = publishers.setdefault(key, {"key": key, "name": row["name"], "articles": 0, "collectable": False})
                item["articles"] += row["articles"]
                item["textAvailable"] = item.get("textAvailable", 0) + row["text_available"]
        return {"sources": sources, "publishers": sorted(publishers.values(), key=lambda x: x["name"].casefold())}

    def coverage(self, job_id: str = "", *, allowed_target_keys: list[str], cursor: int = 0, page_size: int = 50) -> dict:
        allowed = _scope(allowed_target_keys)
        status = self.status(job_id, allowed_target_keys=allowed)
        current = status["current"]
        if not current:
            return {"jobId": "", "sources": [], "gaps": []}
        with self._connect() as conn:
            rows = conn.execute("""SELECT source_key,kind,status,COUNT(*) AS count FROM political_tasks
                WHERE job_id=%s GROUP BY source_key,kind,status ORDER BY source_key,kind,status""", (current["id"],)).fetchall()
            size = max(1, min(int(page_size), 200))
            if cursor < 0:
                raise ValueError("invalid_cursor")
            total = conn.execute("SELECT COUNT(*) AS n FROM political_tasks WHERE job_id=%s AND status IN ('gap','failed','retryable')", (current["id"],)).fetchone()["n"]
            gaps = conn.execute("""SELECT id,source_key,kind,status,error_type,payload->>'date_from' AS date_from,
                payload->>'date_to' AS date_to FROM political_tasks WHERE job_id=%s AND status IN ('gap','failed','retryable')
                AND id>%s ORDER BY id LIMIT %s""", (current["id"], cursor, size + 1)).fetchall()
        more, gaps = len(gaps) > size, gaps[:size]
        return {"jobId": current["id"], "status": current["status"], "sources": [dict(row) for row in rows],
                "gaps": [dict(row) for row in gaps], "metrics": current["metrics"], "totalGaps": total,
                "hasMore": more, "nextCursor": gaps[-1]["id"] if more else None}

    def _article_filters(self, allowed: list[str], *, target_keys=None, cursor="", q="", date_from="", date_to="", source_key="", body_status="", story_id=None):
        selected = _scope(allowed, target_keys)
        clauses = ["EXISTS (SELECT 1 FROM political_mentions m WHERE m.article_id=a.id AND m.target_key=ANY(%s))"]
        args: list[Any] = [selected]
        if story_id is not None:
            clauses.append("EXISTS (SELECT 1 FROM political_story_articles sa WHERE sa.article_id=a.id AND sa.story_id=%s)")
            args.append(int(story_id))
        if cursor:
            stamp, article_id = decode_cursor(cursor)
            clauses.append("(COALESCE(a.published_at,a.discovered_at),a.id)<(%s,%s)")
            args.extend([stamp, article_id])
        if q:
            clauses.append("(a.title ILIKE %s OR a.snippet ILIKE %s)")
            escaped = str(q)[:200].replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            args.extend([f"%{escaped}%"] * 2)
        if date_from:
            clauses.append("a.published_at >= %s")
            args.append(datetime.combine(date.fromisoformat(date_from), datetime.min.time(), ZONE))
        if date_to:
            clauses.append("a.published_at < %s")
            args.append(datetime.combine(date.fromisoformat(date_to) + timedelta(days=1), datetime.min.time(), ZONE))
        if source_key:
            clauses.append("a.source_key=ANY(%s)")
            args.append(source_aliases(source_key))
        if body_status:
            if body_status not in {"metadata_only", "body_extracted", "legacy_body"}:
                raise ValueError("invalid_body_status")
            clauses.append("a.body_status=%s")
            args.append(body_status)
        return " AND ".join(clauses), args

    def _article_rows(self, conn, where: str, args: list, allowed: list[str], limit: int) -> list[dict]:
        return conn.execute(f"""SELECT a.*, COALESCE(a.published_at,a.discovered_at) AS sort_stamp,
            (SELECT array_agg(m.target_key ORDER BY m.target_key) FROM political_mentions m
             WHERE m.article_id=a.id AND m.target_key=ANY(%s)) AS visible_targets,
            (SELECT MIN(story_id) FROM political_story_articles sa WHERE sa.article_id=a.id) AS story_id
            FROM political_articles a WHERE {where}
            ORDER BY COALESCE(a.published_at,a.discovered_at) DESC,a.id DESC LIMIT %s""", [allowed] + args + [limit]).fetchall()

    @staticmethod
    def _article_dto(row: dict) -> dict:
        return {"id": row["id"], "url": row["canonical_url"], "title": row["title"],
                "sourceName": row["source_name"], "sourceKey": row["source_key"],
                "publishedAt": str(row["published_at"]) if row["published_at"] else None,
                "discoveredAt": str(row["discovered_at"]), "dateStatus": row["date_status"],
                "snippet": row["snippet"], "summary": row["summary"], "targetKeys": row.get("visible_targets") or [],
                "bodyStatus": row["body_status"], "bodyChars": row["body_chars"],
                "textAvailable": bool(row.get("text_object_key")),
                "textExtent": (row.get("metadata") or {}).get("text_extent", "unknown" if row.get("text_object_key") else "absent"),
                "extractionMethod": (row.get("metadata") or {}).get("extraction_method", ""),
                "restrictionEvidence": (row.get("metadata") or {}).get("restriction_evidence", []),
                "needsReview": row["body_status"] != "body_extracted" or row["date_status"] not in {"page_verified", "api_verified"},
                "storyId": row.get("story_id"), "legacyId": row["legacy_id"]}

    def list_articles(self, *, allowed_target_keys: list[str], page_size: int = 50, cursor: str = "", target_keys=None,
                      q: str = "", date_from: str = "", date_to: str = "", source_key: str = "", body_status: str = "", story_id=None,
                      job_id: str = "") -> dict:
        allowed = _scope(allowed_target_keys)
        self.ensure_schema()
        size = max(1, min(int(page_size), 200))
        where, args = self._article_filters(allowed, target_keys=target_keys, cursor=cursor, q=q, date_from=date_from,
                                           date_to=date_to, source_key=source_key, body_status=body_status, story_id=story_id)
        with self._connect() as conn:
            if job_id:
                self._authorize_job(conn.execute("SELECT target_keys FROM political_jobs WHERE id=%s", (job_id,)).fetchone(), allowed)
                where += " AND EXISTS (SELECT 1 FROM political_observations o WHERE o.job_id=%s AND o.article_id=a.id)"
                args.append(job_id)
            rows = self._article_rows(conn, where, args, allowed, size + 1)
        more = len(rows) > size
        rows = rows[:size]
        return {"items": [self._article_dto(row) for row in rows], "hasMore": more,
                "nextCursor": encode_cursor(rows[-1]["sort_stamp"], rows[-1]["id"]) if more else ""}

    def _article_by_identifier(self, conn, article_id: int, allowed: list[str]) -> dict:
        # Merge revisions already preserve every retired identifier and are
        # reassigned when the canonical row itself merges again. Resolve within
        # the same SQL snapshot as the scoped article read, including its text
        # pointer, so a concurrent merge cannot produce a missing second row.
        rows = self._article_rows(conn, """a.id=COALESCE(
            (SELECT current_article.id FROM political_articles current_article WHERE current_article.id=%s),
            (SELECT r.article_id FROM political_article_revisions r
             WHERE r.reason='canonical_duplicate_merge' AND r.previous->>'id'=%s
             ORDER BY r.id DESC LIMIT 1))
            AND EXISTS (SELECT 1 FROM political_mentions m WHERE m.article_id=a.id AND m.target_key=ANY(%s))""",
            [int(article_id), str(int(article_id)), allowed], allowed, 1)
        if not rows:
            raise PoliticalNotFound("political_article_not_found")
        return rows[0]

    def article(self, article_id: int, *, allowed_target_keys: list[str]) -> dict:
        allowed = _scope(allowed_target_keys)
        self.ensure_schema()
        with self._connect() as conn:
            row = self._article_by_identifier(conn, article_id, allowed)
        result = self._article_dto(row)
        if result["id"] != int(article_id):
            result["requestedId"] = int(article_id)
        return result

    def list_stories(self, *, allowed_target_keys: list[str], page_size: int = 50, cursor: str = "", **filters) -> dict:
        allowed = _scope(allowed_target_keys)
        self.ensure_schema()
        size = max(1, min(int(page_size), 200))
        where, args = self._article_filters(allowed, **filters)
        preview_args = list(args)
        having = ""
        if cursor:
            stamp, story_id = decode_cursor(cursor)
            having = "WHERE (last_article,s.id)<(%s,%s)"
            args.extend([stamp, story_id])
        with self._connect() as conn:
            rows = conn.execute(f"""WITH visible AS (
                SELECT sa.story_id,MAX(COALESCE(a.published_at,a.discovered_at)) AS last_article,COUNT(*) AS count
                FROM political_articles a JOIN political_story_articles sa ON sa.article_id=a.id
                WHERE {where} GROUP BY sa.story_id)
                SELECT s.*,v.last_article,v.count FROM visible v JOIN political_stories s ON s.id=v.story_id
                {having} ORDER BY last_article DESC,s.id DESC LIMIT %s""", args + [size + 1]).fetchall()
            more = len(rows) > size
            rows = rows[:size]
            items = []
            for row in rows:
                articles = self._article_rows(conn,
                    "EXISTS (SELECT 1 FROM political_story_articles sa WHERE sa.article_id=a.id AND sa.story_id=%s) "
                    "AND " + where, [row["id"]] + preview_args, allowed, 1)
                items.append({"id": row["id"], "title": articles[0]["title"] if articles else row["title"],
                              "summary": articles[0]["summary"] if articles else "", "articleCount": row["count"],
                              "legacyId": row["legacy_id"], "articles": [self._article_dto(item) for item in articles],
                              "hasMoreArticles": int(row["count"]) > len(articles),
                              "targetKeys": sorted({key for item in articles for key in (item.get("visible_targets") or [])})})
        return {"items": items, "hasMore": more,
                "nextCursor": encode_cursor(rows[-1]["last_article"], rows[-1]["id"]) if more else ""}

    def _read_text(self, key: str, digest: str) -> str:
        return self._read_object_bytes(key, digest).decode("utf-8")

    def _read_object_bytes(self, key: str, digest: str) -> bytes:
        if not key:
            return b""
        if hasattr(self.store, "read_political_object"):
            payload = self.store.read_political_object(key)
        else:
            response = requests.get(self.store._object_url(key), headers=self.store._headers(), timeout=30, stream=True)
            response.raise_for_status()
            chunks, size = [], 0
            started = time.monotonic()
            try:
                for part in response.iter_content(65536):
                    size += len(part)
                    if size > MAX_RESPONSE_BYTES:
                        raise FetchProblem("text_object_too_large", retryable=False)
                    chunks.append(part)
            finally:
                record_timing("http_body", time.monotonic() - started, status_code=response.status_code)
                response.close()
            payload = b"".join(chunks)
        import io
        with gzip.GzipFile(fileobj=io.BytesIO(payload)) as zipped:
            raw = zipped.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES or hashlib.sha256(raw).hexdigest() != digest:
            raise FetchProblem("text_object_integrity_error", retryable=False)
        return raw

    def _read_discovery_response(self, key: str, digest: str) -> bytes:
        if not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
            raise FetchProblem("discovery_object_key_mismatch", retryable=False)
        expected = f"{self.store.prefix}/political/objects/{digest[:2]}/{digest}.discovery.gz"
        if key != expected:
            raise FetchProblem("discovery_object_key_mismatch", retryable=False)
        return self._read_object_bytes(key, digest)

    def article_text(self, article_id: int, *, allowed_target_keys: list[str]) -> dict:
        allowed = _scope(allowed_target_keys)
        self.ensure_schema()
        with self._connect() as conn:
            row = self._article_by_identifier(conn, article_id, allowed)
        metadata = row.get("metadata") or {}
        return {"id": row["id"], **({"requestedId": int(article_id)} if row["id"] != int(article_id) else {}),
                "bodyStatus": row["body_status"],
                "textAvailable": bool(row["text_object_key"]),
                "textExtent": metadata.get("text_extent", "unknown") if row["text_object_key"] else "unavailable",
                "extractionMethod": metadata.get("extraction_method", ""),
                "extractionVersion": metadata.get("extraction_version", ""),
                "contentFormat": metadata.get("content_format", "article"),
                "bodyOrigin": metadata.get("body_origin", ""),
                "restrictionEvidence": metadata.get("restriction_evidence", []),
                "publisherProvenance": metadata.get("publisher_provenance", {}),
                "contentHash": row["content_hash"],
                "text": self._read_text(row["text_object_key"], row["content_hash"])}

    def classifications(self, article_id: int, *, allowed_target_keys: list[str]) -> dict:
        allowed = _scope(allowed_target_keys)
        article_id = self.article(article_id, allowed_target_keys=allowed)["id"]
        with self._connect() as conn:
            rows = conn.execute("""SELECT * FROM political_classifications WHERE article_id=%s AND target_key=ANY(%s)
                                   ORDER BY target_key""", (int(article_id), allowed)).fetchall()
        return {"articleId": int(article_id), "items": [{"targetKey": row["target_key"], "payload": row["payload"],
                  "updatedBy": row["updated_by"], "updatedAt": str(row["updated_at"]), "legacyId": row["legacy_id"]} for row in rows]}

    def upsert_classification(self, article_id: int, payload: dict, *, allowed_target_keys: list[str], updated_by: str) -> dict:
        target_key = str(payload.get("target_key") or payload.get("targetKey") or "")
        _scope(allowed_target_keys, [target_key])
        article_id = self.article(article_id, allowed_target_keys=[target_key])["id"]
        content = payload.get("payload") if isinstance(payload.get("payload"), dict) else {key: value for key, value in payload.items() if key not in {"target_key", "targetKey"}}
        if len(_json(content).encode()) > 32000:
            raise ValueError("classification_too_large")
        for key in ("article_sentiment", "target_sentiment", "articleSentiment", "targetSentiment"):
            if key in content and content[key] not in {None, "positive", "negative", "neutral"}:
                raise ValueError("invalid_sentiment")
        with self._connect() as conn:
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (f"political-classification:{article_id}:{target_key}",))
            if not conn.execute("SELECT 1 FROM political_mentions WHERE article_id=%s AND target_key=%s",
                                (int(article_id), target_key)).fetchone():
                raise PoliticalNotFound("political_article_not_found")
            previous = conn.execute("SELECT * FROM political_classifications WHERE article_id=%s AND target_key=%s FOR UPDATE",
                                    (int(article_id), target_key)).fetchone()
            if previous and previous["payload"] != content:
                conn.execute("INSERT INTO political_classification_revisions(article_id,target_key,previous,updated_by) VALUES (%s,%s,%s::jsonb,%s)",
                             (int(article_id), target_key, _json(dict(previous)), updated_by))
            conn.execute("""INSERT INTO political_classifications(article_id,target_key,payload,updated_by)
                VALUES (%s,%s,%s::jsonb,%s) ON CONFLICT(article_id,target_key) DO UPDATE SET
                payload=EXCLUDED.payload,updated_by=EXCLUDED.updated_by,updated_at=NOW()""",
                         (int(article_id), target_key, _json(content), updated_by))
        return self.classifications(article_id, allowed_target_keys=allowed_target_keys)

    def revision_history(self, article_id: int, *, allowed_target_keys: list[str], limit: int = 50) -> dict:
        allowed = _scope(allowed_target_keys)
        article_id = self.article(article_id, allowed_target_keys=allowed)["id"]
        with self._connect() as conn:
            articles = conn.execute("SELECT id,previous,reason,created_at FROM political_article_revisions WHERE article_id=%s ORDER BY id DESC LIMIT %s",
                                    (int(article_id), max(1, min(int(limit), 100)))).fetchall()
            classifications = conn.execute("""SELECT id,target_key,previous,updated_by,created_at FROM political_classification_revisions
                WHERE article_id=%s AND target_key=ANY(%s) ORDER BY id DESC LIMIT %s""", (int(article_id), allowed, max(1, min(int(limit), 100)))).fetchall()
        # Revision metadata contains object pointers, never storage credentials or other targets' classifications.
        return {"articleId": int(article_id), "articles": [dict(row) for row in articles],
                "classifications": [dict(row) for row in classifications]}

    def insert_manual_story(self, payload: dict, *, allowed_target_keys: list[str], created_by: str) -> dict:
        selected = _scope(allowed_target_keys, payload.get("target_keys") or payload.get("targetKeys"))
        url = canonicalize_url(str(payload.get("url") or ""))
        title = clean_title(payload.get("title") or "")
        if urlparse(url).scheme not in {"https", "http"} or not urlparse(url).hostname or not title:
            raise ValueError("url_and_title_required")
        snapshots = self._snapshots(payload, selected)
        body = str(payload.get("full_text") or payload.get("fullText") or "")
        digest, key = self._store_text(body)
        published = parse_date(payload.get("published_at") or payload.get("publishedAt"))
        if published and published.astimezone(ZONE).date() < START_DATE:
            raise ValueError("invalid_political_date_window")
        self.ensure_schema()
        hits = [{"target_key": row["key"], "target_name": row.get("display_name") or row.get("label") or row["key"],
                 "keyword_matched": "manual_assignment"} for row in snapshots]
        with self._connect() as conn:
            article_id = self._persist_article(conn, {"url": url, "title": title, "source_key": "manual",
                "source_name": str(payload.get("source_name") or payload.get("sourceName") or "Manual"),
                "snippet": str(payload.get("snippet") or ""), "metadata": {"manual": True, "created_by": created_by}}, hits,
                published=published, date_status="manual" if published else "unknown", body_chars=len(body), digest=digest, object_key=key,
                summary=str(payload.get("summary") or ""))
        return self.article(article_id, allowed_target_keys=allowed_target_keys)

    def import_sqlite(self, sqlite_path, *, allowed_target_keys: list[str], source_key: str = "legacy_clipping", batch_size: int = 100,
                      snapshot_sha256: str = "", remote_backup: str = "") -> dict:
        from .political_migration import import_batch
        return import_batch(self, sqlite_path, allowed_target_keys=allowed_target_keys, source_key=source_key, batch_size=batch_size,
                            snapshot_sha256=snapshot_sha256, remote_backup=remote_backup)

    def heartbeat(self, worker_id: str, kind: str, task_id: int | None = None, error_type: str = "") -> None:
        self.ensure_schema()
        with self._connect() as conn:
            conn.execute("""INSERT INTO political_workers(id,kind,task_id,error_type) VALUES (%s,%s,%s,%s)
                ON CONFLICT(id) DO UPDATE SET kind=EXCLUDED.kind,task_id=EXCLUDED.task_id,error_type=EXCLUDED.error_type,heartbeat_at=NOW()""",
                         (worker_id, kind, task_id, error_type[:100]))

    @staticmethod
    def _discovery_backpressure(conn, *, reserve_next=False, next_capacity=500) -> tuple[bool, list[str]]:
        """Aggregate once across active jobs, instead of once per queued task.

        Below 2000 active fetches every source may discover. From 2000 to
        3999, admit only sources with fewer than 100 active fetches. Reserve
        each running page's maximum (100 for recovery, bounded Atom or Google, 500 for other discovery,
        zero for already identified sitemap indexes) before admission, so
        concurrent results fit the 4000-fetch budget.
        """
        rows = conn.execute("""SELECT t.source_key,COUNT(*) AS n FROM political_tasks t
            JOIN political_jobs j ON j.id=t.job_id
            WHERE t.kind='fetch' AND t.status=ANY(%s) AND j.status IN ('queued','running')
            GROUP BY t.source_key""", (list(ACTIVE),)).fetchall()
        total = sum(int(row["n"]) for row in rows)
        running = conn.execute("""SELECT COALESCE(SUM(CASE WHEN """ + SITEMAP_INDEX_TASK_SQL + """ THEN 0
            WHEN t.payload->>'strategy' IN ('recover','expanded_blogger_feed') OR (t.payload->>'strategy'='google_news'
                AND t.cursor->>'google_batch_capacity'='100') THEN 100 ELSE 500 END),0) AS n FROM political_tasks t
            JOIN political_jobs j ON j.id=t.job_id WHERE t.kind='discovery'
            AND t.status='running' AND t.leased_until>NOW() AND j.status IN ('queued','running')""").fetchone()["n"]
        reservation = int(running) + (next_capacity if reserve_next else 0)
        return total + reservation > 4000 or total >= 4000, [row["source_key"] for row in rows if total >= 2000 and int(row["n"]) >= 100]

    def claim_task(self, kind: str, *, worker_id: str, lease_seconds: int = LEASE_SECONDS) -> dict | None:
        if kind not in {"discovery", "fetch"}:
            raise ValueError("invalid_worker_kind")
        self.ensure_schema()
        kinds = ["discovery", "review"] if kind == "discovery" else ["fetch"]
        maximum = 2 if kind == "discovery" else fetch_concurrency()
        with self._connect() as conn:
            conn.execute("SELECT pg_advisory_xact_lock(%s)", (734892102 if kind == "discovery" else 734892103,))
            blocked_sources = []
            small_page_only = False
            index_only = False
            if kind == "discovery":
                stop_discovery, blocked_sources = self._discovery_backpressure(conn, reserve_next=True)
                if stop_discovery:
                    stop_small_page, blocked_sources = self._discovery_backpressure(conn, reserve_next=True, next_capacity=100)
                    small_page_only = True
                    # Known indexes emit bounded discovery children, never
                    # article-fetch tasks; no fetch capacity is reserved for them.
                    index_only = stop_small_page
            count = conn.execute("""SELECT COUNT(*) AS n FROM political_tasks WHERE kind=ANY(%s)
                AND status='running' AND leased_until>NOW()""", (kinds,)).fetchone()["n"]
            if count >= maximum:
                return None
            source_domains = _source_domains()
            # Prefer a publisher whose normal 1rps reservation is already due,
            # before applying source fairness and section priority. Busy domains
            # remain eligible when there is no ready work; fetch still enforces
            # the shared reservation and every Retry-After cooldown.
            row = conn.execute("""SELECT t.* FROM political_tasks t JOIN political_jobs j ON j.id=t.job_id
                LEFT JOIN political_source_leases scheduling ON scheduling.source_key=t.source_key
                LEFT JOIN political_domain_limits cooling ON cooling.domain=""" + TASK_DOMAIN_FALLBACK_SQL + """
                WHERE t.kind=ANY(%s) AND j.status IN ('queued','running')
                AND (t.kind='fetch' OR """ + SITEMAP_INDEX_TASK_SQL + """ OR NOT (t.source_key=ANY(%s)))
                AND (NOT %s OR t.payload->>'strategy' IN ('recover','google_news','expanded_blogger_feed','expanded_congresso_archive') OR """ + SITEMAP_INDEX_TASK_SQL + """)
                AND (NOT %s OR """ + SITEMAP_INDEX_TASK_SQL + """)
                AND (cooling.cooldown_until IS NULL OR cooling.cooldown_until<=NOW())
                AND (t.status IN ('queued','retryable') OR (t.status='running' AND t.leased_until<NOW()))
                AND (t.next_attempt_at IS NULL OR t.next_attempt_at<=NOW())
                AND (t.kind='fetch' OR NOT EXISTS (SELECT 1 FROM political_source_leases s
                    WHERE s.source_key=t.source_key AND s.leased_until>NOW()))
                AND (t.kind<>'fetch' OR COALESCE(t.cursor->>'resolved_url',t.payload->>'url') NOT LIKE 'https://news.google.com/%%'
                    OR NOT EXISTS (SELECT 1 FROM political_tasks active
                        WHERE active.kind='fetch' AND active.status='running' AND active.leased_until>NOW()
                        AND COALESCE(active.cursor->>'resolved_url',active.payload->>'url') LIKE 'https://news.google.com/%%'))
                AND (t.payload->>'document_task' IS NULL OR NOT EXISTS (
                    SELECT 1 FROM political_tasks heavy WHERE heavy.kind='fetch'
                    AND heavy.payload->>'document_task' IS NOT NULL
                    AND heavy.status='running' AND heavy.leased_until>NOW()))
                AND (t.payload->>'document_task' IS NULL OR NOT %s)
                ORDER BY CASE WHEN t.kind='fetch' AND cooling.next_request_at>NOW() THEN 1 ELSE 0 END,
                    CASE WHEN t.kind='discovery' AND t.payload->>'strategy'='recover' THEN 0 ELSE 1 END,
                    CASE WHEN t.kind='fetch' THEN scheduling.fetch_claimed_at
                              ELSE scheduling.discovery_claimed_at END ASC NULLS FIRST,
                    CASE WHEN t.kind='discovery' AND t.payload->>'strategy'='expanded_blogger_feed' THEN 0 ELSE 1 END,
                    CASE WHEN t.kind='discovery' AND t.payload->'partition_hint'->>0 IS NOT NULL THEN 0 ELSE 1 END,
                    t.priority DESC,
                    CASE WHEN t.kind='fetch' AND COALESCE(t.payload->>'published_at','')<>'' THEN 0 ELSE 1 END,
                    t.id LIMIT 1""", (_json(source_domains), kinds, blocked_sources, small_page_only, index_only,
                        os.environ.get("POLITICAL_HEAVY_PAUSED", "").lower() in {"1", "true", "yes"})).fetchone()
            if not row:
                return None
            # Finish/cancel transactions lock the job before its tasks and
            # source scheduling row. Taking those locks in reverse order here
            # deadlocked with discovery inserting the next page's candidates.
            # Wait for a busy job before acquiring any task/source row locks.
            # A short save transaction must not turn into the worker's full
            # empty-queue sleep while other fetch capacity remains available.
            job = conn.execute("""SELECT id FROM political_jobs WHERE id=%s
                AND status IN ('queued','running') FOR UPDATE""",
                               (row["job_id"],)).fetchone()
            if not job:
                return None
            row = conn.execute("""SELECT * FROM political_tasks WHERE id=%s
                AND (status IN ('queued','retryable') OR (status='running' AND leased_until<NOW()))
                AND (next_attempt_at IS NULL OR next_attempt_at<=NOW())
                FOR UPDATE SKIP LOCKED""", (row["id"],)).fetchone()
            if not row:
                return None
            token = uuid.uuid4().hex
            row = conn.execute("""UPDATE political_tasks SET status='running',attempts=attempts+1,
                lease_owner=%s,lease_token=%s,leased_until=NOW()+(%s*INTERVAL '1 second'),
                cursor=CASE WHEN kind='discovery' AND payload->>'strategy'='google_news'
                    THEN cursor || '{"google_batch_capacity":100}'::jsonb ELSE cursor END,
                request_domain=COALESCE(request_domain,%s),updated_at=NOW()
                WHERE id=%s RETURNING *""", (worker_id, token, lease_seconds,
                    task_request_domain(row["kind"], row["payload"], source_domains), row["id"])).fetchone()
            if kind == "discovery":
                conn.execute("""UPDATE political_source_leases SET task_id=%s,lease_token=%s,
                    discovery_claimed_at=NOW(),
                    leased_until=NOW()+(%s*INTERVAL '1 second') WHERE source_key=%s""",
                             (row["id"], token, lease_seconds, row["source_key"]))
            else:
                conn.execute("UPDATE political_source_leases SET fetch_claimed_at=NOW() WHERE source_key=%s",
                             (row["source_key"],))
            conn.execute("UPDATE political_jobs SET status='running',updated_at=NOW() WHERE id=%s", (row["job_id"],))
        return dict(row)

    def renew_lease(self, task: dict) -> bool:
        with self._connect() as conn:
            changed = conn.execute("""UPDATE political_tasks SET leased_until=NOW()+(%s*INTERVAL '1 second'),updated_at=NOW()
                WHERE id=%s AND lease_token=%s AND status='running' AND leased_until>NOW() RETURNING id""",
                                   (LEASE_SECONDS, task["id"], task["lease_token"])).fetchone()
            if changed and task["kind"] != "fetch":
                conn.execute("UPDATE political_source_leases SET leased_until=NOW()+(%s*INTERVAL '1 second') WHERE lease_token=%s",
                             (LEASE_SECONDS, task["lease_token"]))
        return bool(changed)

    def _lock_task(self, conn, task: dict) -> dict:
        job = conn.execute("SELECT * FROM political_jobs WHERE id=%s FOR UPDATE", (task["job_id"],)).fetchone()
        row = conn.execute("""SELECT * FROM political_tasks WHERE id=%s AND lease_token=%s
            AND status='running' AND leased_until>NOW() FOR UPDATE""", (task["id"], task["lease_token"])).fetchone()
        if not row or not job or job["status"] not in {"queued", "running"}:
            raise LeaseLost("political_task_lease_lost")
        return job

    def _finish(self, conn, task: dict, status: str, *, cursor: dict | None = None, result: dict | None = None,
                raw_count: int = 0, error_type: str = "", delay: int = 0) -> None:
        self._lock_task(conn, task)
        conn.execute("""UPDATE political_tasks SET status=%s,cursor=%s::jsonb,result=%s::jsonb,
            raw_count=raw_count+%s,error_type=%s,lease_owner=NULL,lease_token=NULL,leased_until=NULL,
            next_attempt_at=CASE WHEN %s>0 THEN NOW()+(%s*INTERVAL '1 second') ELSE NULL END,
            attempts=CASE WHEN %s='queued' THEN 0 ELSE attempts END,updated_at=NOW() WHERE id=%s""",
                     (status, _json(cursor if cursor is not None else task["cursor"]), _json(result or {}), raw_count,
                      error_type[:150], delay, delay, status, task["id"]))
        conn.execute("UPDATE political_source_leases SET leased_until=NULL,lease_token=NULL,task_id=NULL WHERE lease_token=%s",
                     (task["lease_token"],))
        self._refresh_job(conn, task["job_id"])

    @staticmethod
    def _refresh_job(conn, job_id: str) -> None:
        conn.execute("""UPDATE political_jobs j SET status=CASE
            WHEN EXISTS(SELECT 1 FROM political_tasks t WHERE t.job_id=j.id AND t.status IN ('queued','running','retryable')) THEN 'running'
            WHEN EXISTS(SELECT 1 FROM political_tasks t WHERE t.job_id=j.id AND t.status IN ('gap','failed')) THEN 'completed_with_gaps'
            ELSE 'succeeded' END,
            finished_at=CASE WHEN EXISTS(SELECT 1 FROM political_tasks t WHERE t.job_id=j.id AND t.status IN ('queued','running','retryable'))
                            THEN NULL ELSE NOW() END,updated_at=NOW()
            WHERE j.id=%s AND j.status<>'cancelled'""", (job_id,))

    def reserve_domain(self, domain: str) -> float:
        domain = normalize_domain(domain)
        interval = max([1.0] + [float(s.get("min_request_interval_seconds", 1)) for s in catalog_sources()
                              if domain in {normalize_domain(d) for d in [s.get("domain", ""), *s.get("domains", [])]}])
        with self._connect() as conn:
            conn.execute("INSERT INTO political_domain_limits(domain) VALUES (%s) ON CONFLICT DO NOTHING", (domain,))
            # Lock the same row updated by HTTP rate-limit responses before
            # reserving a normal 1rps slot. A cooldown does not grow this queue.
            conn.execute("SELECT domain FROM political_domain_limits WHERE domain=%s FOR UPDATE", (domain,))
            deadline = active_cooldown(conn, domain)
            if deadline:
                raise DomainCooldown(domain, deadline)
            row = conn.execute("""UPDATE political_domain_limits SET next_request_at=GREATEST(NOW(),next_request_at)+(%s*INTERVAL '1 second')
                WHERE domain=%s RETURNING EXTRACT(EPOCH FROM (next_request_at-NOW()-(%s*INTERVAL '1 second'))) AS wait_seconds""", (interval, domain, interval)).fetchone()
        return max(0.0, float(row["wait_seconds"]))

    def _check_domain_cooldown(self, domain: str) -> None:
        with self._connect() as conn:
            deadline = active_cooldown(conn, domain)
        if deadline:
            raise DomainCooldown(domain, deadline)

    @staticmethod
    def _public_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.port not in {None, 80, 443}:
            raise FetchProblem("invalid_article_url", retryable=False)
        try:
            addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
        except UnicodeError as exc:
            # A malformed publisher redirect can concatenate the article slug
            # into the hostname. Retrying cannot repair an invalid IDNA label.
            raise FetchProblem("invalid_article_hostname", retryable=False) from exc
        except OSError as exc:
            raise FetchProblem("dns_failed") from exc
        if not addresses or any(not ipaddress.ip_address(address[4][0]).is_global for address in addresses):
            raise FetchProblem("private_article_url", retryable=False)

    def fetch(self, url: str, **kwargs) -> requests.Response:
        large_sitemap = bool(kwargs.get("stream_sitemap"))
        stream_pdf = bool(kwargs.get("stream_pdf"))
        snapshot = str(kwargs.get("sitemap_snapshot") or "")
        cache = Path(os.environ.get("POLITICAL_SITEMAP_CACHE_DIR") or (Path(tempfile.gettempdir()) / "clipping-political-sitemaps"))
        if large_sitemap:
            # Only discovery opts into disk-backed XML; article responses keep the
            # original 8 MiB budget. Cursor snapshot names are content hashes.
            cache.mkdir(parents=True, exist_ok=True)
            if len(snapshot) == 64 and all(char in "0123456789abcdef" for char in snapshot):
                cached = cache / (snapshot + ".xml")
                if cached.is_file():
                    response = requests.Response()
                    response.status_code, response.url = 200, url
                    response._content = b""
                    response.sitemap_path, response.sitemap_snapshot = str(cached), snapshot
                    cached.touch()
                    return response
        current = url
        for _ in range(8):
            # A Google /sorry/ redirect is an access challenge, not a publisher
            # or a transient article response. Do not request/churn that page,
            # reset a shared cooldown indefinitely, or try to bypass it.
            if is_google_access_challenge(current):
                raise FetchProblem("google_access_challenge", retryable=False)
            if kwargs.get("allowed_hosts") and urlparse(current).hostname not in kwargs["allowed_hosts"]:
                raise FetchProblem("istoe_redirect_outside_portal", retryable=False)
            self._public_url(current)
            domain = normalize_domain(urlparse(current).hostname)
            wait = self.reserve_domain(domain)
            if wait:
                with timed_operation("throttle_wait"):
                    time.sleep(wait)
            # Another worker may have received 429 while this ordinary 1rps
            # reservation waited. Recheck before every actual redirected request.
            self._check_domain_cooldown(domain)
            session = getattr(self._http_local, "session", None)
            if session is None:
                session = self._http_local.session = requests.Session()
                session.headers["User-Agent"] = "ClippingProject/1.0 (+political-news-monitor)"
            method = str(kwargs.get("method") or "GET").upper()
            if method not in {"GET", "POST"}:
                raise FetchProblem("invalid_fetch_method", retryable=False)
            with timed_operation("http") as measurement:
                response = session.request(method, current, data=kwargs.get("data"), headers=kwargs.get("headers"),
                                           timeout=(8, 60 if large_sitemap else 20), allow_redirects=False, stream=True,
                                           verify=publisher_verify(current))
                measurement.status_code = response.status_code
            # Honor explicit Retry-After immediately. A headerless 503 needs
            # its body inspected: Google can return an automated-query block
            # here, which must not renew the default outage pause indefinitely.
            if response.status_code == 429 or (response.status_code == 503 and response.headers.get("Retry-After")):
                with self._connect() as conn:
                    record_response_cooldown(conn, domain, response.status_code, response.headers.get("Retry-After"))
            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")
                response.close()
                if not location:
                    raise FetchProblem("redirect_without_location", retryable=False)
                current = urljoin(current, location)
                continue
            if stream_pdf and response.status_code < 400:
                # The document processor streams to disk, checks its own byte
                # and time budgets, and closes this response. Never materialize
                # a full public edition inside the web/worker heap.
                return response
            chunks, size = [], 0
            started = time.monotonic()
            temporary = None
            try:
                if large_sitemap and response.status_code < 400:
                    digest = hashlib.sha256()
                    with tempfile.NamedTemporaryFile(dir=cache, mode="wb", delete=False) as output:
                        temporary = output.name
                        for chunk in response.iter_content(65536):
                            size += len(chunk)
                            if size > MAX_SITEMAP_RESPONSE_BYTES or time.monotonic() - started > MAX_SITEMAP_RESPONSE_SECONDS:
                                raise FetchProblem("sitemap_download_budget_exceeded", retryable=False)
                            digest.update(chunk)
                            output.write(chunk)
                        output.flush()
                        os.fsync(output.fileno())
                    snapshot = digest.hexdigest()
                    cached = cache / (snapshot + ".xml")
                    os.replace(temporary, cached)
                    temporary = None
                    response.sitemap_path, response.sitemap_snapshot = str(cached), snapshot
                    response.sitemap_bytes = size
                    # Cache is reconstructible, capped on disk as well as in RAM.
                    entries = sorted(cache.glob("*.xml"), key=lambda item: item.stat().st_mtime, reverse=True)
                    for expired in entries[4:]:
                        if expired != cached:
                            expired.unlink(missing_ok=True)
                            Path(str(expired) + ".entries.jsonl").unlink(missing_ok=True)
                else:
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > MAX_RESPONSE_BYTES or time.monotonic() - started > 35:
                            raise FetchProblem("response_budget_exceeded")
                        chunks.append(chunk)
            finally:
                response.close()
                if temporary:
                    Path(temporary).unlink(missing_ok=True)
                record_timing("http_body", time.monotonic() - started, status_code=response.status_code)
            response._content = b"".join(chunks)
            response._content_consumed = True
            if is_google_block_response(current, response.status_code, response.content):
                raise FetchProblem("google_access_challenge", retryable=False)
            if response.status_code == 503 and not response.headers.get("Retry-After"):
                with self._connect() as conn:
                    record_response_cooldown(conn, domain, response.status_code, None)
            if "text/html" in response.headers.get("Content-Type", "").lower() and "charset=" not in response.headers.get("Content-Type", "").lower():
                declared = requests.utils.get_encodings_from_content(response.content[:8192].decode("ascii", errors="ignore"))
                if declared:
                    response.encoding = declared[0]
                else:
                    try:
                        response.content.decode("utf-8")
                    except UnicodeDecodeError:
                        pass
                    else:
                        response.encoding = "utf-8"
            return response
        raise FetchProblem("redirect_limit", retryable=False)

    def _store_text(self, body: str) -> tuple[str, str]:
        if not body:
            return "", ""
        raw = body.encode("utf-8")
        if len(raw) > MAX_RESPONSE_BYTES:
            raise FetchProblem("body_too_large", retryable=False)
        digest = hashlib.sha256(raw).hexdigest()
        key = f"{self.store.prefix}/political/objects/{digest[:2]}/{digest}.txt.gz"
        with timed_operation("object_upload"):
            if not self.store.enabled or not self.store.upload_bytes(gzip.compress(raw, mtime=0), key, "application/gzip"):
                raise FetchProblem("body_storage_failed")
        return digest, key

    def _store_html(self, raw_html: str) -> tuple[str, str]:
        raw = raw_html.encode("utf-8")
        if len(raw) > MAX_RESPONSE_BYTES:
            raise FetchProblem("html_too_large", retryable=False)
        digest = hashlib.sha256(raw).hexdigest()
        key = f"{self.store.prefix}/political/objects/{digest[:2]}/{digest}.html.gz"
        with timed_operation("object_upload"):
            if not self.store.enabled or not self.store.upload_bytes(gzip.compress(raw, mtime=0), key, "application/gzip"):
                raise FetchProblem("html_storage_failed")
        return digest, key

    def _store_date_response(self, raw: bytes) -> tuple[str, str]:
        if len(raw) > 512 * 1024:
            raise FetchProblem("date_evidence_too_large", retryable=False)
        digest = hashlib.sha256(raw).hexdigest()
        key = f"{self.store.prefix}/political/objects/{digest[:2]}/{digest}.dates.json.gz"
        with timed_operation("object_upload"):
            if not self.store.enabled or not self.store.upload_bytes(gzip.compress(raw, mtime=0), key, "application/gzip"):
                raise FetchProblem("date_evidence_storage_failed")
        return digest, key

    def _store_discovery_response(self, raw: bytes) -> tuple[str, str]:
        if len(raw) > MAX_RESPONSE_BYTES:
            raise FetchProblem("discovery_evidence_too_large", retryable=False)
        digest = hashlib.sha256(raw).hexdigest()
        key = f"{self.store.prefix}/political/objects/{digest[:2]}/{digest}.discovery.gz"
        with timed_operation("object_upload"):
            if not self.store.enabled or not self.store.upload_bytes(gzip.compress(raw, mtime=0), key, "application/gzip"):
                raise FetchProblem("discovery_evidence_storage_failed")
        return digest, key

    def _record_access_failure(self, task: dict, response) -> None:
        """Keep bounded access evidence without letting its storage stop the job."""
        evidence = {"status": response.status_code, "url": response.url,
                    "at": datetime.now(timezone.utc).isoformat(),
                    "environment": os.environ.get("RENDER_SERVICE_ID", "local"),
                    "content_type": response.headers.get("Content-Type", ""),
                    "retry_after": response.headers.get("Retry-After", "")}
        body = response.text[:65536]
        evidence["kind"] = "challenge" if re.search(r"cf-chl|challenge-platform|Just a moment|sucuri_cloudproxy_js", body, re.I) else "http_refusal"
        try:
            digest, key = self._store_html(body)
            evidence.update(html_hash=digest, html_object_key=key)
        except Exception as exc:
            evidence["evidence_storage_error"] = type(exc).__name__
        with self._connect() as conn:
            self._lock_task(conn, task)
            conn.execute("UPDATE political_observations SET metadata=metadata || %s::jsonb WHERE job_id=%s AND observed_url=%s",
                         (_json({"access_failure": evidence}), task["job_id"], task["payload"]["url"]))

    def process_task(self, task: dict) -> dict:
        try:
            if task["kind"] == "discovery":
                return self._discover(task)
            if task["kind"] == "review":
                return self._review(task)
            if task["payload"].get("document_task"):
                return self.process_document_task(task)
            return self._fetch_article(task)
        except LeaseLost:
            return {"taskId": task["id"], "status": "lease_lost"}
        except Exception as exc:
            deferred = domain_deferral(exc)
            if deferred:
                try:
                    with self._connect() as conn:
                        self._finish(conn, task, "retryable", error_type="domain_cooldown",
                            result={"deferredDomain": deferred.domain, "retryAt": deferred.retry_at.isoformat()})
                        conn.execute("""UPDATE political_tasks SET attempts=GREATEST(0,attempts-1),
                            request_domain=%s,next_attempt_at=%s WHERE id=%s""",
                            (deferred.domain, deferred.retry_at, task["id"]))
                except LeaseLost:
                    return {"taskId": task["id"], "status": "lease_lost"}
                return {"taskId": task["id"], "status": "deferred", "errorType": "domain_cooldown",
                        "domain": deferred.domain, "retryAt": deferred.retry_at.isoformat()}
            retryable = bool(getattr(exc, "retryable", True))
            delay = max(int(getattr(exc, "retry_after", 0) or 0), min(3600, 15 * 2 ** min(8, int(task["attempts"]) - 1)))
            status = "retryable" if retryable and int(task["attempts"]) < int(task["max_attempts"]) else "gap"
            error_type = str(exc) if isinstance(exc, (FetchProblem, DocumentProblem)) else type(exc).__name__
            if not isinstance(exc, FetchProblem) and hasattr(exc, "status_code"):
                error_type = f"{type(exc).__name__}:http_{int(getattr(exc, 'status_code', 0) or 0)}"
                safe_detail = str(exc)
                if safe_detail in {"malformed XML response", "sitemap byte limit reached", "expanded sitemap byte limit reached", "unsupported XML entity declaration"}:
                    error_type = safe_detail.replace(" ", "_").lower()
                cause = exc.__cause__
                for _ in range(5):
                    if cause is None:
                        break
                    if isinstance(cause, FetchProblem) and str(cause) == "google_access_challenge":
                        error_type = "google_access_challenge"
                        break
                    cause = cause.__cause__
            if task["kind"] == "fetch" and not task["payload"].get("document_task") and not getattr(exc, "metadata_handled", False):
                try:
                    with self._connect() as conn:
                        job = conn.execute("SELECT * FROM political_jobs WHERE id=%s", (task["job_id"],)).fetchone()
                    self._save_metadata_attempt(task, job, task.get("_verified_candidate") or task["payload"],
                        FetchProblem(error_type), date_status=task.get("_verified_date_status") or "")
                except LeaseLost:
                    return {"taskId": task["id"], "status": "lease_lost"}
            if task.get("_metadata_date_conflict"):
                status, error_type = "gap", "publication_date_conflict"
            with self._connect() as conn:
                if task["kind"] == "discovery" and status == "gap":
                    self._enqueue_discovery_fallback(conn, task)
                self._finish(conn, task, status, error_type=error_type, delay=delay if status == "retryable" else 0)
            return {"taskId": task["id"], "status": status, "errorType": error_type}

    def _enqueue_discovery_fallback(self, conn, task: dict) -> None:
        from .political_discovery import fallback_tasks
        job = self._lock_task(conn, task)
        discovery_keys = (job.get("metadata") or {}).get("discovery_target_keys", job["target_keys"])
        if task["payload"].get("strategy") == "recover":
            return
        for child in fallback_tasks(task["payload"], [s for s in job["target_snapshots"] if s["key"] in discovery_keys]):
            self._insert_task(conn, task["job_id"], "discovery", {**child,
                **({"source_snapshot": task["payload"]["source_snapshot"]} if task["payload"].get("source_snapshot") else {})})

    def _checkpoint_fetch(self, task: dict, changes: dict) -> None:
        """Commit retry state under the live lease before additional network I/O."""
        cursor = {**task["cursor"], **changes}
        with self._connect() as conn:
            self._lock_task(conn, task)
            conn.execute("UPDATE political_tasks SET cursor=%s::jsonb,updated_at=NOW() WHERE id=%s",
                         (_json(cursor), task["id"]))
            if changes.get("resolved_url"):
                conn.execute("UPDATE political_tasks SET request_domain=%s WHERE id=%s",
                             (urlparse(changes["resolved_url"]).hostname, task["id"]))
                conn.execute("""INSERT INTO political_resolved_urls(original_url,resolved_url) VALUES(%s,%s)
                    ON CONFLICT(original_url) DO UPDATE SET resolved_url=EXCLUDED.resolved_url,resolved_at=NOW()""",
                    (task["payload"]["url"], changes["resolved_url"]))
        task["cursor"] = cursor
        if changes.get("resolved_url"):
            set_publisher_source(_confirmed_publisher(task["payload"], changes["resolved_url"])["source_key"])
            task["_verified_candidate"] = {**_confirmed_publisher(task["payload"], changes["resolved_url"]),
                "url": changes["resolved_url"], "observed_url": task["payload"]["url"]}

    def _discover(self, task: dict) -> dict:
        from .political_discovery import discover
        known_index = _known_sitemap_index(task["payload"], task["cursor"])
        if not known_index:
            with self._connect() as conn:
                stop_discovery, blocked_sources = self._discovery_backpressure(conn)
            if stop_discovery or task["source_key"] in blocked_sources:
                with self._connect() as conn:
                    self._finish(conn, task, "queued", delay=15)
                return {"taskId": task["id"], "status": "backpressure"}
        payload = {**task["payload"], "cursor": task["cursor"]}
        sitemap_cache = None
        istoe_inventory = None
        discovery_fetch = self.fetch
        if payload.get("strategy") == "istoe_direct_v1":
            from .political_istoe_inventory import InventoryTransport
            istoe_inventory = InventoryTransport(self, task)
            discovery_fetch = istoe_inventory.fetch
        if payload.get("strategy") in {"expanded_sitemap", "expanded_daily_sitemap"}:
            from .political_sitemap_cache import PaginatedSitemapCache
            sitemap_cache = PaginatedSitemapCache(self.fetch, task["cursor"],
                save_object=self._store_discovery_response, read_object=self._read_discovery_response)
            discovery_fetch = sitemap_cache.fetch
        if payload.get("strategy") == "google_news" and task["cursor"].get("google_pending_result"):
            result = task["cursor"]["google_pending_result"]
        else:
            result = self._recover_discovery(task, source_for_task(payload)) if payload.get("strategy") == "recover" else discover(payload, discovery_fetch)
        if sitemap_cache and result.get("next_cursor"):
            result["next_cursor"] = sitemap_cache.checkpoint(result["next_cursor"])
        if istoe_inventory:
            result["next_cursor"] = istoe_inventory.checkpoint(result.get("next_cursor"))
        if payload.get("strategy") == "expanded_congresso_archive":
            # Preserve real listing evidence before committing candidates/cursor.
            # A failed upload leaves the task resumable at the same page.
            raw = result.pop("archive_response")
            digest, object_key = self._store_discovery_response(raw)
            proof = result["publisher_archive"]
            if digest != proof["responseHash"]:
                raise FetchProblem("archive_evidence_hash_mismatch", retryable=False)
            receipts = list(task["cursor"].get("archive_receipts") or [])
            receipts.append({**proof, "objectKey": object_key})
            result["publisher_archive"] = {**proof, "receipts": receipts}
            if result.get("next_cursor"):
                result["next_cursor"]["archive_receipts"] = receipts
        candidates = result.get("candidates") or []
        if known_index and candidates:
            raise FetchProblem("sitemap_index_emitted_article_candidates", retryable=False)
        if len(candidates) > 500:
            raise FetchProblem("discovery_page_too_large", retryable=False)
        if payload.get("strategy") == "expanded_blogger_feed" and len(candidates) > 100:
            raise FetchProblem("atom_discovery_page_too_large", retryable=False)
        if payload.get("strategy") == "google_news":
            result = _page_google_result(result)
            candidates = result.get("candidates") or []
        outcome = str(result.get("outcome") or "gap")
        if outcome not in {"complete", "continue", "split", "gap"}:
            raise ValueError("invalid_discovery_outcome")
        batch_refs, batch_fallback = {}, str(result.get("body_batch_fallback") or "")
        if batch_fallback:
            record_timing("body_batch_fallback", 0, outcome="error")
        if result.get("body_batch"):
            try:
                for reference in self._body_batches.store_batch(result["body_batch"]):
                    batch_refs[reference["post_id"]] = reference
            except BatchBodyUnavailable as exc:
                # A body-cache optimization must never discard discovered URLs
                # or prevent healthy sources from continuing after storage trouble.
                batch_fallback = str(exc)
                record_timing("body_batch_fallback", 0, outcome="error")
        date_api_facts, date_api_stats = {}, {}
        if payload.get("strategy") == "expanded_sitemap" and candidates:
            from .political_public_date_batches import ENDPOINTS, lookup
            if task["source_key"] in ENDPOINTS:
                with self._connect() as conn:
                    prior_dates, prior_articles = self._discovery_publication_state(conn, candidates)
                # Never supersede saved articles, human date corrections, or
                # already verified facts. Look up only newly encountered URLs.
                unresolved = [{**c, "url": canonicalize_url(c.get("url", ""))} for c in candidates if canonicalize_url(c.get("url", "")) not in prior_dates
                              and canonicalize_url(c.get("url", "")) not in prior_articles]
                def fetch_date_metadata(url):
                    with timed_operation("publication_date_batch_http") as measurement:
                        response = self.fetch(url)
                        measurement.status_code = response.status_code
                        measurement.outcome = "error" if response.status_code >= 400 else "ok"
                        return response
                date_api_facts, date_api_stats = lookup(task["source_key"], unresolved, fetch_date_metadata, self._store_date_response)
                record_timing("publication_date_batch", date_api_stats["durationMs"] / 1000,
                              outcome="fallback" if date_api_stats["fallback"] else "ok")
        with self._connect() as conn:
            job = self._lock_task(conn, task)
            if istoe_inventory:
                from .political_istoe_inventory import record_urls
                record_urls(conn, candidates)
            known_dates, current_articles = self._discovery_publication_state(conn, candidates) if job["kind"] == "collect" else ({}, set())
            dates_reused = dates_from_api = 0
            for candidate in candidates:
                url = canonicalize_url(str(candidate.get("url") or ""))
                if not url or urlparse(url).scheme not in {"http", "https"}:
                    continue
                candidate = {**candidate, "url": url, "source_key": task["source_key"]}
                if payload.get("source_snapshot"):
                    candidate["source_snapshot"] = payload["source_snapshot"]
                if candidate.get("document_type") == "edition_pdf":
                    self.enqueue_document_candidate(conn, task["job_id"], candidate)
                    continue
                reference = batch_refs.get((candidate.get("metadata") or {}).get("publisher_post_id", (candidate.get("metadata") or {}).get("wordpress_id")))
                if reference:
                    candidate["body_batch_ref"] = reference
                elif batch_fallback:
                    candidate["metadata"] = {**(candidate.get("metadata") or {}), "body_batch_fallback": batch_fallback}
                api_date = (date_api_facts.get(url) if url not in known_dates and url not in current_articles else None)
                if api_date:
                    candidate["published_at"] = api_date[0].isoformat()
                    candidate["metadata"] = {**(candidate.get("metadata") or {}),
                        **self._publication_fact(*api_date),
                        "wordpress_id": api_date[2]["publisher_post_id"],
                        "public_date_batch_evidence": api_date[2]}
                conn.execute("""INSERT INTO political_observations(job_id,source_task_id,observed_url,source_key,title,snippet,metadata)
                    VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb) ON CONFLICT(job_id,observed_url) DO NOTHING""",
                             (task["job_id"], task["id"], url, task["source_key"], str(candidate.get("title") or "")[:1000],
                              str(candidate.get("snippet") or "")[:2000], _json(candidate.get("metadata") or {})))
                known_date = known_dates.get(url) or api_date
                if (not candidate.get("force_refresh") and known_date and known_date[0] and not job["date_from"] <=
                        known_date[0].astimezone(ZONE).date() <= job["date_to"]):
                    # Retain discovery evidence, but avoid creating a fetch task
                    # whose existing first action would reject this verified date.
                    # Unknown/reported dates and prior no-match results never
                    # exclude a URL through this optimization.
                    changed = conn.execute("""UPDATE political_observations
                        SET disposition='outside_window',metadata=metadata || %s::jsonb
                        WHERE job_id=%s AND observed_url=%s AND disposition='pending' AND article_id IS NULL""",
                        (_json({**self._publication_fact(*known_date),
                                **({"date_verified_in_public_api_batch": True} if api_date else {"date_reused_in_discovery": True})}),
                         task["job_id"], url))
                    if api_date:
                        dates_from_api += changed.rowcount
                    else:
                        dates_reused += changed.rowcount
                    continue
                if candidate.get("istoe_defer_body") and url not in current_articles and not known_date:
                    conn.execute("""UPDATE political_observations SET disposition='deferred_date'
                        WHERE job_id=%s AND observed_url=%s AND disposition='pending'""", (task["job_id"],url))
                    continue
                self._insert_task(conn, task["job_id"], "fetch", candidate)
            if istoe_inventory and outcome == "gap" and result.get("gap_reason") == "istoe_unverified_older_urls":
                unresolved = conn.execute("SELECT COUNT(*) AS n FROM political_observations WHERE source_task_id=%s AND disposition='deferred_date'", (task['id'],)).fetchone()['n']
                if not unresolved:
                    outcome = "complete"
                    result['gap_reason'] = ""
            for child in result.get("child_tasks") or []:
                self._insert_task(conn, task["job_id"], "discovery", {**child,
                    **({"source_snapshot": payload["source_snapshot"]} if payload.get("source_snapshot") else {})})
            if outcome == "gap":
                self._enqueue_discovery_fallback(conn, task)
            calendar_pruned = []
            if result.get("calendar_partition_excluded"):
                # Old workers queued entire obsolete calendar years. Finish
                # at most 100 never-started siblings under the same job lock,
                # retaining a separate proof on every task. Do not touch live
                # leases, retries, other sources/jobs or already scanned pages.
                from .political_expanded_discovery import calendar_exclusion
                siblings = conn.execute("""SELECT id,payload FROM political_tasks
                    WHERE job_id=%s AND source_key=%s AND kind='discovery'
                    AND status='queued' AND attempts=0 AND payload->>'strategy'='expanded_sitemap'
                    ORDER BY id LIMIT 100 FOR UPDATE SKIP LOCKED""", (task["job_id"],task["source_key"])).fetchall()
                for sibling in siblings:
                    proof = calendar_exclusion(sibling["payload"], source_for_task(sibling["payload"]))
                    if proof:
                        conn.execute("""UPDATE political_tasks SET status='complete',updated_at=NOW(),
                            result=result || %s::jsonb WHERE id=%s""",
                            (_json({"calendarPartitionExcluded":proof,"calendarPrunedByTask":task["id"]}),sibling["id"]))
                        calendar_pruned.append(sibling["id"])
            self._finish(conn, task, "queued" if outcome == "continue" else outcome,
                         cursor=result.get("next_cursor") or task["cursor"], raw_count=int(result.get("raw_count") or 0),
                         error_type=str(result.get("gap_reason") or ""),
                         result={"istoeInventory": result.get("istoe_inventory"),
                                 "istoeSnapshotReused": bool(istoe_inventory and istoe_inventory.reused),
                                 "bodyBatchRecords": len(batch_refs), "bodyBatchFallback": batch_fallback,
                                 "datesReusedBeforeFetch": dates_reused,
                                 "publicDateBatch": {**date_api_stats, "excludedBeforeFetch": dates_from_api} if date_api_stats else {},
                                 "calendarSiblingsPruned": calendar_pruned,
                                 "structuralIndexExcluded": result.get("structural_index_excluded"),
                                 "publisherSearch": result.get("publisher_search"),
                                 "publisherArchive": result.get("publisher_archive"),
                                 "calendarPartitionExcluded": result.get("calendar_partition_excluded")})
        return {"taskId": task["id"], "status": outcome, "candidates": len(candidates),
                "datesReusedBeforeFetch": dates_reused, "publicAPIDatesBeforeFetch": dates_from_api}

    @staticmethod
    def _discovery_verified_dates(conn, candidates: list[dict]) -> dict:
        return PoliticalCorpusService._discovery_publication_state(conn, candidates)[0]

    @staticmethod
    def _discovery_publication_state(conn, candidates: list[dict]) -> tuple[dict, set]:
        """Batch the same conservative date evidence used by article fetching.

        At most 500 current candidates are inspected. This does not scan or
        revise the archive, infer publication from lastmod, or cache no-match.
        Google wrappers still resolve through their normal fetch path.
        """
        from .political_discovery import is_google_intermediary
        from .political_jota_extraction import original_date_trusted
        variants_to_urls: dict[str, set[str]] = {}
        candidate_urls: set[str] = set()
        for candidate in candidates:
            url = canonicalize_url(str(candidate.get("url") or ""))
            if (not url or urlparse(url).scheme not in {"http", "https"}
                    or candidate.get("force_refresh") or candidate.get("document_type")
                    or is_google_intermediary(url)):
                continue
            candidate_urls.add(url)
            for variant in publisher_article_identity_urls(url):
                variants_to_urls.setdefault(variant, set()).add(url)
        if not candidate_urls:
            return {}, set()
        variants = list(variants_to_urls)
        rows = conn.execute("""SELECT a.id,a.canonical_url,a.published_at,a.date_status,a.metadata,
            ARRAY(SELECT u.url FROM political_url_aliases u WHERE u.article_id=a.id AND u.url=ANY(%s)) AS matched_aliases
            FROM political_articles a WHERE a.canonical_url=ANY(%s) OR EXISTS (
                SELECT 1 FROM political_url_aliases u WHERE u.article_id=a.id AND u.url=ANY(%s))
            ORDER BY a.body_chars DESC,a.id""", (variants, variants, variants)).fetchall()
        existing, known = set(), {}
        for row in rows:
            urls = set(variants_to_urls.get(row["canonical_url"], ()))
            for alias in row["matched_aliases"]:
                urls.update(variants_to_urls[alias])
            for url in urls - existing:
                existing.add(url)
                if row["date_status"] in {"page_verified", "api_verified"} and original_date_trusted(url,row["metadata"]):
                    known[url] = (row["published_at"], row["date_status"], row["metadata"].get("publication_date_evidence"))
        unresolved = list(candidate_urls - existing)
        if unresolved:
            facts = conn.execute("""SELECT DISTINCT ON (observed_url) observed_url,metadata
                FROM political_observations WHERE observed_url=ANY(%s)
                AND metadata ? 'verified_publication_at' ORDER BY observed_url,id DESC""", (unresolved,)).fetchall()
            for row in facts:
                metadata = row["metadata"]
                if metadata.get("publication_date_status") in {"page_verified", "api_verified"} and original_date_trusted(row["observed_url"],metadata):
                    known[row["observed_url"]] = (parse_date(metadata["verified_publication_at"]), metadata["publication_date_status"], metadata.get("publication_date_evidence"))
        return known, existing

    @staticmethod
    def _publication_fact(published, date_status: str, date_evidence=None) -> dict:
        if not published or date_status not in {"page_verified", "api_verified"}:
            return {}
        return {"verified_publication_at": published.isoformat(), "publication_date_status": date_status,
                **({"publication_date_evidence":date_evidence} if date_evidence else {})}

    def _finish_fetch_outside_window(self, task: dict, *, published=None, date_status="", reused_date=False) -> dict:
        with self._connect() as conn:
            job = self._lock_task(conn, task)
            # A prior failed attempt may have saved the feed's inaccurate date.
            # Correct a non-legacy record encountered by this job, retaining
            # content, associations, classifications and its previous metadata.
            if published and date_status in {"page_verified", "api_verified"}:
                previous = conn.execute("""SELECT a.* FROM political_articles a
                    WHERE a.id=COALESCE((SELECT o.article_id FROM political_observations o
                        WHERE o.job_id=%s AND o.observed_url=%s),%s)
                    AND a.legacy_id IS NULL AND EXISTS(SELECT 1 FROM political_mentions m
                        WHERE m.article_id=a.id AND m.target_key=ANY(%s))
                    FOR UPDATE OF a""", (task["job_id"], task["payload"]["url"],
                                         task.get("_undated_existing_article_id"), job["target_keys"])).fetchone()
                if previous and (previous["published_at"] != published or previous["date_status"] != date_status):
                    conn.execute("INSERT INTO political_article_revisions(article_id,previous,reason) VALUES(%s,%s::jsonb,'publication_date_verification')",
                                 (previous["id"], _json(dict(previous))))
                    conn.execute("UPDATE political_articles SET published_at=%s,date_status=%s,metadata=metadata || %s::jsonb WHERE id=%s",
                                 (published,date_status,_json(task.get("_date_probe_evidence") or {}),previous["id"]))
            date_evidence = ((task.get("_verified_candidate") or {}).get("metadata") or {}).get("publication_date_evidence") or task.get("_known_date_evidence")
            conn.execute("UPDATE political_observations SET disposition='outside_window',article_id=NULL,metadata=metadata || %s::jsonb WHERE job_id=%s AND observed_url=%s",
                         (_json({**self._publication_fact(published, date_status),
                                 **({"publication_date_evidence":date_evidence} if date_evidence else {})}), task["job_id"], task["payload"]["url"]))
            self._finish(conn, task, "complete", result={"disposition": "outside_window", "dateReused": reused_date})
        return {"taskId": task["id"], "status": "outside_window"}

    def _finish_fetch_not_news(self, task: dict, url: str, *, title: str | None = None) -> dict:
        result = {"disposition": "not_news", "reason": non_news_reason(url, title if title is not None else task["payload"].get("title", "")),
                  "recordKind": "candidate_profile", "resolvedUrl": canonicalize_url(url)}
        with self._connect() as conn:
            self._lock_task(conn, task)
            conn.execute("""UPDATE political_observations SET disposition='not_news',article_id=NULL,
                metadata=metadata || %s::jsonb WHERE job_id=%s AND observed_url=%s""",
                (_json({"non_news": result}), task["job_id"], task["payload"]["url"]))
            self._finish(conn, task, "complete", result=result)
        return {"taskId": task["id"], "status": "not_news", "reason": result["reason"]}

    @staticmethod
    def _find_article(conn, url: str) -> dict | None:
        variants = list(publisher_article_identity_urls(canonicalize_url(url)))
        return conn.execute("""SELECT a.* FROM political_articles a
            WHERE a.canonical_url=ANY(%s) OR EXISTS (
                SELECT 1 FROM political_url_aliases u WHERE u.article_id=a.id AND u.url=ANY(%s))
            ORDER BY a.body_chars DESC,a.id LIMIT 1""", (variants, variants)).fetchone()

    def _probe_saved_publication(self, task: dict, url: str):
        from .political_discovery import extract_article
        deferred = False
        try:
            response = self.fetch(publisher_article_request_url(url))
        except DomainCooldown:
            deferred = True
            raise
        finally:
            if not deferred:
                with self._connect() as conn:
                    self._lock_task(conn, task)
                    conn.execute("UPDATE political_jobs SET fetch_attempted=fetch_attempted+1 WHERE id=%s", (task["job_id"],))
        if response.status_code >= 400:
            self._record_access_failure(task, response)
            deadline = retry_after_deadline(response.headers.get("Retry-After"))
            raise FetchProblem(f"http_{response.status_code}",
                retryable=response.status_code in {408,425,429} or response.status_code >= 500,
                status_code=response.status_code, retry_after=remaining_seconds(deadline) if deadline else 0)
        if is_publisher_access_challenge(response.url, response.text):
            self._record_access_failure(task, response)
            raise FetchProblem("publisher_access_challenge", retryable=False)
        # A home page redirect cannot establish this article's publication.
        if canonicalize_url(response.url).rstrip("/") not in {
                v.rstrip("/") for v in publisher_article_identity_urls(url)}:
            return None
        with timed_operation("publication_date_probe"):
            extracted = extract_article(response.text, url)
        canonical = canonicalize_url(str(extracted.get("canonical_url") or ""))
        if canonical and canonical.rstrip("/") not in {v.rstrip("/") for v in publisher_article_identity_urls(url)}:
            return None
        published = parse_date(extracted.get("published_at"))
        if not published:
            return None
        digest, key = self._store_html(response.text)
        return published, {"url": response.url, "published_at": published.isoformat(),
            "html_hash": digest, "html_object_key": key,
            "at": datetime.now(timezone.utc).isoformat(), "body_reused": True}

    def _fetch_article(self, task: dict) -> dict:
        from .political_discovery import extract_article, is_google_intermediary
        from .political_jota_extraction import original_date_trusted
        candidate = task["payload"]
        def article_fetch(url, **kwargs):
            if task["source_key"] == "istoe":
                kwargs["allowed_hosts"] = ("istoe.com.br", "www.istoe.com.br")
            return self.fetch(url, **kwargs)
        fetch_url = (task["cursor"].get("publisher_alternative_url") if task["source_key"] == "congresso_em_foco" else None) or task["cursor"].get("resolved_url") or candidate["url"]
        if (task["source_key"] == "congresso_em_foco" and task["cursor"].get("empty_body_responses")
                and not task["cursor"].get("publisher_alternative_url")
                and urlparse(fetch_url).hostname == "www.congressoemfoco.com.br"
                and re.fullmatch(r"/(?:noticia|artigo|coluna|informativo)/\d+/[^/?]+", urlparse(fetch_url).path)):
            # Use the next permitted attempt on the public alternate edition,
            # instead of requesting the same empty primary page again.
            changes = {"publisher_alternative_url": "https://www.congressoemfoco.com.br/amp" + urlparse(fetch_url).path,
                "publisher_alternative_original_url": canonicalize_url(fetch_url),
                "publisher_alternative_reason": "primary_empty_editorial_body"}
            with self._connect() as conn:
                observation = conn.execute("SELECT metadata FROM political_observations WHERE job_id=%s AND observed_url=%s",
                    (task["job_id"], candidate["url"])).fetchone()
            metadata = (observation or {}).get("metadata") or {}
            if metadata.get("html_object_key") and metadata.get("html_hash"):
                previous = extract_article(self._read_text(metadata["html_object_key"], metadata["html_hash"]), fetch_url)
                if (previous.get("published_at") and canonicalize_url(previous.get("canonical_url") or "") == canonicalize_url(fetch_url)):
                    changes.update(publisher_alternative_primary_date=previous["published_at"],
                        publisher_alternative_primary_html_key=metadata["html_object_key"],
                        publisher_alternative_primary_html_hash=metadata["html_hash"])
            self._checkpoint_fetch(task, changes)
            fetch_url = changes["publisher_alternative_url"]
        if is_google_intermediary(fetch_url):
            with self._connect() as conn:
                resolved = conn.execute("SELECT resolved_url FROM political_resolved_urls WHERE original_url=%s", (fetch_url,)).fetchone()
            if resolved:
                self._checkpoint_fetch(task, {"resolved_url": resolved["resolved_url"]})
                fetch_url = resolved["resolved_url"]
        if not is_google_intermediary(fetch_url):
            set_publisher_source(_confirmed_publisher(candidate, fetch_url)["source_key"])
        if task['source_key'] == 'istoe':
            from .political_istoe_discovery import allowed
            if not allowed(fetch_url):
                raise FetchProblem('istoe_direct_url_required', retryable=False)
        force_refresh = bool(candidate.get("force_refresh"))
        if non_news_reason(candidate["url"], candidate.get("title", "")):
            return self._finish_fetch_not_news(task, candidate["url"])
        with self._connect() as conn:
            job = conn.execute("SELECT * FROM political_jobs WHERE id=%s", (task["job_id"],)).fetchone()
            existing = self._find_article(conn, fetch_url)
            if existing and not original_date_trusted(fetch_url,existing.get("metadata")):
                force_refresh = True
                task["_undated_existing_article_id"] = existing["id"]
            if (existing and existing["published_at"] is None and existing["legacy_id"] is None
                    and not existing["source_key"].startswith(("manual", "legacy"))):
                task["_undated_existing_article_id"] = existing["id"]
            if not existing and job["kind"] == "recover" and candidate.get("recover_partial_text"):
                # Older Google metadata may not yet have a publisher URL alias.
                # The frozen recovery reference still identifies its retained
                # body, which must participate in the no-degradation check.
                recovery_article = ((candidate.get("metadata") or {}).get("recovery") or {}).get("article_id")
                if recovery_article:
                    existing = conn.execute("""SELECT a.* FROM political_articles a WHERE a.id=%s AND EXISTS
                        (SELECT 1 FROM political_mentions m WHERE m.article_id=a.id AND m.target_key=ANY(%s))""",
                        (recovery_article, job["target_keys"])).fetchone()
            known_date = None
            if not force_refresh:
                if existing and existing["date_status"] in {"page_verified", "api_verified"} and original_date_trusted(fetch_url,existing.get("metadata")):
                    known_date = (existing["published_at"], existing["date_status"])
                    task["_known_date_evidence"] = existing["metadata"].get("publication_date_evidence")
                elif not existing:
                    fact = conn.execute("""SELECT metadata FROM political_observations
                        WHERE observed_url=%s AND metadata ? 'verified_publication_at'
                        ORDER BY id DESC LIMIT 1""", (candidate["url"],)).fetchone()
                    if fact and fact["metadata"].get("publication_date_status") in {"page_verified", "api_verified"} and original_date_trusted(fetch_url,fact["metadata"]):
                        known_date = (parse_date(fact["metadata"]["verified_publication_at"]), fact["metadata"]["publication_date_status"])
                        task["_known_date_evidence"] = fact["metadata"].get("publication_date_evidence")
        # Reuse only verified publication dates to reject a different period.
        # A prior no_match result is never evidence against newly selected people.
        if known_date and known_date[0] and not job["date_from"] <= known_date[0].astimezone(ZONE).date() <= job["date_to"]:
            return self._finish_fetch_outside_window(task, published=known_date[0], date_status=known_date[1], reused_date=True)
        if existing and non_news_reason(existing["canonical_url"], existing["title"]):
            return self._finish_fetch_not_news(task, existing["canonical_url"], title=existing["title"])
        body, final_url, title = "", fetch_url, str(candidate.get("title") or "")
        published = parse_date(candidate.get("published_at"))
        date_status = ("api_verified" if (candidate.get("metadata") or {}).get("wordpress_id") is not None else "source_reported") if published else "unknown"
        digest = key = ""
        html_hash = html_key = ""
        recover_partial = bool(job["kind"] == "recover" and candidate.get("recover_partial_text") and existing
            and existing["text_object_key"] and (existing.get("metadata") or {}).get("text_extent") == "partial")
        use_saved_body = bool(existing and existing["text_object_key"] and existing["body_status"] == "body_extracted"
                              and not force_refresh and not recover_partial and existing["source_key"] != "google_news")
        batch_body, batch_fallback, body_origin = None, "", "publisher_page"
        historical = None
        if (candidate.get("body_batch_ref") and not use_saved_body and not force_refresh
                and not (recover_partial and task["cursor"].get("recovery_batch_used"))
                and not (recover_partial and candidate.get("recovery_html") and not task["cursor"].get("recovery_html_used"))):
            with self._connect() as conn:
                self._lock_task(conn, task)
            try:
                batch_body = self._body_batches.read_body(candidate["body_batch_ref"], candidate)
            except BatchBodyUnavailable as exc:
                batch_fallback = str(exc)
                record_timing("body_batch_fallback", 0, outcome="error")
                candidate = {**candidate, "metadata": {**(candidate.get("metadata") or {}),
                                                       "body_batch_fallback": batch_fallback}}
        if use_saved_body:
            body = self._read_text(existing["text_object_key"], existing["content_hash"])
            final_url, title = existing["canonical_url"], existing["title"]
            published, date_status = existing["published_at"], existing["date_status"]
            digest, key = existing["content_hash"], existing["text_object_key"]
            body_origin = "saved_object"
            if not published and task.get("_undated_existing_article_id"):
                # A saved body is reusable even when the initial parser missed
                # its publication field. Recheck only this rediscovered URL;
                # retain the original text and classifications unchanged.
                date_probe = self._probe_saved_publication(task, final_url)
                if date_probe:
                    published, date_evidence = date_probe
                    date_status = "page_verified"
                    task["_date_probe_evidence"] = {"publication_date_evidence": date_evidence}
                    candidate = {**candidate, "metadata": {**(candidate.get("metadata") or {}),
                        **task["_date_probe_evidence"]}}
        elif batch_body is not None:
            body, final_url = batch_body["full_text"], batch_body["canonical_url"]
            published, date_status = parse_date(batch_body["published_at"]), batch_body.get("publication_date_status", "api_verified")
            candidate = _confirmed_publisher(candidate, final_url)
            candidate["metadata"]["publisher_provenance"].update(batch_body["provenance"])
            task["_verified_candidate"] = {**candidate, "url": final_url,
                "observed_url": task["payload"]["url"], "published_at": str(published or "")}
            task["_verified_date_status"] = date_status
            body_origin = batch_body.get("body_origin", "wordpress_api_batch")
            candidate["metadata"].update(body_origin=body_origin, text_extent=batch_body.get("text_extent", "unknown"))
        else:
            with self._connect() as conn:
                self._lock_task(conn, task)
            domain_deferred = False
            historical = task["cursor"].get("estadao_liveblog_html") or task["cursor"].get("estadao_uva_html") or (candidate.get("recovery_html") if not task["cursor"].get("recovery_html_used") else None)
            try:
                if historical:
                    try:
                        raw = self._read_text(historical["key"], historical["hash"])
                        response = requests.Response()
                        response.status_code, response.url, response.encoding = 200, final_url, "utf-8"
                        response._content = raw.encode("utf-8")
                        body_origin = "historical_html"
                        html_hash, html_key = historical["hash"], historical["key"]
                        candidate = {**candidate, "html_hash": html_hash, "html_object_key": html_key}
                    except (FetchProblem, requests.RequestException, OSError, KeyError):
                        self._checkpoint_fetch(task, {"recovery_html_used": True})
                        response = article_fetch(publisher_article_request_url(final_url))
                        historical = None
                else:
                    response = article_fetch(publisher_article_request_url(final_url))
            except DomainCooldown:
                domain_deferred = True
                raise
            finally:
                # A shared cooldown is scheduling, not an article fetch attempt.
                if not domain_deferred and not historical:
                    with self._connect() as conn:
                        self._lock_task(conn, task)
                        conn.execute("UPDATE political_jobs SET fetch_attempted=fetch_attempted+1 WHERE id=%s", (task["job_id"],))
            if task['source_key'] == 'istoe':
                from .political_istoe_discovery import allowed
                if not allowed(response.url):
                    raise FetchProblem('istoe_redirect_outside_portal', retryable=False)
            if non_news_reason(response.url):
                return self._finish_fetch_not_news(task, response.url)
            if is_google_intermediary(candidate["url"]) and not is_google_intermediary(response.url):
                self._checkpoint_fetch(task, {"resolved_url": canonicalize_url(response.url)})
            if (task["source_key"] == "congresso_em_foco" and response.status_code == 404
                    and not task["cursor"].get("publisher_alternative_url")
                    and urlparse(response.url).hostname == "www.congressoemfoco.com.br"
                    and re.fullmatch(r"/(?:noticia|artigo|coluna|informativo)/\d+/[^/?]+", urlparse(response.url).path)):
                # The publisher's public AMP edition can survive a broken main
                # route. Persist the choice before fetching so retries reuse it.
                self._record_access_failure(task, response)
                alternative = "https://www.congressoemfoco.com.br/amp" + urlparse(response.url).path
                self._checkpoint_fetch(task, {"publisher_alternative_url": alternative,
                    "publisher_alternative_original_url": canonicalize_url(response.url),
                    "publisher_alternative_reason": "primary_http_404"})
                response = article_fetch(alternative)
            if response.status_code >= 400:
                self._record_access_failure(task, response)
                retry_at = retry_after_deadline(response.headers.get("Retry-After"))
                problem = FetchProblem(f"http_{response.status_code}", retryable=response.status_code in {408,425,429} or response.status_code >= 500,
                                       status_code=response.status_code, retry_after=remaining_seconds(retry_at) if retry_at else 0)
                self._save_metadata_attempt(task, job, task.get("_verified_candidate") or candidate, problem)
                raise problem
            final_url = canonicalize_url(response.url)
            if task["source_key"] == "estadao" and not task["cursor"].get("estadao_public_original"):
                from .political_estadao import public_original
                original = public_original(response.text, final_url)
                if original:
                    original_hash, original_key = self._store_html(response.text)
                    self._checkpoint_fetch(task, {"resolved_url": canonicalize_url(original["url"]),
                        "recovery_html_used": True,
                        "estadao_public_original": {**original, "html_hash": original_hash, "html_object_key": original_key}})
                    # Re-enter through saved-object lookup; retries and storage
                    # failures preserve the public resolution in the lease cursor.
                    return self._fetch_article(task)
            if is_google_intermediary(final_url):
                from . import political_discovery
                resolver = getattr(political_discovery, "resolve_google_redirect", None)
                with timed_operation("google_resolution"):
                    resolved = resolver(candidate["url"], self.fetch, initial_response=response) if resolver and urlparse(candidate["url"]).hostname == "news.google.com" else None
                if resolved and not is_google_intermediary(resolved):
                    if non_news_reason(resolved):
                        return self._finish_fetch_not_news(task, resolved)
                    self._checkpoint_fetch(task, {"resolved_url": canonicalize_url(resolved)})
                    with self._connect() as conn:
                        resolved_article = self._find_article(conn, resolved)
                    if (resolved_article and resolved_article["text_object_key"]
                            and resolved_article["body_status"] == "body_extracted"
                            and resolved_article["source_key"] != "google_news" and not force_refresh):
                        # Resolution can reveal an already stored publisher URL.
                        # Re-enter with its committed cursor to reuse that text.
                        return self._fetch_article(task)
                    response = article_fetch(publisher_article_request_url(resolved))
                    if non_news_reason(response.url):
                        return self._finish_fetch_not_news(task, response.url)
                    if is_google_intermediary(response.url):
                        problem = FetchProblem("google_url_unresolved")
                        self._save_metadata_attempt(task, job, candidate, problem)
                        raise problem
                    if response.status_code >= 400:
                        self._record_access_failure(task, response)
                        retry_at = retry_after_deadline(response.headers.get("Retry-After"))
                        problem = FetchProblem(f"http_{response.status_code}",
                            retryable=response.status_code in {408,425,429} or response.status_code >= 500,
                            status_code=response.status_code, retry_after=remaining_seconds(retry_at) if retry_at else 0)
                        failed_candidate = _confirmed_publisher(candidate, response.url)
                        self._save_metadata_attempt(task, job, {**failed_candidate,
                            "url": canonicalize_url(response.url), "observed_url": candidate["url"]}, problem)
                        raise problem
                    final_url = canonicalize_url(response.url)
                else:
                    problem = FetchProblem("google_url_unresolved")
                    self._save_metadata_attempt(task, job, candidate, problem)
                    raise problem
            if is_publisher_access_challenge(final_url, response.text):
                self._record_access_failure(task, response)
                problem = FetchProblem("publisher_access_challenge", retryable=False)
                self._save_metadata_attempt(task, job, candidate, problem)
                raise problem
            with timed_operation("extraction"):
                extracted = extract_article(response.text, final_url)
            if task["source_key"] == "estadao":
                from . import political_estadao_liveblog as liveblog
                from . import political_estadao_uva as uva
                try:
                    uva_url = uva.announced_url(response.text, final_url)
                    if uva_url:
                        if not task["cursor"].get("estadao_uva_html"):
                            initial_hash,initial_key = self._store_html(response.text)
                            self._checkpoint_fetch(task,{"estadao_uva_html":{"hash":initial_hash,"key":initial_key,"url":final_url}})
                        checkpoint = task["cursor"].get("estadao_uva_data")
                        if checkpoint:
                            if checkpoint["url"] != uva_url:
                                raise ValueError("estadao_uva_checkpoint_identity_changed")
                            uva_data = json.loads(self._read_discovery_response(checkpoint["key"],checkpoint["hash"]))
                        else:
                            page = article_fetch(uva_url)
                            if page.status_code >= 400:
                                retry_at = retry_after_deadline(page.headers.get("Retry-After"))
                                raise FetchProblem(f"http_{page.status_code}",retryable=page.status_code in {408,425,429} or page.status_code>=500,
                                    status_code=page.status_code,retry_after=remaining_seconds(retry_at) if retry_at else 0)
                            uva_data = page.json()
                            uva.editorial(uva_data)
                            page_hash,page_key = self._store_discovery_response(page.content)
                            checkpoint = {"url":uva_url,"hash":page_hash,"key":page_key}
                            self._checkpoint_fetch(task,{"estadao_uva_data":checkpoint})
                        extracted = {**extracted,**uva.editorial(uva_data)}
                        extracted["uva_provenance"]["response"] = checkpoint
                        body_origin = "publisher_public_uva"
                    live_state = liveblog.initial(response.text, final_url)
                    if live_state:
                        first_date = parse_date(live_state["published_at"])
                        if first_date and not job["date_from"] <= first_date.astimezone(ZONE).date() <= job["date_to"]:
                            return self._finish_fetch_outside_window(task, published=first_date, date_status="page_verified")
                        checkpoint = task["cursor"].get("estadao_liveblog_state")
                        if checkpoint:
                            saved_state = json.loads(self._read_discovery_response(checkpoint["key"], checkpoint["hash"]))
                            if saved_state["article_id"] != live_state["article_id"]:
                                raise ValueError("estadao_liveblog_checkpoint_identity_changed")
                            live_state = saved_state
                            if live_state["offset"] < live_state["total"]:
                                page_url = liveblog.next_url(live_state)
                                page = article_fetch(page_url)
                                if page.status_code >= 400:
                                    retry_at = retry_after_deadline(page.headers.get("Retry-After"))
                                    raise FetchProblem(f"http_{page.status_code}", retryable=page.status_code in {408,425,429} or page.status_code>=500,
                                        status_code=page.status_code,retry_after=remaining_seconds(retry_at) if retry_at else 0)
                                live_state = liveblog.append(live_state, page.json())
                                page_hash,page_key = self._store_discovery_response(page.content)
                                live_state["receipts"] = live_state["receipts"] + [{"url":page_url,"hash":page_hash,"key":page_key}]
                        if not task["cursor"].get("estadao_liveblog_html"):
                            initial_hash,initial_key = self._store_html(response.text)
                            self._checkpoint_fetch(task,{"estadao_liveblog_html":{"hash":initial_hash,"key":initial_key,"url":final_url}})
                        state_hash,state_key = self._store_discovery_response(_json(live_state).encode())
                        self._checkpoint_fetch(task,{"estadao_liveblog_state":{"hash":state_hash,"key":state_key}})
                        if live_state["offset"] < live_state["total"]:
                            with self._connect() as conn:
                                self._finish(conn,task,"queued",result={"liveblogUpdates":live_state["offset"],"liveblogTotal":live_state["total"]})
                                # Successful pagination is progress, not a failed attempt.
                                conn.execute("UPDATE political_tasks SET attempts=0 WHERE id=%s",(task["id"],))
                            return {"taskId":task["id"],"status":"continue"}
                        extracted = liveblog.article(live_state)
                        body_origin = "publisher_public_liveblog"
                except ValueError as exc:
                    raise FetchProblem(str(exc),retryable=False) from exc
            if task["source_key"] == "congresso_em_foco" and task["cursor"].get("publisher_alternative_url"):
                if canonicalize_url(str(extracted.get("canonical_url") or "")) != task["cursor"]["publisher_alternative_original_url"]:
                    raise FetchProblem("congresso_amp_unverified_identity", retryable=False)
                body_origin = "publisher_public_amp"
                candidate = {**candidate, "metadata": {**(candidate.get("metadata") or {}),
                    "publisher_access_alternative": {"url": task["cursor"]["publisher_alternative_url"],
                        "original_url": task["cursor"]["publisher_alternative_original_url"],
                        "reason": task["cursor"].get("publisher_alternative_reason")}}}
                primary_date = parse_date(task["cursor"].get("publisher_alternative_primary_date"))
                amp_date = parse_date(extracted.get("published_at"))
                if primary_date:
                    if amp_date and primary_date.astimezone(ZONE).date() != amp_date.astimezone(ZONE).date():
                        raise FetchProblem("congresso_amp_publication_date_conflict", retryable=False)
                    extracted["published_at"] = primary_date.isoformat()
                    extracted["publication_date_evidence"] = {
                        "method": "congresso_primary_metadata_with_amp_body", "precision": "timestamp",
                        "primary_date": primary_date.isoformat(), "amp_date": str(amp_date or ""),
                        "primary_html_key": task["cursor"].get("publisher_alternative_primary_html_key"),
                        "primary_html_hash": task["cursor"].get("publisher_alternative_primary_html_hash")}
            body = str(extracted.get("full_text") or "")
            title = str(extracted.get("title") or title)
            page_date = parse_date(extracted.get("published_at"))
            if (extracted.get("publication_date_evidence") or {}).get("method") == "missing_original_post_date":
                published, date_status = None, "unknown"
            if page_date:
                published, date_status = page_date, "page_verified"
                if task.get("_undated_existing_article_id"):
                    if not html_key:
                        html_hash, html_key = self._store_html(response.text)
                    task["_date_probe_evidence"] = {"publication_date_evidence": {
                        **(extracted.get("publication_date_evidence") or {}),
                        "url": response.url, "published_at": published.isoformat(),
                        "html_hash": html_hash, "html_object_key": html_key,
                        "at": datetime.now(timezone.utc).isoformat()}}
            canonical = canonicalize_url(str(extracted.get("canonical_url") or ""))
            if canonical and normalize_domain(urlparse(canonical).hostname) == normalize_domain(urlparse(final_url).hostname):
                final_url = canonical
            if non_news_reason(final_url):
                return self._finish_fetch_not_news(task, final_url)
            candidate = _confirmed_publisher(candidate, final_url)
            candidate["metadata"].update({key: extracted[key] for key in
                ("extraction_method", "extraction_version", "text_extent", "restriction_evidence", "content_format",
                 "publication_date_evidence", "liveblog_provenance", "uva_provenance", "format_provenance") if key in extracted})
            candidate["metadata"]["body_origin"] = body_origin
            if task["cursor"].get("estadao_public_original"):
                candidate["metadata"]["publisher_resolution"] = task["cursor"]["estadao_public_original"]
            candidate["metadata"].update(task.get("_date_probe_evidence") or {})
            # Preserve confirmed metadata if immutable-object storage fails after
            # extraction; the generic retry handler must not revert to RSS dates.
            task["_verified_candidate"] = {**candidate, "url": final_url,
                "observed_url": task["payload"]["url"], "title": candidate.get("title") or title,
                "published_at": str(published or "")}
            task["_verified_date_status"] = date_status
            if published and not job["date_from"] <= published.astimezone(ZONE).date() <= job["date_to"]:
                return self._finish_fetch_outside_window(task, published=published, date_status=date_status)
            # Preserve genuine short editorial text; snippets remain separate.
            editorial_available = bool(body.strip()) and (extracted.get("extraction_method") or len(body.split()) >= 40)
            insufficient_body = not editorial_available
            sample = int(hashlib.sha256(final_url.encode()).hexdigest()[:8], 16) % 100 < 5
            if insufficient_body or (sample and match_targets(job["target_snapshots"], title, body)):
                if not html_key:
                    html_hash, html_key = self._store_html(response.text)
                candidate = {**candidate, "html_hash": html_hash, "html_object_key": html_key}
                with self._connect() as conn:
                    self._lock_task(conn, task)
                    conn.execute("UPDATE political_observations SET metadata=metadata || %s::jsonb WHERE job_id=%s AND observed_url=%s",
                        (_json({"html_hash": html_hash, "html_object_key": html_key}), task["job_id"], task["payload"]["url"]))
            if insufficient_body:
                if historical:
                    self._checkpoint_fetch(task, {"recovery_html_used": True})
                empty_count = int(task["cursor"].get("empty_body_responses", 0)) + 1
                self._checkpoint_fetch(task, {"empty_body_responses": empty_count})
                problem = FetchProblem("body_missing", retryable=empty_count < 2)
                self._save_metadata_attempt(task, job, {**candidate, "url": final_url,
                    "title": candidate.get("title") or title, "published_at": str(published or ""),
                    "metadata": {**(candidate.get("metadata") or {}),
                                 "discovery_published_at": candidate.get("published_at") or ""}},
                    problem, date_status=date_status)
                raise problem
        if published and not job["date_from"] <= published.astimezone(ZONE).date() <= job["date_to"]:
            return self._finish_fetch_outside_window(task, published=published, date_status=date_status)
        if recover_partial:
            same_text = hashlib.sha256(body.encode("utf-8")).hexdigest() == existing["content_hash"]
            improved_extent = (candidate.get("metadata") or {}).get("text_extent") == "available"
            if len(body) < max(1, int(existing["body_chars"])) or (same_text and not improved_extent):
                # Recovery cannot replace retained text with a shorter response
                # or report the same restricted excerpt as repaired. A retained
                # HTML attempt may try the current public page once afterwards.
                if historical:
                    self._checkpoint_fetch(task, {"recovery_html_used": True})
                elif batch_body is not None:
                    self._checkpoint_fetch(task, {"recovery_batch_used": True})
                problem = FetchProblem("partial_text_not_improved", retryable=bool(historical or batch_body is not None))
                self._save_metadata_attempt(task, job, {**candidate, "url": final_url,
                    "title": title, "published_at": str(published or "")}, problem, date_status=date_status)
                raise problem
        hits = match_targets(job["target_snapshots"], title, body)
        if existing and (force_refresh or job["kind"] == "recover") and not hits:
            # A changed source article must retain its archived association and human
            # classification while recording corrected text; review never erases it.
            with self._connect() as conn:
                old_hits = conn.execute("SELECT target_key,target_name,keyword_matched FROM political_mentions WHERE article_id=%s",
                                        (existing["id"],)).fetchall()
            hits = [dict(hit) for hit in old_hits if hit["target_key"] in job["target_keys"]]
        # Publisher discovery deliberately fetches stories before matching their
        # bodies. Only relevant, in-window stories need durable body objects.
        if hits and body and not digest:
            digest, key = self._store_text(body)
        with self._connect() as conn:
            self._lock_task(conn, task)
            article_id = None
            write_result = {}
            disposition = "no_match"
            if hits:
                recovery_origin = ((candidate.get("metadata") or {}).get("recovery") or {}).get("observed_url")
                article_id = self._persist_article(conn, {**candidate, "url": final_url, "title": title,
                    "observed_url": recovery_origin or task["payload"]["url"]}, hits,
                    published=published, date_status=date_status, body_chars=len(body), digest=digest, object_key=key, job_id=task["job_id"],
                    force_correction=force_refresh, write_result=write_result)
                conn.execute("INSERT INTO political_url_aliases(url,article_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (candidate["url"], article_id))
                disposition = "saved" if write_result["inserted"] else "duplicate"
            conn.execute("UPDATE political_observations SET article_id=%s,disposition=%s,metadata=metadata || %s::jsonb WHERE job_id=%s AND observed_url=%s",
                         (article_id, disposition, _json(self._publication_fact(published, date_status,
                            (candidate.get("metadata") or {}).get("publication_date_evidence"))), task["job_id"], candidate["url"]))
            partial_remaining = bool(recover_partial and article_id and (candidate.get("metadata") or {}).get("text_extent") == "partial")
            next_cursor = dict(task["cursor"])
            enriched = bool(write_result.get("enriched", False) or next_cursor.get("partial_body_enriched"))
            if recover_partial and enriched:
                next_cursor["partial_body_enriched"] = True
            # Keep every improved excerpt, but finish its public-page attempt
            # before calling an explicitly partial record recovered.
            continue_partial = partial_remaining and bool(historical or batch_body is not None)
            if continue_partial:
                next_cursor["recovery_html_used" if historical else "recovery_batch_used"] = True
            finish_status = "queued" if continue_partial else "gap" if partial_remaining else "complete"
            self._finish(conn, task, finish_status, cursor=next_cursor,
                error_type="partial_text_remaining" if partial_remaining and not continue_partial else "",
                result={"articleId": article_id, "disposition": disposition, "bodyEnriched": enriched,
                    "partialTextRecovered": bool(recover_partial and article_id and (candidate.get("metadata") or {}).get("text_extent") == "available"),
                    "partialTextRemaining": partial_remaining, "bodyOrigin": body_origin, "bodyBatchFallback": batch_fallback})
        return {"taskId": task["id"], "status": "continue" if continue_partial else "gap" if partial_remaining else disposition, "articleId": article_id,
                "bodyOrigin": body_origin, "bodyBatchFallback": batch_fallback}

    def _save_metadata_attempt(self, task: dict, job: dict, candidate: dict, problem: FetchProblem, *, date_status: str = "") -> None:
        # The generic failure handler must not save the original RSS candidate
        # again after this attempt resolved its publisher URL or corrected date.
        problem.metadata_handled = True
        # Failed extraction can already have resolved the publisher. Keep the
        # discovery URL so persistence can rename/merge its earlier metadata row.
        candidate = {**candidate, "observed_url": candidate.get("observed_url") or task["payload"]["url"]}
        hits = match_targets(job["target_snapshots"], str(candidate.get("title") or ""), str(candidate.get("snippet") or ""))
        if not hits:
            return
        published = parse_date(candidate.get("published_at"))
        if published and not job["date_from"] <= published.astimezone(ZONE).date() <= job["date_to"]:
            return
        with self._connect() as conn:
            self._lock_task(conn, task)
            existing = self._find_article(conn, candidate["url"])
            if existing and existing["published_at"] and not job["date_from"] <= existing["published_at"].astimezone(ZONE).date() <= job["date_to"]:
                task["_metadata_date_conflict"] = True
                # A new RSS date must not attach an older, unverified metadata
                # record to this window. Preserve the record and both dates for
                # review; this is not proof that either publication date is right.
                conn.execute("""UPDATE political_observations SET article_id=NULL,disposition='date_conflict',
                    metadata=metadata || %s::jsonb WHERE job_id=%s AND observed_url=%s""",
                    (_json({"date_conflict":{"existingArticleId":existing["id"],
                        "existingPublication":str(existing["published_at"]),"candidatePublication":str(published or ""),
                        "existingDateStatus":existing["date_status"],"fetchFailure":str(problem)}}),task["job_id"],task["payload"]["url"]))
                return
            if existing and existing["canonical_url"] != candidate["url"]:
                candidate = {**candidate, "observed_url": candidate.get("observed_url") or candidate["url"], "url": existing["canonical_url"]}
            article_id = self._persist_article(conn, candidate, hits, published=published,
                date_status=(date_status or ("api_verified" if (candidate.get("metadata") or {}).get("wordpress_id") is not None else "source_reported")) if published else "unknown",
                job_id=task["job_id"])
            for observed_url in {task["payload"]["url"], candidate.get("observed_url") or candidate["url"]}:
                conn.execute("INSERT INTO political_url_aliases(url,article_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                             (canonicalize_url(observed_url), article_id))
            conn.execute("UPDATE political_observations SET article_id=%s,disposition='metadata_only' WHERE job_id=%s AND observed_url=%s",
                         (article_id, task["job_id"], task["payload"]["url"]))

    def _persist_article(self, conn, candidate: dict, hits: list[dict], *, published=None, date_status="unknown",
                         body_chars=0, digest="", object_key="", legacy_id=None, summary="", story_key="", story_title="",
                         story_summary="", legacy_story_id=None, job_id=None, force_correction=False, write_result=None) -> int:
        url = canonicalize_url(candidate["url"])
        title = clean_title(candidate.get("title") or url)[:1000]
        observed_url = canonicalize_url(str(candidate.get("observed_url") or url))
        identity_urls = list(publisher_article_identity_urls(url))
        observed_urls = list(publisher_article_identity_urls(observed_url))
        for locked_url in sorted(set(identity_urls + observed_urls)):
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", ("political-url:" + locked_url,))
        previous_rows = conn.execute("SELECT * FROM political_articles WHERE canonical_url=ANY(%s) ORDER BY id FOR UPDATE", (identity_urls,)).fetchall()
        previous = previous_rows[0] if previous_rows else None
        if previous:
            for duplicate in previous_rows[1:]:
                self._merge_articles(conn, duplicate, previous)
            # Keep the original record and its URL; attach the verified host
            # variant as an alias instead of inserting a second article.
            url = previous["canonical_url"]
        publisher_confirmed = candidate.get("_publisher_confirmed") is True
        if observed_url != url:
            alias = conn.execute("""SELECT a.* FROM political_articles a WHERE a.canonical_url=%s OR EXISTS
                (SELECT 1 FROM political_url_aliases u WHERE u.article_id=a.id AND u.url=%s)
                ORDER BY (a.canonical_url=%s) DESC,a.id LIMIT 1 FOR UPDATE""",
                (observed_url, observed_url, observed_url)).fetchone()
            if alias and (not previous or alias["id"] != previous["id"]):
                if previous:
                    self._merge_articles(conn, alias, previous)
                else:
                    conn.execute("INSERT INTO political_article_revisions(article_id,previous,reason) VALUES (%s,%s::jsonb,'canonical_url_resolved')",
                                 (alias["id"], _json(dict(alias))))
                    conn.execute("UPDATE political_articles SET canonical_url=%s WHERE id=%s", (url, alias["id"]))
                    previous = {**alias, "canonical_url": url}
        if previous:
            publisher_changed = publisher_confirmed and (candidate.get("source_key"), candidate.get("source_name")) != (previous["source_key"], previous["source_name"])
            changed = (digest and digest != previous["content_hash"]) or (published and date_status in {"page_verified", "api_verified"} and published != previous["published_at"])
            changed = changed or (body_chars > 0 and title != previous["title"]) or publisher_changed
            if changed:
                conn.execute("INSERT INTO political_article_revisions(article_id,previous,reason) VALUES (%s,%s::jsonb,%s)",
                             (previous["id"], _json(dict(previous)), "publisher_correction" if publisher_changed else "review_correction" if force_correction else "fetch_update"))
            if 0 < body_chars < previous["body_chars"] and not force_correction:
                body_chars, digest, object_key = previous["body_chars"], previous["content_hash"], previous["text_object_key"]
                if not candidate.get("html_object_key"):
                    candidate = {**candidate, "html_hash": previous["html_hash"], "html_object_key": previous["html_object_key"]}
        row = conn.execute("""INSERT INTO political_articles(canonical_url,title,source_key,source_name,published_at,date_status,discovered_at,
            snippet,summary,body_status,body_chars,content_hash,text_object_key,legacy_id,metadata)
            VALUES (%s,%s,%s,%s,%s,%s,COALESCE(%s,NOW()),%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
            ON CONFLICT(canonical_url) DO UPDATE SET
            title=CASE WHEN EXCLUDED.body_chars>0 THEN EXCLUDED.title ELSE political_articles.title END,
            published_at=CASE WHEN EXCLUDED.date_status IN ('page_verified','api_verified') THEN EXCLUDED.published_at
                              ELSE COALESCE(political_articles.published_at,EXCLUDED.published_at) END,
            date_status=CASE WHEN EXCLUDED.date_status IN ('page_verified','api_verified') THEN EXCLUDED.date_status ELSE political_articles.date_status END,
            discovered_at=LEAST(political_articles.discovered_at,EXCLUDED.discovered_at),
            body_status=CASE WHEN EXCLUDED.body_chars>0 THEN EXCLUDED.body_status ELSE political_articles.body_status END,
            body_chars=CASE WHEN EXCLUDED.body_chars>0 THEN EXCLUDED.body_chars ELSE political_articles.body_chars END,
            content_hash=CASE WHEN EXCLUDED.body_chars>0 THEN EXCLUDED.content_hash ELSE political_articles.content_hash END,
            text_object_key=CASE WHEN EXCLUDED.body_chars>0 THEN EXCLUDED.text_object_key ELSE political_articles.text_object_key END,
            source_key=CASE WHEN %s THEN EXCLUDED.source_key ELSE political_articles.source_key END,
            source_name=CASE WHEN %s THEN EXCLUDED.source_name ELSE political_articles.source_name END,
            metadata=CASE WHEN EXCLUDED.body_chars>0 THEN political_articles.metadata || EXCLUDED.metadata
                          WHEN %s THEN political_articles.metadata || jsonb_build_object('publisher_provenance',EXCLUDED.metadata->'publisher_provenance')
                          ELSE political_articles.metadata END,
            legacy_id=COALESCE(political_articles.legacy_id,EXCLUDED.legacy_id),updated_at=NOW() RETURNING id,(xmax=0) AS inserted""",
            (url, title, str(candidate.get("source_key") or "legacy"), str(candidate.get("source_name") or ""), published, date_status, parse_date(candidate.get("discovered_at")),
             str(candidate.get("snippet") or "")[:2000], summary[:20000], "body_extracted" if body_chars >= BODY_MIN_CHARS else "metadata_only",
             body_chars, digest, object_key, legacy_id, _json(candidate.get("metadata") or {}),
             publisher_confirmed, publisher_confirmed, publisher_confirmed)).fetchone()
        article_id = int(row["id"])
        if write_result is not None:
            write_result["inserted"] = bool(row["inserted"])
            write_result["enriched"] = bool(previous and object_key and (not previous["text_object_key"]
                or (candidate.get("recover_partial_text") and digest != previous["content_hash"])))
        if candidate.get("html_object_key"):
            conn.execute("UPDATE political_articles SET html_hash=%s,html_object_key=%s WHERE id=%s",
                         (str(candidate.get("html_hash") or ""), str(candidate["html_object_key"]), article_id))
        for alias_url in set(identity_urls + [url]):
            conn.execute("INSERT INTO political_url_aliases(url,article_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (alias_url, article_id))
        mentions_added = 0
        for hit in hits:
            changed = conn.execute("""INSERT INTO political_mentions(article_id,target_key,target_name,keyword_matched,legacy_id)
                VALUES (%s,%s,%s,%s,%s) ON CONFLICT(article_id,target_key) DO NOTHING""",
                         (article_id, hit["target_key"], hit["target_name"], hit["keyword_matched"], hit.get("legacy_id")))
            mentions_added += changed.rowcount
        if job_id:
            conn.execute("UPDATE political_jobs SET articles_inserted=articles_inserted+%s,mentions_inserted=mentions_inserted+%s WHERE id=%s",
                         (int(row["inserted"]), mentions_added, job_id))
        if not story_key:
            day = published.astimezone(ZONE).date().isoformat() if published else "unknown"
            story_key = "title:" + hashlib.sha256((day + ":" + title.casefold()).encode()).hexdigest()
        story = conn.execute("""INSERT INTO political_stories(story_key,title,summary,legacy_id) VALUES (%s,%s,%s,%s)
            ON CONFLICT(story_key) DO UPDATE SET updated_at=NOW() RETURNING id""",
                             (story_key, story_title or title, story_summary or summary, legacy_story_id)).fetchone()
        if legacy_story_id is not None:
            conn.execute("""INSERT INTO political_story_articles(article_id,story_id) VALUES (%s,%s)
                ON CONFLICT DO NOTHING""", (article_id, story["id"]))
        else:
            conn.execute("""INSERT INTO political_story_articles(article_id,story_id)
                SELECT %s,%s WHERE NOT EXISTS (SELECT 1 FROM political_story_articles WHERE article_id=%s)
                ON CONFLICT DO NOTHING""", (article_id, story["id"], article_id))
        return article_id

    @staticmethod
    def _merge_articles(conn, old: dict, canonical: dict) -> None:
        """Merge a resolved wrapper into an existing outlet article without losing review data."""
        old_id, new_id = old["id"], canonical["id"]
        # URL/article locks already fence concurrent article merges. Editors use
        # the same per-mention advisory lock and recheck membership after taking
        # it: let any earlier edit commit before copying, and hold these locks
        # until deleting the wrapper commits so later stale edits get not found.
        pairs = conn.execute("""SELECT article_id,target_key FROM political_mentions
            WHERE article_id=ANY(%s) ORDER BY article_id,target_key""", ([old_id, new_id],)).fetchall()
        for pair in pairs:
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                         (f"political-classification:{pair['article_id']}:{pair['target_key']}",))
        conn.execute("INSERT INTO political_article_revisions(article_id,previous,reason) VALUES (%s,%s::jsonb,'canonical_duplicate_merge')",
                     (new_id, _json(dict(old))))
        conn.execute("""INSERT INTO political_mentions(article_id,target_key,target_name,keyword_matched,legacy_id,rule_version,created_at)
            SELECT %s,target_key,target_name,keyword_matched,legacy_id,rule_version,created_at FROM political_mentions WHERE article_id=%s
            ON CONFLICT DO NOTHING""", (new_id, old_id))
        conn.execute("""INSERT INTO political_classification_revisions(article_id,target_key,previous,updated_by)
            SELECT %s,target_key,to_jsonb(c),'canonical_merge' FROM political_classifications c WHERE article_id=%s""", (new_id, old_id))
        conn.execute("""INSERT INTO political_classifications(article_id,target_key,payload,updated_by,updated_at,legacy_id)
            SELECT %s,target_key,payload,updated_by,updated_at,legacy_id FROM political_classifications WHERE article_id=%s
            ON CONFLICT DO NOTHING""", (new_id, old_id))
        conn.execute("UPDATE political_article_revisions SET article_id=%s WHERE article_id=%s", (new_id, old_id))
        conn.execute("UPDATE political_classification_revisions SET article_id=%s WHERE article_id=%s", (new_id, old_id))
        conn.execute("UPDATE political_observations SET article_id=%s WHERE article_id=%s", (new_id, old_id))
        conn.execute("UPDATE political_url_aliases SET article_id=%s WHERE article_id=%s", (new_id, old_id))
        conn.execute("""INSERT INTO political_story_articles(article_id,story_id)
            SELECT %s,story_id FROM political_story_articles WHERE article_id=%s ON CONFLICT DO NOTHING""", (new_id, old_id))
        conn.execute("UPDATE political_legacy_story_articles SET article_id=%s WHERE article_id=%s", (new_id, old_id))
        conn.execute("UPDATE political_legacy_ids SET new_id=%s WHERE new_id=%s AND entity_type IN ('article','mention','classification')", (new_id, old_id))
        conn.execute("DELETE FROM political_articles WHERE id=%s", (old_id,))

    def _review(self, task: dict) -> dict:
        with self._connect() as conn:
            job = conn.execute("SELECT * FROM political_jobs WHERE id=%s", (task["job_id"],)).fetchone()
            after = int(task["cursor"].get("after_id") or 0)
            ceiling = task["cursor"].get("ceiling")
            if ceiling is None:
                ceiling = conn.execute("SELECT COALESCE(MAX(id),0) AS n FROM political_articles").fetchone()["n"]
            rows = conn.execute("""SELECT * FROM political_articles WHERE id>%s AND id<=%s
                AND (published_at IS NULL OR (published_at AT TIME ZONE 'America/Sao_Paulo')::date BETWEEN %s AND %s)
                ORDER BY id LIMIT 100""", (after, ceiling, job["date_from"], job["date_to"])).fetchall()
        prepared = []
        for row in rows:
            try:
                body = self._read_text(row["text_object_key"], row["content_hash"]) if row["text_object_key"] else row["snippet"]
            except (FetchProblem, requests.RequestException, KeyError, OSError):
                # A missing/corrupt archive is a per-article repair, not a whole
                # review-window retry that prevents later articles being examined.
                row = {**row, "body_status": "metadata_only"}
                body = row["snippet"]
            prepared.append((row, match_targets(job["target_snapshots"], row["title"], body)))
        with self._connect() as conn:
            self._lock_task(conn, task)
            added = 0
            for row, hits in prepared:
                if row["body_status"] != "body_extracted" or row["date_status"] not in {"page_verified", "api_verified"}:
                    candidate = {"url": row["canonical_url"], "title": row["title"], "source_key": row["source_key"],
                        "source_name": row["source_name"], "snippet": row["snippet"], "published_at": str(row["published_at"] or ""),
                        "force_refresh": True}
                    conn.execute("""INSERT INTO political_observations(job_id,source_task_id,observed_url,source_key,title,snippet)
                        VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                        (task["job_id"], task["id"], row["canonical_url"], row["source_key"], row["title"], row["snippet"]))
                    self._insert_task(conn, task["job_id"], "fetch", candidate)
                for hit in hits:
                    changed = conn.execute("""INSERT INTO political_mentions(article_id,target_key,target_name,keyword_matched)
                        VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING article_id""",
                                           (row["id"], hit["target_key"], hit["target_name"], hit["keyword_matched"])).fetchone()
                    added += bool(changed)
            more = len(rows) == 100 and rows[-1]["id"] < ceiling
            conn.execute("UPDATE political_jobs SET mentions_inserted=mentions_inserted+%s WHERE id=%s", (added, task["job_id"]))
            self._finish(conn, task, "queued" if more else "complete",
                         cursor={"after_id": rows[-1]["id"] if rows else ceiling, "ceiling": ceiling},
                         result={"scanned": len(rows), "mentionsAdded": added}, raw_count=len(rows))
        return {"taskId": task["id"], "status": "continue" if more else "complete", "scanned": len(rows), "mentionsAdded": added}


political_corpus = PoliticalCorpusService()
