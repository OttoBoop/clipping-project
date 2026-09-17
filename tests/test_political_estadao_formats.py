"""Actual failed publisher responses; no generated article text."""
import gzip,hashlib,json
from pathlib import Path
import pytest
from bs4 import BeautifulSoup
from web_app.political_editorial_extraction import extract_for_publisher
ROOT=Path(__file__).parent/'fixtures/political_estadao'
ROWS=json.loads((ROOT/'format-manifest.json').read_text())
@pytest.mark.parametrize('row',ROWS)
def test_real_estadao_formats_preserve_editorial_paragraphs(row):
 raw=gzip.decompress((ROOT/row['fixture']).read_bytes()).decode()
 assert hashlib.sha256(raw.encode()).hexdigest()==row['html_sha256']
 result=extract_for_publisher(raw,row['url'])
 assert result['published_at']==row['date']
 assert result['content_format']==row['format']
 soup=BeautifulSoup(raw,'html.parser');body=result['full_text']
 if row['format']=='sponsored_article':
  paragraphs=[p.get_text(' ',strip=True) for p in soup.select('.content-left-sponsored p') if len(p.get_text(strip=True))>100]
 else:
  paragraphs=[p.get_text(' ',strip=True) for page in soup.select('amp-story-page')[:6] for p in page.select('p') if not p.find_parent(class_='credits') and len(p.get_text(strip=True))>100]
  assert result['format_provenance']['promotional_or_related_pages_removed']==3
  assert 'Assine o Estadão' not in body and 'Veja também:' not in body and 'Veja mais:' not in body
 assert paragraphs
 normalize=lambda s:' '.join(s.split())
 assert all(normalize(p) in normalize(body) for p in paragraphs)
 assert 'Copyright' not in body and 'PUBLICIDADE' not in body


def test_real_non_amp_webstory_uses_its_own_public_state():
 from web_app.political_estadao_webstory import extract
 import re
 m=json.loads((ROOT/'state-webstory-manifest.json').read_text());raw=gzip.decompress((ROOT/'real-state-webstory.html.gz').read_bytes()).decode()
 assert hashlib.sha256(raw.encode()).hexdigest()==m['htmlHash']
 a=extract_for_publisher(raw,m['url']);assert a['published_at']==m['date'] and a['content_format']=='web_story'
 match=re.search(r'Fusion.globalContent\s*=\s*',raw);data=json.JSONDecoder().raw_decode(raw[match.end():])[0]
 paragraphs=[x['content'] for x in data['content_elements'] if x.get('type')=='text' and x.get('content') and len(x['content'])>100 and '<a' not in x['content']]
 assert len(paragraphs)==5 and all(x in a['full_text'] for x in paragraphs)
 assert 'Leia Mais' not in a['full_text'] and 'PF detectou pagamento' not in a['full_text']
 assert extract(raw,m['url']+'-another-page') is None
