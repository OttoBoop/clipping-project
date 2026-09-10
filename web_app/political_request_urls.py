"""Request forms verified on publisher pages; stored canonical identities stay unchanged."""
from urllib.parse import urlsplit, urlunsplit


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
