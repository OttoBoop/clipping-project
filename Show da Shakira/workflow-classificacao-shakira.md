# Workflow de Classificação de Notícias — Show da Shakira

## Visão Geral

Este documento guia agentes Claude Code na análise e classificação de centenas de notícias sobre o show da Shakira. A arquitetura é bottom-up: cada artigo recebe uma análise individual rica (narrativa + classificação por tema), escrita num documento compartilhado. Loops posteriores de agregação descobrem os grandes eixos temáticos e geram relatórios.

**Regra fundamental:** cada artigo é analisado individualmente, um por vez, com atenção total. Não há processamento em lote. Subagentes podem trabalhar em paralelo, mas cada subagente processa apenas um artigo por vez.

---

## Estrutura de Arquivos

Todos os outputs ficam na pasta `Análise Show Shakira/` na raiz do repositório `Clipping-project`:

```
Análise Show Shakira/
├── analise-individual.md      ← documento compartilhado (Etapa 1)
├── consolidacao-temas.md      ← output da Etapa 2
└── relatorios/                ← outputs da Etapa 3
    ├── relatorio-geral.md
    └── [um .md por grande tema]
```

---

## Etapa Pré-0 — Convocação da Persona Loop-Runner

> Adicionada 2026-05-06 por Penelope+Iris. Esta etapa só é necessária quando o
> loop vai rodar autônomo, longo, e sem supervisão humana ativa. Para um run
> supervisionado curto, pode ser pulada.

### Objetivo

Antes de começar a tecer, garantir que existe uma identidade nomeada
responsável pelo loop, com claims registrados no canal vivo
(`md documents/Who_Is_Doing_What-WRITE_WHAT_YOU'RE_DOING_HERE.md`) e um
character sheet que outros agentes (e Otávio, ao revisar) possam consultar.

### Por que isso importa

Loops longos sem supervisão correm dois riscos: (a) o agente desviar do plano
porque ninguém está olhando, e (b) a perda de contexto se a sessão for
interrompida e outro agente precisar continuar. Uma persona nomeada com
character sheet escrito mitiga ambos: o agente atual sabe exatamente que
disciplina lhe foi confiada, e o sucessor (humano ou IA) tem um documento de
referência para retomar.

### Tarefas

1. Confirmar que a persona apropriada existe em `md documents/`. Para o
   arquétipo "executor cíclico de plano pré-escrito", a persona é **Penelope**
   (`md documents/PENELOPE_CHARACTER_SHEET.md`). Para outros arquétipos
   (auditor, fix-implementer, orquestrador), consultar
   `md documents/ORCHESTRATORS_FRAMEWORK_FOR_THE_CLIPPING_PROJECT.md`.
2. Se a persona não existir, criar o character sheet seguindo o padrão de
   Ariadne/Iris/Penelope (epígrafe mitológica + identidade + regra
   principal + protocolos + ownership).
3. Registrar a convocação no canal vivo:
   - §1 AGORA: linha nova com a persona ativa, atividade, data início,
     "aberto pra colab?" geralmente "não — loop autônomo".
   - §2 Claims: claims sobre os arquivos/pastas que o loop vai modificar.
   - §5 Log: entrada datada explicando o que/por que/qual plano.
4. Identidade híbrida: declarar a stack completa que está rodando (ex.
   `Penelope + Iris + CC (Opus 4.7)`) — útil para auditoria post-mortem.
5. Commitar este pré-passo como unidade lógica antes de começar a Etapa 0.

### Checkpoint

Persona convocada e canal vivo atualizado. Não esperar aprovação humana se
Otávio já autorizou o run autônomo na conversa que deu origem ao loop.

---

## Etapa 0 — Reconhecimento da Base de Dados

### Objetivo

Descobrir como os artigos estão armazenados no repositório e documentar o método de acesso. O site `clipping-project.onrender.com` é alimentado por uma base de dados no GitHub. O agente deve investigar a estrutura do repositório para entender:

### Tarefas

1. Clonar o repositório `Clipping-project`.
2. Explorar a estrutura de diretórios e arquivos.
3. Identificar: em que formato os artigos são armazenados (JSON, CSV, .md, banco SQLite, etc.), quais campos existem (título, fonte, data, URL, texto bruto, etc.), como os artigos são indexados ou nomeados, e quantos artigos existem no total.
4. **Escrever as descobertas na seção abaixo**, preenchendo o template.
5. Criar a pasta `Análise Show Shakira/` e o arquivo `analise-individual.md` com o cabeçalho inicial.

### Descobertas da Base de Dados

> **Preenchido em 2026-05-06 por Penelope (sessão Penelope+Iris+CC).**
> **Status:** descobertas técnicas completas via leitura de código; **bloqueio
> operacional** identificado para acessar a fonte de dados real (Shakira) — ver
> seção dedicada abaixo.

#### Arquitetura de armazenamento (em ordem de "verdade")

A base de dados real do projeto é **dual**:

1. **SQLite no disco do Render** (`data/clipping.db`) — fonte primária de
   ingestão. Schema definido em `pipeline/database.py` (linhas 23–122).
   Tabelas relevantes para o show da Shakira:
   - `articles(id, url, title, source_name, source_type, published_at,
     discovered_at, snippet, full_text, raw_html, summary, metadata)` — uma
     linha por URL única.
   - `mentions(id, article_id, target_key, target_name, keyword_matched,
     sentiment, sentiment_reason, context)` — N×M; um artigo pode mencionar
     vários targets, e um target pode ter várias mentions. `target_key` =
     `"shakira"` filtra os relevantes.
   - `stories(id, title, summary, temperature, created_at, updated_at)` —
     agrupamento de artigos similares.
   - `story_articles(story_id, article_id)` e `story_targets(story_id,
     target_key)` — tabelas de junção.
2. **Snapshot estático** (`assets/clipping-data.json` +
   `assets/clipping-raw-texts.json`) — exportado periodicamente por
   `tools/export_mobile_snapshot.py` a partir do SQLite. É o que o **site
   público** (`https://clipping-project.onrender.com/` e a versão GitHub Pages
   `https://ottoboop.github.io/clipping-project/`) consome diretamente. É o
   formato **mais conveniente para iterar** durante a análise — não exige
   conexão com SQLite, é JSON puro, já pré-processado.

A Etapa 0 e 1 deste workflow devem usar **o snapshot JSON**, não consultas
diretas ao SQLite. O snapshot é a versão "publicada", sem campos internos
ruidosos.

#### Formato de armazenamento (snapshot JSON)

**`assets/clipping-data.json`** — dicionário top-level com chaves:

```
meta:           dict (totalStories, totalArticles, generatedAt, etc.)
targets:        list[Target]   # alvos monitorados ativos
defaultTargets: list[str]      # alvo selecionado por padrão na UI
stories:        list[Story]    # núcleo do payload
```

**Story (objeto):**

| Campo | Tipo | Descrição |
|---|---|---|
| `storyIdInt` | int | ID interno da story |
| `title` | str | Título representativo da história agrupada |
| `summaryLabel` | str | Rótulo do tipo de resumo ("Resumo IA", "Sem resumo", etc.) |
| `summaryText` | str | Texto do resumo (curto) |
| `temperature` | float | Pontuação interna (não relevante para análise temática) |
| `articleCount` | int | Quantos artigos a história agrupa |
| `aiCount` | int | Quantos têm summary IA |
| `rawCount` | int | Quantos só têm texto bruto |
| `firstPublishedAt` | str (ISO) | Data do artigo mais antigo na história |
| `lastPublishedAt` | str (ISO) | Data do mais recente |
| `targetKeys` | list[str] | Chaves de alvos cujas histórias entram no agrupamento |
| `articles` | list[Article] | Os artigos agrupados |

**Article (objeto, dentro de `story.articles`):**

| Campo | Tipo | Descrição |
|---|---|---|
| `articleId` | int | ID único do artigo (chave primária no SQLite) |
| `title` | str | Título do artigo |
| `url` | str | URL original |
| `sourceName` | str | Nome do veículo/fonte conforme registrado no pipeline |
| `sourceHost` | str | Host do domínio (ex. `tupi.fm`) |
| `publishedAt` | str (ISO 8601) | Data de publicação |
| `publishedDisplay` | str | Data formatada para UI (ex. `"12/04/2026 11:45 UTC"`) |
| `targetKeys` | list[str] | Alvos que este artigo individualmente menciona (após safe-surface check) |
| `summaryLabel` | str | "Resumo IA", "Resumo simples", "Sem resumo" |
| `summaryPreview` | str | Preview do resumo (truncado) |
| `summarySource` | str | `"ai"` ou `"preview"` |
| `rawTextKey` | str \| null | Chave para buscar texto bruto em `clipping-raw-texts.json` (ex. `"article-602"`); pode ser `null` para artigos sem texto extraído |

**`assets/clipping-raw-texts.json`** — `dict[str, str]`. Chaves no formato
`"article-{articleId}"`, valores são o texto bruto do artigo (já com markup
HTML removido, mas com algum boilerplate de menu/navegação preservado).
Tamanho típico do arquivo: ~17 MB no estado pós-Shakira.

#### Quantidade total de artigos (target shakira)

Otávio confirmou: **119 artigos** na base de produção sob o target
`"shakira"`, no momento desta documentação (2026-05-06). Esse número pode ter
crescido se o pipeline rodar novamente antes do início da análise; o agente
deve recontar via `len([a for s in stories for a in s.articles if 'shakira'
in a.targetKeys])` ao iniciar.

(O snapshot atualmente comitado em `assets/clipping-data.json` é de
13/04/2026 17:28 UTC e tem 0 artigos Shakira — predates o adicionamento do
target `shakira` ao sistema. Ver seção "Bloqueio operacional" abaixo.)

#### Como iterar pelos artigos

Pseudocódigo de iteração (para o Etapa 1 loop):

```python
import json

with open("assets/clipping-data.json") as f:
    payload = json.load(f)
with open("assets/clipping-raw-texts.json") as f:
    raw_texts = json.load(f)

shakira_articles = []
seen = set()
for story in payload["stories"]:
    if "shakira" not in (story.get("targetKeys") or []):
        continue
    for article in story.get("articles") or []:
        if "shakira" not in (article.get("targetKeys") or []):
            # artigo está numa story tagueada Shakira mas o artigo
            # individual não passou no safe-surface — incluir mesmo assim
            # no escopo (regra do plano: "fora de escopo" recebe bloco
            # com classificação N/A).
            pass
        aid = article["articleId"]
        if aid in seen:
            continue
        seen.add(aid)
        shakira_articles.append({
            "id_artigo": f"a-{aid}",
            "title": article["title"],
            "url": article["url"],
            "source": article["sourceName"],
            "source_host": article["sourceHost"],
            "published": article["publishedDisplay"],
            "raw_text": raw_texts.get(article.get("rawTextKey") or "", "")
                        or article.get("summaryPreview") or "",
            "story_title": story["title"],
            "story_id": story["storyIdInt"],
            "in_strict_shakira_scope": "shakira" in (article.get("targetKeys") or []),
        })

# `shakira_articles` é a lista canônica de iteração para a Etapa 1.
```

**ID do artigo no `analise-individual.md`:** usar o formato `a-{articleId}`
(ex. `a-626`). É estável, único e bate com o ID interno do SQLite e com a
chave do raw-texts.

#### Como acessar o texto bruto

Para um artigo específico:

1. Ler `article.rawTextKey` do snapshot. Se `null`, usar `summaryPreview` +
   `title` como fallback (texto pobre, mas é o que existe).
2. Se não-null, buscar `raw_texts[rawTextKey]` em `clipping-raw-texts.json`.
3. O texto vem com algum boilerplate (cabeçalhos de menu, navegação) — é
   responsabilidade do agente classificador identificar e descartar
   boilerplate na hora de produzir o resumo narrativo.

#### Observações relevantes

1. **Filtragem secondary-target safe-surface**: o pipeline (em
   `pipeline/ingest.py`) filtra mentions de targets secundários (`shakira` é
   secundário) para que só apareçam quando o nome aparecer no título ou nos
   primeiros 500 caracteres do snippet/summary/full_text. Histórias que só
   mencionam Shakira em "Notícias relacionadas" / "Veja também" / "Leia mais"
   foram explicitamente removidas (regra adicionada no commit `bb6218e`
   2026-05-05). Isso significa que os 119 artigos esperados já vêm pré-
   filtrados — o agente provavelmente vai encontrar muito poucos
   "Artigo fora de escopo" durante o loop, porque o pipeline já fez essa
   filtragem.
2. **Resumos IA pré-existentes**: cerca de 33 artigos no banco têm
   `summaryLabel="Resumo IA"`; os demais têm `summaryPreview` mais curto
   gerado por preview. O agente pode usar o resumo IA como ponto de partida,
   mas a Etapa 1 exige resumo narrativo *novo*, focado nos temas (não no
   conteúdo geral) — não copiar o resumo IA verbatim.
3. **Datas**: `publishedAt` é UTC ISO. O escopo da mission Shakira (per
   `md documents/05-05-26-Iris-Shakira goals.md`) é `01/04/2026` a
   `05/05/2026`. Artigos fora dessa janela podem aparecer no snapshot
   (backfill de história mais antiga) — analisar mesmo assim, marcar a data
   no bloco. O plano não exige filtro temporal na Etapa 1.
4. **Cleanup post-export**: histórias antigas tagueadas como "stale shakira"
   foram removidas via `web_app/db_admin.py:cleanup_false_backfilled_target_mentions`
   no sprint Atlas em curso. O snapshot de produção atual reflete esse
   cleanup. Não é necessário re-filtrar em Penelope-side.

#### Bloqueio operacional 2026-05-06

> **Importante para qualquer Penelope/agente que retomar este loop.**

A Penelope **não** conseguiu acessar os dados Shakira nesta sessão. Causa
raíz:

1. O sandbox cloud do Claude Code (proxy `host_not_allowed`) recusa egress
   para `*.onrender.com` e `*.supabase.co`. Bloqueia `curl`, `httpx` e
   `WebFetch`. Bug upstream aberto — `anthropics/claude-code#52982` (ver
   commit `b9c5b43` na branch `claude/fix-clipping-website-access-JmfDJ` que
   tentou allowlist via `.claude/settings.json` e descobriu que o proxy
   gerenciado ignora a config user-side).
2. Os arquivos comitados no repo (`assets/clipping-data.json` +
   `assets/clipping-raw-texts.json`) são da geração **13/04/2026 17:28 UTC**,
   anteriores ao adicionamento do target `shakira`. Têm 0 artigos Shakira.
3. Não há repo/branch alternativo conhecido com snapshot Shakira-enriched.

**Caminhos de remediação (qualquer um destes desbloqueia):**

- **(a)** Otávio (ou Atlas) faz um dump do `data/clipping.db` do Render OU
  exporta `assets/clipping-data.json`+`assets/clipping-raw-texts.json` da
  Render disk e comita no repo. Penelope retoma na sessão seguinte. Mais
  simples, mais durável, e não depende de fix do sandbox.
- **(b)** Anthropic resolve o issue `#52982` ou Otávio configura egress
  via Render-side proxy em domínio whitelisted. Improvável short-term.
- **(c)** Otávio ativa um runtime alternativo (Claude Code local em
  máquina dele, ou ambiente sem o egress proxy gerenciado) onde a Penelope
  rodaria o loop com acesso direto a `clipping-project.onrender.com`.

**Q-NNN registrada em** `Who_Is_Doing_What-WRITE_WHAT_YOU'RE_DOING_HERE.md`
§4 (Q-008) com esses três caminhos enumerados como opções.

**Checkpoint:** Etapa 0 está documentada e pronta. Quando o bloqueio for
resolvido (qualquer um dos caminhos a/b/c), a próxima Penelope retoma
direto na Etapa 1 sem precisar refazer Etapa 0 — o método de iteração já
está completo aqui.

---

## Etapa 1 — Análise Individual de Artigos

### Objetivo

Produzir uma análise rica e granular de cada artigo, escrevendo todas as análises sequencialmente no arquivo compartilhado `Análise Show Shakira/analise-individual.md`.

### Protocolo de Coordenação entre Subagentes

O arquivo `analise-individual.md` é compartilhado entre subagentes. Para evitar que dois subagentes analisem o mesmo artigo:

1. **Antes de começar** a analisar um artigo, o subagente DEVE inserir imediatamente no final do arquivo:

```markdown
---
## [ID_DO_ARTIGO] — EM ANDAMENTO
**Subagente:** [identificador]
**Início:** [timestamp]
```

2. **Antes de escolher** qual artigo analisar, o subagente DEVE ler o arquivo `analise-individual.md` e verificar quais IDs já aparecem (tanto "EM ANDAMENTO" quanto concluídos). Escolher apenas artigos que ainda não constam no documento.

3. **Ao concluir** a análise, o subagente substitui o bloco "EM ANDAMENTO" pelo bloco completo de análise (formato abaixo).

4. Se um bloco permanecer "EM ANDAMENTO" por mais de 10 minutos, outro subagente pode assumir aquele artigo — removendo o bloco antigo e recomeçando.

### Formato de Cada Bloco de Análise

Cada artigo analisado deve gerar um bloco com exatamente esta estrutura:

```markdown
---
## [ID_DO_ARTIGO] — [Título do Artigo]

**Fonte:** [nome do veículo]
**Data:** [data de publicação]
**URL:** [link original]

### Resumo Narrativo

[Um a três parágrafos contextualizados descrevendo o que o artigo aborda, em tom
explicativo. Capturar o enquadramento do artigo, os pontos centrais, e a "história"
que ele conta. Não usar bullet points — escrever em prosa corrida.

Exemplo de tom: "O artigo destaca a infraestrutura como ponto crítico do evento,
apontando filas de mais de duas horas para entrada e falta de banheiros químicos
como as principais reclamações dos presentes, enquanto elogia a qualidade sonora
do show em si."]

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| [nome curto, ex: "filas de entrada"] | [frase descrevendo o posicionamento do artigo] | [muito negativo / negativo / neutro / positivo / muito positivo] |
| [próximo tema] | [...] | [...] |

### Classificação Geral

**Sentimento geral do artigo:** [muito negativo / negativo / neutro / positivo / muito positivo]
```

### Instruções para o Loop

1. Usar o método de acesso documentado na Etapa 0 para obter a lista de todos os artigos.
2. Ler o arquivo `analise-individual.md` para saber quais artigos já foram analisados ou estão em andamento.
3. Selecionar o próximo artigo não analisado.
4. Registrar "EM ANDAMENTO" no documento (ver protocolo acima).
5. Ler o texto completo do artigo.
6. Produzir a análise no formato especificado.
7. Escrever o bloco completo no documento, substituindo o bloco "EM ANDAMENTO".
8. Repetir até que todos os artigos tenham sido analisados.

**Se um artigo não tiver relação com o show da Shakira**, escrever o bloco com o resumo "Artigo fora de escopo — não trata do show da Shakira" e classificação "N/A". Não pular o artigo silenciosamente.

**Progresso:** a cada 20 artigos concluídos, reportar ao usuário quantos já foram processados e quantos faltam.

---

## Etapa 2 — Consolidação de Temas

### Objetivo

Percorrer todas as análises individuais em `analise-individual.md` e produzir uma consolidação temática em `Análise Show Shakira/consolidacao-temas.md`.

### Tarefas

1. Ler todo o arquivo `analise-individual.md`.
2. Extrair todos os temas que apareceram nas tabelas de "Temas Identificados".
3. Agrupar temas similares em categorias maiores (ex: "filas de entrada", "banheiros", "acessibilidade" → categoria "Infraestrutura do Evento").
4. Para cada tema e cada categoria, calcular:
   - Quantos artigos mencionam o tema.
   - Distribuição de classificação (quantos muito negativos, negativos, neutros, positivos, muito positivos).
5. Produzir o documento com:
   - Lista de categorias temáticas com seus temas constituintes.
   - Ranking dos temas mais frequentes.
   - Ranking dos temas mais elogiados.
   - Ranking dos temas mais criticados.
   - Distribuição geral de sentimento (todos os artigos).

### Formato do Documento

```markdown
# Consolidação Temática — Show da Shakira

## Sumário Quantitativo

- Total de artigos analisados: [N]
- Artigos fora de escopo: [N]
- Distribuição geral de sentimento: [tabela]

## Categorias Temáticas

### [Nome da Categoria]

**Temas agrupados:** [lista dos temas individuais que compõem esta categoria]
**Frequência:** aparece em [N] artigos ([X]% do total)
**Distribuição de sentimento:**
| Muito Negativo | Negativo | Neutro | Positivo | Muito Positivo |
|---|---|---|---|---|
| N | N | N | N | N |

**Síntese narrativa:** [parágrafo explicando como essa categoria aparece na cobertura]

[repetir para cada categoria]

## Rankings

### Temas mais frequentes
[ranking]

### Temas mais elogiados
[ranking]

### Temas mais criticados
[ranking]
```

**Checkpoint:** apresentar a consolidação ao usuário antes de prosseguir aos relatórios.

---

## Etapa 3 — Relatórios Temáticos

### Objetivo

Produzir relatórios narrativos aprofundados para cada grande categoria temática, além de um relatório geral.

### Para cada categoria temática

Gerar um arquivo em `Análise Show Shakira/relatorios/[nome-da-categoria].md` contendo:

1. **Resumo narrativo do tema:** como ele aparece na cobertura midiática, quais os pontos de elogio e crítica, como diferentes veículos o enquadram.
2. **Dados quantitativos:** frequência, distribuição de sentimento, evolução ao longo do tempo (se as datas permitirem).
3. **Trechos representativos:** referências curtas a artigos específicos que exemplificam posicionamentos distintos (identificados pelo ID do artigo).
4. **Conclusão:** síntese do que a cobertura midiática revela sobre esse aspecto do evento.

### Relatório Geral

Gerar `Análise Show Shakira/relatorios/relatorio-geral.md` com:

1. Panorama da cobertura: volume, período, principais veículos.
2. Os grandes temas e como se relacionam.
3. O que foi mais elogiado e mais criticado, em termos gerais.
4. Tendências observadas.
5. Conclusão geral sobre como a mídia cobriu o show da Shakira.
