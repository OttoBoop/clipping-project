"""HTML archives advertised as children of Exame's sitemap index."""
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser


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

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
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
        if self.current is not None:
            self.current[1].append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.rows.append((self.current[0], ' '.join(' '.join(self.current[1]).split())))
            self.current = None
        if tag in {'h2', 'h3'}:
            self.heading = False
        if tag == 'main':
            self.main = self.heading = False
            self.current = None


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
    if not parser.found_main:
        return expanded._result(outcome='gap', gap_reason='exame_html_archive_not_recognized')
    # These are the actual editorial cards; header/footer links are not news.
    rows = {}
    for href, title in parser.rows:
        link = urljoin(final_url, href)
        if expanded._allowed(link, source, article=True):
            rows.setdefault(link, title)
    fingerprint = expanded._fingerprint(rows)
    seen = cursor.get('page_fingerprints', [])
    if rows and fingerprint in seen:
        return expanded._result(outcome='gap', raw_count=len(rows), gap_reason='expanded_repeated_archive_page')
    offset = int(cursor.get('offset', 0))
    if offset and cursor.get('document_fingerprint') != fingerprint:
        return expanded._result(outcome='gap', raw_count=len(rows), gap_reason='expanded_archive_changed_during_resume')
    cap = min(expanded.MAX_BATCH, max(1, int(task.get('candidate_budget') or expanded.MAX_BATCH)))
    selected = list(rows.items())[offset:offset + cap]
    candidates = [expanded._candidate(source, link, title, metadata={
        'archive_url': final_url, 'archive_format': 'exame_editorial_html',
        'discovered_from_sitemap': task.get('ancestors', []),
    }) for link, title in selected]
    base = {**cursor, 'response_format': 'exame_editorial_html', 'url': url}
    if offset + cap < len(rows):
        return expanded._result(candidates, raw_count=len(selected), next_cursor={
            **base, 'offset': offset + cap, 'document_fingerprint': fingerprint})
    next_url = urljoin(final_url, parser.next_href) if parser.next_href else ''
    page = int(cursor.get('page', 1))
    if next_url:
        if not expanded._allowed(next_url, source) or next_url == final_url:
            return expanded._result(candidates, raw_count=len(selected), outcome='gap', gap_reason='exame_html_archive_invalid_next_page')
        if page >= expanded.MAX_PAGES:
            return expanded._result(candidates, raw_count=len(selected), outcome='gap', gap_reason='expanded_archive_page_cap')
        return expanded._result(candidates, raw_count=len(selected), next_cursor={
            'response_format': 'exame_editorial_html', 'url': next_url, 'page': page + 1,
            'page_fingerprints': (seen + [fingerprint])[-32:]})
    # A terminal HTML page does not prove the publisher's historical inventory.
    return expanded._result(candidates, raw_count=len(selected), outcome='gap',
                            gap_reason='expanded_archive_history_not_proven')
