"""Bounded, checkpointable discovery for political clipping.

Discovery never decides whether a person is relevant: it emits section/archive
candidates before the durable fetch worker matches the actual article body.
Every network operation uses the caller's shared, rate-limited ``fetch``.
"""
from __future__ import annotations

import gzip
import html
import json
import re
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
        if source["key"] not in selected:
            continue
        base = {"source_key": source["key"], "date_from": date_from, "date_to": date_to,
                "target_ids": target_ids, "cursor": {}}
        for strategy in source["strategies"]:
            if strategy == "google_news":
                queries: dict[str, list[str]] = {}
                for row, target_id in zip(target_snapshots, target_ids):
                    for query in _target_queries(row):
                        if source.get("domain"):
                            query += " site:" + source["domain"]
                        queries.setdefault(query, []).append(target_id)
                for query, ids in queries.items():
                    for start, stop in windows:
                        tasks.append({**base, "strategy": strategy, "query": query,
                                      "date_from": start, "date_to": stop, "target_ids": ids})
            elif strategy == "daily_sitemap":
                for start, _ in date_windows(date_from, date_to, 1):
                    tasks.append({**base, "strategy": strategy, "day": start, "cursor": {"page": 1}})
            elif strategy == "sitemap":
                for url in source.get("sitemap_urls", []):
                    tasks.append({**base, "strategy": strategy, "url": url, "depth": 0, "ancestors": []})
            elif strategy == "wordpress":
                for start, stop in windows:
                    tasks.append({**base, "strategy": strategy, "date_from": start, "date_to": stop,
                                  "cursor": {"page": 1}})
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
        for node in entries[offset:offset + MAX_INDEX_CHILDREN]:
            child_url = _child_text(node, "loc")
            if child_url in ancestors:
                unsafe += 1
            elif not _allowed_url(child_url, source):
                unsafe += 1
            elif child_url:
                partition_status = ""
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
    for node in entries[offset:offset + MAX_CANDIDATES]:
        url = _child_text(node, "loc")
        if not _allowed_url(url, source, article=True):
            continue
        # lastmod is a modification date, never an article publication date.
        published = _child_text(node, "publication_date")
        if not in_window(published, task["date_from"], task["date_to"]):
            continue
        candidates.append(_candidate(source, url, _child_text(node, "title"), published,
                                     metadata={"sitemap_url": sitemap_url,
                                               "discovery_day": task.get("day", ""), "needs_date_review": not bool(published)}))
    next_cursor = None
    if offset + MAX_CANDIDATES < len(entries):
        next_cursor = {**cursor, "offset": offset + MAX_CANDIDATES}
    elif task["strategy"] == "daily_sitemap" and entries:
        if page >= int(source.get("max_pages") or MAX_PAGES):
            return _result(candidates, outcome="gap", raw_count=len(entries), gap_reason="sitemap_page_cap")
        next_cursor = {"page": page + 1}
    return _result(candidates, next_cursor=next_cursor, raw_count=len(entries[offset:offset + MAX_CANDIDATES]))


def _wordpress(task, source, fetch):
    page = max(1, int((task.get("cursor") or {}).get("page") or 1))
    params = {"page": page, "per_page": 100, "orderby": "date", "order": "desc",
              "after": task["date_from"] + "T00:00:00", "before": (date.fromisoformat(task["date_to"]) + timedelta(days=1)).isoformat() + "T00:00:00",
              "_fields": "id,link,title,excerpt,date,date_gmt"}
    # No title/name search: date scans discover people mentioned only in bodies.
    response = _get(fetch, source["base_url"].rstrip("/") + "/wp-json/wp/v2/posts?" + urlencode(params), allowed_statuses=(400,))
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
    for row in payload:
        if not isinstance(row, dict) or not _allowed_url(str(row.get("link") or ""), source, article=True):
            continue
        raw_date = row.get("date_gmt") or row.get("date") or ""
        published = parse_publication_date(raw_date, naive_zone=timezone.utc if row.get("date_gmt") else SAO_PAULO)
        if not in_window(published, task["date_from"], task["date_to"]):
            continue
        rendered = lambda value: (value or {}).get("rendered", "") if isinstance(value, dict) else str(value or "")
        candidates.append(_candidate(source, row["link"], rendered(row.get("title")), published,
                                     rendered(row.get("excerpt")), {"wordpress_id": row.get("id"), "collection_mode": "date_scan"}))
    total_pages_raw = response.headers.get("X-WP-TotalPages") or response.headers.get("x-wp-totalpages")
    try:
        total_pages = int(total_pages_raw) if total_pages_raw is not None else None
    except (ValueError, TypeError) as exc:
        raise DiscoveryError("invalid WordPress page count") from exc
    has_next = page < total_pages if total_pages is not None else len(payload) >= 100
    if has_next and page >= MAX_PAGES:
        return _result(candidates, outcome="gap", raw_count=len(payload), gap_reason="wordpress_page_cap")
    return _result(candidates, next_cursor={"page": page + 1} if has_next else None, raw_count=len(payload))


def _archive(task, source, fetch):
    cursor = dict(task.get("cursor") or {})
    page = max(1, int(cursor.get("page") or 1))
    url = cursor.get("url") or task["url"]
    if not _allowed_url(url, source):
        raise DiscoveryError("archive URL outside source domain", retryable=False)
    response = _get(fetch, url)
    raw_html = response.text
    candidates = []
    if task["strategy"] == "camara_archive":
        rows = CAMARA_ARCHIVE_ITEM_RE.findall(raw_html)
        for raw_date, href, title in rows:
            item_url = urljoin(url, html.unescape(href))
            published = _parse_pt_br_datetime(raw_date)
            if _allowed_url(item_url, source, article=True) and in_window(published, task["date_from"], task["date_to"]):
                candidates.append(_candidate(source, item_url, title, published))
        match = CAMARA_NEXT_RE.search(raw_html)
        next_url = urljoin(url, html.unescape(match.group(1))) if match else ""
    else:
        config = {"host": source["domain"], "source_name": source["name"], "article_path_prefix": "/"}
        rows, next_url = _extract_vejario_archive_page(raw_html, url, config)
        candidates = [_candidate(source, row.url, row.title, row.published_at, row.snippet)
                      for row in rows if in_window(row.published_at, task["date_from"], task["date_to"])]
    if not rows and not next_url and not re.search(r'nenhum|sem resultados|no results', raw_html, re.I):
        raise DiscoveryError("archive markup not recognized; exhaustion unconfirmed")
    if next_url and (next_url == url or page >= MAX_PAGES):
        return _result(candidates, outcome="gap", raw_count=len(rows), gap_reason="archive_page_cap_or_cycle")
    return _result(candidates, next_cursor={"page": page + 1, "url": next_url} if next_url else None, raw_count=len(rows))


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
    if strategy in {"camara_archive", "vejario_archive"}:
        return _archive(task, source, fetch)
    raise DiscoveryError("unknown discovery strategy", retryable=False)


_VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
_RELATED = re.compile(r'(?:related|relacionad|recommend|recomendad|leia[-_ ]?mais|read[-_ ]?more|sidebar|newsletter|comments|comentarios|social-share|outbrain|taboola)', re.I)
_BODY = re.compile(r'(?:entry-content|post-content|article-content|materia-content|content-body|article-body|articleBody|mc-article-body|story-body)', re.I)


class _ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.parts = []
        self.blocks = []
        self.title = ""
        self.published = ""
        self.canonical = ""
        self.json_ld = []
        self.script = None
        self.head_title = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            key = attrs.get("property") or attrs.get("name")
            if key in {"og:title", "twitter:title"} and not self.title:
                self.title = attrs.get("content", "")
            if key in {"article:published_time", "pubdate", "datePublished"} and not self.published:
                self.published = parse_publication_date(attrs.get("content", ""))
        if tag == "link" and "canonical" in attrs.get("rel", "").split():
            self.canonical = attrs.get("href", "")
        if tag == "time" and not self.published:
            self.published = parse_publication_date(attrs.get("datetime", ""))
        if tag == "script" and "ld+json" in attrs.get("type", ""):
            self.script = []
        blocked = (bool(self.stack) and self.stack[-1][1]) or tag in {"script", "style", "nav", "aside", "footer", "header", "form"} or bool(_RELATED.search(attrs.get("class", "") + " " + attrs.get("id", "")))
        body = tag == "article" or bool(_BODY.search(attrs.get("class", "") + " " + attrs.get("itemprop", "")))
        if tag not in _VOID_TAGS:
            self.stack.append((tag, blocked, len(self.parts), body))
        if tag in {"p", "div", "br", "li", "h1", "h2", "h3"} and not blocked:
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "script" and self.script is not None:
            self.json_ld.append("".join(self.script))
            self.script = None
        for index in range(len(self.stack) - 1, -1, -1):
            current, blocked, start, body = self.stack[index]
            if current != tag:
                continue
            if tag == "p" and re.match(r"\s*(?:leia (?:tamb[eé]m|mais)|veja (?:tamb[eé]m|mais)|saiba mais|confira tamb[eé]m)\s*:", "".join(self.parts[start:]), re.I):
                del self.parts[start:]
            elif body and not blocked:
                self.blocks.append("".join(self.parts[start:]))
            del self.stack[index:]
            break

    def handle_data(self, data):
        if self.script is not None:
            self.script.append(data)
        if any(row[0] == "title" for row in self.stack):
            self.head_title.append(data)
        if self.stack and not self.stack[-1][1]:
            self.parts.append(data)


def extract_article(raw_html: str) -> dict[str, str]:
    parser = _ArticleParser()
    parser.feed(raw_html or "")
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
            parser.title = parser.title or str(item.get("headline") or "")
            parser.published = parser.published or parse_publication_date(item.get("datePublished") or "")
            if item.get("articleBody"):
                parser.blocks.append(str(item["articleBody"]))
    blocks = [re.sub(r'[ \t\r\f\v]+', ' ', block).strip() for block in parser.blocks]
    body = max(blocks, key=len) if blocks else ""
    # Without an article container or structured article body the extraction is
    # unconfirmed. Menu/search/paywall text must not become a full article.
    return {"full_text": body, "title": parser.title or "".join(parser.head_title).strip(),
            "published_at": parser.published, "canonical_url": parser.canonical,
            "extraction_state": "full_text" if len(body.split()) >= 40 else "metadata_only"}


def resolve_google_redirect(url: str, fetch: Callable) -> str:
    """Resolve using the injected limiter for GET and the existing Google RPC."""
    if urlparse(url).hostname != "news.google.com":
        return url
    direct = (parse_qs(urlparse(url).query).get("url") or [""])[0]
    if direct.startswith(("https://", "http://")):
        return canonicalize_url(direct)
    response = _get(fetch, url)
    if urlparse(response.url).hostname != "news.google.com":
        return canonicalize_url(response.url)
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
                    if resolved.startswith(("https://", "http://")):
                        return canonicalize_url(resolved)
    except (ValueError, TypeError, IndexError):
        pass
    return ""
