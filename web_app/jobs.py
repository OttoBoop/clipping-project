from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
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
LIVE_CHECKPOINT_MIN_SECONDS = 30
_CHECKPOINT_LOCK = threading.Lock()
_LAST_CHECKPOINT_UPLOAD: dict[str, float] = {}
_LAST_INCREMENTAL_EXPORT: dict[str, float] = {}


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
            return get_job(active) or {"id": active, "status": "running"}
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
            if self._active_job_id or get_active_job():
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

    if preset in PRESETS:
        preset_spec = PRESETS[preset]
        target_keys = validate_target_keys(list(preset_spec["target_keys"]))
        date_from = (today - timedelta(days=int(preset_spec["days"]))).isoformat()
        date_to = today.isoformat()
        max_candidates = int(preset_spec["max_candidates"])
        max_process_seconds = int(preset_spec["max_process_seconds"])
    elif preset == "custom":
        target_keys = validate_target_keys(payload_list(payload, "target_keys", "targetKeys"))
        date_from = validate_date(str(payload.get("date_from") or payload.get("dateFrom") or ""))
        date_to = validate_date(str(payload.get("date_to") or payload.get("dateTo") or ""))
        collector = str(payload.get("collector") or DEFAULT_COLLECTOR).strip() or DEFAULT_COLLECTOR
    else:
        raise ValueError("preset_invalido")

    if preset != "custom":
        collector = DEFAULT_COLLECTOR
    if collector not in SAFE_COLLECTORS:
        raise ValueError("coletor_invalido")
    if date_from > date_to:
        raise ValueError("periodo_invalido")
    target_snapshots = frozen_target_snapshots(target_keys)

    return {
        "preset": preset,
        "collector": collector,
        "target_keys": target_keys,
        "target_snapshots": target_snapshots,
        "date_from": date_from,
        "date_to": date_to,
        "export": bool(payload.get("export", True)),
        "max_candidates": max_candidates,
        "max_process_seconds": max_process_seconds,
        "skip_direct_scrape": True,
        "durable": True,
    }


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


def target_to_snapshot(target: Any) -> dict[str, Any]:
    return {
        "key": str(getattr(target, "key", "") or ""),
        "label": str(getattr(target, "label", "") or ""),
        "display_name": str(getattr(target, "display_name", "") or ""),
        "keywords": [str(item) for item in (getattr(target, "keywords", None) or []) if str(item).strip()],
        "exact_aliases": [str(item) for item in (getattr(target, "exact_aliases", None) or []) if str(item).strip()],
        "className": str(getattr(target, "className", "") or ""),
        "primary": bool(getattr(target, "primary", False)),
        "priority": int(getattr(target, "priority", 2) or 2),
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
    completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=EXPORT_TIMEOUT_SECONDS, check=False)
    if completed.returncode != 0:
        raise RuntimeError("export_failed")
    if job_id:
        append_event(job_id, "export_complete", {"lines": len(completed.stdout.splitlines())})


def run_durable_update(job_id: str, spec: dict[str, Any], cancel_event: threading.Event) -> dict[str, Any]:
    ensure_app_tables(db_path())
    labels = target_labels()
    labels.update(target_labels_from_spec(spec))
    totals = {"articles_inserted": 0, "mentions_inserted": 0, "stories_touched": 0}
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
            upload_live_checkpoint(job_id, reason="source-run-checkpoint", force=True)
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
    collector = str(spec.get("collector") or DEFAULT_COLLECTOR)
    targets = selected_targets_from_spec(spec, [target_key])
    if not targets:
        return []
    target = targets[0]
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
        for idx, query in enumerate(build_google_queries_for_target(target)):
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
        queries = build_wordpress_queries_for_target(target)
        for site_idx, site in enumerate(WORDPRESS_API_SITES):
            site_name = str(site.get("source_name") or "WordPress").strip() or "WordPress"
            site_queries = site.get("query_variants") if target.key == "flavio_valle" and isinstance(site.get("query_variants"), list) else queries
            for query_idx, query in enumerate(ordered_unique([str(item or "").strip() for item in site_queries if str(item or "").strip()])):
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
        queries = build_internal_search_queries_for_target(target)
        for adapter_idx, adapter in enumerate(FLAVIO_INTERNAL_SEARCH_TARGETS):
            for query_idx, query in enumerate(queries):
                page_size = max(1, int(getattr(adapter, "page_size", 10) or 10))
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
        queries = build_internal_search_queries_for_target(target)
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
        for target_idx, archive_target in enumerate(VEJARIO_ARCHIVE_TARGETS):
            for page in range(1, VEJARIO_MAX_PAGES + 1):
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
        for page in range(1, CAMARA_MAX_PAGES + 1):
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
            ORDER BY id ASC
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
    source_name = str(row["source_name"])
    source_type = str(row["source_type"])
    cursor = safe_json_dict(row.get("cursor_json"))
    mark_source_run_running(source_run_id)
    append_event(
        job_id,
        "source_run_started",
        {
            "source_name": source_name,
            "source_type": source_type,
            "target_key": target_key,
            "target_label": target_label,
            "status": "running",
        },
    )
    try:
        candidates, next_cursor, complete = collect_source_run_candidates(spec, row, cursor)
        if cancel_event.is_set():
            mark_source_run_interrupted(source_run_id, reason="cancel_requested")
            return {"articles_inserted": 0, "mentions_inserted": 0, "stories_touched": 0, "saved": False}
        record_progress(
            job_id,
            "source_collected",
            {"source_name": source_name, "source_type": source_type, "candidates_total": len(candidates)},
            target_key=target_key,
            target_label=target_label,
        )
        options = IngestionOptions(
            target_keys=[target_key],
            target_snapshots=[target_to_snapshot(target) for target in selected_targets_from_spec(spec, [target_key])],
            date_from=str(spec.get("date_from") or ""),
            date_to=str(spec.get("date_to") or ""),
            request_timeout_seconds=10,
            skip_direct_scrape=True,
            max_candidates_per_source=max(1, int(spec.get("max_candidates") or CUSTOM_MAX_CANDIDATES)),
            max_process_seconds=max(10, int(spec.get("max_process_seconds") or CUSTOM_MAX_PROCESS_SECONDS)),
            db_path=str(db_path()),
            cancel_check=cancel_event.is_set,
            archive_full_text=True,
        )
        result = process_candidates(
            source_name,
            source_type,
            candidates,
            options=options,
            progress_callback=lambda event, data, jid=job_id, tk=target_key, tl=target_label: record_progress(
                jid,
                event,
                data,
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
            candidates_total=len(candidates),
            articles_inserted=result.articles_inserted,
            mentions_inserted=result.mentions_inserted,
            stories_touched=result.stories_touched,
            last_error="",
            finished=complete,
        )
        append_event(
            job_id,
            "source_run_complete" if complete else "source_run_checkpoint",
            {
                "source_name": source_name,
                "source_type": source_type,
                "target_key": target_key,
                "target_label": target_label,
                "candidates_seen": result.candidates_seen,
                "candidates_total": len(candidates),
                "articles_inserted": result.articles_inserted,
                "mentions_inserted": result.mentions_inserted,
                "stories_touched": result.stories_touched,
                "status": next_status,
            },
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
                "status": "failed_needs_fix",
                "error": message,
            },
        )
        return {"articles_inserted": 0, "mentions_inserted": 0, "stories_touched": 0, "saved": False}


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
        return candidates, cursor, True

    if source_type == "google_news":
        query = str(cursor.get("query") or "")
        candidates = collect_google_news(
            queries=[query],
            date_from=date_from,
            date_to=date_to,
            limit_per_query=max_candidates,
            request_timeout=request_timeout,
            resolve_timeout=max(2, request_timeout - 2),
        )
        return candidates, cursor, True

    if source_type == "wordpress_api":
        site = WORDPRESS_API_SITES[max(0, int(cursor.get("site_index") or 0))]
        page = max(1, int(cursor.get("page") or 1))
        candidates = collect_wordpress_api(
            str(cursor.get("query") or ""),
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
        complete = len(candidates) < WORDPRESS_PAGE_SIZE or page >= WORDPRESS_MAX_PAGES
        next_cursor = dict(cursor)
        next_cursor["page"] = page + 1 if not complete else page
        return candidates, next_cursor, complete

    if source_type == "internal_search":
        adapter = FLAVIO_INTERNAL_SEARCH_TARGETS[max(0, int(cursor.get("adapter_index") or 0))]
        page = max(1, int(cursor.get("page") or 1))
        page_size = max(1, int(getattr(adapter, "page_size", 10) or 10))
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
        return candidates, next_cursor, complete

    if source_type == "sitemap_daily":
        source = SITEMAP_DAILY_SOURCES[max(0, int(cursor.get("source_index") or 0))]
        day = str(cursor.get("day") or date_from or date_to)
        queries = [str(item or "").strip() for item in list(cursor.get("queries") or []) if str(item or "").strip()]
        candidates = collect_sitemap_daily(
            queries=queries,
            sources=[source],
            date_from=day,
            date_to=day,
            limit_per_source=max_candidates,
            request_timeout=request_timeout,
            collection_timeout=max(30, request_timeout * 4),
        )
        return candidates, cursor, True

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
        return candidates, cursor, True

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
        return candidates, cursor, True

    raise ValueError(f"unknown_source_type:{source_type}")


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


def record_progress(
    job_id: str,
    event: str,
    payload: dict[str, Any],
    *,
    target_key: str = "",
    target_label: str = "",
) -> None:
    if event == "candidate_evaluated":
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
    for row in rows:
        status = str(row.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "coverageState": coverage,
        "sourceRuns": visible_rows,
        "sourceRunCount": len(rows),
        "sourceRunVisibleCount": len(visible_rows),
        "sourceRunCounts": status_counts,
        "failedSources": failed[:20],
        "resumeAvailable": bool(job_status in RESUMABLE_JOB_STATUSES and rows and any(row.get("status") != "complete" for row in rows)),
        "publishedAt": latest_publish_time(job_id),
    }


def progress_summary(job: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    collected_candidates_total = 0
    run_candidates_total = 0
    run_candidates_seen = 0
    sources_total = 0
    latest_by_source: dict[tuple[str, str, str], dict[str, Any]] = {}
    targets: dict[str, str] = {}
    current_target_key = ""
    current_source = ""

    for event in reversed(events):
        payload = event.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        target_key = str(payload.get("target_key") or "")
        target_label = str(payload.get("target_label") or target_key)
        if target_key:
            targets[target_key] = target_label
            current_target_key = target_key
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
    return {"jobId": job_id, "status": str(job.get("status") or ""), "items": items, "count": len(items)}


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
        row = conn.execute(
            """
            SELECT COALESCE(finished_at, started_at, '') AS published_at
            FROM jobs
            WHERE status = 'succeeded' AND kind IN ('update', 'export', 'manual')
            ORDER BY COALESCE(finished_at, started_at, '') DESC
            LIMIT 1
            """
        ).fetchone()
    return str(row["published_at"] or "") if row else ""


def latest_publish_time(job_id: str = "") -> str:
    latest = latest_successful_publish_time()
    params: tuple[Any, ...] = ()
    job_filter = ""
    if job_id:
        job_filter = "AND job_id = ?"
        params = (job_id,)
    with connect(db_path()) as conn:
        row = conn.execute(
            f"""
            SELECT MAX(created_at) AS published_at
            FROM job_events
            WHERE event IN ('export_complete', 'incremental_publish_complete', 'artifacts_uploaded')
              {job_filter}
            """,
            params,
        ).fetchone()
    event_time = str(row["published_at"] or "") if row else ""
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
