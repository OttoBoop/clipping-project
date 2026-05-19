from __future__ import annotations

from tools import rio_economic_apply_cluster_annotations as clusters


def test_build_annotation_map_marks_representative_and_duplicates():
    rows = [
        {"url": "https://example.com/a"},
        {"url": "https://example.com/b"},
        {"url": "https://example.com/c"},
    ]
    groups = [
        {
            "rows": [1, 3],
            "cluster_key": "sample_cluster",
            "cluster_label": "Sample cluster",
            "primary_dimension": "commerce_services",
            "secondary_dimensions": ["municipal_finance", "tourism_events"],
            "representative_row": 1,
        }
    ]

    annotation_map = clusters.build_annotation_map(rows, groups)

    assert annotation_map[1]["duplicate_of"] == ""
    assert annotation_map[1]["representative_url"] == "https://example.com/a"
    assert annotation_map[3]["duplicate_of"] == "row:1"
    assert annotation_map[3]["secondary_dimensions"] == "municipal_finance, tourism_events"


def test_annotated_rows_preserves_unclustered_rows():
    rows = [{"title": "A"}, {"title": "B"}]
    annotated = clusters.annotated_rows(rows, {2: {"cluster_key": "cluster_b"}})

    assert annotated[0]["cluster_key"] == ""
    assert annotated[0]["title"] == "A"
    assert annotated[1]["cluster_key"] == "cluster_b"
    assert annotated[1]["title"] == "B"
