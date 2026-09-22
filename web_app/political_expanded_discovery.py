"""Publisher-advertised discovery for the gap-closure source catalogue.

All HTTP is delegated to the worker's shared transport. Article eligibility is
never decided by a headline here. Cursor batches are bounded to 500 candidates;
unknown dates survive for body/date extraction, and incomplete mechanisms end in
an explicit gap. The caller supplies the frozen source configuration.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

from pipeline.http_utils import canonicalize_url, html_to_text, is_likely_article_url

REGISTRY_PATH = Path(__file__).resolve().parents[1] / 'data' / 'political_sources_expansion_v1.json'
MAX_BATCH = 500
MAX_INDEX_BATCH = 100
MAX_INDEX_SCAN = 5000
MAX_DEPTH = 6
MAX_PAGES = 2000
VERSION = 'expanded-public-1'


def load_expanded_sources():
    return json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))['sources']


def _core():
    # Deferred import avoids a circular import when the main discovery module
    # dispatches expanded tasks. No live catalogue is read during a task.
    from . import political_discovery
    return political_discovery


def _result(candidates=(), *, next_cursor=None, outcome=None, raw_count=0, child_tasks=(), gap_reason='', **extra):
    return {'candidates': list(candidates), 'next_cursor': next_cursor,
            'outcome': outcome or ('continue' if next_cursor else 'complete'),
            'raw_count': raw_count, 'child_tasks': list(child_tasks), 'gap_reason': gap_reason, **extra}


def _allowed(url, source, article=False):
    parsed = urlparse(url)
    host = (parsed.hostname or '').lower().removeprefix('www.')
    domains = source.get('domains') or [source.get('domain', '')]
    if parsed.scheme not in ('https', 'http') or not host or not any(
        host == d.lower().removeprefix('www.') or host.endswith('.' + d.lower().removeprefix('www.'))
        for d in domains if d
    ):
        return False
    if not article:
        return True
    # Public WordPress numeric permalinks are explicitly supported by the
    # date-filtered API, without assuming every query URL is an article.
    if source.get('numeric_permalink') and re.fullmatch(r'\d+', parse_qs(parsed.query).get('p', [''])[0]):
        return True
    return is_likely_article_url(url)


def _candidate(source, url, title='', published='', snippet='', metadata=None):
    core = _core()
    return {'url': canonicalize_url(url), 'title': html_to_text(title),
            'source_key': source['key'], 'source_name': source['name'],
            'source_type': 'political_discovery', 'published_at': core.parse_publication_date(published),
            'snippet': html_to_text(snippet), 'metadata': {'discovery_adapter': VERSION,
            'needs_date_review': not bool(core.parse_publication_date(published)), **(metadata or {})}}


def _months(start, end):
    cur = start.replace(day=1)
    while cur <= end:
        yield cur
        cur = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)


def build_expanded_tasks(source, date_from, date_to, target_snapshots):
    start, end = date.fromisoformat(date_from), date.fromisoformat(date_to)
    if start > end:
        raise ValueError('date_to must be on or after date_from')
    base = {'source_key': source['key'], 'date_from': date_from, 'date_to': date_to,
            'target_ids': [str(r.get('key') or r.get('id')) for r in target_snapshots], 'cursor': {}}
    tasks = []
    for mechanism in source.get('mechanisms', []):
        kind = mechanism['kind']
        route = {**base, 'strategy': 'expanded_' + kind, 'mechanism': dict(mechanism)}
        if kind == 'daily_sitemap':
            for n in range((end - start).days + 1 + int(mechanism.get('calendar_tail_days', 0))):
                tasks.append({**route, 'day': (start + timedelta(days=n)).isoformat()})
        elif kind == 'monthly_archive':
            tasks.extend({**route, 'month': month.isoformat()[:7]} for month in _months(start, end))
        elif kind == 'wordpress':
            # Limit one response to 50 full bodies and each task to seven days.
            for first, last in _core().date_windows(date_from, date_to):
                tasks.append({**route, 'date_from': first, 'date_to': last})
        elif kind == 'congresso_archive':
            from .political_congresso_archive import build_tasks
            tasks.extend(build_tasks(route))
        elif kind == 'congresso_search':
            from .political_congresso_search import build_tasks
            tasks.extend(build_tasks(route, target_snapshots))
        elif kind in {'sitemap', 'feed', 'blogger_feed', 'archive', 'capability', 'edition_archive', 'metropoles_archive'}:
            tasks.append({**route, 'url': mechanism.get('url', ''), 'section': mechanism.get('section', ''), 'depth': 0, 'ancestors': []})
        else:
            raise ValueError('Unsupported expanded mechanism: ' + kind)
    return tasks


def _partition(url):
    """Calendar hints prune indexes, never become article publication dates."""
    q = parse_qs(urlparse(url).query)
    if all(k in q for k in ('yyyy', 'mm', 'dd')):
        try:
            d = date(int(q['yyyy'][0]), int(q['mm'][0]), int(q['dd'][0]))
            return d, d
        except ValueError:
            return None
    path = urlparse(url).path
    match = re.search(r'(?<!\d)((?:19|20)\d{2})[-/](\d{2})[-/](\d{2})(?!\d)', path)
    if match:
        try:
            d = date(*map(int, match.groups()))
            return d, d
        except ValueError:
            return None
    # Jota advertises annual directories with month-numbered leaves. Retain
    # the entire requested year conservatively; the numeric leaf is not used
    # as an article date or assumed to prove the contents of a whole month.
    if urlparse(url).hostname == 'sitemap.jota.info':
        match = re.fullmatch(r'/posts/((?:19|20)\d{2})/sitemap-post-\d+-\1\.xml', path)
        if match:
            year = int(match[1])
            return date(year, 1, 1), date(year, 12, 31)
    match = re.search(r'(?<!\d)((?:19|20)\d{2})[-/.]?(\d{1,2})(?:\.xml|/|$)', path)
    if match:
        try:
            d = date(int(match[1]), int(match[2]), 1)
            return d, (d.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        except ValueError:
            return None
    return None


def _fingerprint(urls):
    return hashlib.sha256('\n'.join(sorted(set(urls))).encode()).hexdigest()


def _skip_branch(url):
    # Taxonomy/author indexes are structural, not editorial text. Columns are
    # deliberately retained (unlike author landing-page taxonomies). Published
    # Web Stories are editorial HTML and must also reach body/date extraction.
    return _exame_topic_index(url) or bool(re.search(r'(?:sitemap[-_/](?:taxonomy|taxonomies|users|authors?|autor|tag|category)|/(?:autor|authors?|tags)/sitemap)', url, re.I))


def _exame_topic_index(url):
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return (parsed.hostname in {'exame.com', 'www.exame.com'}
            and bool(re.fullmatch(r'/noticias-sobre/(?:\d+/)?sitemap\.xml', parsed.path)))


def structural_exclusion(task, source):
    """Recognize the publisher's taxonomy indexes, including already queued ones."""
    if (source.get('key') == 'exame' and task.get('strategy') == 'expanded_sitemap'
            and int(task.get('depth', 0)) > 0 and _exame_topic_index(task.get('url', ''))):
        return {'url': task['url'], 'basis': 'publisher_topic_collection_sitemap',
                'http_requested': False, 'articles_modified': False}
    return None


def calendar_exclusion(task, source):
    """Prove an advertised child calendar is outside this frozen task window."""
    url = task.get('url', '')
    if task.get('strategy') != 'expanded_sitemap' or int(task.get('depth', 0)) <= 0 or not _allowed(url, source):
        return None
    partition = _partition(url)
    end = date.fromisoformat(task['date_to']) + timedelta(days=int((task.get('mechanism') or {}).get('calendar_tail_days', 0)))
    if partition and (partition[1] < date.fromisoformat(task['date_from']) or partition[0] > end):
        return {'url': url, 'from': partition[0].isoformat(), 'to': partition[1].isoformat(),
                'basis': 'publisher_sitemap_calendar_path', 'http_requested': False}
    return None


def _sitemap(task, source, fetch):
    core = _core()
    mechanism = task.get('mechanism') or {}
    cursor = dict(task.get('cursor') or {})
    from . import political_exame_archive
    exame_archive = political_exame_archive.is_advertised_archive(task, source)
    if exame_archive and cursor.get('response_format') == 'exame_editorial_html':
        return political_exame_archive.discover(task, source, fetch)
    page, offset = int(cursor.get('page', 1)), int(cursor.get('offset', 0))
    daily = task['strategy'] == 'expanded_daily_sitemap'
    if daily:
        day = date.fromisoformat(task['day'])
        url = mechanism['url_template'].format(yyyy=f'{day.year:04}', mm=f'{day.month:02}', dd=f'{day.day:02}', page=page)
    else:
        url = task['url']
    if not _allowed(url, source):
        raise core.DiscoveryError('expanded sitemap outside publisher domains', retryable=False)
    structural = structural_exclusion(task, source)
    if structural:
        return _result(structural_index_excluded=structural)
    # Recheck already queued children as well as newly traversed indexes.
    # Older workers did not recognize pre-2000 days or Jota's annual paths.
    # Preserve an explicit task result without requesting an irrelevant leaf.
    excluded = calendar_exclusion(task, source)
    if excluded:
        return _result(calendar_partition_excluded=excluded)
    response = core._get(fetch, url)
    if (exame_archive or (source.get('key') == 'exame' and source.get('archive_date_adapter')
                         and int(task.get('depth', 0)) > 0)) and response.text.lstrip().lower().startswith(('<!doctype html', '<html')):
        if offset or cursor.get('document_fingerprint'):
            return _result(outcome='gap', gap_reason='expanded_sitemap_kind_changed_during_resume')
        return political_exame_archive.discover(task, source, fetch, response=response)
    root = core._xml(response)
    kind = core._local(root.tag)
    nodes = list(root)
    if kind not in {'sitemapindex', 'urlset'}:
        raise core.DiscoveryError('expanded sitemap response is not a sitemap')
    if 'invalid_children' in cursor and kind != 'sitemapindex':
        return _result(outcome='gap', raw_count=len(nodes), gap_reason='expanded_sitemap_kind_changed_during_resume')
    fingerprint = _fingerprint(core._child_text(n, 'loc') for n in nodes)
    # A changed page may shift offsets: stop visibly instead of silently losing
    # rows or replaying a different partial document under an old cursor.
    if offset and cursor.get('document_fingerprint') not in (None, fingerprint):
        return _result(outcome='gap', raw_count=len(nodes), gap_reason='expanded_sitemap_changed_during_resume')
    cap = min(MAX_BATCH, max(1, int(task.get('candidate_budget') or MAX_BATCH)))
    if kind == 'sitemapindex':
        if int(task.get('depth', 0)) >= MAX_DEPTH:
            return _result(outcome='gap', raw_count=len(nodes), gap_reason='expanded_sitemap_depth_cap')
        batch = min(cap, MAX_INDEX_BATCH)
        children, invalid = [], int(cursor.get('invalid_children', 0))
        ancestors = list(task.get('ancestors') or []) + [url]
        start, end = date.fromisoformat(task['date_from']), date.fromisoformat(task['date_to']) + timedelta(days=int(mechanism.get('calendar_tail_days', 0)))
        seen = set()
        # Calendar filtering can reject thousands of old index branches. Scan
        # them in bounded CPU batches, without spending a worker lease for every
        # 100 rejected dates. The emitted child-task cap remains 100.
        scanned = 0
        for node in nodes[offset:offset + MAX_INDEX_SCAN]:
            scanned += 1
            child_url = core._child_text(node, 'loc')
            if _skip_branch(child_url) or child_url in seen:
                continue
            seen.add(child_url)
            if not _allowed(child_url, source) or child_url in ancestors:
                invalid += 1
                continue
            numbered = mechanism.get('numbered_part_pattern')
            if numbered:
                match = re.fullmatch(numbered, child_url)
                if not match or int(match['part']) < int(mechanism.get('minimum_numbered_part', 1)):
                    continue
            partition = _partition(child_url)
            if partition and (partition[1] < start or partition[0] > end):
                continue
            children.append({**task, 'strategy': 'expanded_sitemap', 'url': child_url,
                             'depth': int(task.get('depth', 0)) + 1, 'ancestors': ancestors, 'cursor': {},
                             'partition_hint': [x.isoformat() for x in partition] if partition else []})
            if len(children) >= batch:
                break
        next_cursor = {'offset': offset + scanned, 'document_fingerprint': fingerprint, 'invalid_children': invalid} if offset + scanned < len(nodes) else None
        residual = bool(mechanism.get('numbered_part_pattern')) and int(task.get('depth', 0)) == 0
        reasons = []
        if invalid:
            reasons.append('expanded_sitemap_invalid_or_cyclic_children')
        if residual:
            reasons.append('expanded_earlier_partitions_not_verified')
        return _result(child_tasks=children, next_cursor=next_cursor, raw_count=scanned,
                       outcome='gap' if reasons and not next_cursor else None,
                       gap_reason=';'.join(reasons) if not next_cursor else '')
    if page > 1 and offset == 0 and fingerprint in cursor.get('page_fingerprints', []):
        return _result(outcome='gap', raw_count=len(nodes), gap_reason='expanded_repeated_sitemap_page')
    candidates = []
    structural_entries = []
    for node in nodes[offset:offset + cap]:
        article_url = core._child_text(node, 'loc')
        if source.get('key') == 'exame' and source.get('archive_date_adapter'):
            basis = political_exame_archive.structural_listing(article_url, url)
            if basis:
                structural_entries.append({'url': article_url, 'basis': basis})
                continue
        if not _allowed(article_url, source, article=True):
            continue
        published = core._child_text(node, 'publication_date')
        if not core.in_window(published, task['date_from'], task['date_to']):
            continue
        # Store lastmod solely as a hint; never substitute it for publication or
        # silently exclude an undated story based on its modification timestamp.
        candidates.append(_candidate(source, article_url, core._sitemap_title(node), published,
            metadata={'sitemap_url': url, 'sitemap_lastmod_hint': core._child_text(node, 'lastmod'),
                      'partition_hint': task.get('partition_hint', []), 'discovery_day': task.get('day', '')}))
    if offset + cap < len(nodes):
        return _result(candidates, next_cursor={**cursor, 'offset': offset + cap, 'document_fingerprint': fingerprint}, raw_count=len(nodes[offset:offset + cap]), structural_entries=structural_entries)
    if daily and mechanism.get('pagination') == 'numbered' and nodes:
        if page >= int(mechanism.get('max_pages', MAX_PAGES)):
            return _result(candidates, outcome='gap', raw_count=len(nodes[offset:]), gap_reason='expanded_sitemap_page_cap')
        return _result(candidates, next_cursor={'page': page + 1, 'page_fingerprints': (cursor.get('page_fingerprints', []) + [fingerprint])[-32:]}, raw_count=len(nodes[offset:]))
    recent = mechanism.get('history_complete') is False or ('news' in urlparse(url).path.rsplit('/', 1)[-1])
    return _result(candidates, raw_count=len(nodes[offset:]), outcome='gap' if recent else None,
                   gap_reason='expanded_recent_sitemap_not_historical_inventory' if recent else '',
                   structural_entries=structural_entries)


def _wordpress(task, source, fetch):
    core = _core()
    mechanism, cursor = task['mechanism'], task.get('cursor') or {}
    page = int(cursor.get('page', 1))
    size = min(50, max(1, int(mechanism.get('page_size', 50))))
    params = {'page': page, 'per_page': size, 'orderby': 'date', 'order': 'desc',
              'after': (datetime.fromisoformat(task['date_from']) - timedelta(seconds=1)).isoformat(),
              'before': (date.fromisoformat(task['date_to']) + timedelta(days=1)).isoformat() + 'T00:00:00',
              '_fields': 'id,link,title,excerpt,date,date_gmt,content,modified_gmt'}
    root = mechanism['url']
    rest_base = mechanism.get('rest_base', 'posts')
    if not re.fullmatch('[a-z][a-z0-9_-]{0,63}', rest_base):
        raise core.DiscoveryError('invalid frozen WordPress rest base', retryable=False)
    endpoint = root + 'wp/v2/' + rest_base + '&' + urlencode(params) if 'rest_route=' in root else root.rstrip('/') + '/wp/v2/' + rest_base + '?' + urlencode(params)
    if not _allowed(endpoint, source):
        raise core.DiscoveryError('expanded API outside publisher domains', retryable=False)
    response = core._get(fetch, endpoint, allowed_statuses=(400,))
    try:
        payload = json.loads(response.text)
    except (ValueError, TypeError) as exc:
        raise core.DiscoveryError('expanded WordPress returned non-JSON') from exc
    if response.status_code == 400:
        if page > 1 and isinstance(payload, dict) and payload.get('code') == 'rest_post_invalid_page_number':
            return _result()
        raise core.DiscoveryError('expanded WordPress rejected date/page query', retryable=False, status_code=400)
    if not isinstance(payload, list):
        raise core.DiscoveryError('expanded WordPress did not return post list')
    fingerprint = _fingerprint(str(row.get('id')) + ':' + str(row.get('link')) for row in payload if isinstance(row, dict))
    if page > 1 and payload and fingerprint in cursor.get('page_fingerprints', []):
        return _result(outcome='gap', raw_count=len(payload), gap_reason='expanded_repeated_api_page')
    candidates, bodies = [], []
    outside = 0
    for row in payload:
        if not isinstance(row, dict):
            continue
        published = core.parse_publication_date(row.get('date_gmt') or row.get('date', ''), naive_zone=timezone.utc if row.get('date_gmt') else core.SAO_PAULO)
        if not core.in_window(published, task['date_from'], task['date_to']):
            outside += 1
            continue
        url = str(row.get('link') or '')
        if not _allowed(url, source, article=True):
            continue
        rendered = lambda value: value.get('rendered', '') if isinstance(value, dict) else str(value or '')
        metadata = {'wordpress_id': row.get('id'), 'wordpress_rest_base': rest_base, 'collection_mode': 'date_scan'}
        if source.get('numeric_permalink') and parse_qs(urlparse(url).query).get('p'):
            metadata['wordpress_numeric_permalink_verified'] = True
        candidate = _candidate(source, url, rendered(row.get('title')), published, rendered(row.get('excerpt')), metadata)
        candidates.append(candidate)
        content = row.get('content')
        if published and isinstance(content, dict) and isinstance(content.get('rendered'), str) and type(row.get('id')) is int:
            bodies.append({'post_id': row['id'], 'url': candidate['url'], 'published_at': published,
                           'content_html': content['rendered'], 'protected': content.get('protected') is not False,
                           'modified_gmt': str(row.get('modified_gmt') or '')})
    try:
        total_raw = response.headers.get('X-WP-TotalPages') or response.headers.get('x-wp-totalpages')
        total = int(total_raw) if total_raw is not None else None
    except (TypeError, ValueError) as exc:
        raise core.DiscoveryError('invalid expanded API total pages') from exc
    has_next = page < total if total is not None else len(payload) >= size
    gap = 'expanded_api_ignored_date_filter' if outside else 'expanded_api_page_cap' if has_next and page >= MAX_PAGES else ''
    result = _result(candidates, raw_count=len(payload), next_cursor={'page': page + 1,
        'page_fingerprints': (cursor.get('page_fingerprints', []) + [fingerprint])[-32:]} if has_next and not gap else None,
        outcome='gap' if gap else None, gap_reason=gap)
    if bodies:
        result['body_batch'] = {'source_key': source['key'], 'records': bodies}
    return result


class _Links(HTMLParser):
    def __init__(self, base):
        super().__init__(convert_charrefs=True)
        self.base, self.links, self.feeds, self.next_url = base, [], [], ''
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'link' and attrs.get('type') in {'application/rss+xml', 'application/atom+xml'}:
            self.feeds.append(urljoin(self.base, attrs.get('href', '')))
        if tag in {'link', 'a'} and 'next' in attrs.get('rel', '').split():
            self.next_url = urljoin(self.base, attrs.get('href', ''))
        if tag == 'a' and attrs.get('href'):
            self.current = [urljoin(self.base, attrs['href']), '']

    def handle_data(self, data):
        if self.current is not None:
            self.current[1] += data

    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            if self.current[1].strip().casefold() in {'›', 'próximo', 'próxima', 'próxima página', 'ver mais', 'mais notícias...', 'older posts', 'next'}:
                self.next_url = self.current[0]
            self.links.append(tuple(self.current))
            self.current = None


def _feed(task, source, fetch):
    core, mechanism = _core(), task['mechanism']
    cursor = task.get('cursor') or {}
    page = int(cursor.get('page', 1))
    url = cursor.get('url') or task['url']
    if mechanism.get('pagination') == 'wordpress_paged' and page > 1:
        parts = urlparse(task['url'])
        params = parse_qs(parts.query)
        params['paged'] = [str(page)]
        url = urlunparse(parts._replace(query=urlencode(params, doseq=True)))
    if not _allowed(url, source):
        raise core.DiscoveryError('expanded feed outside publisher domains', retryable=False)
    response = core._get(fetch, url)
    root = core._xml(response)
    if core._local(root.tag) not in {'rss', 'feed', 'RDF'}:
        raise core.DiscoveryError('expanded feed did not return RSS or Atom')
    entries = [n for n in root.iter() if core._local(n.tag) in {'item', 'entry'}]
    candidates, urls, dates = [], [], []
    for node in entries[:MAX_BATCH]:
        link = core._child_text(node, 'link') or next((n.get('href', '') for n in node if core._local(n.tag) == 'link' and n.get('rel', 'alternate') == 'alternate'), '')
        link = urljoin(url, link)
        urls.append(link)
        published = core._child_text(node, 'pubDate') or core._child_text(node, 'published')
        dates.append(core.parse_publication_date(published))
        if _allowed(link, source, article=True) and core.in_window(published, task['date_from'], task['date_to']):
            candidates.append(_candidate(source, link, core._child_text(node, 'title'), published,
                              core._child_text(node, 'description') or core._child_text(node, 'summary'),
                              {'feed_url': url, 'feed_content_available': bool(core._child_text(node, 'encoded') or core._child_text(node, 'content'))}))
    fingerprint = _fingerprint(urls)
    seen = cursor.get('page_fingerprints', [])
    if entries and fingerprint in seen:
        return _result(outcome='gap', raw_count=len(entries), gap_reason='expanded_repeated_feed_page')
    body_batch = None
    if mechanism.get('public_body_batch'):
        from .political_access_alternatives import parse_public_feed
        parsed = parse_public_feed(response.content, url, source)
        candidates = [c for c in parsed['candidates'] if core.in_window(c.get('published_at', ''), task['date_from'], task['date_to'])]
        selected = {c['url'] for c in candidates}
        body_batch = {**parsed['body_batch'], 'records': [r for r in parsed['body_batch']['records'] if r['url'] in selected]}
    next_url = next((urljoin(url, n.get('href', '')) for n in root.iter() if core._local(n.tag) == 'link' and n.get('rel') == 'next'), '')
    if len(entries) > MAX_BATCH:
        result = _result(candidates, raw_count=len(entries), outcome='gap', gap_reason='expanded_feed_candidate_cap')
    elif mechanism.get('pagination') == 'wordpress_paged':
        parsed_dates = [datetime.fromisoformat(d) for d in dates if d]
        ordered = len(parsed_dates) == len(entries) and all(a >= b for a, b in zip(parsed_dates, parsed_dates[1:]))
        previous = cursor.get('oldest_publication')
        if previous and parsed_dates and max(parsed_dates) > datetime.fromisoformat(previous):
            ordered = False
        chronology_gap = bool(cursor.get('chronology_gap')) or (bool(entries) and not ordered)
        start = datetime.fromisoformat(task['date_from']).replace(tzinfo=core.SAO_PAULO)
        older = bool(parsed_dates) and ordered and max(parsed_dates) < start
        older_pages = int(cursor.get('older_pages', 0)) + 1 if older else 0
        unknown_dates = int(cursor.get('unknown_dates', 0)) + sum(not d for d in dates)
        if not entries or (older_pages >= 2 and not chronology_gap):
            gap = 'expanded_feed_unknown_publication_dates' if unknown_dates else ''
            result = _result(candidates, raw_count=len(entries), outcome='gap' if gap else None, gap_reason=gap)
        elif page >= int(mechanism.get('max_pages', MAX_PAGES)):
            result = _result(candidates, raw_count=len(entries), outcome='gap', gap_reason='expanded_feed_page_cap')
        elif older_pages >= 10 and chronology_gap:
            result = _result(candidates, raw_count=len(entries), outcome='gap', gap_reason='expanded_feed_chronology_not_proven')
        else:
            result = _result(candidates, raw_count=len(entries), next_cursor={'page': page + 1,
                'page_fingerprints': (seen + [fingerprint])[-32:], 'older_pages': older_pages,
                'oldest_publication': min(parsed_dates).isoformat() if parsed_dates else previous,
                'chronology_gap': chronology_gap, 'unknown_dates': unknown_dates})
    elif next_url and _allowed(next_url, source) and page < MAX_PAGES:
        result = _result(candidates, raw_count=len(entries), next_cursor={'url': next_url, 'page': page + 1, 'page_fingerprints': (seen + [fingerprint])[-32:]})
    else:
        result = _result(candidates, raw_count=len(entries), outcome='gap',
                        gap_reason='expanded_feed_page_cap' if next_url else 'expanded_feed_history_not_proven')
    if body_batch and body_batch['records']:
        result['body_batch'] = body_batch
    return result


def _archive(task, source, fetch):
    core, mechanism = _core(), task['mechanism']
    cursor = task.get('cursor') or {}
    url = cursor.get('url') or task.get('url')
    if task['strategy'] == 'expanded_monthly_archive' and not url:
        year, month = task['month'].split('-')
        url = mechanism['url_template'].format(yyyy=year, mm=month)
    if not _allowed(url, source):
        raise core.DiscoveryError('expanded archive outside publisher domains', retryable=False)
    response = core._get(fetch, url)
    parser = _Links(getattr(response, 'url', '') or url)
    parser.feed(response.text)
    rows = list(dict.fromkeys((u, t.strip()) for u, t in parser.links if _allowed(u, source, article=True)))
    fingerprint = _fingerprint(u for u, _ in rows)
    seen = cursor.get('page_fingerprints', [])
    if rows and fingerprint in seen:
        return _result(outcome='gap', raw_count=len(rows), gap_reason='expanded_repeated_archive_page')
    offset = int(cursor.get('offset', 0))
    if offset and cursor.get('document_fingerprint') != fingerprint:
        return _result(outcome='gap', raw_count=len(rows), gap_reason='expanded_archive_changed_during_resume')
    candidates = [_candidate(source, u, t, metadata={'archive_url': url}) for u, t in rows[offset:offset + MAX_BATCH]]
    if offset + MAX_BATCH < len(rows):
        return _result(candidates, raw_count=len(rows[offset:offset + MAX_BATCH]), next_cursor={**cursor, 'url': url, 'offset': offset + MAX_BATCH, 'document_fingerprint': fingerprint})
    page = int(cursor.get('page', 1))
    if parser.next_url and _allowed(parser.next_url, source) and page < MAX_PAGES:
        return _result(candidates, raw_count=len(rows[offset:]), next_cursor={'url': parser.next_url, 'page': page + 1, 'page_fingerprints': (seen + [fingerprint])[-32:]})
    return _result(candidates, raw_count=len(rows[offset:]), outcome='gap',
                   gap_reason='expanded_archive_page_cap' if parser.next_url else 'expanded_archive_history_not_proven')


def _capability(task, source, fetch):
    # A source without an advertised working historical mechanism still gets a
    # reproducible direct attempt, followed by an explicit gap and Google fallback.
    result = _archive(task, source, fetch)
    if not result.get('next_cursor'):
        result.update(outcome='gap', gap_reason='expanded_direct_historical_mechanism_unconfirmed')
    return result


def discover_expanded(task, source, fetch):
    strategy = task['strategy']
    if strategy == 'expanded_congresso_archive':
        from .political_congresso_archive import discover
        return discover(task, source, fetch)
    if strategy == 'expanded_congresso_search':
        from .political_congresso_search import discover
        return discover(task, source, fetch)
    if strategy in {'expanded_sitemap', 'expanded_daily_sitemap'}:
        return _sitemap(task, source, fetch)
    if strategy == 'expanded_wordpress':
        return _wordpress(task, source, fetch)
    if strategy == 'expanded_blogger_feed':
        from .political_blogger_feed import discover_blogger_feed
        return discover_blogger_feed(task, source, fetch)
    if strategy == 'expanded_feed':
        return _feed(task, source, fetch)
    if strategy in {'expanded_archive', 'expanded_monthly_archive'}:
        return _archive(task, source, fetch)
    if strategy == 'expanded_capability':
        return _capability(task, source, fetch)
    if strategy == 'expanded_metropoles_archive':
        return _metropoles_current(task, source, fetch)
    if strategy == 'expanded_edition_archive':
        from .political_document_tasks import discover_edition_archive
        return discover_edition_archive(task, source, fetch)
    raise _core().DiscoveryError('unsupported expanded discovery strategy', retryable=False)


def _metropoles_current(task, source, fetch):
    """Use currently advertised assets; a still-served old bundle can be stale.

    On2026-09-14 the old static bundle returned200 while its action returned404.
    Renew only this discovery action, keeping the saved historical date cursor.
    """
    from .political_metropoles_archive import ASSET, ACTION, discover_archive
    core = _core()
    mechanism = task.get('mechanism') or {}
    slug = mechanism.get('section') or task.get('section') or 'brasil'
    if slug not in source.get('public_archive_sections', []):
        raise core.DiscoveryError('metropoles_archive_invalid_section', retryable=False)
    cursor = dict(task.get('cursor') or {})
    # Brasil advertises the shared public pagination action; the Colunas
    # landing page does not include that JavaScript bundle. The same action
    # was verified against the Colunas aggregator in a real publisher POST.
    action_page = source.get('public_archive_action_page') or slug
    if action_page not in source.get('public_archive_sections', []):
        raise core.DiscoveryError('metropoles_action_page_not_in_frozen_sections', retryable=False)
    page_url = 'https://www.metropoles.com/' + action_page
    if not cursor.get('action_id'):
        assets = cursor.get('action_assets')
        if assets is None:
            response = core._get(fetch, page_url)
            assets = list(reversed(list(dict.fromkeys(ASSET.findall(response.text)))))
            if not assets:
                return _result(outcome='gap', gap_reason='metropoles_current_public_assets_missing')
            return _result(next_cursor={**cursor, 'action_assets': assets[:64], 'asset_index': 0,
                                        'action_page': page_url, 'asset_cap_hit': len(assets) > 64})
        index = int(cursor.get('asset_index', 0))
        if index >= len(assets):
            return _result(outcome='gap', gap_reason='metropoles_current_action_asset_cap' if cursor.get('asset_cap_hit') else 'metropoles_current_public_action_not_found')
        asset = assets[index]
        if not ASSET.fullmatch(asset):
            raise core.DiscoveryError('metropoles_unadvertised_action_asset', retryable=False)
        response = core._get(fetch, asset, allowed_statuses=(404,))
        found = ACTION.search(response.text) if response.status_code == 200 else None
        return _result(next_cursor={**cursor, **({'action_id': found.group(1), 'action_asset': asset} if found else {'asset_index': index + 1})})
    try:
        result = discover_archive({**task, 'section': slug}, {**source, 'public_archive_action_bundle_hint': ''}, fetch)
    except core.DiscoveryError as exc:
        refreshes = int(cursor.get('action_refresh_count', 0))
        if exc.status_code not in {404, 410}:
            raise
        if refreshes >= 2:
            return _result(outcome='gap', gap_reason='metropoles_public_action_refresh_exhausted')
        renewed = {k:v for k,v in cursor.items() if k not in {'action_id','action_assets','asset_index','action_asset','asset_cap_hit'}}
        renewed['action_refresh_count'] = refreshes + 1
        renewed['stale_action_id'] = cursor['action_id']
        return _result(next_cursor=renewed)
    if result.get('next_cursor'):
        result['next_cursor'] = {**{k:v for k,v in cursor.items() if k in {'action_page','action_asset','action_refresh_count'}}, **result['next_cursor']}
    return result
