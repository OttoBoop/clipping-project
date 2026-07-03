from __future__ import annotations

import gc
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from pipeline.collectors import (
    CandidateArticle,
    collect_camara_archive,
    collect_google_news,
    collect_internal_site_search,
    collect_rss,
    collect_sitemap_daily,
    collect_vejario_archive,
    collect_wordpress_api,
)
from pipeline.ingest import IngestionOptions, ordered_unique, process_candidates, run_ingestion, select_targets
from pipeline.database import ClippingDB
from pipeline.matcher import Target
from pipeline.settings import (
    CAMARA_ARCHIVE_TARGET,
    FLAVIO_INTERNAL_SEARCH_TARGETS,
    RSS_FEEDS,
    SITEMAP_DAILY_SOURCES,
    VEJARIO_ARCHIVE_TARGETS,
    WORDPRESS_API_SITES,
    build_google_queries_for_target,
    build_internal_search_queries_for_target,
    build_wordpress_queries_for_target,
    get_active_targets,
)

from .config import ROOT, db_path
from .db_admin import (
    backfill_missing_target_mentions,
    cleanup_false_backfilled_target_mentions,
    connect,
    ensure_app_tables,
    load_targets,
    primary_target_keys,
    target_labels,
    validate_configured_db_file,
    validate_target_keys,
)
from .rio_topics import (
    RIO_CITY_TOPIC,
    RIO_ECONOMICO_SCOPE,
    RIO_TOURISM_TOPIC,
    load_rio_topic_config,
    rio_topic_labels,
    rio_topic_source_query_texts,
    rio_topic_target_snapshot,
    resolve_rio_topic_request,
)
from .storage_bridge import ArtifactStore, artifact_store


SAFE_COLLECTORS = {
    "all",
    "rss",
    "google_news",
    "wordpress_api",
    "internal_search",
    "sitemap_daily",
    "vejario_archive",
    "camara_archive",
}

ACTIVE_JOB_STATUSES = ("queued", "running", "exporting")
RESUMABLE_JOB_STATUSES = ("interrupted_resumable", "failed_needs_fix")
SOURCE_ACTIVE_STATUSES = {"pending", "running", "retrying", "interrupted_resumable"}
SOURCE_TERMINAL_STATUSES = {"complete", "failed_needs_fix"}
GROUPED_SOURCE_RUN_TARGET_KEY = "__all_targets__"
DEFAULT_COLLECTOR = "all"
EXPORT_TIMEOUT_SECONDS = 300
INCREMENTAL_EXPORT_MIN_SECONDS = 90
WORDPRESS_SOURCE_VERSION = "v2"
WORDPRESS_PAGE_SIZE = 25
WORDPRESS_MAX_PAGES = 240
INTERNAL_SEARCH_SOURCE_VERSION = "v2"
INTERNAL_SEARCH_MAX_PAGES = 60
VEJARIO_MAX_PAGES = 50
CAMARA_MAX_PAGES = 100
SECRET_ENV_MARKERS = ("PASSWORD", "SECRET", "TOKEN", "API_KEY", "SERVICE_KEY", "DATABASE_URL", "DEPLOY_HOOK")
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)(\b(?:authorization|api[-_]?key|apikey|service[-_]?key|session[-_]?secret|secret|token|password)\b\s*[:=]\s*)([^,\s;]+)"
)
BEARER_TOKEN_RE = re.compile(r"(?i)(Bearer\s+)([A-Za-z0-9._~+/\-]+=*)")
QUERY_SECRET_RE = re.compile(
    r"(?i)([?&](?:api[-_]?key|apikey|key|token|secret|password|access_token|refresh_token)=)[^&\s]+"
)

PRESETS: dict[str, dict[str, Any]] = {
    "rapido": {
        "target_keys": ["flavio_valle"],
        "days": 1,
        "max_candidates": 90000,
        "max_process_seconds": 90000,
    },
    "completo": {
        "target_keys": ["flavio_valle", "pedro_angelito"],
        "days": 7,
        "max_candidates": 90000,
        "max_process_seconds": 90000,
    },
}

CUSTOM_MAX_CANDIDATES = 90000
CUSTOM_MAX_PROCESS_SECONDS = 90000
DEFAULT_CANDIDATE_WORKERS = 4
DEFAULT_CANDIDATE_WORKER_LIMIT = 1
RIO_CANDIDATE_WORKER_LIMIT = 4
RIO_WORDPRESS_PAGES_PER_SLICE = 8
RIO_WORDPRESS_SOFT_FAIL_AFTER_PAGE = 3
RIO_TOPIC_QUERY_CHUNK_SIZE = 8
RIO_RECENT_ARCHIVE_MAX_PAGES = 5
RIO_FULL_TEXT_MAX_CHARS = 30000
RIO_RAW_HTML_MAX_CHARS = 0
LIVE_CHECKPOINT_MIN_SECONDS = 30
DEFAULT_SOURCE_RUN_YIELD_SECONDS = 0.05
_CHECKPOINT_LOCK = threading.Lock()
_LAST_CHECKPOINT_UPLOAD: dict[str, float] = {}
_LAST_INCREMENTAL_EXPORT: dict[str, float] = {}


def is_rio_topic_spec(spec: dict[str, Any]) -> bool:
    return (
        str(spec.get("scope") or "") == RIO_ECONOMICO_SCOPE
        and str(spec.get("topic") or "") in {RIO_CITY_TOPIC, RIO_TOURISM_TOPIC}
    )


def is_rio_tourism_spec(spec: dict[str, Any]) -> bool:
    return is_rio_topic_spec(spec) and str(spec.get("topic") or "") == RIO_TOURISM_TOPIC


def topic_queries_from_spec(spec: dict[str, Any], *, source_type: str = "google_news") -> list[str]:
    raw_values = spec.get("topic_queries") or []
    if source_type != "google_news" and spec.get("topic_source_queries"):
        raw_values = spec.get("topic_source_queries") or []
    return ordered_unique(
        [
            str(item.get("query") if isinstance(item, dict) else item).strip()
            for item in list(raw_values)
            if str(item.get("query") if isinstance(item, dict) else item).strip()
        ]
    )


def topic_query_meta(spec: dict[str, Any], query: str = "") -> dict[str, Any]:
    meta = {
        "scope": str(spec.get("scope") or ""),
        "topic": str(spec.get("topic") or ""),
        "dimension": str(spec.get("topic_dimension") or spec.get("topic") or ""),
        "topic_config_version": str(spec.get("topic_config_version") or ""),
    }
    if query:
        meta["query"] = query
        for row in list(spec.get("topic_queries") or []):
            if isinstance(row, dict) and str(row.get("query") or "").strip() == query:
                meta.update(
                    {
                        "query_group": str(row.get("group") or ""),
                        "query_weight": row.get("weight", ""),
                        "query_why": str(row.get("why") or ""),
                    }
                )
                break
    return {key: value for key, value in meta.items() if value != ""}


def annotate_topic_candidates(
    spec: dict[str, Any],
    candidates: list[CandidateArticle],
    *,
    cursor: dict[str, Any],
) -> list[CandidateArticle]:
    if not is_rio_topic_spec(spec):
        return candidates
    query = str(cursor.get("query") or "").strip()
    query_list = source_run_queries(cursor)
    if not query and len(query_list) == 1:
        query = query_list[0]
    meta = topic_query_meta(spec, query=query)
    if query_list:
        meta["queries"] = query_list
    for candidate in candidates:
        if not isinstance(candidate.metadata, dict):
            candidate.metadata = {}
        candidate.metadata.update(meta)
    return candidates


def effective_candidate_workers(spec: dict[str, Any]) -> int:
    requested = max(1, int(spec.get("candidate_workers") or DEFAULT_CANDIDATE_WORKERS))
    default_limit = RIO_CANDIDATE_WORKER_LIMIT if is_rio_topic_spec(spec) else DEFAULT_CANDIDATE_WORKER_LIMIT
    if spec.get("candidate_worker_limit") is not None:
        default_limit = safe_positive_int(spec.get("candidate_worker_limit"), default_limit)
        if str(spec.get("scope") or "") == RIO_ECONOMICO_SCOPE and str(spec.get("topic") or "") == RIO_CITY_TOPIC:
            default_limit = max(default_limit, RIO_CANDIDATE_WORKER_LIMIT)
    raw_limit = str(os.environ.get("CLIPPING_MAX_CANDIDATE_WORKERS") or default_limit).strip()
    try:
        limit = max(1, int(raw_limit))
    except ValueError:
        limit = default_limit
    return max(1, min(requested, limit))


def safe_positive_int(value: Any, default: int, *, minimum: int = 1, maximum: int | None = None) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = int(default)
    parsed = max(minimum, parsed)
    if maximum is not None:
        parsed = min(parsed, maximum)
    return parsed


def wordpress_pages_per_slice(spec: dict[str, Any]) -> int:
    default = RIO_WORDPRESS_PAGES_PER_SLICE if is_rio_topic_spec(spec) else 1
    return safe_positive_int(spec.get("wordpress_pages_per_slice"), default, minimum=1, maximum=12)


def wordpress_max_pages(spec: dict[str, Any]) -> int:
    return safe_positive_int(spec.get("wordpress_max_pages"), WORDPRESS_MAX_PAGES, minimum=1, maximum=WORDPRESS_MAX_PAGES)


def wordpress_soft_fail_after_page(spec: dict[str, Any]) -> int:
    default = RIO_WORDPRESS_SOFT_FAIL_AFTER_PAGE if is_rio_topic_spec(spec) else 5
    return safe_positive_int(spec.get("wordpress_soft_fail_after_page"), default, minimum=1, maximum=WORDPRESS_MAX_PAGES)


def rio_city_query_grouping_enabled(spec: dict[str, Any]) -> bool:
    if not is_rio_topic_spec(spec) or str(spec.get("topic") or "") != RIO_CITY_TOPIC:
        return False
    raw = spec.get("group_topic_queries_by_source")
    if raw is None:
        return True
    return str(raw).strip().lower() not in {"0", "false", "no", "off"}


def topic_query_chunk_size(spec: dict[str, Any]) -> int:
    return safe_positive_int(spec.get("topic_query_chunk_size"), RIO_TOPIC_QUERY_CHUNK_SIZE, minimum=1, maximum=25)


def rio_city_wordpress_date_scan_enabled(spec: dict[str, Any], site: dict[str, Any]) -> bool:
    return (
        str(spec.get("scope") or "") == RIO_ECONOMICO_SCOPE
        and str(spec.get("topic") or "") == RIO_CITY_TOPIC
        and str(site.get("rio_city_date_scan") or "").strip().lower() in {"1", "true", "yes", "on"}
    )


def chunk_queries(queries: list[str], chunk_size: int) -> list[list[str]]:
    size = max(1, int(chunk_size or 1))
    return [queries[index : index + size] for index in range(0, len(queries), size)] or []


def recent_short_window(spec: dict[str, Any], *, max_days: int = 31, max_age_days: int = 120) -> bool:
    try:
        start = date.fromisoformat(str(spec.get("date_from") or ""))
        end = date.fromisoformat(str(spec.get("date_to") or ""))
    except ValueError:
        return False
    if start > end:
        return False
    return (end - start).days + 1 <= max_days and (date.today() - end).days <= max_age_days


def archive_page_limit(spec: dict[str, Any], default: int) -> int:
    if not is_rio_topic_spec(spec) or not recent_short_window(spec):
        return default
    recent_limit = safe_positive_int(
        spec.get("recent_archive_max_pages"),
        RIO_RECENT_ARCHIVE_MAX_PAGES,
        minimum=1,
        maximum=default,
    )
    return min(default, recent_limit)


def should_soft_complete_wordpress_timeout(
    spec: dict[str, Any],
    exc: BaseException,
    *,
    page: int,
    seen_before: int,
) -> bool:
    if "hard timeout" not in str(exc):
        return False
    threshold_page = wordpress_soft_fail_after_page(spec)
    threshold_seen = WORDPRESS_PAGE_SIZE * max(1, threshold_page - 1)
    return page >= threshold_page and seen_before >= threshold_seen


def should_soft_complete_wordpress_http_error(
    spec: dict[str, Any],
    exc: BaseException,
    *,
    page: int,
    seen_before: int,
) -> bool:
    status = int(getattr(exc, "code", 0) or 0)
    if is_rio_topic_spec(spec):
        return status in {429, 500, 502, 503, 504}
    return is_late_wordpress_transient_http_error(exc, page=page, seen_before=seen_before)


def wordpress_soft_error_cursor(cursor: dict[str, Any], *, page: int, exc: BaseException) -> dict[str, Any]:
    next_cursor = dict(cursor)
    next_cursor["page"] = max(1, int(page or 1))
    next_cursor["page_size"] = WORDPRESS_PAGE_SIZE
    next_cursor["soft_error"] = sanitize_error(exc)
    next_cursor["soft_error_at"] = datetime.now(timezone.utc).isoformat()
    return next_cursor


def durable_source_run_yield_seconds() -> float:
    raw = str(os.environ.get("CLIPPING_SOURCE_RUN_YIELD_SECONDS") or DEFAULT_SOURCE_RUN_YIELD_SECONDS).strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        return DEFAULT_SOURCE_RUN_YIELD_SECONDS


def cooperative_source_run_yield(cancel_event: threading.Event) -> None:
    delay = durable_source_run_yield_seconds()
    if delay > 0:
        cancel_event.wait(delay)


@dataclass(slots=True)
class SourceUnit:
    source_key: str
    source_name: str
    source_type: str
    cursor: dict[str, Any]
    order: int


class JobConflict(RuntimeError):
    pass


class JobManager:
    def __init__(self, store: ArtifactStore) -> None:
        self.store = store
        self._lock = threading.Lock()
        self._active_job_id: str | None = None
        self._cancel_events: dict[str, threading.Event] = {}

    def current_status(self) -> dict[str, Any]:
        active = self._active_job_id
        if active:
            job = get_job(active)
            if job and str(job.get("status") or "") in ACTIVE_JOB_STATUSES:
                return job
            self._active_job_id = None
        active_job = get_active_job()
        if active_job:
            self._active_job_id = str(active_job["id"])
            return active_job
        rows = recent_jobs(1)
        return rows[0] if rows else {"status": "idle"}

    def cancel_active(self) -> dict[str, Any]:
        with self._lock:
            job_id = self._active_job_id
            if not job_id:
                active_job = get_active_job()
                if active_job:
                    job_id = str(active_job["id"])
            if not job_id:
                raise JobConflict("no_active_job")
            job = get_job(job_id)
            if job and str(job.get("status") or "") not in ACTIVE_JOB_STATUSES:
                raise JobConflict("no_active_job")
            event = self._cancel_events.get(job_id)
            if event is not None:
                event.set()
            else:
                self._active_job_id = None
        update_job(
            job_id,
            status="cancelled",
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        append_event(job_id, "job_cancelled", {"status": "cancelled"})
        return get_job(job_id) or {"id": job_id, "status": "cancelled"}

    def start_update(self, payload: dict[str, Any], *, started_by: str) -> dict[str, Any]:
        spec = build_update_spec(payload)
        return self._start("update", spec, started_by=started_by)

    def resume_update(self, job_id: str = "", *, started_by: str) -> dict[str, Any]:
        if not self.store.writes_available:
            raise RuntimeError("persistent_storage_not_configured")
        ensure_app_tables(db_path())
        with self._lock:
            if self._active_job_id:
                active_job = get_job(self._active_job_id)
                if active_job and str(active_job.get("status") or "") in ACTIVE_JOB_STATUSES:
                    raise JobConflict("job_already_running")
                self._active_job_id = None
            if get_active_job():
                raise JobConflict("job_already_running")
            job = get_resumable_job(job_id)
            if not job:
                raise JobConflict("no_resumable_job")
            resume_job_id = str(job["id"])
            spec = job_spec(job)
            if not spec.get("durable"):
                raise JobConflict("no_resumable_job")
            reset_resumable_source_runs(resume_job_id)
            update_job(
                resume_job_id,
                status="queued",
                finished_at="",
                error_message="",
            )
            append_event(
                resume_job_id,
                "job_resumed",
                {"status": "queued", "reason": "manual_resume", "started_by": started_by},
            )
            self._active_job_id = resume_job_id
            cancel_event = threading.Event()
            self._cancel_events[resume_job_id] = cancel_event
            thread = threading.Thread(
                target=self._run,
                args=(resume_job_id, "update", spec, cancel_event),
                name=f"clipping-job-{resume_job_id}-resume",
                daemon=True,
            )
            thread.start()
        return get_job(resume_job_id) or {"id": resume_job_id, "status": "queued"}

    def resume_startup_jobs(self) -> int:
        if not self.store.writes_available:
            return 0
        ensure_app_tables(db_path())
        if self._active_job_id or get_active_job():
            return 0
        job = get_resumable_job("")
        if not job:
            return 0
        try:
            self.resume_update(str(job["id"]), started_by="startup")
        except Exception:
            return 0
        return 1

    def start_export(self, *, started_by: str) -> dict[str, Any]:
        spec = {
            "preset": "export",
            "collector": "export",
            "target_keys": [],
            "date_from": "",
            "date_to": "",
            "export": True,
        }
        return self._start("export", spec, started_by=started_by)

    def record_completed_manual(
        self,
        *,
        result: dict[str, Any],
        uploaded: list[str],
        started_by: str,
        export: bool = True,
        mentions_inserted: int = 0,
    ) -> dict[str, Any]:
        job_id = f"manual-{uuid.uuid4().hex[:12]}"
        spec = {
            "preset": "manual",
            "collector": "manual",
            "target_keys": [],
            "date_from": "",
            "date_to": "",
            "export": bool(export),
        }
        ensure_app_tables(db_path())
        create_job(job_id, "manual", spec, started_by=started_by, enforce_single_active=False)
        articles_inserted = 1 if result.get("status") == "created" else 0
        stories_touched = 1 if result.get("storyId") else 0
        target_keys = [
            str(key).strip()
            for key in (result.get("targetKeys") or result.get("target_keys") or [])
            if str(key).strip()
        ]
        target_labels_map = result.get("targetLabels") if isinstance(result.get("targetLabels"), dict) else {}
        if articles_inserted:
            first_target = target_keys[0] if target_keys else ""
            append_event(
                job_id,
                "article_saved",
                {
                    "article_id": safe_int(result.get("articleId")),
                    "story_id": safe_int(result.get("storyId")),
                    "url": str(result.get("url") or ""),
                    "title": str(result.get("title") or ""),
                    "published_at": str(result.get("publishedAt") or result.get("published_at") or ""),
                    "source_name": str(result.get("sourceName") or result.get("source_name") or ""),
                    "source_type": str(result.get("sourceType") or result.get("source_type") or "manual"),
                    "target_keys": target_keys,
                    "target_key": first_target,
                    "target_label": str(target_labels_map.get(first_target) or first_target),
                    "articles_inserted_delta": 1,
                    "mentions_inserted_delta": mentions_inserted,
                    "stories_touched_delta": stories_touched,
                    "publication_state": "saved",
                    "reason": "manual_story",
                },
            )
        append_event(
            job_id,
            "manual_story_completed",
            {
                "status": str(result.get("status") or ""),
                "articles_inserted": articles_inserted,
                "mentions_inserted": mentions_inserted if articles_inserted else 0,
                "stories_touched": stories_touched,
            },
        )
        append_event(job_id, "artifacts_uploaded", artifact_upload_summary(uploaded))
        update_job(
            job_id,
            status="succeeded",
            finished_at=datetime.now(timezone.utc).isoformat(),
            articles_inserted=articles_inserted,
            mentions_inserted=mentions_inserted if articles_inserted else 0,
            stories_touched=stories_touched,
        )
        return get_job(job_id) or {"id": job_id, "status": "succeeded"}

    def _start(self, kind: str, spec: dict[str, Any], *, started_by: str) -> dict[str, Any]:
        if not self.store.writes_available:
            raise RuntimeError("persistent_storage_not_configured")
        with self._lock:
            if self._active_job_id or get_active_job():
                raise JobConflict("job_already_running")
            job_id = uuid.uuid4().hex[:12]
            ensure_app_tables(db_path())
            create_job(job_id, kind, spec, started_by=started_by)
            self._active_job_id = job_id
            cancel_event = threading.Event()
            self._cancel_events[job_id] = cancel_event
            thread = threading.Thread(
                target=self._run,
                args=(job_id, kind, spec, cancel_event),
                name=f"clipping-job-{job_id}",
                daemon=True,
            )
            thread.start()
        return get_job(job_id) or {"id": job_id, "status": "queued"}

    def _run(self, job_id: str, kind: str, spec: dict[str, Any], cancel_event: threading.Event) -> None:
        try:
            if cancel_event.is_set():
                return
            update_job(job_id, status="running")
            self.store.backup_current_artifacts(job_id)
            totals = {"articles_inserted": 0, "mentions_inserted": 0, "stories_touched": 0}
            coverage_state = ""

            if kind == "update":
                cleanup = cleanup_false_backfilled_target_mentions(db_path(), list(spec["target_keys"]))
                if cleanup.get("removedMentions"):
                    append_event(
                        job_id,
                        "target_backfill_cleanup",
                        {
                            "target_keys": list(spec["target_keys"]),
                            "mentions_inserted": 0,
                            "stories_touched": int(cleanup.get("storiesTouched") or 0),
                            "count": int(cleanup.get("removedMentions") or 0),
                        },
                    )
                    upload_live_checkpoint(job_id, reason="target-backfill-cleanup", force=True)

                backfill = backfill_missing_target_mentions(db_path(), list(spec["target_keys"]))
                if backfill.get("updatedCount"):
                    labels = target_labels()
                    labels.update(target_labels_from_spec(spec))
                    totals["mentions_inserted"] += int(backfill.get("mentionsInserted") or 0)
                    totals["stories_touched"] += int(backfill.get("storiesTouched") or 0)
                    for item in list(backfill.get("updated") or [])[:100]:
                        target_key = str(item.get("target_key") or "")
                        append_event(
                            job_id,
                            "article_saved",
                            {
                                "article_id": int(item.get("article_id") or 0),
                                "story_id": int(item.get("story_id") or 0),
                                "url": str(item.get("url") or ""),
                                "title": str(item.get("title") or ""),
                                "published_at": str(item.get("published_at") or ""),
                                "source_name": str(item.get("source_name") or ""),
                                "source_type": str(item.get("source_type") or ""),
                                "target_keys": [target_key] if target_key else [],
                                "target_key": target_key,
                                "target_label": labels.get(target_key, target_key),
                                "articles_inserted_delta": 0,
                                "mentions_inserted_delta": 1,
                                "stories_touched_delta": 1,
                                "publication_state": "saved",
                                "reason": "existing_article_backfill",
                            },
                        )
                    append_event(
                        job_id,
                        "target_backfill_complete",
                        {
                            "target_keys": list(spec["target_keys"]),
                            "mentions_inserted": totals["mentions_inserted"],
                            "stories_touched": totals["stories_touched"],
                        },
                    )
                    update_job(job_id, **totals)
                    upload_live_checkpoint(job_id, reason="target-backfill", force=True)

                if spec.get("durable"):
                    durable_result = run_durable_update(job_id, spec, cancel_event)
                    totals["articles_inserted"] += int(durable_result.get("articles_inserted") or 0)
                    totals["mentions_inserted"] += int(durable_result.get("mentions_inserted") or 0)
                    totals["stories_touched"] += int(durable_result.get("stories_touched") or 0)
                    coverage_state = str(durable_result.get("coverage_state") or "")
                    update_job(job_id, **totals)
                    if durable_result.get("failed_sources"):
                        update_job(
                            job_id,
                            status="failed_needs_fix",
                            finished_at=datetime.now(timezone.utc).isoformat(),
                            error_message="Uma ou mais fontes precisam de correção antes da cobertura completa.",
                            **totals,
                        )
                        append_event(
                            job_id,
                            "coverage_failed",
                            {
                                "status": "failed_needs_fix",
                                "count": len(durable_result.get("failed_sources") or []),
                            },
                        )
                        publish_incremental_snapshot(job_id, reason="failed-needs-fix", force=True)
                        uploaded = self.store.upload_current_artifacts(
                            manifest={
                                "jobId": job_id,
                                "kind": kind,
                                "spec": {k: v for k, v in spec.items() if k not in {"error"}},
                                "totals": totals,
                                "coverageState": coverage_state or "failed_needs_fix",
                                "finishedAt": datetime.now(timezone.utc).isoformat(),
                            },
                            job_id=job_id,
                        )
                        append_event(job_id, "artifacts_uploaded", artifact_upload_summary(uploaded))
                        return
                else:
                    labels = target_labels()
                    labels.update(target_labels_from_spec(spec))
                    for target_key in spec["target_keys"]:
                        if cancel_event.is_set():
                            return
                        target_label = labels.get(target_key, target_key)
                        options = IngestionOptions(
                            target_keys=[target_key],
                            target_snapshots=[target_to_snapshot(target) for target in selected_targets_from_spec(spec, [target_key])],
                            date_from=spec["date_from"],
                            date_to=spec["date_to"],
                            request_timeout_seconds=10,
                            skip_direct_scrape=True,
                            max_candidates_per_source=int(spec["max_candidates"]),
                            max_process_seconds=int(spec["max_process_seconds"]),
                            db_path=str(db_path()),
                            cancel_check=cancel_event.is_set,
                            archive_full_text=bool(spec.get("archive_full_text", True)),
                            archive_raw_html=bool(spec.get("archive_raw_html", True)),
                            full_text_max_chars=safe_positive_int(spec.get("full_text_max_chars"), 60000, minimum=0),
                            raw_html_max_chars=safe_positive_int(spec.get("raw_html_max_chars"), 120000, minimum=0),
                            candidate_workers=effective_candidate_workers(spec),
                        )
                        results = run_ingestion(
                            spec["collector"],
                            options=options,
                            progress_callback=lambda event, data, jid=job_id, tk=target_key, tl=target_label: record_progress(
                                jid,
                                event,
                                data,
                                target_key=tk,
                                target_label=tl,
                            ),
                        )
                        totals["articles_inserted"] += sum(r.articles_inserted for r in results)
                        totals["mentions_inserted"] += sum(r.mentions_inserted for r in results)
                        totals["stories_touched"] += sum(r.stories_touched for r in results)
                        update_job(job_id, **totals)
                        if cancel_event.is_set():
                            return

            if cancel_event.is_set():
                return
            if spec.get("export"):
                if kind == "export":
                    cleanup = cleanup_false_backfilled_target_mentions(db_path(), active_secondary_target_keys())
                    if cleanup.get("removedMentions"):
                        append_event(
                            job_id,
                            "target_backfill_cleanup",
                            {
                                "target_keys": active_secondary_target_keys(),
                                "mentions_inserted": 0,
                                "stories_touched": int(cleanup.get("storiesTouched") or 0),
                                "count": int(cleanup.get("removedMentions") or 0),
                            },
                        )
                update_job(job_id, status="exporting", **totals)
                run_export_snapshot(job_id)

            if cancel_event.is_set():
                return
            manifest = {
                "jobId": job_id,
                "kind": kind,
                "spec": {k: v for k, v in spec.items() if k not in {"error"}},
                "totals": totals,
                "coverageState": coverage_state or source_coverage_state(job_id),
                "finishedAt": datetime.now(timezone.utc).isoformat(),
            }
            update_job(job_id, status="succeeded", finished_at=manifest["finishedAt"], **totals)
            uploaded = self.store.upload_current_artifacts(manifest=manifest, job_id=job_id)
            append_event(job_id, "artifacts_uploaded", artifact_upload_summary(uploaded))
        except Exception as exc:
            if cancel_event.is_set():
                return
            update_job(
                job_id,
                status="failed",
                finished_at=datetime.now(timezone.utc).isoformat(),
                error_message=sanitize_error(exc),
            )
            append_event(job_id, "job_failed", {"error": sanitize_error(exc)})
        finally:
            with self._lock:
                if self._active_job_id == job_id:
                    self._active_job_id = None
                self._cancel_events.pop(job_id, None)


def build_update_spec(payload: dict[str, Any]) -> dict[str, Any]:
    preset = str(payload.get("preset") or "rapido").strip()
    today = date.today()
    max_candidates = CUSTOM_MAX_CANDIDATES
    max_process_seconds = CUSTOM_MAX_PROCESS_SECONDS
    topic_config = resolve_rio_topic_request(payload)

    if topic_config is not None:
        config = topic_config
        date_from_raw = str(payload.get("date_from") or payload.get("dateFrom") or "")
        date_to_raw = str(payload.get("date_to") or payload.get("dateTo") or "")
        date_from = validate_date(date_from_raw) if date_from_raw else (today - timedelta(days=30)).isoformat()
        date_to = validate_date(date_to_raw) if date_to_raw else today.isoformat()
        collector = str(payload.get("collector") or DEFAULT_COLLECTOR).strip() or DEFAULT_COLLECTOR
        target_keys = [RIO_ECONOMICO_SCOPE]
        target_snapshots = [rio_topic_target_snapshot(config)]
        preset = "rio_tourism" if config.topic == RIO_TOURISM_TOPIC else config.topic
        topic_queries = [dict(row) for row in config.queries]
        topic_source_queries = rio_topic_source_query_texts(config)
        forced_terms = list(config.forced_terms)
        required_terms = list(config.required_terms)
        exclude_title_terms = list(config.exclude_title_terms)
        exclude_body_terms = list(config.exclude_body_terms)
    elif preset in PRESETS:
        preset_spec = PRESETS[preset]
        target_keys = validate_target_keys(list(preset_spec["target_keys"]))
        date_from = (today - timedelta(days=int(preset_spec["days"]))).isoformat()
        date_to = today.isoformat()
        max_candidates = int(preset_spec["max_candidates"])
        max_process_seconds = int(preset_spec["max_process_seconds"])
        target_snapshots = frozen_target_snapshots(target_keys)
        topic_queries = []
        topic_source_queries = []
        forced_terms = []
        required_terms = []
        exclude_title_terms = []
        exclude_body_terms = []
    elif preset == "custom":
        target_keys = validate_target_keys(payload_list(payload, "target_keys", "targetKeys"))
        date_from = validate_date(str(payload.get("date_from") or payload.get("dateFrom") or ""))
        date_to = validate_date(str(payload.get("date_to") or payload.get("dateTo") or ""))
        collector = str(payload.get("collector") or DEFAULT_COLLECTOR).strip() or DEFAULT_COLLECTOR
        target_snapshots = frozen_target_snapshots(target_keys)
        topic_queries = []
        topic_source_queries = []
        forced_terms = []
        required_terms = []
        exclude_title_terms = []
        exclude_body_terms = []
    else:
        raise ValueError("preset_invalido")

    if preset not in {"custom", "rio_tourism", RIO_CITY_TOPIC}:
        collector = DEFAULT_COLLECTOR
    if collector not in SAFE_COLLECTORS:
        raise ValueError("coletor_invalido")
    if date_from > date_to:
        raise ValueError("periodo_invalido")

    spec = {
        "preset": preset,
        "collector": collector,
        "target_keys": target_keys,
        "target_snapshots": target_snapshots,
        "date_from": date_from,
        "date_to": date_to,
        "export": bool(payload.get("export", True)),
        "max_candidates": max_candidates,
        "max_process_seconds": max_process_seconds,
        "candidate_workers": DEFAULT_CANDIDATE_WORKERS,
        "skip_direct_scrape": True,
        "durable": True,
    }
    if topic_queries:
        config = topic_config or load_rio_topic_config(RIO_CITY_TOPIC)
        spec.update(
            {
                "scope": RIO_ECONOMICO_SCOPE,
                "topic": config.topic,
                "topic_dimension": config.dimension,
                "topic_config_version": config.version,
                "topic_queries": topic_queries,
                "topic_source_queries": topic_source_queries,
                "candidate_worker_limit": RIO_CANDIDATE_WORKER_LIMIT,
                "wordpress_pages_per_slice": RIO_WORDPRESS_PAGES_PER_SLICE,
                "wordpress_max_pages": WORDPRESS_MAX_PAGES,
                "wordpress_soft_fail_after_page": RIO_WORDPRESS_SOFT_FAIL_AFTER_PAGE,
                "group_topic_queries_by_source": config.topic == RIO_CITY_TOPIC,
                "topic_query_chunk_size": RIO_TOPIC_QUERY_CHUNK_SIZE if config.topic == RIO_CITY_TOPIC else 1,
                "recent_archive_max_pages": RIO_RECENT_ARCHIVE_MAX_PAGES,
                "archive_full_text": True,
                "archive_raw_html": False,
                "full_text_max_chars": RIO_FULL_TEXT_MAX_CHARS,
                "raw_html_max_chars": RIO_RAW_HTML_MAX_CHARS,
                "forced_terms": forced_terms,
                "forced_terms_mode": "any",
                "required_terms": required_terms,
                "exclude_title_terms": exclude_title_terms,
                "exclude_body_terms": exclude_body_terms,
            }
        )
    return spec


def validate_date(raw: str) -> str:
    try:
        value = date.fromisoformat(raw)
    except Exception as exc:
        raise ValueError("data_invalida") from exc
    if value > date.today():
        raise ValueError("data_futura")
    return value.isoformat()


def payload_list(payload: dict[str, Any], snake_key: str, camel_key: str) -> list[str]:
    value = payload.get(snake_key)
    if value is None:
        value = payload.get(camel_key)
    return value if isinstance(value, list) else []


def target_field(target: Any, key: str, default: Any = "") -> Any:
    if isinstance(target, dict):
        return target.get(key, default)
    return getattr(target, key, default)


def target_to_snapshot(target: Any) -> dict[str, Any]:
    return {
        "key": str(target_field(target, "key", "") or ""),
        "label": str(target_field(target, "label", "") or ""),
        "display_name": str(target_field(target, "display_name", "") or ""),
        "keywords": [str(item) for item in (target_field(target, "keywords", None) or []) if str(item).strip()],
        "exact_aliases": [
            str(item)
            for item in (target_field(target, "exact_aliases", None) or target_field(target, "exactAliases", None) or [])
            if str(item).strip()
        ],
        "className": str(target_field(target, "className", "") or target_field(target, "class_name", "") or ""),
        "primary": bool(target_field(target, "primary", False)),
        "priority": int(target_field(target, "priority", 2) or 2),
    }


def target_from_snapshot(row: dict[str, Any]) -> Target:
    return Target(
        key=str(row.get("key") or ""),
        label=str(row.get("label") or row.get("display_name") or row.get("key") or ""),
        display_name=str(row.get("display_name") or row.get("label") or row.get("key") or ""),
        keywords=[str(item) for item in (row.get("keywords") or []) if str(item).strip()],
        exact_aliases=[str(item) for item in (row.get("exact_aliases") or []) if str(item).strip()],
        className=str(row.get("className") or row.get("class_name") or ""),
        primary=bool(row.get("primary")),
        priority=int(row.get("priority") or 2),
    )


def frozen_target_snapshots(target_keys: list[str]) -> list[dict[str, Any]]:
    return [target_to_snapshot(target) for target in select_targets(get_active_targets(), target_keys)]


def targets_from_spec(spec: dict[str, Any]) -> list[Target]:
    snapshots = spec.get("target_snapshots") or spec.get("targetSnapshots") or []
    if isinstance(snapshots, list) and snapshots:
        targets: list[Target] = []
        for row in snapshots:
            if isinstance(row, dict) and str(row.get("key") or "").strip():
                targets.append(target_from_snapshot(row))
        if targets:
            return targets
    return get_active_targets()


def selected_targets_from_spec(spec: dict[str, Any], target_keys: list[str]) -> list[Target]:
    return select_targets(targets_from_spec(spec), target_keys)


def target_labels_from_spec(spec: dict[str, Any]) -> dict[str, str]:
    return {
        target.key: target.display_name or target.label or target.key
        for target in targets_from_spec(spec)
        if str(target.key or "").strip()
    }


def active_secondary_target_keys() -> list[str]:
    primary = set(primary_target_keys())
    keys: list[str] = []
    for row in load_targets():
        key = str(row.get("key") or "").strip()
        if not key or key in primary or bool(row.get("archived")):
            continue
        keys.append(key)
    return keys


def run_export_snapshot(job_id: str | None = None) -> None:
    export_db_path = validate_configured_db_file(db_path())
    cmd = [
        sys.executable,
        "tools/export_mobile_snapshot.py",
        "--all-stories",
        "--merge-from",
        "index.html",
        "--db",
        str(export_db_path),
    ]
    # OOM mitigation (2026-05-22): pipe stdout/stderr to DEVNULL instead of
    # capturing. capture_output=True buffered the entire child output in the
    # parent process, doubling memory pressure during exports of 460+ stories
    # / 780+ articles. The child prints progress lines that we never used
    # except for a count log — replaced by a synthetic ok/fail marker.
    # See WORK_LOG_MAJOR.md "OOMs são CRÔNICOS" (2026-05-21).
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=EXPORT_TIMEOUT_SECONDS,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("export_failed")
    if job_id:
        append_event(job_id, "export_complete", {"returncode": completed.returncode})


def run_durable_update(job_id: str, spec: dict[str, Any], cancel_event: threading.Event) -> dict[str, Any]:
    ensure_app_tables(db_path())
    labels = target_labels()
    labels.update(target_labels_from_spec(spec))
    totals = {"articles_inserted": 0, "mentions_inserted": 0, "stories_touched": 0}
    if grouped_source_runs_enabled(spec):
        target_keys = update_spec_target_keys(spec)
        ensure_grouped_source_runs(job_id, spec)
        target_label = f"{len(target_keys)} targets selecionados"
        while not cancel_event.is_set():
            row = next_pending_source_run(job_id, GROUPED_SOURCE_RUN_TARGET_KEY)
            if not row:
                break
            result = run_source_run(job_id, spec, row, target_label=target_label, cancel_event=cancel_event)
            for key in totals:
                totals[key] += int(result.get(key) or 0)
            update_job(job_id, **totals)
            if result.get("saved"):
                publish_incremental_snapshot(job_id, reason="source-run-saved")
                upload_live_checkpoint(job_id, reason="source-run-saved-checkpoint", force=True)
            else:
                upload_live_checkpoint(job_id, reason="source-run-checkpoint")
            cooperative_source_run_yield(cancel_event)
    else:
        for target_key in list(spec.get("target_keys") or []):
            if cancel_event.is_set():
                break
            target_label = labels.get(target_key, target_key)
            ensure_source_runs(job_id, spec, str(target_key))
            while not cancel_event.is_set():
                row = next_pending_source_run(job_id, str(target_key))
                if not row:
                    break
                result = run_source_run(job_id, spec, row, target_label=target_label, cancel_event=cancel_event)
                for key in totals:
                    totals[key] += int(result.get(key) or 0)
                update_job(job_id, **totals)
                if result.get("saved"):
                    publish_incremental_snapshot(job_id, reason="source-run-saved")
                    upload_live_checkpoint(job_id, reason="source-run-saved-checkpoint", force=True)
                else:
                    upload_live_checkpoint(job_id, reason="source-run-checkpoint")
                cooperative_source_run_yield(cancel_event)
    if cancel_event.is_set():
        return {**totals, "coverage_state": "cancel_requested", "failed_sources": []}
    failed = failed_source_runs(job_id)
    coverage = source_coverage_state(job_id)
    append_event(
        job_id,
        "coverage_summary",
        {
            "coverage_state": coverage,
            "status": coverage,
            "count": len(failed),
        },
    )
    publish_incremental_snapshot(job_id, reason="coverage-complete", force=True)
    return {**totals, "coverage_state": coverage, "failed_sources": failed}


def ensure_source_runs(job_id: str, spec: dict[str, Any], target_key: str) -> None:
    units = build_source_units(spec, target_key)
    ensure_source_run_units(job_id, target_key, units)


def ensure_grouped_source_runs(job_id: str, spec: dict[str, Any]) -> None:
    units = build_grouped_source_units(spec)
    legacy_rows_removed = 0
    with connect(db_path()) as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM job_source_runs
            WHERE job_id = ? AND target_key != ?
            """,
            (job_id, GROUPED_SOURCE_RUN_TARGET_KEY),
        ).fetchone()
        legacy_rows_removed = int(row["count"] if row else 0)
        if legacy_rows_removed:
            conn.execute("DELETE FROM job_source_runs WHERE job_id = ?", (job_id,))
    if legacy_rows_removed:
        append_event(
            job_id,
            "source_run_ledger_migrated",
            {
                "status": "complete",
                "reason": "multi_target_grouped_source_runs",
                "source_run_mode": "grouped",
                "legacy_source_runs_removed": legacy_rows_removed,
                "source_runs_inserted": len(units),
                "target_count": len(update_spec_target_keys(spec)),
                "target_keys": update_spec_target_keys(spec),
            },
        )
    ensure_source_run_units(job_id, GROUPED_SOURCE_RUN_TARGET_KEY, units)


def ensure_source_run_units(job_id: str, target_key: str, units: list[SourceUnit]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with connect(db_path()) as conn:
        active_keys = {unit.source_key for unit in units}
        placeholders = ",".join("?" for _ in active_keys)
        if active_keys:
            conn.execute(
                f"""
                UPDATE job_source_runs
                SET status = 'complete',
                    last_error = 'Fonte removida ou desativada na configuração ativa.',
                    updated_at = ?,
                    finished_at = COALESCE(finished_at, ?)
                WHERE job_id = ?
                  AND target_key = ?
                  AND status != 'complete'
                  AND source_key NOT IN ({placeholders})
                """,
                (now, now, job_id, target_key, *sorted(active_keys)),
            )
        else:
            conn.execute(
                """
                UPDATE job_source_runs
                SET status = 'complete',
                    last_error = 'Nenhuma fonte ativa para este coletor.',
                    updated_at = ?,
                    finished_at = COALESCE(finished_at, ?)
                WHERE job_id = ?
                  AND target_key = ?
                  AND status != 'complete'
                """,
                (now, now, job_id, target_key),
            )
        for unit in units:
            conn.execute(
                """
                INSERT OR IGNORE INTO job_source_runs (
                    job_id, target_key, source_key, source_name, source_type, status,
                    cursor_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    target_key,
                    unit.source_key,
                    unit.source_name,
                    unit.source_type,
                    "pending",
                    json.dumps(unit.cursor, ensure_ascii=False),
                    now,
                ),
            )


def build_source_units(spec: dict[str, Any], target_key: str) -> list[SourceUnit]:
    targets = selected_targets_from_spec(spec, [target_key])
    return build_source_units_for_targets(spec, targets, grouped=False)


def build_grouped_source_units(spec: dict[str, Any]) -> list[SourceUnit]:
    targets = selected_targets_from_spec(spec, update_spec_target_keys(spec))
    return build_source_units_for_targets(spec, targets, grouped=True)


def build_source_units_for_targets(spec: dict[str, Any], targets: list[Target], *, grouped: bool) -> list[SourceUnit]:
    collector = str(spec.get("collector") or DEFAULT_COLLECTOR)
    if not targets:
        return []
    topic_mode = is_rio_topic_spec(spec)
    group_topic_queries = rio_city_query_grouping_enabled(spec)
    units: list[SourceUnit] = []
    order = 0

    def include(source_type: str) -> bool:
        return collector == "all" or collector == source_type or (collector == "internal_search" and source_type == "internal_search")

    if include("rss"):
        for idx, feed in enumerate(RSS_FEEDS):
            if str(feed.get("disabled") or "").strip().lower() in {"1", "true", "yes"}:
                continue
            units.append(
                SourceUnit(
                    source_key=f"rss:{idx}",
                    source_name=str(feed.get("source_name") or f"RSS {idx + 1}"),
                    source_type="rss",
                    cursor={"feed_index": idx},
                    order=order,
                )
            )
            order += 1

    if include("google_news"):
        google_queries = topic_queries_from_spec(spec, source_type="google_news") if topic_mode else build_google_queries_for_targets(targets)
        if grouped or group_topic_queries:
            chunks = chunk_queries(google_queries, topic_query_chunk_size(spec) if group_topic_queries else len(google_queries))
            for chunk_idx, query_chunk in enumerate(chunks):
                units.append(
                    SourceUnit(
                        source_key="google_news:0" if grouped and not group_topic_queries else f"google_news:chunk:{chunk_idx}",
                        source_name="Google News",
                        source_type="google_news",
                        cursor={"query_index": chunk_idx * max(1, topic_query_chunk_size(spec)), "queries": query_chunk},
                        order=order,
                    )
                )
                order += 1
        else:
            for idx, query in enumerate(google_queries):
                units.append(
                    SourceUnit(
                        source_key=f"google_news:{idx}",
                        source_name="Google News",
                        source_type="google_news",
                        cursor={"query_index": idx, "query": query},
                        order=order,
                    )
                )
                order += 1

    if include("wordpress_api"):
        for site_idx, site in enumerate(WORDPRESS_API_SITES):
            site_name = str(site.get("source_name") or "WordPress").strip() or "WordPress"
            if rio_city_wordpress_date_scan_enabled(spec, site):
                units.append(
                    SourceUnit(
                        source_key=f"wordpress_api_{WORDPRESS_SOURCE_VERSION}:{site_idx}:date_scan",
                        source_name=site_name,
                        source_type="wordpress_api",
                        cursor={
                            "site_index": site_idx,
                            "date_scan": True,
                            "page": 1,
                            "page_size": WORDPRESS_PAGE_SIZE,
                        },
                        order=order,
                    )
                )
                order += 1
                continue
            site_queries = topic_queries_from_spec(spec, source_type="wordpress_api") if topic_mode else build_wordpress_queries_for_targets(targets, site=site)
            if grouped or group_topic_queries:
                chunks = chunk_queries(site_queries, topic_query_chunk_size(spec) if group_topic_queries else len(site_queries))
                for chunk_idx, query_chunk in enumerate(chunks):
                    query_index = chunk_idx * max(1, topic_query_chunk_size(spec))
                    units.append(
                        SourceUnit(
                            source_key=(
                                f"wordpress_api_{WORDPRESS_SOURCE_VERSION}:{site_idx}:all"
                                if grouped and not group_topic_queries
                                else f"wordpress_api_{WORDPRESS_SOURCE_VERSION}:{site_idx}:chunk:{chunk_idx}"
                            ),
                            source_name=site_name,
                            source_type="wordpress_api",
                            cursor={
                                "site_index": site_idx,
                                "query_index": query_index,
                                "queries": query_chunk,
                                "query_chunk_index": chunk_idx,
                                "page": 1,
                                "page_size": WORDPRESS_PAGE_SIZE,
                                "complete_queries": [],
                            },
                            order=order,
                        )
                    )
                    order += 1
            else:
                for query_idx, query in enumerate(site_queries):
                    units.append(
                        SourceUnit(
                            source_key=f"wordpress_api_{WORDPRESS_SOURCE_VERSION}:{site_idx}:{query_idx}",
                            source_name=site_name,
                            source_type="wordpress_api",
                            cursor={
                                "site_index": site_idx,
                                "query_index": query_idx,
                                "query": query,
                                "page": 1,
                                "page_size": WORDPRESS_PAGE_SIZE,
                            },
                            order=order,
                        )
                    )
                    order += 1

    if include("internal_search"):
        queries = topic_queries_from_spec(spec, source_type="internal_search") if topic_mode else build_internal_search_queries_for_targets(targets)
        for adapter_idx, adapter in enumerate(FLAVIO_INTERNAL_SEARCH_TARGETS):
            page_size = max(1, int(getattr(adapter, "page_size", 10) or 10))
            if grouped or group_topic_queries:
                chunks = chunk_queries(queries, topic_query_chunk_size(spec) if group_topic_queries else len(queries))
                for chunk_idx, query_chunk in enumerate(chunks):
                    query_index = chunk_idx * max(1, topic_query_chunk_size(spec))
                    units.append(
                        SourceUnit(
                            source_key=(
                                f"internal_search_{INTERNAL_SEARCH_SOURCE_VERSION}:{adapter_idx}:all"
                                if grouped and not group_topic_queries
                                else f"internal_search_{INTERNAL_SEARCH_SOURCE_VERSION}:{adapter_idx}:chunk:{chunk_idx}"
                            ),
                            source_name=str(adapter.source_name),
                            source_type="internal_search",
                            cursor={
                                "adapter_index": adapter_idx,
                                "query_index": query_index,
                                "queries": query_chunk,
                                "query_chunk_index": chunk_idx,
                                "page": 1,
                                "page_size": page_size,
                            },
                            order=order,
                        )
                    )
                    order += 1
            else:
                for query_idx, query in enumerate(queries):
                    units.append(
                        SourceUnit(
                            source_key=f"internal_search_{INTERNAL_SEARCH_SOURCE_VERSION}:{adapter_idx}:{query_idx}",
                            source_name=str(adapter.source_name),
                            source_type="internal_search",
                            cursor={
                                "adapter_index": adapter_idx,
                                "query_index": query_idx,
                                "query": query,
                                "page": 1,
                                "page_size": page_size,
                            },
                            order=order,
                        )
                    )
                    order += 1

    if include("sitemap_daily"):
        days = source_window_days(str(spec.get("date_from") or ""), str(spec.get("date_to") or ""))
        queries = topic_queries_from_spec(spec, source_type="sitemap_daily") if topic_mode else build_internal_search_queries_for_targets(targets)
        for source_idx, source in enumerate(SITEMAP_DAILY_SOURCES):
            for day_idx, day in enumerate(days):
                units.append(
                    SourceUnit(
                        source_key=f"sitemap_daily:{source_idx}:{day}",
                        source_name=str(source.get("source_name") or "Sitemap Daily"),
                        source_type="sitemap_daily",
                        cursor={"source_index": source_idx, "day_index": day_idx, "day": day, "queries": queries},
                        order=order,
                    )
                )
                order += 1

    if include("vejario_archive"):
        max_pages = archive_page_limit(spec, VEJARIO_MAX_PAGES)
        for target_idx, archive_target in enumerate(VEJARIO_ARCHIVE_TARGETS):
            for page in range(1, max_pages + 1):
                units.append(
                    SourceUnit(
                        source_key=f"vejario_archive:{target_idx}:{page}",
                        source_name=str(archive_target.get("source_name") or "Veja Rio Archive"),
                        source_type="vejario_archive",
                        cursor={"target_index": target_idx, "page": page},
                        order=order,
                    )
                )
                order += 1

    if include("camara_archive"):
        max_pages = archive_page_limit(spec, CAMARA_MAX_PAGES)
        for page in range(1, max_pages + 1):
            units.append(
                SourceUnit(
                    source_key=f"camara_archive:0:{page}",
                    source_name=str(CAMARA_ARCHIVE_TARGET.get("source_name") or "Camara Rio Archive"),
                    source_type="camara_archive",
                    cursor={"page": page},
                    order=order,
                )
            )
            order += 1

    return units


def grouped_source_runs_enabled(spec: dict[str, Any]) -> bool:
    return len(update_spec_target_keys(spec)) > 1


def update_spec_target_keys(spec: dict[str, Any]) -> list[str]:
    return ordered_unique([str(item or "").strip() for item in list(spec.get("target_keys") or []) if str(item or "").strip()])


def build_google_queries_for_targets(targets: list[Target]) -> list[str]:
    queries: list[str] = []
    for target in targets:
        queries.extend(build_google_queries_for_target(target))
    return ordered_unique(queries)


def build_wordpress_queries_for_targets(targets: list[Target], *, site: dict[str, Any]) -> list[str]:
    queries: list[str] = []
    site_queries = site.get("query_variants")
    for target in targets:
        if target.key == "flavio_valle" and isinstance(site_queries, list):
            queries.extend([str(item or "").strip() for item in site_queries if str(item or "").strip()])
        else:
            queries.extend(build_wordpress_queries_for_target(target))
    return ordered_unique(queries)


def build_internal_search_queries_for_targets(targets: list[Target]) -> list[str]:
    queries: list[str] = []
    for target in targets:
        queries.extend(build_internal_search_queries_for_target(target))
    return ordered_unique(queries)


def source_window_days(date_from: str, date_to: str) -> list[str]:
    try:
        start = date.fromisoformat(date_from)
    except Exception:
        start = date.today() - timedelta(days=7)
    try:
        end = date.fromisoformat(date_to)
    except Exception:
        end = date.today()
    if start > end:
        start, end = end, start
    days: list[str] = []
    current = start
    while current <= end:
        days.append(current.isoformat())
        current += timedelta(days=1)
    return days


def next_pending_source_run(job_id: str, target_key: str) -> dict[str, Any] | None:
    with connect(db_path()) as conn:
        row = conn.execute(
            """
            SELECT * FROM job_source_runs
            WHERE job_id = ? AND target_key = ? AND status IN ('pending', 'retrying', 'interrupted_resumable')
            ORDER BY CASE WHEN source_key LIKE '%:date_scan' THEN 0 ELSE 1 END, id ASC
            LIMIT 1
            """,
            (job_id, target_key),
        ).fetchone()
    return dict(row) if row else None


def run_source_run(
    job_id: str,
    spec: dict[str, Any],
    row: dict[str, Any],
    *,
    target_label: str,
    cancel_event: threading.Event,
) -> dict[str, Any]:
    source_run_id = int(row["id"])
    target_key = str(row["target_key"])
    source_target_keys = source_run_target_keys(spec, row)
    source_name = str(row["source_name"])
    source_type = str(row["source_type"])
    cursor = safe_json_dict(row.get("cursor_json"))
    mark_source_run_running(source_run_id)
    # OOM diagnosis (2026-05-22): snapshot RSS antes do source_run para
    # rastrear quais sources elevam memória durante update jobs.
    try:
        from .diagnostics import rss_mib
        rss_before = rss_mib()
    except Exception:
        rss_before = 0.0
    append_event(
        job_id,
        "source_run_started",
        {
            "source_name": source_name,
            "source_type": source_type,
            "target_key": target_key,
            "target_label": target_label,
            "target_keys": source_target_keys,
            "status": "running",
            "rss_mib_before": rss_before,
        },
    )
    candidates: list[CandidateArticle] = []
    candidate_total = 0
    try:
        candidates, next_cursor, complete = collect_source_run_candidates(spec, row, cursor)
        candidate_total = len(candidates)
        if cancel_event.is_set():
            mark_source_run_interrupted(source_run_id, reason="cancel_requested")
            return {"articles_inserted": 0, "mentions_inserted": 0, "stories_touched": 0, "saved": False}
        record_progress(
            job_id,
            "source_collected",
            {
                "source_name": source_name,
                "source_type": source_type,
                "candidates_total": candidate_total,
                "target_keys": source_target_keys,
            },
            target_key=target_key,
            target_label=target_label,
        )
        source_targets = selected_targets_from_spec(spec, source_target_keys)
        metadata_extra = topic_query_meta(spec) if is_rio_topic_spec(spec) else {}
        options = IngestionOptions(
            target_keys=source_target_keys,
            target_snapshots=[target_to_snapshot(target) for target in source_targets],
            date_from=str(spec.get("date_from") or ""),
            date_to=str(spec.get("date_to") or ""),
            request_timeout_seconds=10,
            skip_direct_scrape=True,
            max_candidates_per_source=max(1, int(spec.get("max_candidates") or CUSTOM_MAX_CANDIDATES)),
            max_process_seconds=max(10, int(spec.get("max_process_seconds") or CUSTOM_MAX_PROCESS_SECONDS)),
            db_path=str(db_path()),
            cancel_check=cancel_event.is_set,
            archive_full_text=bool(spec.get("archive_full_text", True)),
            archive_raw_html=bool(spec.get("archive_raw_html", True)),
            full_text_max_chars=safe_positive_int(spec.get("full_text_max_chars"), 60000, minimum=0),
            raw_html_max_chars=safe_positive_int(spec.get("raw_html_max_chars"), 120000, minimum=0),
            forced_terms=list(spec.get("forced_terms") or []),
            forced_terms_mode=str(spec.get("forced_terms_mode") or "any"),
            required_terms=list(spec.get("required_terms") or []),
            exclude_title_terms=list(spec.get("exclude_title_terms") or []),
            exclude_body_terms=list(spec.get("exclude_body_terms") or []),
            metadata_extra=metadata_extra,
            candidate_workers=effective_candidate_workers(spec),
        )
        if source_type == "google_news" and target_key == GROUPED_SOURCE_RUN_TARGET_KEY:
            record_progress(
                job_id,
                "source_progress",
                {
                    "source_name": source_name,
                    "source_type": source_type,
                    "candidates_total": candidate_total,
                    "candidates_seen": candidate_total,
                    "articles_inserted": 0,
                    "mentions_inserted": 0,
                    "stories_touched": 0,
                    "status": "google_news_grouped_circuit_breaker",
                    "reason": "skip_google_news_full_ingest_for_grouped_backfill",
                    "target_keys": source_target_keys,
                },
                target_key=target_key,
                target_label=target_label,
            )
            result = SimpleNamespace(
                candidates_seen=candidate_total,
                articles_inserted=0,
                mentions_inserted=0,
                stories_touched=0,
                errors=[],
            )
        else:
            result = process_candidates(
                source_name,
                source_type,
                candidates,
                options=options,
                progress_callback=lambda event, data, jid=job_id, tk=target_key, tl=target_label, tks=source_target_keys, sri=source_run_id, sk=str(row.get("source_key") or ""): record_progress(
                    jid,
                    event,
                    {**data, "target_keys": list(tks), "source_run_id": sri, "source_key": sk},
                    target_key=tk,
                    target_label=tl,
                ),
            )
        if cancel_event.is_set():
            mark_source_run_interrupted(source_run_id, reason="cancel_requested")
            return {
                "articles_inserted": result.articles_inserted,
                "mentions_inserted": result.mentions_inserted,
                "stories_touched": result.stories_touched,
                "saved": bool(result.articles_inserted or result.mentions_inserted or result.stories_touched),
            }
        next_status = "complete" if complete else "pending"
        update_source_run(
            source_run_id,
            status=next_status,
            cursor=next_cursor,
            candidates_seen=result.candidates_seen,
            candidates_total=candidate_total,
            articles_inserted=result.articles_inserted,
            mentions_inserted=result.mentions_inserted,
            stories_touched=result.stories_touched,
            last_error="",
            finished=complete,
        )
        try:
            from .diagnostics import rss_mib
            rss_after = rss_mib()
        except Exception:
            rss_after = 0.0
        completion_payload = {
            "source_name": source_name,
            "source_type": source_type,
            "target_key": target_key,
            "target_label": target_label,
            "target_keys": source_target_keys,
            "candidates_seen": result.candidates_seen,
            "candidates_total": candidate_total,
            "articles_inserted": result.articles_inserted,
            "mentions_inserted": result.mentions_inserted,
            "stories_touched": result.stories_touched,
            "status": next_status,
            "rss_mib_before": rss_before,
            "rss_mib_after": rss_after,
            "rss_mib_delta": round(rss_after - rss_before, 2),
        }
        if next_cursor.get("soft_error"):
            completion_payload["soft_error"] = str(next_cursor.get("soft_error") or "")
            completion_payload["soft_error_at"] = str(next_cursor.get("soft_error_at") or "")
        append_event(
            job_id,
            "source_run_complete" if complete else "source_run_checkpoint",
            completion_payload,
        )
        return {
            "articles_inserted": result.articles_inserted,
            "mentions_inserted": result.mentions_inserted,
            "stories_touched": result.stories_touched,
            "saved": bool(result.articles_inserted or result.mentions_inserted or result.stories_touched),
        }
    except Exception as exc:
        message = sanitize_error(exc)
        update_source_run(
            source_run_id,
            status="failed_needs_fix",
            cursor=cursor,
            last_error=message,
            finished=True,
        )
        append_event(
            job_id,
            "source_run_failed",
            {
                "source_name": source_name,
                "source_type": source_type,
                "target_key": target_key,
                "target_label": target_label,
                "target_keys": source_target_keys,
                "status": "failed_needs_fix",
                "error": message,
            },
        )
        return {"articles_inserted": 0, "mentions_inserted": 0, "stories_touched": 0, "saved": False}
    finally:
        candidates.clear()
        gc.collect()


def source_run_target_keys(spec: dict[str, Any], row: dict[str, Any]) -> list[str]:
    row_target_key = str(row.get("target_key") or "").strip()
    if row_target_key == GROUPED_SOURCE_RUN_TARGET_KEY:
        return update_spec_target_keys(spec)
    return [row_target_key] if row_target_key else []


def collect_source_run_candidates(
    spec: dict[str, Any],
    row: dict[str, Any],
    cursor: dict[str, Any],
) -> tuple[list[CandidateArticle], dict[str, Any], bool]:
    source_type = str(row["source_type"])
    request_timeout = 10
    date_from = str(spec.get("date_from") or "")
    date_to = str(spec.get("date_to") or "")
    max_candidates = max(1, int(spec.get("max_candidates") or CUSTOM_MAX_CANDIDATES))

    if source_type == "rss":
        feed = RSS_FEEDS[max(0, int(cursor.get("feed_index") or 0))]
        candidates = collect_rss(
            feeds=[feed],
            limit_per_feed=max_candidates,
            request_timeout=request_timeout,
            date_from=date_from,
            date_to=date_to,
            collection_timeout=max(20, request_timeout + 10),
            raise_on_error=True,
        )
        return annotate_topic_candidates(spec, candidates, cursor=cursor), cursor, True

    if source_type == "google_news":
        if str(row.get("target_key") or "") == GROUPED_SOURCE_RUN_TARGET_KEY:
            return [], cursor, True
        queries = source_run_queries(cursor) or [str(cursor.get("query") or "")]
        candidates = collect_google_news(
            queries=queries,
            date_from=date_from,
            date_to=date_to,
            limit_per_query=max_candidates,
            request_timeout=request_timeout,
            resolve_timeout=max(2, request_timeout - 2),
        )
        return annotate_topic_candidates(spec, candidates, cursor=cursor), cursor, True

    if source_type == "wordpress_api":
        queries = source_run_queries(cursor)
        if queries:
            return collect_grouped_wordpress_source_run(spec, row, cursor, queries)
        site = WORDPRESS_API_SITES[max(0, int(cursor.get("site_index") or 0))]
        start_page = max(1, int(cursor.get("page") or 1))
        max_pages = wordpress_max_pages(spec)
        pages_per_slice = wordpress_pages_per_slice(spec)
        query = str(cursor.get("query") or "")
        candidates: list[CandidateArticle] = []
        complete = False
        next_page = start_page
        last_page = start_page
        for _ in range(pages_per_slice):
            page = next_page
            last_page = page
            if page > max_pages:
                complete = True
                last_page = max_pages
                break
            try:
                batch = collect_wordpress_api(
                    query,
                    source_name=str(site.get("source_name") or "WordPress"),
                    base_url=str(site.get("base_url") or ""),
                    date_from=date_from,
                    date_to=date_to,
                    per_site_limit=WORDPRESS_PAGE_SIZE,
                    per_page=WORDPRESS_PAGE_SIZE,
                    request_timeout=request_timeout,
                    start_page=page,
                    max_pages=1,
                    raise_on_error=True,
                )
            except TimeoutError as exc:
                seen_before = max(safe_int(row.get("candidates_seen")), safe_int(row.get("candidates_total"))) + len(candidates)
                if should_soft_complete_wordpress_timeout(spec, exc, page=page, seen_before=seen_before):
                    next_cursor = wordpress_soft_error_cursor(cursor, page=page, exc=exc)
                    return annotate_topic_candidates(spec, dedupe_source_run_candidates(candidates), cursor=cursor), next_cursor, True
                raise
            except urllib.error.HTTPError as exc:
                seen_before = max(safe_int(row.get("candidates_seen")), safe_int(row.get("candidates_total"))) + len(candidates)
                if should_soft_complete_wordpress_http_error(spec, exc, page=page, seen_before=seen_before):
                    next_cursor = wordpress_soft_error_cursor(cursor, page=page, exc=exc)
                    return annotate_topic_candidates(spec, dedupe_source_run_candidates(candidates), cursor=cursor), next_cursor, True
                raise
            candidates.extend(batch)
            if len(batch) < WORDPRESS_PAGE_SIZE or page >= max_pages:
                complete = True
                break
            next_page = page + 1
        next_cursor = dict(cursor)
        next_cursor["page"] = next_page if not complete else last_page
        next_cursor["page_size"] = WORDPRESS_PAGE_SIZE
        next_cursor["pages_per_slice"] = pages_per_slice
        return annotate_topic_candidates(spec, dedupe_source_run_candidates(candidates), cursor=cursor), next_cursor, complete

    if source_type == "internal_search":
        adapter = FLAVIO_INTERNAL_SEARCH_TARGETS[max(0, int(cursor.get("adapter_index") or 0))]
        page = max(1, int(cursor.get("page") or 1))
        page_size = max(1, int(getattr(adapter, "page_size", 10) or 10))
        queries = source_run_queries(cursor)
        if queries:
            limit = page_size * len(queries)
            candidates = collect_internal_site_search(
                queries=queries,
                adapters=[adapter],
                date_from=date_from,
                date_to=date_to,
                limit_per_adapter=limit,
                max_pages_per_adapter=1,
                start_page=page,
                request_timeout=request_timeout,
            )
            complete = len(candidates) < limit or page >= INTERNAL_SEARCH_MAX_PAGES
            next_cursor = dict(cursor)
            next_cursor["page"] = page + 1 if not complete else page
            next_cursor["page_size"] = page_size
            return annotate_topic_candidates(spec, candidates, cursor=cursor), next_cursor, complete
        candidates = collect_internal_site_search(
            queries=[str(cursor.get("query") or "")],
            adapters=[adapter],
            date_from=date_from,
            date_to=date_to,
            limit_per_adapter=page_size,
            max_pages_per_adapter=1,
            start_page=page,
            request_timeout=request_timeout,
        )
        complete = len(candidates) < page_size or page >= INTERNAL_SEARCH_MAX_PAGES
        next_cursor = dict(cursor)
        next_cursor["page"] = page + 1 if not complete else page
        next_cursor["page_size"] = page_size
        return annotate_topic_candidates(spec, candidates, cursor=cursor), next_cursor, complete

    if source_type == "sitemap_daily":
        source = SITEMAP_DAILY_SOURCES[max(0, int(cursor.get("source_index") or 0))]
        day = str(cursor.get("day") or date_from or date_to)
        queries = source_run_queries(cursor)
        candidates = collect_sitemap_daily(
            queries=queries,
            sources=[source],
            date_from=day,
            date_to=day,
            limit_per_source=max_candidates,
            request_timeout=request_timeout,
            collection_timeout=max(30, request_timeout * 4),
        )
        return annotate_topic_candidates(spec, candidates, cursor=cursor), cursor, True

    if source_type == "vejario_archive":
        target = dict(VEJARIO_ARCHIVE_TARGETS[max(0, int(cursor.get("target_index") or 0))])
        page = max(1, int(cursor.get("page") or 1))
        if page > 1:
            target["start_url"] = paged_url(str(target.get("start_url") or ""), page)
        candidates = collect_vejario_archive(
            targets=[target],
            date_from=date_from,
            date_to=date_to,
            limit_per_target=max_candidates,
            max_pages_per_target=1,
            request_timeout=request_timeout,
        )
        return annotate_topic_candidates(spec, candidates, cursor=cursor), cursor, True

    if source_type == "camara_archive":
        page = max(1, int(cursor.get("page") or 1))
        page_size = max(1, int(CAMARA_ARCHIVE_TARGET.get("page_size") or 10))
        candidates = collect_camara_archive(
            date_from=date_from,
            date_to=date_to,
            limit_total=max_candidates,
            max_pages=1,
            request_timeout=request_timeout,
            start_offset=(page - 1) * page_size,
        )
        return annotate_topic_candidates(spec, candidates, cursor=cursor), cursor, True

    raise ValueError(f"unknown_source_type:{source_type}")


def source_run_queries(cursor: dict[str, Any]) -> list[str]:
    return ordered_unique([str(item or "").strip() for item in list(cursor.get("queries") or []) if str(item or "").strip()])


def collect_grouped_wordpress_source_run(
    spec: dict[str, Any],
    row: dict[str, Any],
    cursor: dict[str, Any],
    queries: list[str],
) -> tuple[list[CandidateArticle], dict[str, Any], bool]:
    request_timeout = 10
    date_from = str(spec.get("date_from") or "")
    date_to = str(spec.get("date_to") or "")
    site = WORDPRESS_API_SITES[max(0, int(cursor.get("site_index") or 0))]
    start_page = max(1, int(cursor.get("page") or 1))
    max_pages = wordpress_max_pages(spec)
    pages_per_slice = wordpress_pages_per_slice(spec)
    complete_queries = {
        str(item or "").strip()
        for item in list(cursor.get("complete_queries") or [])
        if str(item or "").strip()
    }
    candidates: list[CandidateArticle] = []
    next_page = start_page
    last_page = start_page
    complete = len(complete_queries) >= len(queries)
    for _ in range(pages_per_slice):
        page = next_page
        if page > max_pages:
            complete = True
            last_page = max_pages
            break
        last_page = page
        for query in queries:
            if query in complete_queries:
                continue
            try:
                batch = collect_wordpress_api(
                    query,
                    source_name=str(site.get("source_name") or "WordPress"),
                    base_url=str(site.get("base_url") or ""),
                    date_from=date_from,
                    date_to=date_to,
                    per_site_limit=WORDPRESS_PAGE_SIZE,
                    per_page=WORDPRESS_PAGE_SIZE,
                    request_timeout=request_timeout,
                    start_page=page,
                    max_pages=1,
                    raise_on_error=True,
                )
            except TimeoutError as exc:
                seen_before = max(safe_int(row.get("candidates_seen")), safe_int(row.get("candidates_total"))) + len(candidates)
                if should_soft_complete_wordpress_timeout(spec, exc, page=page, seen_before=seen_before):
                    complete_queries.add(query)
                    continue
                raise
            except urllib.error.HTTPError as exc:
                seen_before = max(safe_int(row.get("candidates_seen")), safe_int(row.get("candidates_total"))) + len(candidates)
                if should_soft_complete_wordpress_http_error(spec, exc, page=page, seen_before=seen_before):
                    complete_queries.add(query)
                    continue
                raise
            candidates.extend(batch)
            if len(batch) < WORDPRESS_PAGE_SIZE:
                complete_queries.add(query)
        complete = len(complete_queries) >= len(queries) or page >= max_pages
        if complete:
            break
        next_page = page + 1
    next_cursor = dict(cursor)
    next_cursor["page"] = next_page if not complete else last_page
    next_cursor["page_size"] = WORDPRESS_PAGE_SIZE
    next_cursor["pages_per_slice"] = pages_per_slice
    next_cursor["complete_queries"] = sorted(complete_queries)
    return annotate_topic_candidates(spec, dedupe_source_run_candidates(candidates), cursor=cursor), next_cursor, complete


def is_late_wordpress_transient_http_error(exc: BaseException, *, page: int, seen_before: int) -> bool:
    status = int(getattr(exc, "code", 0) or 0)
    return status in {502, 503, 504} and page >= 5 and seen_before >= WORDPRESS_PAGE_SIZE * 4


def dedupe_source_run_candidates(candidates: list[CandidateArticle]) -> list[CandidateArticle]:
    deduped: list[CandidateArticle] = []
    seen: set[str] = set()
    for candidate in candidates:
        url = str(candidate.url or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        deduped.append(candidate)
    return deduped


def paged_url(base_url: str, page: int) -> str:
    clean = str(base_url or "").split("?", 1)[0].rstrip("/")
    return f"{clean}/pagina/{max(1, int(page))}/"


def mark_source_run_running(source_run_id: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with connect(db_path()) as conn:
        conn.execute(
            """
            UPDATE job_source_runs
            SET status = 'running', attempts = attempts + 1, started_at = COALESCE(started_at, ?),
                updated_at = ?, last_error = NULL
            WHERE id = ?
            """,
            (now, now, source_run_id),
        )


def update_source_run(
    source_run_id: int,
    *,
    status: str,
    cursor: dict[str, Any],
    candidates_seen: int = 0,
    candidates_total: int = 0,
    articles_inserted: int = 0,
    mentions_inserted: int = 0,
    stories_touched: int = 0,
    last_error: str = "",
    finished: bool = False,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    finished_at = now if finished else None
    with connect(db_path()) as conn:
        conn.execute(
            """
            UPDATE job_source_runs
            SET status = ?, cursor_json = ?, candidates_seen = candidates_seen + ?,
                candidates_total = candidates_total + ?, articles_inserted = articles_inserted + ?,
                mentions_inserted = mentions_inserted + ?, stories_touched = stories_touched + ?,
                last_error = ?, updated_at = ?, finished_at = COALESCE(?, finished_at)
            WHERE id = ?
            """,
            (
                status,
                json.dumps(cursor, ensure_ascii=False),
                int(candidates_seen or 0),
                int(candidates_total or 0),
                int(articles_inserted or 0),
                int(mentions_inserted or 0),
                int(stories_touched or 0),
                last_error or None,
                now,
                finished_at,
                source_run_id,
            ),
        )


def mark_source_run_interrupted(source_run_id: int, *, reason: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with connect(db_path()) as conn:
        conn.execute(
            """
            UPDATE job_source_runs
            SET status = 'interrupted_resumable', last_error = ?, updated_at = ?
            WHERE id = ?
            """,
            (reason, now, source_run_id),
        )


def mark_running_source_runs_resumable(job_id: str, *, reason: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with connect(db_path()) as conn:
        conn.execute(
            """
            UPDATE job_source_runs
            SET status = 'interrupted_resumable', last_error = ?, updated_at = ?
            WHERE job_id = ? AND status IN ('pending', 'running', 'retrying')
            """,
            (reason, now, job_id),
        )


def reset_resumable_source_runs(job_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with connect(db_path()) as conn:
        conn.execute(
            """
            UPDATE job_source_runs
            SET status = 'pending', updated_at = ?, finished_at = NULL
            WHERE job_id = ? AND status IN ('interrupted_resumable', 'failed_needs_fix', 'running', 'retrying')
            """,
            (now, job_id),
        )


def failed_source_runs(job_id: str) -> list[dict[str, Any]]:
    return [
        source_run_public(row)
        for row in source_run_rows(job_id)
        if str(row.get("status") or "") == "failed_needs_fix"
    ]


def source_coverage_state(job_id: str) -> str:
    rows = source_run_rows(job_id)
    if not rows:
        return "untracked"
    statuses = {str(row.get("status") or "") for row in rows}
    if "failed_needs_fix" in statuses:
        return "failed_needs_fix"
    if statuses.issubset({"complete"}):
        return "complete"
    if "interrupted_resumable" in statuses:
        return "interrupted_resumable"
    if statuses.intersection({"running", "retrying"}):
        return "running"
    return "pending"


def source_run_rows(job_id: str) -> list[dict[str, Any]]:
    with connect(db_path()) as conn:
        rows = conn.execute(
            "SELECT * FROM job_source_runs WHERE job_id = ? ORDER BY id ASC",
            (job_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def source_run_public(row: dict[str, Any]) -> dict[str, Any]:
    cursor = safe_json_dict(row.get("cursor_json"))
    return {
        "sourceKey": str(row.get("source_key") or ""),
        "targetKey": str(row.get("target_key") or ""),
        "sourceName": str(row.get("source_name") or ""),
        "sourceType": str(row.get("source_type") or ""),
        "status": str(row.get("status") or ""),
        "cursor": sanitize_cursor(cursor),
        "candidatesSeen": safe_int(row.get("candidates_seen")),
        "candidatesTotal": safe_int(row.get("candidates_total")),
        "articlesInserted": safe_int(row.get("articles_inserted")),
        "mentionsInserted": safe_int(row.get("mentions_inserted")),
        "storiesTouched": safe_int(row.get("stories_touched")),
        "attempts": safe_int(row.get("attempts")),
        "lastError": str(row.get("last_error") or ""),
        "updatedAt": str(row.get("updated_at") or ""),
    }


def sanitize_cursor(cursor: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "feed_index",
        "query_index",
        "site_index",
        "adapter_index",
        "source_index",
        "day_index",
        "day",
        "page",
        "page_size",
    }
    return {key: cursor[key] for key in allowed if key in cursor}


def safe_json_dict(raw: Any) -> dict[str, Any]:
    try:
        value = json.loads(str(raw or "{}"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def get_resumable_job(job_id: str = "") -> dict[str, Any] | None:
    ensure_app_tables(db_path())
    with connect(db_path()) as conn:
        if job_id:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return None
            data = dict(row)
            return data if str(data.get("status") or "") in RESUMABLE_JOB_STATUSES else None
        row = conn.execute(
            f"""
            SELECT * FROM jobs
            WHERE status IN ({','.join('?' for _ in RESUMABLE_JOB_STATUSES)})
            ORDER BY COALESCE(finished_at, started_at, '') DESC
            LIMIT 1
            """,
            RESUMABLE_JOB_STATUSES,
        ).fetchone()
    return dict(row) if row else None


def job_spec(job: dict[str, Any]) -> dict[str, Any]:
    spec = safe_json_dict(job.get("spec_json"))
    if spec:
        return spec
    return {
        "preset": str(job.get("preset") or "custom"),
        "collector": str(job.get("collector") or DEFAULT_COLLECTOR),
        "target_keys": parse_target_keys(job.get("target_keys")),
        "date_from": str(job.get("date_from") or ""),
        "date_to": str(job.get("date_to") or ""),
        "export": True,
        "max_candidates": CUSTOM_MAX_CANDIDATES,
        "max_process_seconds": CUSTOM_MAX_PROCESS_SECONDS,
        "skip_direct_scrape": True,
        "durable": False,
    }


def publish_incremental_snapshot(job_id: str, *, reason: str, force: bool = False) -> None:
    if not artifact_store.enabled:
        return
    now = time.monotonic()
    previous = _LAST_INCREMENTAL_EXPORT.get(job_id, 0.0)
    if not force and now - previous < INCREMENTAL_EXPORT_MIN_SECONDS:
        return
    _LAST_INCREMENTAL_EXPORT[job_id] = now
    try:
        run_export_snapshot(job_id)
        uploaded = artifact_store.upload_current_artifacts(
            manifest={
                "kind": "incremental-publish",
                "jobId": job_id,
                "reason": reason,
                "createdAt": datetime.now(timezone.utc).isoformat(),
            },
            job_id=f"{job_id}-incremental-publish",
        )
        append_event(job_id, "incremental_publish_complete", artifact_upload_summary(uploaded))
    except Exception as exc:
        append_event(job_id, "incremental_publish_failed", {"error": sanitize_error(exc)})


def create_job(
    job_id: str,
    kind: str,
    spec: dict[str, Any],
    *,
    started_by: str,
    enforce_single_active: bool = True,
) -> None:
    with connect(db_path()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        if enforce_single_active:
            active = conn.execute(
                f"SELECT id FROM jobs WHERE status IN ({','.join('?' for _ in ACTIVE_JOB_STATUSES)}) LIMIT 1",
                ACTIVE_JOB_STATUSES,
            ).fetchone()
            if active:
                raise JobConflict("job_already_running")
        conn.execute(
            """
            INSERT INTO jobs (
                id, kind, status, preset, target_keys, collector, date_from, date_to,
                started_by, started_at, spec_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                kind,
                "queued",
                spec.get("preset", ""),
                json.dumps(spec.get("target_keys") or [], ensure_ascii=False),
                spec.get("collector", ""),
                spec.get("date_from", ""),
                spec.get("date_to", ""),
                started_by,
                datetime.now(timezone.utc).isoformat(),
                json.dumps(spec, ensure_ascii=False),
            ),
        )


def update_job(job_id: str, **fields: Any) -> None:
    allowed = {
        "status",
        "finished_at",
        "articles_inserted",
        "mentions_inserted",
        "stories_touched",
        "error_message",
    }
    updates = [(key, value) for key, value in fields.items() if key in allowed]
    if not updates:
        return
    sql = ", ".join(f"{key} = ?" for key, _ in updates)
    with connect(db_path()) as conn:
        conn.execute(f"UPDATE jobs SET {sql} WHERE id = ?", [value for _, value in updates] + [job_id])


def append_event(job_id: str, event: str, payload: dict[str, Any]) -> None:
    safe_payload = sanitize_payload(payload)
    with connect(db_path()) as conn:
        conn.execute(
            """
            INSERT INTO job_events (job_id, created_at, event, payload_json)
            VALUES (?, ?, ?, ?)
            """,
            (job_id, datetime.now(timezone.utc).isoformat(), event, json.dumps(safe_payload, ensure_ascii=False)),
        )


def payload_flag(value: Any) -> int:
    if isinstance(value, str):
        return 1 if value.strip().lower() in {"1", "true", "yes", "ok"} else 0
    return 1 if value else 0


def candidate_decision(payload: dict[str, Any]) -> str:
    status = str(payload.get("status") or "").strip().lower()
    reason = str(payload.get("reason") or "").strip().lower()
    if status == "selected":
        return "saved"
    if status == "duplicate" or reason.startswith("already_in_database"):
        return "duplicate"
    if reason.startswith("fetch_fail") or reason.startswith("google_redirect"):
        return "source_error"
    if reason in {
        "no_match_exact_name",
        "target_only_in_page_boilerplate",
        "required_terms_not_matched",
        "forced_terms_not_matched",
        "exclude_title_terms_matched",
        "exclude_body_terms_matched",
    }:
        return "outside_city"
    if reason == "outside_date_window":
        return "outside_date"
    if reason == "missing_published_at":
        return "missing_date"
    return "discarded"


def first_payload_value(value: Any) -> str:
    if isinstance(value, list):
        for item in value:
            text = str(item or "").strip()
            if text:
                return text
        return ""
    return str(value or "").strip()


def record_candidate_audit(job_id: str, payload: dict[str, Any]) -> None:
    ensure_app_tables(db_path())
    matched_targets = [str(item) for item in list(payload.get("matched_targets") or []) if str(item).strip()]
    matched_keywords = [str(item) for item in list(payload.get("matched_keywords") or []) if str(item).strip()]
    target_key = str(payload.get("target_key") or first_payload_value(payload.get("target_keys")) or "").strip()
    final_url = str(payload.get("final_url") or payload.get("candidate_url") or "").strip()
    published_at = str(payload.get("published_at") or "").strip()
    text_chars = safe_int(payload.get("text_chars")) or len(str(payload.get("summary_excerpt") or "").strip())
    query = str(payload.get("query") or first_payload_value(payload.get("queries")) or "").strip()
    municipal_match = payload_flag(payload.get("municipal_match")) or (1 if RIO_ECONOMICO_SCOPE in matched_targets else 0)
    with connect(db_path()) as conn:
        conn.execute(
            """
            INSERT INTO job_candidate_audit (
                job_id, created_at, source_run_id, source_key, source_name, source_type,
                target_key, target_label, scope, topic, dimension, query,
                candidate_url, final_url, title, published_at, status, reason, decision,
                stage, matched_targets_json, matched_keywords_json, url_resolved,
                text_chars, has_text, has_canonical_date, municipal_match
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                datetime.now(timezone.utc).isoformat(),
                safe_int(payload.get("source_run_id")),
                str(payload.get("source_key") or ""),
                str(payload.get("source_name") or ""),
                str(payload.get("source_type") or ""),
                target_key,
                str(payload.get("target_label") or ""),
                str(payload.get("scope") or ""),
                str(payload.get("topic") or ""),
                str(payload.get("dimension") or ""),
                query,
                str(payload.get("candidate_url") or ""),
                final_url,
                str(payload.get("candidate_title") or payload.get("title") or "")[:500],
                published_at,
                str(payload.get("status") or ""),
                str(payload.get("reason") or "")[:500],
                candidate_decision(payload),
                str(payload.get("stage") or ""),
                json.dumps(matched_targets, ensure_ascii=False),
                json.dumps(matched_keywords, ensure_ascii=False),
                payload_flag(payload.get("url_resolved")) or (1 if final_url else 0),
                text_chars,
                payload_flag(payload.get("has_text")) or (1 if text_chars > 0 else 0),
                payload_flag(payload.get("has_canonical_date")) or (1 if published_at else 0),
                municipal_match,
            ),
        )


def record_progress(
    job_id: str,
    event: str,
    payload: dict[str, Any],
    *,
    target_key: str = "",
    target_label: str = "",
) -> None:
    if event == "candidate_evaluated":
        record_candidate_audit(job_id, enrich_progress_payload(payload, target_key=target_key, target_label=target_label))
        return
    append_event(job_id, event, enrich_progress_payload(payload, target_key=target_key, target_label=target_label))
    if event in {"article_saved", "source_progress", "source_complete", "run_complete", "run_cancelled"}:
        sync_live_progress_totals(job_id)
    if event == "article_saved":
        upload_live_checkpoint(job_id, reason="article-saved")


def upload_live_checkpoint(job_id: str, *, reason: str, force: bool = False) -> list[str]:
    if not artifact_store.enabled:
        return []
    now = time.monotonic()
    with _CHECKPOINT_LOCK:
        previous = _LAST_CHECKPOINT_UPLOAD.get(job_id, 0.0)
        if not force and now - previous < LIVE_CHECKPOINT_MIN_SECONDS:
            return []
        _LAST_CHECKPOINT_UPLOAD[job_id] = now
    manifest = {
        "kind": "live-save-checkpoint",
        "jobId": job_id,
        "reason": reason,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    uploaded = artifact_store.upload_database_checkpoint(manifest=manifest, job_id=f"{job_id}-live-checkpoint")
    if uploaded:
        append_event(job_id, "live_checkpoint_uploaded", artifact_upload_summary(uploaded))
    return uploaded


def record_target_sync(target_key: str, *, reason: str, cleanup: bool = False, started_by: str = "coworker") -> dict[str, Any]:
    """Backfill a target into the current base and expose touched articles as live results."""
    target_key = str(target_key or "").strip()
    if not target_key:
        return {
            "targetKey": "",
            "updatedCount": 0,
            "mentionsInserted": 0,
            "storiesTouched": 0,
            "cleanup": {},
            "jobId": "",
        }
    ensure_app_tables(db_path())
    cleanup_result = (
        cleanup_false_backfilled_target_mentions(db_path(), [target_key])
        if cleanup
        else {"removedMentions": 0, "storiesTouched": 0}
    )
    backfill = backfill_missing_target_mentions(db_path(), [target_key])
    try:
        target_snapshots = frozen_target_snapshots(validate_target_keys([target_key]))
    except ValueError:
        target_snapshots = []
    job_id = f"target-sync-{uuid.uuid4().hex[:12]}"
    spec = {
        "preset": "target-sync",
        "collector": "target-sync",
        "target_keys": [target_key],
        "target_snapshots": target_snapshots,
        "date_from": "",
        "date_to": "",
        "export": False,
        "durable": False,
        "reason": reason,
    }
    create_job(job_id, "target-sync", spec, started_by=started_by, enforce_single_active=False)
    update_job(job_id, status="running")
    labels = target_labels(include_archived=True)
    for item in list(backfill.get("updated") or [])[:240]:
        if not isinstance(item, dict):
            continue
        item_key = str(item.get("target_key") or target_key)
        append_event(
            job_id,
            "article_saved",
            {
                "article_id": safe_int(item.get("article_id")),
                "story_id": safe_int(item.get("story_id")),
                "target_key": item_key,
                "target_keys": [item_key],
                "target_label": str(item.get("target_label") or labels.get(item_key) or item_key),
                "title": str(item.get("title") or ""),
                "url": str(item.get("url") or ""),
                "source_name": str(item.get("source_name") or ""),
                "source_type": str(item.get("source_type") or ""),
                "published_at": str(item.get("published_at") or ""),
                "articles_inserted_delta": 0,
                "mentions_inserted_delta": 1,
                "stories_touched_delta": 1,
                "publication_state": "saved",
                "reason": reason,
            },
        )
    totals = {
        "articles_inserted": 0,
        "mentions_inserted": int(backfill.get("mentionsInserted") or 0),
        "stories_touched": int(backfill.get("storiesTouched") or 0)
        + int(cleanup_result.get("storiesTouched") or 0),
    }
    append_event(
        job_id,
        "target_sync_complete",
        {
            "target_key": target_key,
            "target_label": labels.get(target_key, target_key),
            "reason": reason,
            "updated_count": int(backfill.get("updatedCount") or 0),
            "mentions_inserted": totals["mentions_inserted"],
            "stories_touched": totals["stories_touched"],
            "cleanup": cleanup_result,
        },
    )
    update_job(
        job_id,
        status="succeeded",
        finished_at=datetime.now(timezone.utc).isoformat(),
        **totals,
    )
    upload_live_checkpoint(job_id, reason="target-sync", force=True)
    return {
        "jobId": job_id,
        "targetKey": target_key,
        "updatedCount": int(backfill.get("updatedCount") or 0),
        "mentionsInserted": totals["mentions_inserted"],
        "storiesTouched": totals["stories_touched"],
        "cleanup": cleanup_result,
    }


def enrich_progress_payload(payload: dict[str, Any], *, target_key: str = "", target_label: str = "") -> dict[str, Any]:
    enriched = dict(payload)
    if target_key:
        enriched["target_key"] = target_key
    if target_label:
        enriched["target_label"] = target_label
    source = enriched.get("source") or enriched.get("source_name") or enriched.get("source_type") or ""
    if source:
        enriched["source"] = source
    return enriched


def get_job(job_id: str) -> dict[str, Any] | None:
    ensure_app_tables(db_path())
    with connect(db_path()) as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            return None
        events = conn.execute(
            "SELECT created_at, event, payload_json FROM job_events WHERE job_id = ? ORDER BY id DESC LIMIT 50",
            (job_id,),
        ).fetchall()
    data = dict(row)
    data["events"] = [
        {
            "created_at": event_row["created_at"],
            "event": event_row["event"],
            "payload": safe_event_payload(event_row["payload_json"]),
        }
        for event_row in events
    ]
    data.update(job_observability_from_events(data, data["events"]))
    return data


def get_active_job() -> dict[str, Any] | None:
    ensure_app_tables(db_path())
    with connect(db_path()) as conn:
        row = conn.execute(
            f"""
            SELECT * FROM jobs
            WHERE status IN ({','.join('?' for _ in ACTIVE_JOB_STATUSES)})
            ORDER BY started_at ASC
            LIMIT 1
            """,
            ACTIVE_JOB_STATUSES,
        ).fetchone()
    return with_job_observability(dict(row)) if row else None


def mark_orphaned_active_jobs_interrupted(reason: str = "startup_recovered_active_job") -> int:
    ensure_app_tables(db_path())
    with connect(db_path()) as conn:
        rows = conn.execute(
            f"""
            SELECT id FROM jobs
            WHERE status IN ({','.join('?' for _ in ACTIVE_JOB_STATUSES)})
            ORDER BY started_at ASC
            """,
            ACTIVE_JOB_STATUSES,
        ).fetchall()
    if not rows:
        return 0
    now = datetime.now(timezone.utc).isoformat()
    for row in rows:
        job_id = str(row["id"])
        job = get_job(job_id) or {"id": job_id}
        durable = bool(job_spec(job).get("durable"))
        next_status = "interrupted_resumable" if durable else "interrupted"
        message = (
            "A atualização foi interrompida por reinício do servidor. Ela pode ser retomada do último checkpoint."
            if durable
            else "A atualização foi interrompida por reinício do servidor. Os itens já salvos continuam preservados."
        )
        update_job(
            job_id,
            status=next_status,
            finished_at=now,
            error_message=message,
        )
        if durable:
            mark_running_source_runs_resumable(job_id, reason=reason)
        append_event(job_id, "job_interrupted", {"status": next_status, "reason": reason})
    return len(rows)


def recent_jobs(limit: int = 8, *, include_observability: bool = True) -> list[dict[str, Any]]:
    ensure_app_tables(db_path())
    with connect(db_path()) as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY started_at DESC LIMIT ?", (int(limit),)).fetchall()
    jobs = [dict(row) for row in rows]
    if not include_observability:
        return jobs
    return [with_job_observability(job) for job in jobs]


def last_successful_update(target_key: str = "") -> dict[str, Any] | None:
    ensure_app_tables(db_path())
    with connect(db_path()) as conn:
        rows = conn.execute(
            """
            SELECT * FROM jobs
            WHERE kind = 'update' AND status = 'succeeded'
            ORDER BY COALESCE(finished_at, started_at, '') DESC
            LIMIT 25
            """
        ).fetchall()
    for row in rows:
        job = dict(row)
        if target_key and target_key not in parse_target_keys(job.get("target_keys")):
            continue
        return with_job_observability(job)
    return None


def suggested_update_window(*, days: int = 1, target_key: str = "") -> dict[str, str]:
    today = date.today()
    last = last_successful_update(target_key)
    date_from = today - timedelta(days=max(1, int(days)))
    if last and str(last.get("date_to") or ""):
        try:
            date_from = min(today, date.fromisoformat(str(last["date_to"])) + timedelta(days=1))
        except ValueError:
            pass
    return {"date_from": date_from.isoformat(), "date_to": today.isoformat()}


def parse_target_keys(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(item) for item in raw]
    try:
        parsed = json.loads(str(raw or "[]"))
    except Exception:
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def with_artifact_upload(job: dict[str, Any]) -> dict[str, Any]:
    return with_job_observability(job)


def with_job_observability(job: dict[str, Any]) -> dict[str, Any]:
    job_id = str(job.get("id") or "")
    if not job_id:
        return job
    with connect(db_path()) as conn:
        rows = conn.execute(
            """
            SELECT created_at, event, payload_json
            FROM job_events
            WHERE job_id = ?
            ORDER BY id DESC
            LIMIT 50
            """,
            (job_id,),
        ).fetchall()
    events = [
        {"created_at": row["created_at"], "event": row["event"], "payload": safe_event_payload(row["payload_json"])}
        for row in rows
    ]
    job.update(job_observability_from_events(job, events))
    return job


def safe_event_payload(raw: Any) -> dict[str, Any]:
    try:
        payload = json.loads(str(raw or "{}"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def job_observability_from_events(job: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    recent_events = [
        {
            "created_at": str(event.get("created_at") or ""),
            "event": str(event.get("event") or ""),
            "payload": sanitize_payload(event.get("payload") if isinstance(event.get("payload"), dict) else {}),
        }
        for event in events[:20]
    ]
    data = artifact_upload_from_events(events)
    data["recentEvents"] = recent_events
    data["progress"] = progress_summary(job, events)
    data.update(source_runs_observability(str(job.get("id") or ""), str(job.get("status") or "")))
    funnel = candidate_funnel_summary(str(job.get("id") or ""))
    data["funnel"] = funnel
    data.update(
        {
            "candidates_observed": funnel["candidates_observed"],
            "urls_resolved": funnel["urls_resolved"],
            "text_extracted": funnel["text_extracted"],
            "canonical_dates_ok": funnel["canonical_dates_ok"],
            "articles_saved": funnel["articles_saved"],
            "skipped_by_reason": funnel["skipped_by_reason"],
        }
    )
    return data


def source_runs_observability(job_id: str, job_status: str = "") -> dict[str, Any]:
    if not job_id:
        return {
            "coverageState": "untracked",
            "sourceRuns": [],
            "sourceRunCount": 0,
            "sourceRunVisibleCount": 0,
            "sourceRunCounts": {},
            "failedSources": [],
            "resumeAvailable": False,
            "publishedAt": latest_publish_time(),
        }
    rows = [source_run_public(row) for row in source_run_rows(job_id)]
    failed = [row for row in rows if row.get("status") == "failed_needs_fix"]
    if rows:
        coverage = source_coverage_state(job_id)
    elif job_status in {"succeeded", "failed", "interrupted", "cancelled"}:
        coverage = "untracked"
    else:
        coverage = "pending"
    priority = {"failed_needs_fix": 0, "running": 1, "retrying": 2, "interrupted_resumable": 3, "pending": 4, "complete": 5}
    visible_rows = sorted(rows, key=lambda row: (priority.get(str(row.get("status") or ""), 6), str(row.get("updatedAt") or "")))[:80]
    status_counts: dict[str, int] = {}
    target_counts: dict[str, int] = {}
    source_type_counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        target_key = str(row.get("targetKey") or "")
        source_type = str(row.get("sourceType") or "")
        if target_key:
            target_counts[target_key] = target_counts.get(target_key, 0) + 1
        if source_type:
            source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
    return {
        "coverageState": coverage,
        "sourceRuns": visible_rows,
        "sourceRunCount": len(rows),
        "sourceRunVisibleCount": len(visible_rows),
        "sourceRunCounts": status_counts,
        "sourceRunTargetCounts": target_counts,
        "sourceRunSourceTypeCounts": source_type_counts,
        "failedSources": failed[:20],
        "resumeAvailable": bool(job_status in RESUMABLE_JOB_STATUSES and rows and any(row.get("status") != "complete" for row in rows)),
        "publishedAt": latest_publish_time(job_id),
    }


def candidate_funnel_summary(job_id: str) -> dict[str, Any]:
    empty = {
        "candidates_observed": 0,
        "candidates_evaluated": 0,
        "urls_resolved": 0,
        "text_extracted": 0,
        "canonical_dates_ok": 0,
        "municipal_matches": 0,
        "articles_saved": 0,
        "duplicates": 0,
        "skipped_by_reason": {},
        "decisions": {},
        "by_source_type": {},
        "source_failures": [],
    }
    if not job_id:
        return empty
    try:
        ensure_app_tables(db_path())
        with connect(db_path()) as conn:
            totals = conn.execute(
                """
                SELECT
                    COUNT(*) AS candidates_evaluated,
                    SUM(CASE WHEN final_url IS NOT NULL AND final_url != '' THEN 1 ELSE 0 END) AS urls_resolved,
                    SUM(CASE WHEN has_text = 1 OR text_chars > 0 THEN 1 ELSE 0 END) AS text_extracted,
                    SUM(CASE WHEN has_canonical_date = 1 THEN 1 ELSE 0 END) AS canonical_dates_ok,
                    SUM(CASE WHEN municipal_match = 1 THEN 1 ELSE 0 END) AS municipal_matches,
                    SUM(CASE WHEN decision = 'saved' THEN 1 ELSE 0 END) AS articles_saved,
                    SUM(CASE WHEN decision = 'duplicate' THEN 1 ELSE 0 END) AS duplicates
                FROM job_candidate_audit
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()
            reason_rows = conn.execute(
                """
                SELECT COALESCE(NULLIF(reason, ''), 'unknown') AS reason, COUNT(*) AS total
                FROM job_candidate_audit
                WHERE job_id = ? AND COALESCE(status, '') != 'selected'
                GROUP BY COALESCE(NULLIF(reason, ''), 'unknown')
                ORDER BY total DESC, reason ASC
                LIMIT 25
                """,
                (job_id,),
            ).fetchall()
            decision_rows = conn.execute(
                """
                SELECT COALESCE(NULLIF(decision, ''), 'unknown') AS decision, COUNT(*) AS total
                FROM job_candidate_audit
                WHERE job_id = ?
                GROUP BY COALESCE(NULLIF(decision, ''), 'unknown')
                ORDER BY total DESC, decision ASC
                """,
                (job_id,),
            ).fetchall()
            source_rows = conn.execute(
                """
                SELECT COALESCE(NULLIF(source_type, ''), 'unknown') AS source_type, COUNT(*) AS total
                FROM job_candidate_audit
                WHERE job_id = ?
                GROUP BY COALESCE(NULLIF(source_type, ''), 'unknown')
                ORDER BY total DESC, source_type ASC
                """,
                (job_id,),
            ).fetchall()
        observed_from_runs = sum(max(safe_int(row.get("candidates_total")), safe_int(row.get("candidates_seen"))) for row in source_run_rows(job_id))
        evaluated = safe_int(totals["candidates_evaluated"] if totals else 0)
        return {
            "candidates_observed": max(observed_from_runs, evaluated),
            "candidates_evaluated": evaluated,
            "urls_resolved": safe_int(totals["urls_resolved"] if totals else 0),
            "text_extracted": safe_int(totals["text_extracted"] if totals else 0),
            "canonical_dates_ok": safe_int(totals["canonical_dates_ok"] if totals else 0),
            "municipal_matches": safe_int(totals["municipal_matches"] if totals else 0),
            "articles_saved": safe_int(totals["articles_saved"] if totals else 0),
            "duplicates": safe_int(totals["duplicates"] if totals else 0),
            "skipped_by_reason": {str(row["reason"]): safe_int(row["total"]) for row in reason_rows},
            "decisions": {str(row["decision"]): safe_int(row["total"]) for row in decision_rows},
            "by_source_type": {str(row["source_type"]): safe_int(row["total"]) for row in source_rows},
            "source_failures": [
                {
                    "sourceName": str(row.get("sourceName") or ""),
                    "sourceType": str(row.get("sourceType") or ""),
                    "lastError": str(row.get("lastError") or ""),
                }
                for row in source_runs_observability(job_id).get("failedSources", [])
            ][:20],
        }
    except Exception as exc:
        data = dict(empty)
        data["error"] = sanitize_error(exc)
        return data


def progress_summary(job: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    collected_candidates_total = 0
    run_candidates_total = 0
    run_candidates_seen = 0
    sources_total = 0
    latest_by_source: dict[tuple[str, str, str], dict[str, Any]] = {}
    labels = target_labels()
    targets: dict[str, str] = {
        key: labels.get(key, key)
        for key in parse_target_keys(job.get("target_keys"))
        if key
    }
    current_target_key = ""
    current_source = ""

    for event in reversed(events):
        payload = event.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        target_key = str(payload.get("target_key") or "")
        target_label = str(payload.get("target_label") or target_key)
        if target_key:
            if target_key != GROUPED_SOURCE_RUN_TARGET_KEY:
                targets[target_key] = target_label
            current_target_key = target_key
        for payload_key in event_target_keys(payload):
            if payload_key and payload_key != GROUPED_SOURCE_RUN_TARGET_KEY:
                targets.setdefault(payload_key, labels.get(payload_key, payload_key))
        source_label = str(payload.get("source_name") or payload.get("source") or "")
        if source_label:
            current_source = source_label
        if event.get("event") == "run_started":
            sources_total += safe_int(payload.get("sources_total"))
            run_candidates_total += safe_int(payload.get("candidates_total"))
        if event.get("event") in {"run_complete", "run_cancelled"}:
            run_candidates_seen = max(run_candidates_seen, safe_int(payload.get("candidates_seen")))
            run_candidates_total = max(run_candidates_total, safe_int(payload.get("candidates_total")))
        if event.get("event") == "source_collected":
            collected_candidates_total += safe_int(payload.get("candidates_total"))
        if event.get("event") in {"source_progress", "source_complete"}:
            source_key = (
                target_key,
                str(payload.get("source_type") or ""),
                str(payload.get("source_name") or payload.get("source") or ""),
            )
            latest_by_source[source_key] = payload

    source_totals = source_progress_totals(latest_by_source.values())
    saved_totals = article_saved_totals(events)
    candidates_seen = max(
        run_candidates_seen,
        sum(safe_int(payload.get("candidates_seen")) for payload in latest_by_source.values()),
    )
    progress_candidates_total = sum(safe_int(payload.get("candidates_total")) for payload in latest_by_source.values())
    known_candidates_total = max(run_candidates_total, collected_candidates_total, progress_candidates_total)
    candidates_total = known_candidates_total or candidates_seen
    if known_candidates_total:
        candidates_seen = min(candidates_seen, known_candidates_total)
    return {
        "status": str(job.get("status") or ""),
        "targetKeys": list(targets),
        "targetLabels": targets,
        "currentTargetKey": current_target_key,
        "currentSource": current_source,
        "dateFrom": str(job.get("date_from") or ""),
        "dateTo": str(job.get("date_to") or ""),
        "sourcesTotal": max(sources_total, len(latest_by_source)),
        "candidatesSeen": candidates_seen,
        "candidatesTotal": candidates_total,
        "articlesInserted": max(
            safe_int(job.get("articles_inserted")),
            source_totals["articlesInserted"],
            saved_totals["articlesInserted"],
        ),
        "mentionsInserted": max(
            safe_int(job.get("mentions_inserted")),
            source_totals["mentionsInserted"],
            saved_totals["mentionsInserted"],
        ),
        "storiesTouched": max(
            safe_int(job.get("stories_touched")),
            source_totals["storiesTouched"],
            saved_totals["storiesTouched"],
        ),
    }


def source_progress_totals(payloads: Any) -> dict[str, int]:
    totals = {"articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0}
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        totals["articlesInserted"] += safe_int(payload.get("articles_inserted"))
        totals["mentionsInserted"] += safe_int(payload.get("mentions_inserted"))
        totals["storiesTouched"] += safe_int(payload.get("stories_touched"))
    return totals


def article_saved_totals(events: list[dict[str, Any]]) -> dict[str, int]:
    totals = {"articlesInserted": 0, "mentionsInserted": 0, "storiesTouched": 0}
    for event in events:
        if event.get("event") != "article_saved":
            continue
        payload = event.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        totals["articlesInserted"] += safe_int(payload.get("articles_inserted_delta"))
        totals["mentionsInserted"] += safe_int(payload.get("mentions_inserted_delta"))
        totals["storiesTouched"] += safe_int(payload.get("stories_touched_delta"))
    return totals


def sync_live_progress_totals(job_id: str) -> None:
    with connect(db_path()) as conn:
        job = conn.execute(
            "SELECT articles_inserted, mentions_inserted, stories_touched FROM jobs WHERE id = ?",
            (job_id,),
        ).fetchone()
        if not job:
            return
        rows = conn.execute(
            "SELECT event, payload_json FROM job_events WHERE job_id = ? ORDER BY id DESC",
            (job_id,),
        ).fetchall()
        latest_by_source: dict[tuple[str, str, str], dict[str, Any]] = {}
        article_events: list[dict[str, Any]] = []
        for row in reversed(rows):
            event = str(row["event"] or "")
            if event not in {"article_saved", "source_progress", "source_complete"}:
                continue
            try:
                payload = json.loads(row["payload_json"])
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            if event == "article_saved":
                article_events.append({"event": event, "payload": payload})
                continue
            source_key = (
                str(payload.get("target_key") or ""),
                str(payload.get("source_type") or ""),
                str(payload.get("source_name") or payload.get("source") or ""),
            )
            latest_by_source[source_key] = payload
        totals = source_progress_totals(latest_by_source.values())
        saved_totals = article_saved_totals(article_events)
        next_articles = max(safe_int(job["articles_inserted"]), totals["articlesInserted"], saved_totals["articlesInserted"])
        next_mentions = max(safe_int(job["mentions_inserted"]), totals["mentionsInserted"], saved_totals["mentionsInserted"])
        next_stories = max(safe_int(job["stories_touched"]), totals["storiesTouched"], saved_totals["storiesTouched"])
        conn.execute(
            """
            UPDATE jobs
            SET articles_inserted = ?, mentions_inserted = ?, stories_touched = ?
            WHERE id = ?
            """,
            (next_articles, next_mentions, next_stories, job_id),
        )


def live_results_for_job(
    job_id: str = "",
    *,
    target_key: str = "",
    scope: str = "",
    limit: int = 60,
) -> dict[str, Any]:
    ensure_app_tables(db_path())
    if scope == "base":
        return live_results_for_base(target_key=target_key, limit=limit)
    job: dict[str, Any] | None = None
    if job_id:
        job = get_job(job_id)
    else:
        job = get_active_job() or (recent_jobs(1)[0] if recent_jobs(1) else None)
    if not job or not str(job.get("id") or ""):
        return {"jobId": "", "status": "idle", "items": [], "count": 0}

    job_id = str(job["id"])
    with connect(db_path()) as conn:
        rows = conn.execute(
            """
            SELECT created_at, payload_json
            FROM job_events
            WHERE job_id = ? AND event = 'article_saved'
            ORDER BY id DESC
            LIMIT ?
            """,
            (job_id, max(1, normalized_limit(limit) * 3)),
        ).fetchall()

    items = live_items_from_event_rows(
        rows,
        target_key=target_key,
        limit=limit,
        published_cutoff=latest_publish_time(job_id),
    )
    return {
        "jobId": job_id,
        "status": str(job.get("status") or ""),
        "items": items,
        "count": len(items),
        "funnel": candidate_funnel_summary(job_id),
    }


def live_results_for_base(*, target_key: str = "", limit: int = 240) -> dict[str, Any]:
    ensure_app_tables(db_path())
    row_limit = max(300, normalized_limit(limit) * 8)
    with connect(db_path()) as conn:
        rows = conn.execute(
            """
            SELECT e.created_at, e.payload_json
            FROM job_events e
            JOIN jobs j ON j.id = e.job_id
            WHERE e.event = 'article_saved'
            ORDER BY e.id DESC
            LIMIT ?
            """,
            (row_limit,),
        ).fetchall()

    items = live_items_from_event_rows(
        rows,
        target_key=target_key,
        limit=limit,
        published_cutoff=latest_publish_time(),
    )
    return {"jobId": "", "status": "base", "items": items, "count": len(items)}


def live_items_from_event_rows(
    rows: list[Any],
    *,
    target_key: str = "",
    limit: int = 60,
    published_cutoff: str = "",
) -> list[dict[str, Any]]:
    labels = target_labels()
    labels.update(rio_topic_labels())
    active_keys = set(labels)
    merged: dict[int, dict[str, Any]] = {}
    order: list[int] = []
    for row in reversed(rows):
        try:
            payload = json.loads(row["payload_json"])
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        article_id = safe_int(payload.get("article_id"))
        if article_id <= 0:
            continue
        payload_keys = event_target_keys(payload)
        if target_key and target_key not in payload_keys:
            continue
        if active_keys and not active_keys.intersection(payload_keys):
            continue
        if article_id not in merged:
            merged[article_id] = {
                "article_id": article_id,
                "story_id": safe_int(payload.get("story_id")),
                "saved_at": str(row["created_at"] or ""),
                "target_keys": [],
                "event_payload": payload,
            }
            order.append(article_id)
        item = merged[article_id]
        item["saved_at"] = str(row["created_at"] or item["saved_at"])
        if safe_int(payload.get("story_id")):
            item["story_id"] = safe_int(payload.get("story_id"))
        for key in list(payload.get("target_keys") or []):
            key = str(key or "").strip()
            if key and key not in item["target_keys"]:
                item["target_keys"].append(key)
        event_key = str(payload.get("target_key") or "").strip()
        if event_key and event_key not in item["target_keys"]:
            item["target_keys"].append(event_key)
        item["event_payload"] = payload

    article_ids = order[-normalized_limit(limit) :]
    db_articles = {int(row["article_id"]): row for row in ClippingDB(db_path()).list_articles_by_ids(article_ids)}
    items: list[dict[str, Any]] = []
    for article_id in reversed(article_ids):
        event_item = merged.get(article_id) or {}
        payload = event_item.get("event_payload") or {}
        article = db_articles.get(article_id, {})
        if article:
            target_keys = [key for key in list(article.get("target_keys") or []) if key in active_keys]
        else:
            target_keys = [key for key in list(event_item.get("target_keys") or []) if key in active_keys]
        if target_key and target_key not in target_keys:
            continue
        if not target_keys:
            continue
        story_id = safe_int(article.get("story_id")) or safe_int(event_item.get("story_id"))
        saved_at = str(event_item.get("saved_at") or "")
        published = bool(published_cutoff and saved_at and saved_at <= published_cutoff)
        items.append(
            {
                "articleId": article_id,
                "storyId": story_id,
                "title": str(article.get("title") or payload.get("title") or ""),
                "url": str(article.get("url") or payload.get("url") or ""),
                "sourceName": str(article.get("source_name") or payload.get("source_name") or ""),
                "sourceType": str(article.get("source_type") or payload.get("source_type") or ""),
                "publishedAt": str(article.get("published_at") or payload.get("published_at") or ""),
                "savedAt": saved_at,
                "summary": str(article.get("summary") or payload.get("summary_excerpt") or ""),
                "snippet": str(article.get("snippet") or ""),
                "targetKeys": target_keys,
                "targetLabels": {key: labels.get(key, key) for key in target_keys},
                "publicationState": "published" if published else "saved",
            }
        )
    return items


def event_target_keys(payload: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    for key in list(payload.get("target_keys") or payload.get("targetKeys") or []):
        key = str(key or "").strip()
        if key and key not in keys:
            keys.append(key)
    target_key = str(payload.get("target_key") or "").strip()
    if target_key and target_key not in keys:
        keys.append(target_key)
    return keys


def latest_successful_publish_time() -> str:
    with connect(db_path()) as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM jobs
            WHERE status = 'succeeded' AND kind IN ('update', 'export', 'manual')
            ORDER BY COALESCE(finished_at, started_at, '') DESC
            LIMIT 50
            """
        ).fetchall()
    for row in rows:
        data = dict(row)
        kind = str(data.get("kind") or "")
        spec = job_spec(data)
        if kind == "export" or bool(spec.get("export")):
            return str(data.get("finished_at") or data.get("started_at") or "")
    return ""


def latest_publish_event_time(job_id: str = "") -> str:
    params: tuple[Any, ...] = ()
    job_filter = ""
    if job_id:
        job_filter = "AND job_id = ?"
        params = (job_id,)
    with connect(db_path()) as conn:
        rows = conn.execute(
            f"""
            SELECT created_at, event, payload_json
            FROM job_events
            WHERE event IN ('export_complete', 'incremental_publish_complete', 'artifacts_uploaded')
              {job_filter}
            ORDER BY created_at DESC
            LIMIT 100
            """,
            params,
        ).fetchall()
    for row in rows:
        event = str(row["event"] or "")
        if event == "artifacts_uploaded":
            payload = safe_json_dict(row["payload_json"])
            items = payload.get("items") if isinstance(payload.get("items"), list) else []
            if int(payload.get("count") or len(items)) <= 0:
                continue
        return str(row["created_at"] or "")
    return ""


def latest_publish_time(job_id: str = "") -> str:
    latest = latest_successful_publish_time()
    event_time = latest_publish_event_time(job_id)
    if event_time and (not latest or event_time > latest):
        return event_time
    return latest


def normalized_limit(limit: int) -> int:
    try:
        value = int(limit)
    except Exception:
        value = 60
    return min(500, max(1, value))


def safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def artifact_upload_summary(uploaded: list[str]) -> dict[str, Any]:
    safe_items = []
    for item in uploaded:
        safe = safe_artifact_name(item)
        if safe:
            safe_items.append(safe)
    return {"count": len(safe_items), "items": safe_items}


def safe_artifact_name(value: Any) -> str:
    raw = str(value or "").strip().replace("\\", "/").lstrip("/")
    parts = [part for part in raw.split("/") if part and part not in {".", ".."}]
    if not parts:
        return ""
    safe_parts = []
    for part in parts:
        cleaned = re.sub(r"[^A-Za-z0-9._-]", "-", part)[:120]
        if cleaned:
            safe_parts.append(cleaned)
    return "/".join(safe_parts)


def artifact_upload_from_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    for event in events:
        if event.get("event") != "artifacts_uploaded":
            continue
        payload = event.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        items = [safe_artifact_name(item) for item in payload.get("items") or []]
        items = [item for item in items if item]
        count = int(payload.get("count") or len(items))
        return {
            "artifactUpload": {
                "count": count,
                "items": items,
            },
            "uploadedArtifactCount": count,
            "uploadedArtifacts": items,
        }
    return {}


def sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "collector",
        "source_name",
        "source_type",
        "sources_total",
        "candidates_total",
        "candidates_seen",
        "articles_inserted",
        "mentions_inserted",
        "stories_touched",
        "target_key",
        "target_label",
        "source",
        "source_key",
        "status",
        "reason",
        "coverage_state",
        "resume_available",
        "started_by",
        "article_id",
        "story_id",
        "url",
        "title",
        "published_at",
        "target_keys",
        "articles_inserted_delta",
        "mentions_inserted_delta",
        "stories_touched_delta",
        "publication_state",
        "summary_excerpt",
        "count",
        "items",
        "lines",
        "error",
        # Diagnostics (Goal 4 — 2026-05-22): RSS instrumentation per
        # source_run lets admin trace memory growth by source/target.
        "rss_mib_before",
        "rss_mib_after",
        "rss_mib_delta",
        "returncode",
        "source_run_mode",
        "legacy_source_runs_removed",
        "source_runs_inserted",
        "target_count",
    }
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        if key in allowed:
            safe[key] = redact_secret_text(str(value))[:160] if key == "error" else value
        elif key == "errors":
            safe[key] = ["erro_de_coleta" for _ in list(value or [])[:3]]
    return safe


def sanitize_error(exc: Exception) -> str:
    text = str(exc) or exc.__class__.__name__
    if "export_failed" in text:
        return "Falha ao exportar o painel."
    if "unknown_target_keys" in text:
        return "Nome acompanhado desconhecido."
    return redact_secret_text(text)[:160]


def redact_secret_text(text: str) -> str:
    redacted = text
    for name, value in os.environ.items():
        if any(marker in name.upper() for marker in SECRET_ENV_MARKERS):
            secret = value.strip()
            if len(secret) >= 8:
                redacted = redacted.replace(secret, "[redacted]")
    redacted = BEARER_TOKEN_RE.sub(r"\1[redacted]", redacted)
    redacted = SECRET_ASSIGNMENT_RE.sub(r"\1[redacted]", redacted)
    return QUERY_SECRET_RE.sub(r"\1[redacted]", redacted)


job_manager = JobManager(artifact_store)
