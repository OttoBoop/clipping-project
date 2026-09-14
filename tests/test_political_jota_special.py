"""Replays real public worker responses, never production archive inserts."""
import gzip,hashlib,json
from pathlib import Path
from bs4 import BeautifulSoup
import pytest
from web_app.political_discovery import extract_article
from web_app.political_jota_extraction import extract_jota_special,original_date_trusted

ROOT=Path(__file__).parent/'fixtures/political_jota_special'
PROOF=json.loads((ROOT/'provenance.json').read_text())

def real(n):
    raw=gzip.decompress((ROOT/f'{n}.html.gz').read_bytes())
    assert hashlib.sha256(raw).hexdigest()==PROOF[n]['sha256']
    return raw.decode(),PROOF[n]['url']


def change(n,mutation):
    raw,url=real(n);s=BeautifulSoup(raw,'html.parser');t=s.select_one('#__NEXT_DATA__');p=json.loads(t.string);mutation(p);t.string=json.dumps(p)
    return str(s),url


@pytest.mark.parametrize('n,expected_date,heading',[(0,'2015-12-31T13:02:27+00:00','O direito de família na legalidade constitucional'),(1,'2015-06-22T13:00:51+00:00','Introdução')])
def test_real_special_sections_recover_public_prose_and_original_date(n,expected_date,heading):
    raw,url=real(n);result=extract_article(raw,url)
    assert result['published_at']==expected_date
    assert len(result['full_text'])>25000 and heading in result['full_text']
    assert 'Atualizamos nossos Termos de uso' not in result['full_text']
    assert 'Trabalhe Conosco' not in result['full_text']
    assert result['text_extent']=='available' and result['extraction_method']=='publisher_next_data:post.sections'
    assert original_date_trusted(url,result)
    payload=json.loads(BeautifulSoup(raw,'html.parser').select_one('#__NEXT_DATA__').string)
    sections=payload['props']['pageProps']['post']['sections']
    for section in sections:
        assert section['title'].strip() in result['full_text']
    assert result['published_at']!=PROOF[n]['extraction']['published_at']


def test_missing_original_dates_never_fall_back_to_2026_jsonld():
    def mutate(p):
        p['props']['pageProps']['post']['dates']={};p['props']['pageProps']['post']['date']=''
    raw,url=change(0,mutate);r=extract_jota_special(raw,url)
    assert r['published_at']=='' and len(r['full_text'])>25000
    assert r['publication_date_evidence']['method']=='missing_original_post_date'
    assert not original_date_trusted(url,r)


def test_different_post_identity_does_not_use_embedded_prose():
    raw,url=change(0,lambda p:p['props']['pageProps']['post'].update(full_url='/especiais/another-post'))
    assert extract_jota_special(raw,url) is None


def test_ordinary_jota_pages_keep_existing_extractor_path():
    raw,url=change(0,lambda p:p.update(page='/ordinary-post/[slug]'))
    assert extract_jota_special(raw,url) is None


def test_pro_restriction_is_preserved_without_claiming_complete_text():
    raw,url=change(0,lambda p:p['props']['pageProps']['post'].update(inherits_from_PRO=True))
    r=extract_jota_special(raw,url)
    assert r['text_extent']=='unknown' and r['restriction_evidence']


def test_old_special_date_facts_are_not_trusted_but_other_products_are_unchanged():
    _,url=real(0)
    assert not original_date_trusted(url,{'publication_date_status':'page_verified'})
    assert original_date_trusted('https://www.jota.info/politica/news',{})
    assert original_date_trusted('https://publisher.example/especiais/story',{})
