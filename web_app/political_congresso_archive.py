"""Dated public editorial archives, shared across people; no search-engine fallback.

Only the named editorial widget is read. Related/sidebar lists never provide
candidates. Reported archive dates select candidates; article pages confirm them.
"""
from datetime import date, datetime, timedelta
import hashlib
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse

VERSION = 'congresso-editorial-archive-2'
PRODUCTS = {'noticia': 'NOTICIAS_LISTA', 'artigo': 'ARTIGOS_LISTA',
            'coluna': 'COLUNAS_LISTA', 'informativo': 'INFORMATIVO_LISTA'}
BASE = 'https://www.congressoemfoco.com.br/'
MAX_ROWS = 100


class _StateScript(HTMLParser):
    """Read only the SSR JSON using the standard-library production runtime."""
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.inside = False
        self.count = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('id') == 'ng-state':
            self.inside = True
            self.count += 1

    def handle_endtag(self, tag):
        if tag == 'script':
            self.inside = False

    def handle_data(self, data):
        if self.inside:
            self.parts.append(data)


def _state(raw):
    parser = _StateScript()
    parser.feed(raw.decode('utf-8'))
    parser.close()
    if parser.count != 1:
        raise ValueError('single SSR state required')
    return json.loads(''.join(parser.parts))


def build_tasks(route):
    mechanism = route['mechanism']
    product = mechanism.get('product')
    if product not in PRODUCTS or mechanism.get('url') != BASE + product:
        raise ValueError('congresso_archive_invalid_route')
    if product == 'informativo':
        month = date.fromisoformat(route['date_from']).replace(day=1)
        end = date.fromisoformat(route['date_to'])
        tasks = []
        while month <= end:
            tasks.append({**route, 'url': mechanism['url'], 'month': month.isoformat()[:7]})
            month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
        return tasks
    return [{**route, 'url': mechanism['url']}]


def _widget(state, code, *, page=None, month=None):
    from .political_discovery import DiscoveryError
    prefix = 'key_/Widget/Get_' + code + '_' + code + '_'
    found = []
    for key, value in state.items():
        if not key.startswith(prefix):
            continue
        # Require the actual SSR context, not merely a query in the request URL.
        if page is not None and not re.search(r'\bpagenumber:' + str(page) + r'\b', key):
            continue
        if month is not None and not (re.search(r'\bmonth:' + str(month.month) + r'\b', key)
                                      and re.search(r'\byear:' + str(month.year) + r'\b', key)):
            continue
        if not isinstance(value, dict) or value.get('Code') != 0:
            raise DiscoveryError('congresso_archive_widget_error', retryable=False)
        data = value.get('Data')
        if not isinstance(data, dict) or data.get('code') != code or not isinstance(data.get('widgetassets'), list):
            raise DiscoveryError('congresso_archive_invalid_widget', retryable=False)
        found.append(data)
    if len(found) != 1:
        raise DiscoveryError('congresso_archive_context_missing', retryable=False)
    if len(found[0]['widgetassets']) > MAX_ROWS:
        raise DiscoveryError('congresso_archive_row_limit', retryable=False)
    return found[0]


def discover(task, source, fetch):
    from . import political_expanded_discovery as expanded
    core = expanded._core()
    mechanism = task['mechanism']
    product = mechanism.get('product')
    if source.get('key') != 'congresso_em_foco' or product not in PRODUCTS or mechanism.get('url') != BASE + product:
        raise core.DiscoveryError('congresso_archive_invalid_route', retryable=False)
    cursor = task.get('cursor') or {}
    page = int(cursor.get('page', 1))
    if page < 1:
        raise core.DiscoveryError('congresso_archive_invalid_page', retryable=False)
    month = date.fromisoformat(task['month'] + '-01') if product == 'informativo' else None
    params = {'month': month.month, 'year': month.year} if month else {'pagina': page}
    url = mechanism['url'] + '?' + urlencode(params)
    response = core._get(fetch, url)
    final = urlparse(getattr(response, 'url', '') or url)
    if final.hostname != 'www.congressoemfoco.com.br' or final.path.rstrip('/') != '/' + product:
        raise core.DiscoveryError('congresso_archive_redirected', retryable=False)
    try:
        state = _state(response.content)
    except (ValueError, TypeError) as exc:
        raise core.DiscoveryError('congresso_archive_state_missing', retryable=False) from exc
    if not isinstance(state, dict):
        raise core.DiscoveryError('congresso_archive_invalid_state', retryable=False)
    data = _widget(state, PRODUCTS[product], page=None if month else page, month=month)
    rows = list(data['widgetassets'])
    # The newest headline is a separate editorial widget on the news archive.
    featured = []
    if product == 'noticia' and page == 1:
        value = state.get('key_/Widget/Get_NOTICIAS_LISTA_NOTICIA_PRINCIPAL') or {}
        featured = (value.get('Data') or {}).get('widgetassets') or []
        if not isinstance(featured, list) or len(featured) > 10:
            raise core.DiscoveryError('congresso_archive_invalid_featured', retryable=False)
    urls, dates, candidates, invalid, unknown = [], [], [], 0, 0
    start, end = date.fromisoformat(task['date_from']), date.fromisoformat(task['date_to'])
    outside_month = 0
    for position, entry in enumerate(rows + featured):
        asset = entry.get('asset') if isinstance(entry, dict) else None
        if not isinstance(asset, dict):
            invalid += 1
            continue
        article_url = (((asset.get('href') or {}).get('address') or {}).get('absoluteuri') or '')
        parsed = urlparse(article_url)
        if (parsed.hostname != 'www.congressoemfoco.com.br' or parsed.scheme != 'https'
                or not re.fullmatch('/' + product + r'/\d+/[^/?]+', parsed.path)):
            invalid += 1
            continue
        published = core.parse_publication_date(asset.get('pubdate'))
        day = datetime.fromisoformat(published).astimezone(core.SAO_PAULO).date() if published else None
        if position < len(rows):
            urls.append(article_url)
            if day:
                dates.append(day)
            else:
                unknown += 1
            if month and day and (day.year, day.month) != (month.year, month.month):
                outside_month += 1
        if day and not start <= day <= end:
            continue
        candidates.append(expanded._candidate(source, article_url, asset.get('title', ''), published,
            asset.get('summary', ''), {'discovery_format': VERSION, 'record_product': product,
                'archive_url': url, 'archive_reported_pubdate': asset.get('pubdate'),
                'archive_response_hash': hashlib.sha256(response.content).hexdigest(),
                'archive_widget': PRODUCTS[product], 'archive_featured': position >= len(rows)}))
    fingerprint = hashlib.sha256('\n'.join(urls).encode()).hexdigest()
    previous = cursor.get('fingerprints') or []
    repeated = bool(urls) and fingerprint in previous
    pages = int(cursor.get('pages_read', 0)) + 1
    invalid += int(cursor.get('invalid_rows', 0))
    ordering_bad = bool(cursor.get('ordering_unverified')) or any(a < b for a, b in zip(dates, dates[1:]))
    if dates and cursor.get('previous_newest') and max(dates).isoformat() > cursor['previous_newest']:
        ordering_bad = True
    all_older = bool(rows) and len(dates) == len(rows) and all(d < start for d in dates)
    old_pages = int(cursor.get('older_pages', 0)) + 1 if all_older and not ordering_bad else 0
    proof = {'version': VERSION, 'product': product, 'url': url, 'page': page if not month else None,
             'month': task.get('month'), 'pagesRead': pages, 'rows': len(rows),
             'invalidRows': invalid, 'unknownDatesThisPage': unknown,
             'oldestReportedDate': min(dates).isoformat() if dates else None,
             'newestReportedDate': max(dates).isoformat() if dates else None,
             'olderPages': old_pages, 'orderingUnverified': ordering_bad,
             'responseHash': hashlib.sha256(response.content).hexdigest(), 'fingerprint': fingerprint,
             'candidateCount': len(candidates), 'headlineMatchingUsed': False}
    reasons = []
    if invalid:
        reasons.append('congresso_archive_invalid_rows')
    if repeated:
        reasons.append('congresso_archive_repeated_page')
    if outside_month:
        reasons.append('congresso_archive_month_mismatch')
    complete = bool(month) or not rows or old_pages >= 2
    if not complete and page >= min(400, int(mechanism.get('max_pages', 400))):
        reasons.append('congresso_archive_page_cap')
    if repeated or outside_month or 'congresso_archive_page_cap' in reasons or complete:
        proof['stoppedBy'] = 'month' if month else 'empty_page' if not rows else 'dated_boundary' if old_pages >= 2 else 'gap'
        return expanded._result(candidates, raw_count=len(rows) + len(featured),
            outcome='gap' if reasons else 'complete', gap_reason=';'.join(reasons), publisher_archive=proof,
            archive_response=response.content)
    next_cursor = {'page': page + 1, 'pages_read': pages, 'fingerprints': (previous + [fingerprint])[-400:],
                   'older_pages': old_pages, 'invalid_rows': invalid, 'ordering_unverified': ordering_bad,
                   'previous_newest': max(dates).isoformat() if dates else cursor.get('previous_newest')}
    return expanded._result(candidates, raw_count=len(rows) + len(featured), next_cursor=next_cursor,
                            publisher_archive=proof, archive_response=response.content)
