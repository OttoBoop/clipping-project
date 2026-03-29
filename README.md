
## Testing Set e Benchmarks

O oraculo de avaliacao do clipping e o Excel `Acompanhamento GVFV.xlsx` (aba `Assessoria de Imprensa`).

- Definicao e criterios do testing set: `TESTING_SET.md`
- Snapshot do status por fonte (verde/parcial/zerado/backlog): `CLIPPING CATALOGUE.md`

### Benchmark por fonte (vs Excel)

O runner principal grava `JSON` e `CSV` em `data/experiments/`.

Exemplo (testing set completo, por host):

```powershell
python tools\benchmark_sources_vs_excel.py `
  --hosts cbn.globo.com,agendadopoder.com.br,diariodorio.com,temporealrj.com `
  --start-date 2025-01-24 `
  --end-date 2026-02-26 `
  --budget-seconds 5400
```

Para fontes de sitemap muito grandes, existe um modo pratico para varrer apenas dias presentes no Excel:

```powershell
python tools\benchmark_sources_vs_excel.py `
  --hosts oglobo.globo.com,g1.globo.com,extra.globo.com `
  --modules sitemap_daily `
  --start-date 2025-01-24 `
  --end-date 2026-02-26 `
  --excel-days-only `
  --excel-day-padding 2 `
  --budget-seconds 5400 `
  --run-id globo_family_exceldays_pad2
```

### Diagnostico por URL (familia Globo)

Esse diagnostico nao faz discovery. Ele pega as URLs do Excel e classifica o que falha por:
`fetch_error`, `extractor_hit`, `extractor_loss_*` ou `site_content_gap`.

```powershell
python tools\globo_family_diagnostic.py `
  --start-date 2025-01-24 `
  --end-date 2026-02-26 `
  --hosts oglobo.globo.com,g1.globo.com,extra.globo.com
```