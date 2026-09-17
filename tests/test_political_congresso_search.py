"""Real public search results, page dates and publisher pagination limitations."""
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from web_app import political_expanded_discovery as expanded
from web_app.political_discovery import DiscoveryError, extract_article

ROOT = Path(__file__).parent / 'fixtures/political_congresso_search'


def setup(capped=False, start='2026-06-01', end='2026-09-10'):
    source = next(s for s in expanded.load_expanded_sources() if s['key'] == 'congresso_em_foco')
    task = next(t for t in expanded.build_expanded_tasks(source, start, end,
        [{'key': 'eduardo_paes', 'display_name': 'Eduardo Paes'}]) if t['strategy'] == 'expanded_congresso_search')
    path = 'capped-public-search.json.gz' if capped else 'public-date-query.response.gz'
    raw = gzip.decompress((ROOT / path).read_bytes())
    proof = json.loads((ROOT / ('capped-provenance.json' if capped else 'public-date-query.json')).read_text())
    assert hashlib.sha256(raw).hexdigest() == proof['sha256']
    response = SimpleNamespace(content=raw, status_code=200, url=task['url'], headers={})
    return task, source, response


def test_real_date_query_keeps_eleven_candidates_and_never_calls_snippets_article_text():
    task, source, response = setup()
    calls = []
    def fetch(url, **kwargs):
        calls.append((url, kwargs));return response
    result = expanded.discover_expanded(task, source, fetch)
    assert result['outcome'] == 'complete' and len(result['candidates']) == 11
    assert len(calls) == 1 and calls[0][1]['method'] == 'POST'
    payload = json.loads(calls[0][1]['data'])
    assert payload['usertoken'] is None and payload['query'] == 'Eduardo Paes'
    assert payload['datefrom'] == '2026-06-01T00:00:00-03:00'
    assert payload['dateto'] == '2026-09-10T23:59:59.999999-03:00'
    assert all('full_text' not in c and 'body_html' not in c for c in result['candidates'])
    assert not result['publisher_search']['bodyTextProvided']
    first = result['candidates'][0]
    assert 'Eduardo Paes' not in first['title']
    raw = gzip.decompress((ROOT / 'date-check-0.html.gz').read_bytes())
    article = extract_article(raw.decode(), first['url'])
    assert 'eduardo paes' in article['full_text'].lower()
    assert article['published_at'] == first['published_at']


def test_primary_names_are_individual_and_unbounded_sitemap_is_deferred():
    _, source, _ = setup()
    rows = [{'key': 'paes', 'display_name': 'Eduardo Paes', 'exact_aliases': ['Paes']},
            {'key': 'portinho', 'display_name': 'Carlos Portinho'},
            {'key': 'waguinho', 'display_name': 'Waguinho'}]
    tasks = expanded.build_expanded_tasks(source, '2026-08-09', '2026-08-09', rows)
    searches = [t for t in tasks if t['strategy'] == 'expanded_congresso_search']
    assert [t['query'] for t in searches] == ['Eduardo Paes', 'Carlos Portinho', 'Waguinho']
    assert [t['target_ids'] for t in searches] == [['paes'], ['portinho'], ['waguinho']]
    assert not any(t['strategy'] == 'expanded_sitemap' for t in tasks)
    assert source['deferred_mechanisms'][0]['kind'] == 'sitemap'


def test_real_capped_search_splits_date_windows_without_assuming_complete_pagination():
    task, source, response = setup(capped=True)
    result = expanded.discover_expanded(task, source, lambda *a, **k: response)
    assert result['outcome'] == 'split' and result['raw_count'] == 500
    left, right = result['child_tasks']
    from datetime import date, timedelta
    assert left['date_from'] == task['date_from'] and right['date_to'] == task['date_to']
    assert date.fromisoformat(left['date_to']) + timedelta(days=1) == date.fromisoformat(right['date_from'])
    assert left['query'] == right['query'] == task['query']
    assert not result['publisher_search']['paginationUsed']
    # The historical probe omitted searchkey and repeated page one. It proves
    # that page alone is insufficient, not that publisher continuation is broken.
    pages = json.loads((ROOT / 'pagination.json').read_text())['rows']
    assert pages[0]['results'] == pages[1]['results']
    assert pages[1]['metrics']['page'] == 1


def test_single_day_saturation_and_ignored_dates_remain_visible_gaps():
    task, source, response = setup(capped=True, start='2026-08-09', end='2026-08-09')
    result = expanded.discover_expanded(task, source, lambda *a, **k: response)
    assert result['outcome'] == 'gap'
    assert 'single_day_limit' in result['gap_reason']
    assert 'ignored_date_filter' in result['gap_reason']
    assert not result['child_tasks'] and len(result['candidates']) <= 500


def test_http429_remains_retryable_with_publisher_retry_after():
    task, source, response = setup()
    response.status_code = 429;response.headers['Retry-After'] = '17'
    with pytest.raises(DiscoveryError) as failure:
        expanded.discover_expanded(task, source, lambda *a, **k: response)
    assert failure.value.retryable and failure.value.retry_after == 17


def test_unknown_date_survives_until_article_extraction():
    task, source, response = setup()
    document = json.loads(response.content)
    document['Data']['results'][0]['date'] = None
    response.content = json.dumps(document).encode()
    result = expanded.discover_expanded(task, source, lambda *a, **k: response)
    assert len(result['candidates']) == 11
    assert result['candidates'][0]['metadata']['needs_date_review']
    assert not result['candidates'][0]['published_at']


def test_google_disabled_for_new_jobs_fallback_and_legacy_tasks():
    from web_app import political_discovery as core
    task, source, _ = setup()
    people = [{'key': 'paes', 'display_name': 'Eduardo Paes'}]
    tasks = core.build_tasks(people, '2026-06-01', '2026-09-10',
                             ['congresso_em_foco'], [source])
    assert len([t for t in tasks if t['strategy'] == 'expanded_congresso_search']) == 1
    assert len([t for t in tasks if t['strategy'] == 'expanded_congresso_archive']) == 7
    assert not any(t['strategy'] == 'google_news' for t in tasks)
    assert core.fallback_tasks({**task, 'source_snapshot': source}, people) == []
    legacy = {**task, 'strategy': 'google_news', 'source_snapshot': source}
    def forbidden(*a, **k):
        pytest.fail('Google must never be requested')
    with pytest.raises(DiscoveryError, match='congresso_em_foco_google_disabled'):
        core.discover(legacy, forbidden)


@pytest.mark.parametrize('raw', [b'[]', b'{}', b'null', b'{"Code":0,"Data":{}}'])
def test_unrecognized_api_payload_is_not_an_empty_completed_search(raw):
    task, source, response = setup();response.content = raw
    with pytest.raises(DiscoveryError, match='invalid_result'):
        expanded.discover_expanded(task, source, lambda *a, **k: response)


def test_real_empty_public_search_is_verified_zero_not_a_parser_failure():
    task, source, response = setup()
    response.content = gzip.decompress((ROOT / 'real-empty-search.json.gz').read_bytes())
    proof = json.loads((ROOT / 'empty-provenance.json').read_text())
    assert hashlib.sha256(response.content).hexdigest() == proof['sha256']
    result = expanded.discover_expanded(task, source, lambda *a, **k: response)
    assert result['outcome'] == 'complete' and result['candidates'] == []
    assert result['publisher_search']['reportedResults'] == 0
