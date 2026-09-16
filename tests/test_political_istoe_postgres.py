"""Real publisher documents through disposable PostgreSQL and immutable objects."""
import gzip
import json
import os

import pytest

from test_political_corpus_postgres import MemoryStore
from test_political_istoe import FIXTURES, SOURCE, PEOPLE, response
from web_app.political_corpus import PoliticalCorpusService
from web_app.political_istoe_inventory import InventoryTransport

DSN=os.environ.get('POLITICAL_TEST_DATABASE_URL','')
pytestmark=pytest.mark.skipif(not DSN,reason='explicit disposable PostgreSQL required')


@pytest.fixture
def service():
    service=PoliticalCorpusService(store=MemoryStore(),database_url=DSN)
    service.ensure_schema()
    with service._connect() as conn:
        conn.execute('TRUNCATE political_jobs,political_articles,political_stories,political_source_leases,political_domain_limits,political_workers,political_istoe_documents,political_istoe_urls RESTART IDENTITY CASCADE')
    yield service
    service.close()


def start(service):
    return service.start_job({'target_keys':[p['key'] for p in PEOPLE],'target_snapshots':PEOPLE,
        'date_from':'2026-06-01','date_to':'2026-09-10','source_keys':['istoe'],'collection_profile':'psd_rj_2026'},
        started_by='test',allowed_target_keys=[p['key'] for p in PEOPLE])


def test_snapshot_durable_reuse_and_missing_object_does_not_refetch_changed_page(service,monkeypatch):
    calls=[]
    def fetch(url,**kwargs):
        calls.append(url);return response(url,'index.xml.gz')
    monkeypatch.setattr(service,'fetch',fetch)
    historical={'cursor':{},'payload':{'date_to':'2000-01-01'}}
    first=InventoryTransport(service,historical)
    r=first.fetch('https://istoe.com.br/wp-sitemap.xml');cursor=first.checkpoint({'offset':32})
    assert len(calls)==1
    resumed=InventoryTransport(service,{'cursor':cursor})
    assert resumed.fetch(r.url).content==r.content and len(calls)==1
    fresh_job=InventoryTransport(service,historical)
    assert fresh_job.fetch(r.url).content==r.content and len(calls)==1
    service.store.objects.clear()
    with pytest.raises(Exception,match='istoe_snapshot_unavailable'):
        InventoryTransport(service,{'cursor':cursor}).fetch(r.url)
    assert len(calls)==1


def test_current_day_refreshes_sitemap_but_resume_keeps_its_snapshot(service,monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    calls=[]
    def fetch(url,**kwargs):
        calls.append(url)
        return response(url,'index.xml.gz')
    monkeypatch.setattr(service,'fetch',fetch)
    first=InventoryTransport(service,{'cursor':{},'payload':{'date_to':'2000-01-01'}})
    url='https://istoe.com.br/wp-sitemap.xml'
    original=first.fetch(url).content
    cursor=first.checkpoint({'offset':32})
    captured=datetime.fromisoformat(first.reference['fetched_at']).astimezone(ZoneInfo('America/Sao_Paulo')).date().isoformat()
    current={'cursor':{},'payload':{'date_to':captured}}
    assert InventoryTransport(service,current).fetch(url).content==original
    assert len(calls)==2, 'a new same-day job must check for newly published URLs'
    resumed=InventoryTransport(service,{**current,'cursor':cursor})
    assert resumed.fetch(url).content==original
    assert len(calls)==2, 'resume must remain tied to its immutable snapshot'


def test_discovery_commits_inventory_cursor_and_no_google_tasks(service,monkeypatch):
    job=start(service)
    monkeypatch.setattr(service,'fetch',lambda url,**kw:response(url,'index.xml.gz' if url.endswith('wp-sitemap.xml') else url.split('/')[-1]+'.gz'))
    result=service.process_task(service.claim_task('discovery',worker_id='root'))
    assert result['status']=='gap'
    # Latest part 604 is processed in bounded pages, including no-name URLs.
    first=service.claim_task('discovery',worker_id='part')
    assert first['payload']['url'].endswith('-604.xml')
    assert service.process_task(first)['status']=='continue'
    with service._connect() as conn:
        saved=conn.execute('SELECT cursor FROM political_tasks WHERE id=%s',(first['id'],)).fetchone()['cursor']
        assert saved['offset']==500 and saved['inventory_snapshot']['object_key']
        assert conn.execute('SELECT COUNT(*) n FROM political_istoe_urls').fetchone()['n']==500
        assert conn.execute("SELECT COUNT(*) n FROM political_tasks WHERE payload->>'strategy'='google_news'").fetchone()['n']==0
        assert conn.execute('SELECT COUNT(*) n FROM political_observations WHERE job_id=%s',(job['id'],)).fetchone()['n']==500
    expired=service.claim_task('discovery',worker_id='resume')
    assert expired['id']==first['id']
    assert service.process_task(expired)['status']=='complete'
    with service._connect() as conn:
        assert conn.execute('SELECT COUNT(*) n FROM political_istoe_urls').fetchone()['n']==767


def test_storage_failure_does_not_advance_discovery(service,monkeypatch):
    start(service)
    monkeypatch.setattr(service,'fetch',lambda url,**kw:response(url,'index.xml.gz'))
    monkeypatch.setattr(service.store,'upload_bytes',lambda *a,**k:False)
    task=service.claim_task('discovery',worker_id='storage')
    result=service.process_task(task)
    assert result['status']=='retryable'
    with service._connect() as conn:
        assert conn.execute('SELECT cursor FROM political_tasks WHERE id=%s',(task['id'],)).fetchone()['cursor']=={}
        assert conn.execute('SELECT COUNT(*) n FROM political_istoe_documents').fetchone()['n']==0
        assert conn.execute('SELECT COUNT(*) n FROM political_tasks').fetchone()['n']==1


def test_real_body_saved_transactionally_and_reused_for_another_job(service,monkeypatch):
    article=next(a for a in json.loads((FIXTURES/'articles.json').read_text()) if 'ventos-fortes' in a['url'])
    calls=[]
    def fetch(url,**kw):
        calls.append(url);assert url==article['url']
        return response(url,article['file'])
    monkeypatch.setattr(service,'fetch',fetch)
    for n in range(2):
        job=start(service)
        with service._connect() as conn:
            service._insert_task(conn,job['id'],'fetch',{'source_key':'istoe','source_name':'IstoÉ','url':article['url']})
        result=service.process_task(service.claim_task('fetch',worker_id='article'))
        assert result['status']==('saved' if n==0 else 'duplicate')
        with service._connect() as conn:
            row=conn.execute('SELECT * FROM political_articles WHERE id=%s',(result['articleId'],)).fetchone()
            assert row['metadata']['extraction_version']=='istoe-editorial-1'
            assert 'Eduardo Cavaliere' in service._read_text(row['text_object_key'],row['content_hash'])
            assert conn.execute('SELECT COUNT(*) n FROM political_articles').fetchone()['n']==1
            assert conn.execute('SELECT COUNT(*) n FROM political_mentions').fetchone()['n']==1
    assert len(calls)==1


def test_foreign_or_google_fetch_rejected_before_network(service,monkeypatch):
    job=start(service)
    monkeypatch.setattr(service,'fetch',lambda *a,**kw:pytest.fail('network forbidden'))
    with service._connect() as conn:
        service._insert_task(conn,job['id'],'fetch',{'source_key':'istoe','url':'https://news.google.com/articles/unresolved'})
    task=service.claim_task('fetch',worker_id='blocked')
    assert service.process_task(task)['errorType']=='istoe_direct_url_required'


def test_deferred_date_recovery_is_scoped_and_does_not_review_archive(service,monkeypatch):
    job=start(service)
    with service._connect() as conn:
        task_id=conn.execute("SELECT id FROM political_tasks WHERE job_id=%s",(job['id'],)).fetchone()['id']
        conn.execute("""INSERT INTO political_observations(job_id,source_task_id,observed_url,source_key,disposition,metadata)
            VALUES(%s,%s,'https://istoe.com.br/tse-julga-recurso-claudio-castro-eleicao-rio','istoe','deferred_date','{}')""",(job['id'],task_id))
        conn.execute("UPDATE political_tasks SET status='complete' WHERE job_id=%s",(job['id'],))
        conn.execute("UPDATE political_jobs SET status='succeeded' WHERE id=%s",(job['id'],))
    recovery=service.start_job({'kind':'recover','source_keys':['istoe'],'collection_profile':'psd_rj_2026',
        'target_keys':[p['key'] for p in PEOPLE],'target_snapshots':PEOPLE,'date_from':'2026-06-01','date_to':'2026-09-10',
        'recovery_gap_types':['istoe_deferred_dates']},started_by='test',allowed_target_keys=[p['key'] for p in PEOPLE])
    monkeypatch.setattr(service,'fetch',lambda *_:pytest.fail('discovery must read frozen observations only'))
    assert service.process_task(service.claim_task('discovery',worker_id='recover'))['status']=='complete'
    with service._connect() as conn:
        tasks=conn.execute('SELECT kind,payload FROM political_tasks WHERE job_id=%s',(recovery['id'],)).fetchall()
        assert len(tasks)==2
        assert not any(t['kind']=='review' or t['payload'].get('strategy')=='google_news' for t in tasks)
        assert next(t for t in tasks if t['kind']=='fetch')['payload']['metadata']['body_deferred'] is False
