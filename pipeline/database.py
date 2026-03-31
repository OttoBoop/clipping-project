"""SQLite wrapper for the clipping pipeline.

RECOVERY NOTE (2026-03-30):
This file was reconstructed from a 63 MB Codex session log
(D:/recovery/YOUR_FILES/recovered_224598MB_63334KB.py).

Verbatim sections recovered from multiple Get-Content outputs and
JSON-embedded file dumps.  Sections marked [RECONSTRUCTED] were filled
in from surrounding context, apply_patch diffs, and call-site evidence
in export_mobile_snapshot.py.  All other code is byte-for-byte verbatim
from the session log.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    published_at TEXT,
    discovered_at TEXT NOT NULL,
    snippet TEXT,
    full_text TEXT,
    raw_html TEXT,
    summary TEXT,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    target_key TEXT NOT NULL,
    target_name TEXT NOT NULL,
    keyword_matched TEXT NOT NULL,
    sentiment TEXT NOT NULL DEFAULT 'neutral',
    sentiment_reason TEXT,
    context TEXT,
    FOREIGN KEY(article_id) REFERENCES articles(id)
);

CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    temperature REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS story_articles (
    story_id INTEGER NOT NULL,
    article_id INTEGER NOT NULL UNIQUE,
    FOREIGN KEY(story_id) REFERENCES stories(id),
    FOREIGN KEY(article_id) REFERENCES articles(id)
);

CREATE TABLE IF NOT EXISTS story_targets (
    story_id INTEGER NOT NULL,
    target_key TEXT NOT NULL,
    UNIQUE(story_id, target_key),
    FOREIGN KEY(story_id) REFERENCES stories(id)
);

CREATE TABLE IF NOT EXISTS scrape_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    articles_found INTEGER DEFAULT 0,
    mentions_found INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS backfill_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    current_date TEXT NOT NULL,
    current_page INTEGER DEFAULT 1,
    status TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(query, start_date, end_date)
);
"""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ClippingDB:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # Compat: tools and tests use `with ClippingDB(path) as db:` pattern.
    # Original used connect() context manager; these bridge the gap.
    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self

    def __exit__(self, *args):
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
            self.conn = None

    def close(self):
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
            self.conn = None

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA_SQL)

    # Compat methods: simplified API used by rewritten ingest.py, server.py, tests
    def article_exists(self, url):
        with self.connect() as conn:
            row = conn.execute("SELECT 1 FROM articles WHERE url = ?", (url,)).fetchone()
            return row is not None

    def insert_article(self, url, title, source_name, source_type, published_at, snippet, full_text=None):
        aid, is_new = self.insert_article_if_new(
            url=url, title=title, source_name=source_name, source_type=source_type,
            published_at=published_at, snippet=snippet, full_text=full_text or "",
            raw_html="", summary="", metadata_json="",
        )
        return aid if is_new else None

    def insert_mention(self, article_id, target_key, target_name, keyword_matched):
        self.insert_mentions(article_id, [{
            "target_key": target_key, "target_name": target_name,
            "keyword_matched": keyword_matched,
        }])

    def count_articles(self):
        with self.connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]

    def count_mentions(self):
        with self.connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0]

    # ------------------------------------------------------------------
    # VERBATIM from session log (lines 111-151)
    # ------------------------------------------------------------------
    def insert_article_if_new(
        self,
        *,
        url: str,
        title: str,
        source_name: str,
        source_type: str,
        published_at: str,
        snippet: str,
        full_text: str,
        raw_html: str,
        summary: str,
        metadata_json: str,
    ) -> tuple[int, bool]:
        with self.connect() as conn:
            row = conn.execute("SELECT id FROM articles WHERE url = ?", (url,)).fetchone()
            if row:
                return int(row["id"]), False
            discovered_at = utc_now_iso()
            cur = conn.execute(
                """
                INSERT INTO articles (
                    url, title, source_name, source_type, published_at, discovered_at,
                    snippet, full_text, raw_html, summary, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    url,
                    title,
                    source_name,
                    source_type,
                    published_at,
                    discovered_at,
                    snippet,
                    full_text,
                    raw_html,
                    summary,
                    metadata_json,
                ),
            )
            return int(cur.lastrowid), True

    # ------------------------------------------------------------------
    # VERBATIM from session log (lines 153-174)
    # ------------------------------------------------------------------
    def insert_mentions(self, article_id: int, mentions: list[dict]) -> None:
        if not mentions:
            return
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT INTO mentions (article_id, target_key, target_name, keyword_matched, sentiment, sentiment_reason, context)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        article_id,
                        m["target_key"],
                        m["target_name"],
                        m["keyword_matched"],
                        m.get("sentiment", "neutral"),
                        m.get("sentiment_reason", ""),
                        m.get("context", ""),
                    )
                    for m in mentions
                ],
            )

    # ------------------------------------------------------------------
    # VERBATIM from session log (lines 176-185)
    # ------------------------------------------------------------------
    def list_recent_stories(self, days: int = 7) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT * FROM stories
                WHERE updated_at >= datetime('now', ?)
                ORDER BY temperature DESC, updated_at DESC
                """,
                (f"-{days} days",),
            ).fetchall()

    # ------------------------------------------------------------------
    # VERBATIM from session log (lines 187-220+)
    # ------------------------------------------------------------------
    def list_story_context(self, *, days: int = 365, limit: int = 160) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    s.id,
                    s.title,
                    s.summary,
                    s.updated_at,
                    s.temperature,
                    COUNT(sa.article_id) AS article_count,
                    GROUP_CONCAT(DISTINCT st.target_key) AS target_keys
                FROM stories s
                LEFT JOIN story_articles sa ON sa.story_id = s.id
                LEFT JOIN story_targets st ON st.story_id = s.id
                WHERE s.updated_at >= datetime('now', ?)
                GROUP BY s.id
                ORDER BY s.updated_at DESC, s.temperature DESC
                LIMIT ?
                """,
                (f"-{max(1, int(days))} days", max(1, int(limit))),
            ).fetchall()
            payload: list[dict] = []
            for row in rows:
                payload.append(
                    {
                        "story_id": int(row["id"]),
                        "title": row["title"] or "",
                        "summary": row["summary"] or "",
                        "updated_at": row["updated_at"] or "",
                        "temperature": float(row["temperature"] or 0.0),
                        "article_count": int(row["article_count"] or 0),
                        "target_keys": [v for v in str(row["target_keys"] or "").split(",") if v],
                    }
                )
            return payload

    # ------------------------------------------------------------------
    # VERBATIM from session log offset 5900000 (lines ~223-253)
    # ------------------------------------------------------------------
    def log_scrape_start(self, source_name: str, source_type: str) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO scrape_log (source_name, source_type, started_at, status)
                VALUES (?, ?, ?, 'running')
                """,
                (source_name, source_type, utc_now_iso()),
            )
            return int(cur.lastrowid)

    def log_scrape_end(
        self,
        log_id: int,
        *,
        articles_found: int,
        mentions_found: int,
        status: str,
        error_message: str = "",
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE scrape_log
                SET finished_at = ?, articles_found = ?, mentions_found = ?, status = ?, error_message = ?
                WHERE id = ?
                """,
                (utc_now_iso(), articles_found, mentions_found, status, error_message, log_id),
            )

    # ------------------------------------------------------------------
    # VERBATIM from session log offset 5900000 (lines ~255-282)
    # ------------------------------------------------------------------
    def get_backfill_state(self, query: str, start_date: str, end_date: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM backfill_state
                WHERE query = ? AND start_date = ? AND end_date = ?
                """,
                (query, start_date, end_date),
            ).fetchone()
            if not row:
                return None
            return {
                "id": int(row["id"]),
                "query": row["query"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "current_date": row["current_date"],
                "current_page": int(row["current_page"]),
                "status": row["status"],
                "updated_at": row["updated_at"],
            }

    # ------------------------------------------------------------------
    # [RECONSTRUCTED] from schema + pattern in get_backfill_state
    # ------------------------------------------------------------------
    def upsert_backfill_state(
        self,
        *,
        query: str,
        start_date: str,
        end_date: str,
        current_date: str,
        current_page: int,
        status: str,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO backfill_state (query, start_date, end_date, current_date, current_page, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(query, start_date, end_date) DO UPDATE SET
                    current_date = excluded.current_date,
                    current_page = excluded.current_page,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (query, start_date, end_date, current_date, current_page, status, utc_now_iso()),
            )

    # ------------------------------------------------------------------
    # VERBATIM from session log (Skip 300 output, lines 301-311)
    # ------------------------------------------------------------------
    def story_article_stats(self, story_id: int) -> tuple[int, int]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(sa.article_id) AS article_count,
                    COUNT(DISTINCT a.source_name) AS unique_sources
                FROM story_articles sa
                JOIN articles a ON a.id = sa.article_id
                WHERE sa.story_id = ?
                """,
                (int(story_id),),
            ).fetchone()
            if not row:
                return 0, 0
            return int(row["article_count"] or 0), int(row["unique_sources"] or 0)

    # ------------------------------------------------------------------
    # [RECONSTRUCTED] from schema + ingest.py call signatures + class patterns
    # story_article_stats is RECOVERED (SQL body from session log)
    # ------------------------------------------------------------------
    def create_story(
        self,
        title: str,
        summary: str,
        temperature: float,
        target_keys: list[str],
    ) -> int:
        now = utc_now_iso()
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO stories (title, summary, temperature, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, summary, float(temperature), now, now),
            )
            story_id = int(cur.lastrowid)
            if target_keys:
                conn.executemany(
                    """
                    INSERT OR IGNORE INTO story_targets (story_id, target_key)
                    VALUES (?, ?)
                    """,
                    [(story_id, tkey) for tkey in target_keys],
                )
            return story_id

    def attach_article_to_story(self, story_id: int, article_id: int) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO story_articles (story_id, article_id)
                VALUES (?, ?)
                """,
                (int(story_id), int(article_id)),
            )

    def ensure_story_target(self, story_id: int, tkey: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO story_targets (story_id, target_key)
                VALUES (?, ?)
                """,
                (int(story_id), str(tkey)),
            )

    def update_story(
        self,
        story_id: int,
        temperature: float | None = None,
    ) -> None:
        now = utc_now_iso()
        with self.connect() as conn:
            if temperature is not None:
                conn.execute(
                    """
                    UPDATE stories
                    SET temperature = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (float(temperature), now, int(story_id)),
                )
            else:
                conn.execute(
                    """
                    UPDATE stories
                    SET updated_at = ?
                    WHERE id = ?
                    """,
                    (now, int(story_id)),
                )

    def get_story_targets(self, story_id: int) -> list[str]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT target_key FROM story_targets WHERE story_id = ?",
                (int(story_id),),
            ).fetchall()
            return [row["target_key"] for row in rows]

    # ------------------------------------------------------------------
    # VERBATIM from session log (block 10 extraction, lines 312-411)
    # [RECONSTRUCTED] lines 412-430: closing of article dict and output.append
    # ------------------------------------------------------------------
    def story_with_articles(self) -> list[dict]:
        with self.connect() as conn:
            stories = conn.execute(
                "SELECT * FROM stories ORDER BY temperature DESC, updated_at DESC"
            ).fetchall()
            if not stories:
                return []

            # Fast path: avoid N+1 queries by preloading targets, articles, and mention aggregates.
            story_ids = [int(s["id"]) for s in stories]
            placeholders = ", ".join("?" for _ in story_ids)

            targets_map: dict[int, list[str]] = {sid: [] for sid in story_ids}
            for row in conn.execute(
                f"SELECT story_id, target_key FROM story_targets WHERE story_id IN ({placeholders})",
                tuple(story_ids),
            ).fetchall():
                try:
                    targets_map[int(row["story_id"])].append(str(row["target_key"] or "").strip())
                except Exception:
                    continue

            article_rows = conn.execute(
                f"""
                SELECT
                    sa.story_id AS story_id,
                    a.id AS id,
                    a.title AS title,
                    a.url AS url,
                    a.source_name AS source_name,
                    a.published_at AS published_at,
                    a.discovered_at AS discovered_at,
                    a.summary AS summary,
                    a.snippet AS snippet
                FROM story_articles sa
                JOIN articles a ON a.id = sa.article_id
                WHERE sa.story_id IN ({placeholders})
                ORDER BY sa.story_id ASC, COALESCE(a.published_at, a.discovered_at) DESC
                """,
                tuple(story_ids),
            ).fetchall()

            articles_by_story: dict[int, list[sqlite3.Row]] = {sid: [] for sid in story_ids}
            article_ids: list[int] = []
            for row in article_rows:
                try:
                    sid = int(row["story_id"])
                    aid = int(row["id"])
                except Exception:
                    continue
                articles_by_story.setdefault(sid, []).append(row)
                article_ids.append(aid)

            sentiment_map: dict[int, str] = {}
            ai_summary_map: dict[int, bool] = {}
            if article_ids:
                ph = ", ".join("?" for _ in article_ids)
                for row in conn.execute(
                    f"""
                    SELECT
                        article_id,
                        MIN(sentiment) AS sentiment_any,
                        MAX(CASE WHEN COALESCE(sentiment_reason, '') = 'anthropic_batch' THEN 1 ELSE 0 END) AS has_ai_summary
                    FROM mentions
                    WHERE article_id IN ({ph})
                    GROUP BY article_id
                    """,
                    tuple(article_ids),
                ).fetchall():
                    try:
                        aid = int(row["article_id"])
                    except Exception:
                        continue
                    sentiment_map[aid] = str(row["sentiment_any"] or "neutral")
                    ai_summary_map[aid] = bool(int(row["has_ai_summary"] or 0))

            output: list[dict] = []
            for story in stories:
                sid = int(story["id"])
                rows_for_story = articles_by_story.get(sid) or []
                if not rows_for_story:
                    continue
                published_values: list[str] = []
                article_payload: list[dict] = []
                for a in rows_for_story:
                    aid = int(a["id"])
                    sentiment = sentiment_map.get(aid, "neutral")
                    published = a["published_at"] or a["discovered_at"]
                    if published:
                        published_values.append(published)
                    has_ai = bool(ai_summary_map.get(aid, False))
                    article_payload.append(
                        {
                            "id": f"a-{aid}",
                            "title": a["title"],
                            "url": a["url"],
                            "source": a["source_name"],
                            "publishedAt": published,
                            "sentiment": sentiment,
                            "summary": a["summary"] or "",
                            "snippet": a["snippet"] or "",
                            "hasAiSummary": has_ai,
                        }
                    )
                output.append(
                    {
                        "id": f"st-{sid}",
                        "title": story["title"],
                        "summary": story["summary"],
                        "temperature": float(story["temperature"] or 0.0),
                        "createdAt": story["created_at"],
                        "updatedAt": story["updated_at"],
                        "targets": targets_map.get(sid) or [],
                        "articles": article_payload,
                    }
                )
            return output

    # ------------------------------------------------------------------
    # VERBATIM from session log (Skip 430 output, lines 436-501)
    # Fixed known corruption: target_km_ey -> target_key
    # ------------------------------------------------------------------
    def list_articles(self, limit: int = 300) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    a.id,
                    a.title,
                    a.url,
                    a.source_name,
                    a.source_type,
                    a.published_at,
                    a.discovered_at,
                    a.snippet,
                    a.summary,
                    sa.story_id,
                    GROUP_CONCAT(DISTINCT m.target_key) AS target_keys,
                    GROUP_CONCAT(DISTINCT m.keyword_matched) AS keywords,
                    (
                      SELECT m2.sentiment
                      FROM mentions m2
                      WHERE m2.article_id = a.id
                      ORDER BY m2.id ASC
                      LIMIT 1
                    ) AS sentiment,
                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM mentions m3
                            WHERE m3.article_id = a.id
                              AND COALESCE(m3.sentiment_reason, '') = 'anthropic_batch'
                        ) THEN 1 ELSE 0
                    END AS has_ai_summary
                FROM articles a
                LEFT JOIN mentions m ON m.article_id = a.id
                LEFT JOIN story_articles sa ON sa.article_id = a.id
                GROUP BY a.id
                ORDER BY COALESCE(a.published_at, a.discovered_at) DESC
                LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()

            payload: list[dict] = []
            for row in rows:
                targets = [t for t in str(row["target_keys"] or "").split(",") if t]
                keywords = [k for k in str(row["keywords"] or "").split(",") if k]
                published = row["published_at"] or row["discovered_at"] or ""
                payload.append(
                    {
                        "id": f"a-{row['id']}",
                        "title": row["title"] or "",
                        "url": row["url"] or "",
                        "source": row["source_name"] or "",
                        "sourceType": row["source_type"] or "",
                        "publishedAt": published,
                        "snippet": row["snippet"] or "",
                        "summary": row["summary"] or "",
                        "sentiment": row["sentiment"] or "neutral",
                        "hasAiSummary": bool(int(row["has_ai_summary"] or 0)),
                        "summarySource": "llm" if bool(int(row["has_ai_summary"] or 0)) else "raw",
                        "targets": targets,
                        "keywords": keywords,
                        "storyId": f"st-{row['story_id']}" if row["story_id"] else "",
                    }
                )
            return payload

    # ------------------------------------------------------------------
    # VERBATIM from session log (Skip 500 output, lines 502-580)
    # Fixed known corruption: mamp. -> mp.
    # ------------------------------------------------------------------
    def list_articles_for_llm_batch(
        self,
        *,
        limit: int = 200,
        date_from: str = "",
        date_to: str = "",
        target_keys: list[str] | None = None,
        only_pending: bool = True,
    ) -> list[dict]:
        target_keys = [t for t in (target_keys or []) if str(t).strip()]
        where: list[str] = ["1=1"]
        params: list = []

        if date_from:
            where.append("COALESCE(a.published_at, a.discovered_at) >= ?")
            params.append(date_from)
        if date_to:
            where.append("COALESCE(a.published_at, a.discovered_at) <= ?")
            params.append(date_to)
        if target_keys:
            placeholders = ", ".join("?" for _ in target_keys)
            where.append(
                f"""
                EXISTS (
                    SELECT 1
                    FROM mentions mt
                    WHERE mt.article_id = a.id
                      AND mt.target_key IN ({placeholders})
                )
                """
            )
            params.extend(target_keys)
        if only_pending:
            where.append(
                """
                EXISTS (
                    SELECT 1
                    FROM mentions mp
                    WHERE mp.article_id = a.id
                      AND COALESCE(mp.sentiment_reason, '') != 'anthropic_batch'
                )
                """
            )

        sql = f"""
            SELECT
                a.id,
                a.url,
                a.title,
                a.source_name,
                a.source_type,
                COALESCE(a.published_at, a.discovered_at) AS published_at,
                a.snippet,
                a.full_text,
                a.summary,
                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM mentions m2
                        WHERE m2.article_id = a.id
                          AND COALESCE(m2.sentiment_reason, '') = 'anthropic_batch'
                    ) THEN 1 ELSE 0
                END AS has_ai_summary,
                GROUP_CONCAT(DISTINCT m.target_key) AS target_keys,
                GROUP_CONCAT(DISTINCT m.target_name) AS target_names,
                GROUP_CONCAT(DISTINCT m.keyword_matched) AS keywords,
                sa.story_id
            FROM articles a
            JOIN mentions m ON m.article_id = a.id
            LEFT JOIN story_articles sa ON sa.article_id = a.id
            WHERE {" AND ".join(where)}
            GROUP BY a.id
            ORDER BY COALESCE(a.published_at, a.discovered_at) DESC
            LIMIT ?
        """
        params.append(max(1, int(limit)))

        with self.connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
            payload: list[dict] = []
            for row in rows:
                payload.append(
                    {
                        "article_id": int(row["id"]),
                        "url": row["url"] or "",
                        "title": row["title"] or "",
                        "source_name": row["source_name"] or "",
                        "source_type": row["source_type"] or "",
                        "published_at": row["published_at"] or "",
                        "snippet": row["snippet"] or "",
                        "full_text": row["full_text"] or "",
                        "summary": row["summary"] or "",
                        "has_ai_summary": bool(int(row["has_ai_summary"] or 0)),
                        "summary_source": "llm" if bool(int(row["has_ai_summary"] or 0)) else "raw",
                        "target_keys": [v for v in str(row["target_keys"] or "").split(",") if v],
                        "target_names": [v for v in str(row["target_names"] or "").split(",") if v],
                        "keywords": [v for v in str(row["keywords"] or "").split(",") if v],
                        "story_id": int(row["story_id"]) if row["story_id"] else 0,
                    }
                )
            return payload

    # ------------------------------------------------------------------
    # VERBATIM from session log (Skip 430 output, lines 605-654)
    # [RECONSTRUCTED] closing dict and return from pattern matching
    # ------------------------------------------------------------------
    def list_articles_by_ids(self, article_ids: list[int]) -> list[dict]:
        ids = [int(v) for v in article_ids if int(v) > 0]
        if not ids:
            return []
        placeholders = ", ".join("?" for _ in ids)
        sql = f"""
            SELECT
                a.id,
                a.url,
                a.title,
                a.source_name,
                a.source_type,
                COALESCE(a.published_at, a.discovered_at) AS published_at,
                a.snippet,
                a.full_text,
                a.summary,
                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM mentions m2
                        WHERE m2.article_id = a.id
                          AND COALESCE(m2.sentiment_reason, '') = 'anthropic_batch'
                    ) THEN 1 ELSE 0
                END AS has_ai_summary,
                GROUP_CONCAT(DISTINCT m.target_key) AS target_keys,
                GROUP_CONCAT(DISTINCT m.target_name) AS target_names,
                GROUP_CONCAT(DISTINCT m.keyword_matched) AS keywords
            FROM articles a
            JOIN mentions m ON m.article_id = a.id
            WHERE a.id IN ({placeholders})
            GROUP BY a.id
        """
        with self.connect() as conn:
            rows = conn.execute(sql, tuple(ids)).fetchall()
            return [
                {
                    "article_id": int(row["id"]),
                    "url": row["url"] or "",
                    "title": row["title"] or "",
                    "source_name": row["source_name"] or "",
                    "source_type": row["source_type"] or "",
                    "published_at": row["published_at"] or "",
                    "snippet": row["snippet"] or "",
                    "full_text": row["full_text"] or "",
                    "summary": row["summary"] or "",
                    "has_ai_summary": bool(int(row["has_ai_summary"] or 0)),
                    "summary_source": "llm" if bool(int(row["has_ai_summary"] or 0)) else "raw",
                    "target_keys": [v for v in str(row["target_keys"] or "").split(",") if v],
                    "target_names": [v for v in str(row["target_names"] or "").split(",") if v],
                    "keywords": [v for v in str(row["keywords"] or "").split(",") if v],
                }
                for row in rows
            ]

    # ------------------------------------------------------------------
    # VERBATIM from apply_patch + from_patches file
    # ------------------------------------------------------------------
    def list_articles_for_export(
        self,
        *,
        limit: int = 5000,
        date_from: str = "",
        date_to: str = "",
        target_keys: list[str] | None = None,
    ) -> list[dict]:
        target_keys = [t for t in (target_keys or []) if str(t).strip()]
        where: list[str] = ["1=1"]
        params: list = []

        if date_from:
            where.append("COALESCE(a.published_at, a.discovered_at) >= ?")
            params.append(date_from)
        if date_to:
            where.append("COALESCE(a.published_at, a.discovered_at) <= ?")
            params.append(date_to)
        if target_keys:
            placeholders = ", ".join("?" for _ in target_keys)
            where.append(
                f"""
                EXISTS (
                    SELECT 1
                    FROM mentions mt
                    WHERE mt.article_id = a.id
                      AND mt.target_key IN ({placeholders})
                )
                """
            )
            params.extend(target_keys)
        sql = f"""
            SELECT
                a.id,
                a.url,
                a.title,
                a.source_name,
                a.source_type,
                COALESCE(a.published_at, a.discovered_at) AS published_at,
                a.snippet,
                a.full_text,
                a.summary,
                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM mentions m2
                        WHERE m2.article_id = a.id
                          AND COALESCE(m2.sentiment_reason, '') = 'anthropic_batch'
                    ) THEN 1 ELSE 0
                END AS has_ai_summary,
                GROUP_CONCAT(DISTINCT m.target_key) AS target_keys,
                GROUP_CONCAT(DISTINCT m.target_name) AS target_names,
                GROUP_CONCAT(DISTINCT m.keyword_matched) AS keywords,
                sa.story_id
            FROM articles a
            JOIN mentions m ON m.article_id = a.id
            LEFT JOIN story_articles sa ON sa.article_id = a.id
            WHERE {" AND ".join(where)}
            GROUP BY a.id
            ORDER BY COALESCE(a.published_at, a.discovered_at) DESC
            LIMIT ?
        """
        params.append(max(1, int(limit)))
        with self.connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
            payload: list[dict] = []
            for row in rows:
                payload.append(
                    {
                        "article_id": int(row["id"]),
                        "url": row["url"] or "",
                        "title": row["title"] or "",
                        "source_name": row["source_name"] or "",
                        "source_type": row["source_type"] or "",
                        "published_at": row["published_at"] or "",
                        "snippet": row["snippet"] or "",
                        "full_text": row["full_text"] or "",
                        "summary": row["summary"] or "",
                        "has_ai_summary": bool(int(row["has_ai_summary"] or 0)),
                        "summary_source": "llm" if bool(int(row["has_ai_summary"] or 0)) else "raw",
                        "target_keys": [v for v in str(row["target_keys"] or "").split(",") if v],
                        "target_names": [v for v in str(row["target_names"] or "").split(",") if v],
                        "keywords": [v for v in str(row["keywords"] or "").split(",") if v],
                        "story_id": int(row["story_id"]) if row["story_id"] else 0,
                    }
                )
            return payload

    # ------------------------------------------------------------------
    # VERBATIM from session log (Skip 780 output, lines 781-800)
    # ------------------------------------------------------------------
    def get_paused_backfills(self) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM backfill_state WHERE status = 'paused'"
            ).fetchall()
            return [
                {
                    "id": int(r["id"]),
                    "query": r["query"],
                    "start_date": r["start_date"],
                    "end_date": r["end_date"],
                    "current_date": r["current_date"],
                    "current_page": int(r["current_page"]),
                    "status": r["status"],
                    "updated_at": r["updated_at"],
                }
                for r in rows
            ]
