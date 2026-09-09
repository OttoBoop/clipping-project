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
from .political_metrics import record_timing, timed_operation
from .political_rate_limits import (
    DomainCooldown, TASK_DOMAIN_FALLBACK_SQL, active_cooldown, domain_deferral,
    normalize_domain, record_response_cooldown, remaining_seconds,
    retry_after_deadline, task_request_domain,
)
from .publisher_tls import publisher_verify
from .storage_bridge import ArtifactStore, artifact_store
from .political_body_batches import BatchBodyUnavailable, WordPressBodyBatches
from .political_record_types import non_news_reason

START_DATE = date(2026, 6, 1)
ZONE = ZoneInfo("America/Sao_Paulo")
LEASE_SECONDS = 180
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_SITEMAP_RESPONSE_BYTES = 128 * 1024 * 1024
MAX_SITEMAP_RESPONSE_SECONDS = 120
BODY_MIN_CHARS = 200
TERMINAL = {"complete", "gap", "failed", "cancelled", "split"}
ACTIVE = {"queued", "running", "retryable"}


def _publisher_host(hostname: str) -> str:
    hostname = str(hostname).strip().lower().rstrip(".")
    return hostname[4:] if hostname.startswith("www.") else hostname


@lru_cache(maxsize=1)
def _publisher_registry() -> dict[str, tuple[str, str]]:
    with (DATA_DIR / "political_sources_v1.json").open(encoding="utf-8") as source_file:
        rows = json.load(source_file)["sources"]
    return {_publisher_host(row["domain"]): (row["key"], row["name"])
            for row in rows if row.get("domain")}


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


class PoliticalCorpusService:
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
        kind = str(payload.get("kind") or "collect")
        if kind not in {"collect", "review"}:
            raise ValueError("invalid_political_job_kind")
        if not self.store.enabled:
            raise PoliticalCorpusNotConfigured("political_body_storage_not_configured")
        self.ensure_schema()
        if kind == "review":
            tasks = [{"source_key": "_review", "strategy": "review", "cursor": {"after_id": 0}}]
        else:
            from .political_discovery import build_tasks
            tasks = build_tasks(snapshots, start.isoformat(), end.isoformat(),
                                source_keys=payload.get("source_keys") or payload.get("sourceKeys"))
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
                    return self._job_dto(existing)
            conn.execute("""INSERT INTO political_jobs(id,kind,target_keys,target_snapshots,date_from,date_to,requested_by,request_key)
                            VALUES (%s,%s,%s,%s::jsonb,%s,%s,%s,%s)""",
                         (job_id, kind, selected, _json(snapshots), start, end, started_by, request_key))
            for task in tasks:
                self._insert_task(conn, job_id, "review" if kind == "review" else "discovery", task)
            row = conn.execute("SELECT * FROM political_jobs WHERE id=%s", (job_id,)).fetchone()
        return self._job_dto(row)

    def _insert_task(self, conn, job_id: str, kind: str, payload: dict) -> None:
        source_key = str(payload.get("source_key") or "unknown")
        dedupe = canonicalize_url(str(payload.get("url") or "")) if kind == "fetch" else hashlib.sha256(_json(payload).encode()).hexdigest()
        # Source rotation still comes first when claiming. Within each source,
        # finish its direct publisher discovery before optional Google queries.
        priority = 0 if kind == "discovery" and payload.get("strategy") == "google_news" else 10
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
                "targetKeys": row["target_keys"], "dateFrom": str(row["date_from"]), "dateTo": str(row["date_to"]),
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
        observed = conn.execute("""SELECT COUNT(*) AS unique_candidates,
            COUNT(DISTINCT article_id) FILTER(WHERE EXISTS (SELECT 1 FROM political_mentions m
                WHERE m.article_id=o.article_id AND m.target_key=ANY(j.target_keys))) AS articles_saved,
            COUNT(*) FILTER (WHERE disposition='duplicate') AS duplicates,
            COUNT(*) FILTER (WHERE disposition='no_match') AS no_match,
            COUNT(*) FILTER (WHERE disposition='outside_window') AS outside_window
            FROM political_observations o JOIN political_jobs j ON j.id=o.job_id WHERE o.job_id=%s""", (job_id,)).fetchone()
        quality = conn.execute("""SELECT COUNT(*) FILTER (WHERE a.body_status='body_extracted') AS body_extracted,
            COUNT(*) FILTER (WHERE a.published_at IS NULL) AS unknown_dates,
            COUNT(*) FILTER (WHERE a.body_status<>'body_extracted' OR a.date_status NOT IN ('page_verified','api_verified')) AS needs_review,
            COUNT(*) FILTER (WHERE a.date_status IN ('page_verified','api_verified')) AS dates_verified
            FROM political_articles a WHERE EXISTS
            (SELECT 1 FROM political_observations o WHERE o.job_id=%s AND o.article_id=a.id)""", (job_id,)).fetchone()
        return {"uniqueCandidates": int(observed["unique_candidates"]), "articlesSaved": int(observed["articles_saved"]),
                "articlesInserted": int(counters["articles_inserted"]), "mentionsInserted": int(counters["mentions_inserted"]),
                "fetchAttempted": int(counters["fetch_attempted"]),
                "fetchPending": sum(int(row["count"]) for row in tasks if row["kind"] == "fetch" and row["status"] in ACTIVE),
                "duplicates": int(observed["duplicates"]), "noMatch": int(observed["no_match"]),
                "outsideWindow": int(observed["outside_window"]), "bodyExtracted": int(quality["body_extracted"]),
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

    def coverage(self, job_id: str = "", *, allowed_target_keys: list[str]) -> dict:
        allowed = _scope(allowed_target_keys)
        status = self.status(job_id, allowed_target_keys=allowed)
        current = status["current"]
        if not current:
            return {"jobId": "", "sources": [], "gaps": []}
        with self._connect() as conn:
            rows = conn.execute("""SELECT source_key,kind,status,COUNT(*) AS count FROM political_tasks
                WHERE job_id=%s GROUP BY source_key,kind,status ORDER BY source_key,kind,status""", (current["id"],)).fetchall()
            gaps = conn.execute("""SELECT id,source_key,kind,status,error_type,payload->>'date_from' AS date_from,
                payload->>'date_to' AS date_to FROM political_tasks WHERE job_id=%s AND status IN ('gap','failed','retryable')
                ORDER BY id LIMIT 100""", (current["id"],)).fetchall()
        return {"jobId": current["id"], "status": current["status"], "sources": [dict(row) for row in rows],
                "gaps": [dict(row) for row in gaps], "metrics": current["metrics"]}

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
            clauses.append("a.source_key=%s")
            args.append(source_key)
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

    def article(self, article_id: int, *, allowed_target_keys: list[str]) -> dict:
        allowed = _scope(allowed_target_keys)
        self.ensure_schema()
        with self._connect() as conn:
            rows = self._article_rows(conn, "a.id=%s AND EXISTS (SELECT 1 FROM political_mentions m WHERE m.article_id=a.id AND m.target_key=ANY(%s))",
                                      [int(article_id), allowed], allowed, 1)
        if not rows:
            raise PoliticalNotFound("political_article_not_found")
        return self._article_dto(rows[0])

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
        if not key:
            return ""
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
        return raw.decode("utf-8")

    def article_text(self, article_id: int, *, allowed_target_keys: list[str]) -> dict:
        self.article(article_id, allowed_target_keys=allowed_target_keys)
        with self._connect() as conn:
            row = conn.execute("SELECT text_object_key,content_hash,body_status FROM political_articles WHERE id=%s", (int(article_id),)).fetchone()
        return {"id": int(article_id), "bodyStatus": row["body_status"], "text": self._read_text(row["text_object_key"], row["content_hash"])}

    def classifications(self, article_id: int, *, allowed_target_keys: list[str]) -> dict:
        allowed = _scope(allowed_target_keys)
        self.article(article_id, allowed_target_keys=allowed)
        with self._connect() as conn:
            rows = conn.execute("""SELECT * FROM political_classifications WHERE article_id=%s AND target_key=ANY(%s)
                                   ORDER BY target_key""", (int(article_id), allowed)).fetchall()
        return {"articleId": int(article_id), "items": [{"targetKey": row["target_key"], "payload": row["payload"],
                  "updatedBy": row["updated_by"], "updatedAt": str(row["updated_at"]), "legacyId": row["legacy_id"]} for row in rows]}

    def upsert_classification(self, article_id: int, payload: dict, *, allowed_target_keys: list[str], updated_by: str) -> dict:
        target_key = str(payload.get("target_key") or payload.get("targetKey") or "")
        _scope(allowed_target_keys, [target_key])
        self.article(article_id, allowed_target_keys=[target_key])
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
        self.article(article_id, allowed_target_keys=allowed)
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
    def _discovery_backpressure(conn) -> tuple[bool, list[str]]:
        """Aggregate once across active jobs, instead of once per queued task.

        Below 2000 active fetches every source may discover. From 2000 to
        3999, admit only sources with fewer than 100 active fetches. At 4000,
        stop admission entirely. These are admission thresholds, not strict
        queue caps: two already running discovery pages can each enqueue up to
        the existing 5000-candidate page limit before the next check.
        """
        rows = conn.execute("""SELECT t.source_key,COUNT(*) AS n FROM political_tasks t
            JOIN political_jobs j ON j.id=t.job_id
            WHERE t.kind='fetch' AND t.status=ANY(%s) AND j.status IN ('queued','running')
            GROUP BY t.source_key""", (list(ACTIVE),)).fetchall()
        total = sum(int(row["n"]) for row in rows)
        return total >= 4000, [row["source_key"] for row in rows if total >= 2000 and int(row["n"]) >= 100]

    def claim_task(self, kind: str, *, worker_id: str, lease_seconds: int = LEASE_SECONDS) -> dict | None:
        if kind not in {"discovery", "fetch"}:
            raise ValueError("invalid_worker_kind")
        self.ensure_schema()
        kinds = ["discovery", "review"] if kind == "discovery" else ["fetch"]
        maximum = 2 if kind == "discovery" else 4
        with self._connect() as conn:
            conn.execute("SELECT pg_advisory_xact_lock(%s)", (734892102 if kind == "discovery" else 734892103,))
            blocked_sources = []
            if kind == "discovery":
                stop_discovery, blocked_sources = self._discovery_backpressure(conn)
                if stop_discovery:
                    return None
            count = conn.execute("""SELECT COUNT(*) AS n FROM political_tasks WHERE kind=ANY(%s)
                AND status='running' AND leased_until>NOW()""", (kinds,)).fetchone()["n"]
            if count >= maximum:
                return None
            source_domains = _source_domains()
            row = conn.execute("""SELECT t.* FROM political_tasks t JOIN political_jobs j ON j.id=t.job_id
                LEFT JOIN political_source_leases scheduling ON scheduling.source_key=t.source_key
                LEFT JOIN political_domain_limits cooling ON cooling.domain=""" + TASK_DOMAIN_FALLBACK_SQL + """
                WHERE t.kind=ANY(%s) AND j.status IN ('queued','running')
                AND (t.kind='fetch' OR NOT (t.source_key=ANY(%s)))
                AND (cooling.cooldown_until IS NULL OR cooling.cooldown_until<=NOW())
                AND (t.status IN ('queued','retryable') OR (t.status='running' AND t.leased_until<NOW()))
                AND (t.next_attempt_at IS NULL OR t.next_attempt_at<=NOW())
                AND (t.kind='fetch' OR NOT EXISTS (SELECT 1 FROM political_source_leases s
                    WHERE s.source_key=t.source_key AND s.leased_until>NOW()))
                AND (t.kind<>'fetch' OR t.payload->>'url' NOT LIKE 'https://news.google.com/%%'
                    OR NOT EXISTS (SELECT 1 FROM political_tasks active
                        WHERE active.kind='fetch' AND active.status='running' AND active.leased_until>NOW()
                        AND active.payload->>'url' LIKE 'https://news.google.com/%%'))
                ORDER BY CASE WHEN t.kind='fetch' THEN scheduling.fetch_claimed_at
                              ELSE scheduling.discovery_claimed_at END ASC NULLS FIRST,
                    t.priority DESC,
                    CASE WHEN t.kind='fetch' AND COALESCE(t.payload->>'published_at','')<>'' THEN 0 ELSE 1 END,
                    t.id FOR UPDATE OF t SKIP LOCKED LIMIT 1""", (_json(source_domains), kinds, blocked_sources)).fetchone()
            if not row:
                return None
            token = uuid.uuid4().hex
            row = conn.execute("""UPDATE political_tasks SET status='running',attempts=attempts+1,
                lease_owner=%s,lease_token=%s,leased_until=NOW()+(%s*INTERVAL '1 second'),
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
        with self._connect() as conn:
            conn.execute("INSERT INTO political_domain_limits(domain) VALUES (%s) ON CONFLICT DO NOTHING", (domain,))
            # Lock the same row updated by HTTP rate-limit responses before
            # reserving a normal 1rps slot. A cooldown does not grow this queue.
            conn.execute("SELECT domain FROM political_domain_limits WHERE domain=%s FOR UPDATE", (domain,))
            deadline = active_cooldown(conn, domain)
            if deadline:
                raise DomainCooldown(domain, deadline)
            row = conn.execute("""UPDATE political_domain_limits SET next_request_at=GREATEST(NOW(),next_request_at)+INTERVAL '1 second'
                WHERE domain=%s RETURNING EXTRACT(EPOCH FROM (next_request_at-NOW()-INTERVAL '1 second')) AS wait_seconds""", (domain,)).fetchone()
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
        except OSError as exc:
            raise FetchProblem("dns_failed") from exc
        if not addresses or any(not ipaddress.ip_address(address[4][0]).is_global for address in addresses):
            raise FetchProblem("private_article_url", retryable=False)

    def fetch(self, url: str, **kwargs) -> requests.Response:
        large_sitemap = bool(kwargs.get("stream_sitemap"))
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
            if response.status_code in {429, 503}:
                with self._connect() as conn:
                    record_response_cooldown(conn, domain, response.status_code, response.headers.get("Retry-After"))
            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")
                response.close()
                if not location:
                    raise FetchProblem("redirect_without_location", retryable=False)
                current = urljoin(current, location)
                continue
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

    def process_task(self, task: dict) -> dict:
        try:
            if task["kind"] == "discovery":
                return self._discover(task)
            if task["kind"] == "review":
                return self._review(task)
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
            error_type = str(exc) if isinstance(exc, FetchProblem) else type(exc).__name__
            if not isinstance(exc, FetchProblem) and hasattr(exc, "status_code"):
                error_type = f"{type(exc).__name__}:http_{int(getattr(exc, 'status_code', 0) or 0)}"
                safe_detail = str(exc)
                if safe_detail in {"malformed XML response", "sitemap byte limit reached", "expanded sitemap byte limit reached", "unsupported XML entity declaration"}:
                    error_type = safe_detail.replace(" ", "_").lower()
            if task["kind"] == "fetch" and not getattr(exc, "metadata_handled", False):
                try:
                    with self._connect() as conn:
                        job = conn.execute("SELECT * FROM political_jobs WHERE id=%s", (task["job_id"],)).fetchone()
                    self._save_metadata_attempt(task, job, task.get("_verified_candidate") or task["payload"],
                        FetchProblem(error_type), date_status=task.get("_verified_date_status") or "")
                except LeaseLost:
                    return {"taskId": task["id"], "status": "lease_lost"}
            with self._connect() as conn:
                if task["kind"] == "discovery" and status == "gap":
                    self._enqueue_discovery_fallback(conn, task)
                self._finish(conn, task, status, error_type=error_type, delay=delay if status == "retryable" else 0)
            return {"taskId": task["id"], "status": status, "errorType": error_type}

    def _enqueue_discovery_fallback(self, conn, task: dict) -> None:
        from .political_discovery import fallback_tasks
        job = self._lock_task(conn, task)
        for child in fallback_tasks(task["payload"], job["target_snapshots"]):
            self._insert_task(conn, task["job_id"], "discovery", child)

    def _discover(self, task: dict) -> dict:
        from .political_discovery import discover
        with self._connect() as conn:
            stop_discovery, blocked_sources = self._discovery_backpressure(conn)
        if stop_discovery or task["source_key"] in blocked_sources:
            with self._connect() as conn:
                self._finish(conn, task, "queued", delay=15)
            return {"taskId": task["id"], "status": "backpressure"}
        payload = {**task["payload"], "cursor": task["cursor"]}
        result = discover(payload, self.fetch)
        candidates = result.get("candidates") or []
        if len(candidates) > 5000:
            raise FetchProblem("discovery_page_too_large", retryable=False)
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
        with self._connect() as conn:
            self._lock_task(conn, task)
            for candidate in candidates:
                url = canonicalize_url(str(candidate.get("url") or ""))
                if not url or urlparse(url).scheme not in {"http", "https"}:
                    continue
                candidate = {**candidate, "url": url, "source_key": task["source_key"]}
                reference = batch_refs.get((candidate.get("metadata") or {}).get("wordpress_id"))
                if reference:
                    candidate["body_batch_ref"] = reference
                elif batch_fallback:
                    candidate["metadata"] = {**(candidate.get("metadata") or {}), "body_batch_fallback": batch_fallback}
                conn.execute("""INSERT INTO political_observations(job_id,source_task_id,observed_url,source_key,title,snippet,metadata)
                    VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb) ON CONFLICT(job_id,observed_url) DO NOTHING""",
                             (task["job_id"], task["id"], url, task["source_key"], str(candidate.get("title") or "")[:1000],
                              str(candidate.get("snippet") or "")[:2000], _json(candidate.get("metadata") or {})))
                self._insert_task(conn, task["job_id"], "fetch", candidate)
            for child in result.get("child_tasks") or []:
                self._insert_task(conn, task["job_id"], "discovery", child)
            if outcome == "gap":
                self._enqueue_discovery_fallback(conn, task)
            self._finish(conn, task, "queued" if outcome == "continue" else outcome,
                         cursor=result.get("next_cursor") or task["cursor"], raw_count=int(result.get("raw_count") or 0),
                         error_type=str(result.get("gap_reason") or ""),
                         result={"bodyBatchRecords": len(batch_refs), "bodyBatchFallback": batch_fallback})
        return {"taskId": task["id"], "status": outcome, "candidates": len(candidates)}

    def _finish_fetch_outside_window(self, task: dict, *, published=None, date_status="") -> dict:
        with self._connect() as conn:
            self._lock_task(conn, task)
            # A prior failed attempt may have saved the feed's inaccurate date.
            # Correct only this job's newly collected record, retaining content,
            # associations, classifications and the original metadata revision.
            if published and date_status in {"page_verified", "api_verified"}:
                previous = conn.execute("""SELECT a.* FROM political_articles a
                    JOIN political_observations o ON o.article_id=a.id
                    WHERE o.job_id=%s AND o.observed_url=%s AND a.legacy_id IS NULL
                    FOR UPDATE OF a""", (task["job_id"], task["payload"]["url"])).fetchone()
                if previous and (previous["published_at"] != published or previous["date_status"] != date_status):
                    conn.execute("INSERT INTO political_article_revisions(article_id,previous,reason) VALUES(%s,%s::jsonb,'publication_date_verification')",
                                 (previous["id"], _json(dict(previous))))
                    conn.execute("UPDATE political_articles SET published_at=%s,date_status=%s WHERE id=%s",
                                 (published,date_status,previous["id"]))
            conn.execute("UPDATE political_observations SET disposition='outside_window',article_id=NULL WHERE job_id=%s AND observed_url=%s",
                         (task["job_id"], task["payload"]["url"]))
            self._finish(conn, task, "complete", result={"disposition": "outside_window"})
        return {"taskId": task["id"], "status": "outside_window"}

    def _finish_fetch_not_news(self, task: dict, url: str) -> dict:
        result = {"disposition": "not_news", "reason": non_news_reason(url),
                  "recordKind": "candidate_profile", "resolvedUrl": canonicalize_url(url)}
        with self._connect() as conn:
            self._lock_task(conn, task)
            conn.execute("""UPDATE political_observations SET disposition='not_news',article_id=NULL,
                metadata=metadata || %s::jsonb WHERE job_id=%s AND observed_url=%s""",
                (_json({"non_news": result}), task["job_id"], task["payload"]["url"]))
            self._finish(conn, task, "complete", result=result)
        return {"taskId": task["id"], "status": "not_news", "reason": result["reason"]}

    def _fetch_article(self, task: dict) -> dict:
        from .political_discovery import extract_article, is_google_intermediary
        candidate = task["payload"]
        if non_news_reason(candidate["url"]):
            return self._finish_fetch_not_news(task, candidate["url"])
        with self._connect() as conn:
            job = conn.execute("SELECT * FROM political_jobs WHERE id=%s", (task["job_id"],)).fetchone()
            existing = conn.execute("""SELECT a.* FROM political_articles a LEFT JOIN political_url_aliases u ON u.article_id=a.id
                WHERE a.canonical_url=%s OR u.url=%s ORDER BY a.id LIMIT 1""", (candidate["url"], candidate["url"])).fetchone()
        body, final_url, title = "", candidate["url"], str(candidate.get("title") or "")
        published = parse_date(candidate.get("published_at"))
        date_status = ("api_verified" if (candidate.get("metadata") or {}).get("wordpress_id") is not None else "source_reported") if published else "unknown"
        digest = key = ""
        force_refresh = bool(candidate.get("force_refresh"))
        html_hash = html_key = ""
        use_saved_body = bool(existing and existing["text_object_key"] and existing["body_status"] == "body_extracted"
                              and not force_refresh and existing["source_key"] != "google_news")
        batch_body, batch_fallback, body_origin = None, "", "publisher_page"
        if candidate.get("body_batch_ref") and not use_saved_body and not force_refresh:
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
        elif batch_body is not None:
            body, final_url = batch_body["full_text"], batch_body["canonical_url"]
            published, date_status = parse_date(batch_body["published_at"]), "api_verified"
            candidate = _confirmed_publisher(candidate, final_url)
            candidate["metadata"]["publisher_provenance"].update(batch_body["provenance"])
            task["_verified_candidate"] = {**candidate, "url": final_url,
                "observed_url": task["payload"]["url"], "published_at": str(published or "")}
            task["_verified_date_status"] = date_status
            body_origin = "wordpress_api_batch"
        else:
            with self._connect() as conn:
                self._lock_task(conn, task)
            domain_deferred = False
            try:
                response = self.fetch(final_url)
            except DomainCooldown:
                domain_deferred = True
                raise
            finally:
                # A shared cooldown is scheduling, not an article fetch attempt.
                if not domain_deferred:
                    with self._connect() as conn:
                        self._lock_task(conn, task)
                        conn.execute("UPDATE political_jobs SET fetch_attempted=fetch_attempted+1 WHERE id=%s", (task["job_id"],))
            if non_news_reason(response.url):
                return self._finish_fetch_not_news(task, response.url)
            if response.status_code >= 400:
                retry_at = retry_after_deadline(response.headers.get("Retry-After"))
                problem = FetchProblem(f"http_{response.status_code}", retryable=response.status_code in {408,425,429} or response.status_code >= 500,
                                       status_code=response.status_code, retry_after=remaining_seconds(retry_at) if retry_at else 0)
                self._save_metadata_attempt(task, job, candidate, problem)
                raise problem
            final_url = canonicalize_url(response.url)
            if is_google_intermediary(final_url):
                from . import political_discovery
                resolver = getattr(political_discovery, "resolve_google_redirect", None)
                resolved = resolver(candidate["url"], self.fetch, initial_response=response) if resolver and urlparse(candidate["url"]).hostname == "news.google.com" else None
                if resolved and not is_google_intermediary(resolved):
                    if non_news_reason(resolved):
                        return self._finish_fetch_not_news(task, resolved)
                    response = self.fetch(resolved)
                    if non_news_reason(response.url):
                        return self._finish_fetch_not_news(task, response.url)
                    if is_google_intermediary(response.url):
                        problem = FetchProblem("google_url_unresolved")
                        self._save_metadata_attempt(task, job, candidate, problem)
                        raise problem
                    if response.status_code >= 400:
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
            with timed_operation("extraction"):
                extracted = extract_article(response.text)
            body = str(extracted.get("full_text") or "")
            title = str(extracted.get("title") or title)
            page_date = parse_date(extracted.get("published_at"))
            if page_date:
                published, date_status = page_date, "page_verified"
            canonical = canonicalize_url(str(extracted.get("canonical_url") or ""))
            if canonical and urlparse(canonical).hostname == urlparse(final_url).hostname:
                final_url = canonical
            if non_news_reason(final_url):
                return self._finish_fetch_not_news(task, final_url)
            candidate = _confirmed_publisher(candidate, final_url)
            # Preserve confirmed metadata if immutable-object storage fails after
            # extraction; the generic retry handler must not revert to RSS dates.
            task["_verified_candidate"] = {**candidate, "url": final_url,
                "observed_url": task["payload"]["url"], "title": candidate.get("title") or title,
                "published_at": str(published or "")}
            task["_verified_date_status"] = date_status
            if published and not job["date_from"] <= published.astimezone(ZONE).date() <= job["date_to"]:
                return self._finish_fetch_outside_window(task, published=published, date_status=date_status)
            insufficient_body = len(body.strip()) < BODY_MIN_CHARS or extracted.get("extraction_state") == "metadata_only"
            sample = int(hashlib.sha256(final_url.encode()).hexdigest()[:8], 16) % 100 < 5
            if insufficient_body or (sample and match_targets(job["target_snapshots"], title, body)):
                html_hash, html_key = self._store_html(response.text)
                candidate = {**candidate, "html_hash": html_hash, "html_object_key": html_key}
                with self._connect() as conn:
                    self._lock_task(conn, task)
                    conn.execute("UPDATE political_observations SET metadata=metadata || %s::jsonb WHERE job_id=%s AND observed_url=%s",
                        (_json({"html_hash": html_hash, "html_object_key": html_key}), task["job_id"], task["payload"]["url"]))
            if insufficient_body:
                problem = FetchProblem("body_missing")
                self._save_metadata_attempt(task, job, {**candidate, "url": final_url,
                    "title": candidate.get("title") or title, "published_at": str(published or ""),
                    "metadata": {**(candidate.get("metadata") or {}),
                                 "discovery_published_at": candidate.get("published_at") or ""}},
                    problem, date_status=date_status)
                raise problem
        if published and not job["date_from"] <= published.astimezone(ZONE).date() <= job["date_to"]:
            return self._finish_fetch_outside_window(task, published=published, date_status=date_status)
        hits = match_targets(job["target_snapshots"], title, body)
        if existing and force_refresh and not hits:
            # A changed source article must retain its archived association and human
            # classification while recording corrected text; review never erases it.
            with self._connect() as conn:
                old_hits = conn.execute("SELECT target_key,target_name,keyword_matched FROM political_mentions WHERE article_id=%s",
                                        (existing["id"],)).fetchall()
            hits = [dict(hit) for hit in old_hits]
        # Publisher discovery deliberately fetches stories before matching their
        # bodies. Only relevant, in-window stories need durable body objects.
        if hits and body and not digest:
            digest, key = self._store_text(body)
        with self._connect() as conn:
            self._lock_task(conn, task)
            article_id = None
            disposition = "no_match"
            if hits:
                write_result = {}
                article_id = self._persist_article(conn, {**candidate, "url": final_url, "title": title, "observed_url": task["payload"]["url"]}, hits,
                    published=published, date_status=date_status, body_chars=len(body), digest=digest, object_key=key, job_id=task["job_id"],
                    force_correction=force_refresh, write_result=write_result)
                conn.execute("INSERT INTO political_url_aliases(url,article_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (candidate["url"], article_id))
                disposition = "saved" if write_result["inserted"] else "duplicate"
            conn.execute("UPDATE political_observations SET article_id=%s,disposition=%s WHERE job_id=%s AND observed_url=%s",
                         (article_id, disposition, task["job_id"], candidate["url"]))
            self._finish(conn, task, "complete", result={"articleId": article_id, "disposition": disposition,
                         "bodyOrigin": body_origin, "bodyBatchFallback": batch_fallback})
        return {"taskId": task["id"], "status": disposition, "articleId": article_id,
                "bodyOrigin": body_origin, "bodyBatchFallback": batch_fallback}

    def _save_metadata_attempt(self, task: dict, job: dict, candidate: dict, problem: FetchProblem, *, date_status: str = "") -> None:
        # The generic failure handler must not save the original RSS candidate
        # again after this attempt resolved its publisher URL or corrected date.
        problem.metadata_handled = True
        hits = match_targets(job["target_snapshots"], str(candidate.get("title") or ""), str(candidate.get("snippet") or ""))
        if not hits:
            return
        published = parse_date(candidate.get("published_at"))
        if published and not job["date_from"] <= published.astimezone(ZONE).date() <= job["date_to"]:
            return
        with self._connect() as conn:
            self._lock_task(conn, task)
            existing = conn.execute("""SELECT a.canonical_url FROM political_articles a
                LEFT JOIN political_url_aliases u ON u.article_id=a.id
                WHERE a.canonical_url=%s OR u.url=%s ORDER BY a.id LIMIT 1""",
                (candidate["url"], candidate["url"])).fetchone()
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
        for locked_url in sorted({url, observed_url}):
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", ("political-url:" + locked_url,))
        previous = conn.execute("SELECT * FROM political_articles WHERE canonical_url=%s FOR UPDATE", (url,)).fetchone()
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
            metadata=CASE WHEN %s THEN political_articles.metadata || jsonb_build_object('publisher_provenance',EXCLUDED.metadata->'publisher_provenance')
                          ELSE political_articles.metadata END,
            legacy_id=COALESCE(political_articles.legacy_id,EXCLUDED.legacy_id),updated_at=NOW() RETURNING id,(xmax=0) AS inserted""",
            (url, title, str(candidate.get("source_key") or "legacy"), str(candidate.get("source_name") or ""), published, date_status, parse_date(candidate.get("discovered_at")),
             str(candidate.get("snippet") or "")[:2000], summary[:20000], "body_extracted" if body_chars >= BODY_MIN_CHARS else "metadata_only",
             body_chars, digest, object_key, legacy_id, _json(candidate.get("metadata") or {}),
             publisher_confirmed, publisher_confirmed, publisher_confirmed)).fetchone()
        article_id = int(row["id"])
        if write_result is not None:
            write_result["inserted"] = bool(row["inserted"])
        if candidate.get("html_object_key"):
            conn.execute("UPDATE political_articles SET html_hash=%s,html_object_key=%s WHERE id=%s",
                         (str(candidate.get("html_hash") or ""), str(candidate["html_object_key"]), article_id))
        conn.execute("INSERT INTO political_url_aliases(url,article_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (url, article_id))
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
        conn.execute("""INSERT INTO political_mentions(article_id,target_key,target_name,keyword_matched,legacy_id,rule_version)
            SELECT %s,target_key,target_name,keyword_matched,legacy_id,rule_version FROM political_mentions WHERE article_id=%s
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
