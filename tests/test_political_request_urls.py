import pytest

from web_app.political_request_urls import is_google_access_challenge, publisher_article_request_url


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
