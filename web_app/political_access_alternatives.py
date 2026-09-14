"""Public feed bodies verified from the actual production worker.

No fetching occurs here. The caller retains the response in the existing
immutable body-batch store before enqueueing references, and owns throttling,
pagination and date filtering. RSS descriptions never substitute for bodies.
"""
from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from urllib.parse import parse_qs, urljoin, urlparse

from pipeline.http_utils import canonicalize_url, html_to_text
from .political_editorial_extraction import _date

PUBLIC_FEED_BODY_SOURCES = {"diario_do_vale": "diariodovale.com.br"}
MAX_FEED_BYTES = 4 * 1024 * 1024
MAX_FEED_ITEMS = 100


def _host(url):
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def parse_public_feed(raw: str | bytes, feed_url: str, source: dict) -> dict:
    """Return candidates and bounded immutable-batch records from public RSS.

    WordPress numeric IDs come from the publisher's GUID, never a fabricated
    counter. Missing IDs/dates keep URL discovery but cannot enter body batches.
    ``unknown`` means that RSS text was obtained but its extent relative to the
    individual web article has not been independently certified.
    """
    key = source.get("key")
    expected = PUBLIC_FEED_BODY_SOURCES.get(key)
    if not expected or _host(feed_url) != expected or urlparse(feed_url).scheme != "https":
        raise ValueError("unverified_public_feed_source")
    payload = raw.encode("utf-8") if isinstance(raw, str) else raw
    if not isinstance(payload, bytes) or len(payload) > MAX_FEED_BYTES:
        raise ValueError("public_feed_response_limit")
    root = ET.fromstring(payload)
    if root.tag != "rss":
        raise ValueError("public_feed_expected_rss")
    items = root.findall("./channel/item")
    if len(items) > MAX_FEED_ITEMS:
        raise ValueError("public_feed_candidate_limit")
    digest = hashlib.sha256(payload).hexdigest()
    candidates, records, dates, seen, all_urls = [], [], [], set(), []
    for item in items:
        url = canonicalize_url(urljoin(feed_url, item.findtext("link", "")))
        published = _date(item.findtext("pubDate", ""))
        dates.append(published)
        all_urls.append(url)
        if _host(url) != expected or urlparse(url).scheme != "https" or url in seen:
            continue
        seen.add(url)
        guid = item.findtext("guid", "")
        identifier = parse_qs(urlparse(guid).query).get("p", [""])[0] if _host(guid) == expected else ""
        post_id = int(identifier) if re.fullmatch(r"[1-9]\d{0,14}", identifier) else None
        content = item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded", "")
        metadata = {"feed_url": feed_url, "feed_sha256": digest,
                    "feed_content_available": bool(content.strip()),
                    "discovery_adapter": "public_feed_body_v1",
                    "needs_date_review": not bool(published)}
        if post_id:
            metadata["wordpress_id"] = post_id
        candidates.append({"url": url, "title": html_to_text(item.findtext("title", "")),
            "source_key": key, "source_name": source.get("name", "Diário do Vale"),
            "source_type": "political_discovery", "published_at": published,
            "snippet": html_to_text(item.findtext("description", "")), "metadata": metadata})
        if content.strip() and post_id and published:
            records.append({"post_id": post_id, "url": url, "published_at": published,
                "content_html": content, "protected": False,
                "body_origin": "publisher_rss", "feed_url": feed_url,
                "feed_sha256": digest, "text_extent": "unknown"})
    return {"candidates": candidates, "body_batch": {"source_key": key, "records": records},
            "raw_count": len(items), "publication_dates": dates,
            "fingerprint": hashlib.sha256("\n".join(all_urls).encode()).hexdigest()}
