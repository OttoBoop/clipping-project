# Implementação e validação

Aprovado: persistência durável em PostgreSQL com worker separado; novas coletas somente por acionamento manual; recorte a partir de 01/06/2026; pasta no projeto e grupos no site; revisão do acervo existente preservando classificações e permissões.

## Entregas locais

- [x] Manifesto versionado com 25 pessoas, grupos, partidos, papéis, fontes, aliases e data de verificação.
- [x] Preservação dos registros herdados e distinção entre seleção sugerida de coleta e nomes principais/protegidos.
- [x] Mesclagem idempotente após restauração de artefatos, sem reativação de registros arquivados.
- [x] Metadados disponíveis no carregamento `Target`, na normalização e nas APIs existentes de nomes.
- [x] Correspondência de frases com limites de palavras, insensível a acentos e pontuação; contexto para homônimos.
- [x] Revisão legada SQLite limitada a páginas por ID, com checkpoint e alterações na mesma transação; classificações existentes preservadas.
- [x] Testes de paginação/reinício, interrupção com rollback, idempotência, intervalos de datas, classificação e contexto.
- [x] PostgreSQL com tarefas duráveis de descoberta, extração e revisão; leases, retomada e limites de concorrência.
- [x] Worker separado, sem agendador político; o site consulta resultados confirmados enquanto a coleta continua.
- [x] Interface `/politica` com grupos, filtros e paginação; texto e classificação carregados por notícia, sem baixar o arquivo global.
- [x] Autorização por perfil, simulação somente leitura, CSRF, limite de corpo JSON de 2 MiB e snapshots de nomes construídos no servidor.
- [x] Importador com snapshot SQLite consistente, backup remoto imutável verificado por SHA-256 e lotes PostgreSQL de até 100 artigos.
- [x] Registro local de 15 fontes, descoberta paginada e sinalização de consultas incompletas.
- [x] Verificador de qualidade somente leitura sobre artigos anotados; controles sintéticos separados das métricas do acervo.
- [x] Exportação estática explícita do PostgreSQL, limitada a 100 artigos/associações por página, com classificações por escopo e texto individual opcional.
- [x] Morte real de processo durante extração e transação; rollback de banco, retomada de tarefa e continuidade de outra fonte validados.

A persistência política principal em PostgreSQL tem seu próprio fluxo de tarefas e revisão. O checkpoint SQLite descrito abaixo mantém o fluxo legado compatível; não substitui os checkpoints do worker PostgreSQL.

## Contrato dos nomes

Campos opcionais novos: `political_roster_version`, `group`, `group_label`, `role`, `party`, `verified_at`, `sources` (`url`, `note`), `preferred_for_political_run` e `match_context`. Este último contém `required_for`, `any_of`, `none_of`, `exempt_aliases` e `window_chars`.

`group` usa `requested`, `rio_psd`, `rio_governor_opponents`, `coalition_partners` ou `national_psd`. `preferred_for_political_run` vale `true` apenas para os cinco nomes solicitados. Os campos `primary`, `className`, `archived` e as permissões dos perfis mantêm suas funções anteriores.

## Revisão legada limitada

```python
backfill_missing_target_mentions(
    db_file, target_keys, *, batch_size=100, max_batches=1,
    sample_limit=20, rule_version="political_names_v1",
    date_from=None, date_to=None, reset=False,
)
```

- Cada chamada processa no máximo 100 artigos por página e 10 páginas; o padrão é uma página. Apenas trechos necessários à correspondência são lidos.
- O checkpoint em `target_review_progress` inclui hash das regras, nomes selecionados e intervalo. Regras ou escopos novos geram um checkpoint independente; `reset=True` recomeça explicitamente o mesmo escopo.
- A resposta mantém `updated`, `updatedCount`, `mentionsInserted` e `storiesTouched`. `updated` contém no máximo `sample_limit` exemplos; os totais são exatos para a chamada, não derivados do tamanho da amostra.
- Novos campos: `scannedCount`, `checkpointKey`, `cursor`, `hasMore`, `sampleTruncated`, `ruleVersion`. O worker continua enquanto `hasMore` for verdadeiro e verifica cancelamento entre chamadas.
- Datas opcionais filtram a publicação original. A data de descoberta não substitui uma publicação desconhecida. Sem datas, o acervo legado permanece revisável integralmente.
- Múltiplos nomes compartilham o mesmo artigo/história. O procedimento só adiciona associações ausentes e não reescreve texto, sentimento, classificação ou categorias já registrados.

## Verificação e implantação

A [execução final consolidada](validation/political-regression-summary.json), em 09/09/2026, terminou com **507 testes aprovados em 56,88 segundos**, sem falhas, erros ou testes ignorados. O [relatório JUnit](validation/political-regression-tests.xml) registra cada caso.

A suíte cobre autenticação e perfis, interface/API, controles de escopo, os coletores novos e legados, janelas de datas, homônimos, extração de corpo, paginação, cancelamento e retomada, PostgreSQL, snapshots/backup, migração, classificações, correções de fonte, exportação e avaliação de qualidade. Os testes PostgreSQL usaram um banco local descartável. Houve morte real de workers durante extração e durante uma transação ainda não confirmada; registros confirmados sobreviveram e tarefas retomadas foram concluídas sem associações parciais. Falha de transação e falhas de armazenamento foram injetadas separadamente.

O [teste de escala local](validation/political-scale-benchmark.json) usou 100.000 artigos e menções existentes, 25 nomes e 120 entradas novas, com latência simulada de 150 ms por extração. A fila PostgreSQL gravou as 120 entradas em 6,732 s contra 19,128 s no caminho legado: 2,842 vezes a vazão. Não faltaram associações de nomes/histórias; resultados confirmados ficaram visíveis antes do fim. O p95 HTTP foi 189,991 ms em 117 consultas; o pico de memória do processo foi 101,039 MiB, 19,734% da capacidade de referência de 512 MiB.

Esses números não medem provedores reais nem armazenamento remoto. O legado começou vazio; PostgreSQL começou com o acervo grande. O armazenamento de objetos era local, as requisições HTTP usaram ASGI TestClient, e a memória exclui o servidor PostgreSQL. Não há promessa de ganho idêntico em produção.

O [teste de navegador](validation/political-browser-smoke.json) passou em 1440×1000 e 390×844, com dados fictícios e rotas/autenticação reais em servidor local. Cobriu grupos, próxima/anterior, leitura sob demanda, classificação e troca de nome após salvar, datas, histórias, inclusão manual, métricas e iniciar/cancelar/retomar por clique. Foram 28 requisições em cada viewport, sem erro de console, erro de página ou rolagem horizontal. O cadastro da simulação arquiva Otto Alencar de propósito: 24 nomes aparecem ativos, sem alterar o manifesto real de 25.

A [verificação da exportação estática](validation/political-static-export-check.json) usou tabelas temporárias PostgreSQL e Chromium: 100 artigos únicos, 101 associações, duas páginas, classificações por escopo, nenhum corpo baixado antecipadamente e um arquivo individual ao abrir a notícia. Não houve chamadas de API nem erros do navegador; corpos compartilhados foram reutilizados sem falhas. Essa verificação também usa dados simulados e não publica arquivos.

Os screenshots permanecem em `/tmp/political-browser-smoke/` nesta sessão e não foram incorporados ao repositório. `tools/political_browser_smoke.py` os regenera; o JSON copiado preserva os caminhos originais como referência temporária.

- [x] Verificar interface desktop/mobile e limites de perfil localmente.
- [x] Executar benchmark controlado de escala e preservar seu relatório e limitações.
- [x] Consolidar a execução final de testes após os últimos ajustes: 507 aprovados.
- [ ] Resolver o workspace Render e conferir infraestrutura/credenciais do ambiente de destino.
- [ ] Importar o snapshot real, validar contagens e classificações e testar a retomada.
- [ ] Executar canários reais de um dia e uma semana, com revisão de cobertura e homônimos.
- [ ] Medir latência, memória, armazenamento, falhas e limites de fontes no ambiente remoto.
- [ ] Ativar `POLITICAL_DASHBOARD_DEFAULT=1` somente após os critérios do [roteiro operacional](OPERACAO.md).

**Estado de produção em 09/09/2026:** health público HTTP 200; `rioCorpus.configured=false`; armazenamento habilitado; `politicalCorpus` ausente. A escolha do workspace Render solicitada pelo conector permanece pendente. Nenhuma migração ou coleta remota foi realizada; o conector exige a confirmação do workspace de destino antes de acessar seus recursos. Os limites e testes reduzem riscos específicos, mas ausência de crashes em produção ainda não foi demonstrada.
