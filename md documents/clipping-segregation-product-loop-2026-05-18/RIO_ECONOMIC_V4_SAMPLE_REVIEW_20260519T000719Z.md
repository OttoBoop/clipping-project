# Rio Economic V4 Sample Review - 20260519T000719Z

_Created 2026-05-18 by Atlas/Codex._

Title-level review for the v4 Rio economic dry-run sample. This is a
methodology artifact and still does not approve a production `rio_economico`
target row.

Source artifacts:

```text
data/reports/rio_economic_revised_queries_v4_20260518.json
data/reports/rio_economic_dry_run_20260519T000719Z.json
data/reports/rio_economic_dry_run_20260519T000719Z.csv
data/reports/rio_economic_dry_run_20260519T000719Z.md
RIO_ECONOMIC_V3_BODY_SOURCE_REVIEW_20260518.md
```

Dry-run safety:

```text
row_count=31
query_count=12
resolve_timeout=0
redirect_resolution_skipped=true
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

## What V4 Changed

V4 applies the body/source review mitigations from v3:

```text
generic hotel-jobs row removed
state-government Fazenda/PF/Claudio Castro row removed
municipal-finance state terms excluded
hotel jobs exact ambiguous title excluded
tourism occupancy query flagged for canonical source/date check
duplicate-prone stories flagged for clustering before dashboard display
```

## Title Labels

| # | Dimension | Label | False Positive Reason | Title-Level Note |
| --- | --- | --- | --- | --- |
| 1 | tourism_events | useful_unclear | source_date_mismatch | Still useful city occupancy title, but body/source review found canonical date risk. |
| 2 | tourism_events | true_positive |  | Zona Sul hotel occupancy around Shakira event. |
| 3 | tourism_events | true_positive |  | Rio carnival hotel occupancy above 99%. |
| 4 | tourism_events | true_positive |  | Prefeitura quantifies Shakira economic impact. |
| 5 | tourism_events | true_positive |  | Copacabana event with explicit economic-impact title. |
| 6 | tourism_events | true_positive |  | Rio visitor volume and impact forecast. |
| 7 | commerce_services | true_positive |  | Jacarepagua ambulante/sidewalk commerce action. |
| 8 | commerce_services | true_positive |  | Mercado Popular da Uruguaiana official launch. |
| 9 | commerce_services | duplicate | duplicate_story | Same Mercado Popular story from another source. |
| 10 | commerce_services | duplicate | duplicate_story | Same Mercado Popular story from another source. |
| 11 | jobs_income | true_positive |  | Prefeitura/SMTE city jobs count. |
| 12 | jobs_income | true_positive |  | City jobs count from Diario do Rio. |
| 13 | jobs_income | true_positive |  | Trabalha Rio service in city neighborhoods. |
| 14 | jobs_income | true_positive |  | Grand Hyatt Rio hiring. |
| 15 | jobs_income | true_positive |  | Hilton Copacabana/Barra hiring. |
| 16 | construction_real_estate | true_positive |  | Works regularization with municipal discount. |
| 17 | construction_real_estate | duplicate | duplicate_story | Same Mais Valia/Mais Valera story from another source. |
| 18 | construction_real_estate | duplicate | duplicate_story | Same Mais Valia/Mais Valera story from another source. |
| 19 | construction_real_estate | true_positive |  | Rio real-estate investment signal. |
| 20 | construction_real_estate | true_positive |  | Foreign buying in Rio apartments. |
| 21 | construction_real_estate | true_positive |  | Real-estate funds and Rio projects. |
| 22 | municipal_finance | true_positive |  | Tourism ISS revenue figure. |
| 23 | municipal_finance | true_positive |  | Missed tax revenue / fiscal accountability. |
| 24 | municipal_finance | true_positive |  | Airport-services ISS revenue growth. |
| 25 | municipal_finance | true_positive |  | Municipal Fazenda results in Camara do Rio. |
| 26 | municipal_finance | true_positive |  | Fazenda accountability hearing in Camara do Rio. |
| 27 | economic_development | true_positive |  | Invest.Rio business/investor attraction. |
| 28 | economic_development | true_positive |  | Invest.Rio capital attraction. |
| 29 | economic_development | true_positive |  | Invest.Rio/Maravalley business mission. |
| 30 | economic_development | duplicate | duplicate_story | Shakira impact story already captured in tourism/economic impact cluster. |
| 31 | economic_development | duplicate | duplicate_story | Shakira impact story already captured in tourism/economic impact cluster. |

## Tally

```text
true_positive=24
useful_unclear=1
duplicate=6
false_positive=0
unclear=0
useful_or_unclear_before_clustering=25/31
```

Duplicate cluster follow-up:

```text
RIO_ECONOMIC_V4_DUPLICATE_CLUSTER_REVIEW.md
Shakira economic impact rows: 4, 30, 31
Mercado Popular rows: 8, 9, 10
Mais Valia/Mais Valera rows: 16, 17, 18
```

After clustering, the v4 sample should be evaluated by `story_count` as well as
`article_count`.

## Gate Status

V4 is better than v3 for known false positives, but it still is not production
approval.

Remaining blockers:

```text
canonical source/date check for Google News rows
story clustering before dashboard display
fresh logged-out Render smoke after latest deploy
fresh authenticated viewer proof or explicit Otavio acceptance of password blocker
first production run must be narrow date-window only
post-run proof that Flavio/Shakira/Rio payloads remain segregated
```

Canonical source/date follow-up started:

```text
tools/rio_economic_canonical_review.py
data/reports/rio_economic_canonical_review_20260519T002419Z.json
rows_checked=3
row 1 canonical_date_missing
row 2 same_day
row 3 same_day
```

Implication: row 1 remains blocked for production until the canonical date is
confirmed manually or the source is excluded. Rows 2 and 3 passed same-day
canonical checks in the sample.

Next safe step:

```text
poll Render for 48baf67
run live logged-out privacy smoke when it is live
extend canonical URL/date review beyond the first three rows
```
