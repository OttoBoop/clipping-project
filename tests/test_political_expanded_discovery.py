"""Protocol regressions replay immutable real public publisher responses.

Fixtures are discovery documents, not fabricated archive records. No test writes
or queues anything in production; provenance.json records their URLs and hashes.
"""
from copy import deepcopy
from dataclasses import dataclass, field
import gzip
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from web_app import political_expanded_discovery as expanded
from web_app import political_discovery as core

FIXTURES = Path(__file__).parent / 'fixtures' / 'political_expanded'


@dataclass
class Response:
    content: bytes
    status_code: int = 200
    headers: dict = field(default_factory=dict)
    url: str = ''

    @property
    def text(self):
        return self.content.decode('utf-8')


def response(name):
    provenance = next(r for r in json.loads((FIXTURES / 'provenance.json').read_text()) if r['name'] == name)
    raw = gzip.decompress((FIXTURES / (name + '.gz')).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == provenance['sha256']
    return Response(raw, headers=provenance['headers'], url=provenance['url'])


def source(key):
    return next(s for s in expanded.load_expanded_sources() if s['key'] == key)


def task(key, start='2026-08-09', end='2026-08-09'):
    return expanded.build_expanded_tasks(source(key), start, end, [{'key': 'paes', 'display_name': 'Eduardo Paes'}])[0]


def test_all_38_active_inventory_products_and_audited_nationals_have_scoped_routes():
    rows = expanded.load_expanded_sources()
    assert len(rows) == 70 and len({r['key'] for r in rows}) == 70
    assert sum('audit_state' in r for r in rows) == 42
    assert all(r['allowed_profiles'] == ['psd_rj_2026'] and r['google_policy'] == 'on_direct_gap' for r in rows)
    assert all(r['evidence'] and r['mechanisms'] and r['legacy_source_keys'] for r in rows)
    assert {'exame', 'congresso_em_foco', 'nf_noticias', 'elizeu_pires', 'ultima_hora_online', 'estadao', 'istoe', 'crusoe'} <= {r['key'] for r in rows}
    assert 'publisher:congressoemfoco.uol.com.br' in source('congresso_em_foco')['legacy_source_keys']


def test_publisher_discovery_does_not_multiply_by_people_or_inject_reference_urls():
    s = source('istoe')
    one = expanded.build_expanded_tasks(s, '2026-06-01', '2026-09-10', [{'key': 'one'}])
    many = expanded.build_expanded_tasks(s, '2026-06-01', '2026-09-10', [{'key': str(i)} for i in range(35)])
    assert len(one) == len(many) == 1
    assert many[0]['url'] == 'https://istoe.com.br/wp-sitemap.xml'
    assert len(many[0]['target_ids']) == 35
    assert not any(t['strategy'] == 'google_news' for t in many)


def test_actual_istoe_index_preserves_complete_audited_parts_and_explicit_residual_gap():
    run, s = task('istoe', '2026-06-01', '2026-09-10'), source('istoe')
    run['source_snapshot'] = {'frozen': True}
    children, outcomes = [], []
    while True:
        result = expanded.discover_expanded(run, s, lambda u: response('istoe_index'))
        assert len(result['child_tasks']) <= 100 and result['raw_count'] <= 100
        children += result['child_tasks']; outcomes.append(result['outcome'])
        if not result['next_cursor']:
            assert result['outcome'] == 'gap' and 'earlier_partitions' in result['gap_reason']
            break
        run['cursor'] = result['next_cursor']
    assert [r['url'] for r in children] == ['https://istoe.com.br/wp-sitemap-posts-post-603.xml', 'https://istoe.com.br/wp-sitemap-posts-post-604.xml']
    assert all(r['source_snapshot'] == {'frozen': True} for r in children)


def test_actual_istoe_leaf_batches_500_and_keeps_lastmod_as_hint_not_publication():
    s = source('istoe');run = {**task('istoe'), 'url': 'https://istoe.com.br/wp-sitemap-posts-post-603.xml', 'depth': 1}
    collected, counts = [], []
    while True:
        result = expanded.discover_expanded(run, s, lambda u: response('istoe_603'))
        counts.append(result['raw_count']);collected += result['candidates']
        assert len(result['candidates']) <= 500
        if not result['next_cursor']:
            break
        run['cursor'] = result['next_cursor']
    assert counts == [500, 500, 500, 500]
    assert len(collected) > 1900
    assert all(not c['published_at'] and c['metadata']['needs_date_review'] for c in collected)
    assert any(c['metadata']['sitemap_lastmod_hint'].startswith('2026-06-') for c in collected)
    assert any('tse-julga-recurso-claudio-castro' in c['url'] for c in collected)


def test_actual_veja_daily_sitemap_is_unpaged_and_does_not_request_phantom_page_two():
    s = source('veja');run = task('veja', '2026-06-24', '2026-06-24');calls=[]
    def fetch(url):
        calls.append(url);return response('veja_day')
    result = expanded.discover_expanded(run, s, fetch)
    assert calls == ['https://veja.abril.com.br/sitemap.xml?yyyy=2026&mm=06&dd=24']
    assert result['outcome'] == 'complete' and result['next_cursor'] is None
    assert result['raw_count'] > 0 and result['candidates']


def test_real_index_does_not_emit_unbounded_children():
    run = {**task('cnn_brasil', '2026-06-01', '2026-09-10'), 'strategy': 'expanded_sitemap', 'url': 'https://www.cnnbrasil.com.br/sitemap_index.xml', 'mechanism': {'kind': 'sitemap'}}
    result = expanded.discover_expanded(run, source('cnn_brasil'), lambda u: response('cnn_index'))
    assert len(result['child_tasks']) <= 100 and result['next_cursor']['offset'] == 100


def test_retry_after_429_propagates_without_claiming_completion():
    with pytest.raises(core.DiscoveryError) as info:
        expanded.discover_expanded(task('istoe'), source('istoe'), lambda u: Response(b'', 429, {'Retry-After': '60'}))
    assert info.value.retryable and info.value.status_code == 429 and info.value.retry_after == 60


def test_cross_publisher_sitemap_is_rejected_before_fetch():
    run = {**task('istoe'), 'url': 'https://www.acessa.com/sitemap.xml'}
    with pytest.raises(core.DiscoveryError, match='outside publisher'):
        expanded.discover_expanded(run, source('istoe'), lambda u: pytest.fail('must not fetch another publisher'))


def test_actual_wordpress_api_keeps_full_public_content_for_shared_fetches():
    s, run = source('elizeu_pires'), task('elizeu_pires');calls=[]
    def fetch(url, **kw):
        calls.append(url);return response('elizeu_api')
    result = expanded.discover_expanded(run, s, fetch)
    assert 'search' not in parse_qs(urlparse(calls[0]).query)
    assert result['raw_count'] == 2 and result['candidates']
    assert result['body_batch']['records']
    assert all(r['content_html'] and r['published_at'] for r in result['body_batch']['records'])
    assert all('content_html' not in c for c in result['candidates'])
    assert result['next_cursor'] is None  # The real response reports one page.


def test_actual_api_repeated_page_ends_as_gap():
    run, s = task('elizeu_pires'), source('elizeu_pires')
    first = expanded.discover_expanded(run, s, lambda u, **kw: response('elizeu_api'))
    rows = json.loads(response('elizeu_api').text)
    fingerprint = expanded._fingerprint(str(row['id']) + ':' + row['link'] for row in rows)
    repeated = expanded.discover_expanded({**run, 'cursor': {'page': 2, 'page_fingerprints': [fingerprint]}}, s, lambda u, **kw: response('elizeu_api'))
    assert repeated['outcome'] == 'gap' and repeated['gap_reason'] == 'expanded_repeated_api_page'


def test_frozen_source_configuration_is_used_instead_of_live_reload(monkeypatch):
    s, run = source('veja'), task('veja', '2026-06-24', '2026-06-24')
    monkeypatch.setattr(expanded, 'load_expanded_sources', lambda: pytest.fail('task must use frozen source'))
    assert expanded.discover_expanded(run, s, lambda u: response('veja_day'))['outcome'] == 'complete'


def test_calendar_pruning_covers_months_and_estadao_three_day_lag():
    assert expanded._partition('https://oantagonista.com.br/sitemap-posttype-post.202608.xml')[1].isoformat() == '2026-08-31'
    assert source('estadao')['mechanisms'][0]['calendar_tail_days'] == 3
    assert expanded._partition('https://noticias.r7.com/arc/outboundfeeds/sitemap/2026-08-24/')[0].isoformat() == '2026-08-24'


def test_real_body_batch_for_new_source_survives_object_readback():
    from web_app.political_body_batches import WordPressBodyBatches
    s, run = source('elizeu_pires'), task('elizeu_pires')
    result = expanded.discover_expanded(run, s, lambda u, **kw: response('elizeu_api'))
    class Store:
        prefix='real-protocol-test';enabled=True
        def __init__(self):self.objects={}
        def upload_bytes(self,data,key,kind):self.objects[key]=data;return True
        def read_political_object(self,key):return self.objects[key]
    store=Store();refs=WordPressBodyBatches(store).store_batch(result['body_batch'])
    reference=refs[0];candidate=next(c for c in result['candidates'] if c['metadata']['wordpress_id']==reference['post_id'])
    body=WordPressBodyBatches(store).read_body(reference,candidate)
    assert len(body['full_text'])>200 and body['canonical_url']==candidate['url']
    assert body['provenance']['method']=='wordpress_api_batch'


def public_feed_response(kind):
    directory=FIXTURES.parent / 'political_public_feed_real'
    row=next(r for r in json.loads((directory/'manifest.json').read_text())['responses'] if r['kind']==kind)
    raw=gzip.decompress((directory/row['body_file']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==row['sha256']
    return Response(raw,url=row['url'])


def test_worker_verified_rss_pagination_and_body_batches_resume_from_saved_page():
    s=source('diario_do_vale');run=task('diario_do_vale','2026-07-04','2026-07-05')
    calls=[]
    def fetch(url):calls.append(url);return public_feed_response('feed_history_page_150')
    result=expanded.discover_expanded({**run,'cursor':{'page':150}},s,fetch)
    assert calls==['https://diariodovale.com.br/feed/?paged=150']
    assert result['raw_count']==20 and result['candidates'] and result['body_batch']['records']
    assert all(r['body_origin']=='publisher_rss' for r in result['body_batch']['records'])
    assert result['next_cursor']['page']==151
    assert any('paes' in r['url'] for r in result['candidates'])


def test_actual_consecutive_rss_pages_end_after_two_ordered_pages_older_than_start():
    s=source('diario_do_vale');run=task('diario_do_vale','2026-09-15','2026-09-15')
    first=expanded.discover_expanded(run,s,lambda u:public_feed_response('advertised_feed'))
    assert first['next_cursor']['older_pages']==1
    second=expanded.discover_expanded({**run,'cursor':first['next_cursor']},s,lambda u:public_feed_response('feed_page_two'))
    assert second['outcome']=='complete' and second['next_cursor'] is None
    assert not second['candidates']


def test_actual_rss_ignored_pagination_is_a_gap_not_repeated_saved_articles():
    s=source('diario_do_vale');run=task('diario_do_vale','2026-06-01','2026-09-14')
    first=expanded.discover_expanded(run,s,lambda u:public_feed_response('advertised_feed'))
    second=expanded.discover_expanded({**run,'cursor':first['next_cursor']},s,lambda u:public_feed_response('feed_date_archive'))
    assert second['outcome']=='gap' and second['gap_reason']=='expanded_repeated_feed_page'


def test_api_start_boundary_requests_prior_second_without_changing_end_exclusivity():
    calls=[]
    expanded.discover_expanded(task('elizeu_pires'),source('elizeu_pires'),lambda u,**kw:(calls.append(u),response('elizeu_api'))[1])
    query=parse_qs(urlparse(calls[0]).query)
    assert query['after']==['2026-08-08T23:59:59']
    assert query['before']==['2026-08-10T00:00:00']


def metro_source():
    from web_app.political_source_catalog import catalog_sources
    return next(row for row in catalog_sources() if row['key'] == 'metropoles')


def test_current_metropoles_catalog_searches_brasil_and_all_columns_shared():
    s = metro_source()
    tasks = expanded.build_expanded_tasks(s, '2026-08-09', '2026-08-09', [{'key':str(i)} for i in range(35)])
    assert {t['section'] for t in tasks} == {'brasil', 'colunas'}
    assert len(tasks) == 2
    assert all(t['strategy'] == 'expanded_metropoles_archive' for t in tasks)
    assert not s['public_archive_action_bundle_hint']


def test_real_metropoles_stale_action_refresh_preserves_historical_progress():
    s = metro_source();run = expanded.build_expanded_tasks(s, '2026-08-09', '2026-08-09', [])[1]
    run['cursor'] = {'action_id':'404f01c3d0caa10b02ca3723e7fc61b7cbf5d9c8aa',
                     'after':'2026-08-09 12:00:00', 'page':7, 'parse_gap':True}
    calls=[]
    def fetch(url, **kwargs):
        calls.append((url,kwargs));result=response('metro_stale_action');result.status_code=404;return result
    result=expanded.discover_expanded(run,s,fetch)
    assert result['outcome']=='continue'
    assert result['next_cursor']['after']=='2026-08-09 12:00:00'
    assert result['next_cursor']['page']==7 and result['next_cursor']['parse_gap']
    assert result['next_cursor']['action_refresh_count']==1 and 'action_id' not in result['next_cursor']
    assert calls[0][1]['method']=='POST'
    run['cursor']=result['next_cursor']
    fresh=expanded.discover_expanded(run,s,lambda url:response('metro_brasil_page'))
    assets=fresh['next_cursor']['action_assets']
    assert 'https://assets-v4.metroimg.com/_next/static/chunks/3p1vg_mg74ng_.js' in assets
    assert 'https://assets-v4.metroimg.com/_next/static/chunks/3_-cu-39abe67.js' not in assets
    assert fresh['next_cursor']['page']==7


def test_actual_metropoles_current_javascript_yields_publisher_action():
    s=metro_source();run=expanded.build_expanded_tasks(s,'2026-08-09','2026-08-09',[])[1]
    asset=response('metro_current_action')
    run['cursor']={'action_assets':[asset.url],'asset_index':0,'after':'2026-08-10 00:00:00'}
    result=expanded.discover_expanded(run,s,lambda url:asset)
    assert result['next_cursor']['action_id']=='40a579897be38972ef04fa3b5ef195ca842a76a2ae'
    assert result['next_cursor']['action_asset']==asset.url


@pytest.mark.parametrize('section',['brasil','colunas'])
def test_real_metropoles_historical_rows_supply_editorial_candidates(section):
    s=metro_source();run=next(t for t in expanded.build_expanded_tasks(s,'2026-08-09','2026-08-09',[]) if t['section']==section)
    run['cursor']={'action_id':'40a579897be38972ef04fa3b5ef195ca842a76a2ae','action_refresh_count':1}
    calls=[]
    def fetch(url,**kwargs):
        calls.append(kwargs);return response('metro_'+section+'_aug9')
    result=expanded.discover_expanded(run,s,fetch)
    assert result['candidates'] and result['raw_count']>0
    assert all(core.in_window(c['published_at'],'2026-08-09','2026-08-09') for c in result['candidates'])
    assert all(c['metadata']['metropoles_public_archive']==section for c in result['candidates'])
    assert json.loads(calls[0]['data'])[0]['slug']==section
    if result['next_cursor']:
        assert result['next_cursor']['action_refresh_count']==1


def test_actual_ft_index_selects_requested_unpadded_months_only():
    s=source('financial_times');run=task('financial_times','2026-06-01','2026-09-10');children=[]
    while True:
        result=expanded.discover_expanded(run,s,lambda url:response('ft_historical_index'))
        children.extend(result['child_tasks'])
        if not result['next_cursor']:break
        run['cursor']=result['next_cursor']
    assert {c['url'] for c in children if '/archive-' in c['url']}=={'https://www.ft.com/sitemaps/archive-2026-'+str(m)+'.xml' for m in (6,7,8,9)}
    assert all('/archive-' in c['url'] or c['url']=='https://www.ft.com/sitemaps/news.xml' for c in children)


def test_real_lume_feed_discovers_body_only_reference_without_manual_seeding():
    s=source('agencia_lume');run=next(t for t in expanded.build_expanded_tasks(s,'2026-06-01','2026-09-10',[]) if t['strategy']=='expanded_feed')
    result=expanded.discover_expanded(run,s,lambda url:response('lume_public_feed'))
    assert result['raw_count']==20 and len(result['candidates'])==3
    # The discovery itself supplies all3 chronological candidates. Person/body
    # matching remains the fetch worker's responsibility.
    assert any('como-a-luta-de-moradores-de-jacarepagua' in c['url'] for c in result['candidates'])
    assert result['outcome']=='gap' and 'feed' in result['gap_reason']


def test_real_folha_lagos_full_sitemap_stays_bounded_and_does_not_treat_lastmod_as_publication():
    s=source('folha_dos_lagos');run={**task('folha_dos_lagos'),'url':'https://www.folhadoslagos.com/sitemaps/sitemap1.xml','depth':1}
    result=expanded.discover_expanded(run,s,lambda url:response('folha_lagos_historical_leaf'))
    assert result['raw_count']==500 and len(result['candidates'])<=500
    assert result['next_cursor']['offset']==500
    assert all(not c['published_at'] for c in result['candidates'])


def test_verified_custom_types_are_frozen_and_do_not_collapse_into_posts():
    s=source('azmina')
    runs=expanded.build_expanded_tasks(s,'2026-07-01','2026-07-31',[])
    assert {r['mechanism']['rest_base'] for r in runs}=={'posts','az_reportagem','az_coluna_article'}
    run=next(r for r in runs if r['mechanism']['rest_base']=='az_reportagem' and r['date_to']=='2026-07-31')
    # Use the same public month response with the month bounds it was fetched for.
    run.update(date_from='2026-07-01',date_to='2026-07-31')
    calls=[]
    def fetch(url):calls.append(url);return response('azmina_editorial_type')
    result=expanded.discover_expanded(run,s,fetch)
    assert len(result['candidates'])==2 and len(result['body_batch']['records'])==2
    assert '/wp/v2/az_reportagem?' in calls[0]
    assert all(c['metadata']['wordpress_rest_base']=='az_reportagem' for c in result['candidates'])
    assert all(len(r['content_html'])>5000 for r in result['body_batch']['records'])


def test_custom_type_empty_api_body_is_preserved_as_fetch_candidate_not_full_text():
    s=source('genero_e_numero');run=next(r for r in expanded.build_expanded_tasks(s,'2026-07-01','2026-07-31',[]) if r['mechanism']['rest_base']=='reportagens')
    run.update(date_from='2026-07-01',date_to='2026-07-31')
    result=expanded.discover_expanded(run,s,lambda url:response('genero_reportagens_type'))
    assert len(result['candidates'])==2 and all(c['published_at'] for c in result['candidates'])
    assert all(not r['content_html'] for r in result['body_batch']['records'])
    assert all(c['metadata']['wordpress_rest_base']=='reportagens' for c in result['candidates'])
    # read_body already rejects empty fragments, preserving the worker's normal
    # page-fetch fallback instead of claiming a complete editorial text.


def test_record_is_a_distinct_product_and_real_sitemap_yields_companion_articles():
    s=source('record');run={**task('record'),'url':'https://record.r7.com/arc/outboundfeeds/sitemap3/2026-08-09/','depth':1}
    result=expanded.discover_expanded(run,s,lambda url:response('record_aug9_sitemap'))
    assert result['candidates'] and result['raw_count']<=500
    assert all(c['source_key']=='record' and urlparse(c['url']).hostname=='record.r7.com' for c in result['candidates'])
    assert s['legacy_source_keys']==['publisher:record.r7.com']
    assert 'publisher:record.r7.com' not in source('r7')['legacy_source_keys']
