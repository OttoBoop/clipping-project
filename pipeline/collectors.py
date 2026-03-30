"""News source collectors for the clipping pipeline."""
import html as html_mod
import json
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus, urljoin, urlparse, urlencode

from .http_utils import fetch_url, try_resolve_google_redirect
from .normalization import normalize_url, canonicalize_url


@dataclass
class CandidateArticle:
    url: str
    title: str
    source_name: str
    source_type: str
    published_at: str | None = None
    snippet: str = ""
    metadata: dict | None = None


# ── Helpers ──────────────────────────────────────────────────


def _parse_date(date_str):
    """Parse various date formats to ISO 8601 string."""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str[:26], fmt)
            return dt.strftime("%Y-%m-%dT%H:%M:%S")
        except (ValueError, IndexError):
            continue
    try:
        return parsedate_to_datetime(date_str).strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        pass
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", date_str)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}T00:00:00"
    return None


def _within_window(published_at, date_from, date_to):
    """Check if a date string falls within the window (inclusive)."""
    if not published_at:
        return True
    parsed = _parse_date(published_at)
    if not parsed:
        return True
    day = parsed[:10]
    if date_from and day < date_from:
        return False
    if date_to and day > date_to:
        return False
    return True


def _build_candidate(*, title, url, source_name, source_type, published_at=None, snippet="", metadata=None):
    return CandidateArticle(
        url=normalize_url(url),
        title=_strip_html(title or ""),
        source_name=source_name,
        source_type=source_type,
        published_at=_parse_date(published_at),
        snippet=_strip_html(snippet or ""),
        metadata=metadata,
    )


def _dedupe_candidates_by_url(candidates):
    """Remove duplicate URLs, keep first occurrence."""
    seen = set()
    result = []
    for c in candidates:
        key = canonicalize_url(c.url)
        if key and key not in seen:
            seen.add(key)
            result.append(c)
    return result


def _strip_html(text):
    """Remove HTML tags and unescape entities."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", str(text))
    return html_mod.unescape(text).strip()


_A_TAG_RE = re.compile(r'<a\s+([^>]*?)href=["\']([^"\']+)["\']([^>]*)>(.*?)</a>', re.I | re.DOTALL)


def _extract_links(html_text, base_url=""):
    """Extract (url, title_text) pairs from HTML anchor tags."""
    results = []
    for m in _A_TAG_RE.finditer(html_text or ""):
        href = m.group(2)
        text = _strip_html(m.group(4))
        if href and text and len(text) > 10:
            if not href.startswith("http"):
                href = urljoin(base_url, href)
            results.append((href, text))
    return results


def _iter_window_days(date_from, date_to):
    """Iterate over days in the window as datetime objects."""
    try:
        start = datetime.strptime(date_from, "%Y-%m-%d")
        end = datetime.strptime(date_to, "%Y-%m-%d")
    except (ValueError, TypeError):
        return
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)


def _is_article_url(href, host):
    """Check if a URL looks like a news article (not a nav/section page)."""
    parsed = urlparse(href)
    if host not in (parsed.hostname or ""):
        return False
    path = parsed.path
    if path in ("/", "") or "/busca" in path or "/search" in path or "?" in path:
        return False
    segments = [s for s in path.split("/") if s]
    if len(segments) < 2:
        return False
    if len(path) < 15:
        return False
    return True


# ── Google News (RSS) ────────────────────────────────────────


def collect_google_news(query, date_from="", date_to="", limit=100, timeout=8):
    """Collect articles from Google News RSS feed."""
    candidates = []
    try:
        encoded = quote_plus(query)
        url = f"https://news.google.com/rss/search?q={encoded}+when:7d&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        body, _ = fetch_url(url, timeout=timeout)
        if not body:
            print("  [google_news] Failed to fetch RSS feed")
            return []
        root = ET.fromstring(body)
        items = root.findall(".//item")
        for item in items[:limit]:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            source = item.findtext("source", "")
            resolved = try_resolve_google_redirect(link)
            if not _within_window(pub_date, date_from, date_to):
                continue
            candidates.append(_build_candidate(
                title=title, url=resolved, source_name=source or "Google News",
                source_type="google_news", published_at=pub_date,
                metadata={"query": query, "google_link": link},
            ))
    except Exception as e:
        print(f"  [google_news] Error: {e}")
    print(f"  [google_news] Found {len(candidates)} candidates")
    return candidates


# ── RSS Feeds ────────────────────────────────────────────────


def collect_rss(feed_urls, date_from="", date_to="", timeout=8):
    """Collect from standard RSS/Atom feeds."""
    candidates = []
    if not feed_urls:
        print("  [rss] No feeds configured")
        return []
    try:
        import feedparser
    except ImportError:
        print("  [rss] feedparser not installed, skipping")
        return []
    for name, feed_url in feed_urls:
        try:
            body, _ = fetch_url(feed_url, timeout=timeout)
            if not body:
                continue
            feed = feedparser.parse(body)
            for entry in feed.entries:
                pub = entry.get("published", entry.get("updated", ""))
                if not _within_window(pub, date_from, date_to):
                    continue
                candidates.append(_build_candidate(
                    title=entry.get("title", ""), url=entry.get("link", ""),
                    source_name=name, source_type="rss", published_at=pub,
                    snippet=entry.get("summary", ""),
                ))
        except Exception as e:
            print(f"  [rss] Error fetching {name}: {e}")
    print(f"  [rss] Found {len(candidates)} candidates from {len(feed_urls)} feeds")
    return candidates


# ── WordPress API ────────────────────────────────────────────


def collect_wordpress_api(hosts, query, date_from="", date_to="", limit=100, timeout=8):
    """Collect from WordPress REST API."""
    candidates = []
    for host in hosts:
        try:
            page = 1
            while len(candidates) < limit:
                params = {"search": query, "per_page": 20, "page": page, "orderby": "date", "order": "desc"}
                if date_from:
                    params["after"] = f"{date_from}T00:00:00"
                if date_to:
                    params["before"] = f"{date_to}T23:59:59"
                api_url = f"https://{host}/wp-json/wp/v2/posts?{urlencode(params)}"
                body, _ = fetch_url(api_url, timeout=timeout, headers={"Accept": "application/json"})
                if not body:
                    break
                try:
                    posts = json.loads(body)
                except json.JSONDecodeError:
                    break
                if not isinstance(posts, list) or not posts:
                    break
                for post in posts:
                    title = _strip_html(post.get("title", {}).get("rendered", ""))
                    link = post.get("link", "")
                    date = post.get("date", "")
                    excerpt = _strip_html(post.get("excerpt", {}).get("rendered", ""))
                    candidates.append(_build_candidate(
                        title=title, url=link, source_name=host,
                        source_type="wordpress_api", published_at=date,
                        snippet=excerpt, metadata={"query": query},
                    ))
                if len(posts) < 20:
                    break
                page += 1
                time.sleep(0.3)
        except Exception as e:
            print(f"  [wordpress_api] Error fetching {host}: {e}")
    print(f"  [wordpress_api] Found {len(candidates)} candidates from {len(hosts)} hosts")
    return candidates


# ── Globo API Search ─────────────────────────────────────────


def _collect_globo_api(target, query, date_from="", date_to="", limit=50, timeout=8):
    """Collect from Globo busca API (JSON)."""
    candidates = []
    try:
        encoded = quote_plus(query)
        for page in range(1, 4):
            api_url = target.search_url_template.format(query=encoded, page=page)
            body, _ = fetch_url(api_url, timeout=timeout, headers={"Accept": "application/json"})
            if not body:
                break
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                # Might be HTML, try extracting links
                break

            # Globo API returns items in various structures
            items = []
            if isinstance(data, dict):
                items = data.get("items", data.get("results", data.get("hits", [])))
            elif isinstance(data, list):
                items = data

            if not items:
                break

            for item in items:
                if isinstance(item, dict):
                    title = item.get("title", item.get("name", ""))
                    url = item.get("url", item.get("link", item.get("href", "")))
                    pub = item.get("published", item.get("date", item.get("created", "")))
                    snippet = item.get("summary", item.get("description", item.get("abstract", "")))
                else:
                    continue

                if not url:
                    continue
                if not _within_window(pub, date_from, date_to):
                    continue

                candidates.append(_build_candidate(
                    title=title, url=url, source_name=target.name,
                    source_type="internal_search", published_at=pub,
                    snippet=snippet, metadata={"query": query, "api": "globo_busca"},
                ))

            if len(items) < 10:
                break
            time.sleep(0.3)

    except Exception as e:
        print(f"    [{target.name}] Globo API error: {e}")

    return candidates


# ── Internal Site Search (HTML) ──────────────────────────────


def _collect_html_search(target, query, date_from="", date_to="", limit=50, timeout=8):
    """Collect from a site's HTML search page."""
    candidates = []
    try:
        encoded = quote_plus(query)
        for page in range(1, 4):
            search_url = target.search_url_template.format(query=encoded, page=page)
            body, final_url = fetch_url(search_url, timeout=timeout)
            if not body:
                break
            links = _extract_links(body, base_url=search_url)
            new_count = 0
            for href, text in links:
                if not _is_article_url(href, target.host):
                    continue
                if len(text) < 25:
                    continue
                candidates.append(_build_candidate(
                    title=text, url=href, source_name=target.name,
                    source_type="internal_search",
                    metadata={"query": query, "search_url": search_url},
                ))
                new_count += 1
            if new_count == 0:
                break
            time.sleep(0.3)
    except Exception as e:
        print(f"    [{target.name}] HTML search error: {e}")
    return candidates


def collect_internal_site_search(targets, query, date_from="", date_to="", limit_per=50, timeout=8):
    """Search news sites using their internal search pages or APIs."""
    candidates = []
    for target in targets:
        try:
            if target.uses_globo_api:
                batch = _collect_globo_api(target, query, date_from, date_to, limit_per, timeout)
            else:
                batch = _collect_html_search(target, query, date_from, date_to, limit_per, timeout)
            batch = _dedupe_candidates_by_url(batch)[:limit_per]
            candidates.extend(batch)
            print(f"    [{target.name}] {len(batch)} candidates")
        except Exception as e:
            print(f"    [{target.name}] Error: {e}")
    print(f"  [internal_search] Found {len(candidates)} total candidates")
    return candidates


# ── Sitemap Daily ────────────────────────────────────────────


def collect_sitemap_daily(configs, date_from="", date_to="", query="", timeout=8):
    """Collect from XML sitemaps. Supports daily URL templates and standard sitemaps."""
    candidates = []
    for config in configs:
        name = config.get("name", "unknown")
        host = config.get("host", "")
        is_daily = config.get("daily", False)

        try:
            if is_daily and config.get("sitemap_url_template"):
                # Iterate over each day in the window
                template = config["sitemap_url_template"]
                site_count = 0
                for day in _iter_window_days(date_from, date_to):
                    sitemap_url = template.format(
                        yyyy=day.strftime("%Y"), mm=day.strftime("%m"), dd=day.strftime("%d"),
                    )
                    body, _ = fetch_url(sitemap_url, timeout=timeout)
                    if not body:
                        continue
                    try:
                        entries = _parse_sitemap_xml(body, host, date_from, date_to, query)
                        for e in entries:
                            candidates.append(e)
                            site_count += 1
                    except ET.ParseError:
                        continue
                    time.sleep(0.2)
                print(f"    [{name}] {site_count} candidates from daily sitemaps")

            elif config.get("sitemap_url"):
                # Standard single sitemap
                body, _ = fetch_url(config["sitemap_url"], timeout=timeout)
                if not body:
                    print(f"    [{name}] Failed to fetch sitemap")
                    continue
                entries = _parse_sitemap_xml(body, host, date_from, date_to, query)
                candidates.extend(entries)
                print(f"    [{name}] {len(entries)} candidates from sitemap")

        except Exception as e:
            print(f"    [{name}] Error: {e}")

    print(f"  [sitemap_daily] Found {len(candidates)} total candidates")
    return candidates


def _parse_sitemap_xml(xml_text, host, date_from, date_to, query=""):
    """Parse a sitemap XML and return CandidateArticle list."""
    entries = []
    root = ET.fromstring(xml_text)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
          "news": "http://www.google.com/schemas/sitemap-news/0.9",
          "image": "http://www.google.com/schemas/sitemap-image/1.1"}

    for url_elem in root.findall(".//sm:url", ns) or root.findall(".//url"):
        loc = url_elem.findtext("sm:loc", "", ns) or url_elem.findtext("loc", "")
        lastmod = url_elem.findtext("sm:lastmod", "", ns) or url_elem.findtext("lastmod", "")
        news_date = url_elem.findtext(".//news:publication_date", "", ns)
        news_title = url_elem.findtext(".//news:title", "", ns)
        pub_date = news_date or lastmod

        if not loc:
            continue
        # Skip images
        if re.search(r"\.(jpg|jpeg|png|gif|webp|svg)(\?|$)", loc, re.I):
            continue
        if not _within_window(pub_date, date_from, date_to):
            continue

        entries.append(_build_candidate(
            title=news_title or "", url=loc, source_name=host,
            source_type="sitemap_daily", published_at=pub_date,
            metadata={"source": "sitemap"},
        ))
    return entries


# ── Câmara do Rio Archive ────────────────────────────────────


def collect_camara_archive(query, date_from="", date_to="", timeout=8):
    """Collect from Câmara do Rio website search."""
    candidates = []
    try:
        encoded = quote_plus(query)
        # Câmara do Rio uses Joomla search
        for page in range(1, 3):
            search_url = (
                f"https://camara.rio/index.php?option=com_search&view=search"
                f"&searchphrase=exact&searchword={encoded}&limitstart={20 * (page - 1)}"
            )
            body, _ = fetch_url(search_url, timeout=timeout)
            if not body:
                break
            links = _extract_links(body, base_url="https://camara.rio")
            new = 0
            for href, text in links:
                if "camara.rio" not in (urlparse(href).hostname or ""):
                    continue
                if len(text) < 20 or "com_search" in href:
                    continue
                candidates.append(_build_candidate(
                    title=text, url=href, source_name="Câmara do Rio",
                    source_type="camara_archive", metadata={"query": query},
                ))
                new += 1
            if new == 0:
                break
            time.sleep(0.3)
    except Exception as e:
        print(f"  [camara_archive] Error: {e}")
    candidates = _dedupe_candidates_by_url(candidates)
    print(f"  [camara_archive] Found {len(candidates)} candidates")
    return candidates


# ── Veja Rio Archive ─────────────────────────────────────────


def collect_vejario_archive(query, date_from="", date_to="", timeout=8):
    """Collect from Veja Rio archive/search."""
    candidates = []
    try:
        encoded = quote_plus(query)
        for page in range(1, 3):
            search_url = f"https://vejario.abril.com.br/page/{page}/?s={encoded}"
            body, _ = fetch_url(search_url, timeout=timeout)
            if not body:
                break
            links = _extract_links(body, base_url=search_url)
            new = 0
            for href, text in links:
                if "vejario.abril.com.br" not in (urlparse(href).hostname or ""):
                    continue
                if len(text) < 15:
                    continue
                candidates.append(_build_candidate(
                    title=text, url=href, source_name="Veja Rio",
                    source_type="vejario_archive", metadata={"query": query},
                ))
                new += 1
            if new == 0:
                break
            time.sleep(0.3)
    except Exception as e:
        print(f"  [vejario_archive] Error: {e}")
    candidates = _dedupe_candidates_by_url(candidates)
    print(f"  [vejario_archive] Found {len(candidates)} candidates")
    return candidates
