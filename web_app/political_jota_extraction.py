"""Jota special reports embedded in publicly delivered Next.js page data."""
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser
import json
from urllib.parse import urljoin, urlparse


def original_date_trusted(url, metadata):
    parsed = urlparse(url)
    if parsed.hostname not in {'www.jota.info', 'jota.info', 'portal.jota.info'} or not parsed.path.startswith('/especiais/'):
        return True
    evidence = (metadata or {}).get('publication_date_evidence') or {}
    return isinstance(evidence, dict) and evidence.get('method') in {'post.dates.publish_dateGTM', 'post.dates.publish_date', 'post.date'}


class _NextData(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script':
            self.active = attrs.get('id') == '__NEXT_DATA__' and attrs.get('type') == 'application/json'

    def handle_endtag(self, tag):
        if tag == 'script':
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)


def extract_jota_special(raw_html, url):
    from .political_editorial_extraction import _EditorialParser, _date, _normalize
    parsed = urlparse(url)
    if parsed.hostname not in {'www.jota.info', 'jota.info', 'portal.jota.info'}:
        return None
    parser = _NextData()
    parser.feed(raw_html or '')
    try:
        payload = json.loads(''.join(parser.parts))
        post = payload['props']['pageProps']['post']
    except (ValueError, TypeError, KeyError):
        return None
    if (payload.get('page') != '/content/info/especial/[slug]' or not isinstance(post, dict)
            or type(post.get('ID')) is not int or post['ID'] <= 0):
        return None
    identity = urlparse(urljoin(url, str(post.get('full_url') or '')))
    if (not post.get('full_url') or identity.hostname != parsed.hostname
            or identity.path.rstrip('/') != parsed.path.rstrip('/')):
        return None
    sections = post.get('sections')
    if not isinstance(sections, list):
        sections = []

    class EditorialBody(_EditorialParser):
        def _body_start(self, attrs):
            return attrs.get('id') == 'jota-public-post-sections'

    fragments = [post['content']] if isinstance(post.get('content'), str) and post['content'].strip() else []
    for section in sections:
        if not isinstance(section, dict) or not isinstance(section.get('content'), str):
            continue
        if not section['content'].strip():
            continue
        heading = escape(str(section.get('title') or ''))
        lead = section.get('lead') if isinstance(section.get('lead'), str) else ''
        fragments.extend(['<h2>' + heading + '</h2>', '<div>' + lead + '</div>', section['content']])
    body_parser = EditorialBody('jota.info')
    body_parser.feed('<div id="jota-public-post-sections">' + '\n'.join(fragments) + '</div>')
    body_parser.close()
    body = _normalize(''.join(body_parser.parts))
    dates = post.get('dates') if isinstance(post.get('dates'), dict) else {}
    published, date_field = '', ''
    # This is the publisher's actual spelling. The ordinary JSON-LD on these
    # real pages contains a 2026 timestamp despite the original 2015 post date.
    try:
        raw = str(dates.get('publish_dateGTM') or '')
        stamp = datetime.fromisoformat(raw.replace('Z', '+00:00'))
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        published = stamp.astimezone(timezone.utc).isoformat()
        date_field = 'post.dates.publish_dateGTM'
    except ValueError:
        for field, value in [('post.dates.publish_date', dates.get('publish_date')), ('post.date', post.get('date'))]:
            published = _date(value)
            if published:
                date_field = field
                break
    restricted = post.get('inherits_from_PRO') is True
    return {
        'title': str(post.get('title') or '').strip(), 'full_text': body,
        'canonical_url': url, 'published_at': published,
        'extraction_state': 'full_text' if len(body.split()) >= 40 else 'metadata_only',
        'extraction_method': 'publisher_next_data:post.sections',
        'extraction_version': 'jota-public-special-2026-09-14.1',
        'text_extent': 'absent' if not body else 'unknown' if restricted else 'available',
        'restriction_evidence': ['publisher_post:inherits_from_PRO=true'] if restricted else [],
        'publication_date_evidence': {'method': date_field or 'missing_original_post_date',
                                      'publisher_post_id': post['ID'], 'published_at': published},
    }
