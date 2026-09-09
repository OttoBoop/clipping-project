import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest

from web_app import political_diario_archive as archive
from web_app import political_discovery as discovery

FIXTURES = Path(__file__).parent / "fixtures" / "diario_archive"


def response(text, status=200, headers=None):
    return SimpleNamespace(text=text, status_code=status, headers=headers or {})


def task(**changes):
    return {"source_key": "diario_do_rio", "strategy": "diario_archive", "url": archive.ARCHIVE_URL,
            "date_from": "2026-06-01", "date_to": "2026-09-09", "cursor": {"page": 1}, **changes}


def page(rows, *, initial=False, section="90"):
    cards = "".join(
        f'<div class="td_module_1 td_module_wrap clearfix"><h3 class="entry-title td-module-title"><a href="/regional-news-service-{key}/index.html">Serviço regional {key}</a></h3>'
        + (f'<time class="entry-date updated td-module-date" datetime="{day}">{day}</time>' if day else "")
        + '</div>' for key, day in rows)
    if initial:
        return '<div class="td-ss-main-content">' + cards + f'<a class="ddr-loadmore ajax-load-more" data-type="listao" data-sesit="{section}" data-page="2">Mostrar Mais</a></div>'
    return cards + archive.EMPTY_MARKER


def run(current, raw):
    return discovery.discover(current, lambda _: response(raw))


def continuation(page_number, previous="2026-06-23"):
    return {"version": 1, "page": page_number, "section_id": "90", "page_size": 10,
            "seen_pages": [hashlib.sha256(str(n).encode()).hexdigest() for n in range(page_number - 1)],
            "previous_oldest": previous, "ordered_pages": page_number - 1, "older_pages": 0,
            "unknown_dates": 0, "parse_gaps": 0, "chronology_gap": False}


def test_builds_one_shared_full_window_task_without_removing_google_or_sitemap():
    targets = [{"key": str(n), "display_name": f"Pessoa {n}"} for n in range(24)]
    planned = discovery.build_tasks(targets, "2026-06-01", "2026-09-09", ["diario_do_rio"])
    direct = [row for row in planned if row["strategy"] == "diario_archive"]
    assert len(direct) == 1
    assert direct[0]["target_ids"] == [row["key"] for row in targets]
    assert (direct[0]["date_from"], direct[0]["date_to"]) == ("2026-06-01", "2026-09-09")
    assert direct[0]["url"] == archive.ARCHIVE_URL and "query" not in direct[0]
    assert {row["strategy"] for row in planned} == {"diario_archive", "sitemap", "google_news"}
    assert next(s for s in discovery.load_sources() if s["key"] == "diario_do_rio")["archive_max_pages"] == 1000


def test_captured_initial_and_public_continuation_keep_all_ten_untargeted_cards():
    first_html = (FIXTURES / "initial-primary.html").read_text()
    # A same-format sidebar must never become a primary archive candidate.
    first = run(task(), first_html + '<aside>' + page([("sidebar", "2026-09-09")]) + '</aside>')
    assert first["raw_count"] == len(first["candidates"]) == 10
    assert first["outcome"] == "continue" and first["next_cursor"]["page"] == 2
    assert all(row["published_at"] == "" for row in first["candidates"])
    assert all(row["metadata"]["archive_card_day"] == "2026-09-09" for row in first["candidates"])
    assert "ancelotti" in first["candidates"][0]["url"]  # No political/name/title gate.
    calls = []
    def fetch(url):
        calls.append(url)
        return response((FIXTURES / "page2.html").read_text())
    second = discovery.discover(task(cursor=first["next_cursor"]), fetch)
    assert len(calls) == 1
    assert urlparse(calls[0]).path == "/index.php"
    assert parse_qs(urlparse(calls[0]).query) == {"id": ["/readMore.php"], "cd_sesit": ["90"], "p": ["2"]}
    assert second["raw_count"] == len(second["candidates"]) == 10
    assert not {r["url"] for r in first["candidates"]} & {r["url"] for r in second["candidates"]}
    assert second["next_cursor"]["page"] == 3 and len(second["next_cursor"]["seen_pages"]) == 2


def test_captured_june_cards_preserve_migrated_urls_and_never_invent_publication_time():
    raw = (FIXTURES / "page500.html").read_text()
    result = run(task(cursor=continuation(500)), raw)
    assert result["raw_count"] == len(result["candidates"]) == 10
    assert all(r["url"].endswith("/index.html") for r in result["candidates"])
    assert all(r["published_at"] == "" for r in result["candidates"])
    assert all(r["metadata"]["archive_card_day"] == "2026-06-22" and r["metadata"]["needs_date_review"] for r in result["candidates"])
    assert result["next_cursor"]["previous_oldest"] == "2026-06-22"
    assert result["outcome"] == "continue"  # Marker is also in nonempty fragments.


def test_window_filters_hints_without_stopping_scan_before_older_pages():
    first = run(task(date_from="2026-08-09", date_to="2026-08-09"), (FIXTURES / "initial-primary.html").read_text())
    assert first["candidates"] == [] and first["raw_count"] == 10
    assert first["outcome"] == "continue" and first["next_cursor"]["page"] == 2


def test_runtime_public_section_parameter_is_not_hardcoded():
    first = run(task(), page([(1, "2026-06-22")], initial=True, section="91"))
    calls = []
    def fetch(url):
        calls.append(url)
        return response(page([(2, "2026-06-21")]))
    discovery.discover(task(cursor=first["next_cursor"]), fetch)
    assert parse_qs(urlparse(calls[0]).query)["cd_sesit"] == ["91"]


def test_date_cutoff_needs_two_consecutive_fully_older_pages_and_complete_ordering():
    first = run(task(), page([(1, "2026-06-02")], initial=True))
    second = run(task(cursor=first["next_cursor"]), page([(2, "2026-05-31")]))
    assert second["outcome"] == "continue" and second["next_cursor"]["older_pages"] == 1
    third = run(task(cursor=second["next_cursor"]), page([(3, "2026-05-30")]))
    assert third["outcome"] == "complete" and third["candidates"] == []
    assert third["next_cursor"]["page"] == 4 and third["next_cursor"]["older_pages"] == 2


@pytest.mark.parametrize("missing_day", [None, "2026-99-09", "not a date"])
def test_unknown_days_remain_fetchable_and_prevent_false_date_exhaustion(missing_day):
    first = run(task(), page([(1, missing_day)], initial=True))
    assert len(first["candidates"]) == 1 and first["candidates"][0]["published_at"] == ""
    assert first["candidates"][0]["metadata"]["archive_card_day"] == ""
    second = run(task(cursor=first["next_cursor"]), page([(2, "2026-05-31")]))
    third = run(task(cursor=second["next_cursor"]), page([(3, "2026-05-30")]))
    assert third["outcome"] == "continue"
    assert "unknown_card_dates:1" in third["gap_reason"]
    end = run(task(cursor=third["next_cursor"]), " \n" + archive.EMPTY_MARKER)
    assert end["outcome"] == "gap" and "unknown_card_dates:1" in end["gap_reason"]


def test_order_reversal_stays_visible_after_later_ordered_older_pages():
    first = run(task(), page([(1, "2026-06-02")], initial=True))
    second = run(task(cursor=first["next_cursor"]), page([(2, "2026-06-03")]))
    third = run(task(cursor=second["next_cursor"]), page([(3, "2026-05-31")]))
    fourth = run(task(cursor=third["next_cursor"]), page([(4, "2026-05-30")]))
    assert fourth["outcome"] == "continue" and "chronology_unproven" in fourth["gap_reason"]


def test_malformed_or_external_card_has_visible_gap_and_never_fetches_other_host():
    raw = page([(1, "2026-06-22"), (2, "2026-06-22")], initial=True).replace('/regional-news-service-2/index.html', 'https://other.example/story.html')
    first = run(task(), raw)
    assert len(first["candidates"]) == 1 and first["raw_count"] == 2
    assert first["next_cursor"]["parse_gaps"] == 1 and "unparsed_cards:1" in first["gap_reason"]
    assert run(task(cursor=first["next_cursor"]), archive.EMPTY_MARKER)["outcome"] == "gap"


def test_repeated_page_is_a_gap_without_cursor_advance_or_input_mutation():
    first = run(task(), page([(1, "2026-06-22")], initial=True))
    current = task(cursor=first["next_cursor"])
    original = copy.deepcopy(current)
    result = run(current, page([(1, "2026-06-22")]))
    assert result["outcome"] == "gap" and result["gap_reason"] == "diario_archive_repeated_page"
    assert result["next_cursor"] is None and current == original


def test_retry_from_same_checkpoint_is_deterministic_and_does_not_mutate_cursor():
    first = run(task(), page([(1, "2026-06-22")], initial=True))
    current = task(cursor=first["next_cursor"])
    original = copy.deepcopy(current)
    assert run(current, page([(2, "2026-06-21")])) == run(current, page([(2, "2026-06-21")]))
    assert current == original


def test_http_429_uses_shared_fetch_error_and_keeps_checkpoint():
    first = run(task(), page([(1, "2026-06-22")], initial=True))
    current = task(cursor=first["next_cursor"])
    original = copy.deepcopy(current)
    with pytest.raises(discovery.DiscoveryError) as caught:
        discovery.discover(current, lambda _: response("rate limited", 429, {"Retry-After": "120"}))
    assert caught.value.retryable and caught.value.status_code == 429 and caught.value.retry_after == 120
    assert current == original


@pytest.mark.parametrize("raw", ["", "<html>Login required</html>", "<!-- PORTAL:FINISH -->extra"])
def test_blank_or_unrecognized_fragment_never_proves_exhaustion(raw):
    first = run(task(), page([(1, "2026-06-22")], initial=True))
    result = run(task(cursor=first["next_cursor"]), raw)
    assert result["outcome"] == "gap"


def test_exact_empty_fragment_finishes_an_ordered_scan():
    first = run(task(), page([(1, "2026-06-22")], initial=True))
    result = run(task(cursor=first["next_cursor"]), " \n" + archive.EMPTY_MARKER + " \n")
    assert result["outcome"] == "complete" and result["raw_count"] == 0


def test_1000_page_cap_is_explicit_preserves_final_candidates_and_evidence():
    result = run(task(cursor=continuation(1000)), (FIXTURES / "page500.html").read_text())
    assert result["outcome"] == "gap" and result["gap_reason"] == "diario_archive_page_cap"
    assert len(result["candidates"]) == 10 and len(result["next_cursor"]["seen_pages"]) == 1000


@pytest.mark.parametrize("cursor", [{"page": 2}, {"page": 1001}, {"page": "2"}, {"page": -1}])
def test_unproven_or_out_of_bounds_resume_never_issues_request(cursor):
    calls = []
    result = discovery.discover(task(cursor=cursor), lambda url: calls.append(url))
    assert calls == [] and result["gap_reason"] == "diario_archive_invalid_cursor"


@pytest.mark.parametrize("url", ["https://other.example/ultimas-noticias", "https://www.diariodorio.com/wp-json/wp/v2/posts", "https://www.diariodorio.com/ultimas-noticias?guess=1"])
def test_only_verified_public_archive_entry_is_allowed(url):
    calls = []
    result = discovery.discover(task(url=url), lambda target: calls.append(target))
    assert not calls and result["gap_reason"] == "diario_archive_unrecognized_public_url"


def test_changed_public_button_or_page_size_is_an_explicit_gap():
    result = run(task(), page([(1, "2026-06-22")], initial=True).replace('data-type="listao"', 'data-type="unknown"'))
    assert result["gap_reason"] == "diario_archive_public_button_changed"
    first = run(task(), page([(1, "2026-06-22")], initial=True))
    result = run(task(cursor=first["next_cursor"]), page([(2, "2026-06-21"), (3, "2026-06-21")]))
    assert result["gap_reason"] == "diario_archive_page_size_changed" and len(result["candidates"]) == 2


def test_captured_fixtures_match_recorded_provenance_hashes():
    provenance = json.loads((FIXTURES / "provenance.json").read_text())
    for name, info in provenance["files"].items():
        assert hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest() == info["sha256"]
