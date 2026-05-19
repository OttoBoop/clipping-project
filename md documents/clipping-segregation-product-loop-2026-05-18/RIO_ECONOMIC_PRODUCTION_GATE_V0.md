# Rio Economic Production Gate V0

_Created 2026-05-18 by Atlas/Codex._

This is the gate before any production `rio_economico` target row is added to
`data/targets.json`.

## Current Decision

```text
production rio_economico target row approved=false
```

Reason: the Rio economic methodology is promising, but production ingestion
must not contaminate Flavio, Shakira, or future paid-client surfaces.

## Gate 1 - Live Segregation Proof

Required immediately before adding a target row:

```text
Render logged-out payload/API gate still returns 401
rio_economico viewer still exists as isolated profile
rio_economico profile has no Flavio/Shakira/client leakage
Flavio/Shakira scoped payloads still exclude Rio economic rows after first run
```

Current state:

```text
rio_economico profile exists
data/targets.json row absent
live logged-out privacy gate repeatedly passes
authenticated positive proof is blocked in this shell by missing viewer passwords
```

## Gate 2 - Query Quality

Required:

```text
at least 30 reviewed candidate articles
known hotel-jobs and state-Fazenda false positives mitigated
no broad placeholder term such as "Rio Economico"
no single query family dominates the useful sample
```

Current evidence:

```text
v4 sample row_count=31
title-level false_positive=0
useful_or_unclear_before_clustering=25/31
```

## Gate 3 - Date Quality

Rows may count toward a current-period indicator only when:

```text
canonical_date_status=same_day
```

Rows may count after manual approval when:

```text
canonical_date_status=near_date
```

Rows remain research-only when:

```text
date_mismatch
canonical_date_missing
original_date_missing
unresolved_google_url
fetch_error
missing_url
```

Current evidence:

```text
20-row canonical pass: same_day=14, near_date=1, canonical_date_missing=2, date_mismatch=1, fetch_error=2
date_quality_eligible_rows=15
rows 21-31 canonical pass: same_day=8, canonical_date_missing=2, fetch_error=1
full v4 topic report: canonical_rows_checked=31, count_current_period=17, manual_review_before_counting=1, research_only=7
```

## Gate 4 - Cluster Counting

Production Rio views must distinguish:

```text
article_count
story_count
```

Current evidence:

```text
v4 cluster annotation: row_count=31, cluster_count=3, clustered_row_count=9
topic report: article_count=31, story_count=25
extended topic report: count_current_period=11, manual_review_before_counting=1, research_only=4, canonical_check_required=9
full topic report: count_current_period=17, manual_review_before_counting=1, research_only=7, canonical_check_required=0
```

Rows 4/30/31, 8/9/10, and 16/17/18 must not inflate story counts.
The topic report must evaluate date-quality evidence across all rows in a
reviewed cluster, not only the representative row; row 16/17/18 proves why.

## Gate 5 - Source/Body Review

Required before target-row approval:

```text
body/source-reviewed sample covers all dimensions
known body/source false positives are mitigated
date-quality failures are either excluded or manually approved
duplicate clusters have representative story policy
```

Current evidence:

```text
v3 body/source pass reviewed 21 rows across 6 dimensions
v4 mitigated the known row 15 and row 27 false positives
```

## Gate 6 - First Production Run Shape

If approved later, the first production run must be narrow:

```text
add one explicit rio_economico target row only after fresh live scoping proof
use selected query/source families only
run narrow date window
check Flavio/Shakira/client payloads immediately after run
check raw texts for cross-profile leakage
log collection cost and operator time
```

Architecture decision:

```text
RIO_ECONOMIC_INGESTION_ARCHITECTURE_DECISION.md
plain data/targets.json target row is not safe enough for Rio economic monitoring
preferred first production shape is scoped topic/query report before normal dashboard ingestion
first topic-report artifact now exists and keeps target_row_approved=false
extended topic-report artifact now uses cluster-member date evidence and still keeps target_row_approved=false
full v4 topic-report artifact has canonical_rows_checked=31 and still keeps target_row_approved=false
scoped endpoint /api/reports/rio-economic-topic exists for admin/rio_economico only
manual approval policy v0 says only same_day auto-counts; near_date/research-only need logged human evidence
manual approval sidecar exists with not_required=17 and not_reviewed=8; it promotes no rows
manual review queue exists with approved_promotions=0 and rows_remaining_not_reviewed=8
Rio-only UI decision v0 exposes only a read-only panel backed by the scoped endpoint
manual approval validation now rejects unknown approval statuses and blocks approved_current_period without source/date evidence
latest topic report has indicator_policy_counts equal to the date-quality policy counts because approved_promotions=0
```

## Current Next Step

```text
do not add data/targets.json row yet
wait for latest deploys to become live
run fresh production scoping proof
keep the scoped Rio topic-report view read-only until approval writes exist end to end
verify /api/reports/rio-economic-topic on Render after deploy
if an operator reviews row 11 or any research-only row, update the sidecar and regenerate the topic report before any UI promotion
preserve the v4 query families/exclusions in a scoped topic pipeline, not a plain keyword target row
then decide whether the Rio methodology is ready for an operator-approved narrow first run
```
