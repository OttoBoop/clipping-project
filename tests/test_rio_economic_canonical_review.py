from __future__ import annotations

from tools import rio_economic_canonical_review


def test_date_status_classifies_same_near_mismatch_and_missing():
    assert (
        rio_economic_canonical_review.date_status(
            "2026-05-19T12:00:00+00:00",
            "2026-05-19T16:30:00+00:00",
            "https://example.com/a",
        )
        == "same_day"
    )
    assert (
        rio_economic_canonical_review.date_status(
            "2026-05-19T12:00:00+00:00",
            "2026-05-21T16:30:00+00:00",
            "https://example.com/b",
        )
        == "near_date"
    )
    assert (
        rio_economic_canonical_review.date_status(
            "2026-05-19T12:00:00+00:00",
            "2026-04-01T16:30:00+00:00",
            "https://example.com/c",
        )
        == "date_mismatch"
    )
    assert (
        rio_economic_canonical_review.date_status(
            "2026-05-19T12:00:00+00:00",
            "",
            "https://example.com/d",
        )
        == "canonical_date_missing"
    )


def test_status_summary_and_indicator_eligible_count():
    rows = [
        {"status": "same_day"},
        {"status": "same_day"},
        {"status": "near_date"},
        {"status": "date_mismatch"},
        {"status": "canonical_date_missing"},
    ]

    assert rio_economic_canonical_review.summarize_statuses(rows) == {
        "canonical_date_missing": 1,
        "date_mismatch": 1,
        "near_date": 1,
        "same_day": 2,
    }
    assert rio_economic_canonical_review.indicator_eligible_count(rows) == 3


def test_review_rows_preserves_original_row_numbers_with_start_row():
    rows = [
        {"url": "https://example.com/1", "published_at": "2026-05-01T00:00:00+00:00"},
        {"url": "https://example.com/2", "published_at": "2026-05-02T00:00:00+00:00"},
        {"url": "https://example.com/3", "published_at": "2026-05-03T00:00:00+00:00"},
    ]

    original_fetch = rio_economic_canonical_review.fetch_full_article_text

    def fake_fetch(url, *, request_timeout):
        day = url.rsplit("/", 1)[-1]
        return (
            url,
            "",
            "body text",
            f"title {day}",
            f"2026-05-0{day}T12:00:00+00:00",
        )

    try:
        rio_economic_canonical_review.fetch_full_article_text = fake_fetch
        reviewed = rio_economic_canonical_review.review_rows(
            rows,
            max_rows=2,
            request_timeout=1,
            start_row=2,
        )
    finally:
        rio_economic_canonical_review.fetch_full_article_text = original_fetch

    assert [row["row"] for row in reviewed] == [2, 3]
    assert [row["status"] for row in reviewed] == ["same_day", "same_day"]
