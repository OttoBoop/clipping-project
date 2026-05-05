from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pipeline.ingest import IngestionOptions, run_ingestion
from pipeline.database import ClippingDB

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
DEFAULT_COLLECTOR = "all"
EXPORT_TIMEOUT_SECONDS = 300
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

                labels = target_labels()
                for target_key in spec["target_keys"]:
                    if cancel_event.is_set():
                        return
                    target_label = labels.get(target_key, target_key)
                    options = IngestionOptions(
                        target_keys=[target_key],
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
    else:
        raise ValueError("preset_invalido")

    collector = DEFAULT_COLLECTOR
    if collector not in SAFE_COLLECTORS:
        raise ValueError("coletor_invalido")
    if date_from > date_to:
        raise ValueError("periodo_invalido")

    return {
        "preset": preset,
        "collector": collector,
        "target_keys": target_keys,
        "date_from": date_from,
        "date_to": date_to,
        "export": bool(payload.get("export", True)),
        "max_candidates": max_candidates,
        "max_process_seconds": max_process_seconds,
        "skip_direct_scrape": True,
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
                started_by, started_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        {"created_at": event_row["created_at"], "event": event_row["event"], "payload": json.loads(event_row["payload_json"])}
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
        update_job(
            job_id,
            status="interrupted",
            finished_at=now,
            error_message="A atualização foi interrompida por reinício do servidor. Os itens já salvos continuam preservados.",
        )
        append_event(job_id, "job_interrupted", {"status": "interrupted", "reason": reason})
    return len(rows)


def recent_jobs(limit: int = 8) -> list[dict[str, Any]]:
    ensure_app_tables(db_path())
    with connect(db_path()) as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY started_at DESC LIMIT ?", (int(limit),)).fetchall()
    return [with_job_observability(dict(row)) for row in rows]


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
        {"created_at": row["created_at"], "event": row["event"], "payload": json.loads(row["payload_json"])}
        for row in rows
    ]
    job.update(job_observability_from_events(job, events))
    return job


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
    return data


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
        published_cutoff=latest_successful_publish_time(),
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
        published_cutoff=latest_successful_publish_time(),
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
        "status",
        "reason",
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
