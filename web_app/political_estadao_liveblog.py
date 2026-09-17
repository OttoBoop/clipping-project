"""Public, identity-checked liveblog pagination; one ten-update page per lease."""
import json,re
from urllib.parse import urlparse,urljoin,urlencode
from pipeline.http_utils import html_to_text
from .political_editorial_extraction import _date

VERSION='estadao-liveblog-public-1'

def _identity(url):
    p=urlparse(url)
    return p.hostname=='www.estadao.com.br' and p.scheme=='https' and not p.query and not p.username

def initial(raw,url):
    if not _identity(url):return None
    m=re.search(r'\bFusion\.globalContent\s*=\s*',raw)
    if not m:return None
    try:data,_=json.JSONDecoder().raw_decode(raw[m.end():])
    except ValueError:return None
    if not isinstance(data,dict) or data.get('type')!='story' or data.get('subtype')!='parent-article' or 'live_content_elements' not in data:return None
    canonical=urljoin(url,data.get('canonical_url') or data.get('website_url') or '')
    if not _identity(canonical) or canonical.rstrip('/')!=url.rstrip('/') or not data.get('_id'):raise ValueError('estadao_liveblog_identity_mismatch')
    state={'article_id':data['_id'],'url':canonical,'title':(data.get('headlines') or {}).get('basic',''),
        'published_at':_date(data.get('first_publish_date') or ''),'restriction':(data.get('content_restrictions') or {}).get('content_code',''),
        'intro':data.get('content_elements') or [],'updates':[],'total':int(data.get('total',0)),'offset':0,'receipts':[]}
    return append(state,data)

def append(state,data):
    if data.get('_id')!=state['article_id'] or int(data.get('offset',-1))!=state['offset'] or int(data.get('total',-1))!=state['total']:
        raise ValueError('estadao_liveblog_page_identity_or_total_changed')
    rows=data.get('live_content_elements')
    if not isinstance(rows,list) or len(rows)>10:raise ValueError('estadao_liveblog_invalid_batch')
    ids=[str(r.get('id') or '') for r in rows];seen={str(r['id']) for r in state['updates']}
    if any(not x or x in seen for x in ids) or len(set(ids))!=len(ids):raise ValueError('estadao_liveblog_repeated_update')
    if not rows and state['offset']<state['total']:raise ValueError('estadao_liveblog_premature_end')
    if state['total']>5000:raise ValueError('estadao_liveblog_update_limit')
    state={**state,'updates':state['updates']+[{'id':r['id'],'time':r.get('time'),'date':r.get('date'),'hour':r.get('hour'),'content_elements':r.get('content_elements') or []} for r in rows], 'offset':state['offset']+len(rows)}
    if state['offset']>state['total']:raise ValueError('estadao_liveblog_total_exceeded')
    return state

def next_url(state):
    query={'requestUri':urlparse(state['url']).path,'params':json.dumps({'offset':state['offset'],'size':10},separators=(',',':'))}
    return 'https://www.estadao.com.br/pf/api/v3/content/fetch/context?'+urlencode({'query':json.dumps(query,separators=(',',':')),'_website':'estadao'})

def article(state):
    parts=[];unhandled=set()
    def blocks(items):
        for item in items:
            kind=item.get('type')
            if kind in {'text','header'}:
                text=html_to_text(item.get('content') or '')
                if text:parts.append(text)
            elif kind=='list':
                for entry in item.get('items') or []:
                    if isinstance(entry,str):parts.append(html_to_text(entry))
                    elif isinstance(entry,dict):blocks([entry])
            elif kind=='quote':blocks(item.get('content_elements') or [])
            elif kind not in {'image','video','oembed_response','reference','divider','custom_embed'}:unhandled.add(str(kind))
    blocks(state['intro'])
    for update in state['updates']:
        parts.append(' '.join(str(x) for x in [update.get('date'),update.get('hour')] if x));blocks(update['content_elements'])
    complete=state['offset']==state['total'];free=state['restriction']=='free'
    return {'title':state['title'],'canonical_url':state['url'],'published_at':state['published_at'],'full_text':'\n\n'.join(parts),
        'extraction_state':'full_text','extraction_method':'publisher_public_liveblog_pages','extraction_version':VERSION,
        'text_extent':'partial' if not complete else 'available' if free and not unhandled else 'unknown',
        'restriction_evidence':[] if free else ['public_liveblog:content_code='+state['restriction']],
        'content_format':'liveblog','publication_date_evidence':{'method':'public_first_publish_date','precision':'timestamp'},
        'liveblog_provenance':{'updates_retained':state['offset'],'reported_total':state['total'],'unhandled_element_types':sorted(unhandled),'receipts':state['receipts']}}
