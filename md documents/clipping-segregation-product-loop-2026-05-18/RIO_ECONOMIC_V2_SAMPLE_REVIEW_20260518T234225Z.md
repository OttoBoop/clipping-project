# Rio Economic V2 Sample Review - 20260518T234225Z

_Created 2026-05-18 by Atlas/Codex._

Title-level review for the v2 Rio economic dry-run sample. This is still a
review artifact, not production approval.

Source artifacts:

```text
data/reports/rio_economic_revised_queries_v2_20260518.json
data/reports/rio_economic_dry_run_20260518T234225Z.json
data/reports/rio_economic_dry_run_20260518T234225Z.csv
data/reports/rio_economic_dry_run_20260518T234225Z.md
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
| 7 | commerce_services | false_positive | state_not_city | Rio Grande municipal ambulante edital; add exclusion to this query. |
| 8 | commerce_services | true_positive |  | Jacarepagua ambulante/sidewalk commerce action. |
| 9 | commerce_services | true_positive |  | Mercado Popular da Uruguaiana. |
| 10 | commerce_services | true_positive |  | Mercado Sao Braz business/requalification meeting. |
| 11 | commerce_services | useful_unclear | dimension_mismatch | TurisMall is city business/tourism, but closer to economic_development. |
| 12 | commerce_services | useful_unclear | duplicate_or_dimension_mismatch | Same TurisMall story from a second source. |
| 13 | jobs_income | true_positive |  | Prefeitura-linked job/selective-process openings. |
| 14 | jobs_income | true_positive |  | City jobs count from Diario do Rio. |
| 15 | jobs_income | true_positive |  | Trabalha Rio employment service in city neighborhoods. |
| 16 | jobs_income | false_positive | source_not_city_specific | Tourism jobs title does not prove city-of-Rio signal. |
| 17 | jobs_income | true_positive |  | Hotel/tourism vacancies in Rio. |
| 18 | construction_real_estate | true_positive |  | Regularization discount for works. |
| 19 | construction_real_estate | true_positive |  | Mais Valia/Mais Valera works regularization. |
| 20 | construction_real_estate | true_positive |  | Works regularization with municipal deadline. |
| 21 | construction_real_estate | true_positive |  | Rio real-estate investment signal. |
| 22 | construction_real_estate | true_positive |  | Foreign buying in Rio apartments. |
| 23 | construction_real_estate | true_positive |  | Real-estate funds and Rio projects. |
| 24 | municipal_finance | true_positive |  | Tourism ISS revenue figure. |
| 25 | municipal_finance | true_positive |  | Missed tax revenue / fiscal accountability. |
| 26 | municipal_finance | true_positive |  | Airport-services revenue growth. |
| 27 | municipal_finance | false_positive | national_macro_only | IBS/federalism article, not city-specific finance. |
| 28 | municipal_finance | true_positive |  | Municipal Fazenda results in Câmara do Rio. |
| 29 | economic_development | true_positive |  | Invest.Rio innovation/business attraction. |
| 30 | economic_development | true_positive |  | Invest.Rio capital attraction. |
| 31 | economic_development | true_positive |  | Invest.Rio business/investor attraction. |
| 32 | economic_development | false_positive | official_quote_without_city_signal | Demographic Mother's Day story; not economic development from title. |
| 33 | economic_development | true_positive |  | Shakira event movement/economic impact. |

## Tally

```text
true_positive=27
useful_unclear=2
false_positive=4
unclear=0
useful_or_unclear=29/33
```

The v2 query set is stronger than the previous title-level sample. It still
needs a v3 cleanup before any production target row.

## Query Lessons

- Tourism/event queries are strong and should stay.
- Commerce improved, but `Prefeitura do Rio ambulantes comercio` still needs
  `Rio Grande` exclusion.
- Jobs improved with `Trabalho e Renda`, but the tourism/jobs query still needs
  a stronger city or source anchor.
- `municipal_finance` is much cleaner than the old `budget_finance`, but
  `"municipio do Rio" arrecadacao ISS` still catches national fiscal analysis.
- `economic_development` works well with `Invest.Rio`, but generic
  `"Prefeitura do Rio" "desenvolvimento economico"` catches unrelated official
  stories and should be narrowed.

## V3 Suggestions

Use the next revision to test:

```text
"Prefeitura do Rio" ambulantes comercio
exclude_title_terms += ["Rio Grande", "Festimar"]

"Rio de Janeiro" turismo empregos hotelaria
-> "\"Rio de Janeiro\" hotelaria vagas emprego"

"municipio do Rio" arrecadacao ISS
-> "\"Fazenda\" \"Câmara do Rio\" arrecadação"

"Prefeitura do Rio" "desenvolvimento economico"
-> "\"Prefeitura do Rio\" \"impacto economico\""
-> "\"Invest.Rio\" empresas investidores"
```

## Gate Status

Do not create `data/targets.json` row `rio_economico` yet.

The sample is promising, but the next safe step is v3 query cleanup and another
reviewed dry-run. Production requires a narrow first run plus post-run
contamination checks for Flavio/Shakira/Rio viewer payloads.
