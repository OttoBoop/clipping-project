# Rio Economic Extended Canonical And Topic Report - 20260519T013645Z

_Created 2026-05-18 by Atlas/Codex._

This cycle extends the Rio economic date-quality review from 10 to 20 rows and
rebuilds the scoped topic report without writing production DB, scoped assets,
or `data/targets.json`.

## Source Artifacts

```text
data/reports/rio_economic_dry_run_20260519T000719Z.json
data/reports/rio_economic_clustered_review_20260519T004653Z.json
```

Generated:

```text
data/reports/rio_economic_canonical_review_20260519T013449Z.json
data/reports/rio_economic_canonical_review_20260519T013449Z.csv
data/reports/rio_economic_canonical_review_20260519T013449Z.md
data/reports/rio_economic_topic_report_20260519T013645Z.json
data/reports/rio_economic_topic_report_20260519T013645Z.csv
data/reports/rio_economic_topic_report_20260519T013645Z.md
```

## Canonical Review Result

```text
rows_checked=20
date_quality_eligible_rows=15
same_day=14
near_date=1
date_mismatch=1
canonical_date_missing=2
fetch_error=2
stores_article_body=false
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

Rows with `same_day` can count automatically. The `near_date` row requires
manual approval before counting. `date_mismatch`, `canonical_date_missing`, and
`fetch_error` remain research-only.

## Cluster-Aware Topic Report Result

```text
story_count=25
article_count=31
canonical_rows_checked=20
count_current_period=11
manual_review_before_counting=1
research_only=4
canonical_check_required=9
target_row_approved=false
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

The topic report now records:

```text
date_quality_source_row
date_quality_evidence_rows
date_quality_evidence_statuses
```

This matters because a clustered story may have a representative row whose
canonical fetch fails while another member of the same reviewed duplicate
cluster has valid date evidence.

## Methodology Fix

`tools/rio_economic_build_topic_report.py` now evaluates canonical evidence
across all member rows in a story cluster. It prefers the strongest available
cluster evidence in this order:

```text
same_day
near_date
first recorded non-pass evidence
```

The practical example is the Mais Valia/Mais Valera cluster:

```text
story representative row=16
member_rows=16,17,18
row 16 status=fetch_error
row 17 status=same_day
row 18 status=same_day
date_quality_source_row=17
story policy=count_current_period
```

Without this fix, the topic report treated the whole cluster as `research_only`
because only the representative row was checked. That understated usable Rio
economic signal and made the cluster policy depend on a fragile source choice.

## Production Meaning

This improves the Rio methodology, but it still does not approve production
dashboard ingestion:

- 9 stories still need canonical checks;
- 4 stories remain research-only;
- 1 story needs manual approval before counting;
- authenticated live profile proof still requires viewer/admin passwords;
- no `rio_economico` target row was added.

## Next Safe Step

Either extend canonical review to the remaining rows 21-31 or wire a scoped
topic-report view behind the existing `rio_economico` viewer profile. Do not add
a plain `data/targets.json` row until profile isolation, date quality, cluster
rendering, and a narrow operator-approved run are all proven.
