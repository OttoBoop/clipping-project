"""HTTP utilities for the clipping pipeline."""
import json
import random
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
]


def _build_ssl_fallback_context():
    """Permissive SSL context for sites with bad/expired certs."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def fetch_url(url, *, timeout=8, headers=None):
    """Fetch a URL and return (body_text, final_url). Never raises."""
    if not url:
        return "", ""
    hdrs = {"User-Agent": random.choice(_USER_AGENTS), "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.5"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    for attempt in range(2):
        ctx = None if attempt == 0 else _build_ssl_fallback_context()
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                final_url = resp.url or url
                raw = resp.read()
                encoding = resp.headers.get_content_charset() or "utf-8"
                try:
                    body = raw.decode(encoding, errors="replace")
                except (LookupError, UnicodeDecodeError):
                    body = raw.decode("utf-8", errors="replace")
                return body, final_url
        except ssl.SSLError:
            if attempt == 0:
                continue
            return "", url
        except Exception as e:
            if attempt == 0 and "SSL" in str(e):
                continue
            return "", url
    return "", url


def post_json(url, payload, *, timeout=8):
    """POST JSON and return parsed response dict. Never raises."""
    try:
        data = json.dumps(payload).encode("utf-8")
        hdrs = {
            "User-Agent": random.choice(_USER_AGENTS),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return {}


def try_resolve_google_redirect(url):
    """Resolve Google News redirect URLs to the actual article URL."""
    if not url:
        return url
    # Google News RSS links look like: https://news.google.com/rss/articles/...
    # or contain ./articles/ redirects. The real URL is in a redirect or in the page.
    # Quick method: check for known redirect patterns
    parsed = urllib.parse.urlparse(url)
    if "google.com" not in (parsed.hostname or ""):
        return url
    # Try to extract from query params
    qs = urllib.parse.parse_qs(parsed.query)
    if "url" in qs:
        return qs["url"][0]
    # Try fetching and following redirect
    try:
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(_USER_AGENTS)})
        with urllib.request.urlopen(req, timeout=6) as resp:
            return resp.url or url
    except Exception:
        return url
