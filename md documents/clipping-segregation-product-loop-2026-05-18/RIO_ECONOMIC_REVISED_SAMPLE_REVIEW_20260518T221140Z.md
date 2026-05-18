# Rio Economic Revised Sample Review - 20260518T221140Z

_Created 2026-05-19 by Atlas/Codex._

This is a title-level review of the first sample produced from the revised
query JSON. It remains outside production ingestion.

Source artifacts:

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

## What Improved

- `impacto economico` tourism queries find clearly relevant megaevent/tourism
  stories.
- `mercado imobiliario` is much better than broad `construcao civil`.
- `licenciamento obras` finds concrete city enforcement/building items.
- `ambulantes comercio` finds city commerce-management stories.

## Remaining Pollution

- `state_not_city`: Rio das Ostras and Rio Grande still appear.
- `national_macro_only`: federal tourism/jobs items still appear.
- `ambiguous_city`: "cidade" without explicit Prefeitura/Cidade do Rio source
  can point to another municipality.
- `source_noise`: broad web/news sources sometimes outrank local city sources.

## Next Query Revision Ideas

Test negative terms and stronger source anchors:

```text
"Rio de Janeiro" "ocupacao hoteleira" -"Rio das Ostras"
"cidade do Rio" comercio local -"Rio Grande"
"Rio de Janeiro" vagas emprego Prefeitura -"Porto Velho"
"Prefeitura do Rio" ISS -"Pernambuco"
"Prefeitura da Cidade do Rio de Janeiro" "impacto economico"
"Câmara Municipal do Rio de Janeiro" comercio
"Diário do Rio" "mercado imobiliário"
```

## Title Exclusion Follow-Up

After adding `exclude_title_terms` to the revised query JSON, a filtered sample
was generated:

```text
data/reports/rio_economic_dry_run_20260518T221521Z.json
row_count=26
queries_file=data/reports/rio_economic_revised_queries_20260518.json
```

The obvious title/source-string pollutants checked in that run were absent:

```text
Rio das Ostras=0
Rio Grande=0
Porto Velho=0
portovelho=0
Pernambuco=0
```

## Product Decision

Do not add `rio_economico` to `data/targets.json` yet. The methodology is now
testable and producing useful rows, but it still needs query cleanup before it
becomes an automated client/project feed.
