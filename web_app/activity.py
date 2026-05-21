"""Activity log — captures who did what, when. Backs the "tela de
registros" feature requested by Otávio in 2026-05-19T13:12 ("Uma tela
de registros também seria muito bom").

Design constraints (Goal 4 — regressão-zero):
- record() must NEVER raise — a logging hiccup cannot block a successful
  mutation or login. Errors are swallowed and best-effort.
- Records the *real* session (admin cookie), not the simulated one. When
  admin simulates `?as_profile=X`, the simulated profile lands in details
  so the timeline shows the intent without lying about who acted.
- Table lives next to jobs/job_events in the runtime DB (web_app/db_admin.py
  ensure_app_tables) so the Supabase backup loop already preserves it.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import db_path as _default_db_path


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _resolve_user(session: dict[str, Any] | None) -> tuple[str, str]:
    if not session:
        return ("anonymous", "")
    role = str(session.get("role") or "")
    profile = str(session.get("profile") or "")
    return (role or "unknown", profile)


def record(
    action: str,
    *,
    session: dict[str, Any] | None = None,
    target_key: str | None = None,
    details: dict[str, Any] | None = None,
    db_file: Path | None = None,
) -> None:
    """Insert one activity row. Never raises.

    Args:
        action: short verb identifier (e.g. "login.success", "login.fail",
            "logout", "change_password", "target.create", "target.archive",
            "target.promote", "viewer.create", "viewer.archive").
        session: dict from auth.verify_session() — uses role+profile.
            None for unauthenticated events (failed login).
        target_key: optional target.key when action affects a target.
        details: optional dict serialized as JSON for the details column.
        db_file: optional override (tests). Defaults to config.db_path().
    """
    try:
        path = Path(db_file) if db_file else _default_db_path()
        role, profile = _resolve_user(session)
        details_json = json.dumps(details, ensure_ascii=False) if details else None
        with sqlite3.connect(str(path)) as conn:
            conn.execute(
                "INSERT INTO activity_log (timestamp, user_role, user_profile, action, target_key, details_json) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (_utc_iso_now(), role, profile, str(action), target_key, details_json),
            )
            conn.commit()
    except Exception:
        # Best-effort: never block the caller. The mutation/login already
        # succeeded; a logging failure is an ops concern, not a user one.
        pass


def recent(
    *,
    limit: int = 200,
    since_iso: str | None = None,
    action_prefix: str | None = None,
    profile: str | None = None,
    db_file: Path | None = None,
) -> list[dict[str, Any]]:
    """Return recent activity rows, newest first.

    Filters: since_iso (>= timestamp), action_prefix (LIKE 'X%'), profile
    (exact match on user_profile or target_key). All optional.
    """
    try:
        path = Path(db_file) if db_file else _default_db_path()
        clauses: list[str] = []
        params: list[Any] = []
        if since_iso:
            clauses.append("timestamp >= ?")
            params.append(since_iso)
        if action_prefix:
            clauses.append("action LIKE ?")
            params.append(f"{action_prefix}%")
        if profile:
            clauses.append("(user_profile = ? OR target_key = ?)")
            params.extend([profile, profile])
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = (
            "SELECT id, timestamp, user_role, user_profile, action, target_key, details_json "
            f"FROM activity_log {where} "
            "ORDER BY timestamp DESC, id DESC LIMIT ?"
        )
        params.append(int(limit))
        with sqlite3.connect(str(path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, tuple(params)).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            try:
                details = json.loads(r["details_json"]) if r["details_json"] else None
            except json.JSONDecodeError:
                details = {"raw": r["details_json"]}
            out.append(
                {
                    "id": r["id"],
                    "timestamp": r["timestamp"],
                    "userRole": r["user_role"],
                    "userProfile": r["user_profile"],
                    "action": r["action"],
                    "targetKey": r["target_key"],
                    "details": details,
                }
            )
        return out
    except Exception:
        return []
