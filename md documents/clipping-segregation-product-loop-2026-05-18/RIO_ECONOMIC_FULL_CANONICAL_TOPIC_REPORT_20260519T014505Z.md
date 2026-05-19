# Rio Economic Full Canonical Topic Report - 20260519T014505Z

_Created 2026-05-18 by Atlas/Codex._

This cycle completes canonical date review for all 31 rows in the Rio v4 dry-run
sample without adding a production target row or writing private dashboard
payloads.

## Tooling Change

`tools/rio_economic_canonical_review.py` now supports:

```text
--start-row
```

This lets the loop review rows 21-31 without re-fetching the first 20 rows.

`tools/rio_economic_build_topic_report.py` now accepts multiple:

```text
--canonical-report
```

This lets the topic report combine the 20-row and 11-row canonical passes into
one complete 31-row evidence set.

## Generated Artifacts

```text
data/reports/rio_economic_canonical_review_20260519T014441Z.json
data/reports/rio_economic_canonical_review_20260519T014441Z.csv
data/reports/rio_economic_canonical_review_20260519T014441Z.md
data/reports/rio_economic_topic_report_20260519T014505Z.json
data/reports/rio_economic_topic_report_20260519T014505Z.csv
data/reports/rio_economic_topic_report_20260519T014505Z.md
```

## Rows 21-31 Canonical Result

```text
rows_checked=11
start_row=21
source_rows_total=31
date_quality_eligible_rows=8
same_day=8
canonical_date_missing=2
fetch_error=1
stores_article_body=false
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

## Full Topic Report Result

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

The full report eliminates `canonical_check_required` for this v4 sample. It
does not eliminate the production gate because seven stories remain
research-only and one story still requires manual approval before counting.

## Research-Only Story Reasons

```text
canonical_date_missing=4
date_mismatch=1
fetch_error=2
```

These rows should not count in a current-period economic indicator unless an
operator performs manual approval and logs the reason.

## Production Meaning

The Rio track now has a full reviewed sample suitable for method discussion:

- counts are story-based, not article-row-based;
- duplicate clusters are collapsed;
- date quality is explicit per story;
- report artifacts do not write to production DB, assets, or targets;
- `target_row_approved=false` remains in the report.

The next production-safe step is no longer more canonical review for this
sample. It is one of:

- define the manual-approval workflow for `near_date` and research-only rows;
- build a scoped Rio topic-report view behind the `rio_economico` profile;
- run fresh authenticated production scoping proof when credentials are
  available;
- design a narrow operator-approved first run without a plain target row.
