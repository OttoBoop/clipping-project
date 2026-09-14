"""Bounded, reconstructible XML cache for one discovery task's pagination.

The durable cursor retains the URL/hash; a lost or corrupt local file simply
requires the publisher again. The adapter still checks its document fingerprint
before using an existing offset. A new job or calendar page starts with a fresh
request. Nothing here caches article text or changes source configuration.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
import threading
import time

import requests

from .political_metrics import record_timing

MAX_DOCUMENT_BYTES = 8 * 1024 * 1024
MAX_CACHE_BYTES = 128 * 1024 * 1024
MAX_CACHE_FILES = 64
_LOCK = threading.Lock()


class PaginatedSitemapCache:
    def __init__(self, fetch, cursor, directory=None):
        self.transport = fetch
        self.reference = (cursor or {}).get("response_cache") or {}
        self.directory = Path(directory or os.environ.get("POLITICAL_PAGED_SITEMAP_CACHE_DIR")
                              or Path(tempfile.gettempdir()) / "clipping-paged-sitemaps")
        self.response = None
        self.request_url = ""

    def fetch(self, url, **kwargs):
        self.request_url = url
        digest = str(self.reference.get("sha256") or "")
        if (self.reference.get("url") == url and len(digest) == 64
                and all(c in "0123456789abcdef" for c in digest)):
            started = time.monotonic()
            try:
                path = self.directory / (digest + ".xml")
                with _LOCK:
                    if path.stat().st_size > MAX_DOCUMENT_BYTES:
                        raise ValueError("cache_document_too_large")
                    content = path.read_bytes()
                    if hashlib.sha256(content).hexdigest() != digest:
                        path.unlink(missing_ok=True)
                        raise ValueError("cache_hash_mismatch")
                    path.touch()
                response = requests.Response()
                response.status_code = 200
                response.url = self.reference.get("response_url") or url
                response._content = content
                response._content_consumed = True
                response.headers["Content-Type"] = "application/xml"
                self.response = response
                record_timing("sitemap_cache", time.monotonic() - started, outcome="hit")
                return response
            except (OSError, ValueError):
                record_timing("sitemap_cache", time.monotonic() - started, outcome="miss")
        self.response = self.transport(url, **kwargs)
        return self.response

    def checkpoint(self, cursor):
        """Cache only a parsed page that actually has further cursor work."""
        if not cursor or self.response is None or self.response.status_code != 200:
            return cursor
        content = self.response.content
        if not isinstance(content, bytes) or len(content) > MAX_DOCUMENT_BYTES:
            return cursor
        digest = hashlib.sha256(content).hexdigest()
        temporary = None
        started = time.monotonic()
        try:
            with _LOCK:
                self.directory.mkdir(parents=True, exist_ok=True)
                path = self.directory / (digest + ".xml")
                if not path.exists():
                    with tempfile.NamedTemporaryFile(dir=self.directory, mode="wb", delete=False) as out:
                        temporary = out.name
                        out.write(content)
                        out.flush()
                        os.fsync(out.fileno())
                    os.replace(temporary, path)
                    temporary = None
                path.touch()
                size = count = 0
                for item in sorted(self.directory.glob("*.xml"), key=lambda p: p.stat().st_mtime, reverse=True):
                    size += item.stat().st_size
                    count += 1
                    if size > MAX_CACHE_BYTES or count > MAX_CACHE_FILES:
                        item.unlink(missing_ok=True)
            record_timing("sitemap_cache_store", time.monotonic() - started, outcome="ok")
            return {**cursor, "response_cache": {"url": self.request_url,
                "response_url": self.response.url, "sha256": digest}}
        except OSError:
            # A reconstructible optimization cannot turn healthy discovery into
            # a storage failure. Its absence is observable in worker telemetry.
            record_timing("sitemap_cache_store", time.monotonic() - started, outcome="error")
            return cursor
        finally:
            if temporary:
                try:
                    Path(temporary).unlink(missing_ok=True)
                except OSError:
                    pass
