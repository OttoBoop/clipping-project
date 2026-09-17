"""Read public UVA editorial data announced by the publisher's HTML and JS."""
from html.parser import HTMLParser
import re,json
from urllib.parse import urlparse,urljoin
from pipeline.http_utils import html_to_text

VERSION='estadao-public-uva-2'
class _Embeds(HTMLParser):
    def __init__(self):super().__init__();self.ids=[]
    def handle_starttag(self,tag,pairs):
        a=dict(pairs)
        if tag=='script' and a.get('src') in {
            'https://arte.estadao.com.br/arc/scripts/uva-render-02.js',
            'https://arte.estadao.com.br/arc/scripts/uva-render-03.js',
        }:
            value=a.get('data-uva-id','')
            if not re.fullmatch(r'[A-Za-z0-9_-]{12,100}',value):raise ValueError('estadao_uva_invalid_id')
            self.ids.append(value)

def announced_url(raw,url):
    p=urlparse(url)
    if p.scheme!='https' or p.hostname not in {'www.estadao.com.br','estadao.com.br'}:return None
    parser=_Embeds();parser.feed(raw)
    # The server can expose the embed only in its public hydration state.
    match=re.search(r'\bFusion\.globalContent\s*=\s*',raw)
    if match:
        try:data,_=json.JSONDecoder().raw_decode(raw[match.end():])
        except ValueError:data={}
        if data.get('type')=='story' and data.get('_id'):
            canonical=urljoin(url,data.get('canonical_url') or '')
            if canonical.rstrip('/')!=url.rstrip('/'):
                return None
            for row in data.get('content_elements') or []:
                if row.get('type')=='raw_html':parser.feed(row.get('content') or '')
    ids=list(dict.fromkeys(parser.ids))
    if not ids:return None
    if len(ids)>1:raise ValueError('estadao_uva_multiple_documents')
    ident=ids[0];path='/'.join(ident[i:i+2] for i in range(0,12,2)) if len(ident)==12 else ident
    return f'https://arte.estadao.com.br/public/pages/{path}/page.json'

def editorial(data):
    rows=data.get('conteúdo') if isinstance(data,dict) else None
    if isinstance(rows,dict):rows=list(rows.values())
    if not isinstance(rows,list) or len(rows)>2000:raise ValueError('estadao_uva_unrecognized_document')
    parts=[];unknown=set()
    def add(value):
        if isinstance(value,str):
            text=html_to_text(value)
            if text.strip():parts.append(text)
    for row in rows:
        kind=row.get('type');value=row.get('value')
        if kind in {'text','rodapé'}:add(value)
        elif kind=='frase' and isinstance(value,dict):
            for field in ['texto','nome','descrição']:add(value.get(field))
        elif kind=='html' and isinstance(value,dict):
            # Public editorial lists and explanatory boxes, not iframe contents.
            for item in value.get('conteúdo') or []:
                if item.get('type')=='text':
                    raw=item.get('value') or ''
                    if re.search(r'<\s*(?:iframe|object|embed)\b',raw,re.I):unknown.add('html_external_embed')
                    add(raw)
                else:unknown.add('html:'+str(item.get('type')))
        elif kind=='quiz' and isinstance(value,dict):
            for section in ['perguntas','respostas']:
                for item in value.get(section) or []:
                    if item.get('type') in {'pergunta','resposta'}:add(item.get('value'))
                    elif item.get('type')=='alternativas':
                        for option in item.get('value') or []:add(option)
        elif kind not in {'customização','imagem','leiaMais'}:unknown.add(str(kind))
    return {'full_text':'\n\n'.join(parts),'extraction_method':'publisher_public_uva_data',
        'extraction_version':VERSION,'text_extent':'unknown' if unknown else 'available',
        'content_format':'interactive_article','uva_provenance':{'unhandled_element_types':sorted(unknown),'elements':len(rows)}}
