"""Request forms verified on publisher pages; stored canonical identities stay unchanged."""
from urllib.parse import urlsplit, urlunsplit
import re


def publisher_article_identity_urls(url: str) -> tuple[str, ...]:
    """Known equivalent host forms, without rewriting historical identifiers."""
    parsed = urlsplit(url)
    if parsed.scheme == "https" and parsed.netloc in {"diariodorio.com", "www.diariodorio.com"}:
        other = "diariodorio.com" if parsed.netloc.startswith("www.") else "www.diariodorio.com"
        paths = [parsed.path]
        # Four independently retrieved publisher pages advertise /index.html
        # as their canonical while serving the same editorial slug without it.
        # Do not rewrite IDs or equate different titles/dated permalink shapes.
        base = parsed.path.removesuffix("index.html").rstrip("/")
        if re.fullmatch(r"/[^/.]+-[^/.]+", base):
            paths.extend([base + "/", base + "/index.html"])
        return tuple(dict.fromkeys([url] + [urlunsplit(parsed._replace(netloc=host, path=path))
            for host in (parsed.netloc, other) for path in paths]))
    return (url,)


def is_google_access_challenge(url: str) -> bool:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    google = any(host == domain or host.endswith("." + domain) for domain in ("google.com", "google.com.br"))
    return google and (parsed.path == "/sorry" or parsed.path.startswith("/sorry/"))


def is_google_block_response(url: str, status_code: int, body: bytes) -> bool:
    """Recognize Google's observed HTTP 503 automated-query block, not an outage."""
    host = (urlsplit(url).hostname or "").lower().rstrip(".")
    if host != "news.google.com" or status_code != 503:
        return False
    text = body[:65536].decode("utf-8", errors="replace").lower()
    return bool(re.search(r"<title>\s*sorry\.{3}\s*</title>", text)
                and "sending automated queries" in text
                and "support.google.com/websearch/answer/86640" in text)


def is_publisher_access_challenge(url: str, raw_html: str) -> bool:
    """TV Zoom's preserved HTTP 200 is a Sucuri challenge, not editorial HTML."""
    if (urlsplit(url).hostname or "").removeprefix("www.") != "tvzoom.com.br":
        return False
    text = raw_html[:65536].lower()
    return ("<title>you are being redirected...</title>" in text
            and "sucuri_cloudproxy_js" in text
            and "javascript is required" in text)


def publisher_article_request_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https":
        return url
    # Observed 2026-09-10: www Diário redirects to the bare host; Veja Rio
    # redirects extensionless article paths to a trailing slash. Avoid that
    # extra HTTP request and shared-domain wait without changing DB URL keys.
    if parsed.netloc == "www.diariodorio.com":
        return urlunsplit(parsed._replace(netloc="diariodorio.com"))
    # Three real Estadão stories compared on 2026-09-17: slashless -> 301
    # -> slash, with identical extracted text/date. Keep DB identities intact.
    if (parsed.netloc == "www.estadao.com.br" and not parsed.query
            and not parsed.path.startswith(("/arc/", "/pf/"))
            and re.fullmatch(r"/(?:[^/.]+/)+[^/.]+-[^/.]+", parsed.path)):
        return urlunsplit(parsed._replace(path=parsed.path + "/"))
    # Three real Ponte pages compared on the production worker, 2026-09-14:
    # slashless -> 301 -> slash, with equal extracted-text hashes. The stored
    # identity remains slashless; only the confirmed editorial request changes.
    if parsed.netloc == "ponte.org" and not parsed.query and re.fullmatch(r"/[^/.]+-[^/.]+", parsed.path):
        return urlunsplit(parsed._replace(path=parsed.path + "/"))
    if parsed.netloc == "vejario.abril.com.br" and parsed.path and not parsed.path.endswith("/"):
        segments = parsed.path.strip("/").split("/")
        if len(segments) >= 2 and "." not in segments[-1] and segments[0] != "wp-json":
            return urlunsplit(parsed._replace(path=parsed.path + "/"))
    return url
