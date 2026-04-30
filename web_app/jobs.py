from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pipeline.ingest import IngestionOptions, run_ingestion

from .config import ROOT, db_path
from .db_admin import connect, ensure_app_tables, target_labels, validate_configured_db_file, validate_target_keys
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
        "max_candidates": 250,
        "max_process_seconds": 300,
    },
    "completo": {
        "target_keys": ["flavio_valle", "pedro_angelito", "bernardo_rubiao"],
        "days": 7,
        "max_candidates": 900,
        "max_process_seconds": 900,
    },
}

CUSTOM_MAX_DAYS = 7
CUSTOM_MAX_CANDIDATES = 600
CUSTOM_MAX_PROCESS_SECONDS = 600


class JobConflict(RuntimeError):
    pass


class JobManager:
    def __init__(self, store: ArtifactStore) -> None:
        self.store = store
        self._lock = threading.Lock()
        self._active_job_id: str | None = None

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
            thread = threading.Thread(
                target=self._run,
                args=(job_id, kind, spec),
                name=f"clipping-job-{job_id}",
                daemon=True,
            )
            thread.start()
        return get_job(job_id) or {"id": job_id, "status": "queued"}

    def _run(self, job_id: str, kind: str, spec: dict[str, Any]) -> None:
        try:
            update_job(job_id, status="running")
            self.store.backup_current_artifacts(job_id)
            totals = {"articles_inserted": 0, "mentions_inserted": 0, "stories_touched": 0}

            if kind == "update":
                labels = target_labels()
                for target_key in spec["target_keys"]:
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

            if spec.get("export"):
                update_job(job_id, status="exporting", **totals)
                run_export_snapshot(job_id)

            manifest = {
                "jobId": job_id,
                "kind": kind,
                "spec": {k: v for k, v in spec.items() if k not in {"error"}},
                "totals": totals,
                "finishedAt": datetime.now(timezone.utc).isoformat(),
            }
            uploaded = self.store.upload_current_artifacts(manifest=manifest, job_id=job_id)
            append_event(job_id, "artifacts_uploaded", artifact_upload_summary(uploaded))
            update_job(job_id, status="succeeded", finished_at=datetime.now(timezone.utc).isoformat(), **totals)
        except Exception as exc:
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
    if (date.fromisoformat(date_to) - date.fromisoformat(date_from)).days > CUSTOM_MAX_DAYS:
        raise ValueError("periodo_muito_longo")

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
    candidates_total = 0
    sources_total = 0
    latest_by_source: dict[tuple[str, str, str], dict[str, Any]] = {}
    targets: dict[str, str] = {}

    for event in reversed(events):
        payload = event.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        target_key = str(payload.get("target_key") or "")
        target_label = str(payload.get("target_label") or target_key)
        if target_key:
            targets[target_key] = target_label
        if event.get("event") == "run_started":
            sources_total += safe_int(payload.get("sources_total"))
        if event.get("event") == "source_collected":
            candidates_total += safe_int(payload.get("candidates_total"))
        if event.get("event") in {"source_progress", "source_complete"}:
            source_key = (
                target_key,
                str(payload.get("source_type") or ""),
                str(payload.get("source_name") or payload.get("source") or ""),
            )
            latest_by_source[source_key] = payload

    candidates_seen = sum(safe_int(payload.get("candidates_seen")) for payload in latest_by_source.values())
    return {
        "status": str(job.get("status") or ""),
        "targetKeys": list(targets),
        "targetLabels": targets,
        "sourcesTotal": sources_total,
        "candidatesSeen": candidates_seen,
        "candidatesTotal": candidates_total,
        "articlesInserted": safe_int(job.get("articles_inserted")),
        "mentionsInserted": safe_int(job.get("mentions_inserted")),
        "storiesTouched": safe_int(job.get("stories_touched")),
    }


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
