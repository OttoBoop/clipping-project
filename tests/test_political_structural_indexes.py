"""Real Exame topic taxonomy, distinct from article, column and video indexes."""
import gzip
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from web_app import political_expanded_discovery as expanded

FIXTURES = Path(__file__).parent / 'fixtures/political_exame_topics'


def test_real_topic_index_contains_collection_urls_and_is_not_fetched_as_articles():
    evidence = json.loads((FIXTURES / 'provenance.json').read_text())
    row = next(r for r in evidence['rows'] if r.get('locCount'))
    raw = gzip.decompress((FIXTURES / row['evidence']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == row['sha256']
    locs = [n.text for n in ET.fromstring(raw).iter() if n.tag.endswith('}loc')]
    assert len(locs) == 1000 and all('/noticias-sobre/' in u for u in locs)
    page = next(r for r in evidence['rows'] if r.get('evidence') and not r.get('locCount'))
    html = gzip.decompress((FIXTURES / page['evidence']).read_bytes())
    assert hashlib.sha256(html).hexdigest() == page['sha256']
    assert b'CollectionPage' in html and b'ItemList' in html
    source = next(s for s in expanded.load_expanded_sources() if s['key'] == 'exame')
    task = {**expanded.build_expanded_tasks(source, '2026-08-09', '2026-08-09', [])[0],
            'url': row['url'], 'depth': 1, 'cursor': {'offset': 500}}
    def forbidden(*args, **kwargs):
        pytest.fail('a known taxonomy index does not need another publisher request')
    result = expanded.discover_expanded(task, source, forbidden)
    assert result['outcome'] == 'complete' and not result['candidates']
    assert result['structural_index_excluded']['basis'] == 'publisher_topic_collection_sitemap'
    assert not result['structural_index_excluded']['articles_modified']
    assert expanded._skip_branch(row['url'])


@pytest.mark.parametrize('url', [
    'https://exame.com/colunistas/adriano-lima/ultimas-noticias/',
    'https://exame.com/videos/revista-exame/',
    'https://exame.com/noticias/2026/08/09/sitemap.xml',
    'https://exame.com/webstories/sitemap.xml',
    'https://another.example/noticias-sobre/4/sitemap.xml',
    'https://exame.com/noticias-sobre-noticias/4/sitemap.xml',
])
def test_editorial_routes_and_other_publishers_are_not_excluded(url):
    assert not expanded._exame_topic_index(url)
    assert not expanded.structural_exclusion({'url': url, 'strategy': 'expanded_sitemap', 'depth': 1}, {'key': 'exame'})
