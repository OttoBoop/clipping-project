"""Identity-bound editorial text from public Eldorado episode pages."""
import json
import re
from urllib.parse import urljoin, urlparse

from pipeline.http_utils import html_to_text
from .political_editorial_extraction import _date


def _state(raw, name):
    match = re.search(r"\bFusion\." + name + r"\s*=\s*", raw)
    if not match:
        return {}
    try:
        value, _ = json.JSONDecoder().raw_decode(raw[match.end():])
        return value if isinstance(value, dict) else {}
    except ValueError:
        return {}


def extract(raw, url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"estadao.com.br", "www.estadao.com.br"}:
        return None
    parts = parsed.path.strip("/").split("/")
    if len(parts) != 4 or parts[:2] != ["eldorado", "programas"]:
        return None
    page = _state(raw, "globalContent")
    params = page.get("params") or {}
    if (page.get("subtype") != "eldorado_programas_interna"
            or params.get("id") != parts[2] or params.get("edicaoId") != parts[3]):
        return None
    cache = _state(raw, "contentCache").get("eldorado") or {}
    expected_route = f"/api/program/{parts[2]}/edicoes/{parts[3]}"
    matches = []
    for key, entry in cache.items():
        try:
            query = json.loads(key)
        except (TypeError, ValueError):
            continue
        if not isinstance(query, dict) or query.get("requestUri") != expected_route:
            continue
        for item in entry.get("data") or []:
            if not isinstance(item, dict) or not item.get("_id"):
                continue
            canonical = urlparse(urljoin(url, item.get("canonical_url") or ""))
            if canonical.hostname == parsed.hostname and canonical.path.rstrip("/") == parsed.path.rstrip("/"):
                matches.append(item)
    if len(matches) != 1:
        return None
    episode = matches[0]
    text = []
    unknown = set()
    for element in episode.get("content_elements") or []:
        kind = element.get("type")
        if kind in {"text", "header"}:
            paragraph = html_to_text(element.get("content") or "").strip()
            if paragraph:
                text.append(paragraph)
        elif kind not in {"image", "audio", "divider"}:
            unknown.add(str(kind))
    body = "\n\n".join(text)
    stamp = _date(episode.get("first_publish_date") or "")
    restriction = (episode.get("content_restrictions") or {}).get("content_code", "")
    return {
        "title": (episode.get("headlines") or {}).get("basic", "").strip(),
        "canonical_url": urljoin(url, episode["canonical_url"]),
        "published_at": stamp,
        "full_text": body,
        "extraction_state": "full_text" if len(body.split()) >= 40 else "metadata_only",
        "extraction_method": "publisher_public_eldorado_episode_state",
        "extraction_version": "estadao-eldorado-1",
        "content_format": "radio_episode_text",
        "text_extent": "available" if body and restriction == "free" and not unknown else "unknown" if body else "absent",
        "restriction_evidence": [] if restriction == "free" else ["public_episode:content_code=" + restriction],
        "format_provenance": {"publisher_id": episode["_id"], "cache_route": expected_route,
            "unhandled_element_types": sorted(unknown), "audio_transcribed": False},
        "publication_date_evidence": {"method": "public_episode_first_publish_date" if stamp else "missing_original_post_date",
            "precision": "timestamp", "publisher_republish_date": episode.get("publish_date", "")},
    }
