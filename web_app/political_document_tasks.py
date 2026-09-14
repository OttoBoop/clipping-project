"""Durable public editions, deliberately separate from individual articles.

The corpus owns leases, throttled transport, transaction boundaries and account
authorization. A PDF download and each subsequent page consume one fetch slot;
the worker must serialize payload.document_task across its four fetch slots.
"""
from __future__ import annotations

from datetime import date, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
from urllib.parse import parse_qs, urlparse, urlunparse

import requests

from .political_documents import (
    DocumentProblem, PageResult, VERSION, document_file, download_pdf,
    edition_date, extract_pdf_pages, inspect_pdf, parse_edition_links, store_pdf,
)
from .political_metrics import record_timing

DOCUMENT_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS political_documents (
 id BIGSERIAL PRIMARY KEY, canonical_url TEXT NOT NULL UNIQUE,
 source_key TEXT NOT NULL, source_name TEXT NOT NULL DEFAULT '',
 edition_label TEXT NOT NULL DEFAULT '', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS political_document_versions (
 id BIGSERIAL PRIMARY KEY, document_id BIGINT NOT NULL REFERENCES political_documents(id),
 sha256 TEXT NOT NULL, object_key TEXT NOT NULL, byte_count BIGINT NOT NULL,
 page_count INTEGER NOT NULL CHECK(page_count BETWEEN 1 AND 500),
 download_published_at TEXT NOT NULL DEFAULT '', editorial_date JSONB NOT NULL DEFAULT '{}',
 metadata JSONB NOT NULL DEFAULT '{}', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 UNIQUE(document_id,sha256)
);
CREATE TABLE IF NOT EXISTS political_document_pages (
 id BIGSERIAL PRIMARY KEY, document_id BIGINT NOT NULL REFERENCES political_documents(id),
 page_number INTEGER NOT NULL CHECK(page_number BETWEEN 1 AND 500),
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), UNIQUE(document_id,page_number)
);
CREATE TABLE IF NOT EXISTS political_document_page_versions (
 id BIGSERIAL PRIMARY KEY, page_id BIGINT NOT NULL REFERENCES political_document_pages(id),
 document_version_id BIGINT NOT NULL REFERENCES political_document_versions(id),
 text_hash TEXT NOT NULL DEFAULT '', text_object_key TEXT NOT NULL DEFAULT '',
 text_chars INTEGER NOT NULL DEFAULT 0, extraction_method TEXT NOT NULL,
 extraction_version TEXT NOT NULL, text_state TEXT NOT NULL, error_type TEXT NOT NULL DEFAULT '',
 editorial_date JSONB NOT NULL DEFAULT '{}', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 UNIQUE(page_id,document_version_id)
);
CREATE TABLE IF NOT EXISTS political_document_mentions (
 page_version_id BIGINT NOT NULL REFERENCES political_document_page_versions(id),
 target_key TEXT NOT NULL, target_name TEXT NOT NULL, keyword_matched TEXT NOT NULL DEFAULT '',
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY(page_version_id,target_key)
);
CREATE TABLE IF NOT EXISTS political_document_page_revisions (
 id BIGSERIAL PRIMARY KEY, page_version_id BIGINT NOT NULL REFERENCES political_document_page_versions(id),
 previous JSONB NOT NULL, reason TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS political_job_documents (
 job_id TEXT NOT NULL REFERENCES political_jobs(id) ON DELETE CASCADE,
 document_version_id BIGINT NOT NULL REFERENCES political_document_versions(id),
 first_saved BOOLEAN NOT NULL DEFAULT FALSE, PRIMARY KEY(job_id,document_version_id)
);
CREATE TABLE IF NOT EXISTS political_job_document_pages (
 job_id TEXT NOT NULL REFERENCES political_jobs(id) ON DELETE CASCADE,
 page_version_id BIGINT NOT NULL REFERENCES political_document_page_versions(id),
 first_saved BOOLEAN NOT NULL DEFAULT FALSE, associations_added INTEGER NOT NULL DEFAULT 0,
 reused_text BOOLEAN NOT NULL DEFAULT FALSE,
 PRIMARY KEY(job_id,page_version_id)
);
CREATE INDEX IF NOT EXISTS political_document_page_latest_idx
 ON political_document_page_versions(page_id,document_version_id DESC);
CREATE INDEX IF NOT EXISTS political_document_mentions_target_idx
 ON political_document_mentions(target_key,page_version_id);
CREATE INDEX IF NOT EXISTS political_document_source_idx ON political_documents(source_key,id);
"""


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def document_url(url):
    """A fragment selects a page for a reader, never another document."""
    parsed = urlparse(str(url or ""))
    if parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username or parsed.password:
        raise DocumentProblem("pdf_url_invalid")
    return urlunparse(parsed._replace(fragment=""))


def date_overlaps(evidence, first, last):
    """Unknown dates remain reviewable, without acquiring today's date."""
    lower, upper = evidence.get("period_from"), evidence.get("period_to")
    if not lower or not upper:
        return None
    try:
        return date.fromisoformat(lower) <= date.fromisoformat(str(last)[:10]) and date.fromisoformat(upper) >= date.fromisoformat(str(first)[:10])
    except ValueError:
        return None


def discover_edition_archive(task, source, fetch):
    """Traverse publisher edition indexes with bounded, durable continuations."""
    from .political_discovery import _get
    cursor = task.get("cursor") or {}
    url = cursor.get("url") or task.get("url") or task.get("mechanism", {}).get("url")
    hosts = source.get("domains") or [source.get("domain", "")]
    host = (urlparse(url).hostname or "").removeprefix("www.")
    if host not in {h.removeprefix("www.") for h in hosts}:
        raise DocumentProblem("pdf_archive_outside_publisher")
    response = _get(fetch, url)
    links = parse_edition_links(response.text, url, source["key"], allowed_hosts=hosts)
    if host == "panoramarj.com.br":
        first, last = date.fromisoformat(task["date_from"]), date.fromisoformat(task["date_to"])
        first_month = first.replace(day=1)
        # Panorama's verified weekend cover spans three days; the previous
        # month is needed when such an edition overlaps the first days of this
        # month. Follow only month URLs actually advertised by the publisher.
        if first.day <= 3:
            first_month = (first_month - timedelta(days=1)).replace(day=1)
        last_month = last.replace(day=1)
        selected = []
        for row in links:
            parsed = urlparse(row["url"])
            query = parse_qs(parsed.query)
            if row["product_kind"] == "edition_index" and parsed.path.rstrip("/") == "/edicoes-link":
                try:
                    month = date(int(query["ano"][0]), int(query["mes"][0]), 1)
                except (KeyError, ValueError, IndexError):
                    selected.append(row)  # Unknown partitions stay visible.
                    continue
                if not first_month <= month <= last_month:
                    continue
            selected.append(row)
        links = selected
    fingerprint = hashlib.sha256(_json([row["url"] for row in links]).encode()).hexdigest()
    offset = int(cursor.get("offset", 0))
    if offset and cursor.get("fingerprint") != fingerprint:
        return {"candidates": [], "child_tasks": [], "outcome": "gap", "raw_count": 0,
                "gap_reason": "pdf_edition_index_changed_during_resume"}
    def priority(row):
        if row["product_kind"] == "edition_index":
            return (0, 0)
        stamp = row.get("period_from")
        if not stamp:
            return (2, 0)
        point = date.fromisoformat(stamp)
        first, last = date.fromisoformat(task["date_from"]), date.fromisoformat(task["date_to"])
        return (1, 0 if first <= point <= last else min(abs((point - first).days), abs((point - last).days)))
    links.sort(key=priority)
    # Per-index admission is finite as well as batched. An unbounded public
    # archive must leave an explicit tail gap, not silently monopolize the queue.
    maximum = max(1, min(int(task.get("mechanism", {}).get("max_entries", 100)), 500))
    deferred = max(0, len(links) - maximum)
    links = links[:maximum]
    # Fifty editions at a time avoids reserving hundreds of expensive downloads.
    batch = links[offset:offset + 50]
    children, candidates = [], []
    ancestry = list(task.get("ancestors") or [])
    depth = int(task.get("depth", 0))
    reason = ""
    for row in batch:
        if row["product_kind"] == "edition_index":
            if row["url"] in [*ancestry, url]:
                continue
            if depth >= 6:
                reason = "pdf_edition_index_depth_limit"
                continue
            children.append({**task, "url": row["url"], "cursor": {},
                "depth": depth + 1, "ancestors": ancestry + [url],
                "edition_context": {k: row[k] for k in ("title", "edition_date", "edition_month", "date_status", "date_precision", "period_from", "period_to", "date_evidence")}})
        else:
            metadata = {k: v for k, v in row.items() if k not in {"url", "title", "source_key"}}
            context = task.get("edition_context") or {}
            if metadata.get("date_status") == "unknown" and context.get("date_status", "unknown") != "unknown":
                metadata.update({k: v for k, v in context.items() if k != "title"})
            # A filename's day can be the beginning of a weekend edition: the
            # real 27/06 Panorama cover spans 27–29/06. Only explicit intervals
            # permit exclusion before the cover has been inspected.
            if metadata.get("date_precision") in {"range", "month"} and date_overlaps(metadata, task["date_from"], task["date_to"]) is False:
                continue
            # The cover verifies date labels; do not exclude on an upload date.
            candidates.append({"url": row["url"], "title": row["title"],
                "source_key": source["key"], "source_name": source["name"],
                "document_type": "edition_pdf", "metadata": metadata})
    more = offset + len(batch) < len(links)
    if not links:
        reason = "pdf_edition_links_not_found"
    if deferred and not more:
        reason = "pdf_edition_archive_entry_limit"
    return {"candidates": candidates, "child_tasks": children, "raw_count": len(batch),
        "outcome": "continue" if more else "gap" if reason else "complete",
        "next_cursor": {"offset": offset + len(batch), "fingerprint": fingerprint,
                        "unprocessed_entries": deferred, "entry_limit": maximum} if more or deferred else None,
        "gap_reason": reason}


class PoliticalDocumentMixin:
    def _pdf_cache(self):
        folder = Path(os.environ.get("POLITICAL_PDF_CACHE", str(Path(tempfile.gettempdir()) / "clipping-public-pdfs")))
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _prune_pdf_cache(self, keep):
        total = 0
        files = sorted(self._pdf_cache().glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
        for path in files:
            total += path.stat().st_size
            if total > 128 * 1024 * 1024 and path != Path(keep):
                path.unlink(missing_ok=True)

    def _pdf_object(self, version):
        cached = self._pdf_cache() / (version["sha256"] + ".pdf")
        if cached.exists():
            try:
                verified = document_file(cached, expected_sha256=version["sha256"])
                os.utime(cached, None)
                return verified
            except DocumentProblem:
                cached.unlink(missing_ok=True)
        try:
            if hasattr(self.store, "read_political_object"):
                # This protocol is used by disposable stores in integration tests.
                raw = self.store.read_political_object(version["object_key"])
                with tempfile.NamedTemporaryFile(dir=self._pdf_cache(), suffix=".part", delete=False) as handle:
                    temporary = Path(handle.name)
                    handle.write(raw)
                try:
                    verified = document_file(temporary, expected_sha256=version["sha256"])
                    os.replace(temporary, cached)
                    return document_file(cached, expected_sha256=verified.sha256)
                finally:
                    temporary.unlink(missing_ok=True)
            response = requests.get(self.store._object_url(version["object_key"]),
                headers=self.store._headers(), timeout=(10, 45), stream=True)
            return download_pdf(response, self._pdf_cache(), expected_sha256=version["sha256"])
        except DocumentProblem:
            raise
        except Exception as exc:
            raise DocumentProblem("pdf_object_read_failed", retryable=True) from exc

    @staticmethod
    def _insert_document_task(conn, job_id, payload):
        operation = payload["document_task"]
        identity = ("page:" + str(payload["document_version_id"]) + ":" + str(payload["page_number"])) if operation == "page" else "download:" + document_url(payload["url"])
        dedupe = "pdf:" + identity
        return conn.execute("""INSERT INTO political_tasks(job_id,kind,source_key,dedupe_key,payload,request_domain,priority)
            VALUES (%s,'fetch',%s,%s,%s::jsonb,%s,%s) ON CONFLICT(job_id,kind,dedupe_key) DO NOTHING RETURNING id""",
            (job_id, payload["source_key"], dedupe, _json(payload),
             (urlparse(payload.get("url", "")).hostname or "") if operation == "download" else "", 25 if operation == "page" else 20)).fetchone()

    def enqueue_document_candidate(self, conn, job_id, candidate):
        return self._insert_document_task(conn, job_id, {**candidate,
            "url": document_url(candidate["url"]), "document_task": "download"})

    def process_document_task(self, task):
        return self._download_document(task) if task["payload"]["document_task"] == "download" else self._process_document_page(task)

    def _download_document(self, task):
        candidate = task["payload"]
        response = self.fetch(candidate["url"], stream_pdf=True)
        started = time.monotonic()
        document = download_pdf(response, self._pdf_cache())
        record_timing("http_body", time.monotonic() - started, status_code=200)
        started = time.monotonic()
        original = store_pdf(document, self.store)
        record_timing("object_upload", time.monotonic() - started)
        info = inspect_pdf(document)
        metadata = candidate.get("metadata") or {}
        editorial = {k: metadata.get(k, "") for k in ("edition_date", "edition_month", "date_status", "date_precision", "period_from", "period_to", "date_evidence")}
        if not editorial["date_status"]:
            editorial = edition_date(candidate.get("title", ""), filename=candidate["url"])
        with self._connect() as conn:
            self._lock_task(conn, task)
            row = conn.execute("""INSERT INTO political_documents(canonical_url,source_key,source_name,edition_label)
                VALUES (%s,%s,%s,%s) ON CONFLICT(canonical_url) DO NOTHING RETURNING id""",
                (document_url(candidate["url"]), candidate["source_key"], candidate.get("source_name", ""), candidate.get("title", "")[:1000])).fetchone()
            if not row:
                row = conn.execute("SELECT id FROM political_documents WHERE canonical_url=%s", (document_url(candidate["url"]),)).fetchone()
            version = conn.execute("""INSERT INTO political_document_versions(document_id,sha256,object_key,byte_count,page_count,
                download_published_at,editorial_date,metadata) VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb)
                ON CONFLICT(document_id,sha256) DO NOTHING RETURNING *""",
                (row["id"], document.sha256, original["key"], document.bytes, info["page_count"],
                 str(candidate.get("published_at") or ""), _json(editorial), _json({**metadata, "requested_url": candidate["url"], "resolved_url": document.url, "format_version": VERSION}))).fetchone()
            new = bool(version)
            if not version:
                version = conn.execute("SELECT * FROM political_document_versions WHERE document_id=%s AND sha256=%s", (row["id"], document.sha256)).fetchone()
            conn.execute("""INSERT INTO political_job_documents(job_id,document_version_id,first_saved)
                VALUES (%s,%s,%s) ON CONFLICT DO NOTHING""", (task["job_id"], version["id"], new))
            self._insert_document_task(conn, task["job_id"], {"document_task": "page", "document_version_id": version["id"],
                "page_number": 1, "source_key": candidate["source_key"]})
            result = {"documentsNew": int(new), "documentsReused": int(not new), "documentPages": info["page_count"], "documentBytes": document.bytes}
            self._finish(conn, task, "complete", result=result)
        self._prune_pdf_cache(document.path)
        return {"taskId": task["id"], "status": "complete", **result}

    def _process_document_page(self, task):
        from .political_corpus import match_targets
        payload = task["payload"]
        number = int(payload["page_number"])
        with self._connect() as conn:
            job = self._lock_task(conn, task)
            version = conn.execute("SELECT * FROM political_document_versions WHERE id=%s", (payload["document_version_id"],)).fetchone()
            if not version or not 1 <= number <= version["page_count"]:
                raise DocumentProblem("pdf_page_identity_invalid")
            existing = conn.execute("""SELECT pv.* FROM political_document_page_versions pv JOIN political_document_pages p ON p.id=pv.page_id
                WHERE pv.document_version_id=%s AND p.page_number=%s""", (version["id"], number)).fetchone()
        editorial = version["editorial_date"] or {}
        reused = bool(existing and existing["text_object_key"])
        if reused:
            body = self._read_text(existing["text_object_key"], existing["text_hash"])
            page = PageResult(version["sha256"], number, version["page_count"], body, existing["extraction_method"], existing["text_state"], existing["error_type"])
        else:
            document = self._pdf_object(version)
            started = time.monotonic()
            page = next(extract_pdf_pages(document.path, start_page=number, max_pages=1, expected_sha256=version["sha256"]))
            record_timing("extraction", time.monotonic() - started)
        if number == 1:
            cover_date = edition_date(page.text[:1200])
            if cover_date["date_status"] != "unknown":
                editorial = {**cover_date, "date_source": "edition_cover", "document_sha256": version["sha256"], "page_number": 1}
        inside = date_overlaps(editorial, job["date_from"], job["date_to"])
        # Hyphenated printed line breaks are an extraction representation; the
        # approved target rules themselves are unchanged, and original text stays.
        matching_text = re.sub(r"(?<=\w)-[ \t]*\n[ \t]*(?=\w)", "", page.text)
        matches = match_targets(job["target_snapshots"], "", matching_text) if inside is not False else []
        digest, key = (existing["text_hash"], existing["text_object_key"]) if reused else self._store_text(page.text) if matches and page.text else ("", "")
        error = page.error_type or ("pdf_edition_date_unknown" if inside is None else "")
        with self._connect() as conn:
            self._lock_task(conn, task)
            if number == 1:
                conn.execute("UPDATE political_document_versions SET editorial_date=%s::jsonb WHERE id=%s", (_json(editorial), version["id"]))
            identity = conn.execute("""INSERT INTO political_document_pages(document_id,page_number) VALUES (%s,%s)
                ON CONFLICT(document_id,page_number) DO UPDATE SET page_number=EXCLUDED.page_number RETURNING id""", (version["document_id"], number)).fetchone()
            saved = conn.execute("""INSERT INTO political_document_page_versions(page_id,document_version_id,text_hash,text_object_key,text_chars,
                extraction_method,extraction_version,text_state,error_type,editorial_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                ON CONFLICT(page_id,document_version_id) DO NOTHING RETURNING id""",
                (identity["id"], version["id"], digest, key, len(page.text), page.method, page.version, page.state, page.error_type, _json(editorial))).fetchone()
            new = bool(saved)
            if not saved:
                saved = conn.execute("SELECT * FROM political_document_page_versions WHERE page_id=%s AND document_version_id=%s", (identity["id"], version["id"])).fetchone()
                # A previously unmatched page can acquire retained text for a new
                # approved selection; empty attempts never erase existing text.
                improved = (not saved["text_object_key"] and bool(key)) or (saved["text_state"] != "text_available" and page.state == "text_available")
                date_changed = saved["editorial_date"] != editorial and editorial.get("date_status") not in {"", "unknown", None}
                if improved or date_changed:
                    conn.execute("INSERT INTO political_document_page_revisions(page_version_id,previous,reason) VALUES (%s,%s::jsonb,%s)",
                        (saved["id"], _json(dict(saved)), "recovered_page" if improved else "verified_edition_date"))
                    conn.execute("""UPDATE political_document_page_versions SET
                        text_hash=CASE WHEN text_object_key='' THEN %s ELSE text_hash END,
                        text_object_key=CASE WHEN text_object_key='' THEN %s ELSE text_object_key END,
                        text_chars=GREATEST(text_chars,%s),extraction_method=%s,extraction_version=%s,
                        text_state=%s,error_type=%s,editorial_date=%s::jsonb WHERE id=%s""",
                        (digest, key, len(page.text), page.method, page.version, page.state, page.error_type, _json(editorial), saved["id"]))
            added = 0
            for match in matches:
                inserted = conn.execute("""INSERT INTO political_document_mentions(page_version_id,target_key,target_name,keyword_matched)
                    VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING target_key""",
                    (saved["id"], match["target_key"], match["target_name"], match["keyword_matched"])).fetchone()
                added += bool(inserted)
            conn.execute("""INSERT INTO political_job_document_pages(job_id,page_version_id,first_saved,associations_added,reused_text)
                VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""", (task["job_id"], saved["id"], new, added, reused))
            if inside is not False and number < version["page_count"]:
                self._insert_document_task(conn, task["job_id"], {**payload, "page_number": number + 1})
            result = {"editionPagesNew": int(new and bool(matches)), "editionPagesReused": int(not new and bool(matches)),
                "editionAssociationsNew": added, "editionTextAvailable": int(bool(key)), "editionPageProcessed": 1,
                "editionTextReused": int(reused), "outsideWindow": int(inside is False), "dateUnknown": int(inside is None)}
            self._finish(conn, task, "gap" if error else "complete", result=result, error_type=error)
        return {"taskId": task["id"], "status": "gap" if error else "complete", **result}

    @staticmethod
    def _document_filters(allowed_target_keys, *, target_keys=None, source_key="", date_from="", date_to="", job_id="", cursor="", q="", body_status=""):
        allowed = sorted(set(allowed_target_keys or []))
        if target_keys:
            if not set(target_keys).issubset(allowed):
                from .political_corpus import PoliticalAccessDenied
                raise PoliticalAccessDenied("target_not_allowed")
            allowed = sorted(set(target_keys))
        where = "EXISTS(SELECT 1 FROM political_document_mentions m WHERE m.page_version_id=pv.id AND m.target_key=ANY(%s))"
        args = [allowed]
        if source_key:
            from .political_source_catalog import source_aliases
            where += " AND d.source_key=ANY(%s)"
            args.append(source_aliases(source_key))
        if date_from:
            date.fromisoformat(date_from)
            where += " AND COALESCE(NULLIF(pv.editorial_date->>'period_to','')::date,'infinity'::date)>=%s"
            args.append(date_from)
        if date_to:
            date.fromisoformat(date_to)
            where += " AND COALESCE(NULLIF(pv.editorial_date->>'period_from','')::date,'-infinity'::date)<=%s"
            args.append(date_to)
        if job_id:
            where += " AND EXISTS(SELECT 1 FROM political_job_document_pages jp WHERE jp.page_version_id=pv.id AND jp.job_id=%s)"
            args.append(job_id)
        if cursor:
            where += " AND p.id<%s"
            args.append(int(cursor))
        if q:
            where += " AND (d.edition_label ILIKE %s OR d.source_name ILIKE %s)"
            args.extend(["%" + q + "%"] * 2)
        if body_status == "body_extracted":
            where += " AND pv.text_object_key<>''"
        elif body_status == "metadata_only":
            where += " AND pv.text_object_key=''"
        # Choose the latest version visible to this account and, if requested,
        # this job. A later edition processed for someone else must not hide an
        # authorized older edition or rewrite a historical job's results.
        where += """ AND NOT EXISTS(SELECT 1 FROM political_document_page_versions newer
            WHERE newer.page_id=p.id AND newer.document_version_id>pv.document_version_id
            AND EXISTS(SELECT 1 FROM political_document_mentions nm
                WHERE nm.page_version_id=newer.id AND nm.target_key=ANY(%s))"""
        args.append(allowed)
        if job_id:
            where += " AND EXISTS(SELECT 1 FROM political_job_document_pages nj WHERE nj.page_version_id=newer.id AND nj.job_id=%s)"
            args.append(job_id)
        where += ")"
        return where, args, allowed

    _DOCUMENT_PAGE_FROM = """FROM political_document_pages p JOIN political_documents d ON d.id=p.document_id
        JOIN political_document_page_versions pv ON pv.page_id=p.id
        JOIN political_document_versions dv ON dv.id=pv.document_version_id"""

    def document_pages(self, *, allowed_target_keys, page_size=50, **filters):
        self.ensure_schema()
        size = max(1, min(int(page_size), 200))
        where, args, allowed = self._document_filters(allowed_target_keys, **filters)
        with self._connect() as conn:
            if filters.get("job_id"):
                self._authorize_job(conn.execute("SELECT target_keys FROM political_jobs WHERE id=%s", (filters["job_id"],)).fetchone(), allowed_target_keys)
            rows = conn.execute("""SELECT p.id,p.document_id,p.page_number,d.canonical_url,d.source_key,d.source_name,d.edition_label,
                pv.id AS page_version_id,pv.document_version_id,pv.text_state,pv.text_chars,pv.extraction_method,pv.extraction_version,pv.error_type,
                pv.editorial_date,dv.sha256 AS document_sha256,dv.page_count,(pv.text_object_key<>'') AS text_available,
                ARRAY(SELECT m.target_key FROM political_document_mentions m WHERE m.page_version_id=pv.id AND m.target_key=ANY(%s)) AS target_keys
                """ + self._DOCUMENT_PAGE_FROM + " WHERE " + where + " ORDER BY p.id DESC LIMIT %s", [allowed] + args + [size + 1]).fetchall()
        more, rows = len(rows) > size, rows[:size]
        for row in rows:
            row.update({"recordType": "edition_page", "title": "", "displayLabel": f"Página {row['page_number']} · {row['edition_label']}",
                "originalUrl": row["canonical_url"] + "#page=" + str(row["page_number"])})
        return {"items": rows, "hasMore": more, "nextCursor": str(rows[-1]["id"]) if more else ""}

    def document_page_text(self, page_id, *, allowed_target_keys, page_version_id=None):
        self.ensure_schema()
        if page_version_id is not None:
            where = "pv.id=%s AND EXISTS(SELECT 1 FROM political_document_mentions m WHERE m.page_version_id=pv.id AND m.target_key=ANY(%s))"
            args = [int(page_version_id), sorted(set(allowed_target_keys or []))]
        else:
            where, args, _ = self._document_filters(allowed_target_keys)
        with self._connect() as conn:
            row = conn.execute("""SELECT p.id,p.page_number,d.canonical_url,pv.*,
                dv.sha256 AS document_sha256,dv.object_key AS document_object_key """ + self._DOCUMENT_PAGE_FROM +
                " WHERE p.id=%s AND " + where, [int(page_id)] + args).fetchone()
        if not row:
            from .political_corpus import PoliticalNotFound
            raise PoliticalNotFound("document_page_not_found")
        return {"id": int(page_id), "pageVersionId": row["id"], "recordType": "edition_page", "pageNumber": row["page_number"],
            "text": self._read_text(row["text_object_key"], row["text_hash"]), "textState": row["text_state"],
            "editorialDate": row["editorial_date"], "extractionMethod": row["extraction_method"],
            "extractionVersion": row["extraction_version"], "documentSha256": row["document_sha256"],
            "originalUrl": row["canonical_url"] + "#page=" + str(row["page_number"]), "errorType": row["error_type"]}

    def document_counts(self, *, allowed_target_keys, **filters):
        self.ensure_schema()
        where, args, allowed = self._document_filters(allowed_target_keys, **filters)
        with self._connect() as conn:
            if filters.get("job_id"):
                self._authorize_job(conn.execute("SELECT target_keys FROM political_jobs WHERE id=%s", (filters["job_id"],)).fetchone(), allowed_target_keys)
            row = conn.execute("""SELECT COUNT(*) AS edition_pages,COUNT(DISTINCT d.id) AS documents,
                COUNT(*) FILTER(WHERE pv.text_object_key<>'') AS text_available,
                COUNT(*) FILTER(WHERE pv.text_state='partial_text') AS partial_text,
                COUNT(*) FILTER(WHERE pv.text_object_key='') AS metadata_only,
                COUNT(*) FILTER(WHERE COALESCE(pv.editorial_date->>'date_status','unknown')='unknown') AS unknown_dates,
                COALESCE(SUM((SELECT COUNT(*) FROM political_document_mentions m WHERE m.page_version_id=pv.id AND m.target_key=ANY(%s))),0) AS person_associations
                """ + self._DOCUMENT_PAGE_FROM + " WHERE " + where, [allowed] + args).fetchone()
        return dict(row)
