"""Verified publisher post types must have separate durable discovery cursors."""
import json
from types import SimpleNamespace
from urllib.parse import urlparse,parse_qs

import pytest

from web_app import political_discovery as discovery

SOURCE={'key':'veja_rio','name':'Veja Rio','domain':'vejario.abril.com.br','base_url':'https://vejario.abril.com.br',
        'strategies':['wordpress'],'wordpress_rest_bases':['posts','blog_post'],'enabled':True}
TARGETS=[{'key':'cavaliere','display_name':'Eduardo Cavaliere','keywords':['Eduardo Cavaliere']}]


def test_new_column_tasks_are_distinct_but_existing_posts_payloads_keep_dedupe_identity(monkeypatch):
    monkeypatch.setattr(discovery,'load_sources',lambda:[{k:v for k,v in SOURCE.items() if k!='wordpress_rest_bases'}])
    old=discovery.build_tasks(TARGETS,'2026-06-01','2026-09-09',['veja_rio'])
    monkeypatch.setattr(discovery,'load_sources',lambda:[SOURCE])
    new=discovery.build_tasks(TARGETS,'2026-06-01','2026-09-09',['veja_rio'])
    assert [r for r in new if r.get('rest_base','posts')=='posts']==old
    columns=[r for r in new if r.get('rest_base')=='blog_post']
    assert len(old)==len(columns)==15 and len(new)==30
    assert len({json.dumps(r,sort_keys=True) for r in new})==30
    assert columns[0]['date_from']=='2026-06-01' and columns[-1]['date_to']=='2026-09-09'
    assert all(r['target_ids']==['cavaliere'] and r['cursor']=={'page':1} for r in columns)


def test_columns_use_advertised_endpoint_and_preserve_body_only_candidate_and_raw_page_cursor():
    task={'source_key':'veja_rio','strategy':'wordpress','rest_base':'blog_post','date_from':'2026-06-29','date_to':'2026-07-05','cursor':{'page':2}}
    rows=[{'id':519449,'link':'https://vejario.abril.com.br/coluna/lu-lacerda/lapa-a-escadaria-selaron-vai-ficar-tinindo-de-nova/',
           'date':'2026-07-03T11:09:56','date_gmt':'2026-07-03T14:09:56','title':{'rendered':'Lapa: a Escadaria Selarón vai ficar tinindo de nova'},
           'excerpt':{'rendered':'Trecho sem nomes.'}},
          {'id':2,'link':'https://other.example/not-the-publisher','date_gmt':'2026-07-03T12:00:00'}]
    urls=[]
    def fetch(url):urls.append(url);return SimpleNamespace(status_code=200,headers={'X-WP-TotalPages':'3'},text=json.dumps(rows))
    result=discovery._wordpress(task,SOURCE,fetch)
    assert urlparse(urls[0]).path=='/wp-json/wp/v2/blog_post'
    assert parse_qs(urlparse(urls[0]).query)['page']==['2']
    assert result['raw_count']==2 and result['next_cursor']=={'page':3}
    assert len(result['candidates'])==1 and result['candidates'][0]['metadata']['wordpress_rest_base']=='blog_post'
    assert result['candidates'][0]['published_at']=='2026-07-03T14:09:56+00:00'
    assert 'Eduardo Cavaliere' not in json.dumps(result['candidates'])  # candidates survive until article-body matching
    assert 'body_batch' not in result  # Veja body-batch support has not been verified


@pytest.mark.parametrize('base',['pages','../private','blog_post/519449','https://other.example'])
def test_unadvertised_or_unsafe_rest_bases_never_make_requests(base):
    task={'rest_base':base,'date_from':'2026-06-01','date_to':'2026-06-02','cursor':{}}
    with pytest.raises(discovery.DiscoveryError,match='unadvertised'):
        discovery._wordpress(task,SOURCE,lambda *a:pytest.fail('unadvertised endpoint requested'))


def test_column_rate_limit_remains_a_source_gap_without_silent_exhaustion():
    task={'rest_base':'blog_post','date_from':'2026-06-01','date_to':'2026-06-02','cursor':{'page':2}}
    with pytest.raises(discovery.DiscoveryError) as caught:
        discovery._wordpress(task,SOURCE,lambda *a:SimpleNamespace(status_code=429,headers={'Retry-After':'60'},text=''))
    assert caught.value.status_code==429 and caught.value.retryable
