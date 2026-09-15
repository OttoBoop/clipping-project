"""Public metadata lookup for URLs already discovered, never new discovery.

Endpoints and slug/date fields were verified on each publisher's advertised
WordPress API. An unknown URL or a failed lookup always keeps normal fetching.
"""
from datetime import datetime, timezone
import hashlib
import json
import re
import time
from urllib.parse import unquote, urlencode, urlsplit

ENDPOINTS = {
    'ponte_jornalismo': ('ponte.org', 'https://ponte.org/wp-json/wp/v2/posts'),
    'lupa': ('agencialupa.org', 'https://www.agencialupa.org/wp-json/wp/v2/posts'),
}
VERSION = 'public-wordpress-slug-dates-1'
MAX_URLS = 500
MAX_SLUGS = 20
MAX_REQUEST_BYTES = 4096
MAX_RESPONSE_BYTES = 512 * 1024


def _identity(url, host):
    try:
        p = urlsplit(str(url))
    except ValueError:
        return None
    if (p.scheme not in {'http', 'https'} or p.netloc.lower() not in {host, 'www.' + host} or p.query):
        return None
    return p.path.rstrip('/')


def _request(endpoint, slugs):
    return endpoint + '?' + urlencode({'slug': ','.join(slugs), 'per_page': 100,
        '_fields': 'id,link,slug,date,date_gmt,modified_gmt'})


def lookup(source_key, candidates, fetch, save_response):
    """Return hash-backed date facts for exact URLs only, at most 25 requests.

This reads no article bodies. It does not infer dates from modification fields,
claim a complete API inventory, or treat a missing result as a missing article.
"""
    stats = {'version': VERSION, 'requests': 0, 'matchedURLs': 0, 'responseBytes': 0,
             'fallback': '', 'durationMs': 0}
    if source_key not in ENDPOINTS:
        return {}, stats
    host, endpoint = ENDPOINTS[source_key]
    by_slug = {}
    for c in candidates[:MAX_URLS]:
        if c.get('force_refresh') or c.get('document_type'):
            continue
        url = c.get('url', '')
        identity = _identity(url, host)
        if not identity:
            continue
        slug = unquote(identity.rsplit('/', 1)[-1])
        if not re.fullmatch(r'[\w-]+', slug) or len(_request(endpoint, [slug]).encode()) > MAX_REQUEST_BYTES:
            continue
        by_slug.setdefault(slug, {})[identity] = url
    batches, current = [], []
    for slug in by_slug:
        if current and (len(current) >= MAX_SLUGS or len(_request(endpoint, current + [slug]).encode()) > MAX_REQUEST_BYTES):
            batches.append(current)
            current = []
        current.append(slug)
    if current:
        batches.append(current)
    stats['unqueriedBatches'] = max(0, len(batches) - 25)
    facts = {}
    started = time.monotonic()
    for slugs in batches[:25]:
        api_url = _request(endpoint, slugs)
        stats['requests'] += 1
        try:
            response = fetch(api_url)
            if response.status_code != 200:
                stats['fallback'] = 'http_' + str(response.status_code)
                break
            final = urlsplit(getattr(response, 'url', '') or api_url)
            if final.hostname is None or final.hostname.removeprefix('www.') != host:
                stats['fallback'] = 'response_domain_mismatch'
                break
            raw = response.content
            if not isinstance(raw, bytes) or len(raw) > MAX_RESPONSE_BYTES:
                stats['fallback'] = 'response_size_limit'
                break
            stats['responseBytes'] += len(raw)
            rows = json.loads(raw)
            if not isinstance(rows, list) or len(rows) > 100:
                stats['fallback'] = 'response_not_bounded_posts'
                break
            matched, conflicts = {}, set()
            for row in rows:
                if not isinstance(row, dict) or type(row.get('id')) is not int or row['id'] <= 0:
                    continue
                slug = row.get('slug')
                if slug not in slugs or row.get('status', 'publish') != 'publish':
                    continue
                identity = _identity(row.get('link', ''), host)
                url = by_slug[slug].get(identity)
                date_value = row.get('date_gmt')
                if not url or not isinstance(date_value, str) or not re.match(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d', date_value):
                    continue
                try:
                    published = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                except (ValueError, TypeError, AttributeError):
                    continue
                published = (published.replace(tzinfo=timezone.utc) if published.tzinfo is None
                             else published.astimezone(timezone.utc))
                if url in matched and matched[url][0] != published:
                    conflicts.add(url)
                matched[url] = (published, row['id'])
            for url in conflicts:
                matched.pop(url, None)
            if not matched:
                stats['fallback'] = 'no_exact_url_dates'
                break
            try:
                digest, key = save_response(raw)
            except Exception as exc:
                stats['fallback'] = 'evidence_storage_failed:' + type(exc).__name__
                break
            if digest != hashlib.sha256(raw).hexdigest() or not key:
                stats['fallback'] = 'evidence_hash_mismatch'
                break
            for url, (published, post_id) in matched.items():
                facts[url] = (published, 'api_verified', {
                    'method': VERSION, 'field': 'date_gmt', 'api_url': api_url,
                    'response_hash': digest, 'response_object_key': key,
                    'publisher_post_id': post_id, 'verified_article_url': url})
        except Exception as exc:
            # This optimization cannot consume the normal article retry budget.
            stats['fallback'] = type(exc).__name__
            break
    stats['matchedURLs'] = len(facts)
    stats['durationMs'] = round((time.monotonic() - started) * 1000, 2)
    return facts, stats
