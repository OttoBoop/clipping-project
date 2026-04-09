---
name: clipping
description: Rodar pipeline de clipping — coletar noticias, exportar painel e publicar no GitHub Pages. Use quando o usuario quiser atualizar o clipping, coletar noticias, ou publicar o painel.
user-invocable: true
argument-hint: "rapido | completo | custom"
---

# Pipeline de Clipping

Voce e o operador do pipeline de clipping politico. Seu trabalho e guiar o usuario pelas etapas de coleta, exportacao e publicacao.

## Referencia

Leia `docs/PIPELINE.md` para detalhes completos sobre coletores, candidatos e comandos.

## Fluxo

### Passo 1: Perguntar parametros

Use AskUserQuestion para perguntar os 4 parametros em UMA unica chamada:

**Pergunta 1 — Candidatos** (header: "Candidatos")
- "Flavio Valle" (default, dia a dia)
- "Circulo principal (Flavio + Angelito + Rubiao)"
- "Todos (inclui Pedro Duarte)"
- Other (usuario especifica)

**Pergunta 2 — Coletores** (header: "Coletores")
- "Todos exceto direct scrape (Recomendado)"
- "Somente Google News + RSS (rapido)"
- Other (usuario especifica quais)

**Pergunta 3 — Periodo** (header: "Periodo")
Calcule as datas com base na data de hoje usando `date` no Bash ANTES de mostrar as opcoes.
- "Hoje + ontem" (date-from=ontem, date-to=hoje)
- "Fim de semana (sexta a hoje)" — so mostrar essa opcao se hoje for segunda ou terca
- "Ultima semana (7 dias)"
- Other (usuario especifica datas)

**Pergunta 4 — Acao pos-coleta** (header: "Publicar")
- "Atualizar GitHub Pages (Recomendado)" — exporta + commit + push
- "Somente coletar (sem exportar)" — so roda ingestion
- "Exportar relatorio customizado" — pergunta escopo especifico depois

### Passo 2: Executar coleta

Para cada candidato selecionado, rodar:

```bash
python run_ingestion.py all \
  --target <TARGET_KEY> \
  --date-from <DATE_FROM> \
  --date-to <DATE_TO> \
  --skip-direct-scrape
```

Se o usuario escolheu coletores especificos, substituir `all` pelo nome do coletor.

Mostrar progresso em tempo real. Se houver multiplos candidatos, rodar sequencialmente (um por vez).

### Passo 3: Reportar resultados da coleta

Apos cada `run_ingestion.py`, ler o output e reportar:
- Quantos artigos foram inseridos
- Quantas mencoes encontradas
- Quantas historias tocadas
- Erros (se houver)

### Passo 4: Exportar e publicar (se selecionado)

Se o usuario escolheu "Atualizar GitHub Pages":

```bash
python tools/export_mobile_snapshot.py --all-stories --merge-from index.html
```

IMPORTANTE: o `--merge-from index.html` e OBRIGATORIO. Ele mergeia os dados novos do banco com os dados historicos ja publicados no Pages (incluindo artigos de Pedro Angelito, Bernardo Rubiao e Pedro Duarte que nao estao no banco SQLite). Sem isso, so os dados do banco sao exportados e os historicos sao perdidos.

Verificar o output — deve mostrar stories, artigos e targets.

Depois:

```bash
git add assets/ index.html data/reports/
git commit -m "clipping: atualização <DATE_FROM> a <DATE_TO>"
git push origin master
```

Reportar o link: https://ottoboop.github.io/clipping-project/

### Passo 5: Resumo final

Mostrar resumo com:
- Candidatos coletados
- Periodo
- Artigos novos inseridos
- Link do painel (se publicado)

## Atalhos

Se `$ARGUMENTS` for "rapido" ou estiver vazio:
- Candidatos: Flavio Valle
- Coletores: todos exceto direct scrape
- Periodo: hoje + ontem
- Acao: atualizar GitHub Pages
- **Pular as perguntas e executar direto** (mostrar os parametros usados antes de rodar)

Se `$ARGUMENTS` for "completo":
- Candidatos: circulo principal
- Coletores: todos exceto direct scrape
- Periodo: ultima semana
- Acao: atualizar GitHub Pages
- **Pular as perguntas e executar direto**

Se `$ARGUMENTS` for "custom" ou qualquer outra coisa:
- Fazer todas as perguntas do Passo 1
