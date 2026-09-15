"""Replay publisher HTML preserved from the production worker; no archive writes."""
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from web_app import political_expanded_discovery as expanded

FIXTURES = Path(__file__).parent / 'fixtures' / 'political_exame_archive'


def response(name):
    row = next(r for r in json.loads((FIXTURES / 'provenance.json').read_text())['responses'] if r['evidence'] == name)
    raw = gzip.decompress((FIXTURES / name).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == row['sha256']
    return SimpleNamespace(content=raw, text=raw.decode(), url=row['url'], status_code=200, headers={'Content-Type': row['contentType']})


def setup(name='first-0.response.gz'):
    r = response(name)
    source = next(s for s in expanded.load_expanded_sources() if s['key'] == 'exame')
    task = expanded.build_expanded_tasks(source, '2026-08-09', '2026-08-09', [{'key': 'eduardo_paes'}])[0]
    task.update(url=r.url, depth=1, ancestors=['https://exame.com/sitemap.xml'])
    return task, source, r


@pytest.mark.parametrize('name', ['first-0.response.gz', 'first-1.response.gz'])
def test_real_html_children_yield_cards_in_one_request_without_relative_dates(name):
    task, source, r = setup(name)
    calls = []
    def fetch(url):
        calls.append(url)
        return r
    result = expanded.discover_expanded(task, source, fetch)
    assert calls == [r.url]
    assert len(result['candidates']) == 25
    assert result['next_cursor']['url'] == r.url + '2/'
    assert all(not c['published_at'] and c['metadata']['needs_date_review'] for c in result['candidates'])
    assert all(c['metadata']['archive_format'] == 'exame_editorial_html' for c in result['candidates'])
    assert not any('/login' in c['url'] or '/assine' in c['url'] for c in result['candidates'])


def test_real_second_page_resumes_serialized_cursor_and_reports_unproven_history():
    task, source, r = setup()
    first = expanded.discover_expanded(task, source, lambda url: r)
    task['cursor'] = json.loads(json.dumps(first['next_cursor']))
    second_response = response('next-0.response.gz')
    calls = []
    def fetch(url):
        calls.append(url)
        return second_response
    second = expanded.discover_expanded(task, source, fetch)
    assert calls == [second_response.url]
    assert len(second['candidates']) == 7
    assert not ({c['url'] for c in first['candidates']} & {c['url'] for c in second['candidates']})
    assert second['next_cursor'] is None
    assert second['gap_reason'] == 'expanded_archive_history_not_proven'


def test_real_page_batches_respect_remaining_capacity_and_detect_repeated_page():
    task, source, r = setup()
    task['candidate_budget'] = 10
    found = []
    for expected in (10, 10, 5):
        result = expanded.discover_expanded(task, source, lambda url: r)
        assert len(result['candidates']) == expected
        found.extend(c['url'] for c in result['candidates'])
        task['cursor'] = json.loads(json.dumps(result['next_cursor']))
    assert len(found) == len(set(found)) == 25
    repeated = expanded.discover_expanded(task, source, lambda url: r)
    assert repeated['gap_reason'] == 'expanded_repeated_archive_page'


def test_preexisting_xml_cursor_cannot_be_reinterpreted_as_html_offset():
    task, source, r = setup()
    task['cursor'] = {'offset': 100, 'document_fingerprint': 'previous-xml'}
    result = expanded.discover_expanded(task, source, lambda url: r)
    assert result['gap_reason'] == 'expanded_sitemap_kind_changed_during_resume'
    assert not result['candidates']


def test_bounded_html_cursor_reuses_hash_checked_cache_then_fetches_next_page(tmp_path):
    from web_app.political_sitemap_cache import PaginatedSitemapCache
    task, source, r = setup()
    task['candidate_budget'] = 10
    second = response('next-0.response.gz')
    calls = []
    def fetch(url):
        calls.append(url)
        return second if url == second.url else r
    for _ in range(3):
        cache = PaginatedSitemapCache(fetch, task.get('cursor'), directory=tmp_path)
        result = expanded.discover_expanded(task, source, cache.fetch)
        task['cursor'] = json.loads(json.dumps(cache.checkpoint(result['next_cursor'])))
    assert calls == [r.url]
    cache = PaginatedSitemapCache(fetch, task['cursor'], directory=tmp_path)
    result = expanded.discover_expanded(task, source, cache.fetch)
    assert calls == [r.url, second.url]
    assert len(result['candidates']) == 7


def test_html_fallback_is_scoped_to_exame_advertised_children():
    from web_app.political_exame_archive import is_advertised_archive
    task, source, _ = setup()
    assert is_advertised_archive(task, source)
    assert not is_advertised_archive({**task, 'depth': 0}, source)
    assert not is_advertised_archive(task, {**source, 'key': 'jota'})
    assert not is_advertised_archive({**task, 'url': 'https://other.example/archive/'}, source)
