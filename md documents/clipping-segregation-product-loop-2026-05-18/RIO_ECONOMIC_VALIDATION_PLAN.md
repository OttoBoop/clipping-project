# Rio Economic Validation Plan

_Created 2026-05-19 by Atlas/Codex after production viewer segregation was
proven._

This document turns the Rio economic indicator from a vague future idea into a
safe validation loop. It deliberately does **not** add `rio_economico` to
`data/targets.json` yet.

## Hard Boundary

Do not create a real `rio_economico` target row until a sample set has been
reviewed and false positives are understood.

Reason:

```text
data/targets.json -> pipeline.settings.get_active_targets() ->
label automatically becomes keyword -> collectors/matcher/DB/export
```

Adding a broad placeholder such as `Rio Economico` would become a live matcher
term and could pollute the shared backend.

## Current Safe State

Safe and already live:

```text
viewer profile: rio_economico
target scope: ["rio_economico"]
target row in data/targets.json: absent
Render view: empty isolated profile
```

This proves isolation without collecting unvalidated Rio/economy material.

## First Validation Output

Before an indicator, produce a review table outside the production DB:

```text
query
dimension
source
title
url
published_at
why_candidate
review_label=true_positive|false_positive|unclear
false_positive_reason
notes
```

Store review artifacts under `data/reports/` or a loop doc. Do not pipe them
into `assets/clipping-data.json`, SQLite mentions, or public/private client
payloads until approved.

## Dimensions And Safer Query Patterns

Use city anchors plus an economic dimension. Avoid single broad terms.

| Dimension | Safer Query Patterns | Avoid Alone |
| --- | --- | --- |
| Tourism and events | `"Rio de Janeiro" hotelaria`, `"cidade do Rio" turismo`, `"Rio" ocupação hoteleira` | `turismo`, `evento Rio` |
| Commerce and services | `"cidade do Rio" comércio`, `"Rio de Janeiro" bares restaurantes`, `"Prefeitura do Rio" comércio` | `mercado Rio`, `lojas Rio` |
| Jobs and income | `"Rio de Janeiro" emprego`, `"cidade do Rio" vagas`, `"Prefeitura do Rio" trabalho renda` | `emprego`, `renda` |
| Construction and real estate | `"Rio de Janeiro" construção civil`, `"cidade do Rio" mercado imobiliário`, `"Rio" licenciamento obras` | `imóveis Rio` |
| Budget and public finance | `"Prefeitura do Rio" orçamento`, `"município do Rio" arrecadação`, `"cidade do Rio" ISS` | `orçamento Rio` |
| Logistics and port | `"Porto do Rio" logística`, `"Rio de Janeiro" cargas`, `"Aeroporto do Galeão" cargas` | `porto`, `Galeão` |
| Business openings/closures | `"Rio de Janeiro" inaugura loja`, `"cidade do Rio" fechamento comércio`, `"Rio" falência empresa` | `empresa Rio` |
| Cost of living | `"Rio de Janeiro" cesta básica`, `"cidade do Rio" aluguel`, `"Rio" inflação serviços` | `inflação Rio` |

## Source Tiers For The First Sample

Start with sources already represented in the app:

- Google News for broad discovery;
- G1 Rio and O Globo for city agenda;
- Diário do Rio, Tempo Real RJ, Agenda do Poder, Veja Rio for local signal;
- Prefeitura/Câmara material only when the topic has economic substance, not
  just political positioning.

Do not treat one source hit as enough to define a dimension.

## False Positive Labels

Use these reasons consistently:

- `national_macro_only`: national economy story with incidental Rio mention;
- `state_not_city`: state-level item with no city-specific signal;
- `politics_no_economic_signal`: political story without economic content;
- `event_no_economic_signal`: event/celebrity story without measurable local
  economic angle;
- `crime_no_commerce_signal`: public safety story without commerce/tourism or
  local business impact;
- `ambiguous_rio`: Rio as name/brand/person, not city context;
- `source_date_mismatch`: Google News/source date does not match the canonical
  article body/date well enough for production use;
- `too_generic`: query matched a broad word without useful local content.

## Minimum Acceptance Before Adding A Target

Only after a dry-run sample:

```text
at least 30 reviewed candidate articles
at least 60% true_positive or useful_unclear
no single query family dominates the useful sample
false positive reasons logged and mitigated
dimension labels still make sense after reading examples
Otavio/operator accepts that collection cost is sustainable
```

Then and only then consider:

```text
data/targets.json target row: rio_economico
viewer profile: rio_economico remains isolated
first run: narrow date window + selected collectors
post-run check: Flavio/Shakira payloads still exclude Rio material
```

## First Technical Approach

Preferred first implementation is a dry-run collector/report, not a production
target:

```text
candidate query list -> collector sample -> review CSV/JSON/MD ->
manual labels -> query revision -> repeat
```

If a script is created, it must:

- never write to `data/clipping.db`;
- never update `assets/clipping-data.json`;
- never mutate `data/targets.json`;
- store output under `data/reports/` with a timestamp;
- log sample size and query list in `WORK_LOG.md`.

Current implementation status:

```text
tools/rio_economic_dry_run.py exists
offline fixture mode exists
first offline fixture artifacts generated under data/reports/
live Google News smoke works when redirect resolution is skipped
Google redirect resolution remains a separate runtime/threading risk
first live smoke artifacts generated under data/reports/
```

First live smoke evidence:

```text
data/reports/rio_economic_dry_run_20260518T220015Z.json
row_count=4
query_count=2
request_timeout=5
resolve_timeout=0
redirect_resolution_skipped=true
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

Initial methodology lesson: `"cidade do Rio" turismo` can still catch items
about other municipalities in the state of Rio. Treat this as `state_not_city`
unless the article has a concrete city-of-Rio economic signal.

First 30-row sample evidence:

```text
data/reports/rio_economic_dry_run_20260518T220725Z.json
row_count=32
query_count=8
request_timeout=5
resolve_timeout=0
redirect_resolution_skipped=true
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

Title-level review notes:

```text
RIO_ECONOMIC_SAMPLE_REVIEW_20260518T220725Z.md
```

Early finding: jobs and budget queries are more promising than broad
construction terms. Commerce/tourism terms need tighter city-of-Rio anchors and
false-positive exclusions before any automated target/matcher row exists.

Revised query-file evidence:

```text
data/reports/rio_economic_revised_queries_20260518.json
data/reports/rio_economic_dry_run_20260518T221140Z.json
row_count=29
query_count=10
queries_file=data/reports/rio_economic_revised_queries_20260518.json
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

Revised sample notes:

```text
RIO_ECONOMIC_REVISED_SAMPLE_REVIEW_20260518T221140Z.md
```

The revised set improved event/tourism, real-estate, licensing/works, and
ambulante-commerce signals, but still needs negative terms and stronger source
anchors before any production target row.

Title-exclusion follow-up:

```text
data/reports/rio_economic_dry_run_20260518T221521Z.json
row_count=26
exclude_title_terms active in data/reports/rio_economic_revised_queries_20260518.json
Rio das Ostras=0
Rio Grande=0
Porto Velho=0
portovelho=0
Pernambuco=0
```

This is a cleaner review sample, but still not production ingestion approval.

Title-level labels:

```text
RIO_ECONOMIC_TITLE_LABELS_20260518T221521Z.md
true_positive=18
useful_unclear=4
false_positive=3
unclear=1
```

The useful-or-unclear title-level share is promising, but the remaining false
positives and dimension mismatches confirm that Rio still needs methodology
cleanup before target-row creation.

Source/dimension refinement decision:

```text
RIO_ECONOMIC_SOURCE_DIMENSION_REFINEMENT.md
budget_finance split into municipal_finance and economic_development before next sample
source anchors required for broad jobs/tourism/economic-development queries
production target row still blocked until a revised reviewed sample passes the gate
```

V2 revised sample evidence:

```text
data/reports/rio_economic_revised_queries_v2_20260518.json
data/reports/rio_economic_dry_run_20260518T234225Z.json
row_count=33
query_count=12
municipal_finance and economic_development separated
RIO_ECONOMIC_V2_SAMPLE_REVIEW_20260518T234225Z.md
true_positive=27
useful_unclear=2
false_positive=4
useful_or_unclear=29/33
```

The v2 sample is stronger, but it still needs v3 cleanup for Rio Grande
ambulante false positives, national fiscal-analysis leakage, and generic
official economic-development queries.

V3 revised sample evidence:

```text
data/reports/rio_economic_revised_queries_v3_20260518.json
data/reports/rio_economic_dry_run_20260518T234818Z.json
row_count=33
query_count=12
RIO_ECONOMIC_V3_SAMPLE_REVIEW_20260518T234818Z.md
true_positive=31
useful_unclear=1
false_positive=1
useful_or_unclear=32/33
```

The v3 title-level sample is strong enough for body/source review, but still
does not approve a production target row by itself.

Body/source review plan:

```text
RIO_ECONOMIC_V3_BODY_SOURCE_REVIEW_PLAN.md
first priority rows: v3 #15 and #27
minimum gate: at least 20 body/source-reviewed rows, at least one per dimension,
all known false positives mitigated, fresh production scoping proof
```

First body/source review pass:

```text
RIO_ECONOMIC_V3_BODY_SOURCE_REVIEW_20260518.md
rows_reviewed=21
dimensions_covered=6/6
body_true_positive=16
body_useful_unclear=1
body_false_positive=2
body_duplicate=2
production_target_row_approved=false
```

Main body/source findings:

```text
row 15 hotel-jobs ambiguity needs Rio/title/body/source anchor mitigation
row 27 state-government Fazenda leakage needs exclusions
row 1 exposed Google News recency/source mismatch risk
Shakira and Mercado Popular stories need clustering before dashboard use
```

V4 mitigation sample:

```text
data/reports/rio_economic_revised_queries_v4_20260518.json
data/reports/rio_economic_dry_run_20260519T000719Z.json
row_count=31
query_count=12
RIO_ECONOMIC_V4_SAMPLE_REVIEW_20260519T000719Z.md
true_positive=24
useful_unclear=1
duplicate=6
false_positive=0
useful_or_unclear_before_clustering=25/31
```

V4 removed the known generic hotel-jobs false positive and state-government
Fazenda false positive from the sampled title set. Production is still blocked
until canonical source/date checks, duplicate clustering, and fresh production
segregation proof are handled.

Canonical source/date helper evidence:

```text
tools/rio_economic_canonical_review.py
data/reports/rio_economic_canonical_review_20260519T002419Z.json
rows_checked=3
stores_article_body=false
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
row 1 canonical_date_missing
row 2 same_day
row 3 same_day
```

This proves the canonical-review path can resolve and audit Google News rows
without storing article bodies. It also confirms row 1 must remain blocked or
manually reviewed because the canonical page did not expose a usable published
date.

Duplicate cluster review:

```text
RIO_ECONOMIC_V4_DUPLICATE_CLUSTER_REVIEW.md
Shakira economic impact -> one cross-dimension event cluster
Mercado Popular da Uruguaiana -> one commerce/services cluster
Mais Valia/Mais Valera -> one construction/licensing cluster
```

Future Rio counts must distinguish `article_count` from deduplicated
`story_count`; otherwise repeated sources will inflate the apparent economic
signal.

Cluster review format update:

```text
tools/rio_economic_dry_run.py now emits blank cluster fields:
cluster_key
cluster_label
primary_dimension
secondary_dimensions
representative_url
duplicate_of
```

These fields are manual-review scaffolding only. They do not write to the
production database, scoped assets payload, or `data/targets.json`.

Extended canonical source/date review:

```text
data/reports/rio_economic_canonical_review_20260519T003852Z.json
rows_checked=10
same_day=8
canonical_date_missing=1
date_mismatch=1
stores_article_body=false
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
RIO_ECONOMIC_CANONICAL_REVIEW_20260519T003852Z.md
```

Rows with `date_mismatch` or `canonical_date_missing` must not count toward a
current-period indicator without manual approval.

Date quality policy:

```text
RIO_ECONOMIC_DATE_QUALITY_POLICY.md
tools/rio_economic_canonical_review.py records status_counts and date_quality_eligible_rows for future reports
same_day rows may count
near_date rows require manual review
date_mismatch/canonical_date_missing rows are research-only until manual approval
```

Cluster-annotated v4 review:

```text
tools/rio_economic_apply_cluster_annotations.py
data/reports/rio_economic_v4_cluster_annotations_20260518.json
data/reports/rio_economic_clustered_review_20260519T004653Z.json
row_count=31
cluster_count=3
clustered_row_count=9
RIO_ECONOMIC_CLUSTERED_REVIEW_20260519T004653Z.md
```

The cluster review proves at least nine article rows should collapse into three
stories before dashboard counts or weekly summaries.

Production gate:

```text
RIO_ECONOMIC_PRODUCTION_GATE_V0.md
production rio_economico target row approved=false
requires live scoping proof + query quality + date quality + cluster counting + source/body review + narrow first-run plan
```

Topic-report consolidation:

```text
tools/rio_economic_build_topic_report.py
data/reports/rio_economic_topic_report_20260519T012024Z.json
story_count=25
article_count=31
canonical_rows_checked=10
count_current_period=6
research_only=2
canonical_check_required=17
target_row_approved=false
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
RIO_ECONOMIC_TOPIC_REPORT_20260519T012024Z.md
```

This is the first implementation of the safer topic-report path. It still does
not approve a production target row; it shows that most v4 stories need
canonical checks before current-period counting.

Extended canonical/topic-report pass:

```text
tools/rio_economic_build_topic_report.py now uses cluster-member canonical evidence
data/reports/rio_economic_canonical_review_20260519T013449Z.json
rows_checked=20
date_quality_eligible_rows=15
same_day=14
near_date=1
canonical_date_missing=2
date_mismatch=1
fetch_error=2
data/reports/rio_economic_topic_report_20260519T013645Z.json
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
RIO_ECONOMIC_EXTENDED_CANONICAL_TOPIC_REPORT_20260519T013645Z.md
```

The topic report now records `date_quality_source_row` and
`date_quality_evidence_rows` so duplicate clusters are not downgraded only
because the representative source failed. The Mais Valia/Mais Valera cluster
now counts from row 17 same-day evidence while preserving row 16's fetch error
in `date_quality_evidence_statuses`.

Full canonical/topic-report pass:

```text
tools/rio_economic_canonical_review.py now supports --start-row
tools/rio_economic_build_topic_report.py now accepts multiple --canonical-report values
data/reports/rio_economic_canonical_review_20260519T014441Z.json
rows_checked=11
start_row=21
same_day=8
canonical_date_missing=2
fetch_error=1
data/reports/rio_economic_topic_report_20260519T014505Z.json
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
RIO_ECONOMIC_FULL_CANONICAL_TOPIC_REPORT_20260519T014505Z.md
```

This closes canonical checks for the v4 sample (`canonical_check_required=0` in
the complete topic report), but it does not approve production ingestion.
Manual-approval policy and scoped Rio topic rendering still need review before
any user-facing economic indicator.

Manual approval policy:

```text
RIO_ECONOMIC_MANUAL_APPROVAL_POLICY_V0.md
same_day -> automatic current-period count
near_date -> manual_review_before_counting
research-only statuses -> do not count unless human evidence is logged
automatic count=17
manual review=1
research_only=7
```

The v4 report may discuss 25 reviewed stories, but the indicator count must not
claim more than 17 current-period stories until a sidecar approval file or
explicit manual status field promotes additional rows.

## First Review Questions For The Loop

- Which 8-12 queries produce a broad but reviewable first sample?
- Which sources return local economic signal instead of generic Rio mentions?
- Which terms need explicit city-of-Rio anchors or exclusions to avoid
  state-level false positives?
- Does the first sample look like a dashboard feed, a weekly brief, or a future
  score?
- What is the collection cost per sample?
- What must be excluded before adding any target row?
