"""Última Hora's dated public archive; discovery never filters names or titles."""
from datetime import date
from urllib.parse import urljoin, urlparse, parse_qs
import hashlib
import re

from .political_nf_archive import Document, MONTHS

VERSION = 'ultima-public-archive-2'
BASE = 'https://www.ultimahoraonline.com.br'


def article_url(value):
    url = urljoin(BASE, value)
    p = urlparse(url)
    return url if p.scheme == 'https' and p.hostname == 'www.ultimahoraonline.com.br' and re.fullmatch(r'/noticia/[^/]+', p.path) and not p.query else ''


def parse_page(html, url):
    root = Document(html).root
    rows = []
    for card in root.find('a', cls='bl-noticia'):
        u = article_url(card.attrs.get('href', ''))
        if not u:
            continue
        dates = card.find(cls='bl-noticia-data')
        titles = card.find(cls='bl-noticia-titulo') or card.find(cls='bloco-noticias-dest-tit')
        stamp = re.fullmatch(r'(\d{1,2}) de ([\wç]+) de (\d{4})', dates[0].text().lower() if dates else '')
        try:
            day = date(int(stamp[3]), MONTHS[stamp[2]], int(stamp[1])).isoformat() if stamp else ''
        except (ValueError, KeyError):
            day = ''
        rows.append({'url': u, 'title': titles[0].text() if titles else card.text(), 'date': day,
                     'undated_highlight': card.has('bloco-noticias-dest') and not dates})
    nav = root.find(cls='pagination')
    info = {'page': 1, 'last_page': None, 'next_url': '', 'pagination_found': bool(nav),
            'empty_message': 'Não há registros a serem exibidos.' in root.text()}
    if nav:
        active = nav[0].find(cls='active')
        match = re.match(r'(\d+)', active[0].text()) if active else None
        info['page'] = int(match[1]) if match else 0
        for a in nav[0].find('a'):
            label = a.attrs.get('aria-label')
            u = urljoin(url, a.attrs.get('href', ''))
            if label == 'Next':
                info['next_url'] = u
            if label == 'Last':
                try:
                    info['last_page'] = int(parse_qs(urlparse(u).query)['p'][0])
                except (KeyError, ValueError):
                    pass
    return rows, info



def discover_columns(task, source, fetch):
    from . import political_expanded_discovery as expanded
    url = task['mechanism'].get('url')
    if source['key'] != 'ultima_hora_online' or url != BASE + '/colunistas':
        raise expanded._core().DiscoveryError('ultima_columns_invalid_index', retryable=False)
    response = expanded._core()._get(fetch, url)
    raw = response.content
    root = Document(raw.decode('utf8', 'replace')).root
    urls = sorted({urljoin(BASE, a.attrs.get('href', '')) for a in root.find('a')
        if re.fullmatch(re.escape(BASE) + r'/colunista-noticias/\d+', urljoin(BASE, a.attrs.get('href', '')))})
    proof = {'adapter': VERSION, 'url': url, 'responseHash': hashlib.sha256(raw).hexdigest(), 'authorCount': len(urls)}
    if not urls or len(urls) > 500:
        return expanded._result(outcome='gap', gap_reason='ultima_columns_index_unrecognized_or_capped',
            publisher_archive=proof, archive_response=raw)
    children = [{**task, 'strategy': 'expanded_ultima_archive', 'url': u, 'cursor': {},
        'mechanism': {'kind': 'ultima_archive', 'url': u, 'max_pages': task['mechanism'].get('max_pages', 2000)}} for u in urls]
    return expanded._result(child_tasks=children, raw_count=len(urls), publisher_archive=proof, archive_response=raw)

def valid_route(url, path):
    p = urlparse(url)
    q = parse_qs(p.query)
    return (p.scheme == 'https' and p.hostname == 'www.ultimahoraonline.com.br' and p.path == path
            and set(q) <= {'p'} and (not q or len(q['p']) == 1 and q['p'][0].isdigit() and int(q['p'][0]) > 0))


def discover(task, source, fetch):
    from . import political_expanded_discovery as expanded
    core = expanded._core()
    mechanism = task['mechanism']
    route = mechanism.get('url', '')
    path = urlparse(route).path
    if source['key'] != 'ultima_hora_online' or not (path == '/noticias' or re.fullmatch(r'/colunista-noticias/\d+', path)):
        raise core.DiscoveryError('ultima_archive_invalid_route', retryable=False)
    cursor = task.get('cursor') or {}
    url = cursor.get('url') or route
    if not valid_route(url, path):
        raise core.DiscoveryError('ultima_archive_invalid_url', retryable=False)
    response = core._get(fetch, url)
    raw = response.content
    if not valid_route(getattr(response, 'url', url), path):
        raise core.DiscoveryError('ultima_archive_redirected', retryable=False)
    rows, info = parse_page(raw.decode('utf8', 'replace'), url)
    proof = {'adapter': VERSION, 'url': url, 'responseHash': hashlib.sha256(raw).hexdigest(), **info}
    def finish(candidates=(), **kwargs):
        return expanded._result(candidates, raw_count=len(rows), publisher_archive=proof, archive_response=raw, **kwargs)
    expected = int(cursor.get('page', 1))
    if info['page'] != expected:
        return finish(outcome='gap', gap_reason='ultima_archive_wrong_page')
    fingerprint = hashlib.sha256('\n'.join(r['url'] for r in rows).encode()).hexdigest()
    seen = cursor.get('fingerprints', [])
    if rows and fingerprint in seen:
        return finish(outcome='gap', gap_reason='ultima_archive_repeated_page')
    if len(rows) > 500:
        return finish(outcome='gap', gap_reason='ultima_archive_candidate_cap')
    dates = [r['date'] for r in rows if r['date']]
    unknown = sum(not r['date'] and not r['undated_highlight'] for r in rows)
    start, end = task['date_from'], task['date_to']
    candidates = [expanded._candidate(source, r['url'], r['title'], r['date'], metadata={
        'discovery_format': VERSION, 'archive_url': url, 'archive_reported_date': r['date'],
        'archive_response_hash': proof['responseHash'], 'undated_archive_highlight': r['undated_highlight']})
        for r in rows if not r['date'] or start <= r['date'] <= end]
    unordered = bool(cursor.get('unordered')) or any(a < b for a, b in zip(dates, dates[1:])) or bool(
        dates and cursor.get('previous_oldest') and max(dates) > cursor['previous_oldest'])
    # Undated hero cards are fetched even on the two older boundary pages.
    # They never acquire dates inferred from surrounding cards.
    older = bool(dates) and not unknown and max(dates) < start
    older_pages = int(cursor.get('older_pages', 0)) + 1 if older else 0
    unknown_total = int(cursor.get('unknown_dates', 0)) + unknown
    proof.update(raw_rows=len(rows), candidates=len(candidates), oldest=min(dates) if dates else None,
                 newest=max(dates) if dates else None, unordered=unordered, older_pages=older_pages,
                 undated_highlights=sum(r['undated_highlight'] for r in rows), unknown_dates=unknown,
                 boundary_basis='two_older_dated_pages_with_separately_fetched_undated_heroes')
    gap = ''
    if not rows:
        gap = '' if info['empty_message'] and expected == 1 and path != '/noticias' else 'ultima_archive_empty_unproven'
    elif older_pages >= 2 and not unordered:
        gap = 'ultima_archive_unknown_dates' if unknown_total else ''
    elif not info['next_url']:
        gap = ('ultima_archive_next_missing' if info['last_page'] and info['last_page'] > expected
               else '' if info['pagination_found'] else 'ultima_archive_pagination_missing')
    elif not valid_route(info['next_url'], path) or parse_qs(urlparse(info['next_url']).query).get('p') != [str(expected+1)]:
        gap = 'ultima_archive_next_invalid'
    elif expected >= int(mechanism.get('max_pages', 2000)):
        gap = 'ultima_archive_page_cap'
    elif older_pages >= 10 and unordered:
        gap = 'ultima_archive_chronology_unproven'
    else:
        return finish(candidates, next_cursor={'url': info['next_url'], 'page': expected+1,
            'fingerprints': (seen+[fingerprint])[-32:], 'previous_oldest': min(dates) if dates else cursor.get('previous_oldest'),
            'older_pages': older_pages, 'unordered': unordered, 'unknown_dates': unknown_total})
    return finish(candidates, outcome='gap' if gap else 'complete', gap_reason=gap)
