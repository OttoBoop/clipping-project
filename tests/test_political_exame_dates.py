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
 r=load(fragment);s=next(x for x in expanded.load_expanded_sources() if x['key']=='exame');t=expanded.build_expanded_tasks(s,first,last,[{'key':'eduardo_paes'}])[0];t.update(url=r.url,depth=1,cursor=cursor or {},candidate_budget=budget)
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
