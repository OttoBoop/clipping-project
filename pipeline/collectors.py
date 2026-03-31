from __future__ import annotations

import html
import json
import logging
import random
import re
import time
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Iterable
from urllib.parse import parse_qsl, quote_plus, urlencode, urljoin, urlparse, urlsplit, urlunsplit

from .http_utils import (
    canonicalize_url,
    extract_html_title,
    extract_published_at,
    fetch_url,
    html_to_article_text,
    html_to_text,
    is_likely_article_url,
    post_json,
    try_resolve_google_redirect,
)
from .normalization import normalize_text
from .settings import (
    CAMARA_ARCHIVE_TARGET,
    DIRECT_SCRAPE_TARGETS,
    FLAVIO_INTERNAL_SEARCH_QUERIES,
    FLAVIO_INTERNAL_SEARCH_TARGETS,
    GOOGLE_NEWS_QUERIES,
    InternalSearchTarget,
    RSS_FEEDS,
    SITEMAP_DAILY_SOURCES,
    VEJARIO_ARCHIVE_TARGETS,
    google_news_rss_url,
)


@dataclass(slots=True)
class CandidateArticle:
    title: str
    url: str
    source_name: str
    source_type: str
    published_at: str
    snippet: str
    metadata: dict


def _safe_text(node: ET.Element | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def _parse_datetime(text: str) -> str:
    if not text:
        return datetime.now(timezone.utc).isoformat()
    # RSS pubDate common format.
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    # ISO fallback.
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def _parse_window_boundary(value: str, *, end_of_day: bool) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        if len(raw) == 10:
            dt = datetime.strptime(raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if end_of_day:
                dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            return dt
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _within_window(value: str, *, date_from: str = "", date_to: str = "") -> bool:
    start = _parse_window_boundary(date_from, end_of_day=False)
    end = _parse_window_boundary(date_to, end_of_day=True)
    if not start and not end:
        return True
    try:
        dt = datetime.fromisoformat((value or "").replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
    except Exception:
        return True
    if start and dt < start:
        return False
    if end and dt > end:
        return False
    return True


def parse_rss_or_atom(xml_text: str, source_name: str, source_type: str, metadata: dict | None = None) -> list[CandidateArticle]:
    metadata = metadata or {}
    results: list[CandidateArticle] = []
    root = ET.fromstring(xml_text)

    # RSS 2.0 path.
    for item in root.findall(".//item"):
        title = _safe_text(item.find("title"))
        link = _safe_text(item.find("link"))
        summary = _safe_text(item.find("description"))
        pub = _safe_text(item.find("pubDate"))
        if not link:
            continue
        results.append(
            CandidateArticle(
                title=title,
                url=link,
                source_name=source_name,
                source_type=source_type,
                published_at=_parse_datetime(pub),
                snippet=summary,
                metadata=metadata,
            )
        )

    # Atom path.
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//atom:entry", ns):
        title = _safe_text(entry.find("atom:title", ns))
        link_node = entry.find("atom:link", ns)
        link = link_node.attrib.get("href", "").strip() if link_node is not None else ""
        summary = _safe_text(entry.find("atom:summary", ns)) or _safe_text(entry.find("atom:content", ns))
        pub = _safe_text(entry.find("atom:updated", ns)) or _safe_text(entry.find("atom:published", ns))
        if not link:
            continue
        results.append(
            CandidateArticle(
                title=title,
                url=link,
                source_name=source_name,
                source_type=source_type,
                published_at=_parse_datetime(pub),
                snippet=summary,
                metadata=metadata,
            )
        )
    return results


HREF_ATTR_RE = re.compile(r"""href=["']([^"'#]+)["']""", re.IGNORECASE)


def _extract_hrefs(value: str) -> list[str]:
    if not value:
        return []
    return [m.group(1).strip() for m in HREF_ATTR_RE.finditer(value) if m.group(1).strip()]


def _round_robin_candidates(batches: list[list[CandidateArticle]]) -> list[CandidateArticle]:
    merged: list[CandidateArticle] = []
    indexes = [0 for _ in batches]
    while True:
        progressed = False
        for idx, batch in enumerate(batches):
            pos = indexes[idx]
            if pos >= len(batch):
                continue
            merged.append(batch[pos])
            indexes[idx] += 1
            progressed = True
        if not progressed:
            break
    return merged


def _dedupe_candidates_by_url(candidates: list[CandidateArticle]) -> list[CandidateArticle]:
    deduped: list[CandidateArticle] = []
    seen_urls: set[str] = set()
    for item in candidates:
        canon = canonicalize_url(item.url)
        if not canon or canon in seen_urls:
            continue
        item.url = canon
        seen_urls.add(canon)
        deduped.append(item)
    return deduped


def collect_rss(
    limit_per_feed: int = 30,
    request_timeout: int = 10,
    *,
    date_from: str = "",
    date_to: str = "",
) -> list[CandidateArticle]:
    articles: list[CandidateArticle] = []
    for feed in RSS_FEEDS:
        try:
            _, xml_text = fetch_url(feed["url"], timeout=request_timeout)
            items = parse_rss_or_atom(
                xml_text,
                source_name=feed["source_name"],
                source_type="rss",
                metadata={"feed_url": feed["url"]},
            )
            filtered = [item for item in items if _within_window(item.published_at, date_from=date_from, date_to=date_to)]
            articles.extend(filtered[: max(1, limit_per_feed)])
        except Exception:
            continue
    return articles


def collect_google_news(
    queries: list[str] | None = None,
    *,
    date_from: str = "",
    date_to: str = "",
    limit_per_query: int = 30,
    request_timeout: int = 10,
    resolve_timeout: int = 6,
) -> list[CandidateArticle]:
    query_batches: list[list[CandidateArticle]] = []
    query_list = queries or GOOGLE_NEWS_QUERIES
    for query in query_list:
        q = query.strip()
        if date_from:
            q += f" after:{date_from}"
        if date_to:
            q += f" before:{date_to}"
        url = google_news_rss_url(q)
        try:
            _, xml_text = fetch_url(url, timeout=request_timeout)
            items = parse_rss_or_atom(
                xml_text,
                source_name="Google News",
                source_type="google_news",
                metadata={"query": q},
            )
            for item in items:
                # Prefer direct outlet links when present in snippet.
                links = _extract_hrefs(item.snippet)
                direct_link = ""
                for link in links:
                    host = (urlparse(link).netloc or "").lower()
                    if host and "news.google.com" not in host:
                        direct_link = link
                        break
                item.url = canonicalize_url(direct_link or item.url)
            filtered = [item for item in items if _within_window(item.published_at, date_from=date_from, date_to=date_to)]
            query_batches.append(filtered[: max(1, limit_per_query)])
        except Exception:
            continue
    return _dedupe_candidates_by_url(_round_robin_candidates(query_batches))


LINK_RE = re.compile(r"""<a[^>]+href=["']([^"'#]+)["'][^>]*>(.*?)</a>""", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"(?is)<[^>]+>")
WS_RE = re.compile(r"\s+")
A_TAG_RE = re.compile(r"""(?is)<a\b([^>]*?)href=["']([^"'#]+)["']([^>]*)>(.*?)</a>""")
DIV_CARD_RE = re.compile(r'(?is)<div id="post-\d+" class="[^"]*\blist-item\b[^"]*">(.*?)</div>\s*</div>\s*</div>')
VEJARIO_DATE_RE = re.compile(r'(?is)<span class="date-post">\s*(.*?)\s*</span>')
CAMARA_RESULT_RE = re.compile(
    r'(?is)<dt class="result-title">.*?<a href="([^"]+)">\s*(.*?)\s*</a>.*?</dt>'
    r'.*?<dd class="result-category">.*?</dd>'
    r'.*?<dd class="result-text">\s*(.*?)\s*</dd>'
    r'.*?<dd class="result-created">\s*(.*?)\s*</dd>'
)
CONIB_ARTICLE_RE = re.compile(r'(?is)<article class="uk-article">(.*?)</article>')
CONIB_NEXT_RE = re.compile(r'(?is)<a class="next" href="([^"]+)"')
CAMARA_NEXT_RE = re.compile(r'(?is)<link rel="next" href="([^"]+)"')
CAMARA_ARCHIVE_ITEM_RE = re.compile(
    r'(?is)catItemDateCreated[^>]*>\s*(.*?)\s*</span>.*?'
    r'<h3 class="catItemTitle">.*?<a href="([^"]+)">\s*(.*?)\s*</a>'
)
VEJARIO_INFINITY_RE = re.compile(
    r'(?is)infiniteScroll\s*=\s*\{"settings":\{.*?"path":"([^"]+)".*?(?:"parameters":"([^"]*)")?'
)
PT_MONTHS = {
    "jan": 1,
    "janeiro": 1,
    "fev": 2,
    "fevereiro": 2,
    "mar": 3,
    "marco": 3,
    "março": 3,
    "abr": 4,
    "abril": 4,
    "mai": 5,
    "maio": 5,
    "jun": 6,
    "junho": 6,
    "jul": 7,
    "julho": 7,
    "ago": 8,
    "agosto": 8,
    "set": 9,
    "setembro": 9,
    "out": 10,
    "outubro": 10,
    "nov": 11,
    "novembro": 11,
    "dez": 12,
    "dezembro": 12,
}


def _clean_html_fragment(value: str) -> str:
    text = html.unescape(TAG_RE.sub(" ", value or ""))
    return WS_RE.sub(" ", text).strip()


def _host_matches(host: str, expected: str) -> bool:
    left = (host or "").lower().lstrip(".")
    right = (expected or "").lower().lstrip(".")
    return left == right or left.endswith(f".{right}")


def _parse_pt_br_datetime(value: str) -> str:
    text = _clean_html_fragment(value).lower()
    if not text:
        return ""
    text = text.replace("atualizado em", " ").replace("criado em", " ")
    text = text.replace("às", " ").replace(" as ", " ").replace("•", " ")
    text = text.replace("º", "").replace("ª", "")
    text = WS_RE.sub(" ", text).strip()
    match = re.search(r"(\d{1,2})\s+([a-zç]+)\s+(\d{4})(?:,\s*(\d{1,2})h(\d{2}))?", text)
    if not match:
        return ""
    day = int(match.group(1))
    month = PT_MONTHS.get(match.group(2), 0)
    year = int(match.group(3))
    hour = int(match.group(4) or 12)
    minute = int(match.group(5) or 0)
    if not month:
        return ""
    try:
        dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    except Exception:
        return ""
    return dt.isoformat()


def _anchor_records(value: str) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    for before_attrs, href, after_attrs, inner in A_TAG_RE.findall(value or ""):
        title = _clean_html_fragment(inner)
        attrs = f"{before_attrs} {after_attrs}".strip()
        rows.append((title, href.strip(), attrs, inner))
    return rows


def _generic_next_page_url(html_page: str, current_url: str, expected_host: str) -> str:
    for title, href, attrs, _ in _anchor_records(html_page):
        text = title.lower()
        attrs_lower = attrs.lower()
        if "rel=\"next\"" not in attrs_lower and "rel='next'" not in attrs_lower:
            if "prÃ³ximo" not in text and "proximo" not in text and "next" not in text and 'title="prÃ³ximo"' not in attrs_lower:
                continue
        resolved = canonicalize_url(urljoin(current_url, href))
        parsed = urlparse(resolved)
        if not _host_matches(parsed.netloc, expected_host):
            continue
        return resolved
    return ""


def _build_internal_search_candidate(
    *,
    title: str,
    url: str,
    source_name: str,
    published_at: str,
    snippet: str,
    metadata: dict,
) -> CandidateArticle:
    return CandidateArticle(
        title=_clean_html_fragment(title),
        url=canonicalize_url(url),
        source_name=source_name,
        source_type="internal_search",
        published_at=published_at,
        snippet=_clean_html_fragment(snippet),
        metadata=metadata,
    )


def _extract_vejario_results(html_page: str, search_url: str, source_name: str) -> tuple[list[CandidateArticle], str]:
    candidates: list[CandidateArticle] = []
    seen_urls: set[str] = set()
    for block in DIV_CARD_RE.findall(html_page or ""):
        links = _anchor_records(block)
        if not links:
            continue
        title = ""
        url = ""
        for link_title, link_href, _, _ in links:
            resolved = canonicalize_url(urljoin(search_url, link_href))
            if not is_likely_article_url(resolved, expected_host_fragment="vejario.abril.com.br"):
                continue
            if not url:
                url = resolved
            if link_title:
                title = link_title
                url = resolved
                break
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        desc_match = re.search(r'(?is)<span class="description">\s*(.*?)\s*</span>', block)
        date_match = VEJARIO_DATE_RE.search(block)
        candidates.append(
            _build_internal_search_candidate(
                title=title,
                url=url,
                source_name=source_name,
                published_at=_parse_pt_br_datetime(date_match.group(1) if date_match else ""),
                snippet=desc_match.group(1) if desc_match else "",
                metadata={"search_url": search_url, "internal_search_host": "vejario.abril.com.br"},
            )
        )
    next_url = ""
    history_match = re.search(
        r'"history":\{"host":"vejario\.abril\.com\.br","path":"([^"]+)".*?"parameters":"([^"]+)"',
        html_page or "",
        re.DOTALL,
    )
    current_page = 1
    current_match = re.search(r"/busca/pagina/(\d+)/", search_url)
    if current_match:
        current_page = int(current_match.group(1))
    if history_match:
        path_template = history_match.group(1).replace("\\/", "/")
        parameters = history_match.group(2).replace("\\/", "/")
        next_page = current_page + 1
        next_path = path_template.replace("%d", str(next_page))
        next_url = canonicalize_url(urljoin(search_url, f"{next_path}{parameters}"))
    return candidates, next_url


def _extract_camara_results(html_page: str, search_url: str, source_name: str) -> tuple[list[CandidateArticle], str]:
    candidates: list[CandidateArticle] = []
    seen_urls: set[str] = set()
    for href, title, snippet, created in CAMARA_RESULT_RE.findall(html_page or ""):
        resolved = canonicalize_url(urljoin(search_url, href))
        if not is_likely_article_url(resolved, expected_host_fragment="camara.rio"):
            continue
        if resolved in seen_urls:
            continue
        seen_urls.add(resolved)
        candidates.append(
            _build_internal_search_candidate(
                title=title,
                url=resolved,
                source_name=source_name,
                published_at=_parse_pt_br_datetime(created),
                snippet=snippet,
                metadata={"search_url": search_url, "internal_search_host": "camara.rio"},
            )
        )
    next_match = CAMARA_NEXT_RE.search(html_page or "")
    next_url = canonicalize_url(urljoin(search_url, next_match.group(1))) if next_match else ""
    return candidates, next_url


def _extract_conib_results(html_page: str, search_url: str, source_name: str) -> tuple[list[CandidateArticle], str]:
    candidates: list[CandidateArticle] = []
    seen_urls: set[str] = set()
    for block in CONIB_ARTICLE_RE.findall(html_page or ""):
        links = _anchor_records(block)
        if not links:
            continue
        title, href, _, _ = links[0]
        resolved = canonicalize_url(urljoin(search_url, href))
        if not is_likely_article_url(resolved, expected_host_fragment="conib.org.br"):
            continue
        if resolved in seen_urls:
            continue
        seen_urls.add(resolved)
        snippet = _clean_html_fragment(block)
        candidates.append(
            _build_internal_search_candidate(
                title=title,
                url=resolved,
                source_name=source_name,
                published_at="",
                snippet=snippet,
                metadata={"search_url": search_url, "internal_search_host": "conib.org.br"},
            )
        )
    next_match = CONIB_NEXT_RE.search(html_page or "")
    next_url = canonicalize_url(urljoin(search_url, next_match.group(1))) if next_match else ""
    return candidates, next_url


def _extract_internal_search_results(
    adapter: InternalSearchTarget,
    *,
    html_page: str,
    search_url: str,
) -> tuple[list[CandidateArticle], str]:
    if adapter.host == "vejario.abril.com.br":
        return _extract_vejario_results(html_page, search_url, adapter.source_name)
    if adapter.host == "camara.rio":
        return _extract_camara_results(html_page, search_url, adapter.source_name)
    if adapter.host == "www.conib.org.br":
        return _extract_conib_results(html_page, search_url, adapter.source_name)
    candidates: list[CandidateArticle] = []
    seen_urls: set[str] = set()
    for title, href in _extract_links_from_search(html_page, adapter.source_name):
        resolved = canonicalize_url(urljoin(search_url, href))
        if not is_likely_article_url(resolved, expected_host_fragment=adapter.host):
            continue
        if resolved in seen_urls:
            continue
        seen_urls.add(resolved)
        candidates.append(
            _build_internal_search_candidate(
                title=title,
                url=resolved,
                source_name=adapter.source_name,
                published_at="",
                snippet="",
                metadata={"search_url": search_url, "internal_search_host": adapter.host},
            )
        )
    return candidates, _generic_next_page_url(html_page, search_url, adapter.host)


def _globo_search_payload(adapter: InternalSearchTarget, query: str, *, offset: int) -> list[dict]:
    size = max(1, int(adapter.page_size or 10))
    payload = [
        {
            "search_profile": adapter.search_profile,
            "query": adapter.recency_query_id,
            "params": {"q": query, "from": offset, "size": size},
        }
    ]
    if offset == 0 and adapter.navigational_query_id:
        payload.extend(
            [
                {
                    "search_profile": adapter.navigational_profile or adapter.search_profile,
                    "query": adapter.navigational_query_id,
                    "params": {"q": query, "from": 0, "size": 1},
                },
                {
                    "search_profile": adapter.live_profile or adapter.search_profile,
                    "query": adapter.live_query_id,
                    "params": {"q": query, "from": 0, "size": 1},
                },
                {
                    "search_profile": adapter.search_profile,
                    "query": adapter.editorial_query_id or adapter.recency_query_id,
                    "params": {"q": query, "from": 0, "size": 1},
                },
            ]
        )
    return payload


def _collect_globo_internal_search(
    adapter: InternalSearchTarget,
    *,
    query: str,
    limit_per_adapter: int,
    request_timeout: int,
    date_from: str,
    date_to: str,
) -> list[CandidateArticle]:
    candidates: list[CandidateArticle] = []
    seen_urls: set[str] = set()
    start = _parse_window_boundary(date_from, end_of_day=False)
    offset = 0
    page_size = max(1, int(adapter.page_size or 10))
    while len(candidates) < max(1, limit_per_adapter):
        tenant_id = adapter.host.split(".")[0]  # oglobo.globo.com → oglobo, g1.globo.com → g1
        origin = f"https://{adapter.host}"
        _, body = post_json(
            "https://busca.globo.com/v1/search",
            _globo_search_payload(adapter, query, offset=offset),
            timeout=request_timeout,
            extra_headers={
                "X-Tenant-id": tenant_id,
                "Origin": origin,
                "Referer": f"{origin}/busca/?q={quote_plus(query)}",
            },
        )
        try:
            payload = json.loads(body)
        except Exception:
            break
        if not isinstance(payload, list) or not payload:
            break
        first = payload[0] if isinstance(payload[0], dict) else {}
        hits = (((first.get("result") or {}).get("hits") or {}).get("hits")) or []
        if not hits:
            break
        page_candidates: list[CandidateArticle] = []
        older_hits = 0
        dated_hits = 0
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            source = hit.get("_source") or {}
            url = canonicalize_url(str(source.get("url") or "").strip())
            if not url or url in seen_urls:
                continue
            raw_issued = str(source.get("issued") or "").strip()
            issued = _parse_datetime(raw_issued) if raw_issued else ""
            if issued:
                dated_hits += 1
                if start and datetime.fromisoformat(issued.replace("Z", "+00:00")).astimezone(timezone.utc) < start:
                    older_hits += 1
            page_candidates.append(
                _build_internal_search_candidate(
                    title=str(source.get("title") or ""),
                    url=url,
                    source_name=adapter.source_name,
                    published_at=issued,
                    snippet=str(source.get("description") or source.get("body") or "")[:500],
                    metadata={"query": query, "search_url": adapter.search_url_template, "internal_search_host": adapter.host},
                )
            )
            seen_urls.add(url)
        candidates.extend(page_candidates)
        if dated_hits and older_hits == dated_hits:
            break
        if len(hits) < page_size:
            break
        offset += page_size
    return [item for item in candidates if _within_window(item.published_at, date_from=date_from, date_to=date_to) or not item.published_at]


def _extract_links_from_search(html_page: str, base_source: str) -> Iterable[tuple[str, str]]:
    for href, raw_title in LINK_RE.findall(html_page):
        href = href.strip()
        if href.startswith("javascript:"):
            continue
        if href.startswith("mailto:"):
            continue
        title = html.unescape(TAG_RE.sub(" ", raw_title))
        title = WS_RE.sub(" ", title).strip()
        yield title, href


def collect_direct_scrape(main_query: str = "Flavio Valle", *, per_target_limit: int = 50, request_timeout: int = 10) -> list[CandidateArticle]:
    articles: list[CandidateArticle] = []
    for target in DIRECT_SCRAPE_TARGETS:
        try:
            search_url = target.search_url_template.format(query=quote_plus(main_query))
            expected_host = urlparse(search_url).netloc
            _, html_page = fetch_url(search_url, timeout=request_timeout)
            seen_urls: set[str] = set()
            accepted = 0
            for title, link in _extract_links_from_search(html_page, target.source_name):
                if link.startswith("/"):
                    link = urljoin(search_url, link)
                link = canonicalize_url(link)
                if link in seen_urls:
                    continue
                seen_urls.add(link)
                if not is_likely_article_url(link, expected_host_fragment=expected_host):
                    continue
                articles.append(
                    CandidateArticle(
                        title=title or "",
                        url=link,
                        source_name=target.source_name,
                        source_type="scrape",
                        published_at=datetime.now(timezone.utc).isoformat(),
                        snippet="",
                        metadata={"search_url": search_url},
                    )
                )
                accepted += 1
                if accepted >= max(1, per_target_limit):
                    break
        except Exception:
            continue
    return articles


def collect_wordpress_api(
    query: str,
    *,
    source_name: str,
    base_url: str,
    date_from: str = "",
    date_to: str = "",
    per_site_limit: int = 120,
    request_timeout: int = 10,
) -> list[CandidateArticle]:
    q = (query or "").strip()
    if not q:
        return []

    base = (base_url or "").strip().rstrip("/")
    if not base:
        return []

    endpoint = f"{base}/wp-json/wp/v2/posts"
    per_page = 100
    max_pages = max(3, min(60, (max(1, per_site_limit) // per_page) + 10))

    articles: list[CandidateArticle] = []
    seen_urls: set[str] = set()
    accepted = 0

    for page in range(1, max_pages + 1):
        if accepted >= max(1, per_site_limit):
            break
        params: dict[str, str] = {
            "search": q,
            "per_page": str(per_page),
            "page": str(page),
            "orderby": "date",
            "order": "desc",
            "_fields": "link,title,excerpt,date_gmt,date",
        }
        if date_from:
            params["after"] = f"{date_from}T00:00:00Z"
        if date_to:
            params["before"] = f"{date_to}T23:59:59Z"
        url = f"{endpoint}?{urlencode(params, doseq=True)}"

        try:
            _, body = fetch_url(url, timeout=request_timeout)
        except urllib.error.HTTPError:
            # Typically "invalid page number" once we go beyond available results.
            break
        except Exception:
            break

        try:
            payload = json.loads(body)
        except Exception:
            break
        if not isinstance(payload, list) or not payload:
            break

        for item in payload:
            if not isinstance(item, dict):
                continue
            link = str(item.get("link") or "").strip()
            if not link:
                continue
            canon = canonicalize_url(link)
            if canon in seen_urls:
                continue
            seen_urls.add(canon)

            title_obj = item.get("title") or {}
            if isinstance(title_obj, dict):
                rendered = str(title_obj.get("rendered") or "")
            else:
                rendered = str(title_obj or "")
            title = html.unescape(rendered)
            title = WS_RE.sub(" ", TAG_RE.sub(" ", title)).strip()

            excerpt_obj = item.get("excerpt") or {}
            if isinstance(excerpt_obj, dict):
                excerpt_rendered = str(excerpt_obj.get("rendered") or "")
            else:
                excerpt_rendered = str(excerpt_obj or "")
            excerpt = html.unescape(excerpt_rendered)
            excerpt = WS_RE.sub(" ", TAG_RE.sub(" ", excerpt)).strip()

            published_raw = str(item.get("date_gmt") or item.get("date") or "").strip()
            published_at = _parse_datetime(published_raw)

            articles.append(
                CandidateArticle(
                    title=title,
                    url=canon,
                    source_name=source_name or base,
                    source_type="wordpress_api",
                    published_at=published_at,
                    snippet=excerpt,
                    metadata={"query": q, "wp_base_url": base, "endpoint": endpoint},
                )
            )
            accepted += 1
            if accepted >= max(1, per_site_limit):
                break

        # Heuristic: when fewer than per_page are returned, we're at the end.
        if len(payload) < per_page:
            break

    return articles


def collect_internal_site_search(
    queries: list[str] | None = None,
    *,
    adapters: list[InternalSearchTarget] | None = None,
    date_from: str = "",
    date_to: str = "",
    limit_per_adapter: int = 60,
    max_pages_per_adapter: int = 6,
    request_timeout: int = 10,
) -> list[CandidateArticle]:
    query_list = [str(item or "").strip() for item in (queries or FLAVIO_INTERNAL_SEARCH_QUERIES) if str(item or "").strip()]
    adapter_list = adapters or FLAVIO_INTERNAL_SEARCH_TARGETS
    collected: list[CandidateArticle] = []
    global_seen_urls: set[str] = set()
    start = _parse_window_boundary(date_from, end_of_day=False)

    for adapter in adapter_list:
        adapter_candidates: list[CandidateArticle] = []
        adapter_seen_urls: set[str] = set()
        for query in query_list:
            if len(adapter_candidates) >= max(1, limit_per_adapter):
                break
            if adapter.mode == "globo_api":
                batch = _collect_globo_internal_search(
                    adapter,
                    query=query,
                    limit_per_adapter=max(1, limit_per_adapter) - len(adapter_candidates),
                    request_timeout=request_timeout,
                    date_from=date_from,
                    date_to=date_to,
                )
            else:
                batch = []
                next_url = adapter.search_url_template.format(query=quote_plus(query))
                pages_seen: set[str] = set()
                current_page = 0
                while next_url and current_page < max(1, max_pages_per_adapter):
                    page_url = _canonicalize_search_page_url(next_url)
                    if page_url in pages_seen:
                        break
                    pages_seen.add(page_url)
                    current_page += 1
                    try:
                        _, html_page = fetch_url(page_url, timeout=request_timeout)
                    except Exception:
                        break
                    page_candidates, discovered_next = _extract_internal_search_results(adapter, html_page=html_page, search_url=page_url)
                    older_hits = 0
                    dated_hits = 0
                    for item in page_candidates:
                        if item.published_at:
                            dated_hits += 1
                            parsed = _parse_window_boundary(item.published_at, end_of_day=False)
                            if start and parsed and parsed < start:
                                older_hits += 1
                        batch.append(item)
                        if len(adapter_candidates) + len(batch) >= max(1, limit_per_adapter):
                            break
                    if len(adapter_candidates) + len(batch) >= max(1, limit_per_adapter):
                        break
                    if dated_hits and older_hits == dated_hits:
                        break
                    next_url = discovered_next
            for item in batch:
                if item.url in adapter_seen_urls:
                    continue
                adapter_seen_urls.add(item.url)
                adapter_candidates.append(item)
                if len(adapter_candidates) >= max(1, limit_per_adapter):
                    break
        for item in adapter_candidates:
            if item.url in global_seen_urls:
                continue
            global_seen_urls.add(item.url)
            metadata = dict(item.metadata or {})
            metadata.update(
                {
                    "force_full_fetch": True,
                    "exact_body_only": False,
                    "require_published_extraction": not bool(item.published_at),
                }
            )
            item.metadata = metadata
            collected.append(item)
    return _dedupe_candidates_by_url(collected)


def iterate_google_playwright_day(
    query: str,
    day_str: str,
    start_index: int = 0,
    headed: bool = False,
) -> Iterable[tuple[list[CandidateArticle], int, bool]]:
    """
    Yields (articles_from_page, next_start_index, is_blocked)
    Uses Playwright to physically navigate and click "Next".
    """
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from camoufox.sync_api import Camoufox
    
    q = f'"{query}" -site:instagram.com -site:facebook.com -site:youtube.com -site:tiktok.com -site:twitter.com -site:linkedin.com'
    
    # Strictly format dates for Google url tbs params: cdr:1,cd_min:MM/DD/YYYY,cd_max:MM/DD/YYYY
    # Inline after:YYYY-MM-DD doesn't strictly cull in some regions
    try:
        from datetime import datetime
        dt = datetime.strptime(day_str, "%Y-%m-%d")
        tbs_date = f"{dt.month}/{dt.day}/{dt.year}"
        tbs_param = f"cdr:1,cd_min:{tbs_date},cd_max:{tbs_date}"
    except Exception:
        tbs_param = ""
    
    start_url = f"https://www.google.com/search?q={quote_plus(q)}"
    if tbs_param:
        start_url += f"&tbs={quote_plus(tbs_param)}"
    if start_index > 0:
        start_url += f"&start={start_index}"

    logging.info(f"Initializing Camoufox (headed={headed})...")
    with Camoufox(headless=not headed, humanize=True) as browser:
        logging.info("Camoufox initialized successfully. Creating page...")
        page = browser.new_page()
        
        current_index = start_index
        
        try:
            page.goto(start_url, wait_until="domcontentloaded", timeout=60000)
            
            while True:
                # 1. Check for Captcha / Block
                if page.locator('form[action="/sorry/index"]').count() > 0 or "sorry/index" in page.url:
                    if headed:
                        logging.warning(f"CAPTCHA detected at index {current_index}! Please solve it in the browser window.")
                        try:
                            # Save screenshot for monitoring
                            import os
                            os.makedirs("data/screenshots", exist_ok=True)
                            screenshot_path = f"data/screenshots/captcha_{day_str}_{current_index}.png"
                            page.screenshot(path=screenshot_path)
                            logging.info(f"Saved CAPTCHA screenshot to {screenshot_path}")
                        except Exception as e:
                            logging.warning(f"Failed to capture screenshot: {e}")

                        # Active polling loop (max 5 minutes)
                        resolved = False
                        for _ in range(60):
                            try:
                                if "sorry/index" not in page.url and page.locator('form[action="/sorry/index"]').count() == 0:
                                    if page.locator("div#search").count() > 0:
                                        logging.info("CAPTCHA solved! Resuming extraction...")
                                        resolved = True
                                        break
                            except Exception:
                                pass
                            time.sleep(5)

                        if not resolved:
                            logging.warning("CAPTCHA not solved in time or connection broken. Stopping.")
                            yield [], current_index, True
                            break
                    else:
                        logging.warning(f"CAPTCHA detected on Google at index {current_index}.")
                        yield [], current_index, True
                        break
                    
                # 2. Extract organic results
                # Google organic results typically reside in div.g
                # Or we can just extract all links and filter by google.
                try:
                    page.wait_for_selector("div#search", timeout=10000)
                except PlaywrightTimeoutError:
                    logging.info(f"No more results or empty page at index {current_index}.")
                    break
                
                # Fetch all a tags inside main search area
                locators = page.locator("div#search a[href]").all()
                
                articles: list[CandidateArticle] = []
                seen_urls = set()
                
                for loc in locators:
                    try:
                        href = loc.get_attribute("href") or ""
                        
                        if not href.startswith("http") or "google.com" in href:
                            continue
                            
                        # Try to get the h3 text as title
                        title_loc = loc.locator("h3")
                        if title_loc.count() > 0:
                            title = title_loc.first.text_content() or ""
                        else:
                            title = loc.text_content() or ""
                            
                        title = WS_RE.sub(" ", title).strip()
                        if not title:
                            continue
                            
                        canon_url = canonicalize_url(href)
                        if canon_url in seen_urls:
                            continue
                        seen_urls.add(canon_url)
                        
                        pub_date = day_str + "T12:00:00+00:00"
                        
                        articles.append(
                            CandidateArticle(
                                title=title,
                                url=canon_url,
                                source_name="Google Search",
                                source_type="playwright_google",
                                published_at=pub_date,
                                snippet="",
                                metadata={"query": query},
                            )
                        )
                    except Exception:
                        continue
                        
                next_start_idx = current_index + 10
                
                # Yield current page
                yield articles, next_start_idx, False
                
                # 3. Simulate human delay
                time.sleep(random.uniform(2.5, 5.5))
                
                # 4. Click Next
                # Google's next button usually has id "pnnext"
                next_btn = page.locator("a#pnnext")
                if next_btn.count() > 0:
                    try:
                        next_btn.first.click()
                        page.wait_for_load_state("domcontentloaded", timeout=30000)
                        current_index = next_start_idx
                    except Exception as e:
                        logging.error(f"Failed to click next: {e}")
                        break
                else:
                    # No more pages
                    break
                    
        except PlaywrightTimeoutError:
            logging.error("Playwright timeout navigating google.")
            yield [], current_index, True # Treat as block to be safe
        except Exception as e:
            logging.error(f"Playwright general error: {e}")
            yield [], current_index, True
            
        finally:
            browser.close()


def fetch_full_article_text(url: str, request_timeout: int = 10) -> tuple[str, str, str, str, str]:
    resolved_url = try_resolve_google_redirect(url, timeout=max(3, min(request_timeout, 8)))
    target_url = resolved_url or url
    final_url, raw_html = fetch_url(target_url, timeout=request_timeout)
    full_text = html_to_article_text(raw_html)
    # Heuristic: some sites wrap the real body in containers we don't detect, resulting in tiny text
    # (eg. just an image caption). Fallback to full-page text for matching.
    if len(full_text.split()) < 80:
        fallback = html_to_text(raw_html)
        if len(fallback) > len(full_text):
            full_text = fallback
    title = extract_html_title(raw_html)
    published = extract_published_at(raw_html)
    return canonicalize_url(final_url), raw_html, full_text, title, published


# ── Recovered helper functions ──────────────────────────────────────────
# VERBATIM from 63MB Codex session log (see collectors_recovered.py for provenance)


def _xml_local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _slug_title_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    slug = path.rsplit("/", 1)[-1] if "/" in path else path
    return re.sub(r"[-_]+", " ", slug).strip().title() or ""


def _normalize_query_values(queries: list[str] | None) -> list[str]:
    return [normalize_text(q) for q in (queries or []) if normalize_text(q)]


def _canonicalize_search_page_url(url: str) -> str:
    raw = str(url or "").strip()
    if not raw:
        return ""
    try:
        parts = urlsplit(raw)
    except Exception:
        return raw
    scheme = (parts.scheme or "https").lower()
    netloc = (parts.netloc or "").lower()
    path = re.sub(r"/+", "/", parts.path or "")
    if path != "/":
        path = path.rstrip("/")
    query = urlencode(parse_qsl(parts.query, keep_blank_values=True), doseq=True)
    return urlunsplit((scheme, netloc, path, query, ""))


def _iter_window_days(date_from: str, date_to: str, *, default_days: int = 7) -> list[datetime]:
    start_dt = _parse_window_boundary(date_from, end_of_day=False)
    end_dt = _parse_window_boundary(date_to, end_of_day=True)
    now = datetime.now(timezone.utc)
    if start_dt is None and end_dt is None:
        end_dt = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        start_dt = (end_dt - timedelta(days=max(0, default_days - 1))).replace(
            hour=0, minute=0, second=0, microsecond=0,
        )
    elif start_dt is None and end_dt is not None:
        start_dt = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif start_dt is not None and end_dt is None:
        end_dt = start_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    assert start_dt is not None and end_dt is not None
    if end_dt < start_dt:
        start_dt, end_dt = end_dt, start_dt
    current = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    final = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    days: list[datetime] = []
    while current <= final:
        days.append(current)
        current += timedelta(days=1)
    return days


def _matches_queries(text: str, queries: list[str] | None) -> bool:
    normalized_queries = _normalize_query_values(queries)
    if not normalized_queries:
        return True
    searchable = normalize_text(text)
    if not searchable:
        return False
    return any(query in searchable for query in normalized_queries)


def _parse_sitemap_entries(xml_text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return rows
    for url_node in root.iter():
        if _xml_local_name(url_node.tag) != "url":
            continue
        loc = ""
        title = ""
        published_at = ""
        for child in url_node.iter():
            name = _xml_local_name(child.tag)
            value = _safe_text(child)
            if not value:
                continue
            if name == "loc" and child is not url_node:
                if not loc:
                    loc = value
            elif name in {"title", "news_title"} and not title:
                title = value
            elif name in {"publication_date", "lastmod"} and not published_at:
                published_at = _parse_datetime(value)
        if loc:
            rows.append({"loc": loc, "title": title, "published_at": published_at})
    return rows


def _build_specialized_candidate(
    *,
    title: str,
    url: str,
    source_name: str,
    source_type: str,
    published_at: str,
    snippet: str = "",
    metadata: dict | None = None,
) -> CandidateArticle:
    item_metadata = dict(metadata or {})
    item_metadata.setdefault("force_full_fetch", True)
    item_metadata.setdefault("exact_body_only", True)
    item_metadata.setdefault("require_published_extraction", not bool(published_at))
    return CandidateArticle(
        title=_clean_html_fragment(title) or _slug_title_from_url(url),
        url=canonicalize_url(url),
        source_name=source_name,
        source_type=source_type,
        published_at=published_at,
        snippet=_clean_html_fragment(snippet),
        metadata=item_metadata,
    )


def _extract_vejario_archive_page(
    html_page: str,
    current_url: str,
    target: dict[str, str],
) -> tuple[list[CandidateArticle], str]:
    candidates: list[CandidateArticle] = []
    seen_urls: set[str] = set()
    expected_host = str(target.get("host") or "vejario.abril.com.br").strip() or "vejario.abril.com.br"
    path_prefix = str(target.get("article_path_prefix") or "").strip()
    source_name = str(target.get("source_name") or "Veja Rio Archive").strip() or "Veja Rio Archive"

    for block in DIV_CARD_RE.findall(html_page or ""):
        links = _anchor_records(block)
        chosen_url = ""
        chosen_title = ""
        for link_title, link_href, _, _ in links:
            resolved = canonicalize_url(urljoin(current_url, link_href))
            parsed = urlparse(resolved)
            if not _host_matches(parsed.netloc, expected_host):
                continue
            if path_prefix and not (parsed.path or "").startswith(path_prefix):
                continue
            if not is_likely_article_url(resolved, expected_host_fragment=expected_host):
                continue
            chosen_url = resolved
            chosen_title = link_title or chosen_title
            break
        if not chosen_url or chosen_url in seen_urls:
            continue
        seen_urls.add(chosen_url)
        time_match = re.search(r"(?is)<time[^>]*>(.*?)</time>", block)
        desc_match = re.search(r'(?is)<p[^>]+class=["\'][^"\']*description[^"\']*["\'][^>]*>(.*?)</p>', block)
        candidates.append(
            _build_specialized_candidate(
                title=chosen_title,
                url=chosen_url,
                source_name=source_name,
                source_type="vejario_archive",
                published_at=_parse_pt_br_datetime(time_match.group(1) if time_match else ""),
                snippet=desc_match.group(1) if desc_match else "",
                metadata={"archive_url": current_url, "archive_host": expected_host},
            )
        )

    next_url = ""
    path_match = VEJARIO_INFINITY_RE.search(html_page or "")
    if path_match:
        path_template = path_match.group(1).replace("\\/", "/")
        parameters = (path_match.group(2) or "").replace("\\/", "/")
        current_page = 1
        current_match = re.search(r"/pagina/(\d+)/", current_url)
        if current_match:
            current_page = int(current_match.group(1))
        next_path = path_template.replace("%d", str(current_page + 1))
        next_url = _canonicalize_search_page_url(urljoin(current_url, f"{next_path}{parameters}"))
    return candidates, next_url


# ── Recovered collector functions ──────────────────────────────────────
# VERBATIM from 63MB Codex session log (see collectors_recovered.py for provenance)


def collect_camara_archive(
    *,
    target: dict[str, str | int] | None = None,
    date_from: str = "",
    date_to: str = "",
    limit_total: int = 120,
    max_pages: int = 24,
    request_timeout: int = 10,
) -> list[CandidateArticle]:
    config = target or CAMARA_ARCHIVE_TARGET
    base_url = str(config.get("start_url") or "").strip()
    host = str(config.get("host") or "camara.rio").strip() or "camara.rio"
    source_name = str(config.get("source_name") or "Camara Rio Archive").strip() or "Camara Rio Archive"
    page_size = max(1, int(config.get("page_size") or 10))
    if not base_url:
        return []
    start = _parse_window_boundary(date_from, end_of_day=False)
    end = _parse_window_boundary(date_to, end_of_day=True)
    next_url = f"{base_url}?limit={page_size}&start=0"
    pages_seen: set[str] = set()
    collected: list[CandidateArticle] = []
    seen_urls: set[str] = set()
    current_page = 0
    while next_url and current_page < max(1, max_pages) and len(collected) < max(1, limit_total):
        page_url = _canonicalize_search_page_url(next_url)
        if page_url in pages_seen:
            break
        pages_seen.add(page_url)
        current_page += 1
        try:
            _, html_page = fetch_url(page_url, timeout=request_timeout)
        except Exception:
            break
        page_candidates: list[CandidateArticle] = []
        dated_hits = 0
        older_hits = 0
        for created, href, title in CAMARA_ARCHIVE_ITEM_RE.findall(html_page or ""):
            resolved = canonicalize_url(urljoin(page_url, html.unescape(href)))
            if not is_likely_article_url(resolved, expected_host_fragment=host):
                continue
            if resolved in seen_urls:
                continue
            published_at = _parse_pt_br_datetime(created)
            if published_at:
                parsed = _parse_window_boundary(published_at, end_of_day=False)
                if parsed:
                    dated_hits += 1
                    if start and parsed < start:
                        older_hits += 1
                    if end and parsed > end:
                        continue
                    if start and parsed < start:
                        continue
            seen_urls.add(resolved)
            page_candidates.append(
                _build_specialized_candidate(
                    title=title,
                    url=resolved,
                    source_name=source_name,
                    source_type="camara_archive",
                    published_at=published_at,
                    metadata={"archive_url": page_url, "archive_host": host},
                )
            )
            if len(collected) + len(page_candidates) >= max(1, limit_total):
                break
        collected.extend(page_candidates)
        if len(collected) >= max(1, limit_total):
            break
        if dated_hits and older_hits == dated_hits:
            break
        next_match = CAMARA_NEXT_RE.search(html_page or "")
        next_url = urljoin(page_url, html.unescape(next_match.group(1))) if next_match else ""
    return collected


def collect_vejario_archive(
    *,
    targets: list[dict[str, str]] | None = None,
    date_from: str = "",
    date_to: str = "",
    limit_per_target: int = 120,
    max_pages_per_target: int = 12,
    request_timeout: int = 10,
) -> list[CandidateArticle]:
    target_list = targets or VEJARIO_ARCHIVE_TARGETS
    collected: list[CandidateArticle] = []
    global_seen_urls: set[str] = set()
    start = _parse_window_boundary(date_from, end_of_day=False)
    end = _parse_window_boundary(date_to, end_of_day=True)
    for target in target_list:
        next_url = str(target.get("start_url") or "").strip()
        if not next_url:
            continue
        pages_seen: set[str] = set()
        current_page = 0
        accepted = 0
        while next_url and current_page < max(1, max_pages_per_target) and accepted < max(1, limit_per_target):
            page_url = _canonicalize_search_page_url(next_url)
            if page_url in pages_seen:
                break
            pages_seen.add(page_url)
            current_page += 1
            try:
                _, html_page = fetch_url(page_url, timeout=request_timeout)
            except Exception:
                break
            page_candidates, discovered_next = _extract_vejario_archive_page(html_page, page_url, target)
            dated_hits = 0
            older_hits = 0
            for item in page_candidates:
                if item.published_at:
                    parsed = _parse_window_boundary(item.published_at, end_of_day=False)
                    if parsed:
                        dated_hits += 1
                        if start and parsed < start:
                            older_hits += 1
                        if end and parsed > end:
                            continue
                        if start and parsed < start:
                            continue
                if item.url in global_seen_urls:
                    continue
                global_seen_urls.add(item.url)
                collected.append(item)
                accepted += 1
                if accepted >= max(1, limit_per_target):
                    break
            if accepted >= max(1, limit_per_target):
                break
            if dated_hits and older_hits == dated_hits:
                break
            next_url = discovered_next
    return collected


def collect_sitemap_daily(
    queries: list[str] | None = None,
    *,
    sources: list[dict[str, str]] | None = None,
    date_from: str = "",
    date_to: str = "",
    limit_per_source: int = 240,
    request_timeout: int = 10,
) -> list[CandidateArticle]:
    query_list = [str(item or "").strip() for item in (queries or []) if str(item or "").strip()]
    source_list = sources or SITEMAP_DAILY_SOURCES
    days = _iter_window_days(date_from, date_to, default_days=7)
    collected: list[CandidateArticle] = []
    seen_urls: set[str] = set()
    for source in source_list:
        source_name = str(source.get("source_name") or "Sitemap Daily").strip() or "Sitemap Daily"
        host = str(source.get("host") or "").strip()
        template = str(source.get("sitemap_url_template") or "").strip()
        if not host or not template:
            continue
        accepted = 0
        for day in days:
            if accepted >= max(1, limit_per_source):
                break
            sitemap_url = template.format(
                yyyy=day.strftime("%Y"),
                mm=day.strftime("%m"),
                dd=day.strftime("%d"),
            )
            try:
                _, xml_text = fetch_url(sitemap_url, timeout=request_timeout)
            except Exception:
                continue
            for row in _parse_sitemap_entries(xml_text):
                canon_url = canonicalize_url(str(row.get("loc") or "").strip())
                if not canon_url or canon_url in seen_urls:
                    continue
                if not is_likely_article_url(canon_url, expected_host_fragment=host):
                    continue
                title = str(row.get("title") or "").strip()
                if query_list and not _matches_queries(" ".join([canon_url, title]), query_list):
                    continue
                published_at = str(row.get("published_at") or "").strip() or day.replace(
                    hour=12, minute=0, second=0, microsecond=0,
                ).isoformat()
                if not _within_window(published_at, date_from=date_from, date_to=date_to):
                    continue
                seen_urls.add(canon_url)
                collected.append(
                    _build_specialized_candidate(
                        title=title,
                        url=canon_url,
                        source_name=source_name,
                        source_type="sitemap_daily",
                        published_at=published_at,
                        metadata={"sitemap_url": sitemap_url, "sitemap_host": host},
                    )
                )
                accepted += 1
                if accepted >= max(1, limit_per_source):
                    break
    return collected
