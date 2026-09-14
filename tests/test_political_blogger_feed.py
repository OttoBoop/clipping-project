"""Real publisher Atom responses: historical paging, identity and body reuse."""
from copy import deepcopy
import gzip,hashlib,json
from pathlib import Path
from urllib.parse import parse_qs,urlparse
import requests
import pytest
from web_app import political_blogger_feed as atom,political_expanded_discovery as expanded
from web_app.political_body_batches import WordPressBodyBatches,BatchBodyUnavailable

ROOT=Path(__file__).parent/'fixtures/political_belford_atom'
SOURCE=next(s for s in expanded.load_expanded_sources() if s['key']=='noticias_de_belford_roxo')


def response(index):
    proof=next(p for p in json.loads((ROOT/'provenance.json').read_text()) if p['name']=='page_'+str(index))
    raw=gzip.decompress((ROOT/(proof['name']+'.gz')).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==proof['sha256']
    r=requests.Response();r.status_code=200;r.url=proof['url'];r._content=raw
    return r


def task(first='2026-08-09',last='2026-08-09'):
    return next(t for t in expanded.build_expanded_tasks(SOURCE,first,last,[{'key':'paes'}]) if t['strategy']=='expanded_blogger_feed')


class Store:
    enabled=True
    prefix='local-real-atom-validation'
    def __init__(self):self.objects={}
    def upload_bytes(self,data,key,mime):self.objects[key]=data;return True
    def read_political_object(self,key):return self.objects[key]


def test_real_feed_keeps_publisher_ids_bodies_and_dates_without_calling_them_wordpress():
    r=response(201);data=atom.parse_atom_page(r.content,r.url,SOURCE)
    assert data['raw_count']==25 and len(data['candidates'])==len(data['body_batch']['records'])==25
    assert all('wordpress_id' not in c['metadata'] for c in data['candidates'])
    assert all(c['metadata']['publisher_post_id']>2**53 for c in data['candidates'])
    assert all('2026-06-' in c['published_at'] for c in data['candidates'])
    store=Store();batches=WordPressBodyBatches(store);refs=batches.store_batch(data['body_batch'])
    restarted=WordPressBodyBatches(store)
    for ref,candidate in zip(refs[:3],data['candidates'][:3]):
        body=restarted.read_body(ref,candidate)
        assert len(body['full_text'])>200
        assert body['body_origin']=='publisher_atom' and body['text_extent']=='unknown'
        assert body['publication_date_status']=='publisher_feed_reported'
        assert body['provenance']['feed_sha256']==hashlib.sha256(r.content).hexdigest()


def test_real_august_pagination_survives_cursor_serialization_and_stops_after_two_older_pages():
    run=task();requested=[];all_candidates=[];raw_count=0
    def fetch(url):
        index=int(parse_qs(urlparse(url).query).get('start-index',['1'])[0]);requested.append(index)
        assert urlparse(url).hostname=='www.noticiasdebelfordroxo.com'
        return response(index)
    while True:
        result=expanded.discover_expanded(run,SOURCE,fetch);all_candidates.extend(result['candidates']);raw_count+=result['raw_count']
        if not result['next_cursor']:break
        run={**run,'cursor':json.loads(json.dumps(result['next_cursor']))}
    assert requested==[1,26,51,76,101] and raw_count==125
    assert result['outcome']=='complete'
    from web_app.political_discovery import in_window
    assert all(in_window(c['published_at'],'2026-08-09','2026-08-09') for c in all_candidates)


def test_real_june_boundary_keeps_june_first_and_does_not_infer_from_updated_dates():
    r=response(226);run=task('2026-06-01','2026-06-02');run['cursor']={'url':r.url}
    result=expanded.discover_expanded(run,SOURCE,lambda u:r)
    assert result['candidates']
    assert any('2026-06-01' in c['published_at'] for c in result['candidates'])
    assert all(c['published_at'].startswith(('2026-06-01','2026-06-02')) for c in result['candidates'])


def test_repeated_real_feed_page_is_a_gap_instead_of_false_exhaustion():
    run=task();first=expanded.discover_expanded(run,SOURCE,lambda u:response(1));run['cursor']=first['next_cursor']
    second=expanded.discover_expanded(run,SOURCE,lambda u:response(1))
    assert second['outcome']=='gap' and second['gap_reason']=='atom_repeated_page'


def test_atom_batch_rejects_different_post_blog_or_feed_identity():
    r=response(1);data=atom.parse_atom_page(r.content,r.url,SOURCE);batches=WordPressBodyBatches(Store())
    refs=batches.store_batch(data['body_batch']);candidate=deepcopy(data['candidates'][0]);candidate['metadata']['publisher_post_id']+=1
    with pytest.raises(BatchBodyUnavailable,match='batch_post_id_mismatch'):batches.read_body(refs[0],candidate)
    broken=deepcopy(data['body_batch']);broken['records'][0]['blog_id']='1'
    with pytest.raises(BatchBodyUnavailable,match='batch_atom_provenance_invalid'):batches.store_batch(broken)
    assert not atom.publisher_next_url('https://www.blogger.com/feeds/999/posts/default?start-index=26&max-results=25',r.url,SOURCE,atom.VERIFIED_BLOG_IDS[SOURCE['key']])
    assert not atom.publisher_next_url('https://other.example/feed?start-index=26',r.url,SOURCE,atom.VERIFIED_BLOG_IDS[SOURCE['key']])


def test_missing_published_date_retains_discovery_without_inventing_today_or_using_updated():
    import xml.etree.ElementTree as ET
    r=response(1);root=ET.fromstring(r.content);entry=root.find(atom.ATOM+'entry');entry.remove(entry.find(atom.ATOM+'published'))
    data=atom.parse_atom_page(ET.tostring(root),r.url,SOURCE)
    assert data['candidates'][0]['published_at']=='' and data['candidates'][0]['metadata']['needs_date_review']
    assert len(data['body_batch']['records'])==24
