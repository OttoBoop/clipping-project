"""Public Folha web-story text, including slides hidden by navigation state."""
from html.parser import HTMLParser
import re
from urllib.parse import urlparse

_VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}


class _Slides(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack=[]
        self.slides=[]
        self.capture=None

    def handle_starttag(self,tag,pairs):
        attrs=dict(pairs);classes=set(attrs.get('class','').split())
        slide=self.stack[-1][1] if self.stack else None
        if 'story-slide' in classes:
            slide=len(self.slides);self.slides.append([])
        layer='text-element' in classes or bool(self.stack and self.stack[-1][2])
        if tag not in _VOID:
            self.stack.append((tag,slide,layer))
        if tag=='p' and slide is not None and layer:
            self.capture=(len(self.stack),slide,[])
        elif tag=='br' and self.capture:
            self.capture[2].append('\n')

    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]!=tag:continue
            if self.capture and self.capture[0]>i:
                value=re.sub(r'\s+',' ',''.join(self.capture[2]).replace('\ufeff','')).strip()
                if value:self.slides[self.capture[1]].append(value)
                self.capture=None
            self.stack=self.stack[:i]
            break

    def handle_data(self,data):
        if self.capture and not any(t[0] in {'script','style','noscript'} for t in self.stack):
            self.capture[2].append(data)


def extract_folha_story(raw_html,url):
    from .political_editorial_extraction import EXTRACTION_VERSION
    parsed=urlparse(url)
    if parsed.hostname!='www1.folha.uol.com.br' or not parsed.path.startswith('/webstories/'):
        return None
    parser=_Slides();parser.feed(raw_html);parser.close()
    if not parser.slides:return None
    paragraphs=[]
    for slide in parser.slides:
        if not slide:continue
        first=slide[0]
        # These are separate closing cards in the publisher's preserved story,
        # not phrases removed from an editorial paragraph.
        if first in {'IMAGENS','PRODUÇÃO DE WEB STORIES'}:continue
        if first.startswith(('Sua assinatura ajuda a Folha a seguir fazendo um jornalismo',
                             'Veja as principais notícias do dia no Brasil e no mundo')):continue
        paragraphs.extend(slide)
    from .political_discovery import extract_article
    result=extract_article(raw_html)  # Metadata only; no URL means no adapter recursion.
    body='\n\n'.join(paragraphs)
    result.update(full_text=body,extraction_state='full_text' if body else 'metadata_only',
                  extraction_method='publisher_slides:folha_webstory',extraction_version=EXTRACTION_VERSION,
                  text_extent='available' if body else 'absent',content_format='web_story',restriction_evidence=[])
    return result
