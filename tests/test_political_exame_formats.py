"""Real failed responses: editorial cards and current-gallery captions only."""
import gzip,hashlib,json
from pathlib import Path
import pytest
from bs4 import BeautifulSoup
from web_app.political_discovery import extract_article
from web_app.political_exame_gallery import extract as gallery_extract
P=Path(__file__).parent/'fixtures/political_exame_formats'
ROWS=json.loads((P/'manifest.json').read_text())

@pytest.mark.parametrize('row',ROWS,ids=lambda r:str(r['taskId']))
def test_real_historical_body_and_format(row):
 raw=gzip.decompress((P/row['file']).read_bytes()).decode()
 assert hashlib.sha256(raw.encode()).hexdigest()==row['sha256']
 body=extract_article(raw,row['url']);assert len(body['full_text'])>250
 assert body['canonical_url'].rstrip('/')==row['url'].rstrip('/')
 assert 'Explorar nossas galerias' not in body['full_text']
 assert 'licenciamento de conteúdo' not in body['full_text']
 if '/webstories/' in row['url']:
  doc=BeautifulSoup(raw,'html.parser')
  paragraphs=[p.get_text() for p in doc.select('amp-story-grid-layer.card p')]
  assert paragraphs and all(' '.join(p.split()) in ' '.join(body['full_text'].split()) for p in paragraphs)
  assert body['content_format']=='web_story'
  assert body['format_provenance']['promotional_or_related_pages_removed']==1
  assert 'Leia completa' not in body['full_text'] and 'Ver mais' not in body['full_text']
  assert 'Letícia Ozório' not in body['full_text']
  assert body['published_at']=={25296:'2026-06-17T18:27:00+00:00',25297:'2026-06-17T13:50:00+00:00',25298:'2026-06-17T13:11:00+00:00'}[row['taskId']]
 else:
  assert body['content_format']=='photo_gallery'
  assert body['published_at']==''
  assert body['publication_date_evidence']['method']=='missing_original_post_date'
  assert 'Membros e Convidados do Clube CHRO' not in body['full_text'] or row['taskId'] in {25246,25250}
  assert gallery_extract(raw,'https://exame.com/galeria/other-gallery') is None


def test_real_gallery_named_captions_do_not_mix_related_products():
 row=next(r for r in ROWS if r['taskId']==25246)
 raw=gzip.decompress((P/row['file']).read_bytes()).decode();body=extract_article(raw,row['url'])['full_text']
 assert 'Cristiane Giansante' in body and 'Diretora de Pessoas' in body
 assert 'Pandora' not in body and 'Presentes Dia dos Pais' not in body


def test_real_btg_broken_links_resolve_to_independently_discovered_daily_urls():
 from web_app.political_exame_routes import find_alternative
 rows=json.loads(gzip.decompress((P/'btg-routes.json.gz').read_bytes()))
 assert len(rows['broken'])==171
 for task in rows['broken']:
  alternative=find_alternative(task['payload'],rows['alternatives'])
  assert alternative and alternative['url']!=task['payload']['url']
  assert alternative['basis']=='same_job_publisher_daily_inventory_exact_title_slug_and_publication'


def test_real_api_first_discovery_resolves_same_publisher_aliases():
 from web_app.political_exame_routes import find_alternative
 broken=json.loads(gzip.decompress((P/'btg-routes.json.gz').read_bytes()))['broken']
 alternatives=json.loads(gzip.decompress((P/'btg-api-routes.json.gz').read_bytes()))['alternatives']
 for task in broken:
  route=find_alternative(task['payload'],alternatives)
  assert route and route['basis']=='same_job_publisher_public_api_exact_title_slug_and_publication'
  assert route['publisher_api_url'].startswith('https://classic.exame.com/wp-json/')
 # Removing the verified API date evidence must not authorize a guessed route.
 unverified=[{**t,'payload':{**t['payload'],'metadata':{}}} for t in alternatives]
 assert find_alternative(broken[0]['payload'],unverified) is None


def test_real_guide_family_aliases_use_verified_api_bodies():
 from web_app.political_exame_routes import find_alternative
 rows=json.loads(gzip.decompress((P/'guide-routes.json.gz').read_bytes()))
 assert len(rows['broken'])==256
 for task in rows['broken']:
  assert find_alternative(task['payload'],rows['alternatives']) is not None
