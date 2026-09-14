"""Real Gênero e Número pages with published text absent from content.rendered."""
import gzip
import hashlib
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
import pytest

from web_app.political_discovery import extract_article
from web_app.political_editorial_extraction import EXTRACTION_VERSION, extract_for_publisher

ROOT=Path(__file__).parent/'fixtures/political_genero_editorial_real'
CASES=json.loads((ROOT/'manifest.json').read_text())['cases']


def real(case):
    raw=gzip.decompress((ROOT/case['file']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==case['sha256']
    return raw.decode('utf-8')


def normalize(text):
    return re.sub(r'\s+',' ',text).strip()


@pytest.mark.parametrize('case',CASES,ids=lambda c:c['name'])
def test_real_editorial_paragraphs_are_preserved_and_navigation_is_excluded(case):
    raw=real(case);result=extract_for_publisher(raw,case['url'])
    assert result and result['extraction_state']=='full_text'
    body=result['full_text'];assert len(body)>12000
    soup=BeautifulSoup(raw,'html.parser');container=soup.select_one('section.post-wrapper > div.content')
    paragraphs=container.select('div.text p')
    assert len(paragraphs)>15
    for p in paragraphs:
        text=normalize(p.get_text('',strip=False))
        assert text in normalize(body),text[:100]
    for quote in container.select('blockquote'):
        assert normalize(quote.get_text('',strip=False)) in normalize(body)
    assert 'Receba nossos conteúdos no WhatsApp' not in body
    assert 'Assine nossa newsletter semanal' not in body
    assert 'Apoie a Gênero e Número' not in body
    assert 'Quero apoiar' not in body
    assert result['published_at']==case['publication_day']+'T03:00:00+00:00'
    assert result['extraction_method']=='publisher_selector:'+case['selector']
    assert result['extraction_version']==EXTRACTION_VERSION
    assert result['text_extent']=='available' and not result['restriction_evidence']
    assert result['title']==soup.find('h1').get_text(' ',strip=True)
    assert extract_article(raw,case['url'])['full_text']==body


def test_inline_drop_cap_and_citations_do_not_break_words_or_paragraphs():
    result=extract_for_publisher(real(CASES[0]),CASES[0]['url'])
    assert result['full_text'].startswith('As eleições brasileiras têm produzido')
    assert '\n\n' in result['full_text']
    assert 'Mulheres, Poder e Ciência Política' in result['full_text']


def test_a_sidebar_content_container_is_not_an_editorial_body():
    # Retain the real page content but remove only the publisher's article-root
    # class. A .content name alone must not broaden extraction to the page.
    raw=real(CASES[0]).replace('class="post-wrapper"','class="unrelated-wrapper"')
    assert extract_for_publisher(raw,CASES[0]['url']) is None
