"""Read captions belonging to the current Exame gallery, never recommendations."""
import json
import re
from urllib.parse import urlparse
from pipeline.http_utils import html_to_text
from .political_exame_archive import _EditorialCards


def extract(raw, url):
    parsed = urlparse(url)
    if parsed.hostname not in {'exame.com', 'www.exame.com'} or not parsed.path.startswith('/galeria/'):
        return None
    parser = _EditorialCards()
    parser.feed(raw)
    parser.close()
    canonical = parser.canonical
    if canonical.rstrip('/') != url.rstrip('/'):
        return None
    galleries = []
    for script in parser.scripts:
        prefix = 'self.__next_f.push('
        if not script.startswith(prefix):
            continue
        try:
            frame = json.loads(script[len(prefix):].rstrip().removesuffix(';').removesuffix(')'))
        except ValueError:
            continue
        if not isinstance(frame, list) or len(frame) < 2 or not isinstance(frame[1], str):
            continue
        for match in re.finditer(r'"galleryData"\s*:\s*', frame[1]):
            try:
                gallery, _ = json.JSONDecoder().raw_decode(frame[1][match.end():])
            except ValueError:
                continue
            if isinstance(gallery, dict) and gallery.get('slug') == parsed.path.rstrip('/').rsplit('/',1)[-1]:
                galleries.append(gallery)
    if len(galleries) != 1:
        return None
    gallery = galleries[0]
    acf = gallery.get('acf') or {}
    if not isinstance(acf, dict):
        return None
    parts = []
    for key in ['big_description','description']:
        text = html_to_text(str(acf.get(key) or '')).strip()
        if text and text not in parts:
            parts.append(text)
    images = acf.get('images') or []
    if not isinstance(images, list):
        return None
    for image in images:
        if not isinstance(image, dict):
            continue
        # Caption, description and image title are publisher text, not OCR.
        texts = []
        for key in ['caption','description']:
            text = html_to_text(str(image.get(key) or '')).strip()
            if text and text not in texts:
                texts.append(text)
        if not texts:
            texts = [html_to_text(str(image.get('title') or '')).strip()]
        parts.extend(t for t in texts if t)
    body = '\n\n'.join(parts)
    title = gallery.get('title') or {}
    if not isinstance(title, dict):
        return None
    return {'full_text': body, 'title': html_to_text(title.get('rendered','')),
        'canonical_url': canonical, 'published_at': '',
        'content_format': 'photo_gallery', 'text_extent': 'available' if body else 'absent',
        'extraction_state': 'full_text' if body else 'metadata_only',
        'extraction_method': 'publisher_galleryData_descriptions_and_captions',
        'extraction_version': 'exame-gallery-1', 'restriction_evidence': [],
        'publication_date_evidence': {'method':'missing_original_post_date','reason':'Gallery HTML does not expose original publication; sitemap date remains discovery evidence only.'},
        'format_provenance': {'publisher_id':gallery.get('id'),'images':len(images),
            'scope':'Current gallery descriptions and image captions/titles; related galleries and image binaries excluded.'}}
