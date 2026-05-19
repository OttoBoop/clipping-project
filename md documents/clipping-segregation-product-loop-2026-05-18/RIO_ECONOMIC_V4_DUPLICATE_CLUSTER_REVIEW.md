# Rio Economic V4 Duplicate Cluster Review

_Created 2026-05-18 by Atlas/Codex._

This reviews duplicate-prone stories in the v4 Rio economic sample:

```text
data/reports/rio_economic_dry_run_20260519T000719Z.json
RIO_ECONOMIC_V4_SAMPLE_REVIEW_20260519T000719Z.md
```

It does not create a production `rio_economico` target row. It defines how a
future Rio dashboard should avoid inflated counts from repeated sources.

## Duplicate Clusters Found

| Cluster | Rows | Dimension(s) | Representative Story | Keep As |
| --- | --- | --- | --- | --- |
| Shakira economic impact | 4, 30, 31 | tourism_events, economic_development | Prefeitura/Shakira economic-impact estimate for Copacabana/Todo Mundo no Rio | one cross-dimension event cluster |
| Mercado Popular da Uruguaiana | 8, 9, 10 | commerce_services | Prefeitura launches/relaunches Novo Mercado Popular da Uruguaiana | one commerce/services cluster |
| Mais Valia / Mais Valera regularization | 16, 17, 18 | construction_real_estate | Prefeitura extends regularization discount for works/amplifications | one construction/licensing cluster |

## Counting Policy

For a future Rio economic dashboard:

```text
article_count = raw article/source count
story_count = deduplicated story clusters
dimension_count = dimensions touched by clusters
primary_dimension = one chosen dimension for each cluster
secondary_dimensions = optional supporting dimensions
```

Do not use raw article count alone as an economic signal. It will overstate
events that get reposted across Prefeitura, local press, and syndication.

## Dimension Policy

For cross-dimension stories:

```text
Shakira economic impact -> primary_dimension=tourism_events
secondary_dimensions=economic_development, municipal_finance when ISS/revenue appears
```

Reason: the event is mainly a visitor/event-economy signal. It can inform
economic development, but should not appear as a separate economic event in both
sections unless the UI explicitly supports cross-tags.

For Mercado Popular:

```text
primary_dimension=commerce_services
secondary_dimensions=construction_real_estate only if the article emphasizes construction/investment execution
```

For Mais Valia/Mais Valera:

```text
primary_dimension=construction_real_estate
secondary_dimensions=municipal_finance only if arrecadacao/contrapartida is central
```

## Production Gate Implication

Before Rio production ingestion:

```text
queries may collect multiple articles per story
payload/rendering must group them into one story
weekly summary must mention the cluster once
counts must distinguish article_count from story_count
```

## Suggested Manual Clustering Fields

The dry-run review CSV/JSON/MD format now includes optional blank fields for:

```text
cluster_key
cluster_label
primary_dimension
secondary_dimensions
representative_url
duplicate_of
```

## Current Status

V4 duplicate risk is understood enough for manual review, and the Rio dry-run
script now emits blank cluster fields so the next sample review can annotate
clusters directly without changing production data.

Next safe step:

```text
run the next reviewed sample with cluster annotations, extend canonical
source/date checks, and keep the production rio_economico target row blocked
until fresh scoping proof and methodology acceptance are recorded.
```
