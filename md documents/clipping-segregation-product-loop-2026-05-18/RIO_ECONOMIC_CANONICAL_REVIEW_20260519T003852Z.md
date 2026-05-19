# Rio Economic Canonical Review - 10 Row Pass

_Created 2026-05-18 by Atlas/Codex._

This reviews canonical URL/date evidence for the first 10 rows of:

```text
data/reports/rio_economic_dry_run_20260519T000719Z.json
```

Generated artifacts:

```text
data/reports/rio_economic_canonical_review_20260519T003852Z.json
data/reports/rio_economic_canonical_review_20260519T003852Z.csv
data/reports/rio_economic_canonical_review_20260519T003852Z.md
```

The helper did not store article bodies and did not write production DB,
assets payloads, or `data/targets.json`.

## Result Summary

```text
rows_checked=10
same_day=8
canonical_date_missing=1
date_mismatch=1
stores_article_body=false
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

## Blocking Rows

| Row | Status | Issue | Loop Decision |
| --- | --- | --- | --- |
| 1 | canonical_date_missing | The canonical page did not expose a usable published date. | Keep blocked for automated production use unless manually accepted. |
| 5 | date_mismatch | Google News date was 2026-05-03, canonical page date was 2025-04-08. | Treat as stale/recirculated date risk; do not count in current-period indicator without manual override. |

## Useful Rows

Rows 2, 3, 4, 6, 7, 8, 9, and 10 had canonical dates on the same day as the
Google News date. This supports using the canonical helper as a production gate
before adding Rio economic items to any indicator, weekly brief, or dashboard.

## Methodology Implication

The Rio indicator needs a date-quality field before production ingestion:

```text
canonical_date_status=same_day|near_date|date_mismatch|canonical_date_missing|fetch_error
```

Only `same_day` and carefully reviewed `near_date` rows should count toward a
current-period economic signal. `date_mismatch` and `canonical_date_missing`
rows may remain research notes but should not affect counts, charts, or paid
client summaries until manually approved.
