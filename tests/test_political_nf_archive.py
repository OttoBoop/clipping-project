import gzip,hashlib,json
from pathlib import Path
from types import SimpleNamespace
from web_app import political_nf_archive as nf
from web_app import political_expanded_discovery as expanded
from web_app.political_discovery import extract_article

F=Path(__file__).parent/'fixtures/political_nf_archive'
def response(name):
 r=next(x for x in json.loads((F/'manifest.json').read_text()) if x['name']==name)
 raw=gzip.decompress((F/(name+'.html.gz')).read_bytes());assert hashlib.sha256(raw).hexdigest()==r['sha256']
 return SimpleNamespace(content=raw,text=raw.decode('utf8','replace'),url=r['url'],status_code=200,headers={})
def setup(product='news',first='2026-06-01',last='2026-09-14'):
 source=next(s for s in expanded.load_expanded_sources() if s['key']=='nf_noticias')
 task=next(t for t in expanded.build_expanded_tasks(source,first,last,[{'key':'eduardo_paes'}]) if t['mechanism']['product']==product)
 return task,source

def test_news_real_pages_resume_and_dates_do_not_use_sidebar():
 task,src=setup(last='2026-09-23');one=nf.discover(task,src,lambda u:response('news'))
 assert len(one['candidates'])==12 and one['next_cursor']['page']==2
 task['cursor']=json.loads(json.dumps(one['next_cursor']));two=nf.discover(task,src,lambda u:response('page2'))
 assert len(two['candidates'])==12
 assert not set(x['url'] for x in one['candidates'])&set(x['url'] for x in two['candidates'])
 assert all(x['metadata']['archive_reported_date']=='2026-09-22' for x in two['candidates'])
 assert two['archive_response']==response('page2').content

def test_wrong_page_is_gap():
 task,src=setup();task['cursor']={'url':response('page2').url,'page':2}
 wrong=response('news');wrong.url=response('page2').url
 assert nf.discover(task,src,lambda u:wrong)['gap_reason']=='nf_archive_wrong_page'

def test_real_old_page_uses_two_ordered_boundaries():
 task,src=setup(first='2026-08-09',last='2026-08-09');task['cursor']={'url':response('page100').url,'page':100}
 one=nf.discover(task,src,lambda u:response('page100'));assert not one['candidates'] and one['next_cursor']['older_pages']==1
 # State from an earlier observed page; same real response closes the second boundary.
 task['cursor'].update(older_pages=1,previous_oldest='2026-06-24')
 two=nf.discover(task,src,lambda u:response('page100'));assert two['outcome']=='complete' and not two['next_cursor']

def test_repeat_cap_and_unknown_chronology_stay_visible():
 task,src=setup();task['cursor']={'url':response('page100').url,'page':100};task['mechanism']['max_pages']=100
 r=nf.discover(task,src,lambda u:response('page100'));assert r['gap_reason']=='nf_archive_page_cap'
 fingerprint=hashlib.sha256('\n'.join(x['url'] for x in nf.parse_page(response('page100').text,response('page100').url,'news')[0]).encode()).hexdigest()
 task['cursor']['fingerprints']=[fingerprint]
 assert nf.discover(task,src,lambda u:response('page100'))['gap_reason']=='nf_archive_repeated_page'

def test_home_exposes_seven_author_calendars_without_search_tasks():
 task,src=setup('columns_index');r=nf.discover(task,src,lambda u:response('home'))
 assert len(r['child_tasks'])==7 and src['google_policy']=='disabled'
 assert all(x['mechanism']['product']=='column' and x['cursor']=={} for x in r['child_tasks'])

def test_column_reads_month_table_and_current_post():
 task,src=setup();task.update(url=response('column').url,mechanism={'kind':'nf_archive','product':'column','url':response('column').url})
 r=nf.discover(task,src,lambda u:response('column'))
 assert r['outcome']=='complete';assert r['publisher_archive']['calendar_months']>20
 assert any('/post/876/' in x['url'] for x in r['candidates'])
 assert any('/post/864/' in x['url'] and x['published_at'].startswith('2026-06-12') for x in r['candidates'])
 assert all('/cleytonlacerda/' in x['url'] for x in r['candidates'])

def test_existing_extractor_keeps_real_body_mention_and_publication():
 r=response('article');a=extract_article(r.text,r.url)
 assert 'Eduardo Paes' not in a['title'] and 'Eduardo Paes' in a['full_text']
 assert a['published_at'].startswith('2026-07-29T18:11')
 assert 'TRE-RJ inicia preparação' not in a['full_text']


def test_invalid_author_links_before_requested_period_are_explicitly_outside():
 for name in ['older_mixed_author1','older_mixed_author2']:
  task,src=setup();r=response(name);task.update(url=r.url,mechanism={'kind':'nf_archive','product':'column','url':r.url})
  result=nf.discover(task,src,lambda u:r)
  assert result['outcome']=='complete' and not result['candidates']
  assert result['publisher_archive']['invalid_identity_outside_window']>0
  task['date_from']='2017-01-01'
  result=nf.discover(task,src,lambda u:r)
  assert result['gap_reason']=='nf_column_invalid_identity'


def test_event_listing_keeps_public_articles_but_reports_historical_gap():
 task,src=setup('events');r=response('events');result=nf.discover(task,src,lambda u:r)
 assert len(result['candidates'])==10 and result['gap_reason']=='nf_events_history_not_proven'
 assert all('/evento-' in x['url'] and x['published_at'] for x in result['candidates'])
 assert not any('/noticia-' in x['url'] for x in result['candidates'])
 a=extract_article(response('event_article').text,response('event_article').url)
 assert a['published_at'].startswith('2026-09-11T03:00') and len(a['full_text'])>2000
