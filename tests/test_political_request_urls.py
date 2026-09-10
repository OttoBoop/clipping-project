import pytest

from web_app.political_request_urls import publisher_article_request_url


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
