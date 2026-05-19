# Rio Economic Date Quality Policy

_Created 2026-05-18 by Atlas/Codex._

This policy exists because Google News can surface old or recirculated articles
as if they were current. The Rio economic indicator must not count stale rows
as current-period economic signal.

## Statuses

```text
same_day
near_date
date_mismatch
canonical_date_missing
original_date_missing
unresolved_google_url
fetch_error
missing_url
```

## Counting Rule

Rows may count toward a current-period Rio economic indicator only when:

```text
canonical_date_status=same_day
```

or, after manual review:

```text
canonical_date_status=near_date
```

Rows with these statuses are research-only until manually approved:

```text
date_mismatch
canonical_date_missing
original_date_missing
unresolved_google_url
fetch_error
missing_url
```

## Why This Matters

The 10-row canonical review found:

```text
same_day=8
canonical_date_missing=1
date_mismatch=1
```

The `date_mismatch` row had a Google News date in 2026 but a canonical article
date in 2025. Without this gate, the future indicator could overstate current
tourism/event activity.

## Implementation Note

`tools/rio_economic_canonical_review.py` now records:

```text
date_quality_pass_statuses
date_quality_eligible_rows
status_counts
```

These fields are review evidence only. They do not write to the production DB,
asset payload, or `data/targets.json`.
