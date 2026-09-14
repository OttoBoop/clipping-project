"""Publication fields on newly observed real publisher pages, not crawl dates."""
import gzip
import hashlib
import json
from pathlib import Path
import pytest
from web_app.political_discovery import extract_article

ROOT=Path(__file__).parent/'fixtures/political_new_dates_real'
CASES=json.loads((ROOT/'manifest.json').read_text())

@pytest.mark.parametrize('case',CASES,ids=lambda c:str(c['id']))
def test_real_publication_fields_and_undated_archives(case):
    raw=gzip.decompress((ROOT/case['fixture']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==case['sha256']
    result=extract_article(raw.decode(),case['url'])
    assert result['published_at']==case['expected_date']
    assert result['full_text']
    if 'folhadoslagos.com' in case['url']:
        assert 'Mais Lidas' not in result['full_text']
        assert 'Receba nossa newsletter' not in result['full_text']
        assert '14 de setembro de 2026' not in result['published_at']
    if case['id']==16328:
        assert result['text_extent']=='partial'
        assert 'editorial_body:complete_story_in_print_edition' in result['restriction_evidence']
