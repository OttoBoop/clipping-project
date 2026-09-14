"""Real public Folha slides previously stored as an empty-body failure."""
import gzip
import hashlib
import json
from pathlib import Path
from web_app.political_discovery import extract_article
from web_app.political_webstory_extraction import extract_folha_story

ROOT=Path(__file__).parent/'fixtures/political_folha_story_real'


def sample():
    record=json.loads((ROOT/'manifest.json').read_text())
    raw=gzip.decompress((ROOT/'225004.html.gz').read_bytes())
    assert hashlib.sha256(raw).hexdigest()==record['hash']
    return raw.decode(),record['url']


def test_all_editorial_slides_include_navigation_hidden_slides_in_order():
    raw,url=sample();result=extract_article(raw,url)
    paragraphs=result['full_text'].split('\n\n')
    assert len(paragraphs)==13
    assert paragraphs[0].startswith('Eduardo da Costa Paes nasceu')
    assert paragraphs[1].startswith('A trajetória política começou em 1990')
    assert paragraphs[-1].endswith('eleições de 2026')
    assert result['published_at']=='2026-08-28T18:51:49+00:00'
    assert result['content_format']=='web_story'
    assert result['text_extent']=='available'
    for unwanted in ['Sua assinatura ajuda','Veja as principais notícias','PRODUÇÃO DE WEB STORIES',
                     'IMAGENS','Parece que seu carrinho está vazio','Navegando Histórias']:
        assert unwanted not in result['full_text']


def test_story_adapter_does_not_handle_unrelated_hosts_or_regular_articles():
    raw,url=sample()
    assert extract_folha_story(raw,url.replace('www1.folha.uol.com.br','example.org')) is None
    assert extract_folha_story(raw,url.replace('/webstories/','/')) is None
