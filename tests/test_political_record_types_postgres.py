"""Non-news directory exclusions before fetch, redirects and metadata fallback."""
import pytest

from test_political_corpus_postgres import DATABASE_URL, service, start, enqueue, fake_response
from web_app import political_discovery
from web_app.political_record_types import non_news_reason
from pipeline.normalization import canonicalize_url

pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="Requires disposable PostgreSQL")
PROFILE = "https://ndmais.com.br/eleicoes/2026/candidatos/rj/deputado-estadual/atila-nunes-55055/"
GOOGLE = "https://news.google.com/rss/articles/example"


@pytest.mark.parametrize("route", ["direct", "redirect_200", "redirect_403", "google_resolver", "resolved_redirect"])
def test_directory_never_saved_as_article_or_metadata(service, monkeypatch, route):
    start(service, monkeypatch)
    origin = PROFILE if route == "direct" else GOOGLE
    enqueue(service, monkeypatch, {"url": origin, "title": "Eduardo Paes e Pedro Duarte",
        "source_key": "google_news", "source_name": "Google News", "metadata": {},
        "published_at": "2026-06-01T12:00:00-03:00"})
    calls = []
    editorial = "https://ndmais.com.br/justica/reportagem/"
    def fetch(url, **kwargs):
        calls.append(url)
        if route in {"redirect_200", "redirect_403"} or url == editorial:
            return fake_response(PROFILE, status=403 if route == "redirect_403" else 200)
        return fake_response(url)
    monkeypatch.setattr(service, "fetch", fetch)
    monkeypatch.setattr(political_discovery, "resolve_google_redirect", lambda *a, **kw: editorial if route == "resolved_redirect" else PROFILE)
    result = service.process_task(service.claim_task("fetch", worker_id="non-news-test"))
    assert result["status"] == "not_news"
    assert result["reason"] == "publisher_directory_not_news"
    assert len(calls) == (0 if route == "direct" else 2 if route == "resolved_redirect" else 1)
    assert not service.store.objects
    with service._connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM political_articles").fetchone()["n"] == 0
        assert conn.execute("SELECT COUNT(*) AS n FROM political_mentions").fetchone()["n"] == 0
        observed = conn.execute("SELECT * FROM political_observations").fetchone()
        assert observed["disposition"] == "not_news" and observed["article_id"] is None
        assert observed["metadata"]["non_news"]["resolvedUrl"] == canonicalize_url(PROFILE)
        task = conn.execute("SELECT * FROM political_tasks WHERE kind='fetch'").fetchone()
        assert task["status"] == "complete" and task["result"]["disposition"] == "not_news"


def test_editorial_nd_article_preserved(service, monkeypatch):
    start(service, monkeypatch)
    url = "https://ndmais.com.br/justica/reportagem-hugo-leal/"
    enqueue(service, monkeypatch, {"url": url, "title": "Encontro político", "source_key": "google_news",
        "published_at": "2026-06-01T12:00:00-03:00", "metadata": {}})
    monkeypatch.setattr(service, "fetch", lambda url, **kwargs: fake_response(url))
    assert service.process_task(service.claim_task("fetch", worker_id="editorial-test"))["status"] == "saved"
    assert non_news_reason(url) == ""
    assert non_news_reason("https://example.com/eleicoes/2026/candidatos/name/") == ""
