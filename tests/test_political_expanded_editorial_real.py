"""New live failure cases; these fixtures never count as collected records."""
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from web_app.political_editorial_extraction import extract_for_publisher
from web_app.political_request_urls import is_publisher_access_challenge

ROOT=Path(__file__).parent/'fixtures/political_expanded_editorial_real'
CASES=json.loads((ROOT/'manifest.json').read_text())['cases']


@pytest.mark.parametrize('case',CASES,ids=lambda c:str(c['taskId']))
def test_real_response_editorial_roots_and_access_challenges(case):
    raw=gzip.decompress((ROOT/case['fixture']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==case['htmlHash']
    html=raw.decode()
    if case['expected']=='access_challenge':
        assert is_publisher_access_challenge(case['url'],html)
        return
    assert not is_publisher_access_challenge(case['url'],html)
    result=extract_for_publisher(html,case['url'])
    assert result and result['text_extent']=='available'
    assert result['published_at']==case['publishedAt']
    assert result['extraction_method']=='publisher_selector:'+case['selector']
    body=' '.join(result['full_text'].split())
    for paragraph in case['editorialBlocks']:
        assert paragraph in body
    assert 'Últimas notícias:' not in body
    if case['taskId']==235642:
        # The timeline starts on an earlier day; it is not publication time.
        assert result['published_at'].startswith('2026-09-11')
