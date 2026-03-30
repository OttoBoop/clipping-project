from __future__ import annotations

import html
import json
import re
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import parse_qs, quote, urlparse, urlunparse

from .settings import USER_AGENT


def _build_ssl_fallback_context():
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl._create_unverified_context()


def _urlopen_with_ssl_fallback(req, *, timeout: int):
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except Exception as exc:
        msg = str(exc)
        is_ssl_fail = "CERTIFICATE_VERIFY_FAILED" in msg or "certificate verify failed" in msg.lower()
        target = req.full_url if isinstance(req, urllib.request.Request) else str(req)
        if not (is_ssl_fail and str(target).lower().startswith("https://")):
            raise
        # First fallback: certifi-backed CA bundle (helps when local cert store is missing/outdated).
        # Second fallback: unverified context, as a last resort for hosts with broken TLS chains.
        try:
            context = _build_ssl_fallback_context()
            return urllib.request.urlopen(req, timeout=timeout, context=context)
        except Exception as exc2:
            msg2 = str(exc2)
            is_ssl_fail2 = "CERTIFICATE_VERIFY_FAILED" in msg2 or "certificate verify failed" in msg2.lower()
            if not is_ssl_fail2:
                raise
            context = ssl._create_unverified_context()
            return urllib.request.urlopen(req, timeout=timeout, context=context)


def fetch_url(url: str, timeout: int = 10) -> tuple[str, str]:
    """Return (response_url, body_text)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    data = b""
    final_url = url
    with _urlopen_with_ssl_fallback(req, timeout=timeout) as response:
        final_url = response.geturl()
        data = response.read()
    try:
        body = data.decode("utf-8")
    except UnicodeDecodeError:
        body = data.decode("latin1", errors="ignore")
    return final_url, body


def post_json(url: str, payload, timeout: int = 10) -> tuple[str, str]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
        },
    )
    data = b""
    final_url = url
    with _urlopen_with_ssl_fallback(req, timeout=timeout) as response:
        final_url = response.geturl()
        data = response.read()
    try:
        body = data.decode("utf-8")
    except UnicodeDecodeError:
        body = data.decode("latin1", errors="ignore")
    return final_url, body


GOOGLE_ARTICLE_PATH_RE = re.compile(r"/(?:rss/)?(?:articles|read)/([^/?#]+)")
GOOGLE_DATA_SIG_RE = re.compile(r'data-n-a-sg=["\']([^"\']+)["\']')
GOOGLE_DATA_TS_RE = re.compile(r'data-n-a-ts=["\']([^"\']+)["\']')
GOOGLE_DECODE_CACHE: dict[str, str] = {}


def _extract_google_article_token(url: str) -> str:
    try:
        parsed = urlparse(url)
        if "news.google.com" not in (parsed.netloc or ""):
            return ""
        match = GOOGLE_ARTICLE_PATH_RE.search(parsed.path or "")
        if not match:
            return ""
        token = (match.group(1) or "").strip()
        return token
    except Exception:
        return ""


def _decode_google_article_token(token: str, timeout: int = 6) -> str:
    if not token:
        return ""
    if token in GOOGLE_DECODE_CACHE:
        return GOOGLE_DECODE_CACHE[token]

    try:
        _, article_html = fetch_url(f"https://news.google.com/rss/articles/{token}", timeout=timeout)
    except Exception:
        GOOGLE_DECODE_CACHE[token] = ""
        return ""

    sig_match = GOOGLE_DATA_SIG_RE.search(article_html)
    ts_match = GOOGLE_DATA_TS_RE.search(article_html)
    if not sig_match or not ts_match:
        GOOGLE_DECODE_CACHE[token] = ""
        return ""
    signature = sig_match.group(1)
    timestamp = ts_match.group(1)

    payload = [
        "Fbv4je",
        (
            '["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],'
            '"X","X",1,[1,1,1],1,1,null,0,0,null,0],"'
            f"{token}"
            '",'
            f"{timestamp}"
            ',"'
            f"{signature}"
            '"]'
        ),
    ]
    request_body = f"f.req={quote(json.dumps([[payload]]))}".encode("utf-8")
    request = urllib.request.Request(
        "https://news.google.com/_/DotsSplashUi/data/batchexecute",
        data=request_body,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        },
    )
    try:
        with _urlopen_with_ssl_fallback(request, timeout=timeout) as response:
            raw = response.read()
        response_text = raw.decode("utf-8", errors="ignore")
        parts = response_text.split("\n\n", 1)
        if len(parts) < 2:
            GOOGLE_DECODE_CACHE[token] = ""
            return ""
        rows = json.loads(parts[1])
        for row in rows:
            if not isinstance(row, list) or len(row) < 3:
                continue
            if row[0] != "wrb.fr":
                continue
            inner = json.loads(row[2])
            if isinstance(inner, list) and len(inner) >= 2 and inner[0] == "garturlres":
                decoded = str(inner[1] or "").strip()
                if decoded.startswith("http"):
                    GOOGLE_DECODE_CACHE[token] = decoded
                    return decoded
    except Exception:
        GOOGLE_DECODE_CACHE[token] = ""
        return ""

    GOOGLE_DECODE_CACHE[token] = ""
    return ""


def try_resolve_google_redirect(url: str, timeout: int = 6) -> str:
    parsed = urlparse(url)
    if "news.google.com" not in parsed.netloc:
        return url
    params = parse_qs(parsed.query)
    if "url" in params and params["url"]:
        return params["url"][0]

    token = _extract_google_article_token(url)
    if token:
        decoded = _decode_google_article_token(token, timeout=timeout)
        if decoded:
            return decoded

    # Best effort follow.
    try:
        final_url, _ = fetch_url(url, timeout=timeout)
        final_token = _extract_google_article_token(final_url)
        if final_token:
            decoded = _decode_google_article_token(final_token, timeout=timeout)
            if decoded:
                return decoded
        return final_url
    except Exception:
        return url


def canonicalize_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        path = parsed.path or "/"
        # Remove trailing slash noise except root.
        if len(path) > 1 and path.endswith("/"):
            path = path.rstrip("/")
        clean = parsed._replace(
            query="",
            fragment="",
            path=path,
        )
        return urlunparse(clean)
    except Exception:
        return url


SCRIPT_RE = re.compile(r"(?is)<script.*?>.*?</script>")
STYLE_RE = re.compile(r"(?is)<style.*?>.*?</style>")
TAG_RE = re.compile(r"(?is)<[^>]+>")
WS_RE = re.compile(r"\s+")
URL_RE = re.compile(r"https?://\S+")
ARTICLE_BLOCK_RE = re.compile(r"(?is)<article[^>]*>(.*?)</article>")
MAIN_BLOCK_RE = re.compile(r"(?is)<main[^>]*>(.*?)</main>")
ENTRY_BLOCK_RE = re.compile(
    r'(?is)<div[^>]+class=["\'][^"\']*(entry-content|post-content|article-content|materia-content|content-body)[^"\']*["\'][^>]*>(.*?)</div>'
)


def html_to_text(raw_html: str) -> str:
    text = SCRIPT_RE.sub(" ", raw_html or "")
    text = STYLE_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = URL_RE.sub(" ", text)
    text = WS_RE.sub(" ", text).strip()
    return text


def extract_best_article_html(raw_html: str) -> str:
    html_body = raw_html or ""
    candidates: list[str] = []
    candidates.extend([m.group(1) for m in ARTICLE_BLOCK_RE.finditer(html_body)])
    candidates.extend([m.group(1) for m in MAIN_BLOCK_RE.finditer(html_body)])
    candidates.extend([m.group(2) for m in ENTRY_BLOCK_RE.finditer(html_body)])
    if not candidates:
        return html_body
    return max(candidates, key=lambda chunk: len(chunk))


def html_to_article_text(raw_html: str) -> str:
    best = extract_best_article_html(raw_html)
    return html_to_text(best)


TITLE_RE = re.compile(r"(?is)<title>(.*?)</title>")
OG_TITLE_RE = re.compile(r'(?is)<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']')
TW_TITLE_RE = re.compile(r'(?is)<meta[^>]+name=["\']twitter:title["\'][^>]+content=["\'](.*?)["\']')


def extract_html_title(raw_html: str) -> str:
    for patt in (OG_TITLE_RE, TW_TITLE_RE, TITLE_RE):
        m = patt.search(raw_html or "")
        if m:
            title = html.unescape(m.group(1))
            title = WS_RE.sub(" ", TAG_RE.sub(" ", title)).strip()
            if title:
                return title
    return ""


DATE_PATTERNS = [
    re.compile(r'(?is)<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\'](.*?)["\']'),
    re.compile(r'(?is)<meta[^>]+name=["\']pubdate["\'][^>]+content=["\'](.*?)["\']'),
    re.compile(r'(?is)<time[^>]+datetime=["\'](.*?)["\']'),
]


def parse_iso_datetime(value: str) -> str:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return ""


def extract_published_at(raw_html: str) -> str:
    html_body = raw_html or ""
    for patt in DATE_PATTERNS:
        m = patt.search(html_body)
        if not m:
            continue
        candidate = m.group(1).strip()
        parsed = parse_iso_datetime(candidate)
        if parsed:
            return parsed
    return ""


BAD_PATH_TOKENS = {
    "/feed",
    "/rss",
    "/wp-content",
    "/tag/",
    "/author/",
    "/category/",
    "/comentarios",
    "/search/",
}

BAD_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".js", ".css", ".pdf", ".xml")


def is_likely_article_url(url: str, expected_host_fragment: str = "") -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        host = (parsed.netloc or "").lower()
        if expected_host_fragment and expected_host_fragment.lower() not in host:
            return False
        path = (parsed.path or "").lower()
        if not path or path == "/":
            return False
        if any(tok in path for tok in BAD_PATH_TOKENS):
            return False
        if path.endswith(BAD_EXTENSIONS):
            return False
        # Require slug-like path instead of homepage sections only.
        segments = [seg for seg in path.split("/") if seg]
        if len(segments) < 1:
            return False
        long_segments = [seg for seg in segments if len(seg) >= 12]
        if not long_segments:
            return False
        return True
    except Exception:
        return False
