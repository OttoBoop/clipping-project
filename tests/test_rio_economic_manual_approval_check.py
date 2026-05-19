from __future__ import annotations

from tools import rio_economic_manual_approval_check as check


BASE_REPORT = {
    "meta": {
        "writes_production_db": False,
        "writes_assets_payload": False,
        "writes_targets_json": False,
        "target_row_approved": False,
        "manual_approval_status_counts": {
            "not_required": 1,
            "not_reviewed": 2,
        },
        "indicator_policy_counts": {
            "count_current_period": 1,
            "manual_review_before_counting": 1,
            "research_only": 1,
        },
    },
    "stories": [
        {
            "representative_row": 2,
            "date_quality_policy": "count_current_period",
            "manual_approval_status": "not_required",
            "indicator_policy": "count_current_period",
        },
        {
            "representative_row": 11,
            "date_quality_policy": "manual_review_before_counting",
            "manual_approval_status": "not_reviewed",
            "indicator_policy": "manual_review_before_counting",
        },
        {
            "representative_row": 15,
            "date_quality_policy": "research_only",
            "manual_approval_status": "not_reviewed",
            "indicator_policy": "research_only",
        },
    ],
}

BASE_SIDECAR = {
    "meta": {"approval_status": "template_only_no_promotions"},
    "approvals": [
        {
            "representative_row": 11,
            "manual_approval_status": "not_reviewed",
            "decision": "manual_review_before_counting",
            "reviewer": "",
            "reviewed_at": "",
            "canonical_url": "",
            "observed_source_date": "",
            "date_trust_reason": "",
            "rationale": "near_date",
        },
        {
            "representative_row": 15,
            "manual_approval_status": "not_reviewed",
            "decision": "keep_research_only",
            "reviewer": "",
            "reviewed_at": "",
            "canonical_url": "",
            "observed_source_date": "",
            "date_trust_reason": "",
            "rationale": "fetch_error",
        },
    ],
}

BASE_QUEUE = """
## Current Decision

```text
approved_promotions=0
rows_remaining_not_reviewed=2
target_row_approved=false
```
"""


def test_current_template_queue_state_passes_without_promotions():
    result = check.validate_artifacts(BASE_SIDECAR, BASE_REPORT, BASE_QUEUE)

    assert result["ok"] is True
    assert result["sidecar_rows"] == [11, 15]
    assert result["reviewable_rows"] == [11, 15]
    assert result["manual_approval_status_counts"]["not_reviewed"] == 2


def test_sidecar_must_match_non_automatic_report_rows():
    sidecar = dict(BASE_SIDECAR)
    sidecar["approvals"] = BASE_SIDECAR["approvals"][:1]

    result = check.validate_artifacts(sidecar, BASE_REPORT, BASE_QUEUE)

    assert result["ok"] is False
    assert "sidecar rows must match non-automatic report rows" in result["failures"][0]


def test_queue_counts_must_match_report_status_counts():
    queue = BASE_QUEUE.replace("rows_remaining_not_reviewed=2", "rows_remaining_not_reviewed=1")

    result = check.validate_artifacts(BASE_SIDECAR, BASE_REPORT, queue)

    assert result["ok"] is False
    assert any("queue rows_remaining_not_reviewed mismatch" in failure for failure in result["failures"])


def test_approved_current_period_requires_source_and_date_evidence():
    sidecar = {
        "meta": {"approval_status": "reviewed"},
        "approvals": [
            {
                **BASE_SIDECAR["approvals"][0],
                "manual_approval_status": "approved_current_period",
                "decision": "count_current_period",
                "reviewer": "operator",
                "reviewed_at": "2026-05-20T00:00:00Z",
                "rationale": "accepted near-date source",
            },
            BASE_SIDECAR["approvals"][1],
        ],
    }

    result = check.validate_artifacts(sidecar, BASE_REPORT, BASE_QUEUE)

    assert result["ok"] is False
    assert "row 11 approved_current_period missing source/canonical URL" in result["failures"]
    assert "row 11 approved_current_period missing observed date evidence" in result["failures"]


def test_repository_rio_manual_approval_artifacts_still_match():
    sidecar = check.load_json(check.DEFAULT_SIDECAR)
    report = check.load_json(check.DEFAULT_REPORT)
    queue = check.DEFAULT_QUEUE_DOC.read_text(encoding="utf-8")

    result = check.validate_artifacts(sidecar, report, queue)

    assert result["ok"] is True
    assert result["sidecar_rows"] == [1, 5, 11, 15, 19, 22, 25, 26]
    assert result["manual_approval_status_counts"] == {
        "not_required": 17,
        "not_reviewed": 8,
    }
    assert result["indicator_policy_counts"] == {
        "count_current_period": 17,
        "manual_review_before_counting": 1,
        "research_only": 7,
    }
