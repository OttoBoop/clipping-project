"""Publisher-bounded extraction of editorial HTML, without network operations.

``available`` describes the body present in this response; it never certifies
that a subscription article or another edition was obtained in full.  Selectors
are backed by preserved production responses (see the real-source fixtures).
"""
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
import json
import re
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

EXTRACTION_VERSION = "editorial-2026-09-14.3"
_SAO_PAULO = ZoneInfo("America/Sao_Paulo")
_SELECTORS = {
    "exame.com": "#news-body",
    "congressoemfoco.com.br": ".asset__content .html-content",
    "nfnoticias.com.br": ".wrap__article-detail-content",
    "elizeupires.com": ".conteudo-post",
    "ultimahoraonline.com.br": ".post-detalhe-texto",
    "estadao.com.br": ".news-body[data-paywall-wrapper]",
    "generonumero.media": ".post-wrapper > .content",
}
_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
_BLOCK = {"address", "article", "blockquote", "div", "figcaption", "figure", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ol", "p", "section", "table", "tr", "ul"}
_SKIP_TAGS = {"script", "style", "noscript", "template", "nav", "aside", "button", "form", "iframe", "svg"}
_SKIP_CLASSES = {
    "inner-leiamais", "link-list-wrapper", "container-resumo-de-noticia",
    "container-blogs-e-colunas-vale-ler-tambem", "container-em-alta",
    "ads-placeholder-label", "adsbygoogle", "ai-viewports", "total-views",
    "related-posts", "related-articles", "related-stories", "social-share",
    "share-buttons", "newsletter", "publicidade", "paywall-offer",
}
_MONTHS = {month: index for index, month in enumerate(
    ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"), 1)}
_ARTICLE_KINDS = {"Article", "NewsArticle", "ReportageNewsArticle", "BlogPosting"}


def _date(raw: str) -> str:
    """Parse publisher publication fields; never substitute collection time."""
    value = str(raw or "").strip()
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        numeric = re.search(r"\b(\d{2})/(\d{2})/(\d{4})(?:\s*(?:\||às|-)?\s*(\d{1,2})[:h](\d{2}))?", value)
        named = re.search(r"\b(\d{1,2}) de ([a-zç]+) de (\d{4})(?:\s*(?:\||às|-)?\s*(\d{1,2})[:h](\d{2}))?", value, re.I)
        match = numeric or named
        if match:
            day, month, year, hour, minute = match.groups()
            month = int(month) if numeric else _MONTHS.get(month.lower(), 0)
            try:
                parsed = datetime(int(year), month, int(day), int(hour or 0), int(minute or 0))
            except ValueError:
                return ""
        else:
            try:
                parsed = parsedate_to_datetime(value)
            except (TypeError, ValueError, OverflowError):
                return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_SAO_PAULO)
    return parsed.astimezone(timezone.utc).isoformat()


def _normalize(value: str) -> str:
    # Keep paragraph separation, but do not insert spaces inside inline words.
    lines = [re.sub(r"[^\S\n]+", " ", part).strip() for part in value.splitlines()]
    return "\n\n".join(part for part in lines if part)


def _url_identity(value: str) -> str:
    parsed = urlparse(value)
    return (parsed.hostname or "").removeprefix("www.") + parsed.path.rstrip("/")


class _EditorialParser(HTMLParser):
    def __init__(self, host: str):
        super().__init__(convert_charrefs=True)
        self.host = host
        self.stack: list[tuple[str, dict, bool, bool]] = []
        self.parts: list[str] = []
        self.found_body = False
        self.metadata: dict[str, str] = {}
        self.canonical = ""
        self.captures: list[tuple[str, int, list[str]]] = []
        self.fields: dict[str, list[str]] = {}
        self.json_ld: list[str] = []
        self.restrictions: list[str] = []

    def _body_start(self, attrs: dict) -> bool:
        classes = set(attrs.get("class", "").split())
        if self.host == "exame.com":
            return attrs.get("id") == "news-body"
        if self.host == "congressoemfoco.com.br":
            return "html-content" in classes and any("asset__content" in item[1].get("class", "").split() for item in self.stack)
        if self.host == "generonumero.media":
            return ("content" in classes and bool(self.stack)
                    and "post-wrapper" in self.stack[-1][1].get("class", "").split()
                    and any(item[0] == "main" and "page-single" in item[1].get("class", "").split() for item in self.stack))
        if self.host == "estadao.com.br":
            # The candidate directory wraps its footer in [data-paywall-wrapper]
            # too; only the publisher's editorial news-body is a body selector.
            return "news-body" in classes and "data-paywall-wrapper" in attrs
        return _SELECTORS[self.host][1:] in classes

    def handle_starttag(self, tag: str, pairs):
        attrs = {key: value or "" for key, value in pairs}
        classes = set(attrs.get("class", "").split())
        parent_body = self.stack[-1][2] if self.stack else False
        parent_blocked = self.stack[-1][3] if self.stack else False
        new_body = not self.found_body and not parent_blocked and self._body_start(attrs)
        if new_body:
            self.found_body = True
        body = parent_body or new_body
        skip = tag in _SKIP_TAGS or bool(classes & _SKIP_CLASSES)
        if self.host == "generonumero.media" and parent_body and self.stack:
            # These siblings are the article hero, author/taxonomy, contents
            # list and standalone related/newsletter links. Inline citations
            # inside .text remain part of the editorial paragraphs.
            direct_child = "content" in self.stack[-1][1].get("class", "").split()
            skip = skip or (direct_child and bool(classes & {"hero", "author", "box", "list", "link", "dot"}))
        skip = skip or "hidden" in attrs or attrs.get("aria-hidden", "").lower() == "true"
        skip = skip or bool(re.search(r"display\s*:\s*none", attrs.get("style", ""), re.I))
        blocked = parent_blocked or skip
        if body and ("paywall-offer" in classes or "data-paywall-truncated" in attrs):
            self.restrictions.append("editorial_body:explicit_subscription_gate")
        if tag == "meta":
            key = (attrs.get("property") or attrs.get("name") or "").lower()
            if key and attrs.get("content"):
                self.metadata.setdefault(key, attrs["content"])
        if tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonical = self.canonical or attrs.get("href", "")
        field = ""
        if tag == "script" and attrs.get("type", "").lower() == "application/ld+json":
            field = "json_ld"
        elif (self.host == "generonumero.media" and tag in {"h1", "time"}
              and any(item[0] == "main" and "page-single" in item[1].get("class", "").split() for item in self.stack)
              and (tag == "h1" or "date" in classes)):
            # The hero is omitted from body text, but its editorial title/day
            # still supply metadata. No collection-time date is synthesized.
            field = "h1" if tag == "h1" else "publication_visible"
            if tag == "time" and attrs.get("datetime"):
                self.fields.setdefault("publication_visible", []).append(attrs["datetime"])
        elif tag in {"title", "h1", "time"} and not parent_blocked:
            field = tag
            if tag == "time" and attrs.get("datetime"):
                self.fields.setdefault("time", []).append(attrs["datetime"])
        elif self.host == "ultimahoraonline.com.br" and "post-detalhe-data" in classes:
            field = "publication_visible"
        elif self.host == "nfnoticias.com.br" and tag == "span" and {"text-dark", "ml-1"} <= classes:
            field = "publication_visible"
        if tag not in _VOID:
            self.stack.append((tag, attrs, body, blocked))
            if field:
                self.captures.append((field, len(self.stack), []))
        if body and not blocked and (tag in _BLOCK or tag in {"br", "hr"}):
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] != tag:
                continue
            _, _, body, blocked = self.stack[index]
            if body and not blocked and tag in _BLOCK:
                self.parts.append("\n")
            for field, depth, parts in self.captures:
                if depth > index:
                    value = "".join(parts)
                    if field == "json_ld":
                        self.json_ld.append(value)
                    else:
                        self.fields.setdefault(field, []).append(value.strip())
            self.captures = [entry for entry in self.captures if entry[1] <= index]
            del self.stack[index:]
            break

    def handle_data(self, data):
        for _, _, parts in self.captures:
            parts.append(data)
        if self.stack and self.stack[-1][2] and not self.stack[-1][3]:
            self.parts.append(data)


def extract_for_publisher(raw_html: str, url: str) -> dict | None:
    """Return a bounded publisher result, or None so generic extraction can run.

    A recognized but empty editorial root returns metadata-only, rather than
    falling back to a larger unrelated story or subscription/navigation text.
    """
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    if host in {"noticias.r7.com", "record.r7.com"}:
        from .political_r7_extraction import extract_video_companion
        return extract_video_companion(raw_html, url)
    if host not in _SELECTORS:
        return None
    parser = _EditorialParser(host)
    parser.feed(raw_html or "")
    parser.close()
    if not parser.found_body:
        return None
    canonical = urljoin(url, parser.canonical) if parser.canonical else ""
    title = parser.metadata.get("og:title", "")
    published = ""
    for key in ("article:published_time", "published_date", "datepublished", "published", "pubdate"):
        published = _date(parser.metadata.get(key, ""))
        if published:
            break
    restricted = False
    for raw in parser.json_ld:
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            continue
        queue = data if isinstance(data, list) else [data]
        while queue:
            item = queue.pop(0)
            if not isinstance(item, dict):
                continue
            graph = item.get("@graph")
            if isinstance(graph, list):
                queue.extend(graph)
            kinds = item.get("@type", [])
            kinds = [kinds] if isinstance(kinds, str) else kinds
            if not isinstance(kinds, list) or not (_ARTICLE_KINDS & set(str(kind) for kind in kinds)):
                continue
            identity = item.get("url") or item.get("mainEntityOfPage") or item.get("@id")
            if isinstance(identity, dict):
                identity = identity.get("@id") or identity.get("url")
            if isinstance(identity, str) and identity.startswith(("http://", "https://")):
                if _url_identity(identity) != _url_identity(canonical or url):
                    continue
            title = str(item.get("headline") or title)
            published = published or _date(item.get("datePublished", ""))
            if str(item.get("isAccessibleForFree", "")).lower() == "false":
                restricted = True
                parser.restrictions.append("article_jsonld:isAccessibleForFree=false")
            parts = item.get("hasPart", [])
            for part in parts if isinstance(parts, list) else [parts]:
                if isinstance(part, dict) and str(part.get("isAccessibleForFree", "")).lower() == "false":
                    restricted = True
                    parser.restrictions.append("article_jsonld:hasPart.isAccessibleForFree=false")
    if not published:
        for value in parser.fields.get("publication_visible", []) + parser.fields.get("time", []):
            published = _date(value)
            if published:
                break
    title = title or next(iter(parser.fields.get("h1", [])), "") or next(iter(parser.fields.get("title", [])), "")
    body = _normalize("".join(parser.parts))
    explicit_gate = "editorial_body:explicit_subscription_gate" in parser.restrictions
    extent = "absent" if not body else "partial" if explicit_gate else "unknown" if restricted else "available"
    return {
        "full_text": body, "title": title.strip(), "published_at": published,
        "canonical_url": canonical,
        "extraction_state": "full_text" if len(body.split()) >= 40 else "metadata_only",
        "extraction_method": "publisher_selector:" + _SELECTORS[host],
        "extraction_version": EXTRACTION_VERSION, "text_extent": extent,
        "restriction_evidence": list(dict.fromkeys(parser.restrictions)),
    }
