"""NF Notícias' public dated archive and author calendars; no name/title filter."""
from datetime import date
from html.parser import HTMLParser
from urllib.parse import urljoin,urlparse,parse_qs
import hashlib,re

VERSION='nf-public-archives-3'
BASE='https://www.nfnoticias.com.br/'
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
MONTHS={'janeiro':1,'fevereiro':2,'março':3,'abril':4,'maio':5,'junho':6,'julho':7,'agosto':8,'setembro':9,'outubro':10,'novembro':11,'dezembro':12}

class Node:
    def __init__(self,tag='',attrs=(),parent=None):
        self.tag=tag;self.attrs=dict(attrs);self.parent=parent;self.children=[]
    def text(self):
        return ' '.join(' '.join(c.text() if isinstance(c,Node) else c for c in self.children).split())
    def has(self,cls):return cls in self.attrs.get('class','').split()
    def find(self,tag=None,cls=None):
        out=[]
        for n in self.children:
            if not isinstance(n,Node):continue
            if (not tag or n.tag==tag) and (not cls or n.has(cls)):out.append(n)
            out.extend(n.find(tag,cls))
        return out

class Document(HTMLParser):
    def __init__(self,html):
        super().__init__(convert_charrefs=True);self.root=Node();self.current=self.root;self.feed(html);self.close()
    def handle_starttag(self,tag,attrs):
        n=Node(tag,attrs,self.current);self.current.children.append(n)
        if tag not in VOID:self.current=n
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID:self.handle_endtag(tag)
    def handle_endtag(self,tag):
        n=self.current
        while n.parent and n.tag!=tag:n=n.parent
        if n.parent:self.current=n.parent
    def handle_data(self,data):
        if self.current.tag not in {'script','style'}:self.current.children.append(data)


def article_url(value,kind=None):
    url=urljoin(BASE,value);p=urlparse(url)
    if p.hostname not in {'www.nfnoticias.com.br','nfnoticias.com.br'} or p.scheme!='https':return ''
    pattern=r'/evento-\d+/[^/]+' if kind=='events' else r'/noticia-\d+/[^/]+' if kind=='news' else r'/post/\d+/[^/]+/.+' if kind=='column' else r'/(?:noticia-\d+/[^/]+|post/\d+/[^/]+/.+)'
    return url if re.fullmatch(pattern,p.path) else ''


def parse_page(html,url,kind):
    root=Document(html).root;rows=[];next_url='';page=1
    if kind in {'news','events'}:
        for card in root.find(cls='card__post__content'):
            headings=card.find(cls='card__post__title');dates=card.find(cls='card__post__author-info')
            if not headings:continue
            anchors=headings[0].find('a');a=next((a for a in anchors if article_url(a.attrs.get('href',''),kind)),None)
            if not a:continue
            stamp=re.search(r'\b(\d{2})/(\d{2})/(\d{4})\b',dates[0].text() if dates else '')
            try:day=date(int(stamp[3]),int(stamp[2]),int(stamp[1])).isoformat() if stamp else ''
            except ValueError:day=''
            if kind=='events':
                category=card.find(cls='card__post__category')
                label=category[0].text().lower() if category else ''
                stamp=re.fullmatch(r'(\d{1,2}) de ([\wç]+) de (\d{4})',label)
                try:day=date(int(stamp[3]),MONTHS[stamp[2]],int(stamp[1])).isoformat() if stamp else ''
                except (ValueError,KeyError):day=''
            rows.append({'url':article_url(a.attrs['href'],kind),'title':a.text(),'date':day})
        pagination=root.find(cls='pagination-area')
        if pagination:
            active=pagination[0].find(cls='active')
            if active and active[0].text().isdigit():page=int(active[0].text())
            for a in pagination[0].find('a'):
                candidate=urljoin(BASE,a.attrs.get('href',''));parsed=urlparse(candidate)
                q=parse_qs(parsed.query)
                if (parsed.hostname=='www.nfnoticias.com.br' and parsed.path=='/noticias.php'
                    and set(q)=={'_pagi_pg'} and q['_pagi_pg']==[str(page+1)]):next_url=candidate;break
        return rows,{'page':page,'next_url':next_url,'pagination_found':bool(pagination)}
    if kind=='columns_index':
        authors={}
        for a in root.find('a',cls='dropdown-item'):
            u=article_url(a.attrs.get('href',''),'column')
            if u:authors.setdefault(urlparse(u).path.split('/')[3],u)
        return [],{'authors':authors}
    # The author's current article is separate from the archive modal tables.
    from .political_editorial_extraction import extract_for_publisher
    current=extract_for_publisher(html,url)
    if current:rows.append({'url':url,'title':current['title'],'date':current.get('published_at',''),'current':True})
    valid_months=0;invalid=0
    author=urlparse(url).path.split('/')[3]
    for block in root.find(cls='modal-body'):
        h=block.find('h5');stamp=re.search(r'([\wç]+)\s+de\s+(\d{4})',h[0].text().lower() if h else '')
        if not stamp or stamp[1] not in MONTHS:continue
        valid_months+=1
        for tr in block.find('tr'):
            cells=tr.find('td');links=tr.find('a')
            if len(cells)<2 or not links:continue
            u=article_url(links[0].attrs.get('href',''),'column')
            invalid_identity=not u or urlparse(u).path.split('/')[3]!=author
            try:day=date(int(stamp[2]),MONTHS[stamp[1]],int(cells[0].text())).isoformat()
            except ValueError:day=''
            rows.append({'url':u,'title':links[0].text(),'date':day,'invalid_identity':invalid_identity})
    return rows,{'calendar_months':valid_months,'invalid_rows':invalid,'current_article_found':bool(current)}


def discover(task,source,fetch):
    from . import political_expanded_discovery as expanded
    core=expanded._core();mechanism=task['mechanism'];kind=mechanism.get('product')
    if source['key']!='nf_noticias' or kind not in {'news','events','columns_index','column'}:
        raise core.DiscoveryError('nf_archive_invalid_route',retryable=False)
    cursor=task.get('cursor') or {};url=cursor.get('url') or task.get('url') or mechanism.get('url')
    parsed=urlparse(url)
    valid=(parsed.hostname=='www.nfnoticias.com.br' and parsed.scheme=='https' and
           ((kind=='news' and parsed.path in {'/noticias','/noticias.php'} and set(parse_qs(parsed.query))<={'_pagi_pg'})
            or (kind=='events' and parsed.path=='/eventos' and not parsed.query)
            or (kind=='columns_index' and parsed.path=='/' and not parsed.query)
            or (kind=='column' and article_url(url,'column'))))
    if not valid:raise core.DiscoveryError('nf_archive_invalid_url',retryable=False)
    response=core._get(fetch,url)
    if urlparse(getattr(response,'url',url)).path!=parsed.path:
        raise core.DiscoveryError('nf_archive_redirected',retryable=False)
    rows,info=parse_page(response.content.decode('utf8','replace'),url,kind)
    proof={'adapter':VERSION,'url':url,'kind':kind,'responseHash':hashlib.sha256(response.content).hexdigest(),**info}
    if kind=='columns_index':
        children=[{**task,'strategy':'expanded_nf_archive','url':u,'cursor':{},'mechanism':{**mechanism,'product':'column','url':u}} for u in info['authors'].values()]
        return expanded._result(child_tasks=children,raw_count=len(children),outcome='complete' if children else 'gap',gap_reason='' if children else 'nf_author_index_missing',publisher_archive=proof,archive_response=response.content)
    start,end=date.fromisoformat(task['date_from']),date.fromisoformat(task['date_to']);dates=[];candidates=[];unknown=0;invalid_identity=0;invalid_outside_window=0
    for row in rows:
        published=core.parse_publication_date(row['date']);day=None
        if published:
            from datetime import datetime
            day=datetime.fromisoformat(published).astimezone(core.SAO_PAULO).date();dates.append(day)
        else:unknown+=1
        if day and not start<=day<=end:
            invalid_outside_window+=int(bool(row.get('invalid_identity')))
            continue
        if row.get('invalid_identity'):
            invalid_identity+=1
            continue
        candidates.append(expanded._candidate(source,row['url'],row['title'],published,metadata={'discovery_format':VERSION,'archive_url':url,'archive_reported_date':row['date'],'archive_response_hash':proof['responseHash'],'record_product':'opinion' if kind=='column' else 'event_article' if kind=='events' else 'news'}))
    proof.update(raw_rows=len(rows),candidate_count=len(candidates),unknown_dates=unknown,invalid_identity_in_window=invalid_identity,invalid_identity_outside_window=invalid_outside_window,oldest=min(dates).isoformat() if dates else None,newest=max(dates).isoformat() if dates else None)
    if kind=='events':
        return expanded._result(candidates,raw_count=len(rows),outcome='gap',gap_reason='nf_events_history_not_proven',publisher_archive=proof,archive_response=response.content)
    if kind=='column':
        gap='nf_column_calendar_unrecognized' if not info['calendar_months'] else 'nf_column_invalid_dates' if unknown else 'nf_column_invalid_identity' if invalid_identity else ''
        return expanded._result(candidates,raw_count=len(rows),outcome='gap' if gap else 'complete',gap_reason=gap,publisher_archive=proof,archive_response=response.content)
    fingerprint=hashlib.sha256('\n'.join(r['url'] for r in rows).encode()).hexdigest();seen=cursor.get('fingerprints',[])
    expected=int(cursor.get('page',1))
    if info['page']!=expected:return expanded._result(outcome='gap',raw_count=len(rows),gap_reason='nf_archive_wrong_page',publisher_archive=proof,archive_response=response.content)
    if rows and fingerprint in seen:return expanded._result(outcome='gap',raw_count=len(rows),gap_reason='nf_archive_repeated_page',publisher_archive=proof,archive_response=response.content)
    unordered=bool(cursor.get('unordered')) or any(a<b for a,b in zip(dates,dates[1:])) or bool(dates and cursor.get('previous_oldest') and max(dates).isoformat()>cursor['previous_oldest'])
    older=bool(rows) and len(dates)==len(rows) and max(dates)<start
    older_pages=int(cursor.get('older_pages',0))+1 if older else 0
    proof.update(older_pages=older_pages,unordered=unordered,page=expected)
    gap=''
    if not rows:gap='nf_archive_empty_unproven'
    elif older_pages>=2 and not unordered:
        gap='nf_archive_unknown_dates' if unknown or cursor.get('unknown_dates') else ''
    elif not info['next_url']:gap='nf_archive_missing_next_page' if not info['pagination_found'] else ''
    elif expected>=int(mechanism.get('max_pages',2000)):gap='nf_archive_page_cap'
    elif older_pages>=10 and unordered:gap='nf_archive_chronology_unproven'
    else:
        return expanded._result(candidates,raw_count=len(rows),next_cursor={'url':info['next_url'],'page':expected+1,'fingerprints':(seen+[fingerprint])[-32:],'previous_oldest':min(dates).isoformat() if dates else cursor.get('previous_oldest'),'older_pages':older_pages,'unordered':unordered,'unknown_dates':int(cursor.get('unknown_dates',0))+unknown},publisher_archive=proof,archive_response=response.content)
    return expanded._result(candidates,raw_count=len(rows),outcome='gap' if gap else 'complete',gap_reason=gap,publisher_archive=proof,archive_response=response.content)
