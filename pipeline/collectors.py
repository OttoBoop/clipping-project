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
    """Parse various date formats to ISO 8601 string. Returns None on failure."""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    # Already ISO
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str[:len(fmt)+5], fmt).strftime("%Y-%m-%dT%H:%M:%S")
        except (ValueError, IndexError):
            continue
    # RFC 2822 (RSS dates)
    try:
        return parsedate_to_datetime(date_str).strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        pass
    # Brazilian: DD/MM/YYYY
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", date_str)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}T00:00:00"
    return None


def _within_window(published_at, date_from, date_to):
    """Check if a date string falls within the window (inclusive)."""
    if not published_at:
        return True  # If no date, include it (be permissive)
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

            # Resolve Google redirect
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
    """Collect from standard RSS/Atom feeds. feed_urls: list of (name, url)."""
    candidates = []
    try:
        import feedparser
    except ImportError:
        print("  [rss] feedparser not installed, skipping RSS collection")
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
                    title=entry.get("title", ""),
                    url=entry.get("link", ""),
                    source_name=name,
                    source_type="rss",
                    published_at=pub,
                    snippet=entry.get("summary", ""),
                ))
        except Exception as e:
            print(f"  [rss] Error fetching {name}: {e}")

    print(f"  [rss] Found {len(candidates)} candidates from {len(feed_urls)} feeds")
    return candidates


# ── WordPress API ────────────────────────────────────────────


def collect_wordpress_api(hosts, query, date_from="", date_to="", limit=100, timeout=8):
    """Collect from WordPress REST API (wp/v2/posts)."""
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
                time.sleep(0.5)

        except Exception as e:
            print(f"  [wordpress_api] Error fetching {host}: {e}")

    print(f"  [wordpress_api] Found {len(candidates)} candidates from {len(hosts)} hosts")
    return candidates


# ── Internal Site Search ─────────────────────────────────────


def collect_internal_site_search(targets, query, date_from="", date_to="", limit_per=50, timeout=8):
    """Search news sites using their internal search pages."""
    candidates = []

    for target in targets:
        try:
            site_candidates = []
            encoded_query = quote_plus(query)

            for page in range(1, 4):  # Max 3 pages
                search_url = target.search_url_template.format(query=encoded_query, page=page)
                body, final_url = fetch_url(search_url, timeout=timeout)
                if not body:
                    break

                links = _extract_links(body, base_url=search_url)
                new_count = 0
                for href, text in links:
                    parsed = urlparse(href)
                    # Filter: must be on the same host and look like an article URL
                    if target.host not in (parsed.hostname or ""):
                        continue
                    path = parsed.path
                    # Skip generic pages (home, search, tag, section pages)
                    if path in ("/", "") or "/busca" in path or "/search" in path:
                        continue
                    if len(path) < 15:
                        continue
                    # Must have at least 2 path segments (e.g. /section/article-slug)
                    segments = [s for s in path.split("/") if s]
                    if len(segments) < 2:
                        continue
                    # Skip if title is too short or looks like a nav item
                    if len(text) < 25:
                        continue

                    site_candidates.append(_build_candidate(
                        title=text, url=href, source_name=target.name,
                        source_type="internal_search",
                        metadata={"query": query, "search_url": search_url},
                    ))
                    new_count += 1

                if new_count == 0:
                    break
                time.sleep(0.5)

            # Dedupe per site
            site_candidates = _dedupe_candidates_by_url(site_candidates)[:limit_per]
            candidates.extend(site_candidates)
            print(f"    [{target.name}] {len(site_candidates)} candidates")

        except Exception as e:
            print(f"    [{target.name}] Error: {e}")

    print(f"  [internal_search] Found {len(candidates)} total candidates")
    return candidates


# ── Sitemap Daily ────────────────────────────────────────────


def collect_sitemap_daily(configs, date_from="", date_to="", timeout=8):
    """Collect from XML sitemaps, filtering by date window."""
    candidates = []

    for config in configs:
        name = config.get("name", "unknown")
        sitemap_url = config.get("sitemap_url", "")
        host = config.get("host", "")

        try:
            body, _ = fetch_url(sitemap_url, timeout=timeout)
            if not body:
                print(f"    [{name}] Failed to fetch sitemap")
                continue

            # Parse XML sitemap
            root = ET.fromstring(body)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
                  "news": "http://www.google.com/schemas/sitemap-news/0.9"}

            urls = root.findall(".//sm:url", ns) or root.findall(".//url")
            site_count = 0

            for url_elem in urls:
                loc = url_elem.findtext("sm:loc", "", ns) or url_elem.findtext("loc", "")
                lastmod = url_elem.findtext("sm:lastmod", "", ns) or url_elem.findtext("lastmod", "")
                # Try news:publication_date
                news_date = url_elem.findtext(".//news:publication_date", "", ns)
                news_title = url_elem.findtext(".//news:title", "", ns)
                pub_date = news_date or lastmod

                if not loc:
                    continue
                if not _within_window(pub_date, date_from, date_to):
                    continue

                candidates.append(_build_candidate(
                    title=news_title or "", url=loc, source_name=name,
                    source_type="sitemap_daily", published_at=pub_date,
                    metadata={"sitemap_url": sitemap_url},
                ))
                site_count += 1

            print(f"    [{name}] {site_count} candidates from sitemap")

        except ET.ParseError as e:
            print(f"    [{name}] XML parse error: {e}")
        except Exception as e:
            print(f"    [{name}] Error: {e}")

    print(f"  [sitemap_daily] Found {len(candidates)} total candidates")
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
                    source_type="vejario_archive",
                    metadata={"query": query},
                ))
                new += 1
            if new == 0:
                break
            time.sleep(0.5)

    except Exception as e:
        print(f"  [vejario_archive] Error: {e}")

    candidates = _dedupe_candidates_by_url(candidates)
    print(f"  [vejario_archive] Found {len(candidates)} candidates")
    return candidates


# ── Câmara do Rio Archive ────────────────────────────────────


def collect_camara_archive(query, date_from="", date_to="", timeout=8):
    """Collect from Câmara do Rio website search."""
    candidates = []
    try:
        encoded = quote_plus(query)
        for page in range(1, 3):
            search_url = f"https://www.camara.rio/noticias?busca={encoded}&pagina={page}"
            body, _ = fetch_url(search_url, timeout=timeout)
            if not body:
                break

            links = _extract_links(body, base_url=search_url)
            new = 0
            for href, text in links:
                host = urlparse(href).hostname or ""
                if "camara.rio" not in host:
                    continue
                if len(text) < 15 or "/noticias?" in href:
                    continue
                candidates.append(_build_candidate(
                    title=text, url=href, source_name="Câmara do Rio",
                    source_type="camara_archive",
                    metadata={"query": query},
                ))
                new += 1
            if new == 0:
                break
            time.sleep(0.5)

    except Exception as e:
        print(f"  [camara_archive] Error: {e}")

    candidates = _dedupe_candidates_by_url(candidates)
    print(f"  [camara_archive] Found {len(candidates)} candidates")
    return candidates
