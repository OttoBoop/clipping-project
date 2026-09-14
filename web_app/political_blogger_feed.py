"""Publisher-advertised Atom bodies and bounded historical pagination."""
from __future__ import annotations
import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from pipeline.http_utils import canonicalize_url, html_to_text

PUBLIC_ATOM_BODY_SOURCES = {'noticias_de_belford_roxo': 'noticiasdebelfordroxo.com'}
VERIFIED_BLOG_IDS = {'noticias_de_belford_roxo': '3445980854316391287'}
ATOM = '{http://www.w3.org/2005/Atom}'
MAX_BYTES = 4 * 1024 * 1024
MAX_ENTRIES = 100
MAX_PAGES = 2000


def _host(url):
    return (urlparse(url).hostname or '').lower().removeprefix('www.')


def _feed_url(url, source):
    p=urlparse(url)
    return (p.scheme=='https' and _host(url)==PUBLIC_ATOM_BODY_SOURCES.get(source['key'])
            and p.path=='/feeds/posts/default' and not p.username and not p.password)


def publisher_next_url(value, current_url, source, blog_id):
    """Use only the next parameters advertised for this exact publisher blog.

    Blogger emits its platform hostname even when serving a publisher's custom
    domain. The same start-index/max-results URLs were verified on that domain.
    No additional host is granted access to the publisher's body associations.
    """
    p=urlparse(value);q=parse_qs(p.query,keep_blank_values=True)
    own=_feed_url(value,source)
    platform=(p.scheme=='https' and _host(value)=='blogger.com'
              and p.path==f'/feeds/{blog_id}/posts/default' and not p.username and not p.password)
    if not (own or platform) or set(q)-{'start-index','max-results'}:
        return ''
    if any(len(v)!=1 or not re.fullmatch(r'[1-9]\d{0,7}',v[0]) for v in q.values()):return ''
    first=int(q.get('start-index',['0'])[0]);size=int(q.get('max-results',['25'])[0])
    previous=int(parse_qs(urlparse(current_url).query).get('start-index',['1'])[0])
    if first<=previous or not 1<=size<=MAX_ENTRIES:return ''
    return urlunparse(urlparse(current_url)._replace(query=urlencode({'start-index':first,'max-results':size}),fragment=''))


def parse_atom_page(raw, feed_url, source):
    from .political_discovery import parse_publication_date
    if not _feed_url(feed_url,source):raise ValueError('unverified_atom_feed_source')
    if not isinstance(raw,bytes) or len(raw)>MAX_BYTES:raise ValueError('atom_feed_response_limit')
    root=ET.fromstring(raw);blog_id=VERIFIED_BLOG_IDS[source['key']]
    if root.tag!=ATOM+'feed' or root.findtext(ATOM+'id')!=f'tag:blogger.com,1999:blog-{blog_id}':
        raise ValueError('atom_feed_publisher_identity_mismatch')
    entries=root.findall(ATOM+'entry')
    if len(entries)>MAX_ENTRIES:raise ValueError('atom_feed_entry_limit')
    digest=hashlib.sha256(raw).hexdigest();candidates=[];records=[];dates=[];ids=[];malformed=0;seen_posts=set()
    for entry in entries:
        identity=entry.findtext(ATOM+'id','');ids.append(identity)
        published=parse_publication_date(entry.findtext(ATOM+'published',''));dates.append(published)
        matched=re.fullmatch(r'tag:blogger.com,1999:blog-'+blog_id+r'\.post-([1-9]\d{0,19})',identity)
        link=next((n.get('href','') for n in entry.findall(ATOM+'link') if n.get('rel')=='alternate' and n.get('type')=='text/html'),'')
        url=canonicalize_url(link)
        if not matched or urlparse(url).scheme!='https' or _host(url)!=PUBLIC_ATOM_BODY_SOURCES[source['key']]:
            malformed+=1;continue
        post_id=int(matched[1])
        if post_id in seen_posts:
            malformed+=1;continue
        seen_posts.add(post_id);content=entry.find(ATOM+'content')
        fragment=content.text or '' if content is not None and content.get('type')=='html' else ''
        candidates.append({'url':url,'title':html_to_text(entry.findtext(ATOM+'title','')),
            'source_key':source['key'],'source_name':source['name'],'source_type':'political_discovery',
            'published_at':published,'snippet':html_to_text(entry.findtext(ATOM+'summary','')),
            'metadata':{'publisher_post_id':post_id,'blog_id':blog_id,'feed_url':feed_url,'feed_sha256':digest,
                        'feed_content_available':bool(fragment.strip()),'needs_date_review':not bool(published)}})
        if fragment.strip() and published:
            records.append({'post_id':post_id,'url':url,'published_at':published,'content_html':fragment,
                'protected':False,'body_origin':'publisher_atom','feed_url':feed_url,'feed_sha256':digest,
                'text_extent':'unknown','blog_id':blog_id})
    next_links=[n.get('href','') for n in root.findall(ATOM+'link') if n.get('rel')=='next']
    following=publisher_next_url(next_links[0],feed_url,source,blog_id) if len(next_links)==1 else ''
    return {'candidates':candidates,'body_batch':{'source_key':source['key'],'records':records},
            'dates':dates,'raw_count':len(entries),'malformed':malformed,'ids':ids,
            'fingerprint':hashlib.sha256('\n'.join(ids).encode()).hexdigest(),
            'next_url':following,'invalid_next':bool(next_links) and not following}


def discover_blogger_feed(task,source,fetch):
    from . import political_discovery as core
    from .political_expanded_discovery import _result
    if (task.get('mechanism') or {}).get('blog_id') != VERIFIED_BLOG_IDS.get(source['key']):
        raise core.DiscoveryError('atom_frozen_blog_identity_mismatch',retryable=False)
    cursor=task.get('cursor') or {};url=cursor.get('url') or task['url'];page=int(cursor.get('page',1))
    if not _feed_url(url,source):raise core.DiscoveryError('atom_feed_outside_publisher',retryable=False)
    response=core._get(fetch,url)
    try:parsed=parse_atom_page(response.content,url,source)
    except (ValueError,ET.ParseError) as exc:raise core.DiscoveryError(str(exc),retryable=False) from exc
    seen=cursor.get('page_fingerprints',[])
    if parsed['raw_count'] and parsed['fingerprint'] in seen:
        return _result(outcome='gap',gap_reason='atom_repeated_page',raw_count=parsed['raw_count'])
    dates=[datetime.fromisoformat(d) for d in parsed['dates'] if d]
    ordered=len(dates)==parsed['raw_count'] and all(a>=b for a,b in zip(dates,dates[1:]))
    previous=cursor.get('oldest_publication')
    if previous and dates and max(dates)>datetime.fromisoformat(previous):ordered=False
    changed=bool(set(parsed['ids']) & set(cursor.get('previous_ids',[])))
    chronology_gap=bool(cursor.get('chronology_gap')) or (bool(parsed['raw_count']) and not ordered) or changed
    unknown=int(cursor.get('unknown_dates',0))+sum(not d for d in parsed['dates'])
    malformed=int(cursor.get('malformed',0))+parsed['malformed']
    older=bool(dates) and ordered and max(dates).astimezone(core.SAO_PAULO).date()<datetime.fromisoformat(task['date_from']).date()
    older_pages=int(cursor.get('older_pages',0))+1 if older else 0
    candidates=[c for c in parsed['candidates'] if core.in_window(c['published_at'],task['date_from'],task['date_to'])]
    selected={c['url'] for c in candidates};records=[r for r in parsed['body_batch']['records'] if r['url'] in selected]
    reason='atom_invalid_next_link' if parsed['invalid_next'] else 'atom_page_cap' if page>=MAX_PAGES and parsed['next_url'] else ''
    stop=not parsed['next_url'] or not parsed['raw_count'] or (older_pages>=2 and not chronology_gap) or bool(reason)
    if older_pages>=10 and chronology_gap:stop=True;reason='atom_chronology_not_proven'
    if stop and not reason and (unknown or malformed or chronology_gap):reason='atom_dates_entries_or_order_incomplete'
    next_cursor=None if stop else {'url':parsed['next_url'],'page':page+1,'page_fingerprints':(seen+[parsed['fingerprint']])[-32:],
        'oldest_publication':min(dates).isoformat() if dates else previous,'older_pages':older_pages,
        'chronology_gap':chronology_gap,'unknown_dates':unknown,'malformed':malformed,'previous_ids':parsed['ids']}
    result=_result(candidates,raw_count=parsed['raw_count'],next_cursor=next_cursor,outcome='gap' if reason else None,gap_reason=reason)
    if records:result['body_batch']={'source_key':source['key'],'records':records}
    return result
