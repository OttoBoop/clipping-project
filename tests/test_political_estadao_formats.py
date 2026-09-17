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
