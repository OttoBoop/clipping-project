import gzip,json,hashlib
from pathlib import Path
import pytest
from web_app import political_estadao_liveblog as live
P=Path(__file__).parent/'fixtures/political_estadao'
def pages():
 m=json.loads((P/'liveblog-manifest.json').read_text());raw=gzip.decompress((P/'real-liveblog.html.gz').read_bytes());second=gzip.decompress((P/'real-liveblog-page2.json.gz').read_bytes());assert hashlib.sha256(raw).hexdigest()==m['htmlHash'];assert hashlib.sha256(second).hexdigest()==m['page2']['hash'];return m,raw.decode(),json.loads(second)
def test_real_liveblog_first_page_is_partial_and_uses_original_publication():
 m,raw,second=pages();state=live.initial(raw,m['url']);assert state['offset']==10 and state['total']==69
 a=live.article(state);assert a['text_extent']=='partial';assert a['published_at']=='2026-08-09T21:43:57.166000+00:00';assert 'privatizações' in a['full_text'];assert 'Tarcísio de Freitas' in a['full_text']
 assert live.next_url(state)==m['page2']['url']
 state=live.append(state,second);assert state['offset']==20 and len(state['updates'])==20
 with pytest.raises(ValueError):live.append(state,second)
def test_real_liveblog_requires_own_identity_and_historical_count():
 m,raw,second=pages();state=live.initial(raw,m['url'])
 assert live.initial(raw,m['url'].replace('estadao.com.br','estadao.com.br.example.org')) is None
 with pytest.raises(ValueError):live.initial(raw,m['url']+'-different')
 with pytest.raises(ValueError):live.append(state,{**second,'_id':'different'})
 with pytest.raises(ValueError):live.append(state,{**second,'total':70})
 with pytest.raises(ValueError):live.append(state,{**second,'live_content_elements':[]})


def test_real_updates_with_same_millisecond_id_are_not_the_same_update():
 data=json.loads(gzip.decompress((P/'real-liveblog-id-collision.json.gz').read_bytes()));state=data['state'];page=data['page'];ids=[r['id'] for r in page['live_content_elements']];assert len(ids)==10 and len(set(ids))==9
 final=live.append(state,page);assert final['offset']==20 and len(final['updates'])==20
 body=live.article(final)['full_text'];assert 'Vai começar!' in body and 'Tecnologia como novidade' in body
 with pytest.raises(ValueError):live.append(state,{**page,'live_content_elements':[page['live_content_elements'][0]]*10})
