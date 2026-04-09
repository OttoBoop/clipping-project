# Pipeline de Clipping — Guia Operacional

## Visao geral

O clipping monitora noticias sobre candidatos politicos do Rio de Janeiro. A pipeline coleta artigos de multiplas fontes, agrupa em historias, e publica um painel interativo no GitHub Pages.

## Fluxo diario tipico

```
1. Coletar artigos   →  run_ingestion.py (todos os coletores exceto direct_scrape)
2. Exportar para Pages →  export_mobile_snapshot.py --all-stories
3. Publicar           →  git add + commit + push
```

## Candidatos monitorados

| Candidato | Key | Circulo | Notas |
|-----------|-----|---------|-------|
| Flavio Valle | `flavio_valle` | Principal | Vereador, foco do monitoramento |
| Pedro Angelito | `pedro_angelito` | Principal | |
| Bernardo Rubiao | `bernardo_rubiao` | Principal | |
| Pedro Duarte | `pedro_duarte` | Externo | Aparece em "Outros candidatos" no painel |

Config: `data/targets.json`

## Coletores disponiveis

| Coletor | Comando | Fontes | Notas |
|---------|---------|--------|-------|
| RSS | `rss` | 21 feeds (Globo, Folha, UOL, R7, etc) | Rapido, ~30 ultimas por feed |
| Google News | `google_news` | Google News RSS | Amplo, resolve redirects |
| WordPress API | `wordpress_api` | 6 sites (Diario do Rio, Agenda do Poder, etc) | Paginacao profunda |
| Busca interna | `internal_search` | O Globo, G1, Veja Rio, Camara, Conib, Extra | API Globo + HTML parsing |
| Sitemap diario | `sitemap_daily` | 5 sitemaps Globo + CBN + Veja Rio | Cobertura completa por dia |
| Arquivo Veja Rio | `vejario_archive` | Colunas Lu Lacerda + Adriana Camargo | Paginacao de arquivo |
| Arquivo Camara | `camara_archive` | camara.rio/comunicacao/noticias | Paginacao de noticias |
| Direct scrape | `direct_scrape` | 10 sites (busca HTML) | **Prototipo, nao usar por padrao** |

## Comandos de referencia

### Coleta diaria (hoje + ontem)

```bash
python run_ingestion.py all \
  --target flavio_valle \
  --date-from $(date -d yesterday +%Y-%m-%d) \
  --date-to $(date +%Y-%m-%d) \
  --skip-direct-scrape
```

### Coleta segunda-feira (sexta a segunda)

```bash
python run_ingestion.py all \
  --target flavio_valle \
  --date-from $(date -d "last friday" +%Y-%m-%d) \
  --date-to $(date +%Y-%m-%d) \
  --skip-direct-scrape
```

### Coleta para multiplos candidatos

Rodar uma vez por target:

```bash
for target in flavio_valle pedro_angelito bernardo_rubiao; do
  python run_ingestion.py all \
    --target $target \
    --date-from 2026-04-08 \
    --date-to 2026-04-09 \
    --skip-direct-scrape
done
```

### Exportar e publicar no GitHub Pages

```bash
# Regenera data.json mergeando banco + dados historicos ja publicados
# O --merge-from index.html e OBRIGATORIO para manter dados de todos os targets
python tools/export_mobile_snapshot.py --all-stories --merge-from index.html

# Commit e push
git add assets/ index.html data/reports/
git commit -m "clipping: atualização $(date +%Y-%m-%d)"
git push origin master
```

### Coleta paralela (mais rapida, para backfills)

```bash
python tools/run_parallel_non_direct_ingestion.py \
  --target flavio_valle \
  --date-from 2026-04-01 \
  --date-to 2026-04-09 \
  --max-workers 12
```

## Notas tecnicas

### Deduplicacao
- A pipeline deduplica por URL ao inserir no banco (constraint UNIQUE)
- O export deduplica por URL entre stories (cada URL aparece em no maximo 1 story)
- Artigos sem URL sao mantidos mas raros

### Historias agrupadas
- Depende de analise de similaridade semantica (titulo/resumo)
- Sem IA ativa, o agrupamento usa heuristica lexica
- No painel, "Historias agrupadas" mostra os grupos; "Mais recentes" mostra artigos individuais

### Performance do painel
- Artigos carregam em batches de 50 (load-more button)
- Historias agrupadas tambem carregam em batches de 50
- Raw texts carregam sob demanda (clipping-raw-texts.json, ~17MB)
- DOM limpo ao trocar de view para evitar acumulo de memoria

### GitHub Pages
- URL: https://ottoboop.github.io/clipping-project/
- Deploy: push para master, GitHub Pages serve `index.html` + `assets/`
- Arquivos: `index.html` (shell 4KB), `assets/clipping-data.json` (~1.3MB), `assets/clipping-raw-texts.json` (~17MB)
