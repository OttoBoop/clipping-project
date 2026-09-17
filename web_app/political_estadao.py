"""Resolve the publisher's public snack pages to their advertised original.

The short summary is never treated as an article body. No URL is guessed and
no private endpoint or subscription session participates in resolution.
"""
import json
import re
from urllib.parse import urlparse


def public_original(raw_html: str, page_url: str) -> dict | None:
    page = urlparse(page_url)
    if page.hostname not in {"estadao.com.br", "www.estadao.com.br"} or not page.path.startswith("/em-alta/"):
        return None
    match = re.search(r"\bFusion\.globalContent\s*=\s*", raw_html)
    if not match:
        return None
    try:
        data, _ = json.JSONDecoder().raw_decode(raw_html[match.end():])
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict) or data.get("subtype") != "snack-em-alta":
        return None
    snack = data.get("snack") or {}
    original = snack.get("original_source") or {}
    url = original.get("url") or ""
    parsed = urlparse(url)
    if (parsed.scheme != "https" or parsed.hostname not in {"estadao.com.br", "www.estadao.com.br"}
            or parsed.username or parsed.password or parsed.port not in {None, 443}
            or parsed.path.startswith("/em-alta/") or not original.get("id")
            or original["id"] != snack.get("id")):
        return None
    return {"url": url, "publisher_content_id": original["id"],
            "method": "public_Fusion.globalContent.snack.original_source", "original_page": page_url}
