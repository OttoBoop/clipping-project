from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pipeline.database import ClippingDB, utc_now_iso
from pipeline.normalization import canonicalize_url, normalize_text

from .config import ROOT, db_path as configured_db_path


TARGETS_PATH = ROOT / "data" / "targets.json"


class ValidationError(ValueError):
    pass


@dataclass(slots=True)
class DuplicateArticle:
    article_id: int
    url: str


def connect(db_file: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def validate_configured_db_file(db_file: Path) -> Path:
    resolved = Path(db_file).expanduser().resolve()
    expected = configured_db_path().expanduser().resolve()
    if resolved != expected:
        raise ValidationError("Banco SQLite nao permitido.")
    return resolved


def ensure_app_tables(db_file: Path) -> None:
    ClippingDB(db_file)
    with connect(db_file) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                preset TEXT,
                target_keys TEXT,
                collector TEXT,
                date_from TEXT,
                date_to TEXT,
                started_by TEXT,
                started_at TEXT,
                finished_at TEXT,
                articles_inserted INTEGER DEFAULT 0,
                mentions_inserted INTEGER DEFAULT 0,
                stories_touched INTEGER DEFAULT 0,
                error_message TEXT
            );

            CREATE TABLE IF NOT EXISTS job_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                event TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS manual_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                story_id INTEGER NOT NULL,
                created_by TEXT,
                created_at TEXT NOT NULL,
                note TEXT,
                FOREIGN KEY(article_id) REFERENCES articles(id),
                FOREIGN KEY(story_id) REFERENCES stories(id)
            );

            CREATE INDEX IF NOT EXISTS idx_jobs_active
                ON jobs(status, started_at)
                WHERE status IN ('queued', 'running', 'exporting');

            CREATE INDEX IF NOT EXISTS idx_job_events_job_id
                ON job_events(job_id, id);

            CREATE UNIQUE INDEX IF NOT EXISTS idx_manual_entries_article
                ON manual_entries(article_id);

            CREATE UNIQUE INDEX IF NOT EXISTS idx_manual_entries_story
                ON manual_entries(story_id);
            """
        )


def load_targets() -> list[dict[str, Any]]:
    rows = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    return [row for row in rows if row.get("key")]


def target_labels() -> dict[str, str]:
    return {str(row["key"]): str(row.get("label") or row["key"]) for row in load_targets()}


def validate_target_keys(values: list[str]) -> list[str]:
    if not isinstance(values, list):
        raise ValidationError("Escolha pelo menos um nome acompanhado.")
    available = target_labels()
    cleaned: list[str] = []
    for value in values:
        key = str(value or "").strip()
        if key and key not in cleaned:
            cleaned.append(key)
    if not cleaned:
        raise ValidationError("Escolha pelo menos um nome acompanhado.")
    missing = [key for key in cleaned if key not in available]
    if missing:
        raise ValidationError("Nome acompanhado desconhecido.")
    return cleaned


def validate_url(value: str) -> str:
    url = canonicalize_url(value)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError("Informe um link com http:// ou https://.")
    return url


def insert_manual_story(db_file: Path, payload: dict[str, Any], *, created_by: str) -> dict[str, Any]:
    db_file = validate_configured_db_file(db_file)
    ensure_app_tables(db_file)
    url = validate_url(str(payload.get("url") or ""))
    title = normalize_text(payload.get("title") or "")
    summary = normalize_text(payload.get("summary") or "")
    full_text = normalize_text(payload.get("full_text") or payload.get("fullText") or "")
    source_name = normalize_text(payload.get("source_name") or payload.get("sourceName") or "Fonte informada manualmente")
    published_at = normalize_text(payload.get("published_at") or payload.get("publishedAt") or "")
    note = normalize_text(payload.get("note") or "")
    target_keys = validate_target_keys(payload.get("target_keys") or payload.get("targetKeys") or [])

    if not title:
        raise ValidationError("Informe o titulo da materia.")
    if not summary and not full_text:
        raise ValidationError("Informe um resumo ou o texto da materia.")

    labels = target_labels()
    story_summary = summary or full_text[:800] or title
    now = utc_now_iso()

    with connect(db_file) as conn:
        existing = conn.execute("SELECT id, url FROM articles WHERE url = ?", (url,)).fetchone()
        if existing:
            return {
                "status": "duplicate",
                "articleId": int(existing["id"]),
                "url": str(existing["url"]),
                "message": "Esta materia ja estava na base.",
            }

        cur = conn.execute(
            """
            INSERT INTO articles (
                url, title, source_name, source_type, published_at, discovered_at,
                snippet, full_text, raw_html, summary, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                url,
                title[:500],
                source_name[:240],
                "manual",
                published_at,
                now,
                summary[:3000],
                full_text[:60000],
                "",
                story_summary[:3000],
                json.dumps({"manual": True, "created_by": created_by}, ensure_ascii=False),
            ),
        )
        article_id = int(cur.lastrowid)

        conn.executemany(
            """
            INSERT INTO mentions (
                article_id, target_key, target_name, keyword_matched,
                sentiment, sentiment_reason, context
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    article_id,
                    key,
                    labels.get(key, key),
                    labels.get(key, key),
                    "neutral",
                    "manual_entry",
                    summary[:1000] or title,
                )
                for key in target_keys
            ],
        )

        story_cur = conn.execute(
            """
            INSERT INTO stories (title, summary, temperature, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title[:220], story_summary[:800], 34.0, now, now),
        )
        story_id = int(story_cur.lastrowid)
        conn.execute("INSERT INTO story_articles (story_id, article_id) VALUES (?, ?)", (story_id, article_id))
        conn.executemany(
            "INSERT OR IGNORE INTO story_targets (story_id, target_key) VALUES (?, ?)",
            [(story_id, key) for key in target_keys],
        )
        conn.execute(
            """
            INSERT INTO manual_entries (article_id, story_id, created_by, created_at, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (article_id, story_id, created_by, datetime.now(timezone.utc).isoformat(), note),
        )

    return {
        "status": "created",
        "articleId": article_id,
        "storyId": story_id,
        "url": url,
        "message": "Materia adicionada como nova historia.",
    }


def latest_jobs(db_file: Path, limit: int = 8) -> list[dict[str, Any]]:
    ensure_app_tables(db_file)
    with connect(db_file) as conn:
        rows = conn.execute(
            """
            SELECT id, kind, status, preset, target_keys, collector, date_from, date_to,
                   started_by, started_at, finished_at, articles_inserted,
                   mentions_inserted, stories_touched, error_message
            FROM jobs
            ORDER BY COALESCE(started_at, '') DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
    return [dict(row) for row in rows]
