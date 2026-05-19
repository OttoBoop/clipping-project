# Rio Economic Manual Approval Policy V0

_Created 2026-05-18 by Atlas/Codex._

This policy prevents the Rio economic topic report from becoming a fake
indicator. A story can only move from review material into current-period
indicator counts when its date/source evidence is explicit.

## Count Rules

```text
same_day -> count_current_period
near_date -> manual_review_before_counting
date_mismatch -> research_only
canonical_date_missing -> research_only
fetch_error -> research_only
original_date_missing -> research_only
unresolved_google_url -> research_only
missing_url -> research_only
```

Manual approval can only promote `near_date` or `research_only` rows after an
operator records human evidence. A model must not silently promote these rows.

## Required Manual Evidence

To promote a row, the operator must record:

```text
reviewer
reviewed_at
story row
original Google News date
canonical/source URL
observed source date or reason date is trustworthy
promotion decision: count_current_period or keep_research_only
short rationale
```

The approval note must live in a committed review artifact or an operator log.
It must not live only in chat.

## V4 Rows Requiring Manual Or Research Treatment

From:

```text
data/reports/rio_economic_topic_report_20260519T014505Z.json
```

| Row | Policy | Status | Dimension | Decision |
| --- | --- | --- | --- | --- |
| 1 | research_only | canonical_date_missing | tourism_events | Keep research-only unless source date is manually verified. |
| 5 | research_only | date_mismatch | tourism_events | Keep research-only; canonical date is 2025 while Google News showed 2026. |
| 11 | manual_review_before_counting | near_date | jobs_income | May count only if operator accepts one-day date difference. |
| 15 | research_only | fetch_error | jobs_income | Keep research-only unless fetch succeeds or source date is manually verified. |
| 19 | research_only | canonical_date_missing | construction_real_estate | Keep research-only unless source date is manually verified. |
| 22 | research_only | fetch_error | municipal_finance | Keep research-only unless fetch succeeds or source date is manually verified. |
| 25 | research_only | canonical_date_missing | municipal_finance | Keep research-only unless source date is manually verified. |
| 26 | research_only | canonical_date_missing | municipal_finance | Keep research-only unless source date is manually verified. |

## Product Rule

For a paid client or public-facing Rio indicator:

- automatic count may say `17 current-period stories`;
- the report may separately say `1 pending manual review` and `7 research-only`;
- do not present `25 stories` as an economic signal count;
- do not merge research-only rows into charts, scores, or trend claims;
- do not add a production `rio_economico` target row because this policy exists.

## Next Implementation Step

Implemented sidecar/status scaffold:

```text
data/reports/rio_economic_manual_approvals_v0.json
data/reports/rio_economic_topic_report_20260519T020159Z.json
manual_approval_status_counts:
not_required=17
not_reviewed=8
```

Next implementation step: if an operator promotes a row, update the sidecar with
reviewer, reviewed_at, decision, and rationale before regenerating the report.
