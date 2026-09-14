"""Real publisher feeds: discovery is separate from response body availability."""
import gzip
import hashlib
import json
from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET

import pytest

from web_app.political_access_alternatives import parse_public_feed
from web_app.political_body_batches import WordPressBodyBatches, BatchBodyUnavailable

ROOT = Path(__file__).parent / 'fixtures' / 'political_public_feed_real'
RESPONSES = json.loads((ROOT / 'manifest.json').read_text())['responses']
SOURCE = {'key': 'diario_do_vale', 'name': 'Diário do Vale', 'domain': 'diariodovale.com.br'}


def parsed(kind):
    evidence = next(row for row in RESPONSES if row['kind'] == kind)
    raw = gzip.decompress((ROOT / evidence['body_file']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == evidence['sha256']
    return parse_public_feed(raw, evidence['url'], SOURCE), raw, evidence


class MemoryObjects:
    enabled = True
    prefix = 'test-public-feed'

    def __init__(self):
        self.objects = {}

    def upload_bytes(self, data, key, kind):
        self.objects[key] = data
        return True

    def read_political_object(self, key):
        return self.objects[key]


@pytest.mark.parametrize('kind', ['advertised_feed', 'feed_page_two', 'feed_history_page_80', 'feed_history_page_150'])
def test_real_rss_preserves_all_public_bodies_and_publication_provenance(kind):
    result, _, evidence = parsed(kind)
    assert result['raw_count'] == 20
    assert len(result['candidates']) == len(result['body_batch']['records']) == 20
    assert len(set(row['url'] for row in result['candidates'])) == 20
    for row in result['body_batch']['records']:
        assert row['body_origin'] == 'publisher_rss'
        assert row['feed_sha256'] == evidence['sha256']
        assert row['feed_url'] == evidence['url']
        assert row['text_extent'] == 'unknown'
        assert row['content_html'] and row['published_at'] and row['post_id'] > 0


def test_real_pagination_changes_articles_and_ignored_date_parameter_is_detectable():
    first, _, _ = parsed('advertised_feed')
    second, _, _ = parsed('feed_page_two')
    ignored, _, _ = parsed('feed_date_archive')
    assert first['fingerprint'] != second['fingerprint']
    assert first['fingerprint'] == ignored['fingerprint']
    assert set(row['url'] for row in first['candidates']).isdisjoint(row['url'] for row in second['candidates'])
    july, _, _ = parsed('feed_history_page_150')
    assert all(value.startswith(('2026-07-04', '2026-07-05')) for value in july['publication_dates'])


def test_real_paes_article_survives_immutable_batch_readback_after_restart():
    result, _, _ = parsed('feed_history_page_150')
    candidate = next(row for row in result['candidates'] if 'presidente-da-ferj' in row['url'])
    store = MemoryObjects()
    refs = WordPressBodyBatches(store).store_batch(result['body_batch'])
    ref = next(ref for ref in refs if ref['post_id'] == candidate['metadata']['wordpress_id'])
    body = WordPressBodyBatches(store).read_body(ref, candidate)
    assert 'Eduardo Paes' in body['full_text'] and 'Pedro Paulo' in body['full_text']
    assert body['body_origin'] == 'publisher_rss'
    assert body['provenance']['method'] == 'publisher_rss_batch'
    assert body['provenance']['feed_url'].endswith('?paged=150')
    assert body['text_extent'] == 'unknown'
    assert all('content_html' not in json.dumps(ref) for ref in refs)


def test_description_without_content_encoded_never_becomes_article_body():
    _, raw, evidence = parsed('advertised_feed')
    root = ET.fromstring(raw)
    for item in root.findall('./channel/item'):
        item.remove(item.find('{http://purl.org/rss/1.0/modules/content/}encoded'))
    result = parse_public_feed(ET.tostring(root), evidence['url'], SOURCE)
    assert len(result['candidates']) == 20
    assert result['body_batch']['records'] == []
    assert all(row['snippet'] and not row['metadata']['feed_content_available'] for row in result['candidates'])


def test_missing_date_preserves_discovery_but_requires_review_and_no_dated_body_batch():
    _, raw, evidence = parsed('advertised_feed')
    root = ET.fromstring(raw)
    for item in root.findall('./channel/item'):
        item.remove(item.find('pubDate'))
    result = parse_public_feed(ET.tostring(root), evidence['url'], SOURCE)
    assert len(result['candidates']) == 20
    assert result['body_batch']['records'] == []
    assert all(not row['published_at'] and row['metadata']['needs_date_review'] for row in result['candidates'])


def test_foreign_feed_cannot_be_attributed_to_publisher():
    _, raw, _ = parsed('advertised_feed')
    with pytest.raises(ValueError, match='unverified_public_feed_source'):
        parse_public_feed(raw, 'https://another.example/feed/', SOURCE)
    result, _, _ = parsed('advertised_feed')
    batch = deepcopy(result['body_batch'])
    batch['records'][0]['feed_url'] = 'https://another.example/feed/'
    with pytest.raises(BatchBodyUnavailable, match='batch_feed_provenance_invalid'):
        WordPressBodyBatches(MemoryObjects()).store_batch(batch)


@pytest.mark.parametrize('slug', [
    'defesa-civil-de-resende-participa-de-curso-sobre-artefatos-explosivos-na-aman',
    'china-cria-mecanismos-financeiros-na-africa-para-nao-depender-de-dolar',
])
def test_real_bracketed_quote_or_html_attribute_is_not_missing_shortcode_body(slug):
    for evidence in RESPONSES:
        result = parse_public_feed(gzip.decompress((ROOT / evidence['body_file']).read_bytes()), evidence['url'], SOURCE)
        candidate = next((row for row in result['candidates'] if slug in row['url']), None)
        if not candidate:
            continue
        store = MemoryObjects()
        refs = WordPressBodyBatches(store).store_batch(result['body_batch'])
        ref = next(ref for ref in refs if ref['post_id'] == candidate['metadata']['wordpress_id'])
        body = WordPressBodyBatches(store).read_body(ref, candidate)
        assert len(body['full_text']) > 200
        if slug.startswith('china-'):
            assert '[A parceria]' in body['full_text']
        return
    pytest.fail('Real published response missing from fixture manifest')
