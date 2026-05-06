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

> **Esta seção deve ser preenchida pelo agente após explorar o repositório.**

**Formato de armazenamento:** [a preencher]

**Campos disponíveis por artigo:** [a preencher]

**Quantidade total de artigos:** [a preencher]

**Como iterar pelos artigos:** [a preencher — descrever o método exato: ler linhas de um CSV, iterar por chaves de um JSON, listar arquivos de um diretório, etc.]

**Como acessar o texto bruto de cada artigo:** [a preencher — o caminho/campo exato que contém o conteúdo]

**Observações relevantes:** [a preencher]

**Checkpoint:** apresentar estas descobertas ao usuário e aguardar aprovação antes de prosseguir à Etapa 1.

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
