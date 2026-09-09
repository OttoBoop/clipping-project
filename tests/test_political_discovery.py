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
    assert "google_news" in sources["rc24h"]["strategies"]
    assert "google_news" in sources["j3news"]["strategies"]
    assert "wordpress" not in sources["metropoles"]["strategies"]
    assert all("site:" in row["query"] for row in tasks if row["strategy"] == "google_news")
    assert any(row.get("url") == "https://www.metropoles.com/sitemap/google-news.xml" for row in tasks)
    assert "https://odia.ig.com.br/sitemap/sitemap.xml" in sources["odia"]["sitemap_urls"]


def test_cbn_verified_rio_election_and_podcast_paths_are_discovered_before_body_matching():
    urls = ['https://cbn.globo.com/rio-de-janeiro/noticia/2026/08/09/medidas-apos-acidente.ghtml',
            'https://cbn.globo.com/coberturas/eleicoes-2026/noticia/2026/08/09/primeiros-debates.ghtml',
            'https://cbn.globo.com/podcasts/cbn-eleicoes/noticia/2026/08/09/disputa-estadual.ghtml',
            'https://cbn.globo.com/esporte/noticia/2026/08/09/partida-de-futebol.ghtml']
    xml='<urlset>'+''.join('<url><loc>'+url+'</loc></url>' for url in urls)+'</urlset>'
    result=discovery.discover(task('cbn','daily_sitemap',day='2026-08-09',date_from='2026-08-09',date_to='2026-08-09'),lambda _:Response(xml))
    assert [row['url'] for row in result['candidates']]==urls[:3]
    assert result['raw_count']==4


def test_google_fanout_is_global_plus_four_historical_domains_for_all_24_names():
    snapshots = [{"key": f"person_{i}", "display_name": f"Pessoa {i}"} for i in range(24)]
    tasks = discovery.build_tasks(snapshots, "2026-06-01", "2026-06-07")
    google = [row for row in tasks if row["strategy"] == "google_news"]
    assert len(google) == 24 * 5
    assert {row["source_key"] for row in google} == {"google_news", "metropoles", "rc24h", "j3news", "diario_do_rio"}
    assert {row["target_ids"][0] for row in google if row["source_key"] == "google_news"} == {row["key"] for row in snapshots}


def test_aliases_share_queries_across_case_accents_spacing_and_targets():
    snapshots = [{"key": "one", "display_name": "Flávio Valle", "exact_aliases": ["Flavio Valle", "FLÁVIO  VALLE"]},
                 {"key": "two", "display_name": "flavio valle"}]
    tasks = discovery.build_tasks(snapshots, "2026-06-01", "2026-06-01", ["google_news"])
    assert len(tasks) == 1
    assert tasks[0]["target_ids"] == ["one", "two"]


def rc_cards(ids):
    return ''.join('<div class="tdb_module_loop td_module_wrap"><h3 class="entry-title td-module-title">'
                   f'<a href="https://rc24h.com.br/noticia-regional-{key}/">Notícia regional {key}</a>'
                   '</h3></div>' for key in ids)


def rc_month_page(ids=range(3, 11), *, nonce="fresh-public-token", prefix_offset=3):
    attrs = {"block_type": "tdb_loop", "date_query": {"year": 2026, "month": 6, "day": ""},
             "offset": str(prefix_offset), "limit": "8", "td_column_number": 3}
    return '<script>var td_ajax_url="https://rc24h.com.br/wp-admin/admin-ajax.php?td_theme_name=Newspaper";' \
           'var tdBlockNonce=' + json.dumps(nonce) + ';block_month.atts = \'' + json.dumps(attrs) + "';</script>" \
           '<div id="month">' + rc_cards(ids) + '</div><footer>' + rc_cards([900]) + '</footer>'


def rc_ajax(ids, *, finished=False):
    return Response(json.dumps({"td_block_id": "month", "td_data": rc_cards(ids), "td_hide_next": finished}))


def test_rc_month_tasks_are_shared_across_targets_and_keep_google_history():
    targets = [{"key": str(i), "display_name": f"Pessoa {i}"} for i in range(24)]
    tasks = discovery.build_tasks(targets, "2026-06-15", "2026-08-03", ["rc24h"])
    archive = [row for row in tasks if row["strategy"] == "rc24h_archive"]
    assert [(row["month"], row["date_from"], row["date_to"]) for row in archive] == [
        ("2026-06", "2026-06-15", "2026-06-30"), ("2026-07", "2026-07-01", "2026-07-31"),
        ("2026-08", "2026-08-01", "2026-08-03")]
    assert all(len(row["target_ids"]) == 24 for row in archive)
    assert any(row["strategy"] == "google_news" for row in tasks)


def test_rc_prefix_recovery_and_resumed_original_offset_keep_dates_unknown():
    calls = []
    def fetch(url, **kwargs):
        calls.append((url, kwargs))
        if not kwargs:
            return Response(rc_month_page(nonce=f"public-token-{len(calls)}"))
        data = kwargs["data"]
        attrs = json.loads(data["td_atts"])
        assert attrs["date_query"] == {"year": 2026, "month": 6, "day": ""}
        if data["td_current_page"] == "1":
            assert attrs["offset"] == "0"
            return rc_ajax(range(8))
        assert data["td_current_page"] == "2" and attrs["offset"] == "3"
        assert data["td_magic_token"] == "public-token-3"
        return rc_ajax(range(11, 19))
    run = task("rc24h", "rc24h_archive", month="2026-06")
    first = discovery.discover(run, fetch)
    assert first["outcome"] == "continue" and first["raw_count"] == 16
    assert len(first["candidates"]) == 11
    assert {row["url"] for row in first["candidates"]} == {f"https://rc24h.com.br/noticia-regional-{i}" for i in range(11)}
    assert all(not row["published_at"] and row["metadata"]["needs_date_review"] for row in first["candidates"])
    second = discovery.discover({**run, "cursor": first["next_cursor"]}, fetch)
    assert second["outcome"] == "continue" and len(second["candidates"]) == 8
    assert len(calls) == 4 and second["next_cursor"]["page"] == 3


@pytest.mark.parametrize("finished", [False, True])
def test_rc_repeated_page_is_a_gap_even_when_publisher_claims_exhaustion(finished):
    run = task("rc24h", "rc24h_archive", month="2026-06")
    first = discovery.discover(run, lambda url, **kw: rc_ajax(range(8)) if kw else Response(rc_month_page()))
    repeated = discovery.discover({**run, "cursor": first["next_cursor"]},
        lambda url, **kw: rc_ajax(reversed(range(3, 11)), finished=finished) if kw else Response(rc_month_page()))
    assert repeated["outcome"] == "gap" and repeated["gap_reason"] == "rc24h_repeated_archive_page"


def test_rc_offset_zero_prefix_repetition_cannot_claim_end_of_month():
    run = task("rc24h", "rc24h_archive", month="2026-06")
    first = discovery.discover(run, lambda url, **kw: rc_ajax(range(8)) if kw else Response(rc_month_page()))
    # Real offset0/page56 returned the prefix page and td_hide_next=true.
    repeated = discovery.discover({**run, "cursor": first["next_cursor"]},
        lambda url, **kw: rc_ajax(range(8), finished=True) if kw else Response(rc_month_page()))
    assert repeated["outcome"] == "gap" and repeated["gap_reason"] == "rc24h_repeated_archive_page"


@pytest.mark.parametrize("finished,expected", [(False, "gap"), (True, "complete")])
def test_rc_empty_page_requires_explicit_publisher_exhaustion(finished, expected):
    run = task("rc24h", "rc24h_archive", month="2026-06", cursor={"page": 2, "archive_offset": 3})
    result = discovery.discover(run, lambda url, **kw: rc_ajax([], finished=finished) if kw else Response(rc_month_page()))
    assert result["outcome"] == expected


def test_rc_missing_month_loop_does_not_collect_current_footer_links():
    result = discovery.discover(task("rc24h", "rc24h_archive", month="2026-06"), lambda _: Response('<footer>'+rc_cards([900])+'</footer>'))
    assert result["outcome"] == "gap" and result["candidates"] == []


def test_rc_changed_page_limit_cannot_skip_articles_after_resume():
    run = task("rc24h", "rc24h_archive", month="2026-06")
    first = discovery.discover(run, lambda url, **kw: rc_ajax(range(8)) if kw else Response(rc_month_page()))
    assert first["next_cursor"]["archive_limit"] == 8
    calls = []
    def changed_template(url, **kwargs):
        calls.append((url, kwargs))
        return Response(rc_month_page().replace('"limit": "8"', '"limit": "12"'))
    resumed = discovery.discover({**run, "cursor": first["next_cursor"]}, changed_template)
    assert resumed["outcome"] == "gap" and resumed["gap_reason"] == "rc24h_archive_offset_or_limit_changed"
    assert len(calls) == 1 and resumed["candidates"] == []


def test_rc_missing_prefix_evidence_is_retained_as_gap_through_exhaustion():
    run = task("rc24h", "rc24h_archive", month="2026-06")
    first = discovery.discover(run, lambda url, **kw: rc_ajax([0, 1]) if kw else Response(rc_month_page()))
    assert first["next_cursor"]["parse_gap"] and len(first["candidates"]) == 10
    final = discovery.discover({**run, "cursor": first["next_cursor"]},
        lambda url, **kw: rc_ajax([11], finished=True) if kw else Response(rc_month_page()))
    assert final["outcome"] == "gap" and final["gap_reason"] == "rc24h_archive_parse_gap"
    assert len(final["candidates"]) == 1


def test_rc_rate_limit_is_retryable_and_does_not_become_empty_archive():
    run = task("rc24h", "rc24h_archive", month="2026-06", cursor={"page": 2})
    with pytest.raises(discovery.DiscoveryError) as raised:
        discovery.discover(run, lambda url, **kw: Response('', status_code=429, headers={"Retry-After": "60"}) if kw else Response(rc_month_page()))
    assert raised.value.retryable and raised.value.status_code == 429 and raised.value.retry_after == 60


def test_rc_unparseable_ajax_response_and_page_cap_are_explicit_gaps(monkeypatch):
    run = task("rc24h", "rc24h_archive", month="2026-06", cursor={"page": 2})
    invalid = discovery.discover(run, lambda url, **kw: Response('0') if kw else Response(rc_month_page()))
    assert invalid["outcome"] == "gap" and invalid["gap_reason"] == "rc24h_pagination_response_invalid"
    source = next(row for row in discovery.load_sources() if row["key"] == "rc24h")
    monkeypatch.setattr(discovery, "load_sources", lambda: [{**source, "max_pages": 2}])
    capped = discovery.discover(run, lambda url, **kw: rc_ajax([11]) if kw else Response(rc_month_page()))
    assert capped["outcome"] == "gap" and capped["gap_reason"] == "rc24h_empty_page_or_page_cap"


def test_explicit_direct_gaps_generate_stable_scoped_fallbacks_without_recursion():
    snapshots = [{"key": "paes", "display_name": "Eduardo Paes"}]
    direct = task("g1", "daily_sitemap", day="2026-06-03")
    fallback = discovery.fallback_tasks(direct, snapshots)
    assert len(fallback) == 1
    assert fallback[0]["query"] == '"Eduardo Paes" site:g1.globo.com'
    assert fallback[0]["date_from"] == fallback[0]["date_to"] == "2026-06-03"
    assert discovery.fallback_tasks(fallback[0], snapshots) == []
    assert discovery.fallback_tasks({**direct, "cursor": {"page": 2}}, snapshots) == fallback


def test_tupi_annual_index_skips_years_outside_requested_period():
    urls = [f"https://www.tupi.fm/sitemap-posttype-post.{year}.xml" for year in [2026, 2025, 2024, 2023]]
    xml = "<sitemapindex>" + "".join(f"<sitemap><loc>{url}</loc></sitemap>" for url in urls) + "</sitemapindex>"
    result = discovery.discover(task("tupi", "sitemap", url="https://www.tupi.fm/sitemap.xml"), lambda _: Response(xml))
    assert [row["url"] for row in result["child_tasks"]] == urls[:1]
    assert result["child_tasks"][0]["partition_status"] == "requested_year_partition"


def test_tupi_default_uses_verified_publication_date_api_instead_of_undated_annual_scan():
    tasks = discovery.build_tasks([{"key": "paes", "display_name": "Eduardo Paes"}],
                                  "2026-08-09", "2026-08-09", ["tupi"])
    assert [row["strategy"] for row in tasks] == ["wordpress"]
    assert discovery.fallback_tasks(tasks[0], [{"key": "paes", "display_name": "Eduardo Paes"}])[0]["query"] == '"Eduardo Paes" site:tupi.fm'


def test_tupi_known_nonarticle_sitemap_branches_are_not_scheduled():
    names = ['posttype-post.2026', 'posttype-post.2025', 'posttype-webstories.2026',
             'posttype-webstories.2025', 'taxonomy-category', 'taxonomy-post_tag', 'author', 'news']
    urls = [f'https://www.tupi.fm/sitemap-{name}.xml' for name in names]
    xml = '<sitemapindex>' + ''.join(f'<sitemap><loc>{url}</loc></sitemap>' for url in urls) + '</sitemapindex>'
    current = task('tupi', 'sitemap', url='https://www.tupi.fm/sitemap.xml')
    result = discovery.discover(current, lambda _: Response(xml))
    assert [row['url'] for row in result['child_tasks']] == [urls[0], urls[-1]]
    assert result['outcome'] == 'complete'


def _stream_response(tmp_path, xml):
    import hashlib
    digest = hashlib.sha256(xml.encode()).hexdigest()
    path = tmp_path / (digest + ".xml")
    path.write_text(xml)
    response = Response("")
    response.sitemap_path, response.sitemap_snapshot = str(path), digest
    return response


def test_tupi_stream_uses_seekable_snapshot_cursor_and_builds_index_once(tmp_path, monkeypatch):
    xml = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(
        f'<url><loc>https://www.tupi.fm/politica/noticia-politica-numero-{i}</loc><lastmod>2026-06-01</lastmod></url>' for i in range(5)) + '</urlset>'
    response = _stream_response(tmp_path, xml)
    monkeypatch.setattr(discovery, "MAX_CANDIDATES", 2)
    seen = []
    def fetch(url, **kwargs):
        seen.append(kwargs)
        return response
    current = task("tupi", "sitemap", url="https://www.tupi.fm/sitemap-posttype-post.2026.xml")
    first = discovery.discover(current, fetch)
    assert first["raw_count"] == 2 and first["next_cursor"]["offset"] > 0
    assert first["candidates"][0]["published_at"] == ""
    monkeypatch.setattr(discovery, "_stream_sitemap_entries", lambda _: pytest.fail("snapshot parsed twice"))
    second = discovery.discover({**current, "cursor": first["next_cursor"]}, fetch)
    third = discovery.discover({**current, "cursor": second["next_cursor"]}, fetch)
    assert third["outcome"] == "complete"
    assert [row["url"] for page in [first, second, third] for row in page["candidates"]] == [f"https://www.tupi.fm/politica/noticia-politica-numero-{i}" for i in range(5)]
    assert seen[1]["sitemap_snapshot"] == response.sitemap_snapshot


def test_tupi_lost_snapshot_restarts_changed_content_without_skipping_entries(tmp_path, monkeypatch):
    monkeypatch.setattr(discovery, "MAX_CANDIDATES", 1)
    current = task("tupi", "sitemap", url="https://www.tupi.fm/sitemap-posttype-post.2026.xml")
    old = _stream_response(tmp_path, '<urlset><url><loc>https://www.tupi.fm/politica/old-political-story</loc></url></urlset>')
    first = discovery.discover(current, lambda *args, **kw: old)
    changed = _stream_response(tmp_path, '<urlset><url><loc>https://www.tupi.fm/politica/new-first-political-story</loc></url></urlset>')
    resumed = discovery.discover({**current, "cursor": first["next_cursor"]}, lambda *args, **kw: changed)
    assert resumed["candidates"][0]["url"].endswith("/new-first-political-story")


@pytest.mark.parametrize("xml", ['<!DOCTYPE urlset [<!ENTITY bad "unsafe">]><urlset/>', '<urlset><url><loc>https://www.tupi.fm/politica/test</loc></url>'])
def test_tupi_stream_rejects_entity_declarations_and_truncated_xml_before_committing(tmp_path, xml):
    response = _stream_response(tmp_path, xml)
    current = task("tupi", "sitemap", url="https://www.tupi.fm/sitemap-posttype-post.2026.xml")
    with pytest.raises(discovery.DiscoveryError):
        discovery.discover(current, lambda *args, **kw: response)
    assert not list(tmp_path.glob("*.entries.jsonl"))


def test_sitemap_image_caption_is_not_used_as_article_title():
    xml = '<urlset xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"><url><loc>https://www.tupi.fm/rio/noticia-politica-da-cidade</loc><image:image><image:title>Foto de Lula na Sapucaí</image:title></image:image></url></urlset>'
    result = discovery.discover(task("tupi", "sitemap", url="https://www.tupi.fm/sitemap-news.xml"), lambda _: Response(xml))
    assert result["candidates"][0]["title"] == ""


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


@pytest.mark.parametrize("end_day", ["2026-06-01", "2026-06-07"])
def test_diario_narrow_window_defers_undated_entries_with_persistent_gap(monkeypatch, end_day):
    monkeypatch.setattr(discovery, "MAX_CANDIDATES", 2)
    xml = '<urlset><url><loc>https://www.diariodorio.com/sem-data.html</loc><lastmod>2026-06-01</lastmod></url>' \
          '<url><loc>https://www.diariodorio.com/data-invalida.html</loc><publication_date>invalid</publication_date></url>' \
          '<url><loc>https://www.diariodorio.com/data-verificada.html</loc><publication_date>2026-06-01T12:00:00-03:00</publication_date></url></urlset>'
    current = task("diario_do_rio", "sitemap", date_to=end_day, url="https://www.diariodorio.com/sitemap.xml")
    first = discovery.discover(current, lambda _: Response(xml))
    assert first["candidates"] == [] and first["raw_count"] == 2
    assert first["next_cursor"] == {"offset": 2, "undated_deferred": 2}
    last = discovery.discover({**current, "cursor": first["next_cursor"]}, lambda _: Response(xml))
    assert len(last["candidates"]) == 1 and last["raw_count"] == 1
    assert last["outcome"] == "gap"
    assert last["gap_reason"] == "undated_sitemap_deferred_for_narrow_window:2"
    # This domain already has historical Google tasks; a gap must not duplicate them.
    assert discovery.fallback_tasks(current, [{"key": "paes", "display_name": "Eduardo Paes"}]) == []
    planned = discovery.build_tasks([{"key": "paes", "display_name": "Eduardo Paes"}], "2026-06-01", end_day, ["diario_do_rio"])
    assert len([row for row in planned if row["strategy"] == "google_news"]) == 1


def test_diario_wider_window_keeps_unknown_dates_for_body_review():
    xml = '<urlset><url><loc>https://www.diariodorio.com/sem-data.html</loc><lastmod>2026-06-01</lastmod></url></urlset>'
    result = discovery.discover(task("diario_do_rio", "sitemap", date_to="2026-06-08", url="https://www.diariodorio.com/sitemap.xml"), lambda _: Response(xml))
    assert result["outcome"] == "complete" and len(result["candidates"]) == 1
    assert result["candidates"][0]["published_at"] == ""
    assert result["candidates"][0]["metadata"]["needs_date_review"] is True


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


def test_extraction_primary_body_cannot_be_replaced_by_longer_infinite_scroll_story():
    primary = "Eduardo Paes não compareceu ao debate. " * 12
    unrelated = "Hugo Leal participa de outra campanha. " * 60
    raw = '<div class="entry-content"><p>' + primary + '</p></div>' \
          '<div id="post-expansivel"><div class="elementor-widget-theme-post-content"><p>' + unrelated + '</p></div></div>' \
          '<article><div class="entry-content"><p>' + unrelated + '</p></div></article>'
    result = discovery.extract_article(raw)
    assert result["extraction_state"] == "full_text"
    assert result["full_text"] == primary.strip()
    assert "Hugo Leal" not in result["full_text"]


def test_extraction_nested_primary_body_keeps_full_editorial_text_and_blocks_expanded_posts():
    primary = "O primeiro debate ocorreu no Rio de Janeiro. " * 12
    raw = '<article><div class="entry-content"><p>' + primary + '</p><div class="more-posts">Hugo Leal</div></div>' \
          '<div id="post-expansivel"><div class="entry-content">' + ('Hugo Leal ' * 100) + '</div></div></article>'
    result = discovery.extract_article(raw)
    assert primary.strip() in result["full_text"]
    assert "Hugo Leal" not in result["full_text"]


def test_cbn_playlist_and_next_story_widgets_preserve_editorial_continuation():
    before = "Familiares aguardavam a liberação dos corpos no Instituto Médico-Legal após o acidente durante um voo panorâmico sobre a cidade."
    middle = "O prefeito Eduardo Cavaliere pediu à agência um reforço na fiscalização e a suspensão temporária desse tipo de passeio."
    after = "Uma câmera foi recuperada intacta. O material será analisado junto com os destroços para reconstruir os momentos anteriores à queda."
    playlist = "Hugo Leal comenta uma notícia diferente no podcast mais recente."
    next_story = "Pedro Paulo participa de outro evento amanhã."
    raw = '<div class="mrf-article-body"><div class="mc-article-body"><article><p>' + before + '</p>' \
          '<div class="widget-playlist-player"><ol><li><p class="audio-title">' + playlist + '</p></li></ol></div>' \
          '<p>' + middle + '</p><section class="passador-materia"><a>' + next_story + '</a></section>' \
          '<p>' + after + '</p></article></div></div>'
    raw += '<script type="application/ld+json">' + json.dumps({
        "@type": "NewsArticle", "articleBody": " ".join([before, playlist, middle, next_story, after])
    }) + '</script>'
    result = discovery.extract_article(raw)
    assert result["extraction_state"] == "full_text"
    assert all(paragraph in result["full_text"] for paragraph in (before, middle, after))
    assert "Hugo Leal" not in result["full_text"]
    assert "Pedro Paulo" not in result["full_text"]


def test_rc24h_exact_editorial_container_keeps_long_column_and_excludes_outer_widgets():
    # Exact class tokens and nesting observed in captured public RC24h articles,
    # including the multi-section Boca Miúda column. Body text is synthetic.
    url = "https://rc24h.com.br/boca-miuda-column"
    opening = "Eduardo Paes participou do encontro municipal. " + "A coluna acompanha as decisões locais e seus efeitos para os moradores. " * 12
    later = "Mais notícias sobre o orçamento foram discutidas pelos vereadores durante a sessão."
    conclusion = "Pedro Paulo apresentou propostas ao governo do Rio na última seção editorial."
    editorial = opening + "\n" + later + "\n" + conclusion
    unrelated = "Hugo Leal aparece em outra notícia publicada hoje. " * 60
    structured = json.dumps({"@type": "NewsArticle", "url": url, "articleBody": editorial + unrelated})
    raw = f'''<meta property="og:url" content="{url}">
      <meta property="article:published_time" content="2026-06-01T22:37:04+00:00">
      <script type="application/ld+json">{structured}</script>
      <article><h1>Boca Miúda</h1>
      <div class="td_block_wrap tdb_single_content tdi_72 td-pb-border-top td_block_template_1 td-post-content tagdiv-type">
        <div class="tdb-block-inner td-fix-index"><p>{opening}</p><h2>ORÇAMENTO</h2><p>{later}</p>
        <div class="m-a-box"><div class="m-a-box-bio">Laura Carneiro appears only in the author biography.</div></div>
        <h2>ÚLTIMA SEÇÃO</h2><p>{conclusion}</p></div>
      </div><div class="td_block_wrap tdb_loop"><h2>Mais notícias</h2><p>{unrelated}</p></div></article>'''
    result = discovery.extract_article(raw)
    assert result["extraction_state"] == "full_text"
    assert opening in result["full_text"] and later in result["full_text"] and conclusion in result["full_text"]
    assert "ÚLTIMA SEÇÃO" in result["full_text"] and "Hugo Leal" not in result["full_text"]
    assert "Laura Carneiro" not in result["full_text"]
    assert result["published_at"] == "2026-06-01T22:37:04+00:00"


def test_rc24h_short_editorial_container_does_not_fall_back_to_footer_or_later_article():
    unrelated = "Hugo Leal e Eduardo Paes constam em outra matéria. " * 60
    raw = f'''<link rel="canonical" href="https://rc24h.com.br/restricted-story/">
      <script type="application/ld+json">{json.dumps({'@type': 'NewsArticle', 'articleBody': unrelated})}</script>
      <article><div class="tdb_single_content td-post-content"><p>Conteúdo indisponível.</p></div>
        <div class="tdb_loop">{unrelated}</div></article>
      <article><div class="tdb_single_content td-post-content">{unrelated}</div></article>'''
    result = discovery.extract_article(raw)
    assert result["full_text"] == "Conteúdo indisponível."
    assert result["extraction_state"] == "metadata_only"


def test_rc24h_container_preference_requires_exact_classes_and_publisher_identity():
    editorial = "A reportagem explica os investimentos previstos para os próximos meses. " * 12
    later = "Uma segunda seção legítima descreve a fiscalização desses recursos."
    for url, classes in [("https://example.com/story", "tdb_single_content td-post-content"),
                         ("https://rc24h.com.br/story", "tdb_single_content_preview td-post-content")]:
        raw = f'<link rel="canonical" href="{url}"><article><div class="{classes}">{editorial}</div><p>{later}</p></article>'
        assert later in discovery.extract_article(raw)["full_text"]


def test_metropoles_related_news_nested_articles_cannot_reenter_through_jsonld():
    # Structure verified in the actual publisher page for saved article98.
    url = "https://www.metropoles.com/brasil/campaign-recordings"
    opening = "O presidente iniciou as gravações da campanha com candidatos de diversos estados. " * 5
    later = "O candidato ao governo do Rio de Janeiro, Eduardo Paes, deve participar das gravações na sexta."
    ending = "Além das filmagens, a equipe preparará mensagens destinadas às campanhas estaduais."
    unrelated = "Hugo Leal aparece em outra reportagem sem relação com as gravações."
    structured = json.dumps({"@type": "NewsArticle", "url": url,
        "articleBody": opening + ' Leia também ' + unrelated * 20 + later + ending})
    raw = f'''<meta property="og:url" content="{url}">
      <meta property="article:published_time" content="2026-08-13T15:08:00-03:00">
      <script type="application/ld+json">{structured}</script>
      <article class="mtp-NTEzNjM0OA=="><section>
        <div class="conteudoNoticia-module__P4yESq__conteudoNoticia enquete-module__5j_1KW__enqueteScope">
        <p>{opening}</p><div class="m-news-list-content m-related-news"><h2>Leia também</h2>
          <ul class="columns is-multiline"><li class="column is-full"><article class="m-feed m-feed-small">
          <div class="m-box-text"><h3 class="m-title"><a>{unrelated}</a></h3></div></article></li></ul>
        </div><p>{later}</p><p>{ending}</p></div>
      </section></article>'''
    result = discovery.extract_article(raw)
    assert result["extraction_state"] == "full_text"
    assert all(paragraph in result["full_text"] for paragraph in [opening, later, ending])
    assert "Leia também" not in result["full_text"] and "Hugo Leal" not in result["full_text"]
    assert result["published_at"] == "2026-08-13T18:08:00+00:00"


@pytest.mark.parametrize("host", ["g1.globo.com", "extra.globo.com", "oglobo.globo.com"])
def test_globo_headline_lists_and_news_box_preserve_later_editorial_sections(host):
    # Exact structures from actual saved G1 237, Extra 364 and O Globo 1194.
    # These generic list classes also serve genuine prose; links/lead-ins must
    # be inspected rather than dropping every bullet list on the publisher.
    url = f"https://{host}/rio/noticia/2026/08/12/onibus.ghtml"
    opening = "Os novos ônibus terão piso baixo, acesso facilitado e equipamentos de segurança para todos os passageiros. " * 4
    later = "Eduardo Cavaliere explicou o calendário das entregas e lembrou a proposta apresentada por Eduardo Paes."
    ending = "A última seção informa as próximas linhas atendidas e mantém a comparação final com a transformação do BRT."
    unrelated = "Hugo Leal aparece em uma reportagem diferente."
    raw = f'''<meta property="og:url" content="{url}">
      <meta property="article:published_time" content="2026-08-12T10:29:34-03:00">
      <script type="application/ld+json">{json.dumps({'@type':'NewsArticle','url':url,'articleBody':opening+unrelated*50+later+ending})}</script>
      <div class="mc-article-body"><article><div class="wall protected-content"><p>{opening}</p>
        <div class="mc-column content-text active-extra-styles" data-block-type="raw">
          <p class="content-text__container"><ul class="content-unordered-list">
            <li><strong>Outra matéria:</strong> <a class href="/rio/outra.ghtml">{unrelated}</a></li>
            <li><strong>Uma terceira manchete; </strong><a href="/rio/terceira.ghtml"><strong>Laura Carneiro está em outra pauta.</strong></a></li>
            <li><a href="/rio/quarta.ghtml">Pedro Duarte está em um assunto separado.</a></li>
          </ul></p></div><p>{later}</p><h2>Última seção</h2><p>{ending}</p>
        <section class="mc-column box-wrapper"><div class="you-need-to-know-theme">
          <h2 class="you-need-to-know-theme__title">Notícias do Rio:</h2><div><ul><li>{unrelated}</li></ul></div>
        </div></section></div><section class="passador-materia"><a>Próxima: {unrelated}</a></section>
      </article></div>'''
    result = discovery.extract_article(raw)
    assert all(text in result["full_text"] for text in (opening, later, ending, "Última seção"))
    assert not any(text in result["full_text"] for text in ("Hugo Leal", "Laura Carneiro", "Pedro Duarte", "Notícias do Rio", "Próxima"))
    assert result["published_at"] == "2026-08-12T13:29:34+00:00"
    assert result["extraction_state"] == "full_text"


@pytest.mark.parametrize("item", [
    'A proposta de Eduardo Paes foi discutida, conforme <a href="/rio/antes.ghtml">a reportagem anterior</a>, e aprovada na reunião.',
    '<strong>Eduardo Paes explicou a proposta completa.</strong> <a href="/rio/antes.ghtml">Veja os dados</a>',
    '<a href="https://camara.rio/documento">Pedro Paulo apresenta a íntegra do projeto</a>',
    '<a href="/rio/atual.ghtml#propostas">Eduardo Paes nas propostas desta mesma reportagem</a>',
    'Eduardo Paes apresentou duas propostas.<ul><li><a href="/rio/antes.ghtml">Uma referência</a></li></ul>',
])
def test_globo_ordinary_lists_with_prose_citations_or_nested_items_survive(item):
    opening = "A reportagem explica as decisões tomadas em uma reunião pública. " * 10
    raw = f'<link rel="canonical" href="https://g1.globo.com/rio/atual.ghtml"><article><p>{opening}</p><ul class="content-unordered-list"><li>{item}</li></ul><p>Encerramento editorial preservado.</p></article>'
    result = discovery.extract_article(raw)
    assert "Encerramento editorial preservado." in result["full_text"]
    assert "Eduardo Paes" in result["full_text"] or "Pedro Paulo" in result["full_text"]


def test_globo_related_selectors_require_exact_publisher_and_tokens():
    for host, classes in [("example.com", "you-need-to-know-theme"), ("g1.globo.com", "you-need-to-know-theme-editorial")]:
        raw = f'<link rel="canonical" href="https://{host}/rio/atual.ghtml"><article><div class="{classes}">Texto editorial de Eduardo Paes.</div></article>'
        assert "Eduardo Paes" in discovery.extract_article(raw)["full_text"]


def test_globo_short_primary_text_does_not_reintroduce_related_jsonld():
    raw = '<link rel="canonical" href="https://extra.globo.com/rio/atual.ghtml"><article><p>Assine para continuar.</p><ul class="content-unordered-list"><li><a href="/rio/outra.ghtml">Hugo Leal em outra notícia.</a></li></ul></article>'
    raw += '<script type="application/ld+json">'+json.dumps({'@type':'NewsArticle','articleBody':'Hugo Leal em outra notícia. '*50})+'</script>'
    result = discovery.extract_article(raw)
    assert result["full_text"] == "Assine para continuar."
    assert result["extraction_state"] == "metadata_only"


def test_globo_related_only_primary_cannot_select_later_story_or_jsonld():
    unrelated = "Hugo Leal participa de outra notícia. " * 50
    raw = '<link rel="canonical" href="https://extra.globo.com/rio/atual.ghtml"><article><ul class="content-unordered-list"><li><a href="/rio/outra.ghtml">Hugo Leal em outra notícia.</a></li></ul></article>'
    raw += f'<article><p>{unrelated}</p></article><script type="application/ld+json">'+json.dumps({'@type':'NewsArticle','articleBody':unrelated})+'</script>'
    result = discovery.extract_article(raw)
    assert result["full_text"] == ""
    assert result["extraction_state"] == "metadata_only"


def test_odia_related_lead_outside_anchor_preserves_same_div_continuation():
    # Actual 246 has LEIA MAIS as a div text node, with later genuine prose in
    # the SAME div after the second linked headline and two line breaks.
    opening = "O prefeito explicou os planos para o evento e a organização das próximas apresentações. " * 5
    later = "Eduardo Cavaliere convidou os moradores de São Paulo para o evento no Rio."
    ending = "As negociações com a produtora serão retomadas para definir a data das apresentações."
    raw = f'''<link rel="canonical" href="https://odia.ig.com.br/rio/atual.html">
      <meta property="article:published_time" content="2026-08-14T10:29:05-03:00">
      <article><div class="article-body"><div class="texto">{opening}</div>
      <div class="texto">LEIA MAIS:&nbsp;<a href="/outra.html">Hugo Leal em outra notícia.</a></div>
      <div class="texto">LEIA MAIS:&nbsp;<a href="/terceira.html">Laura Carneiro em outro assunto.</a><br><br>{later}<br><br>{ending}</div>
      </div></article>'''
    result = discovery.extract_article(raw)
    assert all(text in result["full_text"] for text in (opening, later, ending))
    assert not any(text in result["full_text"] for text in ("LEIA MAIS", "Hugo Leal", "Laura Carneiro"))
    assert result["published_at"] == "2026-08-14T13:29:05+00:00"


def test_odia_link_removal_requires_exact_lead_at_start_of_text_block():
    for host, prefix in [("example.com", "LEIA MAIS:"), ("odia.ig.com.br", 'A entrevistada recomendou: LEIA MAIS:')]:
        raw=f'<link rel="canonical" href="https://{host}/atual.html"><article><div class="texto">{prefix}<a href="/outro">Eduardo Paes explicou o tema</a><br>Fim editorial.</div></article>'
        result=discovery.extract_article(raw)
        assert "Eduardo Paes" in result["full_text"] and "Fim editorial." in result["full_text"]


def test_short_primary_body_remains_metadata_only_even_with_long_later_article():
    raw = '<article><p>Assine para continuar.</p></article><article><p>' + ('Outra notícia extensa. ' * 100) + '</p></article>'
    result = discovery.extract_article(raw)
    assert result["extraction_state"] == "metadata_only"
    assert result["full_text"] == "Assine para continuar."


def test_empty_placeholder_article_does_not_hide_the_first_editorial_body():
    primary = "Eduardo Paes não compareceu ao debate. " * 12
    raw = '<article><script>placeholder()</script></article><div class="article-body">' + primary + '</div>'
    assert discovery.extract_article(raw)["full_text"] == primary.strip()


def test_boolean_html_attributes_do_not_crash_article_extraction():
    body = "Eduardo Paes não compareceu ao debate. " * 12
    raw = '<meta property content><link rel href><article class id><div class="entry-content" id>' \
          '<p itemprop>' + body + '</p></div></article>'
    result = discovery.extract_article(raw)
    assert result["extraction_state"] == "full_text"
    assert result["full_text"] == body.strip()


def test_j3_primary_single_text_container_extracts_body_without_sidebar_cards():
    body='O encontro discutiu propostas para o município. ' * 12 + 'Eduardo Paes participou da reunião.'
    raw='<section class="section-single"><div class="col-content-single"><div class="content-txt-single">' \
        '<h1>Propostas para a região</h1><p>'+body+'</p></div></div>' \
        '<div class="sidebar-single"><div class="card-post">Hugo Leal em outra notícia</div></div></section>'
    result=discovery.extract_article(raw)
    assert result['extraction_state']=='full_text' and body in result['full_text']
    assert 'Hugo Leal' not in result['full_text']


def test_j3_short_caption_stays_metadata_only_even_with_long_sidebar():
    raw='<div class="content-txt-single"><h1>Foto do evento</h1><p>Participantes na solenidade.</p></div>' \
        '<div class="sidebar-single">'+('Eduardo Paes em outra notícia. '*40)+'</div>'
    result=discovery.extract_article(raw)
    assert result['extraction_state']=='metadata_only'
    assert 'Eduardo Paes' not in result['full_text']


def test_structured_body_for_another_canonical_article_is_not_selected():
    primary = "Eduardo Paes não compareceu ao debate. " * 12
    raw = '<link rel="canonical" href="https://example.com/debate"><div class="entry-content">' + primary + '</div>'
    other = {"@type": "NewsArticle", "url": "https://example.com/outra-noticia", "articleBody": "Hugo Leal " * 200}
    raw += '<script type="application/ld+json">' + json.dumps(other) + '</script>'
    assert discovery.extract_article(raw)["full_text"] == primary.strip()


def test_syndicated_article_structured_body_matches_document_even_with_external_canonical():
    body = "Eduardo Paes não compareceu ao debate. " * 12
    raw = '<meta property="og:url" content="https://publisher.example/debate-copy">' \
          '<link rel="canonical" href="https://original.example/debate">'
    data = {"@type": "NewsArticle", "mainEntityOfPage": "https://publisher.example/debate-copy", "articleBody": body}
    raw += '<script type="application/ld+json">' + json.dumps(data) + '</script>'
    result = discovery.extract_article(raw)
    assert result["extraction_state"] == "full_text"
    assert result["full_text"] == body.strip()


def test_structured_body_cannot_reintroduce_explicit_related_card_inside_primary_article():
    before = "Eduardo Paes não compareceu ao debate. " * 12
    after = "Pedro Paulo foi citado no segundo bloco. " * 12
    related = "Leia também: Hugo Leal em uma notícia diferente. " * 10
    raw = '<article><p>' + before + '</p><div class="m-related-news">' + related + '</div><p>' + after + '</p></article>'
    raw += '<script type="application/ld+json">' + json.dumps({"@type": "NewsArticle", "articleBody": before + related + after}) + '</script>'
    result = discovery.extract_article(raw)
    assert before.strip() in result["full_text"] and after.strip() in result["full_text"]
    assert "Hugo Leal" not in result["full_text"] and "Leia também" not in result["full_text"]


def test_related_anchor_removal_preserves_following_editorial_text_and_decodes_entities():
    before = "Eduardo Paes não compareceu ao debate. " * 12
    after = "Depois, Pedro Paulo respondeu aos jornalistas. " * 12
    raw = '<article><div class="texto">' + before + '</div><div class="texto">' \
          '<a href="/outra-noticia">LEIA MAIS: previsão do tempo</a>' + after + '</div>' \
          '<p>O candidato disse &amp;#8220;estarei presente&amp;#8221;.</p></article>'
    result = discovery.extract_article(raw)
    assert "LEIA MAIS" not in result["full_text"] and "previsão do tempo" not in result["full_text"]
    assert before.strip() in result["full_text"] and after.strip() in result["full_text"]
    assert '“estarei presente”' in result["full_text"]


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


def test_google_resolver_reuses_landing_response_without_duplicate_get():
    url = "https://news.google.com/rss/articles/token"
    observed = []
    initial = Response('<div data-n-a-sg="signature" data-n-a-ts="123"></div>', url=url)
    def fetch(current, **kwargs):
        observed.append((current, kwargs))
        assert kwargs.get("method") == "POST"
        return Response(")]}'\n\n" + json.dumps([["wrb.fr", "Fbv4je", json.dumps(["garturlres", "https://example.com/article-story"])]]))
    assert discovery.resolve_google_redirect(url, fetch, initial_response=initial) == "https://example.com/article-story"
    assert len(observed) == 1


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


def camara_page(dates, *, start=10, extra_markup=""):
    rows = ''.join('<span class="catItemDateCreated">' + value + '</span>'
                   '<h3 class="catItemTitle"><a href="/comunicacao/noticias/' + str(3000+i) + '-projeto-estadual">Projeto estadual</a></h3>'
                   for i, value in enumerate(dates))
    return rows + extra_markup + f'<link rel="next" href="/comunicacao/noticias?limit=10&amp;start={start}">'


def test_camara_cutoff_requires_consecutive_ordered_pages_and_preserves_window_candidates():
    current = task('camara_rio', 'camara_archive', url='https://camara.rio/comunicacao/noticias', date_from='2026-08-09', date_to='2026-08-09')
    first = discovery.discover(current, lambda _: Response(camara_page(['8 setembro 2026', '7 setembro 2026'])))
    assert first['next_cursor']['previous_oldest'] == '2026-09-07'
    assert first['next_cursor']['ordered_pages'] == 1
    second = discovery.discover({**current, 'cursor':first['next_cursor']}, lambda _: Response(camara_page(['10 agosto 2026', '9 agosto 2026'],start=20)))
    assert len(second['candidates']) == 1 and second['next_cursor']['ordered_pages'] == 2
    third = discovery.discover({**current, 'cursor':second['next_cursor']}, lambda _: Response(camara_page(['8 agosto 2026', '7 agosto 2026'],start=30)))
    assert third['outcome'] == 'complete' and third['next_cursor'] is None and third['raw_count'] == 2


def test_camara_first_older_page_alone_never_proves_date_exhaustion():
    current = task('camara_rio', 'camara_archive', url='https://camara.rio/comunicacao/noticias', date_from='2026-08-09', date_to='2026-08-09')
    first = discovery.discover(current, lambda _: Response(camara_page(['8 agosto 2026', '7 agosto 2026'])))
    assert first['outcome'] == 'continue'
    second = discovery.discover({**current,'cursor':first['next_cursor']}, lambda _: Response(camara_page(['6 agosto 2026', '5 agosto 2026'],start=20)))
    assert second['outcome'] == 'complete' and second['next_cursor'] is None


@pytest.mark.parametrize('partial_markup', [False, True])
def test_camara_unknown_or_unparsed_date_prevents_claim_of_complete_coverage(partial_markup):
    current = task('camara_rio', 'camara_archive', url='https://camara.rio/comunicacao/noticias', date_from='2026-08-09', date_to='2026-08-09')
    dates = ['12 agosto 2026', '10 agosto 2026'] if partial_markup else ['12 agosto 2026', 'data indisponível']
    extra = '<span class="catItemDateCreated">11 agosto 2026</span><h3 class="catItemTitle">Unrecognized item</h3>' if partial_markup else ''
    first = discovery.discover(current, lambda _: Response(camara_page(dates,extra_markup=extra)))
    assert first['next_cursor']['chronology_gap'] is True
    second = discovery.discover({**current,'cursor':first['next_cursor']}, lambda _: Response(camara_page(['8 agosto 2026', '7 agosto 2026'],start=20)))
    assert second['outcome'] == 'continue'
    third = discovery.discover({**current,'cursor':second['next_cursor']}, lambda _: Response(camara_page(['6 agosto 2026', '5 agosto 2026'],start=30)))
    assert third['outcome'] == 'gap' and third['gap_reason'] == 'archive_date_order_unproven'


def test_camara_boundary_order_reversal_is_an_explicit_gap():
    current = task('camara_rio', 'camara_archive', url='https://camara.rio/comunicacao/noticias', date_from='2026-09-01', date_to='2026-09-01')
    first = discovery.discover(current, lambda _: Response(camara_page(['10 agosto 2026', '7 agosto 2026'])))
    second = discovery.discover({**current,'cursor':first['next_cursor']}, lambda _: Response(camara_page(['9 agosto 2026', '6 agosto 2026'],start=20)))
    assert second['outcome'] == 'gap' and second['gap_reason'] == 'archive_date_order_unproven'


def test_camara_legacy_cursor_must_observe_ordering_before_stopping_with_gap():
    current = task('camara_rio','camara_archive',url='https://camara.rio/comunicacao/noticias',date_from='2026-09-01',date_to='2026-09-01',cursor={'page':4,'url':'https://camara.rio/comunicacao/noticias?limit=10&start=30'})
    first = discovery.discover(current,lambda _:Response(camara_page(['10 agosto 2026', '7 agosto 2026'],start=40)))
    assert first['outcome']=='continue' and first['next_cursor']['chronology_gap'] is True
    second = discovery.discover({**current,'cursor':first['next_cursor']},lambda _:Response(camara_page(['6 agosto 2026','5 agosto 2026'],start=50)))
    assert second['outcome']=='gap' and second['gap_reason']=='archive_date_order_unproven'


def test_camara_undated_archive_has_source_specific_visible_fifty_page_cap():
    current=task('camara_rio','camara_archive',url='https://camara.rio/comunicacao/noticias',cursor={'page':50,'url':'https://camara.rio/comunicacao/noticias?limit=10&start=490'})
    result=discovery.discover(current,lambda _:Response(camara_page(['data indisponível'],start=500)))
    assert result['outcome']=='gap' and result['gap_reason']=='archive_page_cap_or_cycle'
    assert len(result['candidates'])==1 and result['candidates'][0]['published_at']==''


def test_benchmark_database_guard_rejects_production_and_nonlocal_urls():
    from tools.political_scale_benchmark import guarded_database_url
    assert guarded_database_url("postgresql://user@127.0.0.1:55439/political_test_scale")
    for url in ("postgresql://user@127.0.0.1/production", "postgresql://user@db.example.com/political_test_scale", "sqlite:///test"):
        with pytest.raises(ValueError):
            guarded_database_url(url)


def test_publisher_cleanup_uses_later_document_metadata():
    # og:url can follow canonical metadata. The O Dia cleanup must still remove
    # the related link and preserve the genuine paragraph following it.
    raw = '''<link rel="canonical" href="https://example.com/story">
    <meta property="og:url" content="https://odia.ig.com.br/politica/story.html">
    <article><div class="texto">LEIA MAIS: <a href="/another-story">Unrelated headline</a>
    Later editorial paragraph remains intact.</div></article>'''
    body = discovery.extract_article(raw)["full_text"]
    assert "Unrelated headline" not in body
    assert "LEIA MAIS" not in body
    assert "Later editorial paragraph remains intact." in body
