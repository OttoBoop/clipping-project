import pytest
from pathlib import Path

from web_app.political_request_urls import (
    is_google_access_challenge, is_google_block_response, publisher_article_identity_urls, publisher_article_request_url,
)


GOOGLE_BLOCK = (Path(__file__).parent / "fixtures/google-automated-query-block-20260911.html").read_bytes()


@pytest.mark.parametrize("url,status,body,expected", [
    ("https://news.google.com/rss/articles/token", 503, GOOGLE_BLOCK, True),
    ("https://news.google.com/rss/search?q=name", 503, GOOGLE_BLOCK, True),
    ("https://publisher.example/story", 503, GOOGLE_BLOCK, False),
    ("https://news.google.com.evil.example/story", 503, GOOGLE_BLOCK, False),
    ("https://news.google.com/rss/search", 429, GOOGLE_BLOCK, False),
    ("https://news.google.com/rss/search", 503, b"Service temporarily unavailable", False),
    ("https://news.google.com/rss/search", 503, b"<title>Sorry...</title>maintenance", False),
    ("https://news.google.com/rss/search", 200, GOOGLE_BLOCK, False),
])
def test_observed_google_503_block_requires_host_status_and_specific_block_evidence(url,status,body,expected):
    assert is_google_block_response(url,status,body) is expected


def test_google_503_block_closes_response_without_default_outage_cooldown(monkeypatch):
    from types import SimpleNamespace
    import requests
    from web_app.political_corpus import FetchProblem, PoliticalCorpusService
    service=PoliticalCorpusService()
    response=requests.Response()
    response.status_code=503
    response._content=GOOGLE_BLOCK
    response._content_consumed=True
    service._http_local.session=SimpleNamespace(request=lambda *a,**k:response)
    monkeypatch.setattr(service,"_public_url",lambda url:None)
    monkeypatch.setattr(service,"reserve_domain",lambda domain:0)
    monkeypatch.setattr(service,"_check_domain_cooldown",lambda domain:None)
    monkeypatch.setattr(service,"_connect",lambda:pytest.fail("terminal block must not renew a default outage cooldown"))
    with pytest.raises(FetchProblem,match="google_access_challenge") as failure:
        service.fetch("https://news.google.com/rss/search?q=name")
    assert not failure.value.retryable


def test_diario_identity_variants_are_symmetric_and_do_not_rewrite_other_hosts():
    bare = "https://diariodorio.com/politica/story.html"
    www = "https://www.diariodorio.com/politica/story.html"
    assert publisher_article_identity_urls(bare) == (bare, www)
    assert publisher_article_identity_urls(www) == (www, bare)
    for url in ("https://www.other.example/story", "http://diariodorio.com/story",
                "https://user@diariodorio.com/story", "https://diariodorio.com:444/story"):
        assert publisher_article_identity_urls(url) == (url,)


def test_diario_real_publisher_canonical_index_reuses_both_verified_forms():
    # Canonical explicitly advertised in the preserved public HTML; live ID2037.
    path = "/parana-pesquisas-mostra-eduardo-paes-na-lideranca-para-o-governo-do-rio/"
    expected = {"https://" + host + path + suffix for host in
                ("diariodorio.com", "www.diariodorio.com") for suffix in ("", "index.html")}
    for url in expected:
        assert set(publisher_article_identity_urls(url)) == expected


@pytest.mark.parametrize("url,expected", [
    ("https://www.google.com/sorry/index?continue=redacted", True),
    ("https://google.com.br/sorry/", True),
    ("https://news.google.com/sorry", True),
    ("https://news.google.com/rss/articles/token", False),
    ("https://publisher.example/sorry/index", False),
    ("https://google.com.evil.example/sorry/index", False),
    ("https://google.com/sorry-not-a-challenge", False),
])
def test_google_challenge_detection_is_limited_to_google_challenge_paths(url, expected):
    assert is_google_access_challenge(url) is expected


def test_google_challenge_redirect_ends_before_requesting_challenge_or_reserving_its_domain(monkeypatch):
    from types import SimpleNamespace
    from web_app.political_corpus import FetchProblem, PoliticalCorpusService
    service = PoliticalCorpusService()
    calls, domains, closed = [], [], []
    response = SimpleNamespace(status_code=302, is_redirect=True, is_permanent_redirect=False,
        headers={"Location": "https://www.google.com/sorry/index?continue=redacted"}, close=lambda: closed.append(True))
    def request(method, url, **kwargs):
        calls.append(url)
        return response
    service._http_local.session = SimpleNamespace(request=request)
    monkeypatch.setattr(service, "_public_url", lambda url: None)
    monkeypatch.setattr(service, "reserve_domain", lambda domain: domains.append(domain) or 0)
    monkeypatch.setattr(service, "_check_domain_cooldown", lambda domain: None)
    with pytest.raises(FetchProblem, match="google_access_challenge") as failure:
        service.fetch("https://news.google.com/_/DotsSplashUi/data/batchexecute", method="POST")
    assert not failure.value.retryable
    assert calls == ["https://news.google.com/_/DotsSplashUi/data/batchexecute"]
    assert domains == ["news.google.com"] and closed == [True]


@pytest.mark.parametrize("url,expected", [
    ("https://www.diariodorio.com/politica/2026/06/story.html", "https://diariodorio.com/politica/2026/06/story.html"),
    ("https://vejario.abril.com.br/coluna/otavio-furtado/story", "https://vejario.abril.com.br/coluna/otavio-furtado/story/"),
    ("https://vejario.abril.com.br/cidade/story?q=value#anchor", "https://vejario.abril.com.br/cidade/story/?q=value#anchor"),
])
def test_verified_request_forms_preserve_path_query_and_fragment(url, expected):
    assert publisher_article_request_url(url) == expected
    assert publisher_article_request_url(expected) == expected


@pytest.mark.parametrize("url", [
    "https://g1.globo.com/rj/rio-de-janeiro/noticia/2026/06/01/story.ghtml",
    "https://news.google.com/rss/articles/token",
    "https://vejario.abril.com.br/cidade/story/",
    "https://vejario.abril.com.br/file.pdf",
    "https://vejario.abril.com.br/wp-json/wp/v2/posts",
    "https://vejario.abril.com.br/",
    "https://vejario.abril.com.br/cidade",
    "https://www.diariodorio.com.evil.example/story",
    "https://user@www.diariodorio.com/story",
    "https://www.diariodorio.com:444/story",
    "http://www.diariodorio.com/story",
])
def test_unverified_hosts_forms_and_non_article_urls_remain_unchanged(url):
    assert publisher_article_request_url(url) == url


def test_real_ponte_worker_comparison_uses_direct_request_and_preserves_identity():
    import json
    from pipeline.http_utils import canonicalize_url
    proof=json.loads((Path(__file__).parent/'fixtures/ponte-worker-redirects-20260914.json').read_text())
    assert proof['environment']=='production_worker' and proof['archiveWrites']==0
    for case in proof['cases']:
        old,new=case['variants']
        assert [c['status'] for c in old['calls']]==[301,200]
        assert [c['status'] for c in new['calls']]==[200]
        assert old['textHash']==new['textHash'] and old['textChars']>5000
        assert publisher_article_request_url(old['requestedUrl'])==new['requestedUrl']
        assert canonicalize_url(new['requestedUrl'])==old['requestedUrl']


@pytest.mark.parametrize('url',[
    'https://ponte.org/wp-json/wp/v2/posts','https://ponte.org/wp-sitemap.xml',
    'https://ponte.org/story-with-query?feed=rss','https://ponte.org/category/politica',
    'https://ponte.org.evil.example/story-title','https://user@ponte.org/story-title',
    'http://ponte.org/story-title','https://ponte.org/story-title/',
])
def test_ponte_request_change_is_limited_to_verified_shape(url):
    assert publisher_article_request_url(url)==url
