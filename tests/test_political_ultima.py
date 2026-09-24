"""Preserved publisher listings; protocol changes are not collection data."""
from pathlib import Path
from types import SimpleNamespace
import gzip,hashlib,json
from web_app.political_expanded_discovery import load_expanded_sources,build_expanded_tasks,discover_expanded
from web_app.political_ultima_archive import parse_page
FIX=Path(__file__).parent/'fixtures/political_ultima'
def response(name):
 p=next(r for r in json.loads((FIX/'provenance.json').read_text()) if r['name']==name)
 raw=gzip.decompress((FIX/(name+'.gz')).read_bytes());assert hashlib.sha256(raw).hexdigest()==p['sha256']
 return SimpleNamespace(content=raw,text=raw.decode(),url=p['url'],status_code=200,headers={})
def config():
 s=next(s for s in load_expanded_sources() if s['key']=='ultima_hora_online')
 return s,build_expanded_tasks(s,'2026-09-22','2026-09-22',[])[0]

def test_all_section_cards_exclude_ticker_and_preserve_undated_hero():
 r=response('archive1');rows,info=parse_page(r.text,r.url)
 assert len(rows)==29 and sum(not x['date'] for x in rows)==1
 assert rows[0]['undated_highlight'] and rows[-1]['date']=='2026-09-22'
 assert info['next_url'].endswith('?p=2') and info['page']==1
 s,t=config();out=discover_expanded(t,s,lambda u:r)
 assert len(out['candidates'])==10 and not out['candidates'][0]['published_at']
 assert 'noticia/vereador-jorge-canella' in out['candidates'][-1]['url']
 assert out['archive_response']==r.content and out['next_cursor']['page']==2
 assert s['google_policy']=='never' and s['strategies']==['expanded']

def test_resume_follows_publisher_next_and_checks_page():
 s,t=config();first=discover_expanded(t,s,lambda u:response('archive1'));t['cursor']=first['next_cursor']
 out=discover_expanded(t,s,lambda u:response('archive2'));assert out['next_cursor']['page']==3
 bad=discover_expanded(t,s,lambda u:response('archive1'));assert bad['gap_reason']=='ultima_archive_wrong_page'

def test_old_boundary_preserves_unknown_hero_without_inventing_date():
 s,t=config();t['cursor']={'page':100,'url':response('archive100').url,'older_pages':1,'previous_oldest':'2026-04-30'}
 r=discover_expanded(t,s,lambda u:response('archive100'))
 assert r['outcome']=='complete' and len(r['candidates'])==1 and not r['candidates'][0]['published_at']
 assert r['publisher_archive']['older_pages']==2

def test_failure_and_missing_pagination_are_not_completed():
 import pytest
 from web_app.political_discovery import DiscoveryError
 s,t=config();r=response('archive1');r.status_code=429;r.headers={'Retry-After':'12'}
 with pytest.raises(DiscoveryError) as e:discover_expanded(t,s,lambda u:r)
 assert e.value.status_code==429 and e.value.retry_after==12
 r=response('archive1');r.content=r.content.replace(b'pagination',b'broken')
 out=discover_expanded(t,s,lambda u:r);assert out['gap_reason']=='ultima_archive_pagination_missing'

def test_missing_date_on_ordinary_card_is_fetched_and_stays_explicit():
 s,t=config();r=response('archive100');r.content=r.content.replace(b'29 de Abril de 2026',b'Data desconhecida')
 t['cursor']={'page':100,'url':r.url,'older_pages':1}
 out=discover_expanded(t,s,lambda u:r)
 assert len(out['candidates'])>1 and out['publisher_archive']['unknown_dates']>0
 assert out['next_cursor'] and out['next_cursor']['unknown_dates']>0


def test_missing_next_cannot_hide_a_publisher_announced_later_page():
 s,t=config();r=response('archive1')
 r.content=r.content.replace(b'aria-label="Next"',b'aria-label="Unavailable"').replace(b"aria-label='Next'",b"aria-label='Unavailable'")
 out=discover_expanded(t,s,lambda u:r)
 assert out['gap_reason']=='ultima_archive_next_missing' and out['publisher_archive']['last_page']>1


def test_real_author_index_discovers_all_routes_without_name_or_manual_urls():
 from web_app.political_ultima_archive import discover_columns
 s,_=config();tasks=build_expanded_tasks(s,'2026-08-09','2026-08-09',[{'key':str(i)} for i in range(35)])
 assert len(tasks)==2
 t=next(t for t in tasks if t['strategy']=='expanded_ultima_columns')
 r=discover_expanded(t,s,lambda url:response('authors'))
 assert len(r['child_tasks'])==51 and r['outcome']=='complete'
 assert all('/colunista-noticias/' in c['url'] and c['strategy']=='expanded_ultima_archive' for c in r['child_tasks'])
 assert r['archive_response']==response('authors').content
