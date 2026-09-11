"""Request forms verified on publisher pages; stored canonical identities stay unchanged."""
from urllib.parse import urlsplit, urlunsplit
import re


def publisher_article_identity_urls(url: str) -> tuple[str, ...]:
    """Known equivalent host forms, without rewriting historical identifiers."""
    parsed = urlsplit(url)
    if parsed.scheme == "https" and parsed.netloc in {"diariodorio.com", "www.diariodorio.com"}:
        other = "diariodorio.com" if parsed.netloc.startswith("www.") else "www.diariodorio.com"
        return url, urlunsplit(parsed._replace(netloc=other))
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


def publisher_article_request_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https":
        return url
    # Observed 2026-09-10: www Diário redirects to the bare host; Veja Rio
    # redirects extensionless article paths to a trailing slash. Avoid that
    # extra HTTP request and shared-domain wait without changing DB URL keys.
    if parsed.netloc == "www.diariodorio.com":
        return urlunsplit(parsed._replace(netloc="diariodorio.com"))
    if parsed.netloc == "vejario.abril.com.br" and parsed.path and not parsed.path.endswith("/"):
        segments = parsed.path.strip("/").split("/")
        if len(segments) >= 2 and "." not in segments[-1] and segments[0] != "wp-json":
            return urlunsplit(parsed._replace(path=parsed.path + "/"))
    return url
