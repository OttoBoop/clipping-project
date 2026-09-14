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
    assert len(rows) == 65 and len({r['key'] for r in rows}) == 65
    assert sum('audit_state' in r for r in rows) == 38
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
