# Rio Economic Sample Review - 20260518T220725Z

_Created 2026-05-19 by Atlas/Codex._

This is a title-level triage of the first 32-row live Google News dry-run
sample. It is not approval to add a `rio_economico` row to `data/targets.json`.

Source artifact:

```text
data/reports/rio_economic_dry_run_20260518T220725Z.json
row_count=32
query_count=8
resolve_timeout=0
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

## Query-Level Triage

| Query | Early Read | Notes |
| --- | --- | --- |
| `"Rio de Janeiro" hotelaria` | mixed | Finds hotel/tourism sector signal, but several titles are national/luxury-market pieces where Rio may be incidental. |
| `"cidade do Rio" turismo` | useful but dirty | Finds Prefeitura/Diario do Rio items, but also nearby-city/state tourism and federal tourism items. |
| `"cidade do Rio" comercio` | mixed | Finds Invest.Rio and Camara commerce items, but also Mercosul and Rio Grande false positives. |
| `"Prefeitura do Rio" comercio` | useful but broad | Finds Shakira economic impact, ambulantes, Rio2C, and enforcement/building items; needs economic-substance labels. |
| `"Rio de Janeiro" emprego` | useful | Finds Rio jobs/vagas/economy items, with some national tourism labor noise. |
| `"Rio de Janeiro" construcao civil` | weak | Mostly national, state, salary, or non-city construction stories. Needs replacement. |
| `"Prefeitura do Rio" orcamento` | useful | Finds city budget and Prefeitura governance, though some items are not directly fiscal/economic. |
| `"municipio do Rio" arrecadacao` | mixed | Finds event impact and BNDES items, but also royalties/ICMS items that may be state-level or sector-specific. |

## Obvious False-Positive Patterns

- `state_not_city`: nearby cities or state-level Rio items without city signal.
- `national_macro_only`: national/federal stories where Rio is incidental.
- `too_generic`: broad construction, commerce, or tourism wording.
- `politics_no_economic_signal`: governance/personnel stories without budget,
  commerce, jobs, or local economic activity.

## Better Next Queries To Test

Replace or narrow the weak construction and state-prone terms:

```text
"Prefeitura do Rio" "licenciamento" obras
"cidade do Rio" "mercado imobiliario"
"Rio de Janeiro" "construcao civil" "Sinduscon"
"Prefeitura do Rio" ISS
"cidade do Rio" arrecadacao ISS
"Rio de Janeiro" vagas emprego Prefeitura
"Rio de Janeiro" "ocupacao hoteleira"
"Rio de Janeiro" "impacto economico" turismo
```

## Next Loop Step

Run a revised dry-run with these replacement queries or add a custom query-file
mode to the tool. Keep outputs under `data/reports/`; do not write
`clipping.db`, `assets/clipping-data.json`, or `data/targets.json`.
