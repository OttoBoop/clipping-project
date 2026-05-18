# Rio Economic Source And Dimension Refinement

_Created 2026-05-18 by Atlas/Codex._

This note converts the 26-row title-label review into the next safe Rio
economic validation step. It does not approve a production `rio_economico`
target row.

## Decision

Split the current broad `budget_finance` bucket before another live sample:

- `municipal_finance`: ISS, arrecadacao, orcamento, tax forgiveness, fiscal
  incentives, official municipal revenue language.
- `economic_development`: Invest.Rio, Rio2C, business hubs, tourism/event
  economic impact, investment attraction, city business climate.

Reason: the cleaned sample had useful Rio economic items that were not really
ISS/revenue stories. Leaving them under `budget_finance` makes later scoring and
review confusing.

## Source Anchor Rules

Use a source anchor when the query is broad enough to catch national, state, or
non-city material.

Preferred source-anchor families:

- official city execution: `Prefeitura do Rio`, `Secretaria Municipal`,
  `Trabalho e Renda`, `Invest.Rio`, `SEOP`;
- city labor and public service: `Central do Trabalhador`, `SMTE`, `vagas no
  Rio`;
- local city press: `Diario do Rio`, `O Globo Rio`, `G1 Rio`, `Tempo Real RJ`,
  `Veja Rio`;
- city-place anchors: `Copacabana`, `Centro do Rio`, `Barra da Tijuca`,
  `Jacarepagua`, `Vidigal`, `Zona Sul`, `Zona Norte`, `Zona Oeste`, but only
  when the economic dimension is explicit.

Avoid treating these as enough by themselves:

- `Rio` without `cidade`, `município`, `Prefeitura`, or a clear city place;
- federal/national tourism or employment stories with incidental Rio mention;
- state government items unless they name city-of-Rio economic impact;
- events/celebrity stories without occupancy, commerce, jobs, investment, tax,
  or local business signal.

## Query Refinement For Next Dry-Run

Keep:

```text
"Rio de Janeiro" "ocupacao hoteleira"
"Rio de Janeiro" "impacto economico" turismo
"Prefeitura do Rio" ambulantes comercio
"Prefeitura do Rio" licenciamento obras
"cidade do Rio" mercado imobiliario
```

Refine:

```text
"Rio de Janeiro" vagas emprego Prefeitura
-> "Prefeitura do Rio" "vagas" "Trabalho e Renda"

"Rio de Janeiro" empregos turismo
-> "Rio de Janeiro" turismo empregos hotelaria

"Prefeitura do Rio" ISS
-> "Prefeitura do Rio" ISS arrecadacao

"cidade do Rio" arrecadacao ISS
-> "municipio do Rio" arrecadacao ISS
```

Add economic-development tests outside `municipal_finance`:

```text
"Invest.Rio" "Rio de Janeiro" empresas
"Rio2C" "impacto economico" "Rio de Janeiro"
"Prefeitura do Rio" "desenvolvimento economico"
```

## Review Labels To Preserve

Continue using:

```text
true_positive
useful_unclear
false_positive
unclear
```

Add these false-positive reasons to future reviews:

```text
dimension_mismatch
ambiguous_city
source_not_city_specific
official_quote_without_city_signal
```

## Promotion Gate

Do not add `rio_economico` to `data/targets.json` until a revised sample proves:

```text
at least 30 reviewed rows
municipal_finance and economic_development separated
jobs_income false positives reduced from title-level review
no broad query family dominates the useful rows
Flavio/Shakira production payloads remain isolated in live smoke
operator confirms collection cost is acceptable
```

If those checks pass, the first production attempt must still use a narrow date
window and post-run profile contamination checks.
