# Rio Economic Title Labels - 20260518T221521Z

_Created 2026-05-19 by Atlas/Codex._

Title-level labels for the cleaner 26-row Rio dry-run sample. These labels are
provisional because article bodies were not read.

Source artifact:

```text
data/reports/rio_economic_dry_run_20260518T221521Z.json
```

| # | Dimension | Label | False Positive Reason | Title-Level Note |
| --- | --- | --- | --- | --- |
| 1 | tourism_events | true_positive |  | Rio short-term rental demand tied to megaevents. |
| 2 | tourism_events | unclear | ambiguous_city | "Cidade" may be Niteroi/O Fluminense coverage; needs body/source check. |
| 3 | tourism_events | true_positive |  | Explicit economic/tourism impact in Rio. |
| 4 | tourism_events | true_positive |  | City tourism growth signal. |
| 5 | tourism_events | true_positive |  | Copacabana event impact signal. |
| 6 | commerce_services | true_positive |  | Ambulante/commercial order in Jacarepagua. |
| 7 | commerce_services | true_positive |  | Ambulantes on Rio beachfront. |
| 8 | commerce_services | true_positive |  | Ambulante sales during major event. |
| 9 | commerce_services | true_positive |  | Invest.Rio/business hub signal. |
| 10 | commerce_services | true_positive |  | Municipal commerce/agriculture-family seal. |
| 11 | jobs_income | true_positive |  | City jobs by municipal labor office. |
| 12 | jobs_income | true_positive |  | Prefeitura/Central do Trabalhador jobs. |
| 13 | jobs_income | false_positive | national_macro_only | National tourism jobs; Rio not clearly city-specific from title. |
| 14 | jobs_income | unclear | too_generic | Tourism jobs listing may not be city-specific. |
| 15 | jobs_income | false_positive | national_macro_only | Federal tourism-sector event/quote, not city-specific. |
| 16 | construction_real_estate | true_positive |  | City licensing/works dispute. |
| 17 | construction_real_estate | true_positive |  | Vidigal construction demolition. |
| 18 | construction_real_estate | true_positive |  | SEOP demolition in Vidigal. |
| 19 | construction_real_estate | true_positive |  | Rio real-estate investment signal. |
| 20 | construction_real_estate | true_positive |  | Rio real-estate project/opportunity signal. |
| 21 | construction_real_estate | true_positive |  | Rio eviction/real-estate pressure signal. |
| 22 | budget_finance | useful_unclear | dimension_mismatch | Relevant economic impact, but not really ISS/revenue. |
| 23 | budget_finance | true_positive |  | ISS forgiveness/asset exchange. |
| 24 | budget_finance | false_positive | state_not_city | Pernambuco project; add `pernambucanos` exclusion. |
| 25 | budget_finance | useful_unclear | dimension_mismatch | Economic development/Rio2C, not explicit arrecadacao/ISS. |
| 26 | budget_finance | useful_unclear | politics_no_economic_signal | Tax/culture incentive debate may matter, but needs body check. |

## Tally

```text
true_positive=18
useful_unclear=4
false_positive=3
unclear=1
```

Useful or unclear share: 22/26 title-level rows. This is promising enough to
continue methodology work, but not enough to create a production target row.

## Query Lessons

- Keep event/tourism economic-impact queries.
- Keep real-estate and licensing/works queries.
- Jobs queries need stronger city/public-source anchors.
- Budget/revenue queries need separate "economic impact" vs "municipal finance"
  dimensions.
- Add `pernambucanos` to the ISS exclusion list.
