"""Disposable-PostgreSQL durability checks for body-batch candidate references."""
from copy import deepcopy
import json

import pytest

from test_political_corpus_postgres import DATABASE_URL, service, start, fake_response
from test_political_body_batches import BODY, SOURCE, candidate, record
from web_app import political_discovery
from web_app.political_body_batches import WordPressBodyBatches
from web_app.political_corpus import LeaseLost

pytestmark=pytest.mark.skipif(not DATABASE_URL,reason='Requires disposable POLITICAL_TEST_DATABASE_URL')


def enqueue_batch(service,monkeypatch,rows=None):
    rows=deepcopy(rows or [record()])
    for row in rows:
        if row['published_at'].startswith('2026-08-09'):
            row['published_at']='2026-06-01T03:00:00+00:00'
    job=start(service,monkeypatch,targets=('paes',),tasks=[{'source_key':SOURCE['key'],'strategy':'wordpress',
        'date_from':'2026-06-01','date_to':'2026-06-02','cursor':{}}])
    result={'candidates':[candidate(row) for row in rows],'raw_count':len(rows),'outcome':'complete',
            'body_batch':{'source_key':SOURCE['key'],'records':rows}}
    monkeypatch.setattr(political_discovery,'discover',lambda *args:deepcopy(result))
    discovery=service.claim_task('discovery',worker_id='batch-discovery')
    assert service.process_task(discovery)['status']=='complete'
    return job,rows,discovery


def test_durable_reference_survives_restart_and_matches_body_only_without_publisher_request(service,monkeypatch):
    job,rows,_=enqueue_batch(service,monkeypatch)
    with service._connect() as conn:
        task=conn.execute("SELECT * FROM political_tasks WHERE kind='fetch'").fetchone()
        assert 'content_html' not in json.dumps(task['payload']) and BODY not in json.dumps(task['payload'])
        assert task['payload']['body_batch_ref']['post_id']==1
    assert len(service.store.objects)==1
    service._body_batches=WordPressBodyBatches(service.store)
    monkeypatch.setattr(service,'fetch',lambda *a,**k:pytest.fail('verified API body must not request publisher HTML'))
    result=service.process_task(service.claim_task('fetch',worker_id='batch-fetch'))
    assert result['status']=='saved' and result['bodyOrigin']=='wordpress_api_batch'
    with service._connect() as conn:
        article=conn.execute('SELECT * FROM political_articles').fetchone()
        assert article['date_status']=='api_verified'
        assert article['metadata']['publisher_provenance']['method']=='wordpress_api_batch'
        assert conn.execute('SELECT target_key FROM political_mentions').fetchone()['target_key']=='paes'
        assert conn.execute('SELECT fetch_attempted FROM political_jobs').fetchone()['fetch_attempted']==0
    assert service._read_text(article['text_object_key'],article['content_hash'])==BODY


def test_no_match_api_body_does_not_upload_final_article_text(service,monkeypatch):
    row=record(text='A reportagem acompanha mudanças em escolas e hospitais da região. '*10)
    enqueue_batch(service,monkeypatch,[row])
    monkeypatch.setattr(service,'fetch',lambda *a,**k:pytest.fail('API no-match does not need HTML'))
    result=service.process_task(service.claim_task('fetch',worker_id='batch-fetch'))
    assert result['status']=='no_match' and result['bodyOrigin']=='wordpress_api_batch'
    with service._connect() as conn:
        assert conn.execute('SELECT COUNT(*) AS n FROM political_articles').fetchone()['n']==0
    assert len(service.store.objects)==1 and all('wordpress-batches/' in key for key in service.store.objects)


@pytest.mark.parametrize('failure',['upload','missing','corrupt','wrong_index','wrong_date','protected','empty','short','force_refresh'])
def test_unusable_batch_falls_back_to_actual_publisher_html_and_saves(service,monkeypatch,failure):
    row=record()
    if failure=='protected':row['protected']=True
    if failure=='empty':row['content_html']=''
    if failure=='short':row['content_html']='<p>Short excerpt only.</p>'
    if failure=='upload':
        original=service.store.upload_bytes
        monkeypatch.setattr(service.store,'upload_bytes',lambda data,key,kind:False if '/wordpress-batches/' in key else original(data,key,kind))
    enqueue_batch(service,monkeypatch,[row])
    service._body_batches=WordPressBodyBatches(service.store)
    with service._connect() as conn:
        task=conn.execute("SELECT * FROM political_tasks WHERE kind='fetch'").fetchone()
        payload=task['payload']
        if failure in {'missing','corrupt'}:
            key=payload['body_batch_ref']['key']
            if failure=='missing':del service.store.objects[key]
            else:service.store.objects[key]=b'corrupt'
        if failure=='wrong_index':payload['body_batch_ref']['index']=100
        if failure=='wrong_date':payload['published_at']='2026-06-02T03:00:00+00:00'
        if failure=='force_refresh':payload['force_refresh']=True
        conn.execute('UPDATE political_tasks SET payload=%s::jsonb WHERE id=%s',(json.dumps(payload),task['id']))
        if failure=='upload':assert 'body_batch_ref' not in payload and payload['metadata']['body_batch_fallback']=='batch_storage_failed'
    requests=[]
    def fetch(url,*a,**k):requests.append(url);return fake_response(url,body=BODY)
    monkeypatch.setattr(service,'fetch',fetch)
    result=service.process_task(service.claim_task('fetch',worker_id='page-fallback'))
    assert result['status']=='saved' and result['bodyOrigin']=='publisher_page' and requests==[row['url']]
    with service._connect() as conn:
        article=conn.execute('SELECT * FROM political_articles').fetchone()
        assert article['date_status']=='page_verified'


@pytest.mark.parametrize('published,status',[('2026-06-03T02:59:59+00:00','saved'),('2026-06-03T03:00:00+00:00','outside_window')])
def test_api_batch_worker_enforces_sao_paulo_inclusive_end_day(service,monkeypatch,published,status):
    row=record();row['published_at']=published;enqueue_batch(service,monkeypatch,[row])
    monkeypatch.setattr(service,'fetch',lambda *a,**k:pytest.fail('verified date/body requires no publisher GET'))
    assert service.process_task(service.claim_task('fetch',worker_id='boundary'))['status']==status


def test_upload_before_failed_discovery_commit_does_not_advance_cursor_or_publish_partial_tasks(service,monkeypatch):
    row=record();row['published_at']='2026-06-01T03:00:00+00:00'
    start(service,monkeypatch,targets=('paes',),tasks=[{'source_key':SOURCE['key'],'strategy':'wordpress',
        'date_from':'2026-06-01','date_to':'2026-06-02','cursor':{'page':1}}])
    monkeypatch.setattr(political_discovery,'discover',lambda *args:{'candidates':[candidate(row)],'raw_count':1,
        'outcome':'continue','next_cursor':{'page':2},'body_batch':{'source_key':SOURCE['key'],'records':[row]}})
    original=service._insert_task
    def fail_insert(*args):raise LeaseLost('simulated lease lost after immutable batch upload')
    monkeypatch.setattr(service,'_insert_task',fail_insert)
    task=service.claim_task('discovery',worker_id='interrupted')
    assert service.process_task(task)['status']=='lease_lost'
    with service._connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM political_tasks WHERE kind='fetch'").fetchone()['n']==0
        assert conn.execute('SELECT COUNT(*) AS n FROM political_observations').fetchone()['n']==0
        assert conn.execute('SELECT cursor FROM political_tasks WHERE id=%s',(task['id'],)).fetchone()['cursor']=={'page':1}
    assert len(service.store.objects)==1  # immutable orphan is safe; no committed URL references lost
    monkeypatch.setattr(service,'_insert_task',original)
    assert service.process_task(task)['status']=='continue'
    with service._connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM political_tasks WHERE kind='fetch'").fetchone()['n']==1
        assert conn.execute('SELECT cursor FROM political_tasks WHERE id=%s',(task['id'],)).fetchone()['cursor']=={'page':2}
    assert len(service.store.objects)==1  # repeat upload has the identical immutable content address
