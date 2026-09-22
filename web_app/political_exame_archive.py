"""HTML archives advertised as children of Exame's sitemap index."""
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser
from datetime import datetime
import json
import re


def structural_listing(url, sitemap_url):
    """Publisher directory entries are not individual editorial articles.

    This does not reject undated article slugs. It recognizes the exact section
    root advertised in category indexes and the observed directories/products.
    Their linked reporting remains discoverable through dated article families;
    this exclusion does not certify those families' completeness.
    """
    parsed, origin = urlparse(url), urlparse(sitemap_url)
    if parsed.hostname not in {'exame.com', 'www.exame.com'} or origin.hostname not in {'exame.com', 'www.exame.com'}:
        return ''
    path = parsed.path.rstrip('/')
    if origin.path == '/static/sitemap.xml':
        return 'publisher_static_directory'
    if path.startswith(('/edicoes/', '/canais-especiais/', '/pagina-especial/')):
        return 'publisher_edition_or_product_listing'
    if origin.path == '/eventos-especiais/sitemap.xml' and path.startswith('/especiais/'):
        return 'publisher_event_listing'
    if origin.path.startswith('/categorias/') and origin.path.endswith('/sitemap.xml'):
        section = origin.path.removeprefix('/categorias').removesuffix('/sitemap.xml')
        if path == section:
            return 'publisher_category_self_entry'
    return ''


class _EditorialCards(HTMLParser):
    """Use the worker's standard library, including for sparse archive HTML."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.main = False
        self.found_main = False
        self.heading = False
        self.current = None
        self.rows = []
        self.next_href = ''
        self.scripts = []
        self.script_parts = None
        self.canonical = ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'link' and 'canonical' in (attrs.get('rel') or '').split():
            self.canonical = attrs.get('href', '')
        if tag == 'script':
            self.script_parts = []
        if tag == 'main':
            self.main = self.found_main = True
        if not self.main:
            return
        if tag in {'h2', 'h3'}:
            self.heading = True
        if tag == 'a' and attrs.get('href'):
            if 'next' in (attrs.get('rel') or '').split() and not self.next_href:
                self.next_href = attrs['href']
            if self.heading:
                self.current = [attrs['href'], []]

    def handle_data(self, data):
        if self.script_parts is not None:
            self.script_parts.append(data)
        if self.current is not None:
            self.current[1].append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.script_parts is not None:
            self.scripts.append(''.join(self.script_parts))
            self.script_parts = None
        if tag == 'a' and self.current is not None:
            self.rows.append((self.current[0], ' '.join(' '.join(self.current[1]).split())))
            self.current = None
        if tag in {'h2', 'h3'}:
            self.heading = False
        if tag == 'main':
            self.main = self.heading = False
            self.current = None


def public_archive_dates(parser, rows, core):
    """Read published hydration JSON as data, bound to every visible card URL.

    No JavaScript evaluation or guessed API. Relative UI dates are never used.
    A foreign/recommended post array cannot date this archive's candidates.
    """
    def normalize(u):
        parsed = urlparse(u)
        # The actual video page renders exame.com links while postsData retains
        # classic.exame.com. Only this observed publisher alias is equivalent.
        if parsed.hostname in {'exame.com', 'www.exame.com', 'classic.exame.com'}:
            return 'https://exame.com' + parsed.path.rstrip('/')
        return u.rstrip('/')
    wanted = {normalize(u) for u in rows}
    if not wanted:
        return None
    for script in parser.scripts:
        prefix = 'self.__next_f.push('
        if not script.startswith(prefix):
            continue
        try:
            frame = json.loads(script[len(prefix):].rstrip().removesuffix(';').removesuffix(')'))
        except (TypeError, ValueError):
            continue
        if not isinstance(frame, list) or len(frame) < 2 or not isinstance(frame[1], str):
            continue
        value = frame[1]
        for match in re.finditer(r'"postsData"\s*:\s*', value):
            try:
                posts, end = json.JSONDecoder().raw_decode(value[match.end():])
            except ValueError:
                continue
            if not isinstance(posts, list) or not posts or not all(isinstance(x, dict) for x in posts):
                continue
            links = [normalize(str(x.get('link') or '')) for x in posts]
            if len(links) != len(set(links)) or set(links) != wanted:
                continue
            dates = [core.parse_publication_date(x.get('date', '')) for x in posts]
            if not all(dates):
                continue
            tail = value[match.end() + end:match.end() + end + 1000]
            total = re.search(r'"totalPages"\s*:\s*(\d+)', tail)
            pages = re.findall(r'"page"\s*:\s*(\d+)', value[max(0, match.start()-500):match.start()])
            return {'dates': dict(zip(links, dates)), 'ordered': all(a >= b for a,b in zip(dates, dates[1:])),
                    'page': int(pages[-1]) if pages else None,
                    'total_pages': int(total[1]) if total else None}
    return None


def is_advertised_archive(task, source):
    return (
        source.get('key') == 'exame'
        and task.get('strategy') == 'expanded_sitemap'
        and int(task.get('depth', 0)) > 0
        and urlparse(task.get('url', '')).hostname in {'exame.com', 'www.exame.com'}
        and not urlparse(task.get('url', '')).path.endswith('.xml')
    )


def discover(task, source, fetch, response=None):
    from . import political_expanded_discovery as expanded

    core = expanded._core()
    cursor = task.get('cursor') or {}
    url = cursor.get('url') or task['url']
    if not expanded._allowed(url, source):
        raise core.DiscoveryError('Exame archive outside publisher domains', retryable=False)
    if response is None:
        response = core._get(fetch, url)
    final_url = getattr(response, 'url', '') or url
    if not expanded._allowed(final_url, source):
        raise core.DiscoveryError('Exame archive redirected outside publisher domains', retryable=False)
    parser = _EditorialCards()
    parser.feed(response.text)
    if parser.canonical and urlparse(parser.canonical).path in ('', '/') and urlparse(url).path not in ('', '/'):
        return expanded._result(outcome='gap', gap_reason='exame_archive_returns_homepage')
    if not parser.found_main:
        return expanded._result(outcome='gap', gap_reason='exame_html_archive_not_recognized')
    # These are the actual editorial cards; header/footer links are not news.
    rows = {}
    for href, title in parser.rows:
        link = urljoin(final_url, href)
        if expanded._allowed(link, source, article=True):
            rows.setdefault(link, title)
    dated = public_archive_dates(parser, rows, core) if source.get('archive_date_adapter') else None
    fingerprint = expanded._fingerprint(rows)
    seen = cursor.get('page_fingerprints', [])
    if rows and fingerprint in seen:
        return expanded._result(outcome='gap', raw_count=len(rows), gap_reason='expanded_repeated_archive_page')
    offset = int(cursor.get('offset', 0))
    if offset and cursor.get('document_fingerprint') != fingerprint:
        return expanded._result(outcome='gap', raw_count=len(rows), gap_reason='expanded_archive_changed_during_resume')
    cap = min(expanded.MAX_BATCH, max(1, int(task.get('candidate_budget') or expanded.MAX_BATCH)))
    selected = list(rows.items())[offset:offset + cap]
    candidates = [expanded._candidate(source, link, title,
        published=dated['dates'][link.rstrip('/')] if dated else '', metadata={
        'archive_url': final_url, 'archive_format': 'exame_editorial_html',
        'archive_publication_basis': 'publisher_postsData_date' if dated else 'unknown',
        'discovered_from_sitemap': task.get('ancestors', []),
    }) for link, title in selected
        if not dated or core.in_window(dated['dates'][link.rstrip('/')], task['date_from'], task['date_to'])]
    base = {**cursor, 'response_format': 'exame_editorial_html', 'url': url}
    if offset + cap < len(rows):
        return expanded._result(candidates, raw_count=len(selected), next_cursor={
            **base, 'offset': offset + cap, 'document_fingerprint': fingerprint})
    next_url = urljoin(final_url, parser.next_href) if parser.next_href else ''
    page = int(cursor.get('page', 1))
    if dated and dated['page'] not in (None, page):
        return expanded._result(outcome='gap', raw_count=len(rows), gap_reason='exame_archive_page_identity_mismatch')
    # Publication order is checked on the complete visible page, not a filtered
    # set of name/title matches. Retain this boundary as explicit evidence.
    if dated and dated['ordered'] and all(datetime.fromisoformat(d).astimezone(core.SAO_PAULO).date().isoformat() < task['date_from'] for d in dated['dates'].values()):
        return expanded._result(candidates, raw_count=len(selected), archive_boundary={
            'basis': 'publisher_card_publication_dates_descending', 'page': page,
            'newest_publication': max(dated['dates'].values()),
            'oldest_publication': min(dated['dates'].values()),
            'remaining_pages': max(0, (dated['total_pages'] or page)-page)})
    if next_url:
        if not expanded._allowed(next_url, source) or next_url == final_url:
            return expanded._result(candidates, raw_count=len(selected), outcome='gap', gap_reason='exame_html_archive_invalid_next_page')
        if page >= expanded.MAX_PAGES:
            return expanded._result(candidates, raw_count=len(selected), outcome='gap', gap_reason='expanded_archive_page_cap')
        return expanded._result(candidates, raw_count=len(selected), next_cursor={
            'response_format': 'exame_editorial_html', 'url': next_url, 'page': page + 1,
            'page_fingerprints': (seen + [fingerprint])[-32:]})
    # A terminal HTML page does not prove the publisher's historical inventory.
    if dated and dated['total_pages'] == page:
        return expanded._result(candidates, raw_count=len(selected), archive_terminal={
            'basis': 'publisher_totalPages_and_card_identity', 'page': page})
    return expanded._result(candidates, raw_count=len(selected), outcome='gap',
                            gap_reason='expanded_archive_history_not_proven')
