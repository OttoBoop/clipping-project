"""SQLite database for storing clipping articles and mentions."""
import sqlite3
from pathlib import Path


class ClippingDB:
    """SQLite wrapper for the clipping database."""

    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                source_name TEXT,
                source_type TEXT,
                published_at TEXT,
                discovered_at TEXT DEFAULT (datetime('now')),
                snippet TEXT,
                full_text TEXT,
                summary TEXT
            );
            CREATE TABLE IF NOT EXISTS mentions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER REFERENCES articles(id),
                target_key TEXT,
                target_name TEXT,
                keyword_matched TEXT,
                sentiment TEXT DEFAULT 'neutral',
                sentiment_reason TEXT
            );
            CREATE TABLE IF NOT EXISTS story_articles (
                article_id INTEGER REFERENCES articles(id),
                story_id TEXT,
                PRIMARY KEY (article_id, story_id)
            );
        """)
        self.conn.commit()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def article_exists(self, url):
        """Check if an article URL is already in the database."""
        row = self.conn.execute("SELECT 1 FROM articles WHERE url = ?", (url,)).fetchone()
        return row is not None

    def insert_article(self, url, title, source_name, source_type, published_at, snippet, full_text=None):
        """Insert an article and return its ID. Returns None if duplicate."""
        try:
            cur = self.conn.execute(
                """INSERT INTO articles (url, title, source_name, source_type, published_at, snippet, full_text)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (url, title, source_name, source_type, published_at, snippet, full_text),
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None

    def insert_mention(self, article_id, target_key, target_name, keyword_matched):
        """Insert a mention linking an article to a target."""
        self.conn.execute(
            """INSERT INTO mentions (article_id, target_key, target_name, keyword_matched)
               VALUES (?, ?, ?, ?)""",
            (article_id, target_key, target_name, keyword_matched),
        )
        self.conn.commit()

    def list_articles_for_export(self, *, date_from="", date_to="", target_key="", limit=5000):
        """List articles with their mentions for export."""
        sql = """
            SELECT a.id, a.url, a.title, a.source_name, a.source_type,
                   a.published_at, a.discovered_at, a.snippet, a.summary,
                   m.target_key, m.target_name, m.keyword_matched, m.sentiment
            FROM articles a
            JOIN mentions m ON m.article_id = a.id
            WHERE 1=1
        """
        params = []
        if date_from:
            sql += " AND a.published_at >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND a.published_at <= ?"
            params.append(date_to + "T23:59:59")
        if target_key:
            sql += " AND m.target_key = ?"
            params.append(target_key)
        sql += " ORDER BY a.published_at DESC LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def count_articles(self):
        return self.conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]

    def count_mentions(self):
        return self.conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0]
