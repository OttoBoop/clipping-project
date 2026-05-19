from __future__ import annotations

from tools import rio_economic_build_topic_report as topic_report


def test_build_stories_collapses_duplicate_clusters_and_preserves_unchecked_rows():
    clustered = {
        "rows": [
            {
                "title": "A",
                "url": "https://example.com/a",
                "dimension": "tourism_events",
                "source": "Fonte A",
                "cluster_key": "cluster_a",
                "primary_dimension": "tourism_events",
                "duplicate_of": "",
            },
            {
                "title": "B",
                "url": "https://example.com/b",
                "dimension": "economic_development",
                "source": "Fonte B",
                "cluster_key": "cluster_a",
                "primary_dimension": "tourism_events",
                "duplicate_of": "row:1",
            },
            {
                "title": "C",
                "url": "https://example.com/c",
                "dimension": "jobs_income",
                "source": "Fonte C",
            },
        ]
    }
    canonical = {
        "rows": [
            {"row": 1, "status": "same_day", "final_url": "https://example.com/a"},
        ]
    }

    stories = topic_report.build_stories(clustered, canonical)

    assert len(stories) == 2
    assert stories[0]["article_count"] == 2
    assert stories[0]["member_rows"] == [1, 2]
    assert stories[0]["date_quality_policy"] == "count_current_period"
    assert stories[0]["date_quality_source_row"] == 1
    assert stories[0]["date_quality_evidence_rows"] == [1]
    assert stories[1]["article_count"] == 1
    assert stories[1]["date_quality_status"] == "not_checked"
    assert stories[1]["date_quality_policy"] == "canonical_check_required"


def test_build_stories_uses_cluster_member_canonical_pass_when_representative_fails():
    clustered = {
        "rows": [
            {
                "title": "A",
                "url": "https://example.com/a",
                "dimension": "construction_real_estate",
                "source": "Fonte A",
                "cluster_key": "cluster_a",
                "primary_dimension": "construction_real_estate",
                "duplicate_of": "",
            },
            {
                "title": "B",
                "url": "https://example.com/b",
                "dimension": "construction_real_estate",
                "source": "Fonte B",
                "cluster_key": "cluster_a",
                "primary_dimension": "construction_real_estate",
                "duplicate_of": "row:1",
            },
        ]
    }
    canonical = {
        "rows": [
            {"row": 1, "status": "fetch_error", "final_url": ""},
            {"row": 2, "status": "same_day", "final_url": "https://example.com/b"},
        ]
    }

    stories = topic_report.build_stories(clustered, canonical)

    assert len(stories) == 1
    assert stories[0]["date_quality_status"] == "same_day"
    assert stories[0]["date_quality_policy"] == "count_current_period"
    assert stories[0]["date_quality_source_row"] == 2
    assert stories[0]["date_quality_evidence_rows"] == [1, 2]
    assert stories[0]["date_quality_evidence_statuses"] == {
        "1": "fetch_error",
        "2": "same_day",
    }


def test_summarize_counts_story_article_dimension_and_date_policy():
    stories = [
        {
            "article_count": 2,
            "primary_dimension": "tourism_events",
            "date_quality_status": "same_day",
            "date_quality_policy": "count_current_period",
        },
        {
            "article_count": 1,
            "primary_dimension": "jobs_income",
            "date_quality_status": "canonical_date_missing",
            "date_quality_policy": "research_only",
        },
    ]

    summary = topic_report.summarize(stories, {"row_count": 3, "cluster_count": 1})

    assert summary["story_count"] == 2
    assert summary["article_count"] == 3
    assert summary["source_row_count"] == 3
    assert summary["source_cluster_count"] == 1
    assert summary["date_quality_policy_counts"] == {
        "count_current_period": 1,
        "research_only": 1,
    }
    assert summary["primary_dimension_story_counts"] == {
        "jobs_income": 1,
        "tourism_events": 1,
    }


def test_merge_canonical_payloads_combines_rows_and_rows_checked():
    merged = topic_report.merge_canonical_payloads(
        [
            {
                "meta": {"rows_checked": 2, "input_report": "sample-a.json"},
                "rows": [
                    {"row": 1, "status": "same_day"},
                    {"row": 2, "status": "fetch_error"},
                ],
            },
            {
                "meta": {"rows_checked": 1, "input_report": "sample-a.json"},
                "rows": [
                    {"row": 2, "status": "same_day"},
                    {"row": 3, "status": "near_date"},
                ],
            },
        ]
    )

    assert merged["meta"]["rows_checked"] == 3
    assert [row["row"] for row in merged["rows"]] == [1, 2, 3]
    assert [row["status"] for row in merged["rows"]] == ["same_day", "same_day", "near_date"]
