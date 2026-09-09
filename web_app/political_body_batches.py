"""Bounded immutable WordPress response bodies; queue payloads carry references only."""
from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
import gzip
import hashlib
import html
import io
import json
import re
import threading
from urllib.parse import urlparse

import requests

from pipeline.normalization import canonicalize_url
from .political_metrics import record_timing, timed_operation

# Opt in only APIs whose public rendered editorial bodies were checked against
# their actual article pages/stored publisher text on 2026-09-09.
WORDPRESS_BODY_SOURCES = {
    "tempo_real_rj": "temporealrj.com", "agenda_do_poder": "agendadopoder.com.br",
    "tupi": "tupi.fm", "j3news": "j3news.com",
}
MAX_BATCH_BYTES = 2 * 1024 * 1024
MAX_RECORDS = 100
MAX_CACHE_BYTES = 8 * 1024 * 1024
MAX_CACHE_BATCHES = 4
VERSION = "wordpress_rendered_v1"


class BatchBodyUnavailable(ValueError):
    """A bounded reason for ordinary publisher-page fallback."""


def _fail(reason):
    raise BatchBodyUnavailable(reason)


def _stamp(value):
    try:
        stamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            _fail("batch_date_unverified")
        return stamp.astimezone(timezone.utc)
    except (ValueError, TypeError):
        _fail("batch_date_unverified")


def _url(value, source):
    url = canonicalize_url(str(value or ""))
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    if source not in WORDPRESS_BODY_SOURCES or host != WORDPRESS_BODY_SOURCES[source] or urlparse(url).scheme != "https":
        _fail("batch_url_mismatch")
    return url


def _record(record, source):
    if not isinstance(record, dict) or type(record.get("post_id")) is not int or record["post_id"] < 1:
        _fail("batch_post_id_invalid")
    _url(record.get("url"), source)
    _stamp(record.get("published_at"))
    if not isinstance(record.get("content_html"), str) or type(record.get("protected")) is not bool:
        _fail("batch_content_invalid")
    return record


class WordPressBodyBatches:
    def __init__(self, store):
        self.store = store
        self._cache = OrderedDict()
        self._cache_bytes = 0
        self._lock = threading.Lock()
        # Bound bookkeeping while coalescing concurrent reads of the same object.
        # Object I/O never holds the global cache lock.
        self._load_locks = [threading.Lock() for _ in range(32)]

    def _key(self, digest):
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            _fail("batch_hash_invalid")
        return f"{self.store.prefix}/political/wordpress-batches/{digest[:2]}/{digest}.json.gz"

    def _cache_put(self, digest, payload, size):
        with self._lock:
            previous = self._cache.pop(digest, None)
            if previous:
                self._cache_bytes -= previous[1]
            self._cache[digest] = (payload, size)
            self._cache_bytes += size
            while self._cache_bytes > MAX_CACHE_BYTES or len(self._cache) > MAX_CACHE_BATCHES:
                _, (_, old_size) = self._cache.popitem(last=False)
                self._cache_bytes -= old_size

    def _cache_get(self, digest):
        with self._lock:
            found = self._cache.get(digest)
            if found:
                self._cache.move_to_end(digest)
                return found[0]
        return None

    def store_batch(self, batch):
        if not isinstance(batch, dict):
            _fail("batch_shape_invalid")
        source = batch.get("source_key")
        records = batch.get("records")
        if source not in WORDPRESS_BODY_SOURCES or not isinstance(records, list) or not 0 < len(records) <= MAX_RECORDS:
            _fail("batch_shape_invalid")
        seen = set()
        for record in records:
            _record(record, source)
            if record["post_id"] in seen:
                _fail("batch_duplicate_post_id")
            seen.add(record["post_id"])
        payload = {"version": VERSION, "source_key": source, "records": records}
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        if len(raw) > MAX_BATCH_BYTES:
            _fail("batch_too_large")
        digest = hashlib.sha256(raw).hexdigest()
        key = self._key(digest)
        try:
            with timed_operation("object_upload"), timed_operation("body_batch_upload"):
                if not self.store.enabled or not self.store.upload_bytes(gzip.compress(raw, mtime=0), key, "application/gzip"):
                    _fail("batch_storage_failed")
        except BatchBodyUnavailable:
            raise
        except Exception:
            _fail("batch_storage_failed")
        self._cache_put(digest, payload, len(raw))
        return [{"version": VERSION, "key": key, "sha256": digest, "index": index,
                 "post_id": record["post_id"], "source_key": source}
                for index, record in enumerate(records)]

    def _download(self, key):
        if hasattr(self.store, "read_political_object"):
            data = self.store.read_political_object(key)
            if not isinstance(data, bytes) or len(data) > MAX_BATCH_BYTES:
                _fail("batch_compressed_limit")
            return data
        with requests.get(self.store._object_url(key), headers=self.store._headers(), timeout=(8, 30), stream=True) as response:
            response.raise_for_status()
            data = bytearray()
            for chunk in response.iter_content(65536):
                data.extend(chunk)
                if len(data) > MAX_BATCH_BYTES:
                    _fail("batch_compressed_limit")
            return bytes(data)

    def _load(self, reference):
        digest = reference.get("sha256")
        key = self._key(digest)
        if reference.get("key") != key or reference.get("version") != VERSION:
            _fail("batch_reference_invalid")
        found = self._cache_get(digest)
        if found is not None:
            record_timing("body_batch_cache_hit", 0)
            return found
        with self._load_locks[int(digest[:8], 16) % len(self._load_locks)]:
            found = self._cache_get(digest)
            if found is not None:
                record_timing("body_batch_cache_hit", 0)
                return found
            try:
                with timed_operation("body_batch_read"):
                    compressed = self._download(key)
                with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
                    raw = stream.read(MAX_BATCH_BYTES + 1)
                if len(raw) > MAX_BATCH_BYTES or hashlib.sha256(raw).hexdigest() != digest:
                    _fail("batch_integrity_error")
                payload = json.loads(raw)
                if not isinstance(payload, dict) or payload.get("version") != VERSION:
                    _fail("batch_shape_invalid")
                records = payload.get("records")
                if not isinstance(records, list) or not 0 < len(records) <= MAX_RECORDS:
                    _fail("batch_shape_invalid")
            except BatchBodyUnavailable:
                raise
            except Exception:
                _fail("batch_read_failed")
            self._cache_put(digest, payload, len(raw))
            return payload

    def read_body(self, reference, candidate):
        if not isinstance(reference, dict):
            _fail("batch_reference_invalid")
        payload = self._load(reference)
        source = candidate.get("source_key")
        if source not in WORDPRESS_BODY_SOURCES or source != reference.get("source_key") or source != payload.get("source_key"):
            _fail("batch_source_mismatch")
        index = reference.get("index")
        if type(index) is not int or not 0 <= index < len(payload["records"]):
            _fail("batch_index_invalid")
        record = _record(payload["records"][index], source)
        post_id = (candidate.get("metadata") or {}).get("wordpress_id")
        if type(post_id) is not int or type(reference.get("post_id")) is not int or post_id != reference.get("post_id") or post_id != record["post_id"]:
            _fail("batch_post_id_mismatch")
        if _url(record["url"], source) != _url(candidate.get("url"), source):
            _fail("batch_url_mismatch")
        if _stamp(record["published_at"]) != _stamp(candidate.get("published_at")):
            _fail("batch_date_mismatch")
        fragment = record["content_html"]
        if record["protected"] or not fragment.strip():
            _fail("batch_text_unavailable")
        # These can represent editorial continuation unavailable in a fragment.
        # Fall back to the real page rather than infer a complete negative match.
        if re.search(r"<!--\s*(?:nextpage|more)\b|\bpage-links\b|\[(?:/?[a-z][a-z0-9_-]*)(?:\s|\])", fragment, re.I):
            _fail("batch_continuation_unverified")
        from .political_discovery import extract_article
        wrapper = ('<html><head><link rel="canonical" href="' + html.escape(record["url"], quote=True)
                   + '"></head><body><article>' + fragment + '</article></body></html>')
        try:
            with timed_operation("extraction"):
                extracted = extract_article(wrapper)
        except Exception:
            _fail("batch_extraction_failed")
        body = extracted.get("full_text") or ""
        if extracted.get("extraction_state") != "full_text" or len(body.strip()) < 200:
            _fail("batch_text_unavailable")
        record_timing("body_batch_use", 0)
        return {"full_text": body, "published_at": record["published_at"],
                "canonical_url": _url(record["url"], source), "provenance": {
                    "method": "wordpress_api_batch", "version": VERSION, "batch": reference}}
