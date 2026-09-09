"""Transport budgets and reconstructible sitemap caches, without network access."""
import threading
from pathlib import Path

import pytest

from web_app import political_corpus
from web_app.political_corpus import FetchProblem, PoliticalCorpusService


class StreamResponse:
    status_code = 200
    is_redirect = is_permanent_redirect = False
    url = "https://www.tupi.fm/sitemap-posttype-post.2026.xml"
    headers = {}
    closed = False

    def __init__(self, chunks):
        self.chunks = chunks

    def iter_content(self, chunk_size):
        assert chunk_size == 65536
        yield from self.chunks()

    def close(self):
        self.closed = True


def service_with_response(tmp_path, monkeypatch, response):
    monkeypatch.setenv("POLITICAL_SITEMAP_CACHE_DIR", str(tmp_path))
    service = PoliticalCorpusService.__new__(PoliticalCorpusService)
    requests = []
    domains = []
    class Session:
        def request(self, method, url, **kwargs):
            requests.append((method, url, kwargs))
            return response
    service._http_local = threading.local()
    service._http_local.session = Session()
    monkeypatch.setattr(service, "_public_url", lambda _: None)
    monkeypatch.setattr(service, "reserve_domain", lambda domain: domains.append(domain) or 0)
    return service, requests, domains


def test_large_xml_spools_past_article_limit_without_materializing_response_and_reuses_snapshot(tmp_path, monkeypatch):
    size = 9 * 1024 * 1024
    response = StreamResponse(lambda: (b"x" * 65536 for _ in range(size // 65536)))
    service, requests, domains = service_with_response(tmp_path, monkeypatch, response)
    result = service.fetch(response.url, stream_sitemap=True)
    assert Path(result.sitemap_path).stat().st_size == size
    assert result._content == b"" and response.closed
    assert len(domains) == 1
    assert requests[0][2]["timeout"] == (8, 60)
    cached = service.fetch(response.url, stream_sitemap=True, sitemap_snapshot=result.sitemap_snapshot)
    assert cached.sitemap_path == result.sitemap_path and len(requests) == 1


def test_article_budget_is_unchanged_and_incomplete_sitemap_downloads_are_removed(tmp_path, monkeypatch):
    response = StreamResponse(lambda: (b"x" * 65536 for _ in range(150)))
    service, _, _ = service_with_response(tmp_path, monkeypatch, response)
    with pytest.raises(FetchProblem, match="response_budget_exceeded"):
        service.fetch(response.url)
    monkeypatch.setattr(political_corpus, "MAX_SITEMAP_RESPONSE_BYTES", 65536)
    with pytest.raises(FetchProblem, match="sitemap_download_budget_exceeded") as error:
        service.fetch(response.url, stream_sitemap=True)
    assert error.value.retryable is False
    assert list(tmp_path.iterdir()) == []


def test_rate_limited_error_response_does_not_become_a_cached_sitemap(tmp_path, monkeypatch):
    response = StreamResponse(lambda: iter([b"too many requests"]))
    response.status_code = 429
    response.headers = {"Retry-After": "60"}
    service, _, _ = service_with_response(tmp_path, monkeypatch, response)
    result = service.fetch(response.url, stream_sitemap=True)
    assert result.status_code == 429 and result.headers["Retry-After"] == "60"
    assert not hasattr(result, "sitemap_path")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("declaration", ['<meta charset="utf-8">', ''])
def test_html_without_http_charset_preserves_publisher_utf8(tmp_path, monkeypatch, declaration):
    import requests
    response = requests.Response()
    response.status_code = 200
    response.url = "https://publisher.example/article"
    response.headers["Content-Type"] = "text/html"
    response.encoding = "ISO-8859-1"
    response._content = (declaration + '<article>Eleição no Rio: Flávio Valle.</article>').encode('utf-8')
    response._content_consumed = True
    service, _, _ = service_with_response(tmp_path, monkeypatch, response)
    result = service.fetch(response.url)
    assert 'Eleição' in result.text and 'Flávio Valle' in result.text
