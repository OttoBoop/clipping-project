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

## First Review Questions For The Loop

- Which 8-12 queries produce a broad but reviewable first sample?
- Which sources return local economic signal instead of generic Rio mentions?
- Which terms need explicit city-of-Rio anchors or exclusions to avoid
  state-level false positives?
- Does the first sample look like a dashboard feed, a weekly brief, or a future
  score?
- What is the collection cost per sample?
- What must be excluded before adding any target row?
