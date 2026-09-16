"""Immutable discovery snapshots reusable across IstoÉ jobs, with strict resume."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import hashlib
import json
import requests

SCHEMA = """
CREATE TABLE IF NOT EXISTS political_istoe_documents (
 url TEXT NOT NULL, sha256 TEXT NOT NULL, object_key TEXT NOT NULL,
 fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), byte_count BIGINT NOT NULL,
 PRIMARY KEY(url,sha256)
);
CREATE INDEX IF NOT EXISTS political_istoe_documents_latest ON political_istoe_documents(url,fetched_at DESC);
CREATE TABLE IF NOT EXISTS political_istoe_urls (
 url TEXT PRIMARY KEY, document_url TEXT NOT NULL, document_hash TEXT NOT NULL,
 lastmod_hint TEXT NOT NULL DEFAULT '', first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


class InventoryTransport:
    def __init__(self, service, task):
        self.service, self.task = service, task
        self.reference = (task.get("cursor") or {}).get("inventory_snapshot")
        self.reused = False

    def fetch(self, url, **kwargs):
        from .political_discovery import DiscoveryError
        service = self.service
        row = self.reference
        if row and row["url"] != url:
            raise DiscoveryError("istoe_snapshot_url_mismatch", retryable=False)
        if not row:
            with service._connect() as conn:
                # Closed historical windows can reuse recent documents. A
                # window including the snapshot's day needs a fresh request,
                # because that sitemap may have gained URLs since capture.
                # A resumed task always keeps its already frozen document.
                row = conn.execute("""SELECT url,sha256,object_key,fetched_at FROM political_istoe_documents
                    WHERE url=%s AND fetched_at>NOW()-INTERVAL '6 hours'
                    ORDER BY fetched_at DESC LIMIT 1""", (url,)).fetchone()
            if row:
                end = str((self.task.get('payload') or {}).get('date_to') or '')
                captured_day = row['fetched_at'].astimezone(ZoneInfo('America/Sao_Paulo')).date().isoformat()
                if not end or end >= captured_day:
                    row = None
        if row:
            try:
                content = service._read_discovery_response(row["object_key"], row["sha256"])
                if hashlib.sha256(content).hexdigest() != row["sha256"]:
                    raise ValueError("hash mismatch")
            except Exception as exc:
                if self.reference:
                    raise DiscoveryError("istoe_snapshot_unavailable") from exc
                row = None
            else:
                self.reused = True
        if not row:
            response = service.fetch(url, allowed_hosts=("istoe.com.br", "www.istoe.com.br"), **kwargs)
            if response.status_code != 200:
                return response
            from .political_istoe_discovery import allowed
            if not allowed(response.url):
                raise DiscoveryError("istoe_redirect_outside_portal", retryable=False)
            # Validate the shape before retaining a response as an XML snapshot.
            from .political_discovery import _xml, _local
            if _local(_xml(response).tag) not in {"sitemapindex", "urlset"}:
                raise DiscoveryError("istoe_invalid_sitemap_response", retryable=False)
            content = response.content
            digest, key = service._store_discovery_response(content)
            with service._connect() as conn:
                conn.execute("""INSERT INTO political_istoe_documents(url,sha256,object_key,byte_count)
                    VALUES(%s,%s,%s,%s) ON CONFLICT(url,sha256) DO UPDATE SET fetched_at=NOW()""",
                    (url,digest,key,len(content)))
            row = {"url": url, "sha256": digest, "object_key": key, "fetched_at": datetime.now(timezone.utc).isoformat()}
        self.reference = {k: str(row[k]) for k in ("url", "sha256", "object_key", "fetched_at")}
        response = requests.Response()
        response.status_code, response.url, response._content = 200, url, content
        response.headers["Content-Type"] = "application/xml; charset=utf-8"
        return response

    def checkpoint(self, cursor):
        return {**(cursor or {}), "inventory_snapshot": self.reference}


def record_urls(conn, candidates):
    rows = [(c['url'], c['metadata']['sitemap_url'], c['metadata']['sitemap_snapshot_hash'],
             c['metadata'].get('sitemap_lastmod_hint', '')) for c in candidates]
    with conn.cursor() as cursor:
        cursor.executemany("""INSERT INTO political_istoe_urls(url,document_url,document_hash,lastmod_hint)
            VALUES(%s,%s,%s,%s) ON CONFLICT(url) DO UPDATE SET document_url=EXCLUDED.document_url,
            document_hash=EXCLUDED.document_hash,lastmod_hint=EXCLUDED.lastmod_hint,last_seen_at=NOW()""", rows)
