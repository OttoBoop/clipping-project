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
    assert stories[1]["article_count"] == 1
    assert stories[1]["date_quality_status"] == "not_checked"
    assert stories[1]["date_quality_policy"] == "canonical_check_required"


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
