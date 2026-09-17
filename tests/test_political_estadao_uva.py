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

def test_real_uva03_keeps_editorial_boxes_quotes_and_marks_external_graphics():
 m=json.loads((ROOT/'uva03-manifest.json').read_text())
 raw=gzip.decompress((ROOT/'real-uva03.html.gz').read_bytes())
 api=gzip.decompress((ROOT/'real-uva03-data.json.gz').read_bytes())
 assert hashlib.sha256(raw).hexdigest()==m['htmlHash']
 assert hashlib.sha256(api).hexdigest()==m['apiHash']
 assert announced_url(raw.decode(),m['url'])==m['apiURL']
 data=json.loads(api);a=editorial(data)
 for row in data['conteúdo']:
  if row['type']=='text':assert html_to_text(row['value']).strip() in a['full_text']
 assert 'R$ 616 milhões' in a['full_text']
 assert 'Como identificar vícios em jogos?' in a['full_text']
 assert 'Em minutos você pode mudar sua vida de cabeça para baixo' in a['full_text']
 assert 'Instituto de Estudos para Políticas de Saúde' in a['full_text']
 assert 'Maioria da população tem imagem negativa sobre celebridades' not in a['full_text']
 assert a['text_extent']=='unknown'
 assert a['uva_provenance']['unhandled_element_types']==['gráfico','html_external_embed']
