#!/usr/bin/env python3
"""Validate Rio manual approval artifacts before any indicator promotion."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import rio_economic_build_topic_report as topic_report  # noqa: E402


LOOP_DOCS = PROJECT_ROOT / "md documents" / "clipping-segregation-product-loop-2026-05-18"
DEFAULT_SIDECAR = PROJECT_ROOT / "data" / "reports" / "rio_economic_manual_approvals_v0.json"
DEFAULT_REPORT = (
    PROJECT_ROOT / "data" / "reports" / "rio_economic_topic_report_20260519T142621Z.json"
)
DEFAULT_QUEUE_DOC = LOOP_DOCS / "RIO_ECONOMIC_MANUAL_REVIEW_QUEUE_2026-05-18.md"

REQUIRED_SIDECAR_FIELDS = {
    "representative_row",
    "manual_approval_status",
    "decision",
    "reviewer",
    "reviewed_at",
    "canonical_url",
    "observed_source_date",
    "date_trust_reason",
    "rationale",
}
SOURCE_FLAGS = ("writes_production_db", "writes_assets_payload", "writes_targets_json")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"expected true/false, got {value!r}")


def parse_current_decision(queue_text: str) -> dict[str, Any]:
    state: dict[str, Any] = {}
    for key, parser in (
        ("approved_promotions", int),
        ("rows_remaining_not_reviewed", int),
        ("target_row_approved", parse_bool),
    ):
        match = re.search(rf"^{key}=(.+)$", queue_text, flags=re.MULTILINE)
        if not match:
            raise ValueError(f"missing queue decision key: {key}")
        state[key] = parser(match.group(1).strip())
    return state


def story_rows(report_payload: dict[str, Any]) -> dict[int, dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    stories = report_payload.get("stories") or []
    if not isinstance(stories, list):
        raise ValueError("topic report must contain a stories list")
    for story in stories:
        if not isinstance(story, dict):
            continue
        try:
            representative_row = int(story.get("representative_row") or 0)
        except (TypeError, ValueError):
            representative_row = 0
        if representative_row > 0:
            rows[representative_row] = story
    return rows


def sidecar_rows(sidecar_payload: dict[str, Any]) -> dict[int, dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    approvals = sidecar_payload.get("approvals") or []
    if not isinstance(approvals, list):
        raise ValueError("manual approval sidecar must contain an approvals list")
    for approval in approvals:
        if not isinstance(approval, dict):
            continue
        try:
            representative_row = int(approval.get("representative_row") or 0)
        except (TypeError, ValueError):
            representative_row = 0
        if representative_row > 0:
            if representative_row in rows:
                raise ValueError(f"duplicate sidecar row: {representative_row}")
            rows[representative_row] = approval
    return rows


def counter_from_stories(stories: dict[int, dict[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(str(story.get(field) or "unknown") for story in stories.values())
    return dict(sorted(counts.items()))


def validate_sidecar_row(
    representative_row: int,
    story: dict[str, Any] | None,
    approval: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    missing_keys = sorted(REQUIRED_SIDECAR_FIELDS - set(approval))
    if missing_keys:
        failures.append(f"row {representative_row} missing sidecar field(s): {', '.join(missing_keys)}")

    status = topic_report.clean_text(approval.get("manual_approval_status"))
    if status not in topic_report.MANUAL_APPROVAL_STATUSES:
        failures.append(f"row {representative_row} has unknown manual_approval_status={status!r}")
        return failures

    decision = topic_report.clean_text(approval.get("decision"))
    if status == "approved_current_period":
        if story and story.get("date_quality_policy") == "count_current_period":
            failures.append(f"row {representative_row} approval is unnecessary for an automatic story")
        if decision != "count_current_period":
            failures.append(f"row {representative_row} approved_current_period must use decision=count_current_period")
        if not topic_report.clean_text(approval.get("reviewer")):
            failures.append(f"row {representative_row} approved_current_period missing reviewer")
        if not topic_report.clean_text(approval.get("reviewed_at")):
            failures.append(f"row {representative_row} approved_current_period missing reviewed_at")
        if not topic_report.clean_text(approval.get("rationale")):
            failures.append(f"row {representative_row} approved_current_period missing rationale")
        if not topic_report.manual_approval_evidence_url(approval):
            failures.append(f"row {representative_row} approved_current_period missing source/canonical URL")
        if not topic_report.manual_approval_date_evidence(approval):
            failures.append(f"row {representative_row} approved_current_period missing observed date evidence")
    elif status == "rejected_research_only":
        if decision != "keep_research_only":
            failures.append(f"row {representative_row} rejected_research_only must use decision=keep_research_only")
        if not topic_report.clean_text(approval.get("reviewer")):
            failures.append(f"row {representative_row} rejected_research_only missing reviewer")
        if not topic_report.clean_text(approval.get("reviewed_at")):
            failures.append(f"row {representative_row} rejected_research_only missing reviewed_at")
        if not topic_report.clean_text(approval.get("rationale")):
            failures.append(f"row {representative_row} rejected_research_only missing rationale")
    elif status == "not_reviewed" and decision == "count_current_period":
        failures.append(f"row {representative_row} not_reviewed cannot use decision=count_current_period")

    return failures


def validate_artifacts(
    sidecar_payload: dict[str, Any],
    report_payload: dict[str, Any],
    queue_text: str | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    meta = report_payload.get("meta") if isinstance(report_payload.get("meta"), dict) else {}
    sidecar_meta = sidecar_payload.get("meta") if isinstance(sidecar_payload.get("meta"), dict) else {}
    stories = story_rows(report_payload)
    approvals = sidecar_rows(sidecar_payload)

    for flag in SOURCE_FLAGS:
        if meta.get(flag) is not False:
            failures.append(f"topic report meta {flag} must be false")
    if meta.get("target_row_approved") is not False:
        failures.append("topic report target_row_approved must remain false")

    reviewable_rows = {
        row
        for row, story in stories.items()
        if story.get("date_quality_policy") != "count_current_period"
    }
    sidecar_row_set = set(approvals)
    if sidecar_row_set != reviewable_rows:
        failures.append(
            "sidecar rows must match non-automatic report rows: "
            f"sidecar={sorted(sidecar_row_set)} report={sorted(reviewable_rows)}"
        )

    for row, approval in approvals.items():
        failures.extend(validate_sidecar_row(row, stories.get(row), approval))

    expected_manual_counts = counter_from_stories(stories, "manual_approval_status")
    if meta.get("manual_approval_status_counts") != expected_manual_counts:
        failures.append(
            "manual_approval_status_counts mismatch: "
            f"meta={meta.get('manual_approval_status_counts')} actual={expected_manual_counts}"
        )

    expected_indicator_counts = counter_from_stories(stories, "indicator_policy")
    if meta.get("indicator_policy_counts") != expected_indicator_counts:
        failures.append(
            "indicator_policy_counts mismatch: "
            f"meta={meta.get('indicator_policy_counts')} actual={expected_indicator_counts}"
        )

    approved_count = expected_manual_counts.get("approved_current_period", 0)
    not_reviewed_count = expected_manual_counts.get("not_reviewed", 0)
    if sidecar_meta.get("approval_status") == "template_only_no_promotions" and approved_count:
        failures.append("sidecar meta still says template_only_no_promotions but approvals exist")

    queue_state = None
    if queue_text is not None:
        queue_state = parse_current_decision(queue_text)
        if queue_state["approved_promotions"] != approved_count:
            failures.append(
                "queue approved_promotions mismatch: "
                f"queue={queue_state['approved_promotions']} report={approved_count}"
            )
        if queue_state["rows_remaining_not_reviewed"] != not_reviewed_count:
            failures.append(
                "queue rows_remaining_not_reviewed mismatch: "
                f"queue={queue_state['rows_remaining_not_reviewed']} report={not_reviewed_count}"
            )
        if queue_state["target_row_approved"] != meta.get("target_row_approved"):
            failures.append(
                "queue target_row_approved mismatch: "
                f"queue={queue_state['target_row_approved']} report={meta.get('target_row_approved')}"
            )

    return {
        "ok": not failures,
        "story_count": len(stories),
        "sidecar_rows": sorted(sidecar_row_set),
        "reviewable_rows": sorted(reviewable_rows),
        "manual_approval_status_counts": expected_manual_counts,
        "indicator_policy_counts": expected_indicator_counts,
        "queue_state": queue_state,
        "target_row_approved": meta.get("target_row_approved"),
        "failures": failures,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Rio manual approval sidecar/report/queue artifacts.")
    parser.add_argument("--sidecar", type=Path, default=DEFAULT_SIDECAR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--queue-doc", type=Path, default=DEFAULT_QUEUE_DOC)
    parser.add_argument("--no-queue-doc", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    queue_text = None if args.no_queue_doc else args.queue_doc.read_text(encoding="utf-8")
    result = validate_artifacts(load_json(args.sidecar), load_json(args.report), queue_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
