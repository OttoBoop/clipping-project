from __future__ import annotations

import json
import os
import re
import sqlite3
import tempfile
import unicodedata
import html
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pipeline.database import ClippingDB, utc_now_iso
from pipeline.normalization import canonicalize_url, normalize_text

from .config import ROOT, db_path as configured_db_path


TARGETS_PATH = ROOT / "data" / "targets.json"
PRIMARY_TARGET_KEYS = ("flavio_valle", "pedro_angelito")
SYNTHETIC_SMOKE_TITLE = "Atlas smoke test: manual unique story flow for Flavio Valle"
SYNTHETIC_SMOKE_SOURCES = {
    "atlas smoke test",
    "atlas smoke test manual",
    "manual smoke test",
}
SYNTHETIC_TARGET_MARKERS = ("atlas_teste", "atlas teste")
SLUG_RE = re.compile(r"[^a-z0-9]+")
TAG_RE = re.compile(r"<[^>]+>")
RELATED_MATCH_NOISE_RE = re.compile(
    r"(?is)\b(not[ií]cias?\s+relacionadas?|leia\s+tamb[eé]m|veja\s+tamb[eé]m|textos?\s+relacionados?|links?\s+relacionados?)\b.*"
)


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
                error_message TEXT,
                spec_json TEXT
            );

            CREATE TABLE IF NOT EXISTS job_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                event TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS job_source_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                target_key TEXT NOT NULL,
                source_key TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                status TEXT NOT NULL,
                cursor_json TEXT NOT NULL DEFAULT '{}',
                candidates_seen INTEGER DEFAULT 0,
                candidates_total INTEGER DEFAULT 0,
                articles_inserted INTEGER DEFAULT 0,
                mentions_inserted INTEGER DEFAULT 0,
                stories_touched INTEGER DEFAULT 0,
                attempts INTEGER DEFAULT 0,
                last_error TEXT,
                started_at TEXT,
                updated_at TEXT NOT NULL,
                finished_at TEXT,
                UNIQUE(job_id, target_key, source_key)
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
                WHERE status IN ('queued', 'running', 'exporting', 'cancel_requested');

            CREATE INDEX IF NOT EXISTS idx_job_events_job_id
                ON job_events(job_id, id);

            CREATE INDEX IF NOT EXISTS idx_job_source_runs_job_status
                ON job_source_runs(job_id, status, id);

            CREATE INDEX IF NOT EXISTS idx_job_source_runs_source
                ON job_source_runs(source_type, source_name);

            CREATE UNIQUE INDEX IF NOT EXISTS idx_manual_entries_article
                ON manual_entries(article_id);

            CREATE UNIQUE INDEX IF NOT EXISTS idx_manual_entries_story
                ON manual_entries(story_id);
            """
        )
        for statement in (
            "ALTER TABLE jobs ADD COLUMN spec_json TEXT",
        ):
            try:
                conn.execute(statement)
            except sqlite3.OperationalError:
                pass


def is_synthetic_test_target(row: dict[str, Any]) -> bool:
    key = str(row.get("key") or "").strip().lower()
    label = str(row.get("label") or row.get("display_name") or "").strip().lower()
    return any(marker in key or marker in label for marker in SYNTHETIC_TARGET_MARKERS)


def archive_metadata(reason: str) -> dict[str, Any]:
    return {
        "archived": True,
        "archived_at": utc_now_iso(),
        "archive_reason": normalize_text(reason or "Arquivado pela equipe."),
    }


def maybe_auto_archive_synthetic_targets(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    archived_keys: list[str] = []
    for row in rows:
        key = str(row.get("key") or "").strip()
        if not key or key in PRIMARY_TARGET_KEYS or bool(row.get("archived")):
            continue
        if not is_synthetic_test_target(row):
            continue
        row.update(archive_metadata("Alvo de teste arquivado automaticamente."))
        archived_keys.append(key)
    return rows, archived_keys


def load_targets() -> list[dict[str, Any]]:
    rows = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    rows = [row for row in rows if row.get("key")]
    rows, archived_keys = maybe_auto_archive_synthetic_targets(rows)
    if archived_keys:
        write_targets_atomic(rows)
    return rows


def normalize_target_slug(value: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    return SLUG_RE.sub("_", ascii_text.lower()).strip("_") or "target"


def ordered_clean_strings(value: Any, *, max_items: int = 24, max_length: int = 120) -> list[str]:
    if value is None:
        return []
    raw_items = value if isinstance(value, list) else [value]
    seen: set[str] = set()
    cleaned: list[str] = []
    for item in raw_items:
        text = normalize_text(item or "")[:max_length]
        if len(text) < 2 or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
        if len(cleaned) >= max_items:
            break
    return cleaned


def unique_target_slug(display_name: str, existing_keys: set[str]) -> str:
    base = normalize_target_slug(display_name)
    candidate = base
    index = 2
    while candidate in existing_keys or candidate in PRIMARY_TARGET_KEYS:
        candidate = f"{base}_{index}"
        index += 1
    return candidate


def locked_primary_keys() -> list[str]:
    return list(PRIMARY_TARGET_KEYS)


def primary_target_keys() -> list[str]:
    return locked_primary_keys()


def sanitize_target(row: dict[str, Any]) -> dict[str, Any]:
    key = str(row.get("key") or "").strip()
    if not key:
        return {}
    display_name = normalize_text(row.get("display_name") or row.get("label") or key)
    label = normalize_text(row.get("label") or display_name or key)
    primary = key in PRIMARY_TARGET_KEYS
    target = {
        "key": key,
        "label": label or key,
        "display_name": display_name or label or key,
        "className": "primary" if primary else "",
        "primary": primary,
        "archived": bool(row.get("archived")),
        "keywords": ordered_clean_strings(row.get("keywords")),
        "exact_aliases": ordered_clean_strings(row.get("exact_aliases") or row.get("aliases")),
    }
    if target["archived"]:
        target["archived_at"] = str(row.get("archived_at") or "")
        target["archive_reason"] = normalize_text(row.get("archive_reason") or "Arquivado pela equipe.")
    return target


def normalize_targets(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        target = sanitize_target(row)
        key = str(target.get("key") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        normalized.append(target)
    return normalized


def normalize_targets_file() -> bool:
    rows = load_targets()
    normalized = normalize_targets(rows)
    if normalized == rows:
        return False
    write_targets_atomic(normalized)
    return True


def public_targets(*, include_archived: bool = False) -> dict[str, Any]:
    targets = [
        target
        for target in normalize_targets(load_targets())
        if target and (include_archived or not target.get("archived"))
    ]
    return {"targets": targets, "primaryKeys": locked_primary_keys()}


def list_public_targets() -> dict[str, Any]:
    return public_targets()


def write_targets_atomic(rows: list[dict[str, Any]]) -> None:
    TARGETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{TARGETS_PATH.name}.", suffix=".tmp", dir=str(TARGETS_PATH.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, TARGETS_PATH)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def find_target_index(rows: list[dict[str, Any]], key: str) -> int:
    normalized = str(key or "").strip()
    for index, row in enumerate(rows):
        if str(row.get("key") or "").strip() == normalized:
            return index
    raise ValidationError("Nome acompanhado desconhecido.")


def ensure_secondary_mutable(row: dict[str, Any]) -> None:
    key = str(row.get("key") or "").strip()
    if key in PRIMARY_TARGET_KEYS:
        raise ValidationError("Nomes principais nao podem ser editados por aqui.")


def clean_target_payload(payload: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    existing = existing or {}
    display_name = normalize_text(
        payload.get("display_name")
        or payload.get("displayName")
        or payload.get("label")
        or payload.get("name")
        or existing.get("display_name")
        or existing.get("label")
        or ""
    )
    if len(display_name) < 3:
        raise ValidationError("Informe um nome de exibicao com pelo menos 3 caracteres.")
    keywords_source = payload.get("keywords")
    if keywords_source is None:
        keywords_source = existing.get("keywords")
    aliases_source = payload.get("exact_aliases")
    if aliases_source is None:
        aliases_source = payload.get("exactAliases")
    if aliases_source is None:
        aliases_source = payload.get("aliases")
    if aliases_source is None:
        aliases_source = existing.get("exact_aliases") or existing.get("aliases")
    keywords = ordered_clean_strings(keywords_source)
    aliases = ordered_clean_strings(aliases_source)
    if display_name not in keywords:
        keywords = [display_name, *keywords]
    return {
        "display_name": display_name,
        "label": display_name,
        "keywords": keywords,
        "exact_aliases": aliases,
    }


def create_secondary_target(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = clean_target_payload(payload)

    rows = normalize_targets(load_targets())

    new_name_folded = cleaned["display_name"].casefold()
    for row in rows:
        if bool(row.get("archived")):
            continue
        existing_name = normalize_text(row.get("display_name") or row.get("label") or "")
        if existing_name.casefold() == new_name_folded:
            raise ValidationError(
                f"Já existe um nome cadastrado como '{row.get('label') or existing_name}'. Escolha um nome diferente ou edite o existente."
            )

    existing_keys = {str(row.get("key") or "").strip() for row in rows}
    key = unique_target_slug(cleaned["display_name"], existing_keys)
    target = {
        "key": key,
        "label": cleaned["display_name"],
        "display_name": cleaned["display_name"],
        "className": "",
        "primary": False,
        "keywords": cleaned["keywords"],
    }
    if cleaned["exact_aliases"]:
        target["exact_aliases"] = cleaned["exact_aliases"]
    if is_synthetic_test_target(target):
        target.update(archive_metadata("Alvo de teste arquivado automaticamente."))
    rows.append(target)
    write_targets_atomic(normalize_targets(rows))
    return sanitize_target(target)


def update_secondary_target(key: str, payload: dict[str, Any]) -> dict[str, Any]:
    rows = normalize_targets(load_targets())
    index = find_target_index(rows, key)
    row = rows[index]
    ensure_secondary_mutable(row)
    if bool(row.get("archived")):
        raise ValidationError("Restaure o nome antes de editar.")
    cleaned = clean_target_payload(payload, row)
    row["label"] = cleaned["display_name"]
    row["display_name"] = cleaned["display_name"]
    row["className"] = ""
    row["primary"] = False
    row["keywords"] = cleaned["keywords"]
    if cleaned["exact_aliases"]:
        row["exact_aliases"] = cleaned["exact_aliases"]
    else:
        row.pop("exact_aliases", None)
        row.pop("aliases", None)
    if is_synthetic_test_target(row):
        row.update(archive_metadata("Alvo de teste arquivado automaticamente."))
    write_targets_atomic(normalize_targets(rows))
    return sanitize_target(row)


def archive_secondary_target(key: str, reason: str = "") -> dict[str, Any]:
    rows = normalize_targets(load_targets())
    index = find_target_index(rows, key)
    row = rows[index]
    ensure_secondary_mutable(row)
    if not bool(row.get("archived")):
        row.update(archive_metadata(reason or "Arquivado pela equipe."))
        write_targets_atomic(normalize_targets(rows))
    return sanitize_target(row)


def restore_secondary_target(key: str) -> dict[str, Any]:
    rows = normalize_targets(load_targets())
    index = find_target_index(rows, key)
    row = rows[index]
    ensure_secondary_mutable(row)
    if is_synthetic_test_target(row):
        raise ValidationError("Alvos de teste nao podem ser restaurados.")
    if bool(row.get("archived")):
        row["archived"] = False
        row.pop("archived_at", None)
        row.pop("archive_reason", None)
        write_targets_atomic(normalize_targets(rows))
    return sanitize_target(row)


def archive_known_test_targets() -> dict[str, Any]:
    rows = normalize_targets(json.loads(TARGETS_PATH.read_text(encoding="utf-8")))
    rows, archived_keys = maybe_auto_archive_synthetic_targets(rows)
    if archived_keys:
        write_targets_atomic(normalize_targets(rows))
    return {"archived": archived_keys, "archivedCount": len(archived_keys)}


def target_labels(*, include_archived: bool = False) -> dict[str, str]:
    return {
        str(row["key"]): str(row.get("label") or row.get("display_name") or row["key"])
        for row in normalize_targets(load_targets())
        if include_archived or not bool(row.get("archived"))
    }


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


def selected_active_targets(target_keys: list[str]) -> list[Any]:
    selected = {str(key or "").strip() for key in target_keys if str(key or "").strip()}
    if not selected:
        return []
    from pipeline.settings import get_active_targets

    return [target for target in get_active_targets() if str(target.key) in selected]


def target_matches_safe_article_fields(target: Any, row: sqlite3.Row | dict[str, Any]) -> bool:
    from pipeline.matcher import CitationMatcher

    return bool(CitationMatcher([target], exact_names_only=True).find_hits(safe_article_match_text(row)))


def safe_article_match_text(row: sqlite3.Row | dict[str, Any]) -> str:
    def value(key: str) -> str:
        try:
            return str(row[key] or "")
        except (KeyError, IndexError):
            return ""

    body_parts: list[str] = []
    if value("summary"):
        body_parts.append(value("summary")[:500])
    if value("full_text"):
        body_parts.append(value("full_text")[:500])
    if not body_parts:
        body_parts.append(value("snippet")[:500])
    raw_text = " ".join([value("title"), *body_parts])
    text = html.unescape(TAG_RE.sub(" ", raw_text))
    text = RELATED_MATCH_NOISE_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def cleanup_false_backfilled_target_mentions(db_file: Path, target_keys: list[str]) -> dict[str, Any]:
    """Remove secondary target matches that are absent from title/snippet/summary."""
    db_file = validate_configured_db_file(db_file)
    ensure_app_tables(db_file)
    targets = selected_active_targets(target_keys)
    if not targets:
        return {"removedMentions": 0, "storiesTouched": 0}

    removed_mentions = 0
    touched_stories: set[int] = set()
    with connect(db_file) as conn:
        for target in targets:
            rows = conn.execute(
                """
                SELECT
                    m.id AS mention_id,
                    m.article_id,
                    a.title,
                    a.snippet,
                    a.full_text,
                    a.summary,
                    sa.story_id
                FROM mentions m
                JOIN articles a ON a.id = m.article_id
                LEFT JOIN story_articles sa ON sa.article_id = a.id
                WHERE m.target_key = ?
                """,
                (target.key,),
            ).fetchall()
            for row in rows:
                if target_matches_safe_article_fields(target, row):
                    continue
                mention_id = int(row["mention_id"])
                story_id = int(row["story_id"] or 0)
                conn.execute("DELETE FROM classifications WHERE mention_id = ?", (mention_id,))
                conn.execute("DELETE FROM mentions WHERE id = ?", (mention_id,))
                removed_mentions += 1
                if not story_id:
                    continue
                remaining = conn.execute(
                    """
                    SELECT 1
                    FROM story_articles sa
                    JOIN mentions m ON m.article_id = sa.article_id
                    WHERE sa.story_id = ? AND m.target_key = ?
                    LIMIT 1
                    """,
                    (story_id, target.key),
                ).fetchone()
                if not remaining:
                    conn.execute(
                        "DELETE FROM story_targets WHERE story_id = ? AND target_key = ?",
                        (story_id, target.key),
                    )
                conn.execute("UPDATE stories SET updated_at = ? WHERE id = ?", (utc_now_iso(), story_id))
                touched_stories.add(story_id)
    return {"removedMentions": removed_mentions, "storiesTouched": len(touched_stories)}


def backfill_missing_target_mentions(db_file: Path, target_keys: list[str]) -> dict[str, Any]:
    """Attach selected active targets to existing articles whose saved text matches them."""
    db_file = validate_configured_db_file(db_file)
    ensure_app_tables(db_file)
    from pipeline.matcher import CitationMatcher

    targets = selected_active_targets(target_keys)
    if not targets:
        return {"updated": [], "updatedCount": 0, "mentionsInserted": 0, "storiesTouched": 0}

    db = ClippingDB(db_file)
    updated: list[dict[str, Any]] = []
    touched_stories: set[int] = set()
    with connect(db_file) as conn:
        article_rows = conn.execute(
            """
            SELECT
                a.id,
                a.title,
                a.url,
                a.source_name,
                a.source_type,
                COALESCE(a.published_at, a.discovered_at) AS published_at,
                a.snippet,
                a.full_text,
                a.summary,
                sa.story_id
            FROM articles a
            LEFT JOIN story_articles sa ON sa.article_id = a.id
            ORDER BY COALESCE(a.published_at, a.discovered_at) DESC
            """
        ).fetchall()

    for target in targets:
        matcher = CitationMatcher([target], exact_names_only=True)
        for row in article_rows:
            article_id = int(row["id"])
            if db.find_mention_id(article_id, target.key) is not None:
                continue
            hits = matcher.find_hits(safe_article_match_text(row))
            if not hits:
                continue
            hit = hits[0]
            db.insert_mentions(
                article_id,
                [
                    {
                        "target_key": hit.target_key,
                        "target_name": hit.target_name,
                        "keyword_matched": hit.keyword_matched,
                        "sentiment": "neutral",
                        "sentiment_reason": "existing_article_backfill",
                        "context": "",
                    }
                ],
            )
            story_id = int(row["story_id"] or 0)
            if not story_id:
                story_id = db.create_story(
                    title=str(row["title"] or "Nova historia")[:220],
                    summary=str(row["summary"] or row["snippet"] or row["title"] or "Nova historia")[:800],
                    temperature=34.0,
                    target_keys=[target.key],
                )
                db.attach_article_to_story(story_id, article_id)
            db.ensure_story_target(story_id, target.key)
            db.update_story(story_id)
            touched_stories.add(story_id)
            updated.append(
                {
                    "article_id": article_id,
                    "story_id": story_id,
                    "target_key": target.key,
                    "target_label": target.display_name or target.label or target.key,
                    "keyword_matched": hit.keyword_matched,
                    "title": str(row["title"] or ""),
                    "url": str(row["url"] or ""),
                    "source_name": str(row["source_name"] or ""),
                    "source_type": str(row["source_type"] or ""),
                    "published_at": str(row["published_at"] or ""),
                }
            )

    return {
        "updated": updated,
        "updatedCount": len(updated),
        "mentionsInserted": len(updated),
        "storiesTouched": len(touched_stories),
    }


def cleanup_synthetic_smoke_artifacts(db_file: Path) -> dict[str, Any]:
    """Remove only the known production manual smoke artifact."""
    db_file = validate_configured_db_file(db_file)
    ensure_app_tables(db_file)
    with connect(db_file) as conn:
        rows = conn.execute(
            """
            SELECT id, title, source_name, url
            FROM articles
            WHERE lower(url) IN ('https://example.com', 'http://example.com')
               OR lower(url) LIKE 'https://example.com/%'
               OR lower(url) LIKE 'http://example.com/%'
            """
        ).fetchall()
        article_ids: list[int] = []
        for row in rows:
            title = str(row["title"] or "").strip()
            source_name = str(row["source_name"] or "").strip().lower()
            if title == SYNTHETIC_SMOKE_TITLE or source_name in SYNTHETIC_SMOKE_SOURCES:
                article_ids.append(int(row["id"]))

        if not article_ids:
            return {
                "articlesRemoved": 0,
                "mentionsRemoved": 0,
                "storiesRemoved": 0,
                "storyLinksRemoved": 0,
            }

        placeholders = ",".join("?" for _ in article_ids)
        story_rows = conn.execute(
            f"SELECT DISTINCT story_id FROM story_articles WHERE article_id IN ({placeholders})",
            article_ids,
        ).fetchall()
        story_ids = [int(row["story_id"]) for row in story_rows]

        mention_rows = conn.execute(f"SELECT id FROM mentions WHERE article_id IN ({placeholders})", article_ids).fetchall()
        mention_ids = [int(row["id"]) for row in mention_rows]
        mentions_removed = len(mention_ids)
        if mention_ids:
            mention_placeholders = ",".join("?" for _ in mention_ids)
            classification_rows = conn.execute(
                f"SELECT id FROM classifications WHERE mention_id IN ({mention_placeholders})",
                mention_ids,
            ).fetchall()
            classification_ids = [int(row["id"]) for row in classification_rows]
            if classification_ids:
                classification_placeholders = ",".join("?" for _ in classification_ids)
                conn.execute(
                    f"DELETE FROM classification_categories WHERE classification_id IN ({classification_placeholders})",
                    classification_ids,
                )
            conn.execute(f"DELETE FROM classifications WHERE mention_id IN ({mention_placeholders})", mention_ids)

        conn.execute(f"DELETE FROM mentions WHERE article_id IN ({placeholders})", article_ids)
        story_links_removed = conn.execute(
            f"DELETE FROM story_articles WHERE article_id IN ({placeholders})",
            article_ids,
        ).rowcount
        conn.execute(f"DELETE FROM articles WHERE id IN ({placeholders})", article_ids)

        stories_removed = 0
        for story_id in story_ids:
            remaining = conn.execute("SELECT 1 FROM story_articles WHERE story_id = ? LIMIT 1", (story_id,)).fetchone()
            story = conn.execute("SELECT title FROM stories WHERE id = ?", (story_id,)).fetchone()
            story_title = str(story["title"] or "").strip() if story else ""
            if remaining and story_title != SYNTHETIC_SMOKE_TITLE:
                continue
            conn.execute("DELETE FROM story_targets WHERE story_id = ?", (story_id,))
            deleted = conn.execute("DELETE FROM stories WHERE id = ?", (story_id,)).rowcount
            stories_removed += max(0, int(deleted or 0))

    return {
        "articlesRemoved": len(article_ids),
        "mentionsRemoved": mentions_removed,
        "storiesRemoved": stories_removed,
        "storyLinksRemoved": max(0, int(story_links_removed or 0)),
    }


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
        "title": title[:500],
        "sourceName": source_name[:240],
        "sourceType": "manual",
        "publishedAt": published_at,
        "targetKeys": target_keys,
        "targetLabels": {key: labels.get(key, key) for key in target_keys},
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
