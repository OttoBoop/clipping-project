"""Real Elizeu responses; protocol perturbations never enter collection totals."""
import gzip,hashlib,json
from pathlib import Path
from copy import deepcopy
from urllib.parse import parse_qs,urlparse
from types import SimpleNamespace

from web_app.political_expanded_discovery import load_expanded_sources,build_expanded_tasks,discover_expanded
from web_app.political_discovery import extract_article
from web_app.political_body_batches import WordPressBodyBatches

FIX=Path(__file__).parent/'fixtures/political_elizeu'
def response(name):
 p=next(r for r in json.loads((FIX/'provenance.json').read_text()) if r['name']==name)
 raw=gzip.decompress((FIX/(name+'.gz')).read_bytes());assert hashlib.sha256(raw).hexdigest()==p['sha256']
 return SimpleNamespace(content=raw,text=raw.decode(),url=p['url'],status_code=200,headers=p['headers'])
def source():return next(s for s in load_expanded_sources() if s['key']=='elizeu_pires')
def task():
 s=source();s['mechanisms'][0]['page_size']=2
 return s,build_expanded_tasks(s,'2026-09-11','2026-09-14',[{'key':'eduardo_paes'}])[0]

class Store:
 prefix='protocol-test';enabled=True
 def __init__(self):self.objects={}
 def upload_bytes(self,data,key,kind):self.objects[key]=data;return True
 def read_political_object(self,key):return self.objects[key]

def test_real_related_block_removed_without_losing_editorial_paragraphs():
 r=response('related');a=extract_article(r.text,r.url)
 assert 'Foi isso que o prefeito de Paraíba do Sul' in a['full_text']
 assert 'Dayse Onofre' in a['full_text']
 assert 'Matérias relacionadas' not in a['full_text']
 assert 'Jogando no campo do adversário' not in a['full_text']
 assert 'Recepção a Paes em Casimiro' not in a['full_text']

def test_real_api_after_utc_midnight_stays_in_sao_paulo_end_day_and_is_preserved():
 s,t=task();calls=[]
 def fetch(url):calls.append(url);return response('api_late')
 result=discover_expanded(t,s,fetch)
 assert len(result['candidates'])==2 and result['candidates'][0]['published_at'].startswith('2026-09-15T01:10')
 assert result['archive_response']==response('api_late').content
 assert result['publisher_archive']['announcedTotal']==534
 assert result['next_cursor']['inventory_rows']==2
 assert 'search' not in parse_qs(urlparse(calls[0]).query)
 assert source()['google_policy']=='never' and source()['strategies']==['expanded']
 batch=WordPressBodyBatches(Store());refs=batch.store_batch(result['body_batch'])
 body=batch.read_body(refs[0],result['candidates'][0]);assert body['provenance']['editorial_extraction']['version']=='editorial-2026-09-23.1'
 assert '30 bilhões' in body['full_text']

def test_real_rows_with_unknown_dates_are_sent_to_page_extraction():
 s,t=task();r=response('api_late');rows=json.loads(r.text);rows[0]['date_gmt']=rows[0]['date']='';r.text=json.dumps(rows);r.content=r.text.encode()
 out=discover_expanded(t,s,lambda url:r)
 assert len(out['candidates'])==2 and not out['candidates'][0]['published_at']
 assert out['candidates'][0]['metadata']['needs_date_review']
 assert len(out['body_batch']['records'])==1

def test_same_actual_page_on_resume_remains_a_gap():
 s,t=task();first=discover_expanded(t,s,lambda url:response('api_late'));t['cursor']=first['next_cursor']
 second=discover_expanded(t,s,lambda url:response('api_late'))
 assert second['outcome']=='gap' and second['gap_reason']=='expanded_repeated_api_page'
 assert second['archive_response']==response('api_late').content

def test_missing_total_is_explicit_gap_with_receipt():
 s,t=task();r=response('api_late');r.headers={}
 out=discover_expanded(t,s,lambda url:r);assert out['outcome']=='gap' and out['gap_reason']=='elizeu_inventory_total_unverified'
