"""Public source-link resolution on an actual preserved publisher response."""
import gzip,hashlib,json
from pathlib import Path
from web_app.political_estadao import public_original
P=Path(__file__).parent/'fixtures/political_estadao'
def real():
 m=json.loads((P/'manifest.json').read_text());raw=gzip.decompress((P/'real-snack.html.gz').read_bytes());assert hashlib.sha256(raw).hexdigest()==m['sha256'];return raw.decode(),m['url']
def test_public_snack_advertises_exact_original_without_using_its_summary():
 raw,url=real();r=public_original(raw,url)
 assert r['url']=='https://www.estadao.com.br/politica/stf-mantem-anulacao-condenacao-anthony-garotinho-pre-candidato-governo-rio-nprp/'
 assert r['publisher_content_id']=='JEAACWDAXFC4XB6FZUJ5FLJ3ZY'
 assert 'resume' not in r and 'full_text' not in r
def test_snack_resolution_requires_exact_host_same_publisher_and_identity():
 raw,url=real();assert public_original(raw,url.replace('www.estadao.com.br','www.estadao.com.br.example.org')) is None
 original=public_original(raw,url)['url']
 assert public_original(raw.replace(original,original.replace('www.estadao.com.br','external.example')),url) is None
 assert public_original(raw.replace('"original_source":{"url"','"different_source":{"url"'),url) is None
 assert public_original(raw,original) is None
