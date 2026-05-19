# Rio Economic Ingestion Architecture Decision

_Created 2026-05-18 by Atlas/Codex._

This decision exists because the Rio economic methodology has become more
specific than a normal person/entity target.

## Decision

Do not implement Rio economic monitoring as a plain `data/targets.json` target
row with label/keywords only.

The first safe production design should use a topic/query configuration that
can preserve:

- economic dimension;
- exact query text;
- title/source exclusion terms;
- canonical date quality;
- duplicate cluster key;
- representative story policy;
- profile/project scope.

Until that exists, keep `rio_economico` as an isolated viewer profile and keep
Rio samples as dry-run review artifacts.

## Why A Plain Target Row Is Unsafe

The current target mechanism is good for monitored names/entities. For Rio
economic monitoring, it is too blunt:

```text
data/targets.json -> label/keywords -> collectors/matcher -> DB/export
```

Risks:

- `Rio Economico` or broad Rio/economy labels become matcher terms;
- target rows do not encode dimension labels;
- target rows do not encode `exclude_title_terms`;
- target rows do not encode canonical-date acceptance rules;
- target rows do not encode duplicate cluster policy;
- broad topic hits could enter the shared DB before review;
- post-run cleanup would be harder than keeping the feed out of production.

## Safe First Production Shape

Preferred shape:

```text
rio_economic_query_config -> collector sample -> canonical date gate ->
cluster annotation/dedup -> scoped rio_economico payload/report
```

Only after that scoped topic pipeline exists should the loop consider whether
to mirror results into the normal dashboard/story model.

## Minimum Technical Requirements

Before any production Rio run:

- query config can store the 12 v4 query families and their exclusions;
- collector output carries `dimension`;
- rows with `date_mismatch` or `canonical_date_missing` are excluded from
  current-period counts unless manually accepted;
- repeated rows collapse into `story_count` clusters;
- output can be scoped to `rio_economico` without appearing in Flavio/Shakira;
- raw texts, if fetched, are only served to the Rio profile;
- first run uses a narrow date window and records operator time/cost.

## V4 Query Families To Preserve

Source:

```text
data/reports/rio_economic_revised_queries_v4_20260518.json
```

The current candidate set has 12 query families across:

```text
tourism_events
commerce_services
jobs_income
construction_real_estate
municipal_finance
economic_development
```

Do not flatten these into one keyword list.

## First-Run Gate

The production target row remains blocked:

```text
production rio_economico target row approved=false
```

The next technical implementation should be either:

1. a scoped Rio topic collector/report that does not mutate the shared clipping
   DB/assets; or
2. a broader dashboard data model change that supports topic/query projects
   with profile scope, date quality, and clustering before export.

Option 1 is safer for the next loop because it preserves isolation and cost
discipline.
