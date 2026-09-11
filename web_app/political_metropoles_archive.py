"""Public 'Ver mais notícias' pagination, with a durable publication cursor."""
import json
import re
from datetime import date, datetime, timedelta
from urllib.parse import urljoin, urlparse

ASSET = re.compile(r'https://assets-v4\.metroimg\.com/_next/static/chunks/[A-Za-z0-9_-]+\.js')
ACTION = re.compile(r'createServerReference\)\("([0-9a-f]{40,64})",[^;]{0,250}?"getMoreArticlesAction"')


def discover_archive(task, source, fetch):
    from .political_discovery import (
        DiscoveryError, SAO_PAULO, _candidate, _get, _result, in_window, parse_publication_date,
    )
    slug = task.get('section', 'brasil')
    if slug not in source.get('public_archive_sections', []):
        raise DiscoveryError('metropoles_archive_invalid_section', retryable=False)
    url = 'https://www.metropoles.com/' + slug
    cursor = dict(task.get('cursor') or {})
    if not cursor.get('action_id'):
        assets = cursor.get('action_assets')
        if assets is None:
            hint = source.get('public_archive_action_bundle_hint', '')
            if ASSET.fullmatch(hint):
                response = _get(fetch, hint, allowed_statuses=(404,))
                found = ACTION.search(response.text) if response.status_code == 200 else None
                if found:
                    return _result(next_cursor={**cursor, 'action_id': found.group(1)})
            page = _get(fetch, url)
            assets = list(dict.fromkeys(ASSET.findall(page.text)))[:32]
            return _result(next_cursor={**cursor, 'action_assets': assets, 'asset_index': 0})
        index = int(cursor.get('asset_index', 0))
        if index >= len(assets):
            return _result(outcome='gap', gap_reason='metropoles_public_action_not_found')
        asset = assets[index]
        if not ASSET.fullmatch(asset):
            raise DiscoveryError('metropoles_invalid_public_asset', retryable=False)
        response = _get(fetch, asset, allowed_statuses=(404,))
        found = ACTION.search(response.text) if response.status_code == 200 else None
        return _result(next_cursor={**cursor, **({'action_id': found.group(1)} if found else {'asset_index': index + 1})})

    # The publisher's displayed date/cursor is local São Paulo time.
    after = cursor.get('after') or (date.fromisoformat(task['date_to']) + timedelta(days=1)).isoformat() + ' 00:00:00'
    page_number = int(cursor.get('page', 1))
    if page_number > int(source.get('public_archive_max_pages', 2000)):
        return _result(outcome='gap', gap_reason='metropoles_public_archive_page_cap')
    response = _get(fetch, url, method='POST',
        data=json.dumps([{'startAfter': after, 'slug': slug}]),
        headers={'Next-Action': cursor['action_id'], 'Accept': 'text/x-component',
                 'Content-Type': 'text/plain;charset=UTF-8', 'Origin': 'https://www.metropoles.com', 'Referer': url})
    rows = None
    for line in response.text.splitlines():
        _, separator, value = line.partition(':')
        if not separator:
            continue
        try:
            decoded = json.loads(value)
        except ValueError:
            continue
        if isinstance(decoded, dict) and isinstance(decoded.get('data'), list):
            rows = decoded['data']
            break
    if rows is None or len(rows) > 500:
        raise DiscoveryError('metropoles_invalid_public_archive_response', retryable=False)
    if not rows:
        return _result(outcome='gap' if cursor.get('parse_gap') else 'complete',
                       gap_reason='metropoles_archive_chronology_or_parse_gap' if cursor.get('parse_gap') else '')
    candidates, times = [], []
    malformed = False
    for row in rows:
        if not isinstance(row, dict):
            malformed = True
            continue
        published = parse_publication_date((row.get('authority') or {}).get('publishedAt'))
        if published:
            times.append(datetime.fromisoformat(published).astimezone(SAO_PAULO))
        else:
            malformed = True
        href = urljoin(url, str(row.get('url') or row.get('href') or ''))
        if urlparse(href).scheme != 'https' or urlparse(href).hostname not in {'www.metropoles.com', 'metropoles.com'} or not (row.get('url') or row.get('href')):
            malformed = True
            continue
        if in_window(published, task['date_from'], task['date_to']):
            candidates.append(_candidate(source, href, row.get('title', ''), published, row.get('subtitle', ''),
                {'metropoles_public_archive': slug, 'publisher_article_id': row.get('id'), 'needs_date_review': not bool(published)}))
    if not times:
        return _result(candidates, raw_count=len(rows), outcome='gap', gap_reason='metropoles_archive_missing_dates')
    oldest = min(times)
    next_after = oldest.strftime('%Y-%m-%d %H:%M:%S')
    if next_after >= after:
        return _result(candidates, raw_count=len(rows), outcome='gap', gap_reason='metropoles_archive_stalled_cursor')
    uncertain = bool(cursor.get('parse_gap')) or malformed or times != sorted(times, reverse=True)
    if oldest.date() < date.fromisoformat(task['date_from']):
        return _result(candidates, raw_count=len(rows), outcome='gap' if uncertain else 'complete',
                       gap_reason='metropoles_archive_chronology_or_parse_gap' if uncertain else '')
    return _result(candidates, raw_count=len(rows), next_cursor={
        'action_id': cursor['action_id'], 'after': next_after, 'page': page_number + 1, 'parse_gap': uncertain,
    })
