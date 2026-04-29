from __future__ import annotations

import json
import subprocess
import sys
import threading
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pipeline.ingest import IngestionOptions, run_ingestion

from .config import ROOT, db_path
from .db_admin import connect, ensure_app_tables, validate_target_keys
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

    def _start(self, kind: str, spec: dict[str, Any], *, started_by: str) -> dict[str, Any]:
        if not self.store.writes_available:
            raise RuntimeError("persistent_storage_not_configured")
        with self._lock:
            if self._active_job_id:
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
                for target_key in spec["target_keys"]:
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
                        progress_callback=lambda event, data, jid=job_id: record_progress(jid, event, data),
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
            append_event(job_id, "artifacts_uploaded", {"count": len(uploaded), "items": uploaded})
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
    if preset == "rapido":
        target_keys = ["flavio_valle"]
        date_from = (today - timedelta(days=1)).isoformat()
        date_to = today.isoformat()
    elif preset == "completo":
        target_keys = ["flavio_valle", "pedro_angelito", "bernardo_rubiao"]
        date_from = (today - timedelta(days=7)).isoformat()
        date_to = today.isoformat()
    elif preset == "custom":
        target_keys = validate_target_keys(payload.get("target_keys") or payload.get("targetKeys") or [])
        date_from = validate_date(str(payload.get("date_from") or payload.get("dateFrom") or ""))
        date_to = validate_date(str(payload.get("date_to") or payload.get("dateTo") or ""))
    else:
        raise ValueError("preset_invalido")

    collector = str(payload.get("collector") or "all").strip()
    if collector == "fast":
        collector = "google_news"
    if collector not in SAFE_COLLECTORS:
        raise ValueError("coletor_invalido")
    if date_from > date_to:
        raise ValueError("periodo_invalido")
    max_days = int(payload.get("max_days") or 30)
    if (date.fromisoformat(date_to) - date.fromisoformat(date_from)).days > max_days:
        raise ValueError("periodo_muito_longo")

    return {
        "preset": preset,
        "collector": collector,
        "target_keys": target_keys,
        "date_from": date_from,
        "date_to": date_to,
        "export": bool(payload.get("export", True)),
        "max_candidates": min(max(int(payload.get("max_candidates") or 600), 25), 3000),
        "max_process_seconds": min(max(int(payload.get("max_process_seconds") or 600), 60), 1800),
    }


def validate_date(raw: str) -> str:
    try:
        return date.fromisoformat(raw).isoformat()
    except Exception as exc:
        raise ValueError("data_invalida") from exc


def run_export_snapshot(job_id: str | None = None) -> None:
    cmd = [
        sys.executable,
        "tools/export_mobile_snapshot.py",
        "--all-stories",
        "--merge-from",
        "index.html",
        "--db",
        str(db_path()),
    ]
    completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300, check=False)
    if completed.returncode != 0:
        raise RuntimeError("export_failed")
    if job_id:
        append_event(job_id, "export_complete", {"lines": len(completed.stdout.splitlines())})


def create_job(job_id: str, kind: str, spec: dict[str, Any], *, started_by: str) -> None:
    with connect(db_path()) as conn:
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


def record_progress(job_id: str, event: str, payload: dict[str, Any]) -> None:
    if event == "candidate_evaluated":
        return
    append_event(job_id, event, payload)


def get_job(job_id: str) -> dict[str, Any] | None:
    ensure_app_tables(db_path())
    with connect(db_path()) as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            return None
        events = conn.execute(
            "SELECT created_at, event, payload_json FROM job_events WHERE job_id = ? ORDER BY id DESC LIMIT 20",
            (job_id,),
        ).fetchall()
    data = dict(row)
    data["events"] = [
        {"created_at": event_row["created_at"], "event": event_row["event"], "payload": json.loads(event_row["payload_json"])}
        for event_row in events
    ]
    return data


def recent_jobs(limit: int = 8) -> list[dict[str, Any]]:
    ensure_app_tables(db_path())
    with connect(db_path()) as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY started_at DESC LIMIT ?", (int(limit),)).fetchall()
    return [dict(row) for row in rows]


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
        "status",
        "count",
        "items",
        "lines",
    }
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        if key in allowed:
            safe[key] = value
        elif key == "errors":
            safe[key] = ["erro_de_coleta" for _ in list(value or [])[:3]]
    return safe


def sanitize_error(exc: Exception) -> str:
    text = str(exc) or exc.__class__.__name__
    if "export_failed" in text:
        return "Falha ao exportar o painel."
    if "unknown_target_keys" in text:
        return "Nome acompanhado desconhecido."
    return text[:160]


job_manager = JobManager(artifact_store)

