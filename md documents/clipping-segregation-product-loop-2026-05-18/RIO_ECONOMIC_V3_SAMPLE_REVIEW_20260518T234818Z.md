# Rio Economic V3 Sample Review - 20260518T234818Z

_Created 2026-05-18 by Atlas/Codex._

Title-level review for the v3 Rio economic dry-run sample. This is still a
methodology artifact, not production ingestion approval.

Source artifacts:

```text
data/reports/rio_economic_revised_queries_v3_20260518.json
data/reports/rio_economic_dry_run_20260518T234818Z.json
data/reports/rio_economic_dry_run_20260518T234818Z.csv
data/reports/rio_economic_dry_run_20260518T234818Z.md
```

Dry-run safety:

```text
row_count=33
query_count=12
resolve_timeout=0
redirect_resolution_skipped=true
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

## Title Labels

| # | Dimension | Label | False Positive Reason | Title-Level Note |
| --- | --- | --- | --- | --- |
| 1 | tourism_events | true_positive |  | Rio hotel reservations for carnival. |
| 2 | tourism_events | true_positive |  | Zona Sul hotel occupancy tied to Shakira event. |
| 3 | tourism_events | true_positive |  | Rio carnival hotel occupancy above 99%. |
| 4 | tourism_events | true_positive |  | Prefeitura quantifies Shakira economic impact. |
| 5 | tourism_events | true_positive |  | Copacabana event with explicit economic impact. |
| 6 | tourism_events | true_positive |  | Rio visitor volume forecast. |
| 7 | commerce_services | true_positive |  | Jacarepagua ambulante/sidewalk commerce action. |
| 8 | commerce_services | true_positive |  | Mercado Popular da Uruguaiana. |
| 9 | commerce_services | true_positive |  | Mercado Popular da Uruguaiana from local press. |
| 10 | commerce_services | true_positive |  | Uruguaiana commerce hub launch. |
| 11 | jobs_income | true_positive |  | Prefeitura-linked job/selective-process openings. |
| 12 | jobs_income | true_positive |  | City jobs count from Diario do Rio. |
| 13 | jobs_income | true_positive |  | Trabalha Rio employment service in city neighborhoods. |
| 14 | jobs_income | true_positive |  | Grand Hyatt Rio hiring. |
| 15 | jobs_income | useful_unclear | source_not_city_specific | Hotel jobs signal, but title does not prove city-specificity. |
| 16 | jobs_income | true_positive |  | Hilton Copacabana/Barra hiring. |
| 17 | construction_real_estate | true_positive |  | Regularization discount for works. |
| 18 | construction_real_estate | true_positive |  | Mais Valia/Mais Valera works regularization. |
| 19 | construction_real_estate | true_positive |  | Works regularization with municipal deadline. |
| 20 | construction_real_estate | true_positive |  | Rio real-estate investment signal. |
| 21 | construction_real_estate | true_positive |  | Foreign buying in Rio apartments. |
| 22 | construction_real_estate | true_positive |  | Real-estate funds and Rio projects. |
| 23 | municipal_finance | true_positive |  | Tourism ISS revenue figure. |
| 24 | municipal_finance | true_positive |  | Missed tax revenue / fiscal accountability. |
| 25 | municipal_finance | true_positive |  | Airport-services revenue growth. |
| 26 | municipal_finance | true_positive |  | Municipal Fazenda results in Câmara do Rio. |
| 27 | municipal_finance | false_positive | state_not_city | State-government exonerações story, not municipal finance. |
| 28 | municipal_finance | true_positive |  | Fazenda accountability hearing in Câmara do Rio. |
| 29 | economic_development | true_positive |  | Invest.Rio business/investor attraction. |
| 30 | economic_development | true_positive |  | Invest.Rio capital attraction. |
| 31 | economic_development | true_positive |  | Invest.Rio/Maravalley business mission. |
| 32 | economic_development | true_positive |  | Shakira event economic-impact estimate. |
| 33 | economic_development | true_positive |  | Prefeitura-linked Shakira economic movement estimate. |

## Tally

```text
true_positive=31
useful_unclear=1
false_positive=1
unclear=0
useful_or_unclear=32/33
```

The v3 title-level sample is the strongest Rio sample so far. It appears good
enough for a body/source review stage, but still not enough by itself to add a
production `rio_economico` target row.

## Improvements Versus V2

- Rio Grande ambulante leakage disappeared.
- Generic TurisMall commerce/development mismatch disappeared.
- National IBS/federalism finance leakage disappeared.
- Generic Mother's Day official story disappeared.
- Jobs became more city-anchored, with only one title-level ambiguity.

## Remaining Cleanup

- The query `"Fazenda" "Camara do Rio" arrecadacao` caught one state-level
  politics item. Next revision should require `Prefeitura` or exclude
  `Governo do Rio`, `Claudio Castro`, and `operação da PF`.
- The hotel jobs query has one title that does not prove city specificity.
  Body/source review should decide whether to keep it.

## Gate Status

Do not create `data/targets.json` row `rio_economico` yet.

Next safe step:

```text
body/source review for the 33 v3 rows
confirm no profile contamination in production after latest Render deploys
decide first narrow production run only after viewer scoping proof is fresh
```
