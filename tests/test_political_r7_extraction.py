"""Real production failures with published text accompanying R7/Record videos."""
import gzip
import hashlib
import json
from pathlib import Path
import pytest
from web_app.political_discovery import extract_article
from web_app.political_r7_extraction import extract_video_companion

FIXTURES=Path(__file__).parent/'fixtures/political_r7_real'
CASES={row['task']:row for row in json.loads((FIXTURES/'manifest.json').read_text())['cases']}


def read(ident):
    row=CASES[ident]
    raw=gzip.decompress((FIXTURES/row['fixture']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==row['hash']
    return raw.decode(),row['url']


@pytest.mark.parametrize('ident,expected_date,ending',[
    (225007,'2026-07-21T04:27:20+00:00','o deputado federal Marcelo Crivella.'),
    (225022,'2026-08-10T19:12:25+00:00','mobilidade urbana e segurança pública.'),
    (225024,'2026-08-18T18:12:52+00:00','William Siri, do PSOL.'),
])
def test_real_video_editorial_text_and_original_publication(ident,expected_date,ending):
    raw,url=read(ident)
    result=extract_article(raw,url)
    assert result['full_text'].endswith(ending)
    assert 'Eduardo Paes' in result['full_text']
    assert result['published_at']==expected_date
    assert result['content_format']=='video_companion_text'
    assert result['text_extent']=='unknown'
    assert 'No RecordPlus' not in result['full_text']
    assert 'Veja também' not in result['full_text']
    assert 'Adicione como fonte' not in result['full_text']
    assert 'Assista à íntegra da 2ª edição do JR 24 Horas desta quarta' not in result['full_text']


def test_embedded_video_without_published_editorial_body_is_not_a_transcript():
    raw,url=read(225008)
    assert extract_video_companion(raw,url) is None
    assert extract_article(raw,url)['extraction_state']=='metadata_only'


def test_primary_fusion_identity_must_match_the_requested_page():
    raw,url=read(225007)
    assert extract_video_companion(raw,'https://noticias.r7.com/another-story/') is None
    assert extract_video_companion(raw,url.replace('noticias.r7.com','unrelated.example')) is None


def test_metadata_description_is_never_a_body_fallback():
    raw,url=read(225022)
    raw=raw.replace('"subheadlines":','"unavailable_subheadlines":')
    result=extract_video_companion(raw,url)
    assert not result['full_text']
    assert result['text_extent']=='absent'
