"""Editorial pages in the public state of Estadão's non-AMP web stories."""
import json,re
from urllib.parse import urlparse,urljoin
from pipeline.http_utils import html_to_text
from .political_editorial_extraction import _date

def extract(raw,url):
    p=urlparse(url)
    if p.scheme!='https' or p.hostname not in {'www.estadao.com.br','estadao.com.br'}:return None
    match=re.search(r'\bFusion\.globalContent\s*=\s*',raw)
    if not match:return None
    try:data,_=json.JSONDecoder().raw_decode(raw[match.end():])
    except ValueError:return None
    if not isinstance(data,dict) or data.get('type')!='story' or not str(data.get('subtype','')).endswith('_web-stories') or not data.get('_id'):return None
    canonical=urljoin(url,data.get('canonical_url') or '')
    if canonical.rstrip('/')!=url.rstrip('/'):return None
    pages=[[]]
    for item in data.get('content_elements') or []:
        if item.get('type')=='divider':
            if pages[-1]:pages.append([])
        else:pages[-1].append(item)
    parts=[];unknown=set();removed=0
    for page in pages:
        texts=[html_to_text(x.get('content') or '') for x in page if x.get('type') in {'text','header'}]
        title=next((html_to_text(x.get('content') or '').lower() for x in page if x.get('type')=='header'),'')
        callout=any(x.get('type')=='text' and re.search(r'<a\b',x.get('content') or '',re.I) and html_to_text(x.get('content') or '').strip().lower() in {'leia mais','saiba mais'} for x in page)
        if title.startswith(('assine o estadão','veja também:','veja mais:')) or (callout and not title):removed+=1;continue
        parts.extend(x for x in texts if x.strip())
        for x in page:
            if x.get('type') not in {'header','text','image','custom_embed'}:unknown.add(str(x.get('type')))
    body='\n\n'.join(parts);restriction=(data.get('content_restrictions') or {}).get('content_code','');stamp=_date(data.get('first_publish_date') or '')
    return {'title':(data.get('headlines') or {}).get('basic',''),'canonical_url':canonical,'published_at':stamp,
        'full_text':body,'extraction_state':'full_text' if body else 'metadata_only','extraction_method':'publisher_public_webstory_state',
        'extraction_version':'estadao-webstory-state-1','content_format':'web_story','text_extent':'available' if body and restriction=='free' and not unknown else 'unknown' if body else 'absent',
        'restriction_evidence':[] if restriction=='free' else ['public_story:content_code='+restriction],
        'format_provenance':{'publisher_id':data['_id'],'subtype':data['subtype'],'pages':len(pages),'promotional_or_related_pages_removed':removed,'unhandled_element_types':sorted(unknown)},
        'publication_date_evidence':{'method':'public_first_publish_date' if stamp else 'missing_original_post_date','precision':'timestamp'}}
