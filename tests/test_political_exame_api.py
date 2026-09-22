"""Real public API responses compared with independently preserved page bodies."""
import gzip
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from web_app import political_expanded_discovery as expanded
from web_app.political_body_batches import WordPressBodyBatches, BatchBodyUnavailable
from web_app.political_discovery import extract_article, in_window
from web_app.political_exame_api import publication, cache_candidate, reuse_candidate
from web_app.political_rate_limits import normalize_domain

FIX = Path(__file__).parent / 'fixtures/political_exame_api'


class Store:
    enabled = True
    prefix = 'test-exame-real-api'
    def __init__(self): self.objects = {}
    def upload_bytes(self, data, key, content_type): self.objects[key] = data; return True
    def read_political_object(self, key): return self.objects[key]


def response():
    raw = gzip.decompress((FIX/'aug09-page1.json.gz').read_bytes())
    manifest = json.loads((FIX/'manifest.json').read_text())
    assert hashlib.sha256(raw).hexdigest() == manifest['api']['hash']
    return SimpleNamespace(content=raw,text=raw.decode(),status_code=200,headers={'X-WP-TotalPages':'2'})


def discovered(cursor=None):
    source = next(s for s in expanded.load_expanded_sources() if s['key']=='exame')
    task = next(t for t in expanded.build_expanded_tasks(source,'2026-08-09','2026-08-09',[])
                if t['strategy']=='expanded_wordpress')
    task['cursor'] = cursor or {}
    urls=[]
    result=expanded.discover_expanded(task,source,lambda url:(urls.append(url) or response()))
    return result, urls


def test_real_api_date_scan_carries_full_bodies_in_bounded_objects():
    result,urls=discovered()
    assert len(result['candidates']) == len(result['body_batch']['records']) == 50
    assert all(in_window(c['published_at'],'2026-08-09','2026-08-09') for c in result['candidates'])
    assert result['candidates'][0]['published_at']=='2026-08-10T00:50:06+00:00'
    params=parse_qs(urlparse(urls[0]).query)
    assert params['after']==['2026-08-08T23:59:59']
    assert params['before']==['2026-08-09T23:59:59']
    assert result['next_cursor']['page']==2
    repeated,_=discovered(result['next_cursor'])
    assert repeated['gap_reason']=='expanded_repeated_api_page'


def test_real_api_and_pages_have_identical_normalized_editorial_bodies_after_restart():
    result,_=discovered();store=Store();refs=WordPressBodyBatches(store).store_batch(result['body_batch'])
    reader=WordPressBodyBatches(store)
    candidates={c['metadata']['wordpress_id']:c for c in result['candidates']}
    refs={r['post_id']:r for r in refs}
    for row in json.loads((FIX/'manifest.json').read_text())['pages']:
        raw=gzip.decompress((FIX/(str(row['publisherPostId'])+'.html.gz')).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==row['pageResponseHash']
        actual=reader.read_body(refs[row['publisherPostId']],candidates[row['publisherPostId']])
        page=extract_article(raw.decode(),url=row['url'])
        assert ' '.join(actual['full_text'].split())==' '.join(page['full_text'].split())
        assert row['dateMatchesAtMinutePrecision'] and row['paragraphs']==row['present']


def test_cache_reuses_a_body_not_a_previous_matching_outcome_or_target_rules():
    result,_=discovered();c=result['candidates'][0]
    refs=WordPressBodyBatches(Store()).store_batch(result['body_batch'])
    c={**c,'body_batch_ref':refs[0]}
    cached=cache_candidate(c)
    old={**c,'source_snapshot':{'frozen':'original'},'metadata':{'original_discovery':'sitemap'}}
    old.pop('body_batch_ref')
    reused=reuse_candidate(old,cached)
    assert reused['body_batch_ref']==refs[0]
    assert reused['source_snapshot']==old['source_snapshot']
    assert reused['metadata']['original_discovery']=='sitemap'
    assert not {'target_keys','target_snapshots','disposition'} & cached.keys()
    other={**old,'url':'https://exame.com/brasil/different'}
    assert reuse_candidate(other,cached)==other


def test_unverified_api_clock_cannot_supply_a_cached_body_date():
    row=json.loads(response().text)[0]
    date,evidence=publication(row,'a'*64,'https://classic.exame.com/wp-json/wp/v2/posts')
    assert date and evidence['method']=='exame_public_wordpress_api'
    broken=deepcopy(row);broken['date_gmt']=broken['date']
    date,evidence=publication(broken,'a'*64,'https://classic.exame.com/wp-json/wp/v2/posts')
    assert date=='' and evidence['method']=='exame_api_date_unverified'


def test_exame_api_and_website_share_one_request_budget():
    assert normalize_domain('classic.exame.com')==normalize_domain('www.exame.com')=='exame.com'
    assert normalize_domain('other.example.com')=='other.example.com'


def test_protected_or_missing_cached_api_object_still_requires_page_fallback():
    result,_=discovered();store=Store();writer=WordPressBodyBatches(store)
    result['body_batch']['records'][0]['protected']=True
    refs=writer.store_batch(result['body_batch'])
    with pytest.raises(BatchBodyUnavailable,match='batch_text_unavailable'):
        writer.read_body(refs[0],result['candidates'][0])
    store.objects.clear()
    with pytest.raises(BatchBodyUnavailable,match='batch_read_failed'):
        WordPressBodyBatches(store).read_body(refs[1],result['candidates'][1])
