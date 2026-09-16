"""IstoÉ's direct, bounded sitemap inventory. No search-engine fallback.

Lastmod orders body work, never becomes a publication date. Older undated URLs
remain durable deferred observations and explicit coverage gaps, not exclusions.
"""
from __future__ import annotations

import hashlib
import re
from datetime import date
from urllib.parse import urlparse

VERSION = "istoe_direct_v1"
INDEX = "https://istoe.com.br/wp-sitemap.xml"
PART = re.compile(r"https://istoe\.com\.br/wp-sitemap-posts-post-(\d+)\.xml")


def allowed(url):
    p = urlparse(url)
    return p.scheme in {"https", "http"} and p.hostname in {"istoe.com.br", "www.istoe.com.br"} and not p.username and not p.password


def build_task(base, source):
    return {**base, "strategy": VERSION, "adapter_version": VERSION, "url": INDEX,
            "inventory_part_budget": min(100, max(1, int(source.get("inventory_part_budget", 32))))}


def discover(task, source, fetch):
    from .political_discovery import DiscoveryError, _get, _xml, _local, _child_text, _result
    from .political_expanded_discovery import _candidate
    if task.get("adapter_version") != VERSION:
        raise DiscoveryError("istoe_adapter_version_unavailable", retryable=False)
    url = task["url"]
    if url != INDEX and not PART.fullmatch(url):
        raise DiscoveryError("istoe_discovery_url_not_allowed", retryable=False)
    response = _get(fetch, url)
    if not allowed(response.url):
        raise DiscoveryError("istoe_redirect_outside_portal", retryable=False)
    root = _xml(response)
    kind = _local(root.tag)
    cursor = dict(task.get("cursor") or {})
    digest = hashlib.sha256(response.content).hexdigest()
    if cursor.get("sha256") and cursor["sha256"] != digest:
        raise DiscoveryError("istoe_snapshot_changed", retryable=False)
    offset = int(cursor.get("offset", 0))
    if url == INDEX:
        if kind != "sitemapindex":
            raise DiscoveryError("istoe_expected_sitemap_index", retryable=False)
        parts = sorted(set(_child_text(n, "loc") for n in root if PART.fullmatch(_child_text(n, "loc"))),
                       key=lambda u: int(PART.fullmatch(u)[1]), reverse=True)
        if not parts:
            raise DiscoveryError("istoe_empty_post_index", retryable=False)
        budget = min(100, max(1, int(task.get("inventory_part_budget", 32))))
        chosen = parts[offset:offset + budget]
        children = [{**task, "url": u, "cursor": {}, "inventory_part": int(PART.fullmatch(u)[1])} for u in chosen]
        next_offset = offset + len(chosen)
        remaining = max(0, len(parts) - next_offset)
        return {**_result(child_tasks=children, raw_count=len(chosen),
                 outcome="gap" if remaining else "complete",
                 next_cursor={"offset": next_offset, "sha256": digest},
                 gap_reason="istoe_inventory_batch_limit" if remaining else ""),
                "istoe_inventory": {"partsTotal": len(parts), "partsAdmitted": next_offset,
                                    "partsRemaining": remaining, "googleRequests": 0}}
    if kind != "urlset":
        raise DiscoveryError("istoe_expected_urlset", retryable=False)
    nodes = list(root)
    if offset > len(nodes):
        raise DiscoveryError("istoe_invalid_cursor", retryable=False)
    cap = min(500, max(1, int(task.get("candidate_budget") or 500)))
    candidates, deferred, invalid = [], int(cursor.get("deferred", 0)), int(cursor.get("invalid", 0))
    for node in nodes[offset:offset + cap]:
        article_url = _child_text(node, "loc")
        if not allowed(article_url):
            invalid += 1
            continue
        modified = _child_text(node, "lastmod")
        try:
            older_hint = date.fromisoformat(modified[:10]) < date.fromisoformat(task["date_from"])
        except ValueError:
            older_hint = False
        metadata = {"discovery_adapter": VERSION, "sitemap_url": url,
                    "sitemap_snapshot_hash": digest, "sitemap_lastmod_hint": modified,
                    "publication_status": "unverified", "body_deferred": older_hint}
        # Every URL survives into the inventory/observations. Older hints are
        # explicitly deferred until publication evidence or requested recovery.
        candidates.append({**_candidate(source, article_url, metadata=metadata),
                           "istoe_defer_body": older_hint})
        deferred += int(older_hint)
    end = offset + min(cap, len(nodes) - offset)
    next_cursor = {"offset": end, "sha256": digest, "deferred": deferred, "invalid": invalid}
    done = end >= len(nodes)
    reason = "istoe_unverified_older_urls" if deferred else "istoe_invalid_urls" if invalid else ""
    return {**_result(candidates, raw_count=end - offset, next_cursor=next_cursor,
             outcome=("gap" if reason else "complete") if done else "continue", gap_reason=reason if done else ""),
            "istoe_inventory": {"entries": len(nodes), "entriesRead": end,
                                "deferredDates": deferred, "invalidUrls": invalid}}
