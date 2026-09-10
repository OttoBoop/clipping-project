"""Bounded, checkpointable discovery for political clipping.

Discovery never decides whether a person is relevant: it emits section/archive
candidates before the durable fetch worker matches the actual article body.
Every network operation uses the caller's shared, rate-limited ``fetch``.
"""
from __future__ import annotations

import gzip
import hashlib
import html
import json
import os
import re
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from datetime import date, datetime, time, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlencode, urljoin, urlparse
from zoneinfo import ZoneInfo

from pipeline.collectors import (
    CAMARA_ARCHIVE_ITEM_RE, CAMARA_NEXT_RE, _extract_vejario_archive_page,
    _parse_pt_br_datetime, parse_rss_or_atom,
)
from pipeline.http_utils import canonicalize_url, html_to_text, is_likely_article_url
from pipeline.settings import google_news_rss_url

SAO_PAULO = ZoneInfo("America/Sao_Paulo")
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "political_sources_v1.json"
MAX_XML_BYTES = 20 * 1024 * 1024
MAX_CANDIDATES = 500
MAX_INDEX_CHILDREN = 500
MAX_SITEMAP_DEPTH = 5
MAX_PAGES = 2000
GOOGLE_RESULT_CAP = 100


class DiscoveryError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool = True, status_code: int = 0, retry_after: float = 0):
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code
        self.retry_after = retry_after


def load_sources() -> list[dict[str, Any]]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return payload["sources"]


def date_windows(date_from: str, date_to: str, days: int = 7) -> list[tuple[str, str]]:
    start, end = date.fromisoformat(date_from), date.fromisoformat(date_to)
    if end < start:
        raise ValueError("date_to must be on or after date_from")
    windows = []
    while start <= end:
        stop = min(start + timedelta(days=days - 1), end)
        windows.append((start.isoformat(), stop.isoformat()))
        start = stop + timedelta(days=1)
    return windows


def parse_publication_date(raw: str, *, naive_zone=SAO_PAULO) -> str:
    """Missing/unparseable dates remain unknown, never the collection date."""
    value = str(raw or "").strip()
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=naive_zone)
    return parsed.astimezone(timezone.utc).isoformat()


def in_window(published_at: str, date_from: str, date_to: str) -> bool:
    parsed = parse_publication_date(published_at)
    if not parsed:
        return True  # candidate survives for article-date extraction / review
    value = datetime.fromisoformat(parsed)
    start = datetime.combine(date.fromisoformat(date_from), time.min, SAO_PAULO)
    end = datetime.combine(date.fromisoformat(date_to) + timedelta(days=1), time.min, SAO_PAULO)
    return start <= value < end


def _target_queries(snapshot: dict[str, Any]) -> list[str]:
    names = [snapshot.get("display_name") or snapshot.get("label") or snapshot.get("name")]
    names += list(snapshot.get("keywords") or []) + list(snapshot.get("exact_aliases") or [])
    return list(dict.fromkeys('"' + str(name).strip().replace('"', '') + '"' for name in names if str(name or "").strip()))


def _google_tasks(snapshots: list[dict], source: dict, date_from: str, date_to: str) -> list[dict]:
    queries = {}
    for person_rank, row in enumerate(snapshots):
        target_id = str(row.get("key") or row.get("id") or "")
        for alias_rank, query in enumerate(_target_queries(row)):
            identity = " ".join("".join(char for char in unicodedata.normalize("NFKD", query)
                                       if not unicodedata.combining(char)).casefold().split())
            shared = queries.setdefault(identity, {"query": query, "target_ids": [],
                                                   "order": (alias_rank, person_rank)})
            shared["order"] = min(shared["order"], (alias_rank, person_rank))
            if target_id not in shared["target_ids"]:
                shared["target_ids"].append(target_id)
    # Query payloads stay identical so existing PostgreSQL dedupe keys remain
    # valid. Only insertion order changes: all people get their primary query
    # in each window before moving to secondary aliases.
    ordered = sorted(queries.values(), key=lambda item: item["order"])
    return [{"source_key": source["key"], "strategy": "google_news", "cursor": {},
             "query": item["query"] + (" site:" + source["domain"] if source.get("domain") else ""),
             "target_ids": item["target_ids"], "date_from": start, "date_to": stop}
            for alias_rank in sorted({item["order"][0] for item in ordered})
            for start, stop in date_windows(date_from, date_to)
            for item in ordered if item["order"][0] == alias_rank]


def fallback_tasks(task: dict, target_snapshots: list[dict]) -> list[dict]:
    """Called only when a direct discovery task records a terminal explicit gap.

    Stable task payloads let PostgreSQL deduplicate fallback requests caused by
    several failed direct mechanisms for the same source and time window.
    """
    source = next((row for row in load_sources() if row["key"] == task["source_key"]), None)
    if not source or source.get("google_policy") != "on_direct_gap" or task.get("strategy") == "google_news":
        return []
    start = task.get("day") or task["date_from"]
    stop = task.get("day") or task["date_to"]
    return _google_tasks(target_snapshots, source, start, stop)


def build_tasks(target_snapshots: list[dict[str, Any]], date_from: str, date_to: str,
                source_keys: list[str] | None = None) -> list[dict[str, Any]]:
    windows = date_windows(date_from, date_to)
    sources = load_sources()
    known = {source["key"] for source in sources}
    if source_keys is not None and set(source_keys) - known:
        raise ValueError("unknown political sources: " + ", ".join(sorted(set(source_keys) - known)))
    selected = known if source_keys is None else set(source_keys)
    target_ids = [str(row.get("key") or row.get("id") or "") for row in target_snapshots]
    tasks: list[dict[str, Any]] = []
    for source in sources:
        if source["key"] not in selected or not source.get("enabled", True):
            continue
        base = {"source_key": source["key"], "date_from": date_from, "date_to": date_to,
                "target_ids": target_ids, "cursor": {}}
        for strategy in source["strategies"]:
            if strategy == "google_news":
                if source.get("google_policy", "always") == "always":
                    tasks.extend(_google_tasks(target_snapshots, source, date_from, date_to))
            elif strategy == "daily_sitemap":
                for start, _ in date_windows(date_from, date_to, 1):
                    tasks.append({**base, "strategy": strategy, "day": start, "cursor": {"page": 1}})
            elif strategy == "sitemap":
                for url in source.get("sitemap_urls", []):
                    tasks.append({**base, "strategy": strategy, "url": url, "depth": 0, "ancestors": []})
            elif strategy == "wordpress":
                for rest_base in source.get("wordpress_rest_bases") or ["posts"]:
                    if not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", str(rest_base)):
                        raise ValueError("invalid publisher WordPress REST base")
                    for start, stop in windows:
                        # Keep existing /posts task identities byte-compatible.
                        # Other advertised post types need distinct durable tasks.
                        endpoint = {"rest_base": rest_base} if rest_base != "posts" else {}
                        tasks.append({**base, **endpoint, "strategy": strategy, "date_from": start, "date_to": stop,
                                      "cursor": {"page": 1}})
            elif strategy == "diario_archive":
                tasks.append({**base, "strategy": strategy, "url": source["archive_url"],
                              "cursor": {"page": 1}})
            elif strategy == "rc24h_archive":
                month = date.fromisoformat(date_from).replace(day=1)
                end = date.fromisoformat(date_to)
                while month <= end:
                    following = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
                    tasks.append({**base, "strategy": strategy, "month": month.isoformat()[:7],
                                  "date_from": max(date.fromisoformat(date_from), month).isoformat(),
                                  "date_to": min(end, following - timedelta(days=1)).isoformat(),
                                  "cursor": {"page": 1}})
                    month = following
            elif strategy in {"camara_archive", "vejario_archive"}:
                for url in source.get("archive_urls", []):
                    tasks.append({**base, "strategy": strategy, "url": url, "cursor": {"page": 1}})
            else:
                raise ValueError("unsupported political discovery strategy: " + strategy)
    return tasks


def _result(candidates=(), *, next_cursor=None, outcome=None, raw_count=0, child_tasks=(), gap_reason=""):
    return {"candidates": list(candidates), "next_cursor": next_cursor,
            "outcome": outcome or ("continue" if next_cursor else "complete"),
            "raw_count": raw_count, "child_tasks": list(child_tasks), "gap_reason": gap_reason}


def _get(fetch: Callable, url: str, *, allowed_statuses=(), **kwargs):
    try:
        response = fetch(url, **kwargs)
    except DiscoveryError:
        raise
    except Exception as exc:
        raise DiscoveryError(f"request failed: {type(exc).__name__}: {str(exc)[:200]}",
                             retryable=bool(getattr(exc, "retryable", True)),
                             status_code=int(getattr(exc, "status_code", 0) or 0),
                             retry_after=float(getattr(exc, "retry_after", 0) or 0)) from exc
    status = int(response.status_code)
    if status >= 400 and status not in allowed_statuses:
        retry = str(response.headers.get("Retry-After") or "0")
        try:
            retry_after = max(0, float(retry))
        except ValueError:
            try:
                retry_after = max(0, (parsedate_to_datetime(retry) - datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError):
                retry_after = 0
        raise DiscoveryError(f"HTTP {status} at {urlparse(url).netloc}{urlparse(url).path}",
                             retryable=status in {408, 425, 429} or status >= 500,
                             status_code=status, retry_after=retry_after)
    return response


def _xml(response) -> ET.Element:
    content = getattr(response, "content", None)
    if not isinstance(content, bytes):
        content = response.text.encode("utf-8")
    if len(content) > MAX_XML_BYTES:
        raise DiscoveryError("sitemap byte limit reached", retryable=False)
    if content.startswith(b"\x1f\x8b"):
        # Read a bounded decompressed stream, including gzip bombs.
        import io
        with gzip.GzipFile(fileobj=io.BytesIO(content)) as stream:
            content = stream.read(MAX_XML_BYTES + 1)
        if len(content) > MAX_XML_BYTES:
            raise DiscoveryError("expanded sitemap byte limit reached", retryable=False)
    if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
        raise DiscoveryError("unsupported XML entity declaration", retryable=False)
    try:
        return ET.fromstring(content)
    except ET.ParseError as exc:
        raise DiscoveryError("malformed XML response") from exc


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(node, name: str) -> str:
    return next(((child.text or "").strip() for child in node.iter() if _local(child.tag) == name), "")


def _sitemap_title(node) -> str:
    # Image captions use image:title in real Tupi sitemaps. They are not an
    # article headline; accept a direct title or the Google News namespace only.
    return next(((child.text or "").strip() for child in node.iter()
                 if child.tag in {"title", "{http://www.google.com/schemas/sitemap-news/0.9}title"}), "")


def _allowed_url(url: str, source: dict, *, article=False) -> bool:
    parsed = urlparse(url)
    domain = source.get("domain", "")
    host = parsed.hostname or ""
    if parsed.scheme not in {"http", "https"} or not domain or not (host == domain or host.endswith("." + domain)):
        return False
    if not article:
        return True
    if not is_likely_article_url(url):
        return False
    sections = source.get("section_patterns") or []
    return not sections or any(re.search(pattern, parsed.path, re.I) for pattern in sections)


def _candidate(source, url, title="", published_at="", snippet="", metadata=None):
    return {"url": canonicalize_url(url), "title": html_to_text(title), "source_key": source["key"],
            "source_name": source["name"], "source_type": "political_discovery",
            "published_at": parse_publication_date(published_at), "snippet": html_to_text(snippet),
            "metadata": dict(metadata or {})}


def _google(task, source, fetch):
    start = date.fromisoformat(task["date_from"])
    end = date.fromisoformat(task["date_to"])
    # Google before: excludes the supplied date. A one-day overlap at the start
    # protects local-time boundaries; publication dates enforce the exact window.
    query = f'{task["query"]} after:{(start - timedelta(days=1)).isoformat()} before:{(end + timedelta(days=1)).isoformat()}'
    response = _get(fetch, google_news_rss_url(query))
    root = _xml(response)
    if _local(root.tag) not in {"rss", "feed"}:
        raise DiscoveryError("Google returned a non-feed response")
    items = parse_rss_or_atom(ET.tostring(root, encoding="unicode"), "Google News", "google_news")
    # RSS/Atom parsing can discard entries without a link. Saturation must use
    # publisher page evidence, including those malformed entries.
    raw_count = sum(_local(node.tag) in {"item", "entry"} for node in root.iter())
    malformed_count = max(0, raw_count - len(items))
    results = []
    seen = set()
    for item in items:
        url = item.url
        # Related-story anchors in RSS descriptions may describe other stories;
        # only use a direct link when its anchor text matches this item's title.
        for href, label in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', item.snippet, re.I | re.S):
            if "news.google.com" not in (urlparse(href).hostname or "") and html_to_text(label) == html_to_text(item.title):
                url = href
                break
        url = canonicalize_url(url)
        if url in seen or not in_window(item.published_at, task["date_from"], task["date_to"]):
            continue
        seen.add(url)
        results.append(_candidate(source, url, item.title, item.published_at, item.snippet,
                                  {"query": task["query"], "google_redirect": (urlparse(url).hostname == "news.google.com")}))
    if raw_count >= GOOGLE_RESULT_CAP:
        if start < end:
            midpoint = start + timedelta(days=(end - start).days // 2)
            children = [{**task, "date_from": lo.isoformat(), "date_to": hi.isoformat(), "cursor": {}}
                        for lo, hi in ((start, midpoint), (midpoint + timedelta(days=1), end))]
            return _result(results, outcome="split", raw_count=raw_count, child_tasks=children)
        reason = "google_daily_result_cap"
        if malformed_count:
            reason += f"; google_malformed_entries:{malformed_count}"
        return _result(results, outcome="gap", raw_count=raw_count, gap_reason=reason)
    if malformed_count:
        return _result(results, outcome="gap", raw_count=raw_count,
                       gap_reason=f"google_malformed_entries:{malformed_count}")
    return _result(results, raw_count=raw_count)


def _stream_sitemap_entries(stream):
    """Yield and release direct URL children; neither XML nor entries accumulate."""
    parser = ET.XMLPullParser(events=("start", "end"))
    root, depth, tail, entry_bytes = None, 0, b"", 0
    try:
        while chunk := stream.read(65536):
            probe = (tail + chunk).upper()
            if b"<!DOCTYPE" in probe or b"<!ENTITY" in probe:
                raise DiscoveryError("unsupported XML entity declaration", retryable=False)
            tail = probe[-16:]
            entry_bytes += len(chunk)
            if entry_bytes > 2 * 1024 * 1024:
                raise DiscoveryError("sitemap entry byte limit reached", retryable=False)
            parser.feed(chunk)
            for event, node in parser.read_events():
                if event == "start":
                    depth += 1
                    if root is None:
                        root = node
                        if _local(node.tag) != "urlset":
                            raise DiscoveryError("streaming sitemap response is not urlset")
                else:
                    if depth == 2:
                        if _local(node.tag) != "url":
                            raise DiscoveryError("unexpected streaming sitemap entry")
                        yield node
                        root.remove(node)
                        node.clear()
                        entry_bytes = 0
                    depth -= 1
        parser.close()
        if root is None:
            raise DiscoveryError("empty sitemap response")
    except ET.ParseError as exc:
        raise DiscoveryError("malformed XML response") from exc


def _stream_sitemap(task, source, fetch):
    cursor = dict(task.get("cursor") or {})
    response = _get(fetch, task["url"], stream_sitemap=True, sitemap_snapshot=cursor.get("snapshot", ""))
    snapshot = str(getattr(response, "sitemap_snapshot", ""))
    # A cache lost during a worker restart can be reconstructed. If the publisher
    # changed the content, restart its index; canonical fetch dedupe protects saves.
    offset = int(cursor.get("offset") or 0) if snapshot and snapshot == cursor.get("snapshot") else 0
    path = getattr(response, "sitemap_path", None)
    if not path or not snapshot:
        raise DiscoveryError("streaming sitemap transport unavailable", retryable=False)
    # Build a bounded disk index once per immutable snapshot. Byte cursors then
    # seek directly to the next entry instead of downloading/parsing a huge annual
    # map again for every 500 URLs. Missing worker-local files are reconstructible.
    index_path = Path(str(path) + ".entries.jsonl")
    if not index_path.exists():
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=index_path.parent, mode="wb", delete=False) as output:
                temporary = output.name
                with Path(path).open("rb") as stream:
                    for node in _stream_sitemap_entries(stream):
                        row = {"url": _child_text(node, "loc"), "title": _sitemap_title(node),
                               "published": _child_text(node, "publication_date")}
                        output.write((json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8"))
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, index_path)
            temporary = None
        finally:
            if temporary:
                Path(temporary).unlink(missing_ok=True)
    candidates, raw_count, malformed = [], 0, int(cursor.get("malformed") or 0) if offset else 0
    with index_path.open("rb") as stream:
        if offset > index_path.stat().st_size:
            raise DiscoveryError("invalid sitemap snapshot cursor", retryable=False)
        stream.seek(offset)
        while line := stream.readline(2 * 1024 * 1024 + 1):
            if len(line) > 2 * 1024 * 1024:
                raise DiscoveryError("sitemap entry byte limit reached", retryable=False)
            row = json.loads(line)
            raw_count += 1
            if not row["url"]:
                malformed += 1
            elif _allowed_url(row["url"], source, article=True) and in_window(row["published"], task["date_from"], task["date_to"]):
                candidates.append(_candidate(source, row["url"], row["title"], row["published"],
                    metadata={"sitemap_url": task["url"], "needs_date_review": not bool(row["published"])}))
            if raw_count >= MAX_CANDIDATES:
                return _result(candidates, raw_count=raw_count,
                               next_cursor={"offset": stream.tell(), "snapshot": snapshot, "malformed": malformed})
    return _result(candidates, raw_count=raw_count, outcome="gap" if malformed else "complete",
                   gap_reason=f"sitemap_missing_locations:{malformed}" if malformed else "")


def _sitemap(task, source, fetch):
    cursor = dict(task.get("cursor") or {})
    page = int(cursor.get("page") or 1)
    if task["strategy"] == "daily_sitemap":
        day = date.fromisoformat(task["day"])
        url = source["sitemap_template"].format(yyyy=day.strftime("%Y"), mm=day.strftime("%m"), dd=day.strftime("%d"), page=page)
    else:
        url = task["url"]
    if not _allowed_url(url, source):
        raise DiscoveryError("sitemap URL outside source domain", retryable=False)
    if source.get("stream_sitemap_pattern") and re.fullmatch(source["stream_sitemap_pattern"], url):
        return _stream_sitemap({**task, "url": url}, source, fetch)
    sitemap_url = url
    root = _xml(_get(fetch, url))
    kind = _local(root.tag)
    entries = list(root)
    offset = max(0, int(cursor.get("offset") or 0))
    if kind == "sitemapindex":
        if int(task.get("depth") or 0) >= MAX_SITEMAP_DEPTH:
            return _result(outcome="gap", gap_reason="sitemap_depth_cap", raw_count=len(entries))
        ancestors = list(task.get("ancestors") or []) + [url]
        children = []
        unsafe = 0
        partition_gap = bool(cursor.get("partition_gap"))
        calendar_pattern = source.get("sitemap_index_date_pattern")
        year_pattern = source.get("sitemap_index_year_pattern")
        for node in entries[offset:offset + MAX_INDEX_CHILDREN]:
            child_url = _child_text(node, "loc")
            if any(re.fullmatch(pattern, child_url) for pattern in source.get("sitemap_index_exclude_patterns", [])):
                continue  # Explicit publisher branches for taxonomies/authors/webstories.
            if child_url in ancestors:
                unsafe += 1
            elif not _allowed_url(child_url, source):
                unsafe += 1
            elif child_url:
                partition_status = ""
                if year_pattern:
                    year_match = re.fullmatch(year_pattern, child_url)
                    if year_match:
                        if not date.fromisoformat(task["date_from"]).year <= int(year_match["year"]) <= date.fromisoformat(task["date_to"]).year:
                            continue
                        partition_status = "requested_year_partition"
                if calendar_pattern:
                    match = re.fullmatch(calendar_pattern, child_url)
                    try:
                        partition_day = date(int(match["year"]), int(match["month"]), int(match["day"])) if match else None
                    except (ValueError, IndexError):
                        partition_day = None
                    if partition_day is None:
                        # Unknown children still run; retain a visible gap so a
                        # changed publisher index cannot silently lose coverage.
                        partition_gap = True
                        partition_status = "unrecognized_calendar_partition"
                    elif not date.fromisoformat(task["date_from"]) <= partition_day <= date.fromisoformat(task["date_to"]):
                        continue
                    else:
                        partition_status = "requested_calendar_partition"
                child = {**task, "strategy": "sitemap", "url": child_url, "depth": int(task.get("depth") or 0) + 1,
                         "ancestors": ancestors, "cursor": {}}
                if partition_status:
                    child["partition_status"] = partition_status
                children.append(child)
        had_gap = bool(unsafe or cursor.get("index_gap"))
        next_cursor = {**cursor, "offset": offset + MAX_INDEX_CHILDREN} if offset + MAX_INDEX_CHILDREN < len(entries) else None
        if next_cursor and had_gap:
            next_cursor["index_gap"] = True
        if next_cursor and partition_gap:
            next_cursor["partition_gap"] = True
        terminal_gap = (had_gap or partition_gap) and not next_cursor
        reasons = []
        if had_gap:
            reasons.append("invalid_or_cyclic_sitemap_child")
        if partition_gap:
            reasons.append("unrecognized_sitemap_calendar_partition")
        return _result(child_tasks=children, next_cursor=next_cursor, raw_count=len(entries[offset:offset + MAX_INDEX_CHILDREN]),
                       outcome="gap" if terminal_gap else None, gap_reason="; ".join(reasons) if terminal_gap else "")
    if kind != "urlset":
        raise DiscoveryError("sitemap response is neither urlset nor sitemapindex")
    candidates = []
    window_days = (date.fromisoformat(task["date_to"]) - date.fromisoformat(task["date_from"])).days + 1
    defer_undated = 0 < window_days <= int(source.get("defer_undated_sitemap_up_to_days") or 0)
    deferred = int(cursor.get("undated_deferred") or 0)
    for node in entries[offset:offset + MAX_CANDIDATES]:
        url = _child_text(node, "loc")
        if not _allowed_url(url, source, article=True):
            continue
        # lastmod is a modification date, never an article publication date.
        published = _child_text(node, "publication_date")
        if defer_undated and not parse_publication_date(published):
            deferred += 1
            continue
        if not in_window(published, task["date_from"], task["date_to"]):
            continue
        candidates.append(_candidate(source, url, _sitemap_title(node), published,
                                     metadata={"sitemap_url": sitemap_url,
                                               "discovery_day": task.get("day", ""), "needs_date_review": not bool(published)}))
    next_cursor = None
    if offset + MAX_CANDIDATES < len(entries):
        next_cursor = {**cursor, "offset": offset + MAX_CANDIDATES}
        if deferred:
            next_cursor["undated_deferred"] = deferred
    elif task["strategy"] == "daily_sitemap" and entries:
        if page >= int(source.get("max_pages") or MAX_PAGES):
            return _result(candidates, outcome="gap", raw_count=len(entries), gap_reason="sitemap_page_cap")
        next_cursor = {"page": page + 1}
    return _result(candidates, next_cursor=next_cursor, raw_count=len(entries[offset:offset + MAX_CANDIDATES]),
                   outcome="gap" if deferred and not next_cursor else None,
                   gap_reason=f"undated_sitemap_deferred_for_narrow_window:{deferred}" if deferred and not next_cursor else "")


def _wordpress_numeric_permalink(row, source, published):
    """J3 advertises dated numeric post permalinks through its public API.

    Keep the general article URL heuristic unchanged. This exception requires
    the publisher's exact post ID and local publication day to agree with its
    own URL, so arbitrary numeric paths cannot enter through other discovery.
    """
    if source.get("key") != "j3news" or type(row.get("id")) is not int or row["id"] <= 0 or not published:
        return False
    url = str(row.get("link") or "")
    if not _allowed_url(url, source):
        return False
    parsed = urlparse(url)
    match = re.fullmatch(r"/(\d{4})/(\d{2})/(\d{2})/(\d+)/?", parsed.path)
    if not match or parsed.query or parsed.fragment or int(match[4]) != row["id"]:
        return False
    try:
        permalink_day = date(int(match[1]), int(match[2]), int(match[3]))
        publication_day = datetime.fromisoformat(published).astimezone(SAO_PAULO).date()
    except (ValueError, TypeError):
        return False
    return permalink_day == publication_day


def _wordpress(task, source, fetch):
    from .political_body_batches import WORDPRESS_BODY_SOURCES
    rest_base = task.get("rest_base") or "posts"
    if rest_base not in (source.get("wordpress_rest_bases") or ["posts"]) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", str(rest_base)):
        raise DiscoveryError("unadvertised WordPress REST base", retryable=False)
    include_body = source["key"] in WORDPRESS_BODY_SOURCES
    page = max(1, int((task.get("cursor") or {}).get("page") or 1))
    params = {"page": page, "per_page": 100, "orderby": "date", "order": "desc",
              "after": task["date_from"] + "T00:00:00", "before": (date.fromisoformat(task["date_to"]) + timedelta(days=1)).isoformat() + "T00:00:00",
              "_fields": "id,link,title,excerpt,date,date_gmt"}
    if include_body:
        params["_fields"] += ",content,modified_gmt"
    # No title/name search: date scans discover people mentioned only in bodies.
    endpoint = source["base_url"].rstrip("/") + "/wp-json/wp/v2/" + rest_base + "?"
    body_batch_fallback = ""
    try:
        response = _get(fetch, endpoint + urlencode(params), allowed_statuses=(400,))
    except DiscoveryError as exc:
        # Adding full bodies can exceed the transport's existing 8MiB/35s
        # response budget. Retry only that precise failure as the original
        # metadata query, preserving page size, page number and date bounds.
        # HTTP429/503, cooldowns and unrelated timeouts keep normal retry policy.
        cause, budget_failure = exc, False
        for _ in range(5):
            if cause is None:
                break
            if str(cause) in {"response_budget_exceeded", "response_too_large"} and not getattr(cause, "status_code", 0):
                budget_failure = True
                break
            cause = cause.__cause__
        if not include_body or not budget_failure:
            raise
        include_body = False
        body_batch_fallback = "api_body_response_budget"
        params["_fields"] = "id,link,title,excerpt,date,date_gmt"
        response = _get(fetch, endpoint + urlencode(params), allowed_statuses=(400,))
    try:
        payload = json.loads(response.text)
    except (ValueError, TypeError) as exc:
        raise DiscoveryError("malformed WordPress JSON") from exc
    if response.status_code == 400:
        if isinstance(payload, dict) and payload.get("code") == "rest_post_invalid_page_number" and page > 1:
            return _result(raw_count=0)
        raise DiscoveryError("WordPress HTTP 400 without confirmed pagination exhaustion", retryable=False, status_code=400)
    if not isinstance(payload, list):
        raise DiscoveryError("WordPress response is not a post list")
    candidates = []
    body_records = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        raw_date = row.get("date_gmt") or row.get("date") or ""
        published = parse_publication_date(raw_date, naive_zone=timezone.utc if row.get("date_gmt") else SAO_PAULO)
        numeric_permalink = _wordpress_numeric_permalink(row, source, published)
        if not _allowed_url(str(row.get("link") or ""), source, article=True) and not numeric_permalink:
            continue
        if not in_window(published, task["date_from"], task["date_to"]):
            continue
        rendered = lambda value: (value or {}).get("rendered", "") if isinstance(value, dict) else str(value or "")
        candidates.append(_candidate(source, row["link"], rendered(row.get("title")), published,
                                     rendered(row.get("excerpt")), {"wordpress_id": row.get("id"), "collection_mode": "date_scan"}))
        if numeric_permalink:
            candidates[-1]["metadata"]["wordpress_numeric_permalink_verified"] = True
        if rest_base != "posts":
            candidates[-1]["metadata"]["wordpress_rest_base"] = rest_base
        content = row.get("content")
        if include_body and published and isinstance(content, dict) and isinstance(content.get("rendered"), str) and type(row.get("id")) is int:
            body_records.append({"post_id": row["id"], "url": candidates[-1]["url"], "published_at": published,
                                 "content_html": content["rendered"], "protected": content.get("protected") is not False,
                                 "modified_gmt": str(row.get("modified_gmt") or "")})
    total_pages_raw = response.headers.get("X-WP-TotalPages") or response.headers.get("x-wp-totalpages")
    try:
        total_pages = int(total_pages_raw) if total_pages_raw is not None else None
    except (ValueError, TypeError) as exc:
        raise DiscoveryError("invalid WordPress page count") from exc
    has_next = page < total_pages if total_pages is not None else len(payload) >= 100
    if has_next and page >= MAX_PAGES:
        result = _result(candidates, outcome="gap", raw_count=len(payload), gap_reason="wordpress_page_cap")
    else:
        result = _result(candidates, next_cursor={"page": page + 1} if has_next else None, raw_count=len(payload))
    if body_records:
        # Ephemeral discovery output only. The worker stores one immutable object
        # before attaching small references to candidate tasks and committing the cursor.
        result["body_batch"] = {"source_key": source["key"], "records": body_records}
    if body_batch_fallback:
        result["body_batch_fallback"] = body_batch_fallback
    return result


def _archive(task, source, fetch):
    cursor = dict(task.get("cursor") or {})
    page = max(1, int(cursor.get("page") or 1))
    url = cursor.get("url") or task["url"]
    if not _allowed_url(url, source):
        raise DiscoveryError("archive URL outside source domain", retryable=False)
    response = _get(fetch, url)
    raw_html = response.text
    candidates = []
    chronology = {}
    date_cutoff = False
    chronology_gap = False
    if task["strategy"] == "camara_archive":
        rows = CAMARA_ARCHIVE_ITEM_RE.findall(raw_html)
        page_dates = []
        for raw_date, href, title in rows:
            item_url = urljoin(url, html.unescape(href))
            published = _parse_pt_br_datetime(raw_date)
            parsed_date = parse_publication_date(published)
            page_dates.append(datetime.fromisoformat(parsed_date).astimezone(SAO_PAULO).date() if parsed_date else None)
            if _allowed_url(item_url, source, article=True) and in_window(published, task["date_from"], task["date_to"]):
                candidates.append(_candidate(source, item_url, title, published))
        match = CAMARA_NEXT_RE.search(raw_html)
        next_url = urljoin(url, html.unescape(match.group(1))) if match else ""
        if source.get("archive_date_order") == "observed_descending" and rows:
            # Check every raw date marker, including entries our article regex
            # failed to recognize. Unknown rows cannot prove a date cutoff.
            raw_date_count = len(re.findall(r'\bcatItemDateCreated\b', raw_html))
            fully_dated = len(page_dates) == raw_date_count and all(page_dates)
            ordered = fully_dated and page_dates == sorted(page_dates, reverse=True)
            previous = str(cursor.get("previous_oldest") or "")
            try:
                previous_oldest = date.fromisoformat(previous) if previous else None
            except ValueError:
                previous_oldest = None
            boundary_ordered = not previous_oldest or (fully_dated and max(page_dates) <= previous_oldest)
            chronology_gap = bool(cursor.get("chronology_gap")) or not ordered or not boundary_ordered
            if page > 1 and (not previous_oldest or not cursor.get("ordered_pages")):
                chronology_gap = True  # A legacy cursor has no verified earlier ordering.
            ordered_pages = int(cursor.get("ordered_pages") or 0) + 1 if ordered and boundary_ordered else 0
            chronology = {"ordered_pages": ordered_pages}
            if fully_dated:
                chronology["previous_oldest"] = min(page_dates).isoformat()
            if chronology_gap:
                chronology["chronology_gap"] = True
            entirely_older = fully_dated and max(page_dates) < date.fromisoformat(task["date_from"])
            # One old first page is insufficient. An observed ordering break
            # remains a visible gap when the dated portion passes the window.
            date_cutoff = entirely_older and previous_oldest is not None and int(cursor.get("ordered_pages") or 0) >= 1
    else:
        config = {"host": source["domain"], "source_name": source["name"], "article_path_prefix": "/"}
        rows, next_url = _extract_vejario_archive_page(raw_html, url, config)
        candidates = [_candidate(source, row.url, row.title, row.published_at, row.snippet)
                      for row in rows if in_window(row.published_at, task["date_from"], task["date_to"])]
    if not rows and not next_url and not re.search(r'nenhum|sem resultados|no results', raw_html, re.I):
        raise DiscoveryError("archive markup not recognized; exhaustion unconfirmed")
    if next_url and date_cutoff:
        return _result(candidates, raw_count=len(rows), outcome="gap" if chronology_gap else "complete",
                       gap_reason="archive_date_order_unproven" if chronology_gap else "")
    if next_url and (next_url == url or page >= int(source.get("max_pages") or MAX_PAGES)):
        return _result(candidates, outcome="gap", raw_count=len(rows), gap_reason="archive_page_cap_or_cycle")
    return _result(candidates, next_cursor={"page": page + 1, "url": next_url, **chronology} if next_url else None, raw_count=len(rows))


class _RCArchiveCards(HTMLParser):
    """Read only the publisher's primary result loop, never footer headlines."""
    def __init__(self, block_id=None):
        super().__init__(convert_charrefs=True)
        self.block_id, self.stack, self.rows = block_id, [], []
        self.raw_count, self.heading = 0, None
        self.root_found = block_id is None

    def handle_starttag(self, tag, attrs):
        attrs = {key: value or "" for key, value in attrs}
        inside = self.block_id is None or bool(self.stack and self.stack[-1][1]) or attrs.get("id") == self.block_id
        self.root_found |= inside
        classes = attrs.get("class", "").split()
        is_module = any(value == "tdb_module_loop" or value.startswith("tdb_module_loop_") for value in classes)
        post_card = bool(self.stack and self.stack[-1][2])
        if inside and is_module:
            self.raw_count += 1
            post_card = "td-cpt-post" in classes
        if inside and tag == "h3" and "entry-title" in classes:
            self.heading = {"url": "", "title": "", "publisher_post_card": post_card,
                            "publisher_bookmark": False}
        if self.heading is not None and tag == "a" and not self.heading["url"]:
            self.heading["url"] = attrs.get("href", "")
            self.heading["publisher_bookmark"] = "bookmark" in attrs.get("rel", "").split()
        if tag not in _VOID_TAGS:
            self.stack.append((tag, inside, post_card))

    def handle_data(self, data):
        if self.heading is not None:
            self.heading["title"] += data

    def handle_endtag(self, tag):
        if tag == "h3" and self.heading is not None:
            if self.heading["url"] and self.heading["title"].strip():
                self.rows.append(self.heading)
            self.heading = None
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break


def _rc24h_card_url_allowed(row, source):
    if _allowed_url(row["url"], source, article=True):
        return True
    # RC's actual June archive advertises a valid /__trashed-3/ news article.
    # Accept short slugs only from an explicit publisher post card's bookmark;
    # keep arbitrary URLs, taxonomy links, assets and other sources unchanged.
    if source.get("key") != "rc24h" or not row.get("publisher_post_card") or not row.get("publisher_bookmark"):
        return False
    if not _allowed_url(row["url"], source):
        return False
    parsed = urlparse(row["url"])
    slug = parsed.path.strip("/")
    reserved = {"feed", "rss", "tag", "tags", "author", "category", "page", "search",
                "login", "logout", "wp-admin", "wp-login", "robots", "sitemap"}
    return bool(not parsed.query and not parsed.fragment and slug not in reserved
                and re.fullmatch(r"/[a-zA-Z0-9_-]{1,11}/?", parsed.path))


def _rc24h_archive(task, source, fetch):
    cursor = task.get("cursor") or {}
    page = max(1, int(cursor.get("page") or 1))
    seen = list(cursor.get("seen_pages") or [])

    def fingerprint(rows):
        return hashlib.sha256(json.dumps(sorted(canonicalize_url(row["url"]) for row in rows)).encode()).hexdigest()

    month = date.fromisoformat(task["month"] + "-01")
    archive_url = f"https://{source['domain']}/{month:%Y/%m}/"
    # Refresh the publisher's public pagination token/config on every resumed
    # step. Persist page evidence, not an expiring token or executable script.
    raw = _get(fetch, archive_url).text
    config = None
    for match in re.finditer(r"block_(\w+)\.atts\s*=\s*'([^']{1,50000})';", raw):
        try:
            attrs = json.loads(match.group(2))
        except ValueError:
            continue
        if isinstance(attrs, dict) and attrs.get("block_type") == "tdb_loop" and attrs.get("date_query") == {"year": month.year, "month": month.month, "day": ""}:
            config = (match.group(1), attrs)
            break
    endpoint = re.search(r'var td_ajax_url\s*=\s*("[^"\n]+")', raw)
    token = re.search(r'var tdBlockNonce\s*=\s*("[^"\n]+")', raw)
    if not config or not endpoint or not token:
        return _result(outcome="gap", gap_reason="rc24h_monthly_loop_configuration_missing")
    block_id, attrs = config
    try:
        endpoint, token = json.loads(endpoint.group(1)), json.loads(token.group(1))
        offset, limit = int(attrs.get("offset") or 0), int(attrs.get("limit") or 0)
    except (ValueError, TypeError):
        return _result(outcome="gap", gap_reason="rc24h_monthly_loop_configuration_invalid")
    if not _allowed_url(endpoint, source) or urlparse(endpoint).path != "/wp-admin/admin-ajax.php":
        return _result(outcome="gap", gap_reason="rc24h_unrecognized_public_pagination_endpoint")
    if offset != 3 or not offset < limit <= MAX_CANDIDATES or cursor.get("archive_offset", offset) != offset or cursor.get("archive_limit", limit) != limit:
        return _result(outcome="gap", gap_reason="rc24h_archive_offset_or_limit_changed")

    def ajax(current_page, query_attrs):
        response = _get(fetch, endpoint, method="POST", headers={"Referer": archive_url}, data={
            "action": "td_ajax_block", "td_atts": json.dumps(query_attrs), "td_block_id": block_id,
            "td_column_number": str(query_attrs.get("td_column_number") or 3), "td_current_page": str(current_page),
            "block_type": "tdb_loop", "td_filter_value": "", "td_user_action": "", "td_magic_token": token})
        try:
            payload = json.loads(response.text)
        except (ValueError, TypeError):
            return None
        if not isinstance(payload, dict) or payload.get("td_block_id") != block_id or not isinstance(payload.get("td_data"), str) or not isinstance(payload.get("td_hide_next"), bool):
            return None
        parsed = _RCArchiveCards()
        parsed.feed(payload["td_data"])
        return parsed, payload["td_hide_next"]

    recovered = []
    recovery_raw = 0
    parse_gap = bool(cursor.get("parse_gap"))
    if page == 1:
        parsed = _RCArchiveCards(block_id)
        parsed.feed(raw)
        if not parsed.root_found:
            return _result(outcome="gap", gap_reason="rc24h_primary_archive_loop_missing")
        # The public template omits three initial entries. Offset zero works for
        # this one prefix request, but REAL page2/page56 probes repeat page1.
        # All subsequent pages must retain the advertised offset of three.
        prefix = ajax(1, {**attrs, "offset": "0"})
        if prefix is None:
            return _result(outcome="gap", gap_reason="rc24h_prefix_response_invalid")
        head, _ = prefix
        recovery_raw = head.raw_count
        recovered = head.rows[:offset]
        if head.rows:
            seen.append(fingerprint(head.rows))
        if len(head.rows) < offset or [row["url"] for row in head.rows[offset:]] != [row["url"] for row in parsed.rows[:limit - offset]]:
            parse_gap = True
        parse_gap |= head.raw_count != len(head.rows)
        finished = False  # publisher AJAX response supplies exhaustion later
    else:
        response = ajax(page, attrs)
        if response is None:
            return _result(outcome="gap", gap_reason="rc24h_pagination_response_invalid")
        parsed, finished = response
    parse_gap |= parsed.raw_count != len(parsed.rows)
    candidates = []
    for row in recovered + parsed.rows:
        if _rc24h_card_url_allowed(row, source):
            candidates.append(_candidate(source, row["url"], row["title"], metadata={
                "archive_month": task["month"], "archive_url": archive_url, "needs_date_review": True,
                "collection_mode": "public_monthly_archive",
                "publisher_post_card": bool(row.get("publisher_post_card")),
                "publisher_bookmark": bool(row.get("publisher_bookmark")),
                "discovery_short_permalink": not _allowed_url(row["url"], source, article=True)}))
        else:
            parse_gap = True
    page_fingerprint = fingerprint(parsed.rows)
    raw_count = parsed.raw_count + recovery_raw
    if parsed.rows and page_fingerprint in seen:
        return _result(candidates, outcome="gap", raw_count=raw_count, gap_reason="rc24h_repeated_archive_page")
    if finished:
        return _result(candidates, outcome="gap" if parse_gap else "complete", raw_count=raw_count,
                       gap_reason="rc24h_archive_parse_gap" if parse_gap else "")
    if not parsed.raw_count or page >= int(source.get("max_pages") or 100):
        return _result(candidates, outcome="gap", raw_count=raw_count, gap_reason="rc24h_empty_page_or_page_cap")
    return _result(candidates, raw_count=raw_count, next_cursor={"page": page + 1, "archive_offset": offset, "archive_limit": limit,
                   "parse_gap": parse_gap, "seen_pages": seen + [page_fingerprint]})


def discover(task: dict[str, Any], fetch: Callable) -> dict[str, Any]:
    source = next((row for row in load_sources() if row["key"] == task["source_key"]), None)
    if source is None:
        raise DiscoveryError("unknown source", retryable=False)
    strategy = task["strategy"]
    if strategy == "google_news":
        return _google(task, source, fetch)
    if strategy in {"sitemap", "daily_sitemap"}:
        return _sitemap(task, source, fetch)
    if strategy == "wordpress":
        return _wordpress(task, source, fetch)
    if strategy == "diario_archive":
        from .political_diario_archive import discover_archive
        return discover_archive(task, source, fetch)
    if strategy == "rc24h_archive":
        return _rc24h_archive(task, source, fetch)
    if strategy in {"camara_archive", "vejario_archive"}:
        return _archive(task, source, fetch)
    raise DiscoveryError("unknown discovery strategy", retryable=False)


_VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
_RELATED = re.compile(r'(?:related|relacionad|recommend|recomendad|leia[-_ ]?mais|read[-_ ]?more|sidebar|newsletter|comments|comentarios|social-share|outbrain|taboola|post-expansivel|more-posts|widget-playlist-player|passador-materia)', re.I)
_BODY = re.compile(r'(?:entry-content|post-content|article-content|materia-content|content-body|article-body|articleBody|mc-article-body|story-body|content-txt-single)', re.I)
_GLOBO_ARTICLE_HOSTS = {"g1.globo.com", "extra.globo.com", "oglobo.globo.com", "cbn.globo.com"}


class _GloboArticleLinkList(HTMLParser):
    """Recognize Globo's headline-only lists, preserving ordinary linked prose."""
    def __init__(self, document_url):
        super().__init__()
        self.document = urlparse(document_url)
        self.tags = []
        self.items = []
        self.item = None
        self.valid = True

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "ul" and "ul" in self.tags:
            self.valid = False
        if tag == "li":
            if self.item is not None:
                self.valid = False
            self.item = {"links": [], "lead": "", "linked_text": False}
        if tag == "a" and self.item is not None:
            link = urlparse(urljoin(self.document.geturl(), attrs.get("href") or ""))
            self.item["links"].append(
                link.scheme in {"http", "https"} and link.hostname == self.document.hostname
                and link.path.endswith(".ghtml") and link.path != self.document.path)
        if tag not in _VOID_TAGS:
            self.tags.append(tag)

    def handle_data(self, data):
        if not data.strip():
            return
        if self.item is None:
            self.valid = False
        elif "a" in self.tags:
            self.item["linked_text"] = True
        elif "strong" in self.tags:
            self.item["lead"] += data
        else:
            # A genuine list item may cite a previous report while retaining
            # its own prose. It must survive this narrowly scoped cleanup.
            self.valid = False

    def handle_endtag(self, tag):
        if tag == "li" and self.item is not None:
            self.items.append(self.item)
            self.item = None
        for index in range(len(self.tags) - 1, -1, -1):
            if self.tags[index] == tag:
                del self.tags[index:]
                break

    def is_related(self):
        return self.valid and bool(self.items) and all(
            item["links"] and all(item["links"]) and item["linked_text"]
            and (not item["lead"].strip() or item["lead"].rstrip().endswith((":", ";")))
            for item in self.items)


class _ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.parts = []
        self.blocks = []
        self.scoped_blocks = []
        self.publisher_editorial_blocks = []
        self.globo_link_lists = []
        self.body_scope = 0
        self.cleaned_scopes = set()
        self.title = ""
        self.published = ""
        self.canonical = ""
        self.document_url = ""
        self.json_ld = []
        self.script = None
        self.head_title = []
        self._publisher_identity = None
        self._publisher_hostname = ""

    def publisher_host(self):
        # A large Globo page contains thousands of tags. Its document identity
        # changes only when metadata is encountered, so parse it once per change.
        identity = self.document_url or self.canonical
        if identity != self._publisher_identity:
            self._publisher_identity = identity
            self._publisher_hostname = (urlparse(identity).hostname or "").lower().rstrip(".")
        return self._publisher_hostname

    def handle_starttag(self, tag, attrs):
        # HTML permits valueless attributes (for example <div class>), which
        # HTMLParser represents as None. Real Globo pages contain these.
        attrs = {key: value or "" for key, value in attrs}
        for _, _, probe in self.globo_link_lists:
            probe.handle_starttag(tag, attrs.items())
        if tag == "meta":
            key = attrs.get("property") or attrs.get("name")
            if key in {"og:title", "twitter:title"} and not self.title:
                self.title = attrs.get("content", "")
            if key == "og:url" and not self.document_url:
                self.document_url = attrs.get("content", "")
            if key in {"article:published_time", "pubdate", "datePublished"} and not self.published:
                self.published = parse_publication_date(attrs.get("content", ""))
        if tag == "link" and "canonical" in attrs.get("rel", "").split():
            self.canonical = attrs.get("href", "")
        if tag == "time" and not self.published:
            self.published = parse_publication_date(attrs.get("datetime", ""))
        if tag == "script" and "ld+json" in attrs.get("type", ""):
            self.script = []
        publisher_host = self.publisher_host()
        classes = set(attrs.get("class", "").split())
        publisher_author_box = "m-a-box" in classes and publisher_host in {"rc24h.com.br", "www.rc24h.com.br"}
        diario_navigation = publisher_host in {"diariodorio.com", "www.diariodorio.com"} and bool(
            classes & {"ddr-author-box", "td-category", "td-post-sharing", "td-post-sharing-top", "td-a-rec"})
        odia_tags = publisher_host == "odia.ig.com.br" and tag == "div" and attrs.get("id") == "tags" and "tags" in classes
        publisher_recommendations = publisher_host in _GLOBO_ARTICLE_HOSTS and "you-need-to-know-theme" in classes
        related = bool(_RELATED.search(attrs.get("class", "") + " " + attrs.get("id", ""))) or publisher_author_box or publisher_recommendations or diario_navigation or odia_tags
        blocked = (bool(self.stack) and self.stack[-1][1]) or tag in {"script", "style", "nav", "aside", "footer", "header", "form"} or related
        body = tag == "article" or bool(_BODY.search(attrs.get("class", "") + " " + attrs.get("itemprop", "")))
        # Exact tokens from RC24h's public article templates. Its enclosing
        # <article> also contains unrelated current headlines and navigation.
        publisher_editorial = {"tdb_single_content", "td-post-content"}.issubset(attrs.get("class", "").split())
        # Diário's migrated template puts tags and its author card inside this
        # editorial container; retain every paragraph while excluding those DOM
        # widgets above. Repeated prose inside the actual content is preserved.
        publisher_editorial = publisher_editorial or (
            publisher_host in {"diariodorio.com", "www.diariodorio.com"}
            and {"td-post-content", "tagdiv-type"}.issubset(classes))
        scope = self.stack[-1][4] if self.stack else 0
        if body and not blocked and not scope:
            self.body_scope += 1
            scope = self.body_scope
        if related and scope:
            self.cleaned_scopes.add(scope)
        if tag == "ul" and "content-unordered-list" in classes and publisher_host in _GLOBO_ARTICLE_HOSTS and not blocked:
            probe = _GloboArticleLinkList(self.document_url or self.canonical)
            probe.handle_starttag(tag, attrs.items())
            self.globo_link_lists.append((len(self.stack), len(self.parts), probe))
        if tag not in _VOID_TAGS:
            self.stack.append((tag, blocked, len(self.parts), body, scope, publisher_editorial, attrs))
        if tag in {"p", "div", "br", "li", "h1", "h2", "h3"} and not blocked:
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for _, _, probe in self.globo_link_lists:
            probe.handle_endtag(tag)
        if tag == "script" and self.script is not None:
            self.json_ld.append("".join(self.script))
            self.script = None
        for index in range(len(self.stack) - 1, -1, -1):
            current, blocked, start, body, scope, publisher_editorial, attrs = self.stack[index]
            if current != tag:
                continue
            globo_related_list = tag == "ul" and any(
                depth == index and probe.is_related() for depth, _, probe in self.globo_link_lists)
            odia_prefix_start = None
            if tag == "a" and index and self.stack[index - 1][0] == "div" and "texto" in self.stack[index - 1][6].get("class", "").split():
                publisher_host = self.publisher_host()
                prefix_start = self.stack[index - 1][2]
                if publisher_host == "odia.ig.com.br" and re.fullmatch(r"\s*LEIA MAIS\s*:\s*", "".join(self.parts[prefix_start:start]), re.I):
                    odia_prefix_start = prefix_start
            if odia_prefix_start is not None:
                # O Dia may put genuine later paragraphs in this same div.
                # Remove only its explicit lead-in and immediate anchor.
                del self.parts[odia_prefix_start:]
                if scope:
                    self.cleaned_scopes.add(scope)
            elif globo_related_list or tag in {"p", "a"} and re.match(r"\s*(?:leia (?:tamb[eé]m|mais)|veja (?:tamb[eé]m|mais)|saiba mais|confira tamb[eé]m)\s*:", "".join(self.parts[start:]), re.I):
                del self.parts[start:]
                if scope:
                    self.cleaned_scopes.add(scope)
            elif body and not blocked:
                text = "".join(self.parts[start:])
                self.blocks.append(text)
                self.scoped_blocks.append((scope, text))
                if publisher_editorial:
                    self.publisher_editorial_blocks.append((scope, text))
            del self.stack[index:]
            self.globo_link_lists = [row for row in self.globo_link_lists if row[0] < index]
            break

    def handle_data(self, data):
        for _, _, probe in self.globo_link_lists:
            probe.handle_data(data)
        if self.script is not None:
            self.script.append(data)
        if any(row[0] == "title" for row in self.stack):
            self.head_title.append(data)
        if self.stack and not self.stack[-1][1]:
            self.parts.append(data)


def extract_article(raw_html: str) -> dict[str, str]:
    parser = _ArticleParser()
    parser.feed(raw_html or "")
    structured_bodies = []
    for raw in parser.json_ld:
        try:
            payload = json.loads(raw)
        except (ValueError, TypeError):
            continue
        queue = payload if isinstance(payload, list) else [payload]
        for item in queue:
            if not isinstance(item, dict):
                continue
            queue.extend(item.get("@graph") or [])
            kinds = item.get("@type") or []
            if isinstance(kinds, str):
                kinds = [kinds]
            if not set(kinds) & {"NewsArticle", "Article", "ReportageNewsArticle", "BlogPosting"}:
                continue
            identity = item.get("url") or item.get("mainEntityOfPage") or item.get("@id") or ""
            if isinstance(identity, dict):
                identity = identity.get("@id") or identity.get("url") or ""
            document_identity = parser.document_url or parser.canonical
            if isinstance(identity, str) and identity.startswith(("http://", "https://")) and document_identity:
                if canonicalize_url(identity.split("#", 1)[0]).rstrip("/") != canonicalize_url(document_identity).rstrip("/"):
                    continue
            parser.title = parser.title or str(item.get("headline") or "")
            parser.published = parser.published or parse_publication_date(item.get("datePublished") or "")
            if item.get("articleBody"):
                structured_bodies.append(str(item["articleBody"]))
    # Infinite-scroll feeds can embed whole, longer stories after the requested
    # article. Only compare nested containers within the first article/body root.
    # A short primary/paywall body must never be replaced by an unrelated story.
    publisher_host = parser.publisher_host()
    primary_candidates = {scope for scope, block in parser.scoped_blocks if block.strip()}
    if publisher_host in _GLOBO_ARTICLE_HOSTS | {"odia.ig.com.br", "diariodorio.com", "www.diariodorio.com"}:
        # Removing the only related cards can leave an empty primary body.
        # That absence must not select a later story or polluted JSON-LD.
        primary_candidates.update(parser.cleaned_scopes)
    primary_scope = min(primary_candidates, default=0)
    primary_blocks = [block for scope, block in parser.scoped_blocks if scope == primary_scope]
    def normalized(block):
        return re.sub(r'[ \t\r\f\v]+', ' ', html.unescape(block)).strip()
    dom_blocks = [normalized(block) for block in primary_blocks]
    dom_body = max(dom_blocks, key=len) if dom_blocks else ""
    exact_editorial = [normalized(block) for scope, block in parser.publisher_editorial_blocks
                       if scope == primary_scope] if publisher_host in {
                           "rc24h.com.br", "www.rc24h.com.br", "diariodorio.com", "www.diariodorio.com"} else []
    if exact_editorial:
        # Keep the entire editorial container, including later Boca Miúda
        # sections. Never substitute a longer outer article/JSON-LD footer for
        # a short or unavailable primary body, and never cut on prose phrases.
        body = max(exact_editorial, key=len)
    elif primary_scope in parser.cleaned_scopes and (
        len(dom_body.split()) >= 40 or publisher_host in _GLOBO_ARTICLE_HOSTS | {"odia.ig.com.br"}
    ):
        # Some publishers flatten related cards into articleBody. Once their
        # bounded DOM containers were removed, do not reintroduce that content
        # merely because the structured string is longer.
        body = dom_body
    else:
        blocks = dom_blocks + [normalized(block) for block in structured_bodies]
        body = max(blocks, key=len) if blocks else ""
    # Without an article container or structured article body the extraction is
    # unconfirmed. Menu/search/paywall text must not become a full article.
    return {"full_text": body, "title": parser.title or "".join(parser.head_title).strip(),
            "published_at": parser.published, "canonical_url": parser.canonical,
            "extraction_state": "full_text" if len(body.split()) >= 40 else "metadata_only"}


def is_google_intermediary(url: str) -> bool:
    """Google landing, consent and challenge pages are never publisher articles."""
    host = (urlparse(url).hostname or "").lower().rstrip(".")
    return any(host == domain or host.endswith("." + domain) for domain in ("google.com", "google.com.br"))


def resolve_google_redirect(url: str, fetch: Callable, *, initial_response=None) -> str:
    """Resolve using the injected limiter for GET and the existing Google RPC."""
    if urlparse(url).hostname != "news.google.com":
        return url
    direct = (parse_qs(urlparse(url).query).get("url") or [""])[0]
    if direct.startswith(("https://", "http://")):
        return "" if is_google_intermediary(direct) else canonicalize_url(direct)
    # The fetch worker already retrieved this landing page. Reusing it avoids a
    # second Google request and keeps the one-request-per-second budget useful.
    response = initial_response if initial_response is not None else _get(fetch, url)
    if urlparse(response.url).hostname != "news.google.com":
        return "" if is_google_intermediary(response.url) else canonicalize_url(response.url)
    token_match = re.search(r'/(?:rss/)?(?:articles|read)/([^/?#]+)', response.url)
    signature = re.search(r'data-n-a-sg=["\']([^"\']+)', response.text)
    timestamp = re.search(r'data-n-a-ts=["\'](\d+)', response.text)
    if not (token_match and signature and timestamp):
        return ""
    inner = ["garturlreq", [["en-US", "US", ["FINANCE_TOP_INDICES", "WEB_TEST_1_0_0"], None, None, 1, 1, "US:en", None, 1, None, None, None, None, None, 0, 1], "en-US", "US", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0], token_match.group(1), int(timestamp.group(1)), signature.group(1)]
    outer = [[["Fbv4je", json.dumps(inner)]]]
    response = _get(fetch, "https://news.google.com/_/DotsSplashUi/data/batchexecute", method="POST",
                    data={"f.req": json.dumps(outer)}, headers={"Referer": "https://news.google.com/"})
    try:
        rows = json.loads(response.text.split("\n\n", 1)[1])
        for row in rows:
            if isinstance(row, list) and len(row) >= 3 and row[0] == "wrb.fr" and row[2]:
                decoded = json.loads(row[2])
                if isinstance(decoded, list) and len(decoded) >= 2 and decoded[0] == "garturlres":
                    resolved = str(decoded[1] or "")
                    if resolved.startswith(("https://", "http://")) and not is_google_intermediary(resolved):
                        return canonicalize_url(resolved)
    except (ValueError, TypeError, IndexError):
        pass
    return ""
