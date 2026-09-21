"""Public raw-HTML editorial blocks omitted by server-side lazy rendering."""
from urllib.parse import urljoin, urlparse

from .political_estadao_eldorado import _state
from .political_editorial_extraction import _EditorialParser, _date, _normalize


def extract(raw, url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"www.estadao.com.br", "estadao.com.br"}:
        return None
    data = _state(raw, "globalContent")
    if data.get("type") != "story" or data.get("subtype") != "reportagem" or not data.get("_id"):
        return None
    canonical = urljoin(url, data.get("canonical_url") or "")
    if canonical.rstrip("/") != url.rstrip("/"):
        return None
    elements = data.get("content_elements") or []
    if not any(e.get("type") == "raw_html" for e in elements):
        return None
    parts = []
    unknown = set()
    gates = []
    for element in elements:
        kind = element.get("type")
        if kind in {"text", "header", "raw_html"}:
            # Reuse the existing editorial parser: no scripts, iframe text,
            # navigation or related-story blocks; never execute embedded HTML.
            parser = _EditorialParser("estadao.com.br")
            parser.feed('<div class="news-body" data-paywall-wrapper="true">'
                        + (element.get("content") or "") + '</div>')
            parser.close()
            gates.extend(parser.restrictions)
            text = _normalize("".join(parser.parts))
            if text:
                parts.append(text)
        elif kind not in {"image", "divider"}:
            unknown.add(str(kind))
    body = "\n\n".join(parts)
    if not body:
        return None
    stamp = _date(data.get("first_publish_date") or "")
    restriction = (data.get("content_restrictions") or {}).get("content_code", "")
    return {"full_text": body, "title": (data.get("headlines") or {}).get("basic", ""),
        "canonical_url": canonical, "published_at": stamp,
        "extraction_state": "full_text" if len(body.split()) >= 40 else "metadata_only",
        "extraction_method": "publisher_public_editorial_raw_html", "extraction_version": "estadao-lazy-body-1",
        "content_format": "article_with_lazy_editorial_html",
        "text_extent": "partial" if gates else "available" if restriction == "free" and not unknown else "unknown",
        "restriction_evidence": gates + ([] if restriction == "free" else ["public_article:content_code=" + restriction]),
        "format_provenance": {"publisher_id": data["_id"], "unhandled_element_types": sorted(unknown),
            "embedded_scripts_executed": False},
        "publication_date_evidence": {"method": "public_first_publish_date" if stamp else "missing_original_post_date",
            "precision": "timestamp"}}
