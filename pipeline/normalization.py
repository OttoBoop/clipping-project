"""URL and text normalization utilities."""
import html as html_mod
import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "gclsrc", "dclid", "msclkid",
    "ref", "ref_src", "ref_url", "_ga", "mc_cid", "mc_eid",
}


def normalize_url(u):
    """Normalize a URL: lowercase host, strip tracking params, trailing slash."""
    if u is None:
        return ""
    u = str(u).strip()
    if not u:
        return ""
    # Fix missing double slash
    u = re.sub(r"^(https?:)/([^/])", r"\1//\2", u, flags=re.I)
    try:
        parsed = urlparse(u)
        host = (parsed.hostname or "").lower()
        path = parsed.path.rstrip("/") or "/"
        qs = parse_qs(parsed.query, keep_blank_values=False)
        filtered = {k: v for k, v in qs.items() if k.lower() not in _TRACKING_PARAMS}
        query = urlencode(filtered, doseq=True) if filtered else ""
        return urlunparse((parsed.scheme.lower(), host, path, "", query, ""))
    except Exception:
        return u.lower().strip()


def canonicalize_url(url):
    """Full URL canonicalization: normalize + sort query params + strip fragment."""
    if not url:
        return ""
    url = normalize_url(url)
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=False)
        sorted_qs = urlencode(sorted(qs.items()), doseq=True) if qs else ""
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", sorted_qs, ""))
    except Exception:
        return url


def clean_title(title):
    """Clean article title: unescape HTML, strip whitespace and quotes."""
    if not title:
        return ""
    title = html_mod.unescape(str(title))
    title = re.sub(r"<[^>]+>", "", title)  # strip HTML tags
    title = re.sub(r"\s+", " ", title).strip()
    title = title.strip("\"'")
    return title
