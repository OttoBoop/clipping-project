"""IstoÉ source integration, using preserved public pages/XML (not news counts)."""
import gzip
import json
import re
from pathlib import Path

import pytest
import requests

from web_app.political_discovery import build_tasks, discover, extract_article, fallback_tasks, DiscoveryError, in_window
from web_app.political_source_catalog import catalog_sources

FIXTURES = Path(__file__).parent / 'fixtures' / 'political_istoe'
SOURCE = next(s for s in catalog_sources() if s['key'] == 'istoe')
PEOPLE = [{'key':'paes','display_name':'Eduardo Paes','keywords':['Eduardo Paes']},
          {'key':'cavaliere','display_name':'Eduardo Cavaliere','keywords':['Eduardo Cavaliere']}]


def response(url, name):
    r = requests.Response()
    r.status_code, r.url = 200, url
    r._content = gzip.decompress((FIXTURES/name).read_bytes())
    r.encoding = 'utf-8'
    return r


def root():
    return build_tasks(PEOPLE, '2026-06-01','2026-09-10',['istoe'],[SOURCE])[0]


def test_shared_inventory_zero_google_even_with_old_fallback_snapshot():
    tasks = build_tasks(PEOPLE, '2026-06-01','2026-09-10',['istoe'],[SOURCE])
    assert len(tasks) == 1 and tasks[0]['strategy'] == 'istoe_direct_v1'
    old = {**SOURCE,'strategies':['expanded','google_news'],'google_policy':'on_direct_gap'}
    assert fallback_tasks({**tasks[0],'source_snapshot':old}, PEOPLE) == []
    with pytest.raises(DiscoveryError,match='istoe_google_disabled'):
        discover({**tasks[0],'strategy':'google_news'},lambda *_:pytest.fail('network called'))


def test_root_has_bounded_resumable_inventory_without_fixed_minimum_part():
    first = discover(root(),lambda url:response(url,'index.xml.gz'))
    assert len(first['child_tasks']) == 32
    assert first['istoe_inventory'] == {'partsTotal':604,'partsAdmitted':32,'partsRemaining':572,'googleRequests':0}
    assert first['outcome'] == 'gap' and first['gap_reason']=='istoe_inventory_batch_limit'
    second = discover({**root(),'cursor':first['next_cursor']},lambda url:response(url,'index.xml.gz'))
    assert len(second['child_tasks'])==32
    assert not {c['url'] for c in first['child_tasks']} & {c['url'] for c in second['child_tasks']}


def test_all_article_urls_inventoried_without_name_or_title_filter_and_lastmod_not_publication():
    first = discover(root(),lambda url:response(url,'index.xml.gz'))
    task = next(t for t in first['child_tasks'] if t['url'].endswith('-603.xml'))
    rows=[]
    for _ in range(4):
        result=discover(task,lambda url:response(url,'wp-sitemap-posts-post-603.xml.gz'))
        assert len(result['candidates'])==500
        rows.extend(result['candidates']);task={**task,'cursor':result['next_cursor']}
    assert len(rows)==2000
    assert all(not c['published_at'] for c in rows)
    assert result['outcome']=='gap' and result['gap_reason']=='istoe_unverified_older_urls'
    assert sum(c['istoe_defer_body'] for c in rows)==648
    target=next(c for c in rows if '/tse-julga-recurso-claudio-castro-eleicao-rio' in c['url'])
    assert not target['istoe_defer_body'] and target['title']==''
    assert target['source_key']=='istoe'


def test_snapshot_mismatch_stops_without_advancing():
    result=discover(root(),lambda url:response(url,'index.xml.gz'))
    def changed(url):
        r=response(url,'index.xml.gz');r._content+=b'\n';return r
    with pytest.raises(DiscoveryError,match='snapshot_changed'):
        discover({**root(),'cursor':result['next_cursor']},changed)


@pytest.mark.parametrize('article',json.loads((FIXTURES/'articles.json').read_text()))
def test_real_editorial_blocks_dates_and_provenance(article):
    raw=gzip.decompress((FIXTURES/article['file']).read_bytes()).decode()
    extracted=extract_article(raw,article['url'])
    normalize=lambda s: re.sub(r'\s+',' ',s).strip()
    text=normalize(extracted['full_text'])
    for block in article['blocks']:
        assert normalize(block) in text
    assert extracted['published_at']==article['published']
    assert extracted['extraction_version']=='istoe-editorial-1'
    assert extracted['text_extent']=='available'
    assert extracted['publication_date_evidence']['method']=='istoe_editorial_fields'


def test_body_only_mentions_and_multiple_people_unchanged_matching():
    from web_app.political_corpus import match_targets
    article=next(a for a in json.loads((FIXTURES/'articles.json').read_text()) if '/tse-julga' in a['url'])
    extracted=extract_article(gzip.decompress((FIXTURES/article['file']).read_bytes()).decode(),article['url'])
    targets=PEOPLE+[{'key':'ruas','display_name':'Douglas Ruas','keywords':['Douglas Ruas']}]
    assert 'Eduardo Paes' not in extracted['title']
    assert {h['target_key'] for h in match_targets(targets,extracted['title'],extracted['full_text'])}=={'paes','ruas'}


def test_sp_day_boundaries():
    assert not in_window('2026-06-01T02:59:59Z','2026-06-01','2026-06-01')
    assert in_window('2026-06-01T03:00:00Z','2026-06-01','2026-06-01')
    assert in_window('2026-06-02T02:59:59Z','2026-06-01','2026-06-01')
    assert not in_window('2026-06-02T03:00:00Z','2026-06-01','2026-06-01')


def test_sustained_resource_pressure_reduces_capacity_and_requires_healthy_recovery():
    from web_app.political_istoe_monitor import protection
    high={'memoryPercent':71,'webError':False}
    low={'memoryPercent':55,'webError':False}
    assert protection([high,high])=='hold'
    assert protection([high,high,high])=='reduce'
    assert protection([high,low,low,low,low])=='hold'
    assert protection([low]*5)=='restore'
    assert protection([{'webError':True}]*3)=='reduce'
    assert protection([{}]*5)=='hold'
