# Rio Economic Manual Approval Sidecar Report - 20260519T020159Z

_Created 2026-05-18 by Atlas/Codex._

This report regenerates the full Rio v4 topic report with an explicit manual
approval sidecar. It does not promote any row; it makes the default approval
state machine visible.

## Source Artifacts

```text
data/reports/rio_economic_clustered_review_20260519T004653Z.json
data/reports/rio_economic_canonical_review_20260519T013449Z.json
data/reports/rio_economic_canonical_review_20260519T014441Z.json
data/reports/rio_economic_manual_approvals_v0.json
```

Generated:

```text
data/reports/rio_economic_topic_report_20260519T020159Z.json
data/reports/rio_economic_topic_report_20260519T020159Z.csv
data/reports/rio_economic_topic_report_20260519T020159Z.md
```

## Result

```text
story_count=25
article_count=31
canonical_rows_checked=31
count_current_period=17
manual_review_before_counting=1
research_only=7
target_row_approved=false
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

Manual approval status counts:

```text
not_required=17
not_reviewed=8
```

## Meaning

The sidecar creates an auditable place for future human approvals. In this
version, every non-automatic row remains `not_reviewed`, so the automatic
indicator count remains 17 current-period stories.

No model should promote a row by editing only generated report output. A
promotion must be made in `rio_economic_manual_approvals_v0.json` or a future
operator-owned approval artifact, then the report must be regenerated.
