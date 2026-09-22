"""Real public publisher archive data; independent evaluation URLs live elsewhere."""
import gzip,json,hashlib
from pathlib import Path
from types import SimpleNamespace
from web_app import political_expanded_discovery as expanded
from web_app.political_exame_archive import _EditorialCards, public_archive_dates
FIX=Path(__file__).parent/'fixtures/political_exame_dates'
def load(fragment):
 row=next(x for x in json.loads((FIX/'manifest.json').read_text()) if fragment in x['url'])
 raw=gzip.decompress((FIX/(row['sha256']+'.gz')).read_bytes());assert hashlib.sha256(raw).hexdigest()==row['sha256']
 return SimpleNamespace(url=row['url'],text=raw.decode(),content=raw,status_code=200,headers={})
def run(fragment,first='2026-06-01',last='2026-09-14',cursor=None,budget=500):
 r=load(fragment);s=next(x for x in expanded.load_expanded_sources() if x['key']=='exame');t=next(t for t in expanded.build_expanded_tasks(s,first,last,[{'key':'eduardo_paes'}]) if t['strategy']=='expanded_sitemap');t.update(url=r.url,depth=1,cursor=cursor or {},candidate_budget=budget)
 return expanded.discover_expanded(t,s,lambda url:r)
def test_real_archive_dates_avoid_fetching_outside_period_cards():
 result=run('colunistas/adriano');assert result['candidates'];assert len(result['candidates'])<25
 assert all(c['published_at'] and not c['metadata']['needs_date_review'] for c in result['candidates'])
 assert result['next_cursor']['url'].endswith('/2/')
def test_real_old_video_page_stops_at_verified_publication_boundary():
 r=run('videos/revista');assert not r['candidates'];assert r['outcome']=='complete';assert r['archive_boundary']['remaining_pages']==3
 assert r['archive_boundary']['newest_publication'].startswith('2020-09-05')
def test_resume_dated_page_small_budget_preserves_every_candidate():
 expected=run('colunistas/adriano')['candidates'];cursor={};found=[]
 for _ in range(3):
  r=run('colunistas/adriano',cursor=cursor,budget=10);found.extend(r['candidates']);cursor=json.loads(json.dumps(r['next_cursor']))
 assert found==expected
 repeated=run('colunistas/adriano',cursor=cursor);assert repeated['gap_reason']=='expanded_repeated_archive_page'
def test_state_must_match_all_visible_cards_before_filtering():
 r=load('colunistas/adriano');p=_EditorialCards();p.feed(r.text);rows=dict(p.rows);assert public_archive_dates(p,rows,expanded._core())
 rows.pop(next(iter(rows)));assert public_archive_dates(p,rows,expanded._core()) is None
 assert public_archive_dates(p,{'https://exame.com/unrelated/article':'other'},expanded._core()) is None

def test_exact_real_archive_day_is_inclusive_sao_paulo():
 r=run('colunistas/adriano','2026-09-01','2026-09-01');assert len(r['candidates'])==1;assert r['candidates'][0]['published_at']=='2026-09-01T17:43:59+00:00'
 assert not run('colunistas/adriano','2026-09-02','2026-09-02')['candidates']
def test_real_daily_sitemap_handles_image_loc_without_losing_article_url():
 r=run('artigos/2026-08/09','2026-08-09','2026-08-09');assert len(r['candidates'])==67
 assert all(c['url'].startswith('https://exame.com/') and c['published_at'] for c in r['candidates'])
def test_new_source_configuration_never_schedules_google():
 s=next(x for x in expanded.load_expanded_sources() if x['key']=='exame');assert s['google_policy']=='never';assert s['strategies']==['expanded']

def test_real_exame_requests_remove_only_verified_redundant_redirect():
 from web_app.political_request_urls import publisher_article_request_url
 for row in json.loads((FIX/'request-form-comparison.json').read_text()):
  old,new=row['forms'];assert old['history']==[308] and new['history']==[]
  assert old['textHash']==new['textHash'] and old['date']==new['date']
  assert publisher_article_request_url(old['requested'])==new['requested']
  assert publisher_article_request_url(new['requested'])==new['requested']
 assert publisher_article_request_url('https://exame.com/artigos/2026-08/09/sitemap.xml')=='https://exame.com/artigos/2026-08/09/sitemap.xml'

def test_real_insight_body_and_visible_publication_preserve_metadata_conflict():
 from web_app.political_discovery import extract_article
 raw=gzip.decompress((FIX/'insight-vibra.html.gz').read_bytes())
 assert hashlib.sha256(raw).hexdigest()=='b5616532f6a19859b96538b38b2915bc7fa76a050811b9f35b88593b2757ed78'
 a=extract_article(raw.decode(),'https://exame.com/exame-in/alem-do-combustivel-a-aposta-da-vibra-em-dados-ia-e-marketing-de-assertividade')
 assert a['extraction_method']=='publisher_selector:main .news-content-container'
 assert 'Responsável por uma das operações mais complexas' in a['full_text']
 assert 'Transformando frentistas em consultores' in a['full_text']
 assert 'Li e concordo' not in a['full_text']
 assert 'LinkedIn Top Voices' not in a['full_text']
 assert a['published_at']=='2026-08-09T12:00:00+00:00'
 assert a['publication_date_evidence']['conflict']
 assert a['publication_date_evidence']['metadata_published']=='2026-08-09T09:00:31+00:00'

def test_real_category_sitemap_does_not_fetch_its_own_landing_page_as_article():
 r=run('categorias/brasil');assert r['structural_entries']==[{'url':'https://exame.com/brasil/','basis':'publisher_category_self_entry'}]
 assert r['candidates'];assert all(c['url']!='https://exame.com/brasil' for c in r['candidates'])

def test_real_short_publisher_slug_does_not_invalidate_all_archive_dates():
 r=run('car-and-fun');assert r['outcome']=='complete';assert not r['candidates'];assert r['archive_boundary']['newest_publication'].startswith('2020-12-18')
 old=run('car-and-fun','2020-02-12','2020-02-12');assert any(x['url'].endswith('/dois-em-um') for x in old['candidates'])

def test_real_malformed_publisher_title_is_literal_not_an_unknown_xml_entity():
 r=run('categorias/negocios','2026-06-01','2026-09-14')
 assert r['publisher_archive']['literal_ampersands_escaped']==1
 assert r['candidates']
 assert r['publisher_archive']['response_sha256']=='1e08608b101251d7c701e551c173880d6a34f4b0d0c20ef214ea7672f468ed08'

def test_archive_boundary_has_durable_publisher_provenance():
 r=run('videos/revista');assert r['publisher_archive']['boundary']==r['archive_boundary']
 assert r['publisher_archive']['response_sha256']==hashlib.sha256(load('videos/revista').content).hexdigest()

def test_real_invest_visible_date_corrects_mislabeled_utc_metadata():
 from web_app.political_discovery import extract_article
 raw=gzip.decompress((FIX/'invest-date.html.gz').read_bytes())
 assert hashlib.sha256(raw).hexdigest()=='b515d435fcd1f6e2c860c3b266b1f37a3ae4bdec23fab54fdeba33ac2e1c1590'
 a=extract_article(raw.decode(),'https://exame.com/invest/mercados/us-17-bilhoes-em-acoes-do-google-o-que-buffett-esta-comprando-na-bolsa-em-2026/')
 assert a['published_at']=='2026-08-15T20:20:00+00:00'
 assert a['publication_date_evidence']['metadata_published']=='2026-08-15T17:20:56+00:00'
 assert a['publication_date_evidence']['conflict']

def test_real_invest_routes_reuse_only_independently_advertised_daily_candidates():
 from web_app.political_exame_routes import find_alternative
 rows=json.loads((FIX/'invest-real-task-routing.json').read_text())
 for task in rows['broken']:
  alternative=find_alternative(task['payload'],rows['alternatives'])
  assert alternative and alternative['url']!=task['payload']['url']
  assert alternative['sitemap_url'].startswith('https://exame.com/artigos/')
  assert find_alternative({**task['payload'],'published_at':'2020-01-01T12:00:00+00:00'},rows['alternatives']) is None
  assert find_alternative({**task['payload'],'title':'different'},rows['alternatives']) is None
 assert find_alternative(rows['broken'][0]['payload'],[]) is None

def test_old_exame_metadata_dates_cannot_prune_rediscovered_day_boundaries():
 from web_app.political_jota_extraction import original_date_trusted
 url='https://exame.com/invest/mercados/us-17-bilhoes-em-acoes-do-google-o-que-buffett-esta-comprando-na-bolsa-em-2026/'
 assert not original_date_trusted(url,{})
 assert not original_date_trusted(url,{'publication_date_evidence':{'method':'article_metadata'}})
 assert original_date_trusted(url,{'publication_date_evidence':{'method':'exame_visible_publication_header'}})
