import json
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlparse

import pytest

from web_app import political_discovery as discovery


@dataclass
class Response:
    text: str
    status_code: int = 200
    url: str = "https://example.com"
    headers: dict = field(default_factory=dict)

    @property
    def content(self):
        return self.text.encode("utf-8")


def rss(count=1, published="Mon, 01 Jun 2026 12:00:00 GMT"):
    return "<rss><channel>" + "".join(
        f"<item><title>Notícia {i}</title><link>https://news.google.com/rss/articles/id{i}</link>"
        f"<pubDate>{published}</pubDate><description>Resumo</description></item>" for i in range(count)
    ) + "</channel></rss>"


def task(source="google_news", strategy="google_news", **kwargs):
    return {"source_key": source, "strategy": strategy, "query": '"Eduardo Paes"',
            "date_from": "2026-06-01", "date_to": "2026-06-07", "cursor": {}, **kwargs}


def test_tasks_include_each_selected_name_and_nonoverlapping_seven_day_windows():
    snapshots = [{"key": str(i), "display_name": name} for i, name in enumerate(
        ["Eduardo Paes", "Flávio Valle", "Pedro Duarte", "Renan Ferreirinha", "Pedro Paulo"])]
    tasks = discovery.build_tasks(snapshots, "2026-06-01", "2026-06-15", ["google_news"])
    assert len(tasks) == 15
    for snapshot in snapshots:
        own = [row for row in tasks if row["target_ids"] == [snapshot["key"]]]
        assert [row["query"] for row in own] == ['"' + snapshot["display_name"] + '"'] * 3
        assert [(row["date_from"], row["date_to"]) for row in own] == [
            ("2026-06-01", "2026-06-07"), ("2026-06-08", "2026-06-14"), ("2026-06-15", "2026-06-15")]


def test_source_scoped_history_queries_and_registry_capabilities():
    tasks = discovery.build_tasks([{"key": "paes", "display_name": "Eduardo Paes"}],
                                  "2026-06-01", "2026-06-07", ["metropoles", "rc24h", "j3news", "tupi", "odia"])
    sources = {row["key"]: row for row in discovery.load_sources()}
    assert sources["rc24h"]["strategies"] == ["google_news"]
    assert sources["j3news"]["strategies"] == ["google_news"]
    assert "wordpress" not in sources["metropoles"]["strategies"]
    assert all("site:" in row["query"] for row in tasks if row["strategy"] == "google_news")
    assert any(row.get("url") == "https://www.metropoles.com/sitemap/google-news.xml" for row in tasks)
    assert "https://odia.ig.com.br/sitemap/sitemap.xml" in sources["odia"]["sitemap_urls"]


def test_odia_advertised_daily_index_only_schedules_requested_calendar_days():
    urls = [f"https://odia.ig.com.br/sitemap/{day}.xml" for day in [
        "2014/01/01", "2026/06/01", "2026/08/08", "2026/08/09", "2026/08/10", "2026/09/09"]]
    body = "<sitemapindex>" + "".join(f"<sitemap><loc>{url}</loc></sitemap>" for url in urls) + "</sitemapindex>"
    selected = task("odia", "sitemap", url="https://odia.ig.com.br/sitemap/sitemap.xml",
                    date_from="2026-08-09", date_to="2026-08-09")
    result = discovery.discover(selected, lambda _: Response(body))
    assert result["raw_count"] == 6
    assert result["outcome"] == "complete"
    assert [row["url"] for row in result["child_tasks"]] == [urls[3]]
    assert "published_at" not in result["child_tasks"][0]
    assert result["child_tasks"][0]["partition_status"] == "requested_calendar_partition"
    full = discovery.discover({**selected, "date_from": "2026-06-01", "date_to": "2026-09-09"}, lambda _: Response(body))
    assert [row["url"] for row in full["child_tasks"]] == urls[1:]


def test_odia_unknown_calendar_children_survive_with_gap_across_cursor(monkeypatch):
    monkeypatch.setattr(discovery, "MAX_INDEX_CHILDREN", 1)
    xml = '<sitemapindex><sitemap><loc>https://odia.ig.com.br/new-archive.xml</loc></sitemap><sitemap><loc>https://odia.ig.com.br/sitemap/2026/99/09.xml</loc></sitemap></sitemapindex>'
    selected = task("odia", "sitemap", url="https://odia.ig.com.br/sitemap/sitemap.xml")
    first = discovery.discover(selected, lambda _: Response(xml))
    assert first["outcome"] == "continue"
    assert first["next_cursor"]["partition_gap"] is True
    assert first["child_tasks"][0]["partition_status"] == "unrecognized_calendar_partition"
    second = discovery.discover({**selected, "cursor": first["next_cursor"]}, lambda _: Response(xml))
    assert len(second["child_tasks"]) == 1
    assert second["outcome"] == "gap"
    assert second["gap_reason"] == "unrecognized_sitemap_calendar_partition"


def test_odia_statewide_dated_news_paths_are_candidates_before_body_matching():
    source = next(row for row in discovery.load_sources() if row["key"] == "odia")
    for region in ["macae", "campos", "niteroi", "sao-goncalo", "cantagalo", "sao-francisco"]:
        assert discovery._allowed_url(f"https://odia.ig.com.br/{region}/2026/06/1234567-reuniao-politica-regional.html", source, article=True)
    assert not discovery._allowed_url("https://odia.ig.com.br/esporte/2026/06/1234567-jogo-de-futebol.html", source, article=True)
    assert not discovery._allowed_url("https://odia.ig.com.br/diversao/2026/06/1234567-programa-de-tv.html", source, article=True)


def test_google_date_operators_include_entire_end_day():
    observed = []
    result = discovery.discover(task(date_to="2026-06-01"), lambda url: (observed.append(url) or Response(rss())))
    query = parse_qs(urlparse(observed[0]).query)["q"][0]
    assert "after:2026-05-31" in query
    assert "before:2026-06-02" in query
    assert result["outcome"] == "complete"
    assert result["candidates"][0]["metadata"]["google_redirect"] is True


def test_saturated_google_splits_windows_and_single_day_exposes_gap():
    fetch = lambda _: Response(rss(100))
    result = discovery.discover(task(), fetch)
    assert result["outcome"] == "split"
    assert [(row["date_from"], row["date_to"]) for row in result["child_tasks"]] == [
        ("2026-06-01", "2026-06-04"), ("2026-06-05", "2026-06-07")]
    last_day = discovery.discover(task(date_to="2026-06-01"), fetch)
    assert last_day["outcome"] == "gap"
    assert last_day["gap_reason"] == "google_daily_result_cap"
    assert len(last_day["candidates"]) == 100


def test_google_missing_link_entries_still_saturate_and_expose_terminal_gap():
    malformed = rss(99).replace("</channel>", "<item><title>Link ausente</title></item></channel>")
    split = discovery.discover(task(), lambda _: Response(malformed))
    assert split["raw_count"] == 100
    assert split["outcome"] == "split"
    assert len(split["candidates"]) == 99
    day = discovery.discover(task(date_to="2026-06-01"), lambda _: Response(malformed))
    assert day["outcome"] == "gap"
    assert "google_daily_result_cap" in day["gap_reason"]
    assert "google_malformed_entries:1" in day["gap_reason"]
    unsaturated = rss(1).replace("</channel>", "<item><title>Link ausente</title></item></channel>")
    gap = discovery.discover(task(), lambda _: Response(unsaturated))
    assert gap["raw_count"] == 2
    assert gap["outcome"] == "gap"
    assert gap["gap_reason"] == "google_malformed_entries:1"


@pytest.mark.parametrize("published,accepted", [
    ("2026-06-01T02:59:59Z", False), ("2026-06-01T03:00:00Z", True),
    ("2026-06-02T02:59:59.999999Z", True), ("2026-06-02T03:00:00Z", False),
    ("", True), ("invalid", True),
])
def test_sao_paulo_date_boundaries_and_unknown_review(published, accepted):
    assert discovery.in_window(published, "2026-06-01", "2026-06-01") is accepted


def test_missing_dates_never_default_to_collection_time():
    from pipeline.collectors import _parse_datetime, parse_rss_or_atom
    assert _parse_datetime("") == _parse_datetime("garbage") == ""
    article = parse_rss_or_atom(rss(published=""), "Test", "rss")[0]
    assert article.published_at == ""
    assert discovery.extract_article("<article>Sem data de publicação</article>")["published_at"] == ""


@pytest.mark.parametrize("status", [429, 502, 403])
def test_page_two_http_failures_never_claim_exhaustion(status):
    cursor = {"page": 2}
    with pytest.raises(discovery.DiscoveryError) as caught:
        discovery.discover(task("diario_do_rio", "wordpress", cursor=cursor),
                           lambda _: Response("blocked", status, headers={"Retry-After": "12"}))
    assert caught.value.status_code == status
    assert caught.value.retry_after == 12
    assert caught.value.retryable is (status != 403)
    assert cursor == {"page": 2}


def test_wordpress_filtered_empty_page_follows_raw_page_and_header_evidence():
    rows = [{"link": f"https://diariodorio.com/noticia-da-cidade-{i}", "title": {"rendered": "Título genérico"},
             "date_gmt": "2026-07-01T12:00:00"} for i in range(100)]
    result = discovery.discover(task("diario_do_rio", "wordpress"), lambda _: Response(json.dumps(rows)))
    assert result["candidates"] == []
    assert result["raw_count"] == 100
    assert result["next_cursor"] == {"page": 2}
    partial = discovery.discover(task("diario_do_rio", "wordpress"),
                                 lambda _: Response(json.dumps(rows[:1]), headers={"X-WP-TotalPages": "3"}))
    assert partial["next_cursor"] == {"page": 2}


def test_wordpress_candidates_are_fetched_before_body_name_matching():
    seen = []
    row = {"link": "https://diariodorio.com/novo-projeto-apresentado-na-camara", "title": {"rendered": "Novo projeto"},
           "date_gmt": "2026-06-01T12:00:00"}
    result = discovery.discover(task("diario_do_rio", "wordpress"),
                                lambda url: (seen.append(url) or Response(json.dumps([row]))))
    assert "search" not in parse_qs(urlparse(seen[0]).query)
    assert len(result["candidates"]) == 1
    extracted = discovery.extract_article('<article><div class="article-body"><p>O vereador Flávio Valle apresentou o projeto. '
                                         + ('A proposta será debatida pela Câmara do Rio. ' * 10) + '</p></div></article>')
    assert "Flávio Valle" in extracted["full_text"]
    assert extracted["extraction_state"] == "full_text"


def test_sitemap_discovers_section_before_name_matching_and_ignores_lastmod_as_publication():
    xml = '<urlset><url><loc>https://g1.globo.com/rj/norte-fluminense/noticia/2026/06/01/projeto-estadual-anunciado.ghtml</loc><lastmod>2026-06-02</lastmod></url>' \
          '<url><loc>https://g1.globo.com/pop-arte/noticia/cantor-anuncia-novo-disco.ghtml</loc></url></urlset>'
    result = discovery.discover(task("g1", "daily_sitemap", day="2026-06-01"), lambda _: Response(xml))
    assert len(result["candidates"]) == 1
    assert result["candidates"][0]["published_at"] == ""
    assert result["next_cursor"] == {"page": 2}
    assert result["raw_count"] == 2


def test_sitemap_index_is_checkpointed_bounded_and_cycles_are_gaps(monkeypatch):
    monkeypatch.setattr(discovery, "MAX_INDEX_CHILDREN", 2)
    xml = '<sitemapindex>' + ''.join(f'<sitemap><loc>https://www.tupi.fm/posts-{i}.xml</loc></sitemap>' for i in range(3)) + '</sitemapindex>'
    current = task("tupi", "sitemap", url="https://www.tupi.fm/sitemap.xml")
    result = discovery.discover(current, lambda _: Response(xml))
    assert len(result["child_tasks"]) == 2
    assert result["next_cursor"] == {"offset": 2}
    assert result["child_tasks"][0]["depth"] == 1
    resumed = discovery.discover({**current, "cursor": result["next_cursor"]}, lambda _: Response(xml))
    assert len(resumed["child_tasks"]) == 1 and resumed["next_cursor"] is None
    cyclic = discovery.discover(current, lambda _: Response('<sitemapindex><sitemap><loc>https://www.tupi.fm/sitemap.xml</loc></sitemap></sitemapindex>'))
    assert cyclic["outcome"] == "gap"


def test_sitemap_candidate_batches_are_bounded_even_with_filtered_empty_first_page(monkeypatch):
    monkeypatch.setattr(discovery, "MAX_CANDIDATES", 1)
    xml = '<urlset><url><loc>https://www.tupi.fm/esportes/noticia-fora-da-politica</loc></url>' \
          '<url><loc>https://www.tupi.fm/politica/noticia-sobre-debate-estadual</loc></url></urlset>'
    current = task("tupi", "sitemap", url="https://www.tupi.fm/sitemap.xml")
    result = discovery.discover(current, lambda _: Response(xml))
    assert result["candidates"] == [] and result["next_cursor"] == {"offset": 1}
    resumed = discovery.discover({**current, "cursor": result["next_cursor"]}, lambda _: Response(xml))
    assert len(resumed["candidates"]) == 1 and resumed["outcome"] == "complete"


@pytest.mark.parametrize("text", ["<html>captcha</html>", "<rss>broken", '<!DOCTYPE rss [<!ENTITY x "y">]><rss/>'])
def test_malformed_or_non_feed_google_responses_are_failures(text):
    with pytest.raises(discovery.DiscoveryError):
        discovery.discover(task(), lambda _: Response(text))


def test_extraction_removes_related_blocks_without_full_page_fallback():
    body = "O projeto foi discutido em plenário. " * 15
    raw = '<html><head><meta property="og:title" content="Projeto discutido"><meta property="article:published_time" content="2026-06-01T22:00:00-03:00"></head>' \
          '<body><nav>Eduardo Paes</nav><article><div class="entry-content"><p>' + body + '</p>' \
          '<div class="related-posts"><div><p>Flávio Valle</p></div></div><aside>Pedro Duarte</aside></div></article></body></html>'
    extracted = discovery.extract_article(raw)
    assert extracted["extraction_state"] == "full_text"
    assert "Flávio" not in extracted["full_text"] and "Pedro" not in extracted["full_text"]
    assert "Eduardo" not in extracted["full_text"]
    assert extracted["published_at"] == "2026-06-02T01:00:00+00:00"
    assert discovery.extract_article('<nav>' + body + '</nav>')["extraction_state"] == "metadata_only"


def test_structured_article_body_and_date_are_usable_without_html_body():
    data = {"@type": "NewsArticle", "headline": "Título", "datePublished": "2026-06-01T09:00:00-03:00",
            "articleBody": "Uma reportagem sobre a disputa estadual. " * 10}
    extracted = discovery.extract_article('<script type="application/ld+json">' + json.dumps(data) + '</script>')
    assert extracted["extraction_state"] == "full_text"
    assert extracted["title"] == "Título"
    assert extracted["published_at"] == "2026-06-01T12:00:00+00:00"


def test_google_canonical_duplicates_share_candidate_url():
    feed = '<rss><channel><item><title>A</title><link>https://example.com/story?utm_source=a</link></item>' \
           '<item><title>A</title><link>https://example.com/story?utm_source=b</link></item></channel></rss>'
    result = discovery.discover(task(), lambda _: Response(feed))
    assert len(result["candidates"]) == 1


def test_google_resolver_uses_injected_fetch_for_post_and_get():
    observed = []
    url = "https://news.google.com/rss/articles/token"
    def fetch(current, **kwargs):
        observed.append((current, kwargs))
        if kwargs.get("method") == "POST":
            return Response(")]}\'\n\n" + json.dumps([["wrb.fr", "Fbv4je", json.dumps(["garturlres", "https://example.com/article-story"])]]))
        return Response('<div data-n-a-sg="signature" data-n-a-ts="123"></div>', url=url)
    assert discovery.resolve_google_redirect(url, fetch) == "https://example.com/article-story"
    assert len(observed) == 2 and observed[1][1]["method"] == "POST"


def test_legacy_google_propagates_rate_limits_for_durable_runner(monkeypatch):
    import urllib.error
    from pipeline import collectors
    def fetch(*args, **kwargs):
        raise urllib.error.HTTPError("https://news.google.com/rss", 429, "rate limit", {}, None)
    monkeypatch.setattr(collectors, "fetch_url", fetch)
    with pytest.raises(urllib.error.HTTPError):
        collectors.collect_google_news(["Eduardo Paes"], raise_on_error=True)


def test_legacy_wordpress_propagates_429_and_malformed_payload(monkeypatch):
    import urllib.error
    from pipeline import collectors
    def fetch(*args, **kwargs):
        raise urllib.error.HTTPError("https://example.com/wp-json", 429, "rate limit", {}, None)
    monkeypatch.setattr(collectors, "fetch_url", fetch)
    with pytest.raises(urllib.error.HTTPError):
        collectors.collect_wordpress_api("Paes", source_name="Test", base_url="https://example.com", raise_on_error=True)
    monkeypatch.setattr(collectors, "fetch_url", lambda *args, **kwargs: ("https://example.com", "invalid-json"))
    with pytest.raises(ValueError):
        collectors.collect_wordpress_api("Paes", source_name="Test", base_url="https://example.com", raise_on_error=True)


def test_wordpress_only_structured_invalid_next_page_proves_exhaustion():
    result = discovery.discover(task("diario_do_rio", "wordpress", cursor={"page": 2}),
                                lambda _: Response(json.dumps({"code": "rest_post_invalid_page_number"}), 400))
    assert result["outcome"] == "complete"
    for payload in ({"code": "rest_forbidden"}, {"message": "Bad request"}):
        with pytest.raises(discovery.DiscoveryError):
            discovery.discover(task("diario_do_rio", "wordpress", cursor={"page": 2}),
                               lambda _: Response(json.dumps(payload), 400))


def test_legacy_globo_raw_page_preserves_pagination_when_window_filters_all(monkeypatch):
    from pipeline import collectors
    from pipeline.settings import FLAVIO_INTERNAL_SEARCH_TARGETS
    adapter = next(row for row in FLAVIO_INTERNAL_SEARCH_TARGETS if row.mode == "globo_api")
    hits = [{"_source": {"url": f"https://oglobo.globo.com/politica/noticia-do-debate-{i}.ghtml",
                         "title": "Debate no Estado", "issued": "2026-07-01T12:00:00Z"}} for i in range(10)]
    monkeypatch.setattr(collectors, "post_json", lambda *args, **kwargs: ("https://busca.globo.com", json.dumps([{"result": {"hits": {"hits": hits}}}])))
    result = collectors._collect_globo_internal_search(adapter, query="Paes", limit_per_adapter=10,
                    request_timeout=10, date_from="2026-06-01", date_to="2026-06-07", max_pages=1, raise_on_error=True)
    assert result == []
    assert result.raw_count == 10 and result.has_next is True


def test_legacy_internal_search_propagates_parse_failure(monkeypatch):
    from pipeline import collectors
    from pipeline.settings import FLAVIO_INTERNAL_SEARCH_TARGETS
    adapter = next(row for row in FLAVIO_INTERNAL_SEARCH_TARGETS if row.mode == "globo_api")
    monkeypatch.setattr(collectors, "post_json", lambda *args, **kwargs: ("https://busca.globo.com", "<html>captcha</html>"))
    with pytest.raises(ValueError):
        collectors.collect_internal_site_search(["Paes"], adapters=[adapter], max_pages_per_adapter=1, raise_on_error=True)


def test_inline_related_paragraphs_are_excluded_from_article_body():
    raw = '<article><div itemprop="articleBody"><p>O assunto é a proposta estadual. ' + ('Detalhes serão apresentados em reunião pública. ' * 15) + '</p><p>Leia também: <a href="/outra">Pedro Duarte anunciou um projeto</a></p></div></article>'
    extracted = discovery.extract_article(raw)
    assert extracted["extraction_state"] == "full_text"
    assert "Pedro Duarte" not in extracted["full_text"]


def test_archive_local_publication_time_keeps_end_day():
    from pipeline.collectors import _parse_pt_br_datetime
    parsed = _parse_pt_br_datetime("1 junho 2026, 23h30")
    assert parsed == "2026-06-02T02:30:00+00:00"
    assert discovery.in_window(parsed, "2026-06-01", "2026-06-01")


def test_benchmark_database_guard_rejects_production_and_nonlocal_urls():
    from tools.political_scale_benchmark import guarded_database_url
    assert guarded_database_url("postgresql://user@127.0.0.1:55439/political_test_scale")
    for url in ("postgresql://user@127.0.0.1/production", "postgresql://user@db.example.com/political_test_scale", "sqlite:///test"):
        with pytest.raises(ValueError):
            guarded_database_url(url)
