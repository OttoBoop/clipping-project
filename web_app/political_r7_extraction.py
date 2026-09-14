"""Published R7/Record video companion text; never generates a transcript."""
import json
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


class _FusionScripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.active = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.active = dict(attrs).get('id') == 'fusion-metadata'

    def handle_endtag(self, tag):
        if tag == 'script':
            self.active = False

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)


def extract_video_companion(raw_html, url):
    from .political_editorial_extraction import _EditorialParser, _date, _normalize, _url_identity, EXTRACTION_VERSION
    host = (urlparse(url).hostname or '').removeprefix('www.')
    if host not in {'noticias.r7.com', 'record.r7.com'}:
        return None
    scripts = _FusionScripts()
    scripts.feed(raw_html)
    script = ''.join(scripts.parts)
    marker = re.search(r'\bFusion\.globalContent\s*=\s*', script)
    if not marker:
        return None
    try:
        data, _ = json.JSONDecoder().raw_decode(script[marker.end():])
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict) or data.get('type') != 'video':
        return None
    # Fusion also embeds other programmes and related stories. Only accept the
    # primary object whose publisher URL matches the requested page.
    site = 'noticias' if host == 'noticias.r7.com' else 'recordtv'
    website = (data.get('websites') or {}).get(site) or {}
    identity = website.get('website_url') or data.get('canonical_url') or ''
    canonical = urljoin(url, identity)
    if not identity or _url_identity(canonical) != _url_identity(url):
        return None
    # description.basic is a search/social teaser. subheadlines.basic is the
    # separate editorial block rendered below the player in the real fixtures.
    editorial = (data.get('subheadlines') or {}).get('basic') or ''
    if not isinstance(editorial, str):
        return None
    parser = _EditorialParser('exame.com')
    parser.feed('<div id="news-body">' + editorial + '</div>')
    parser.close()
    body = _normalize(''.join(parser.parts))
    body = re.sub(r'\s*No RecordPlus, tem mais conteúdo da RECORD para você, ao vivo e de graça\. Baixe o app aqui!\s*$', '', body).strip()
    return {'full_text': body, 'title': str((data.get('headlines') or {}).get('basic') or ''),
            'published_at': _date(data.get('display_date') or data.get('first_publish_date') or ''),
            'canonical_url': canonical, 'extraction_state': 'full_text' if body else 'metadata_only',
            'extraction_method': 'publisher_structured:r7_video_companion',
            'extraction_version': EXTRACTION_VERSION, 'text_extent': 'unknown' if body else 'absent',
            'content_format': 'video_companion_text', 'restriction_evidence': []}
