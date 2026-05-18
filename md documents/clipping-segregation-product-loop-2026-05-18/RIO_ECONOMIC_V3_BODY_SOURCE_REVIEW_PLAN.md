# Rio Economic V3 Body/Source Review Plan

_Created 2026-05-18 by Atlas/Codex._

The v3 title-level sample is strong, but title review is not enough to approve a
production `rio_economico` target row. This plan defines the next review gate.

## Source Artifacts

```text
data/reports/rio_economic_revised_queries_v3_20260518.json
data/reports/rio_economic_dry_run_20260518T234818Z.json
RIO_ECONOMIC_V3_SAMPLE_REVIEW_20260518T234818Z.md
```

## Review Questions

For each row, answer:

```text
does the body/source prove city-of-Rio specificity?
does the body/source prove the assigned economic dimension?
is the source credible enough for a client-facing dashboard?
is the story duplicative of another row?
would this item pollute a political/person clipping profile?
```

## Priority Rows

Review these first:

```text
15 jobs_income
title=Vagas abertas reforçam movimento da hotelaria em janeiro
reason=title does not prove city specificity

27 municipal_finance
title=Governo do Rio faz 40 exonerações após operação da PF que teve Cláudio Castro como alvo
reason=state politics false positive; should be excluded or query narrowed
```

Then review representative true-positive rows from each dimension:

```text
tourism_events: rows 1, 4, 6
commerce_services: rows 7, 8, 10
jobs_income: rows 11, 14, 16
construction_real_estate: rows 17, 20, 22
municipal_finance: rows 23, 26, 28
economic_development: rows 29, 31, 33
```

## Body Review Labels

Use:

```text
body_true_positive
body_useful_unclear
body_false_positive
body_duplicate
body_unreadable
```

False-positive reasons:

```text
state_not_city
source_not_city_specific
dimension_mismatch
politics_no_economic_signal
national_macro_only
event_no_economic_signal
duplicate_story
paywall_or_unreadable
```

## Promotion Gate

Before creating any production target row:

```text
at least 20 body/source-reviewed rows
at least one reviewed row per dimension
all known false-positive rows have a mitigation
latest Render logged-out privacy smoke passes
authenticated viewer proof is fresh or blocker is explicitly accepted by Otavio
first production run is narrow date-window only
post-run payload check proves Flavio/Shakira/Rio separation
```

## Important Boundary

This plan does not approve:

```text
data/targets.json rio_economico row
SQLite ingestion
assets payload update
client-facing Rio dashboard content
```

It only defines the next review step.
