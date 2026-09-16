"""Replay publisher XML to verify identical discovery with fewer downloads."""
import gzip
import hashlib
import json
from pathlib import Path

import pytest
import requests

from web_app import political_expanded_discovery as expanded
from web_app import political_sitemap_cache as cache_module
from web_app.political_sitemap_cache import PaginatedSitemapCache
from web_app.political_discovery import DiscoveryError

FIXTURES = Path(__file__).parent / 'fixtures/political_expanded'


def real_response(name='istoe_603'):
    proof = next(r for r in json.loads((FIXTURES / 'provenance.json').read_text()) if r['name'] == name)
    raw = gzip.decompress((FIXTURES / (name + '.gz')).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == proof['sha256']
    response = requests.Response()
    response.status_code = 200
    response._content = raw
    response.url = proof['url']
    return response


def source_task():
    source = next(s for s in expanded.load_expanded_sources() if s['key'] == 'istoe')
    # This suite validates historical generic tasks, not the new direct adapter.
    source = {**source, 'mechanisms':[{'kind':'sitemap','url':'https://istoe.com.br/wp-sitemap.xml'}]}
    task = expanded.build_expanded_tasks(source, '2026-08-09', '2026-08-09', [{'key': 'eduardo_paes'}])[0]
    return source, {**task, 'url': real_response().url, 'depth': 1}


def run_pages(directory, cache_enabled):
    source, task = source_task()
    calls = []
    def fetch(url):
        calls.append(url)
        return real_response()
    candidates = []
    while True:
        cache = PaginatedSitemapCache(fetch, task.get('cursor'), directory)
        result = expanded.discover_expanded(task, source, cache.fetch if cache_enabled else fetch)
        candidates.extend(result['candidates'])
        if not result['next_cursor']:
            return candidates, calls
        task['cursor'] = cache.checkpoint(result['next_cursor']) if cache_enabled else result['next_cursor']


def test_real_2000_entry_leaf_retains_same_candidates_and_reduces_four_downloads_to_one(tmp_path):
    before, original_calls = run_pages(tmp_path, False)
    after, cached_calls = run_pages(tmp_path, True)
    assert before == after and len(after) > 1900
    assert len(original_calls) == 4 and len(cached_calls) == 1
    assert all(not c['published_at'] for c in after)


def test_real_cache_hits_are_explicit_telemetry_instead_of_other(tmp_path):
    from web_app import political_metrics as metrics
    collector = metrics.Collector(allowed_sources={'istoe'})
    with metrics.task_metrics({'kind':'discovery','source_key':'istoe','id':1},metrics=collector):
        candidates,calls=run_pages(tmp_path,True)
    rows=collector.drain(30)
    assert len(candidates)>1900 and len(calls)==1
    hits=[r for r in rows if r['operation']=='sitemap_cache' and r['outcome']=='hit']
    assert len(hits)==1 and hits[0]['count']==3
    assert not any(r['operation']=='other' for r in rows)


@pytest.mark.parametrize('lost', ['deleted', 'corrupt'])
def test_restart_or_corruption_refetches_and_keeps_offset_when_document_unchanged(tmp_path, lost):
    source, task = source_task()
    calls = []
    def fetch(url):
        calls.append(url); return real_response()
    first = PaginatedSitemapCache(fetch, {}, tmp_path)
    result = expanded.discover_expanded(task, source, first.fetch)
    task['cursor'] = first.checkpoint(result['next_cursor'])
    file = next(tmp_path.glob('*.xml'))
    if lost == 'deleted': file.unlink()
    else: file.write_bytes(b'corrupt local file')
    resumed = expanded.discover_expanded(task, source, PaginatedSitemapCache(fetch, task['cursor'], tmp_path).fetch)
    expected = expanded.discover_expanded(task, source, fetch)
    assert resumed['candidates'] == expected['candidates']
    assert resumed['next_cursor']['offset'] == 1000 and len(calls) == 3


def test_changed_publisher_after_cache_loss_keeps_explicit_gap(tmp_path):
    source, task = source_task()
    cache = PaginatedSitemapCache(lambda u: real_response(), {}, tmp_path)
    first = expanded.discover_expanded(task, source, cache.fetch)
    task['cursor'] = cache.checkpoint(first['next_cursor'])
    next(tmp_path.glob('*.xml')).unlink()
    # A different real publisher response represents a changed fetched document.
    second = PaginatedSitemapCache(lambda u: real_response('istoe_index'), task['cursor'], tmp_path)
    result = expanded.discover_expanded(task, source, second.fetch)
    assert result['outcome'] == 'gap'
    assert result['gap_reason'] == 'expanded_sitemap_changed_during_resume'


def test_new_calendar_url_is_fetched_and_429_is_not_cached(tmp_path):
    response = real_response()
    cache = PaginatedSitemapCache(lambda u: response, {}, tmp_path)
    cache.fetch(response.url)
    cursor = cache.checkpoint({'offset': 500})
    calls = []
    def limited(url):
        calls.append(url)
        r = requests.Response(); r.status_code = 429; r.headers['Retry-After'] = '60';r._content = b''
        return r
    resumed = PaginatedSitemapCache(limited, cursor, tmp_path)
    from web_app.political_discovery import _get
    with pytest.raises(DiscoveryError) as error:
        _get(resumed.fetch, response.url + '?page=2')
    assert error.value.status_code == 429 and error.value.retry_after == 60 and len(calls) == 1
    assert resumed.checkpoint({'offset': 0}) == {'offset': 0}


def test_unavailable_local_cache_does_not_stop_discovery(tmp_path):
    directory = tmp_path / 'not-a-directory'; directory.write_text('existing file')
    result, calls = run_pages(directory, True)
    assert len(result) > 1900 and len(calls) == 4


def test_disk_cache_retains_only_bounded_xml_documents(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_module, 'MAX_CACHE_FILES', 1)
    for name in ['istoe_603', 'istoe_index']:
        response = real_response(name)
        cache = PaginatedSitemapCache(lambda u: response, {}, tmp_path)
        cache.fetch(response.url);cache.checkpoint({'offset': 100})
    assert len(list(tmp_path.glob('*.xml'))) == 1
    assert next(tmp_path.glob('*.xml')).name == hashlib.sha256(real_response('istoe_index').content).hexdigest() + '.xml'


def test_immutable_object_resumes_real_xml_after_worker_loss_and_publisher_change(tmp_path):
    source, task = source_task()
    objects, writes, reads, requests_made = {}, [], [], []
    def save(raw):
        digest = hashlib.sha256(raw).hexdigest(); key = digest + '.discovery.gz'
        objects[key] = gzip.compress(raw, mtime=0); writes.append(key)
        return digest, key
    def read(key, digest):
        reads.append(key)
        return gzip.decompress(objects[key])
    def fetch(url):
        requests_made.append(url)
        return real_response() if len(requests_made) == 1 else real_response('istoe_index')
    first = PaginatedSitemapCache(fetch, {}, tmp_path, save_object=save, read_object=read)
    result = expanded.discover_expanded(task, source, first.fetch)
    task['cursor'] = json.loads(json.dumps(first.checkpoint(result['next_cursor'])))
    next(tmp_path.glob('*.xml')).unlink()
    cache = PaginatedSitemapCache(fetch, task['cursor'], tmp_path, save_object=save, read_object=read)
    resumed = expanded.discover_expanded(task, source, cache.fetch)
    expected = expanded.discover_expanded(task, source, lambda _: real_response())
    assert resumed['candidates'] == expected['candidates']
    assert resumed['next_cursor']['offset'] == 1000
    cache.checkpoint(resumed['next_cursor'])
    assert len(requests_made) == len(writes) == len(reads) == 1
    assert next(tmp_path.glob('*.xml')).read_bytes() == real_response().content


@pytest.mark.parametrize('failure', ['missing', 'corrupt'])
def test_unavailable_or_corrupt_remote_snapshot_keeps_existing_changed_page_gap(tmp_path, failure):
    source, task = source_task()
    original = real_response()
    digest = hashlib.sha256(original.content).hexdigest()
    first = PaginatedSitemapCache(lambda _: original, {}, tmp_path,
        save_object=lambda raw: (digest, 'snapshot.discovery.gz'))
    result = expanded.discover_expanded(task, source, first.fetch)
    task['cursor'] = first.checkpoint(result['next_cursor'])
    next(tmp_path.glob('*.xml')).unlink()
    def read(*args):
        if failure == 'missing':
            raise OSError('storage unavailable')
        return real_response('istoe_index').content
    cache = PaginatedSitemapCache(lambda _: real_response('istoe_index'), task['cursor'], tmp_path, read_object=read)
    result = expanded.discover_expanded(task, source, cache.fetch)
    assert result['outcome'] == 'gap'
    assert result['gap_reason'] == 'expanded_sitemap_changed_during_resume'


def test_remote_snapshot_survives_unwritable_local_cache(tmp_path):
    source, task = source_task()
    original = real_response()
    digest = hashlib.sha256(original.content).hexdigest()
    directory = tmp_path / 'occupied'; directory.write_text('existing file')
    cache = PaginatedSitemapCache(lambda _: original, {}, directory,
        save_object=lambda raw: (digest, 'snapshot.discovery.gz'))
    result = expanded.discover_expanded(task, source, cache.fetch)
    task['cursor'] = cache.checkpoint(result['next_cursor'])
    assert task['cursor']['response_cache']['object_key'] == 'snapshot.discovery.gz'
    def no_fetch(*args):
        pytest.fail('must restore immutable snapshot')
    cache = PaginatedSitemapCache(no_fetch, task['cursor'], directory, read_object=lambda *args: original.content)
    result = expanded.discover_expanded(task, source, cache.fetch)
    assert result['next_cursor']['offset'] == 1000


def test_failed_object_upload_still_uses_local_snapshot(tmp_path):
    source, task = source_task()
    def failed(*args):
        raise OSError('object storage unavailable')
    cache = PaginatedSitemapCache(lambda _: real_response(), {}, tmp_path, save_object=failed)
    result = expanded.discover_expanded(task, source, cache.fetch)
    task['cursor'] = cache.checkpoint(result['next_cursor'])
    assert 'object_key' not in task['cursor']['response_cache']
    cache = PaginatedSitemapCache(lambda _: pytest.fail('local cache remains usable'), task['cursor'], tmp_path)
    assert expanded.discover_expanded(task, source, cache.fetch)['next_cursor']['offset'] == 1000
