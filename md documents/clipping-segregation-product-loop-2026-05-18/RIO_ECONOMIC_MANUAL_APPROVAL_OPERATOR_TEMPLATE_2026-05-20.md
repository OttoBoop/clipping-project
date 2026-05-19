# Rio Economic Manual Approval Operator Template - 2026-05-20

_Created by Atlas/Codex during the segregation product loop._

This is an operator artifact, not an approval. It exists so a future review of
the eight non-automatic Rio stories can be recorded in the sidecar without
turning a model guess into an indicator count.

## Non-Negotiable Rule

Do not count a Rio story unless all of these are true:

```text
the row exists in data/reports/rio_economic_manual_approvals_v0.json
manual_approval_status is approved_current_period
decision is count_current_period
reviewer is filled
reviewed_at is filled
canonical_url or source_url is filled
observed_source_date or date_trust_reason is filled
rationale is filled
tools/rio_economic_build_topic_report.py regenerates without error
tools/rio_economic_manual_approval_check.py returns ok=true
the scoped Rio endpoint stays admin/rio_economico-only after deploy
```

If any part is missing, keep the story as `not_reviewed` or mark it
`rejected_research_only`.

## Sidecar Fields

Each manual-review row must keep these keys:

```text
representative_row
manual_approval_status
decision
reviewer
reviewed_at
canonical_url
observed_source_date
date_trust_reason
rationale
```

Allowed statuses:

```text
not_reviewed
approved_current_period
rejected_research_only
```

`not_required` is produced by the report builder for automatic same-day rows.
It should not be added casually to the manual sidecar.

## Decision Flow

1. Open the source URL named in `RIO_ECONOMIC_MANUAL_REVIEW_QUEUE_2026-05-18.md`.
2. Confirm the article is about city-of-Rio economic signal, not only broader
   state/national context.
3. Record the canonical/source URL actually reviewed.
4. Record the source date, or write a short date-trust reason if the source
   explains why the Google News date should be accepted.
5. Choose one of:

```text
approved_current_period + decision=count_current_period
rejected_research_only + decision=keep_research_only
not_reviewed + original default decision
```

6. Regenerate the topic report and run the manual approval checker.
7. Deploy only after the checker passes and the Rio panel remains read-only.

## Row 11 Template

Row 11 is currently the first review candidate because it is the only
`near_date` story. This block shows the required shape only; it is not an
approval.

```json
{
  "representative_row": 11,
  "manual_approval_status": "not_reviewed",
  "decision": "manual_review_before_counting",
  "reviewer": "",
  "reviewed_at": "",
  "canonical_url": "",
  "observed_source_date": "",
  "date_trust_reason": "",
  "rationale": "near_date"
}
```

To approve row 11 later, change only after human review:

```json
{
  "representative_row": 11,
  "manual_approval_status": "approved_current_period",
  "decision": "count_current_period",
  "reviewer": "operator-name",
  "reviewed_at": "YYYY-MM-DDTHH:MM:SSZ",
  "canonical_url": "https://source.example/article",
  "observed_source_date": "YYYY-MM-DD",
  "date_trust_reason": "",
  "rationale": "short human reason for accepting the source/date evidence"
}
```

## Guard Command

Run before treating the Rio report as updated:

```bash
python3 -B tools/rio_economic_manual_approval_check.py
```

Expected current state:

```text
ok=true
sidecar_rows=[1, 5, 11, 15, 19, 22, 25, 26]
manual_approval_status_counts:
  not_required=17
  not_reviewed=8
indicator_policy_counts:
  count_current_period=17
  manual_review_before_counting=1
  research_only=7
target_row_approved=false
```

## Product Boundary

This template does not authorize:

```text
adding a production rio_economico target row
showing approval buttons in the Rio UI
publishing the eight pending rows as counted signal
using static exports as the private Rio product surface
```
