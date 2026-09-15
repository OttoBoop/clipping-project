"""Real publisher API metadata, frozen with page-date readback provenance."""
from datetime import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest

from web_app.political_public_date_batches import lookup

FIXTURES = Path(__file__).parent / 'fixtures' / 'political_public_dates'


def case(source):
    row = next(r for r in json.loads((FIXTURES / 'provenance.json').read_text())['rows'] if r['source'] == source)
    raw = gzip.decompress((FIXTURES / row['evidence']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == row['sha256']
    return row, SimpleNamespace(content=raw, status_code=200, url=row['url'])


@pytest.mark.parametrize('source', ['ponte_jornalismo', 'lupa'])
def test_exact_real_urls_and_dates_match_twenty_page_readbacks(source):
    row, response = case(source)
    calls, stored = [], []
    def fetch(url):
        calls.append(url)
        return response
    def save(raw):
        stored.append(raw)
        return hashlib.sha256(raw).hexdigest(), 'immutable-evidence.json.gz'
    facts, stats = lookup(source, [{'url': r['observed_url']} for r in row['references']], fetch, save)
    assert len(calls) == len(stored) == 1
    assert len(facts) == stats['matchedURLs'] == 20
    for r in row['references']:
        published, status, evidence = facts[r['observed_url']]
        assert published == datetime.fromisoformat(r['verified_at'])
        assert status == 'api_verified'
        assert evidence['field'] == 'date_gmt'
        assert evidence['response_hash'] == row['sha256']
        assert evidence['verified_article_url'] == r['observed_url']


def test_unmatched_or_foreign_urls_never_get_dates_from_unrelated_posts():
    row, response = case('ponte_jornalismo')
    candidate = row['references'][0]['observed_url']
    urls = [candidate.replace('ponte.org', 'another.example'), candidate + '/unrelated-slug']
    facts, stats = lookup('ponte_jornalismo', [{'url': u} for u in urls], lambda _: response,
                          lambda _: pytest.fail('unmatched metadata must not be saved'))
    assert not facts
    assert stats['fallback'] == 'no_exact_url_dates'


@pytest.mark.parametrize('failure', ['storage', 'http429', 'hash'])
def test_lookup_failure_keeps_normal_fetch_fallback_without_trusted_dates(failure):
    row, response = case('lupa')
    if failure == 'http429':
        response.status_code = 429
    def save(raw):
        if failure == 'storage':
            raise OSError('unavailable')
        return 'wrong', 'key'
    facts, stats = lookup('lupa', [{'url': r['observed_url']} for r in row['references']], lambda _: response, save)
    assert not facts and stats['fallback']
    assert stats['requests'] == 1


def test_lookup_is_scoped_and_forced_refresh_is_not_optimized():
    row, _ = case('ponte_jornalismo')
    def forbidden(*args):
        pytest.fail('no request expected')
    facts, _ = lookup('jota', [{'url': row['references'][0]['observed_url']}], forbidden, forbidden)
    assert not facts
    facts, _ = lookup('ponte_jornalismo', [{'url': r['observed_url'], 'force_refresh': True} for r in row['references']], forbidden, forbidden)
    assert not facts


@pytest.mark.parametrize('source', ['ponte_jornalismo', 'lupa'])
def test_larger_batches_preserve_one_hundred_real_dates_with_bounded_request_urls(source):
    root = FIXTURES / 'large_batches'
    row = next(r for r in json.loads((root / 'provenance.json').read_text())['rows'] if r['source'] == source)
    responses = []
    for evidence in row['responses']:
        raw = gzip.decompress((root / evidence['evidence']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == evidence['sha256']
        responses.append(raw)
    calls = []
    def fetch(url):
        raw = responses[len(calls)]
        slugs = parse_qs(urlsplit(url).query)['slug'][0].split(',')
        assert len(url.encode()) <= 4096 and len(slugs) <= 100
        assert set(slugs) == {p['slug'] for p in json.loads(raw)}
        calls.append(url)
        return SimpleNamespace(content=raw, status_code=200, url=url)
    facts, stats = lookup(source, [{'url': r['observed_url']} for r in row['references']], fetch,
                          lambda raw: (hashlib.sha256(raw).hexdigest(), 'immutable-real-api-response'))
    assert len(calls) == stats['requests'] == 2
    assert stats['matchedURLs'] == 100 and not stats['fallback']
    assert max(len(parse_qs(urlsplit(u).query)['slug'][0].split(',')) for u in calls) > 20
    for ref in row['references']:
        assert facts[ref['observed_url']][0] == datetime.fromisoformat(ref['verified_at'])


def test_new_publisher_parsers_import_without_optional_local_packages():
    # The earlier Exame deployment exposed a local-only dependency. Enforce
    # stdlib-only imports without loading the workstation's site-packages.
    root = Path(__file__).resolve().parents[1]
    script = '''import importlib.util,sys
for path in sys.argv[1:]:
 spec=importlib.util.spec_from_file_location('publisher_parser',path)
 module=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(module)
'''
    subprocess.run([sys.executable, '-S', '-c', script,
        str(root / 'web_app/political_public_date_batches.py'),
        str(root / 'web_app/political_exame_archive.py')], check=True, capture_output=True, timeout=10)
