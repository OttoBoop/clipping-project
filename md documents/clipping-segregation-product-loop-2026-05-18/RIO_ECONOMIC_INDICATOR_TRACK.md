# Rio Economic Indicator Track

_Created 2026-05-18 by Atlas/Codex._

This track exists because Otavio wants an economic indicator for the city of Rio
based on the clipping tool, but that must not pollute the Flavio-focused site or
future paid-client views.

Do not implement collection terms before the segregation layer is verified in
production.

## Product Boundary

Rio economic monitoring is a separate profile/project, not a secondary target
inside the Flavio view.

Current placeholder profile:

```text
rio_economico
```

The profile may start empty. Empty is safer than falling back to political or
client data.

## Current Implementation Audit

Checked 2026-05-19:

- `data/viewer_profiles.json` includes a `rio_economico` viewer profile scoped
  to target key `rio_economico`.
- `web_app/segmentation.py` includes the same default placeholder profile.
- `data/targets.json` does not yet include a `rio_economico` target row.

Decision: do not add a `rio_economico` row to `data/targets.json` yet.

Reason: `pipeline.settings.get_active_targets()` automatically adds a target's
label to its keywords. A placeholder target row would therefore become a real
collector/matcher term before the economic methodology is validated. That would
risk broad Rio/economy pollution, which this track explicitly exists to avoid.

The safe current state is:

```text
viewer profile exists -> empty scoped view is allowed -> no collection terms yet
```

First dry-run state, checked 2026-05-19:

```text
offline fixture review artifact exists
live Google News review artifact exists with redirect resolution skipped
no Rio data was written to clipping.db, assets/clipping-data.json, or targets.json
```

The first live smoke already showed one important risk: even `"cidade do Rio"`
can return state/nearby-city material. Keep `state_not_city` as a first-class
false-positive reason before any target row or automated indicator exists.

## Indicator Goal

Capture signals about Rio's local economic agenda, not generic national economy
news.

The output could become:

- a dashboard of relevant stories;
- a weekly narrative brief;
- a simple signal index;
- an internal research feed used to support analysis.

Do not choose the final output format before validating terms and false
positives.

## Candidate Dimensions

Start with dimensions, not raw keywords:

- employment and income;
- tourism and events;
- public finance and municipal budget;
- real estate and construction;
- commerce and services;
- port, logistics, and airports;
- safety impacts on commerce/tourism;
- regulation, permits, and inspections;
- investment announcements;
- business closures and openings;
- inflation/cost-of-living signals when explicitly local to Rio.

## Term-Design Risks

Rio is ambiguous. Terms must avoid pulling:

- national macroeconomic stories with a casual Rio mention;
- state-level stories that do not affect the city;
- crime/politics stories with no economic angle;
- celebrity/event mentions that do not indicate economic impact;
- tourism fluff with no city signal;
- generic "mercado" or "economia" pieces unrelated to Rio.

## First Term Design Pattern

Use conjunctions of:

```text
Rio/city anchor + economic dimension + local source/date constraints
```

Examples of safer anchors:

- `"Rio de Janeiro" turismo`
- `"Prefeitura do Rio" orçamento`
- `"cidade do Rio" comércio`
- `"Rio" hotelaria`
- `"Rio" construção civil`
- `"Porto do Rio" logística`

Examples that are too broad alone:

- `Rio economia`
- `mercado Rio`
- `turismo`
- `emprego`

## Validation Loop

Before any score/index exists:

1. collect a small sample;
2. label true positive / false positive;
3. record why false positives happened;
4. adjust terms/exclusions;
5. repeat until the feed is clean enough for a human brief.

Use `RIO_ECONOMIC_VALIDATION_PLAN.md` for the first dry-run methodology. That
plan exists specifically to avoid adding a broad `rio_economico` target before
sample review.

## Data Segregation Rule

Rio economic articles must not appear in:

- Flavio viewer payloads unless they explicitly match Flavio's allowed targets;
- Shakira profile;
- paid-client profiles;
- static private-client exports.

## Future Implementation Questions

These should be answered by the loop, not asked prematurely to Otavio:

- Should Rio economic monitoring use target-style matching or a separate topic
  classifier?
- Which sources are high-signal for local economic activity?
- Is a binary relevant/not-relevant label enough before a numeric score?
- Should the indicator separate "volume of coverage" from "economic sentiment"?
- How much AI summarization cost is acceptable per update?

## Not In The First Segregation Sprint

- no numeric index yet;
- no market research yet;
- no new repo/site;
- no automated public claim that the indicator measures the economy;
- no blending with Flavio's political dashboard.
