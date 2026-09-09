"""Body association, bounded storage and fallback tests for public API fragments."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import gzip
import hashlib
import json
import threading
import time
from types import SimpleNamespace

import pytest

from web_app import political_body_batches as batches
from web_app.political_body_batches import BatchBodyUnavailable, WordPressBodyBatches
from web_app.political_discovery import _wordpress

BODY = 'O encontro apresentou propostas para escolas e hospitais em vários municípios. ' * 7 + 'Eduardo Paes participou da reunião no Rio de Janeiro.'
SOURCE = {'key': 'tempo_real_rj', 'domain': 'temporealrj.com', 'base_url': 'https://temporealrj.com', 'name': 'Tempo Real RJ'}


class Store:
    enabled = True
    prefix = 'test-batches'
    def __init__(self): self.objects, self.reads = {}, 0
    def upload_bytes(self, data, key, kind): self.objects[key] = data; return True
    def read_political_object(self, key): self.reads += 1; return self.objects[key]


def record(post_id=1, text=BODY):
    return {'post_id': post_id, 'url': f'https://temporealrj.com/reuniao-politica-municipal-{post_id}',
            'published_at': '2026-08-09T03:00:00+00:00', 'content_html': '<p>' + text + '</p>', 'protected': False}


def candidate(row):
    return {'url': row['url'], 'source_key': SOURCE['key'], 'published_at': row['published_at'],
            'title': 'Encontro municipal', 'metadata': {'wordpress_id': row['post_id']}}


def prepare(rows=None):
    store = Store(); writer = WordPressBodyBatches(store); rows = rows or [record()]
    refs = writer.store_batch({'source_key': SOURCE['key'], 'records': rows})
    return store, refs, rows


def test_restart_reads_durable_hash_reference_and_reuses_a_bounded_cache():
    store, refs, rows = prepare([record(1), record(2)])
    reader = WordPressBodyBatches(store)  # worker restart: no in-memory writer state
    assert reader.read_body(refs[0], candidate(rows[0]))['full_text'] == BODY
    assert reader.read_body(refs[1], candidate(rows[1]))['full_text'] == BODY
    assert store.reads == 1
    assert 'content_html' not in json.dumps(refs)
    assert all(len(json.dumps(ref)) < 500 for ref in refs)
    assert all('wordpress-batches/' in key for key in store.objects)


def test_concurrent_same_batch_consumers_share_one_object_read():
    store, refs, rows = prepare([record(1), record(2)])
    original = store.read_political_object
    def slow_read(key): time.sleep(.02); return original(key)
    store.read_political_object = slow_read
    reader = WordPressBodyBatches(store)
    with ThreadPoolExecutor(max_workers=4) as pool:
        values = list(pool.map(lambda i: reader.read_body(refs[i % 2], candidate(rows[i % 2])), range(8)))
    assert len(values) == 8 and store.reads == 1


@pytest.mark.parametrize('change,reason', [
    (lambda r,c: c.update(url='https://temporealrj.com/different'), 'batch_url_mismatch'),
    (lambda r,c: c.update(source_key='tupi'), 'batch_source_mismatch'),
    (lambda r,c: c['metadata'].update(wordpress_id=2), 'batch_post_id_mismatch'),
    (lambda r,c: r.update(post_id=True), 'batch_post_id_mismatch'),
    (lambda r,c: c.update(published_at='2026-08-10T03:00:00+00:00'), 'batch_date_mismatch'),
    (lambda r,c: c.update(published_at='2026-08-09T03:00:00'), 'batch_date_unverified'),
    (lambda r,c: r.update(index=True), 'batch_index_invalid'),
    (lambda r,c: r.update(index=100), 'batch_index_invalid'),
    (lambda r,c: r.update(key='another-prefix/private.json.gz'), 'batch_reference_invalid'),
])
def test_fragment_never_associates_with_another_url_date_id_or_source(change, reason):
    store, refs, rows = prepare(); ref, item = deepcopy(refs[0]), candidate(rows[0]);change(ref,item)
    with pytest.raises(BatchBodyUnavailable, match=reason): WordPressBodyBatches(store).read_body(ref,item)


@pytest.mark.parametrize('content,protected,reason', [
    ('', False, 'batch_text_unavailable'), ('<img src="image.jpg" alt="">', False, 'batch_text_unavailable'),
    ('<p>Not a full article.</p>', False, 'batch_text_unavailable'), ('<p>'+BODY+'</p>', True, 'batch_text_unavailable'),
    ('<p>'+BODY+'</p><!--nextpage-->', False, 'batch_continuation_unverified'),
    ('<p>'+BODY+'</p>[gallery ids="1"]', False, 'batch_continuation_unverified'),
])
def test_unavailable_protected_short_and_unverified_continuation_require_page_fallback(content, protected, reason):
    row=record();row.update(content_html=content,protected=protected);store,refs,_=prepare([row])
    with pytest.raises(BatchBodyUnavailable, match=reason): WordPressBodyBatches(store).read_body(refs[0],candidate(row))


def test_related_fragment_blocks_are_removed_without_losing_later_primary_body():
    row=record();row['content_html']='<p>'+BODY+'</p><div class="related-posts"><p>Pedro Duarte '+BODY+'</p></div><p>Última declaração editorial de Eduardo Cavaliere no Rio.</p>'
    store,refs,_=prepare([row]);body=WordPressBodyBatches(store).read_body(refs[0],candidate(row))['full_text']
    assert 'Pedro Duarte' not in body and body.endswith('Última declaração editorial de Eduardo Cavaliere no Rio.')


@pytest.mark.parametrize('corruption', ['missing', 'hash', 'gzip_bomb', 'compressed_limit'])
def test_object_failures_are_bounded_and_request_page_fallback(corruption, monkeypatch):
    store,refs,rows=prepare();key=refs[0]['key']
    if corruption=='missing':store.objects.clear()
    elif corruption=='hash':store.objects[key]=gzip.compress(b'wrong')
    elif corruption=='gzip_bomb':store.objects[key]=gzip.compress(b'x'*(batches.MAX_BATCH_BYTES+1))
    else:store.objects[key]=b'x'*(batches.MAX_BATCH_BYTES+1)
    with pytest.raises(BatchBodyUnavailable):WordPressBodyBatches(store).read_body(refs[0],candidate(rows[0]))


def test_cache_is_bounded_and_evicts_oldest_batches(monkeypatch):
    monkeypatch.setattr(batches,'MAX_CACHE_BATCHES',2)
    store=Store();reader=WordPressBodyBatches(store);written=[]
    for i in range(1,4):
        row=record(i);ref=reader.store_batch({'source_key':SOURCE['key'],'records':[row]})[0];written.append((ref,row))
    assert len(reader._cache)==2 and reader._cache_bytes<=batches.MAX_CACHE_BYTES
    assert written[0][0]['sha256'] not in reader._cache
    reader.read_body(written[0][0],candidate(written[0][1]));assert store.reads==1


def test_upload_failure_and_duplicate_ids_fail_without_creating_valid_references():
    store=Store();store.upload_bytes=lambda *a:False
    with pytest.raises(BatchBodyUnavailable,match='batch_storage_failed'):WordPressBodyBatches(store).store_batch({'source_key':SOURCE['key'],'records':[record()]})
    with pytest.raises(BatchBodyUnavailable,match='batch_duplicate_post_id'):WordPressBodyBatches(Store()).store_batch({'source_key':SOURCE['key'],'records':[record(),record()]})


def test_discovery_body_batch_is_separate_from_candidate_payload_and_keeps_raw_pagination():
    row=record();urls=[]
    response=SimpleNamespace(status_code=200,headers={'X-WP-TotalPages':'2'},text=json.dumps([
        {'id':1,'link':row['url'],'date_gmt':'2026-08-09T03:00:00','date':'2026-08-09T00:00:00',
         'title':{'rendered':'Encontro municipal'},'excerpt':{'rendered':'Resumo sem nomes'},'content':{'rendered':row['content_html'],'protected':False}},
        {'id':2,'link':'https://another.example/outside','date_gmt':'2026-08-09T04:00:00'},
    ]))
    def fetch(url):urls.append(url);return response
    result=_wordpress({'date_from':'2026-08-09','date_to':'2026-08-09','cursor':{}},SOURCE,fetch)
    assert result['raw_count']==2 and result['next_cursor']=={'page':2}
    assert len(result['candidates'])==len(result['body_batch']['records'])==1
    assert 'Eduardo Paes' not in json.dumps(result['candidates'])
    assert 'Eduardo Paes' in result['body_batch']['records'][0]['content_html']
    assert 'content' in urls[0]


def test_unproven_wordpress_sources_keep_existing_metadata_only_discovery():
    source={**SOURCE,'key':'veja_rio','domain':'vejario.abril.com.br','base_url':'https://vejario.abril.com.br'}
    urls=[]
    def fetch(url):urls.append(url);return SimpleNamespace(status_code=200,headers={},text='[]')
    result=_wordpress({'date_from':'2026-08-09','date_to':'2026-08-09','cursor':{}},source,fetch)
    assert 'body_batch' not in result and 'content' not in urls[0]


def test_batch_telemetry_distinguishes_store_reads_cache_use_and_fallback_without_keys(caplog):
    import logging
    from web_app import political_metrics as metrics
    collector=metrics.Collector(allowed_sources={SOURCE['key']})
    caplog.set_level(logging.INFO,logger='political_metrics')
    with metrics.task_metrics({'id':1,'kind':'discovery','source_key':SOURCE['key']},metrics=collector) as task:
        store,refs,rows=prepare();task.outcome='complete'
    reader=WordPressBodyBatches(store)
    for task_id in [2,3]:
        with metrics.task_metrics({'id':task_id,'kind':'fetch','source_key':SOURCE['key']},metrics=collector) as task:
            reader.read_body(refs[0],candidate(rows[0]));task.outcome='saved' if task_id==2 else 'duplicate'
    with metrics.task_metrics({'id':4,'kind':'fetch','source_key':SOURCE['key']},metrics=collector) as task:
        metrics.record_timing('body_batch_fallback',0,outcome='error');task.outcome='retryable'
    recorded=collector.drain(10)
    counts={op:sum(row['count'] for row in recorded if row['operation']==op) for op in metrics.OPERATIONS}
    assert counts['body_batch_upload']==counts['body_batch_read']==counts['body_batch_cache_hit']==counts['body_batch_fallback']==1
    assert counts['body_batch_use']==2 and counts['http']==0
    assert sum(r['count'] for r in recorded if r['operation']=='task' and r['outcome']=='saved')==1
    assert sum(r['count'] for r in recorded if r['operation']=='task' and r['outcome']=='duplicate')==1
    assert refs[0]['key'] not in caplog.text and BODY not in caplog.text and 'temporealrj.com' not in caplog.text


def test_missing_publication_date_preserves_url_for_page_verification_without_poisoning_batch():
    rows=[]
    for post_id in [1,2]:
        row=record(post_id);rows.append({'id':post_id,'link':row['url'],'date_gmt':'2026-08-09T03:00:00' if post_id==1 else '',
            'title':{'rendered':'Reportagem municipal'},'content':{'rendered':row['content_html'],'protected':False}})
    response=SimpleNamespace(status_code=200,headers={},text=json.dumps(rows))
    result=_wordpress({'date_from':'2026-08-09','date_to':'2026-08-09','cursor':{}},SOURCE,lambda *a:response)
    assert len(result['candidates'])==2
    assert result['candidates'][1]['published_at']==''
    assert [row['post_id'] for row in result['body_batch']['records']]==[1]


def test_fragment_parser_failure_is_optional_path_failure_not_a_lost_candidate(monkeypatch):
    from web_app import political_discovery
    store,refs,rows=prepare()
    def fail(*args):raise ValueError('publisher fragment parsing failure')
    monkeypatch.setattr(political_discovery,'extract_article',fail)
    with pytest.raises(BatchBodyUnavailable,match='batch_extraction_failed'):
        WordPressBodyBatches(store).read_body(refs[0],candidate(rows[0]))


@pytest.mark.parametrize('code',['response_budget_exceeded','response_too_large'])
def test_rich_response_budget_falls_back_to_same_metadata_cursor_without_losing_candidates(code):
    from urllib.parse import parse_qs,urlparse
    from web_app.political_corpus import FetchProblem
    row=record();urls=[]
    def fetch(url):
        urls.append(url)
        if len(urls)==1:raise FetchProblem(code)
        return SimpleNamespace(status_code=200,headers={'X-WP-TotalPages':'8'},text=json.dumps([
            {'id':1,'link':row['url'],'date_gmt':'2026-08-09T03:00:00','title':{'rendered':'Encontro municipal'}}]))
    result=_wordpress({'date_from':'2026-08-09','date_to':'2026-08-09','cursor':{'page':7}},SOURCE,fetch)
    assert len(urls)==2 and len(result['candidates'])==1 and 'body_batch' not in result
    assert result['body_batch_fallback']=='api_body_response_budget' and result['next_cursor']=={'page':8}
    before,after=[parse_qs(urlparse(url).query) for url in urls]
    assert 'content' in before.pop('_fields')[0] and 'content' not in after.pop('_fields')[0]
    assert before==after and after['per_page']==['100'] and after['page']==['7']


@pytest.mark.parametrize('error',[429,503,'timeout'])
def test_http_errors_and_unrelated_timeouts_never_trigger_an_extra_metadata_query(error):
    from web_app.political_discovery import DiscoveryError
    import requests
    urls=[]
    def fetch(url):
        urls.append(url)
        if error=='timeout':raise requests.Timeout('ordinary network timeout')
        return SimpleNamespace(status_code=error,headers={},text='')
    with pytest.raises(DiscoveryError):_wordpress({'date_from':'2026-08-09','date_to':'2026-08-09','cursor':{}},SOURCE,fetch)
    assert len(urls)==1
