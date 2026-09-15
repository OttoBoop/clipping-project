"""HTML archives advertised as children of Exame's sitemap index."""
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


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
    soup = BeautifulSoup(response.text, 'html.parser')
    main = soup.find('main')
    if main is None:
        return expanded._result(outcome='gap', gap_reason='exame_html_archive_not_recognized')
    # These are the actual editorial cards; header/footer links are not news.
    rows = {}
    for anchor in main.select('h2 a[href], h3 a[href]'):
        link = urljoin(final_url, anchor['href'])
        if expanded._allowed(link, source, article=True):
            rows.setdefault(link, anchor.get_text(' ', strip=True))
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
    next_anchor = main.select_one('a[rel~=next][href]')
    next_url = urljoin(final_url, next_anchor['href']) if next_anchor else ''
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
