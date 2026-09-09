# Operação do clipping político

**Autorização vigente:** o usuário já autorizou implantar, migrar o acervo e executar os coletores reais para **todos os 25 nomes**, desde **01/06/2026 até a data da execução, inclusive, no fuso America/Sao_Paulo**. Essa autorização persiste nas continuações; não pedir nova confirmação para o mesmo trabalho. Testes locais, simulações e preparação de código não substituem a entrega do acervo real atualizado.

O workspace Render confirmado é `tea-d5ruvqu3jp1c73dudl7g`. O serviço web existente é `srv-d7p2p5beo5us739f9k40`; o PostgreSQL existente é `dpg-d9b8e3favr4c73bkuht0-a`. Ainda não há worker político implantado. A [auditoria real inicial](BASELINE_PRODUCAO_2026-09-09.md) confirmou 12.902 artigos, 13.028 associações e 2.330 artigos no recorte de publicação; a publicação mais recente é de 30/06/2026. **Esta execução ainda adicionou 0 artigos novos em produção**. Não interpretar esse zero como o tamanho do acervo anterior.

O health público consultado em **09/09/2026** respondeu HTTP 200, com `rioCorpus.configured=false`, armazenamento habilitado e sem campo `politicalCorpus`. **O acesso SSH agora está confirmado:** a nova chave já foi aceita pelo Render e está persistida em `~/.ssh/clipping_render_ed25519`, com alias `clipping-render`; não há cadastro de chave pendente. A consulta remota `pwd` retornou `/opt/render/project/src`.

A auditoria inicial foi concluída por leitura somente de consulta. O SQLite legado está em `data/clipping.db`. Um backup consistente incluindo WAL foi baixado, descomprimido e verificado por SHA-256 e `PRAGMA integrity_check`, preservando também as duas classificações. O manifesto está em `/home/otavio/Documents/vscode/clipping-live-operations/2026-09-09/predeploy-backup-manifest.json`; SHA-256: `6b223c3cc086de6ceb5a4a993ee74b5ffa0807890987f8c584332edca13276f3`. Este backup anterior à implantação não substitui o snapshot final após bloquear e drenar escritores.

As variáveis de PostgreSQL ainda não estão configuradas no serviço web; as variáveis de Supabase estão presentes. A CLI Render está instalada persistentemente em `~/.local/bin/render`; o login foi autorizado pelo usuário e validado por `render whoami`, com configuração protegida em `~/.render/cli.yaml`. O workspace já confirmado foi selecionado. A primeira tentativa terminou com erro OAuth `slow_down`; o fluxo seguinte respeitou o intervalo e persistiu o login. Não solicitar novo cadastro SSH nem nova autorização para o mesmo trabalho enquanto esses acessos continuarem válidos. Não registrar chave privada, tokens ou credenciais nesta pasta.

## Preparação do ambiente

O [Blueprint](../../render.yaml) declara o serviço web, PostgreSQL e `clipping-political-worker`. O worker político não tem cron: processa tarefas criadas por solicitações explícitas. O cron do acervo geral do Rio é um serviço legado separado.

| Configuração | Uso |
|---|---|
| `POLITICAL_DATABASE_URL` | Conexão PostgreSQL no web, worker e importador. O código aceita `RIO_CORPUS_DATABASE_URL` como fallback; preferir a variável política explícita. |
| `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | Acesso do servidor ao armazenamento de corpos de artigos e backups. Configurar como segredos, sem incluí-los em logs ou comandos versionados. |
| `SUPABASE_BUCKET` | Bucket de armazenamento; o padrão do código é `documentos`. Conferir o bucket efetivamente usado pelo ambiente. |
| `CLIPPING_STORAGE_PREFIX` | Prefixo comum no web/worker/importador; Blueprint: `clipping-project`. |
| `POLITICAL_DASHBOARD_DEFAULT=0` | Manter o painel legado como entrada padrão até completar importação e canários. A página `/politica` continua disponível para verificação autenticada. |
| `CLIPPING_DB_PATH` | Caminho do SQLite legado real, quando diferente de `data/clipping.db`. Conferir antes de executar a importação. |

Preservar os segredos de autenticação e os arquivos de perfis existentes. Após a restauração de artefatos, a inicialização mescla o manifesto político antes de normalizar os nomes: arquivamentos, aliases e edições persistidas prevalecem. Confirmar isso no ambiente de destino e verificar acesso de administrador, perfil autorizado, perfil não relacionado e simulação somente leitura.

Depois da configuração e implantação, conferir `/healthz`, `/api/political/meta` e `/api/political/status` com sessão válida onde necessário. O health público usa `check_database=False`: `configured=true` indica presença de URL, não comprova conexão, migração ou worker saudável. Uma consulta autenticada real e o heartbeat em `status.workers` complementam essa verificação.

## Snapshot imutável e importação

Executar os comandos a partir da raiz do repositório, no ambiente com banco e armazenamento de destino configurados. Os caminhos abaixo pressupõem que o SQLite real foi confirmado em `data/clipping.db`; adaptar somente esse caminho se o ambiente usa outro. O nome `--source-key` identifica permanentemente o escopo dessa importação.

Primeiro lote:

```bash
python tools/political_import_sqlite.py \
  --sqlite data/clipping.db \
  --snapshot data/backups/political_import/rj-2026-09-09.db \
  --source-key legacy_political_20260909 \
  --all-political-targets \
  --batch-size 100 \
  --once
```

O comando executa esta sequência antes de importar artigos:

1. Abre o SQLite original somente para leitura e usa a API de backup do SQLite, incluindo dados confirmados no WAL. Cria um arquivo consistente, verifica `PRAGMA integrity_check` e registra SHA-256, tamanho e contagens no manifesto ao lado do snapshot.
2. Reutiliza o mesmo snapshot nas retomadas. Mudança no hash, origem diferente ou WAL com conteúdo no snapshot interrompe a operação; não substitui silenciosamente o arquivo congelado.
3. Comprime os bytes desse arquivo e envia uma nova geração de backup para `<prefix>/political/import-backups/<sha256>/<uuid>/legacy.sqlite.gz`. Cada execução usa UUID novo, preservando as gerações anteriores.
4. Baixa e descomprime a geração enviada, verifica o SHA-256 dos bytes recuperados e grava o manifesto remoto `.source.json`. Falha de upload, leitura, hash ou manifesto bloqueia o início dos lotes PostgreSQL.
5. Importa até 100 artigos por transação, preservando o conteúdo original, associações, IDs legados e classificações. Corpos ficam no armazenamento de objetos; o snapshot conserva o HTML legado. O checkpoint PostgreSQL permite continuação.

Guardar a primeira linha JSON emitida, especialmente `backup.sha256` e `remoteBackup`, junto à execução operacional. `--once` pode retornar sucesso com `hasMore=true`: isso significa que o primeiro lote terminou, não que a migração esteja concluída.

Conferidos o primeiro lote e seus registros, retomar com **o mesmo snapshot, source-key e conjunto de nomes**; remover apenas `--once`:

```bash
python tools/political_import_sqlite.py \
  --sqlite data/clipping.db \
  --snapshot data/backups/political_import/rj-2026-09-09.db \
  --source-key legacy_political_20260909 \
  --all-political-targets \
  --batch-size 100
```

`--all-political-targets` inclui a lista de 25 pessoas e os quatro nomes políticos originais, inclusive arquivados; dois desses quatro já pertencem à lista. A importação preserva matérias anteriores a junho, pois o recorte de novas buscas não elimina o acervo. Perfis e nomes de outros assuntos seguem no arquivo legado. Para um escopo específico, repetir `--target <chave>` em vez de usar `--all-political-targets`; manter a mesma lista ao retomar. Escopos diferentes exigem outro `--source-key` e snapshot próprio.

Exigir no último resultado `hasMore=false`, `validation.ok=true`, todos os contadores `dangling*` iguais a zero e igualdade das contagens e identidades esperadas/importadas de artigos, menções, classificações, histórias e suas associações. Conferir também `validation.snapshotSha256` e `validation.remoteBackup`, que vinculam o checkpoint ao backup verificado; outro snapshot com o mesmo `source-key` deve ser rejeitado. A deduplicação pode juntar registros canônicos; a validação usa os mapas de IDs originais para comprovar preservação. Conferir amostras de notícias antigas e recentes, notícias com vários nomes, classificações, categorias e textos. Não iniciar novas coletas antes dessa conferência.

## Worker e acionamento manual

O processo supervisionado é:

```bash
python tools/political_worker.py
```

Ele mantém dois consumidores de descoberta/revisão e quatro de extração, com limites globais no PostgreSQL, leases de 180 segundos e renovação periódica. Um sinal de encerramento solicita parada; tarefas interrompidas podem ser retomadas por leases e checkpoints. `python tools/political_worker.py --once` faz uma iteração por tipo de consumidor e é útil para inspeção limitada; não cria uma coleta e não garante esvaziar a fila.

Em `/politica`, selecionar nomes, informar datas e clicar em **Buscar novas notícias** ou **Revisar notícias salvas**. Consultar, trocar filtros ou recarregar a página não cria trabalho. Fechar o navegador não cancela o job. Acompanhar a fila, métricas e fontes pendentes; usar **Cancelar coleta** ou **Retomar coleta** explicitamente quando necessário. Revisão adiciona associações ausentes sem apagar classificações anteriores.

## Canários de cobertura e qualidade

A anotação em `data/political_known_stories_v1.json` contém 14 artigos públicos de oito publicadores, incluindo uma fonte partidária, além de cinco controles sintéticos de homônimos. Ela cobre os cinco nomes pedidos e os oito adversários, mas não mede todo o universo de veículos nem os 25 nomes com a mesma profundidade.

Validar o conjunto localmente, sem banco ou coleta:

```bash
.venv_playwright/bin/python tools/political_quality_check.py \
  --validate-only --output /tmp/political-quality-pending.json
```

Esse sucesso valida anotações e controles sintéticos; não aprova as métricas do acervo. Os comandos seguintes são somente leitura no PostgreSQL configurado, não inicializam esquema e não fazem buscas. Em produção, usar `python` do ambiente no lugar do interpretador local se necessário.

1. Solicitar na interface uma coleta real de **09/08/2026 a 09/08/2026**, dia com artigo anotado, selecionando **todos os 25 nomes**. Conferir data própria das matérias, nomes, URLs canônicas, corpo disponível e cada fonte com falha ou saturação.
2. Após a conclusão, executar:

```bash
python tools/political_quality_check.py \
  --date-from 2026-08-09 --date-to 2026-08-09 \
  --output /tmp/political-quality-canary-day.json
```

3. Somente após corrigir os problemas do dia, solicitar uma coleta real de **09/08/2026 a 15/08/2026**, novamente com **todos os 25 nomes**. Executar:

```bash
python tools/political_quality_check.py \
  --date-from 2026-08-09 --date-to 2026-08-15 \
  --output /tmp/political-quality-canary-week.json
```

4. Exigir, nos casos anotados, recuperação de artigos ≥90%, recuperação de associações corretas de pessoas ≥90% e associações incorretas ≤5%. Os controles sintéticos devem passar separadamente. O checker retorna `0` para os critérios aprovados, `1` para falha e `2` para banco indisponível ou ausência de casos anotados no período. Um período sem exemplos não demonstra cobertura.
5. Revisar também os estados de fontes e janelas em `/api/political/coverage`: resultados vazios não verificados, limites, bloqueios e falhas são pendências explícitas. Avaliar a proporção de texto integral e erros de datas apresentada no relatório; aprovação das três métricas de associação não comprova qualidade do corpo nem cobertura total.
6. Depois dos canários, executar o intervalo já autorizado de **01/06/2026 até a data da execução, inclusive, em America/Sao_Paulo**, com **todos os 25 nomes**. Ao concluir, medir o conjunto anotado completo:

```bash
python tools/political_quality_check.py \
  --output /tmp/political-quality-full-window.json
```

Os relatórios sempre deixam `production_rollout_verified=false`: o comando mede apenas casos anotados. Publicadores não representados exigem inspeção própria. A validação de implantação também depende da migração, dos perfis, da estabilidade e da observação remota de consumo.

## Critérios de conclusão da execução real

- Levantar e guardar o inventário inicial remoto antes da migração: artigos, menções, histórias, classificações e vínculos, com identificação do snapshot e backup recuperável. Enquanto essas contagens forem desconhecidas, não afirmar que o acervo foi preservado ou ampliado.
- Implantar web e worker no workspace confirmado, conectar o PostgreSQL e o armazenamento e verificar acesso autenticado, heartbeat e consultas reais. Concluir a importação com seus validadores e preservar as classificações, os perfis e os registros anteriores.
- Executar os dois canários reais com os 25 nomes, corrigir os problemas encontrados e depois processar integralmente o período autorizado. Registrar IDs dos jobs, nomes selecionados, datas locais, fontes/janelas consultadas e checkpoints; iniciar um job não equivale a concluir sua coleta.
- Acompanhar os trabalhos até o estado final, retomar falhas recuperáveis e revisar lacunas, limites e fontes bloqueadas. Medir os critérios anotados no banco de produção e conferir uma amostra de URLs, publicações, texto e associações. Distinguir ausência verificada de resultados de consulta incompleta.
- Entregar as contagens finais e o acréscimo real em relação ao inventário inicial, por nome e fonte quando disponível, distinguindo artigos únicos, associações, duplicatas, referências sem corpo e falhas. Confirmar no site a leitura e classificação dos registros coletados e informar eventuais lacunas remanescentes com evidência.

Continuar o trabalho já autorizado enquanto essas etapas não estiverem cumpridas. Um relatório sintético aprovado, um deploy isolado ou 0 artigos novos sem investigação não demonstra a conclusão solicitada. Se o acesso continuar indisponível, registrar o obstáculo técnico e o trabalho pendente sem apresentar a coleta como concluída.

## Exportação estática separada

O painel mostra artigos confirmados diretamente do PostgreSQL. A publicação estática continua sendo uma operação explícita e separada. Para preparar uma exportação política em **diretório novo**, com os nomes selecionados:

```bash
python tools/political_static_export.py \
  --output-dir /tmp/clipping-politico-export-20260909 \
  --target eduardo_paes --target flavio_valle \
  --date-from 2026-06-01 --date-to 2026-09-09
```

O comando é somente leitura no banco e não envia arquivos, altera permissões nem substitui os artefatos publicados. Repetir `--target` para os demais nomes desejados. Cada página contém no máximo 100 associações de notícias, usa o formato/renderer existente e preserva IDs políticos em um espaço numérico separado dos IDs legados. `manifest.json` distingue artigos únicos, associações e páginas; histórias compartilhadas mantêm seus vínculos. Busca e filtros do HTML se aplicam à página aberta.

Acrescentar `--include-text` para salvar corpos em arquivos individuais, carregados sob demanda. O padrão mantém metadados e classificações; não rotula trechos como texto integral. Conferir `manifest.status`, `text_failures` e `text-failures.jsonl` quando existir antes de publicar. Uma execução falha deixa o manifesto com estado explícito; repetir a exportação em outro diretório novo.

Para revisar os arquivos localmente:

```bash
python -m http.server 8765 --bind 127.0.0.1 --directory /tmp/clipping-politico-export-20260909
```

Abrir `http://127.0.0.1:8765/`. O comando prepara um artefato para o mecanismo de publicação escolhido; não publica automaticamente nem incorpora outros perfis ou os arquivos legados.

## Ativação e acompanhamento

Manter `POLITICAL_DASHBOARD_DEFAULT=0` até obter: execução final dos testes, migração validada, canários de dia/semana aprovados, conferência de perfis e classificações, backup recuperável e métricas remotas aceitáveis. Depois dessas verificações, alterar a flag para `1` torna `/politica` a entrada padrão de perfis políticos autorizados com banco configurado. O arquivo anterior continua em `/?view=legacy`.

O [benchmark local](validation/political-scale-benchmark.json) passou com 100.000 artigos, mas usou fontes e armazenamento simulados. Durante os canários medir memória do web e worker, p95 de consultas, crescimento de objetos, backlog, heartbeat e taxas de falha por fonte. Não converter o resultado local em garantia de throughput ou ausência de crashes no serviço remoto.

## Interrupção e reversão

Se houver regressão, voltar `POLITICAL_DASHBOARD_DEFAULT=0` e acessar `/?view=legacy`. **Essa flag altera a entrada do site; não cancela trabalhos.** Cancelar os jobs pela interface/API autenticada, aguardar confirmação ou interromper o worker pelo supervisor para impedir novos processamentos. Guardar IDs dos jobs, checkpoints, métricas e erros antes da análise.

Preservar PostgreSQL, objetos imutáveis e snapshots. O importador lê o SQLite original sem substituí-lo; o caminho legado permanece disponível. Não apagar tabelas nem restaurar um snapshot antigo sobre o banco político como resposta automática: classificações e artigos criados após a migração podem existir apenas no novo acervo. Fazer backup desses dados antes de qualquer restauração e avaliar compatibilidade de esquema antes de reverter a versão do aplicativo.

Para retomar importação interrompida, reutilizar o comando, snapshot e source-key originais. Para um job interrompido, corrigir a causa e usar a retomada explícita; validar os resultados antes de reativar a entrada padrão. Registrar a reversão e o novo resultado dos canários nesta pasta.
