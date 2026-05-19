# Rio Economic Manual Review Queue - 2026-05-18

_Created by Atlas/Codex during the segregation product loop._

This is the operator-facing queue for the eight Rio economic stories that are
not automatically countable in:

```text
data/reports/rio_economic_topic_report_20260519T020159Z.json
data/reports/rio_economic_manual_approvals_v0.json
```

It does not approve or promote any row. It translates the sidecar state into a
human review checklist so a future operator can decide whether a row remains
research-only or receives a logged promotion.

## Current Counts

```text
story_count=25
article_count=31
canonical_rows_checked=31
count_current_period=17
manual_review_before_counting=1
research_only=7
manual_approval_status_counts:
  not_required=17
  not_reviewed=8
target_row_approved=false
writes_production_db=false
writes_assets_payload=false
writes_targets_json=false
```

## Review Rules

- Only `same_day` rows count automatically.
- `near_date` rows require explicit human approval before counting.
- `date_mismatch`, `canonical_date_missing`, and `fetch_error` rows stay
  research-only unless a reviewer records trustworthy source/date evidence.
- A promotion must be recorded in an approval artifact or operator log with:

```text
reviewer
reviewed_at
story row
original Google News date
canonical/source URL
observed source date or reason date is trustworthy
decision
rationale
```

- Do not edit generated report output alone to promote a row.
- Do not add a production `rio_economico` target row because this queue exists.

## Queue

| Story Row | Dimension | Current Policy | Date Status | Default Decision | Evidence To Check | Promotion Risk |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | tourism_events | research_only | canonical_date_missing | keep_research_only | Open `https://www.abcdoabc.com.br/mais-de-70-dos-quartos-de-hotel-do-rio-estao-reservados-para-o-carnaval` and record an explicit source date if present. Compare with Google News date `2026-05-17T23:29:28+00:00`. | Counting without source date may turn an undated tourism item into a false current-period signal. |
| 5 | tourism_events | research_only | date_mismatch | keep_research_only | Compare Google News date `2026-05-03T07:00:00+00:00` with canonical source date `2025-04-08T19:08:39+00:00` at `https://inmagazine.ig.com.br/musica/show-de-lady-gaga-em-copacabana-promete-espetaculo-grandioso-e-forte-impacto-economico`. | High risk; source date points to 2025 while Google News points to 2026. Keep out of current-period count unless a human finds clear updated-source evidence. |
| 11 | jobs_income | manual_review_before_counting | near_date | manual_review_before_counting | Open `https://jcconcursos.com.br/noticia/empregos/prefeitura-do-rio-de-janeiro-inscricoes-abertas-para-2867-vagas-em-novo-seletivo-142707`. Compare Google News date `2026-05-19T17:13:38+00:00` with canonical source date `2026-05-20T08:45:01+00:00`. | Medium risk; this is the only row that may plausibly count after manual approval of the one-day difference. |
| 15 | jobs_income | research_only | fetch_error | keep_research_only | Resolve the Google News URL from the generated report or re-run canonical fetch for the ABIH-RJ item. Record canonical URL and source date if fetch succeeds. | Fetch failure means the system has no independent source/date evidence. |
| 19 | construction_real_estate | research_only | canonical_date_missing | keep_research_only | Open `https://veja.abril.com.br/coluna/real-estate/a-nova-onda-de-investimentos-no-mercado-imobiliario-do-rio-de-janeiro` and record an explicit source date if present. Compare with Google News date `2026-05-12T19:17:16+00:00`. | Real-estate story may be useful research, but current-period counting needs date evidence. |
| 22 | municipal_finance | research_only | fetch_error | keep_research_only | Resolve the Google News URL from the generated report or re-run canonical fetch for the Prefeitura ISS/turismo item. Record canonical URL and source date if fetch succeeds. | Fetch failure blocks trustworthy date evidence even if the topic is highly relevant. |
| 25 | municipal_finance | research_only | canonical_date_missing | keep_research_only | Open `https://www.camara.rio/comunicacao/noticias/3094-fazenda-apresenta-resultados-do-ultimo-quadrimestre-de-2025-em-audiencia-publica-na-camara-do-rio` and record an explicit source date if present. Compare with Google News date `2026-04-28T18:31:05+00:00`. | City-finance content is relevant, but no date means it cannot feed a time-series indicator yet. |
| 26 | municipal_finance | research_only | canonical_date_missing | keep_research_only | Open `https://www.camara.rio/comunicacao/noticias/2979-fazenda-presta-contas-a-camara-do-rio-sobre-o-2-quadrimestre-de-2025-do-poder-executivo` and record an explicit source date if present. Compare with Google News date `2025-12-04T08:00:00+00:00`. | Relevant background, but likely old period material; keep outside current-period indicator until reviewed. |

## Suggested Operator Order

1. Review row 11 first. It is the only `near_date` row and the only row that
   may become current-period countable without overriding a harder failure.
2. Review rows 22, 25, and 26 next because municipal-finance signal is central
   to a Rio economic product.
3. Review rows 1, 5, and 19 as research enrichment, not headline indicator
   candidates.
4. Re-run canonical fetch for rows 15 and 22 before any manual promotion.

## Current Decision

```text
approved_promotions=0
rows_remaining_not_reviewed=8
target_row_approved=false
```

The Rio panel may show the automatic count and the existence of pending review,
but it must not present these eight rows as counted economic signal until a
human approval artifact exists.
