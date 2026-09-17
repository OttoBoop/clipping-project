import gzip,hashlib,json
from pathlib import Path
from pipeline.http_utils import html_to_text
from web_app.political_estadao_uva import announced_url,editorial
ROOT=Path(__file__).parent/'fixtures/political_estadao'
def test_real_public_infographic_and_text_blocks():
 m=json.loads((ROOT/'uva-manifest.json').read_text());raw=gzip.decompress((ROOT/'real-uva.html.gz').read_bytes());api=gzip.decompress((ROOT/'real-uva-data.json.gz').read_bytes());data=json.loads(api)
 assert hashlib.sha256(raw).hexdigest()==m['htmlHash']
 assert hashlib.sha256(api).hexdigest()==m['apiHash']
 assert announced_url(raw.decode(),m['url'])==m['apiURL']
 a=editorial(data);assert len(a['full_text'])>7000
 for row in data['conteúdo']:
  if row['type']=='text':assert html_to_text(row['value']).strip() in a['full_text']
 assert 'display: none' not in a['full_text']
 assert a['uva_provenance']['unhandled_element_types']==[]
 assert announced_url(raw.decode(),'https://example.com/article') is None
 assert announced_url(raw.decode(),m['url']+'-other-article') is None
