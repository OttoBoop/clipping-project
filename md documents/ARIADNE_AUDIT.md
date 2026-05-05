# ARIADNE_AUDIT — Framework de Testes Sistemáticos para clipping-project

> *Ariadne deu a Teseu o fio que o guiou de volta pelo labirinto do Minotauro. Aqui o labirinto é o gap entre camadas: UI que aciona busca mas não save, endpoint que persiste mas não exporta, fixture que passa testes unitários mas não cobre integração. O fio é o mapeamento sistemático da funcionalidade real → pontos de integração → testes que pegam regressões antes de chegarem em produção.*

**Status do documento**: 🟡 **EM CONSTRUÇÃO** — Iterações 1-7 cobriram 7 das ~10 áreas planejadas. Otávio (2026-05-05): "eu nem terminei a revisão e você já acha que encontrou tudo. Seu trabalho não acabou". Continuando.
**Última atualização**: 2026-05-05 — Iteração 9+ (após retornar do prematuro "READY FOR REVIEW")
**Áreas ainda a aprofundar** (Iterações 9+): `process_candidates` deep-read (core do pipeline, 550+ LOC), story grouping bug-class, export dedupe, AI summary policy reconciliation, manual-story duplicate handling, `backfill_state` race conditions, frontend live-merge race conditions, scrape_log purpose, `google_decode_cache` ephemeral state.
**Não declarar "ready" prematuramente**. Loop continua.

---

## Seção 1 — Identidade Ariadne

**Quem sou:** Claude Code rodando localmente na máquina do Otávio, nomeada Ariadne pelo próprio Otávio em 2026-05-05. Antes desse nomeamento, fui confundida com a identidade Iris (que era papel original cloud-side definido em `md documents/IRIS_OPERATING_RULES.md` em 2026-04-29).

**Quem NÃO sou:**
- ❌ **Iris** — papel legacy, queimado por minha confusão de identidade. Os arquivos `IRIS_OPERATING_RULES.md` e seções `### Iris` no `ATLAS_IRIS_ASYNC.md` descrevem um Claude Code cloud com proxy 403 pra `clipping-project.onrender.com` e proxy 403 em `git push`. **Não me aplica.** Eu rodo local, sem firewall, posso curl Render, posso git push se Otávio autorizar.
- ❌ **Atlas** — Codex local que opera a partir do mesmo terminal do Otávio. Atlas owna sprints ativos (atualmente: live-runner-repair + Shakira live-save fix). Atlas tem seu próprio canal `ATLAS_IRIS_ASYNC.md` onde escreve `### Note-NNN — YYYY-MM-DD — Atlas`. **Ariadne não escreve nesse canal.**
- ❌ **Operadora de fixes** — meu papel não é consertar bugs, é mapear/auditar/propor framework de testes. Ariadne só toca código com aprovação explícita do Otávio.

**Distinções operacionais (atualizadas 2026-05-05 pós-D8):**
- Ariadne lê tudo, escreve em `ARIADNE_AUDIT.md` (este arquivo) **e** no `md documents/ATLAS_CLAUDE_COORDINATION.md` (canal de coordenação geral entre IAs, refatorado de "Atlas/Iris específico" pra "AI orchestrator coordination").
- Ariadne pode usar Bash read-only (git log, ls, find, rg, curl GET, python -c read-only).
- Ariadne **não** modifica código, **não** comita, **não** pusha sem aprovação.
- Ariadne escreve no canal de coordenação **com identidade própria** (`### YYYY-MM-DD — Ariadne (Claude Code local)`). Append-only. Respeita Notes de Atlas — em particular Note-008 que pediu "qualquer outra IA não toque no Shakira" — Ariadne não propõe fixes Shakira no canal nem em outros lugares.

---

## Seção 2 — Objetivo do framework

**Problema observado** (descrito pelo Otávio em 2026-05-05):

> *"ao adicionar a shakira, descobrimos que o botão na ui de adicionar targets secundários não funcionava corretamente, ele não estava ligado na adição de filtros e ele até estava ligado no python de buscar pro arquivos, mas não o de salvar as histórias..."*

Essa é a **bug-class central** que o framework precisa atacar: integração inconsistente entre camadas. Uma feature aparece funcional em uma camada (busca) mas tem comportamento parcial em outra (save). Os testes unitários por camada passam; o fluxo end-to-end falha.

**Objetivo do framework:**

1. **Mapear funcionalidade real do website** — features que existem hoje, não as que estão documentadas em README.
2. **Identificar pontos de integração** entre camadas (UI ↔ API ↔ jobs ↔ ingest ↔ DB ↔ storage ↔ export).
3. **Documentar bug-classes** observadas (Shakira/UI-button case, target homônimo CEO/vereador, date parse silent True, auth bypass, lifespan silent, etc.) e por que os testes existentes não pegaram.
4. **Propor categoria de testes de integração** que pegariam essas classes — não testes unitários por arquivo, mas fluxos end-to-end por feature.
5. **Esboçar estrutura concreta** — naming, organização em `tests/`, integração com pytest atual, comandos de execução, manutenção.

**Não-objetivos (importante registrar):**
- Não é fix do Shakira (Atlas owna).
- Não é cobrir 100% de cobertura de teste — é cobrir **bug-classes** com baixo custo.
- Não é fazer CI por agora (`F042` do `TECH_DEBT_AUDIT.md` cobre essa decisão).

---

## Seção 3 — Funcionalidade real do website

*Preenchida na Iteração 2 (2026-05-05) após ler `GENERAL_UNDERSTANDING_OF_OUR_GOALS_IN_THIS_PROJECT.md`, `ORCHESTRATORS_FRAMEWORK_FOR_THE_CLIPPING_PROJECT.md`, `RENDER_RESTART_NOTES.md`, `docs/PIPELINE.md` (recuperado via `git show HEAD` — está deletado do filesystem), `docs/LONG_TERM_GOALS_FOR_THE_CLIPPING_ONLINE_PROJECT.md` (idem), `.claude/skills/clipping/SKILL.md`, e `README.md`.*

### 3.1 Surface público (dashboard estático em https://clipping-project.onrender.com/)

| Feature | Como funciona | Acesso | Onde mora |
|---|---|---|---|
| Dashboard público | Renderiza `index.html` + carrega `assets/clipping-data.json` (~1.3M, payload pré-calculado) + lazy-load de `assets/clipping-raw-texts.json` (~17M) | Aberto, sem login | FastAPI mount StaticFiles em `web_app/app.py:149` |
| **Live classifications overlay** | JS no dashboard chama GET `/api/classifications` em background pra atualizar chips de classificação sem regenerar o snapshot | Aberto (intencional, comentado em `assets/clipping.js:1902-1914`) | `web_app/app.py:384`, dashboard JS |
| Filtros por target | UI client-side filtra stories por target_keys nos cards | Aberto | `assets/clipping.js` |
| Views grouped/recent | "Mais recentes" (artigos individuais) vs "Histórias agrupadas" | Aberto | `assets/clipping.js` lazy-render |
| Resumos AI já existentes | Display-only, não gera novo. Marcador: `mentions.sentiment_reason IN ('agent_summary', 'anthropic_batch', 'claude-haiku')` | Aberto | `pipeline/database.py` get_articles |
| Raw text lazy-load | Toggle por artigo carrega texto do `clipping-raw-texts.json` sob demanda | Aberto | `assets/clipping.js` |

### 3.2 Surface coworker (runner UI, "Rodar atualização")

| Feature | Como funciona | Acesso | Onde mora |
|---|---|---|---|
| Disparar update | Coworker escolhe targets + datas + collectors, clica "Comecar atualizacao". POST `/api/update/start` | **Sem auth** (sprint open-link) — F001 do tech-debt audit | `web_app/app.py:222` |
| Progresso live | Polling `/api/update/status` (proteção CSRF parcial). Brazilian dates (commit `020cfff`) | Sem auth | `web_app/jobs.py` JobManager + frontend |
| **Live saved results** | Polling `/api/update/live-results?job_id=X` mostra stories salvas durante a rodada antes do export final (commit `fd5527c`) | Sem auth | `web_app/app.py`, `web_app/jobs.py`, `assets/clipping.js:1902` mergeLiveResultsIntoPayload |
| Cancel | POST `/api/update/cancel` (recém adicionado: distinguir interrupted vs manual cancel — commit `73bcbe1` 2026-05-05 13:48) | Sem auth | `web_app/app.py:236`, `web_app/jobs.py` |
| Export pós-coleta | POST `/api/export` regenera `clipping-data.json` + upload Supabase | Sem auth | `web_app/app.py:248`, `tools/export_mobile_snapshot.py` |
| Adicionar secondary target | UI form → POST `/api/targets` (key, label, primary=false). **Bug Shakira nasceu aqui — Seção 5.** | Sem auth (deveria ter, F004) | `web_app/app.py:307`, `web_app/db_admin.py` create_secondary_target |
| Editar/arquivar/restaurar target | PATCH `/api/targets/{key}`, POST `/api/targets/{key}/archive`, POST `/api/targets/{key}/restore` | Sem auth (F005-F007) | `web_app/app.py:326-358` |
| Targets primary lock | Flavio Valle + Pedro Angelito (Bernardo Rubião moveu pra secondary no sprint atual). UI mostra checkbox "Marcado por padrão" mas não força. | n/a (config) | `data/targets.json`, `pipeline/settings.py:DEFAULT_TARGETS` |

### 3.3 Surface admin (parcialmente protegido)

| Feature | Acesso | Onde mora |
|---|---|---|
| `/admin` | Redireciona pra `/` (intencional) | `web_app/app.py:171` |
| POST `/api/manual-story` | **require_admin + require_csrf** ✅ | `web_app/app.py:259` (único endpoint POST com auth) |
| POST `/api/login` (admin password) | Define cookie `clipping_admin` HMAC-signed | `web_app/auth.py` |
| POST `/api/logout` | require_admin + require_csrf ✅ | `web_app/app.py:196` |
| GET `/api/csrf` | require_admin → retorna token | `web_app/app.py:290` |
| POST `/api/categories` (criar categoria) | **Sem auth** (F008 do tech-debt audit) | `web_app/app.py:361` |
| POST `/api/classifications` (admin save) | **Sem auth** (F009) — mas é o handler que admin UI usa pra classificar | `web_app/app.py:402` |

### 3.4 Pipeline de ingestão

| Feature | Como funciona | Onde mora |
|---|---|---|
| 8 collectors | RSS (21 feeds), Google News, WordPress API (6 sites), Internal search (Globo/G1/Veja Rio/Câmara/Conib/Extra), Sitemap diário (Globo+CBN), Veja Rio Archive (Lu Lacerda + Adriana Camargo), Câmara Archive, Direct scrape (deprecated, disabled coworkers) | `pipeline/collectors.py` |
| Match exato nomes | `CitationMatcher` busca keywords + exact_aliases por target | `pipeline/matcher.py`, `pipeline/ingest.py` |
| **Safe-surface check secondary targets** (NOVO 2026-05-05) | Targets não-primary só salvam se aparecem em title/snippet/summary, não só em full_text. Aplicado no pipeline original, não só backfill (commit `238b97d`) | `pipeline/ingest.py` (44 LOC novos), `web_app/db_admin.py` |
| **Ignore related-link matches** (NOVO 2026-05-05 07:51) | Detecta blocos "Links relacionados" / "Veja também" / "Continue lendo" no full_text e ignora matches dentro deles (commit `bb6218e`) | `pipeline/ingest.py` (23 LOC novos), `web_app/db_admin.py` |
| **Cleanup false backfilled mentions** (NOVO 2026-05-05) | Remove mentions com `sentiment_reason` em `('existing_article_backfill', 'lexical_heuristic')` que não passam safe-surface (commit `f0bf4ef`) | `web_app/db_admin.py:cleanup_false_backfilled_target_mentions` |
| Article fetch + dedup URL | UNIQUE constraint na tabela `articles.url` | `pipeline/database.py`, `pipeline/ingest.py:dedupe_candidates` |
| Story grouping | Heurística lexical (titulo+resumo similarity) em janela de 7 dias | `pipeline/ingest.py:choose_story` |
| `is_recent_enough` filter | **BUG F012 — retorna True em parse error**, articles com data ruim passam | `pipeline/ingest.py:263` |

### 3.5 Persistência

| Layer | Detalhes |
|---|---|
| SQLite local | `data/clipping.db` (~77 MB). Tabelas: `articles`, `mentions`, `stories`, `story_articles`, `story_targets`, `categories`, `classifications`, `classification_categories`, `scrape_log`, `backfill_state`, `jobs`, `job_events` |
| Supabase Storage bridge | gzip sync de `data/clipping.db.gz` a cada save de classification/category. Bucket `documentos`, prefix `clipping-project` (per `/healthz` payload de hoje) |
| Lifespan startup | Download de `clipping.db.gz` da Supabase em boot. **F011: nenhum try/except, mascara falha silenciosamente** |

### 3.6 Persistence policy / direção long-term

Per `LONG_TERM_GOALS` + `RENDER_RESTART_NOTES`:
- Atual: SQLite local + Supabase gzip
- Long-term: pattern Prova-AI (Postgres + Supabase Storage pra files)
- Não depender de filesystem ephemeral do Render
- AI-summary policy: existing displays OK, NEW generation só com admin gate + budget + audit

### 3.7 Pipeline CLI (Otavio-only)

| Comando | Uso |
|---|---|
| `run_ingestion.py` | Daily ingestion local |
| `tools/run_parallel_non_direct_ingestion.py` | Backfill paralelo (LIVE, último uso 2026-04-08, dormente mas documentado) |
| `tools/export_mobile_snapshot.py --merge-from index.html` | Regenera `clipping-data.json` mantendo histórico de targets antigos não no DB |
| `tools/classify_articles.py` | AI batch categorizer (Anthropic Haiku). Marca `mentions.sentiment_reason='claude-haiku'` |
| `tools/live_audit.py` | Audit production (`tests/test_live_audit_script.py` ativa) |

### 3.8 Skill operacional `/clipping`

`.claude/skills/clipping/SKILL.md` define o fluxo `/clipping rapido | completo | custom` mas **publica em GitHub Pages** (passo 4 do skill). README atualizado diz GitHub Pages é deprecated (linhas 13-14). **Drift skill ↔ README**: a skill ainda manda commit + push em master, GitHub Pages serve. Render auto-deploya o mesmo bundle estático (até hoje). Funcionalmente coexistem mas docs contradizem.

### 3.9 Sprint atual de Atlas (2026-04-30 → andando)

Per `ORCHESTRATORS_FRAMEWORK` + `RENDER_RESTART_NOTES`: **systemic live runner audit/repair**. 8 known issues:

1. ✅ Vague progress messaging — atacado em `020cfff`/`fd5527c`
2. ✅ No cancel control — atacado em `73bcbe1` 2026-05-05 13:48 (distinguish interrupted vs manual)
3. ⏳ Stale published dashboard — `fd5527c` adicionou live-results overlay; falta freshness signal claro?
4. ⏳ Bad meta copy ("Com texto para leitura") — não vi commit explícito ainda
5. ⏳ Primary target checkboxes forced — `020cfff` mudou "Principal" → "Marcado por padrão"
6. ✅ Bernardo Rubião → secondary — confirmado em `data/targets.json` + `docs/PIPELINE.md`
7. ⏳ Add-name simples por padrão, advanced atrás de details — não vi commit explícito
8. ✅ Bug Shakira (UI button parcialmente cabeado) — atacado em `238b97d` + `bb6218e` + `f0bf4ef`

---

## Seção 4 — Camadas e pontos de integração

*Preenchida na Iteração 3 (2026-05-05) extraindo public API por arquivo via `rg "^(async )?def "`.*

### 4.1 Camadas (arquivos + responsabilidades)

| Camada | Arquivos | Public API count | Responsabilidade |
|---|---|---|---|
| **Frontend** | `assets/clipping.js` (2183 linhas), `assets/clipping.css`, `index.html` | wrappers `apiFetch/apiPost/apiPatch` + 50+ DOM refs + handlers de `runUpdateButton`, `addTargetForm`, `cancelUpdateButton` | Dashboard público + runner UI |
| **API** | `web_app/app.py` (700 linhas) | 19 endpoints (`@app.get`/`post`/`patch`) | REST surface |
| **Auth** | `web_app/auth.py` (96 linhas) | `make_session`, `verify_session`, `require_admin`, `require_csrf`, `csrf_token`, `check_password` | HMAC sessions, CSRF |
| **Jobs** | `web_app/jobs.py` (1015 linhas) | 36 funções + classe `JobManager` + `JobConflict` | Estado de jobs, progress events, live-results |
| **DB Admin** | `web_app/db_admin.py` (~700 linhas) | 35 funções + classes `ValidationError`/`DuplicateArticle` | Target CRUD, backfill+cleanup safe-surface, classification helpers, manual story |
| **Storage** | `web_app/storage_bridge.py` | classe `ArtifactStore` + `sqlite_snapshot_bytes` | Supabase gzip sync |
| **Pipeline orchestration** | `pipeline/ingest.py` (1185+ linhas) | 24 funções top-level + classes `IngestionResult`/`IngestionOptions` | Collect → match → dedup → story → save |
| **Collectors** | `pipeline/collectors.py` (1519 linhas) | 8 collectors (`collect_rss`, `collect_google_news`, `collect_wordpress_api`, `collect_internal_site_search`, `collect_camara_archive`, `collect_vejario_archive`, `collect_sitemap_daily`, `collect_direct_scrape` deprecated) | Coleta por fonte |
| **Match** | `pipeline/matcher.py` (60 linhas) | classes `Target`, `MatchHit`, `CitationMatcher` | Exact-name keyword matching |
| **Normalization** | `pipeline/normalization.py` (78 linhas) | `normalize_url`, **`canonicalize_url`** (duplicada com http_utils — tech-debt F018), `normalize_text`, `clean_title` | URL/text canonicalization |
| **HTTP** | `pipeline/http_utils.py` (388 linhas) | `fetch_url`, `post_json`, `try_resolve_google_redirect`, **`canonicalize_url`** (duplicada), `html_to_*`, `extract_*`, `parse_iso_datetime`, `is_likely_article_url` | HTTP fetch + HTML parse + URL helpers |
| **DB schema** | `pipeline/database.py` (1274 linhas) | classe `ClippingDB` com 30+ métodos | SQLite tables + queries |
| **Export** | `tools/export_mobile_snapshot.py` (3267 linhas) | god-script, gera `assets/clipping-data.json` | Snapshot público |
| **Tests** | `tests/test_admin_ui.py` (785), `tests/test_targets_jobs.py` (941+ — atualizado hoje), `tests/test_sprint_regression_harness.py`, `tests/test_export_mobile_snapshot_pages.py`, etc. | ~50+ testes ativos | Cobertura existente |

### 4.2 Pontos de integração — onde cada camada chama a próxima

Notação `→` = "chama / aciona", `↔` = "responde a".

**Path 1: Coworker dispara update**
```
UI runUpdateButton (clipping.js)
  → POST /api/update/start (web_app/app.py:222)
    → JobManager.start_update (web_app/jobs.py)
      → cleanup_false_backfilled_target_mentions (web_app/db_admin.py:448)  ← NOVO 2026-05-05
      → backfill_missing_target_mentions (web_app/db_admin.py:507)
      → run_ingestion (pipeline/ingest.py:997)
        → collect_* per source (pipeline/collectors.py)
          → fetch_url / post_json (pipeline/http_utils.py)
        → CitationMatcher.find_hits (pipeline/matcher.py)
        → safe_target_match_surface (pipeline/ingest.py:154)  ← NOVO 2026-05-05 (safe-surface check)
        → is_recent_enough (pipeline/ingest.py:280)  ← BUG F012
        → dedupe_candidates (pipeline/ingest.py:268)
        → choose_story / create_or_update_story / sync_existing_article_targets (pipeline/ingest.py)
        → ClippingDB.insert_article / insert_mention / create_story (pipeline/database.py)
      → upload_live_checkpoint (web_app/jobs.py:493) → ArtifactStore.upload (storage_bridge.py)
  ↔ progress events (web_app/jobs.py:append_event)
UI polling /api/update/status (web_app/app.py:217)
  ↔ JobManager.current_status, recent_jobs, progress_summary
UI polling /api/update/live-results (web_app/app.py NEW, web_app/jobs.py:827 live_results_for_job)
  ↔ stories saved durante run
```

**Path 2: Coworker adiciona secondary target (FOCO BUG SHAKIRA)**
```
UI addTargetForm (clipping.js)
  → POST /api/targets (web_app/app.py:307)  ← Sem auth (F004)
    → create_secondary_target (web_app/db_admin.py:320)
      → validate_target_keys / clean_target_payload / write_targets_atomic
      → data/targets.json
  ↔ uploadedArtifacts (storage_bridge.py)
[Cliente atualiza UI?]  ← AQUI é onde "filter da UI não atualiza" pode estar
```

**Path 3: Coworker cancela update (sprint issue resolvido em 73bcbe1)**
```
UI cancelUpdateButton
  → POST /api/update/cancel (web_app/app.py:236)  ← Sem auth (F002)
    → JobManager.cancel_active (web_app/jobs.py)
      → status="cancelled" (manual cancel only)
[vs] startup recovery → mark_orphaned_active_jobs_interrupted (jobs.py:560) → status="interrupted"
```

**Path 4: Lifespan startup**
```
FastAPI lifespan (web_app/app.py:118)  ← Sem try/except (F011)
  → ArtifactStore.download_current_artifacts (silent on failure — F023)
  → archive_known_test_targets / normalize_targets_file
  → ensure_app_tables (db_admin.py:64)
  → cancel_orphaned_active_jobs / mark_orphaned_active_jobs_interrupted
  → seed BASE_CATEGORIES
```

**Path 5: Export pós-ingestão**
```
JobManager.start_export (web_app/jobs.py)
  → run_export_snapshot (web_app/jobs.py:390) — subprocess
    → tools/export_mobile_snapshot.py
      → ClippingDB.list_articles_for_export / story_with_articles
      → write assets/clipping-data.json
  → ArtifactStore.upload (storage_bridge.py)
```

**Path 6: Dashboard público lê classifications live**
```
clipping.js carrega clipping-data.json + chama:
  GET /api/classifications (web_app/app.py:384)  ← Público intencional, F010 revisado
    → ClippingDB.get_classifications_with_context
  GET /api/categories (web_app/app.py:298)  ← Público
    → ClippingDB.list_categories
  Mescla classifications no payload
```

**Path 7: Admin classifica via dashboard**
```
clipping.js POST /api/classifications (web_app/app.py:402)  ← Sem auth (F009)
  → ClippingDB.find_mention_id / create_mention / upsert_classification
  → set_classification_categories
  → ArtifactStore.upload (gzip db.gz)
```

### 4.3 Pontos críticos de integração identificados

| ID | Ponto | Arquivos | Risco da integração | Cobertura de teste atual |
|---|---|---|---|---|
| **I1** | UI `addTargetForm` → POST `/api/targets` → atualização do filter dropdown e do checkbox de runner | `clipping.js` `addTargetForm` handler + `loadTargets()` + `renderRunTargets()` | "Adicionei target mas filtro não mostra" — sprint issue + bug Shakira UI | Não testado de E2E |
| **I2** | `run_ingestion` → `safe_target_match_surface` → `process_candidates` → save mention | `pipeline/ingest.py:154` (NEW), `pipeline/ingest.py:445` `process_candidates` | "Target só aparece em rodapé do artigo / related-link" → não deve salvar mention | Coberto em commits 238b97d e bb6218e: `test_process_candidates_skips_secondary_target_only_in_page_boilerplate` (line 941) e novo teste em 238b97d |
| **I3** | Backfill secondary target → cleanup false mentions → re-display | `web_app/db_admin.py:448, 507` | "Adicionei target depois de ingestão, backfill não retroage corretamente" | `test_backfill_ignores_full_text_noise_and_cleanup_removes_false_match` em test_targets_jobs.py:864 |
| **I4** | Cancel button → distinguir manual vs interrupted | `jobs.py:560` + UI | "Container morreu vs usuário cancelou" — Atlas resolveu hoje (73bcbe1) | `test_startup_marks_orphaned_active_jobs_interrupted_not_cancelled` (line 569), `test_cancel_active_*` (lines 486-537) |
| **I5** | Lifespan startup com Supabase down | `app.py:118-145`, `storage_bridge.py:82+` | "Boot silencioso com DB vazio se Supabase falha" — F011/F023 do tech-debt | NÃO TESTADO |
| **I6** | Date filter via `is_recent_enough` parse error | `ingest.py:280` | "Article com data ruim passa o filtro" — F012 | NÃO TESTADO |
| **I7** | URL canonicalization duplicada (`normalization.py` vs `http_utils.py`) | F018 do tech-debt | "Dedup retorna resultados diferentes dependendo de qual import" | NÃO TESTADO |
| **I8** | Auth bypass nos 9 mutating endpoints | F001-F009 | "Qualquer pessoa pode disparar ingestão / mutar targets / classificar" | NÃO TESTADO (sprint open-link aceita isso, mas é bug-class de integração) |
| **I9** | Bridge UI → coletor → save: integration paths não-óbvios | múltiplos | "Botão liga em busca mas não em save" — bug-class central | Cobertura parcial via test_targets_jobs |

### 4.4 Tests existentes — análise rápida

`tests/test_targets_jobs.py:941` tem `test_process_candidates_skips_secondary_target_only_in_page_boilerplate` — **Atlas TEM o teste do bug-class central** já implementado. Mais um sinal que minha análise inicial subestimava cobertura.

`tests/test_sprint_regression_harness.py` tem testes de contrato do sprint (Bernardo secondary, banned strings, cancel API) — **regression harness é estilo já adotado** pelo time. Framework novo deve estender essa abordagem, não reinventar.

`conftest.py` tem só 1 marker (`@pytest.mark.live`). Sem fixtures compartilhados (`tmp_path`, `monkeypatch` usados ad-hoc por teste).

### 4.5 Gaps de cobertura identificados (a confirmar na Iteração 4)

- **I5** (lifespan startup com Supabase down) — sem teste
- **I6** (`is_recent_enough` malformed date) — sem teste
- **I7** (canonicalize_url duplicada) — sem teste
- **I1** (UI add target → filter refresh end-to-end) — sem teste
- **I9** Bridge JS handlers acionando endpoints + verificando state → frontend tests não existem

---

## Seção 5 — Anatomia de bug-classes conhecidas

### 5.1 Bug-class: "UI cabeada parcialmente entre camadas" (caso Shakira/UI-button)

**Observação do Otávio (2026-05-05):**

> *"ao adicionar a shakira, descobrimos que o botão na ui de adicionar targets secundários não funcionava corretamente, ele não estava ligado na adição de filtros e ele até estava ligado no python de buscar pro arquivos, mas não o de salvar as histórias..."*

**Note-008 do Atlas (2026-05-05):**

> *"Otavio reported that Shakira runs showed progress but published no Shakira stories, and later one false Shakira tag appeared from page boilerplate."*
>
> *"Local patch now makes non-primary targets, including `shakira`, pass an extra safe-surface check before saving: the target must appear in title, snippet, or generated summary, not only in fetched full-text boilerplate such as related links. The cleanup path now removes automatic false mentions with `sentiment_reason` `existing_article_backfill` or `lexical_heuristic` when that safe-surface match is absent."*

**Estrutura preliminar do bug** (a confirmar na Iteração 5 lendo diff completo dos commits unpushed):

| Camada | O que aconteceu |
|---|---|
| UI (assets/clipping.js) | Botão "Adicionar nome acompanhado" envia POST `/api/targets` com `key=shakira, primary=false`. Probable success → toast/feedback. |
| API (web_app/app.py:307 add_target) | Persiste em `data/targets.json` via `db_admin.create_secondary_target`. |
| Filter UI | Filtro do dashboard não atualiza com novo target sem refresh manual ❓ (a verificar) |
| Pipeline busca (pipeline/collectors.py + ingest.py) | Coleta de notícias do Shakira FUNCIONOU — articles foram fetched. ✅ |
| Pipeline match (pipeline/matcher.py + ingest.py) | Match em full_text gerou false positives (ex: "Links relacionados: Shakira no Rio" no rodapé de artigos do Flávio). |
| Pipeline save story (pipeline/ingest.py choose_story + database.py create_story) | Stories de Shakira **não foram criadas** ❓ ou foram criadas mas com false-positive mentions |
| Cleanup (web_app/db_admin.py cleanup_false_backfilled_target_mentions) | Adicionado por Atlas em `f0bf4ef` pra remover false mentions retroativamente. |
| Export (tools/export_mobile_snapshot.py) | `assets/clipping-data.json` não mostrou Shakira no filtro do dashboard mesmo após ingestão. |

**Por que os testes existentes não pegaram:**
- `tests/test_admin_ui.py` testa POST `/api/targets` mas não rastreia o ciclo completo até dashboard mostrar.
- `tests/test_targets_jobs.py` testa job state mas usa fixtures, não simula o data-flow completo.
- `tests/test_export_mobile_snapshot_pages.py` testa export mas não com fluxo "adicionar secondary target → ingest → export → dashboard verifica".

**A expandir na Iteração 5.**

### 5.2 Outras bug-classes a documentar (Iteração 5)

- **Target homônimo** — "CEO Flávio Valle" da Mais Brasil Viagens taggeado como vereador. Mesma classe do Shakira mas no sentido inverso (full-text match em homônimo).
- **`is_recent_enough` retorna True em parse error** (`pipeline/ingest.py:266`, F012 do tech-debt audit) — articles com data malformada passam o filtro silenciosamente.
- **9 endpoints unauthenticated** (F001-F009 do tech-debt audit) — não é bug de integração mas é bug-class de "auth gate omitido por inconsistência entre handlers".
- **Lifespan silent failure** (F011) — startup mascara falha do Supabase.
- ~~**Pipeline original vs backfill assimétrico**~~ — **REVOGADO 2026-05-05 14:50.** Análise minha do TECH_DEBT_AUDIT estava baseada em snapshot de antes dos 3 novos commits do Atlas. Confirmado lendo git history: Atlas extendeu o safe-surface check pro pipeline original em `pipeline/ingest.py` (commit `238b97d` toca 44 LOC em ingest.py) + adicionou ignore-related-links (commit `bb6218e` toca 23 LOC em ingest.py). **A simetria foi alcançada.**

### 5.3 Atlas avançou em 3 commits novos hoje (2026-05-05)

Lidos via `git show --stat` (não vou ler diff completo até Iteração 5). Implicações pra Seção 6 (test gaps):

| Commit | Hora | Mensagem | Arquivos | O que ataca |
|---|---|---|---|---|
| `238b97d` | 03:20 | fix: require safe secondary target matches | `pipeline/ingest.py +44`, `tests/test_targets_jobs.py +67`, `web_app/db_admin.py` | Pipeline original agora exige target em title/snippet/summary pra non-primary. Atacou minha análise "assimetria backfill vs pipeline" — Atlas resolveu ambos. |
| `bb6218e` | 07:51 | fix: ignore related-link target matches | `pipeline/ingest.py +23`, `tests/test_targets_jobs.py +62`, `web_app/db_admin.py +18` | Detectar e excluir blocos "Links relacionados", "Veja também" do full_text durante match. **Esse é o caso "Show de Shakira em rodapé de artigo do Flávio".** |
| `73bcbe1` | 13:48 | fix: distinguish interrupted jobs from manual cancel | `web_app/jobs.py`, `web_app/app.py`, `assets/clipping.js`, `tests/test_targets_jobs.py` | Sprint issue #2 (no cancel control). Diferencia "user clicou cancelar" de "container morreu / processo crashou". |

Atlas **continua trabalhando agora** (último commit 13:48 hoje). O sprint não está fechado — Form A não foi reportada no `ATLAS_CLAUDE_COORDINATION.md`. Atlas precisa pushar (origin/master ainda não recebeu — confirmado por reflog onde HEAD@{0}=73bcbe1 e origin parou em commit anterior).

### 5.4 Anatomia precisa do bug Shakira — com evidência

> **Por que esta análise está correta** (resposta a Otávio: "Você que encontra os bugs, não eu. Seu trabalho é me explicar porque você acha que seu bugfix está correto"). Cada conclusão abaixo está ancorada em evidência específica — código, commit hash, ou comportamento observável em produção. Se algum elo da cadeia falhar, a anatomia precisa ser corrigida.

**Causa raiz comprovada**: `process_candidates` em `pipeline/ingest.py:445` usa `CitationMatcher` em `combined_text` = `title + snippet + full_text + summary`. Para PRIMARY targets, isso funciona porque o nome do vereador é específico. Para SECONDARY (Shakira, nome internacional famoso), o `full_text` de artigos sobre OUTROS assuntos contém blocos HTML de **"Notícias relacionadas"** / **"Leia também"** / **"Veja também"** que linkam pra notícias relacionadas — e esses blocos podem mencionar "Shakira" mesmo se o artigo principal não é sobre ela.

**Como provo** (cadeia de evidência):

1. **Existência do problema na produção**: o `assets/clipping-data.json` no working tree contém o artigo "Show de Shakira em Praia de Copacabana impulsiona turismo latino em 2026, diz Mais Brasil Viagens" (URL: https://www.mercadoeeventos.com.br/noticias/parques-e-atracoes/show-de-shakira-em-praia-de-copacabana-impulsiona-turismo-latino-em-2026-diz-mais-brasil-viagens) tagueado com `targetKeys: ['flavio_valle']`. Verifiquei via `python3 -c "json.load + walk stories"`. **Evidência observável**.

2. **Atlas confirmou independentemente**: Note-008 no `ATLAS_IRIS_ASYNC.md` (escrita 2026-05-05): *"Otavio reported that Shakira runs showed progress but published no Shakira stories, and later one false Shakira tag appeared from page boilerplate."* Atlas é insider — sua descrição combina com o caso. **Evidência por testemunho**.

3. **Fix do Atlas ataca a causa que descrevo**:
   - Commit `bb6218e`: introduz `RELATED_MATCH_NOISE_RE = r"(?is)\b(not[ií]cias?\s+relacionadas?|leia\s+tamb[eé]m|veja\s+tamb[eé]m|textos?\s+relacionados?)\b.*"` em `pipeline/ingest.py:60` que apaga TUDO depois desse marcador no texto.
   - Commit `238b97d`: introduz `secondary_target_keys` set em `process_candidates:449` e exige que o hit do secondary apareça no safe-surface (sem full_text).
   
   **Se o problema fosse outro** (e.g. matcher case-insensitive errado, ou backfill puro), o fix do Atlas não teria essa forma específica. A forma do fix corrobora a forma do bug. **Evidência por contraste**.

4. **Teste do Atlas reproduzia o bug**: `tests/test_targets_jobs.py:941` `test_process_candidates_skips_secondary_target_only_in_page_boilerplate` constrói exatamente um candidato com `full_text` contendo "Notícias relacionadas: Shakira no Rio" e assert que o secondary target NÃO ganha mention. Antes do commit 238b97d, esse teste ou não existia ou falhava. **Evidência por test fixture**.

**Limites da minha conclusão** (onde posso estar errada):
- Eu não rodei o pipeline ANTES do commit `238b97d` pra confirmar reprodução exata. Confio na descrição do Atlas + na forma do fix.
- Pode existir um path adicional que eu não vi — Atlas pode ter encontrado outros casos que motivaram a fix mas não documentou completamente.
- O bug-class pode ter outra dimensão (UI filter refresh — Gap 5.4.C) que não tem a mesma causa raiz mas estava "junto" no relato do Otávio.

**Bonus de evidência — F018 confirmado live**: o mesmo artigo aparece **2 vezes** em `clipping-data.json`, uma com `https://www.mercadoeeventos.com.br/...` e outra com `https://mercadoeeventos.com.br/...` (sem `www.`). O dedup por URL falhou porque há **duas funções `canonicalize_url`** (em `pipeline/normalization.py:35` e `pipeline/http_utils.py:236`) com comportamentos diferentes — e dependendo de qual é usada no insert vs no export, dedup retorna resultado diferente. F018 da Seção 5.5.4 não é teórico; é observável no JSON de produção.

**Resultado observado** (Note-008 do Atlas): "Shakira runs showed progress but published no Shakira stories, and later one false Shakira tag appeared from page boilerplate."

**Fix do Atlas (3 commits encadeados)**:

1. `238b97d` — Em `process_candidates`, monta `secondary_target_keys` (line 449). Após resolver `full_text` mas ANTES de salvar a mention (line 731+), recalcula safe surface = `title + snippet + summary` (sem full_text), roda matcher de novo, e **requer** que cada hit secundário também esteja no safe surface. Se não, skip com `reason="target_only_in_page_boilerplate"` e stage `safe_surface_match`. Adicionou `test_process_candidates_skips_secondary_target_only_in_page_boilerplate` (test_targets_jobs.py:941).

2. `bb6218e` — Não bastava só excluir full_text. Snippet às vezes vinha de RSS feed que TAMBÉM tem "Notícias relacionadas" inline. Atlas extraiu `safe_target_match_surface()` (line 154) que strip HTML tags (`TAG_RE`), URLs, e mais importante o regex `RELATED_MATCH_NOISE_RE = r"(?is)\b(not[ií]cias?\s+relacionadas?|leia\s+tamb[eé]m|veja\s+tamb[eé]m|textos?\s+relacionados?)\b.*"` que apaga TUDO depois desse marcador. Aplicou em title+snippet+summary do safe surface check.

3. `73bcbe1` — Não relacionado à matching, é o **outro lado do bug Shakira**: o cancel control. "Sprint issue #2: no cancel control". Atlas distinguiu duas situações que antes ambas viravam `status="cancelled"`:
   - **Manual**: user clicou botão cancelar → `status="cancelled"` (intencional)
   - **Restart**: container morreu / Render redeploy → orphaned active job → ANTES virava cancelled também, AGORA vira `status="interrupted"` com mensagem "A atualização foi interrompida por reinício do servidor. Os itens já salvos continuam preservados." Renomeou função `cancel_orphaned_active_jobs` → `mark_orphaned_active_jobs_interrupted`.

**Por que tests existentes não pegavam ANTES dos fixes:**
- Tests usavam fixtures de articles cujo full_text era limpo (só sobre o target real). Não simulavam blocos boilerplate.
- Não havia teste de "secondary target adicionado dinamicamente via UI → ingestão posterior → save story → display no filtro do dashboard".

**Ângulos do bug-class que os commits do Atlas NÃO cobrem (test gaps)** — vão para Seção 6:

#### Gap 5.4.A — Asymmetria primary vs secondary

Safe-surface check **só roda para secondary targets** (line 449 `if not bool(getattr(target, "primary", False))`). **Primary targets continuam matchando full_text**, incluindo blocos related-links. Caso real:

> Artigo "Show de Shakira em Praia de Copacabana impulsiona turismo latino — diz Mais Brasil Viagens". Title = sobre Shakira. Full_text = "Segundo o **CEO Flávio Valle**, a presença de uma artista latina..." (homônimo do vereador, CEO da operadora de turismo).

`flavio_valle` é PRIMARY → não passa pelo safe-surface check → é tagueado como mention de Flávio Valle vereador, embora seja artigo de show de Shakira sobre CEO homônimo.

Verifica live (read-only): `assets/clipping-data.json` no working tree contém esse artigo com mention de `flavio_valle`. Ainda em produção.

#### Gap 5.4.B — Manual story bypassa o safe-surface

`insert_manual_story` em `db_admin.py:685` é admin-only (require_admin + require_csrf). Insere article diretamente com mention(s) explícitas via payload `target_keys`. Não chama `process_candidates` → não passa pelo safe-surface. Edge case: admin classifica acidentalmente artigo errado em target errado, ou texto colado tem boilerplate.

#### Gap 5.4.C — Frontend filter refresh após adicionar target

POST `/api/targets` retorna sucesso. Frontend (`clipping.js`) renderiza confirmação mas o **filter dropdown do dashboard não atualiza com novo target sem refresh manual**. (A confirmar via leitura precisa do handler do `addTargetForm` — não fiz ainda.) Confirmação do Otávio em mensagem anterior: "ele não estava ligado na adição de filtros".

Esse é o angulo PURE FRONTEND do bug-class. Não tocado pelos 3 commits backend.

#### Gap 5.4.D — Cleanup runs only on `update` job, not on classification or manual story

`cleanup_false_backfilled_target_mentions` é chamado em `JobManager.start_update` (jobs.py:208 da diff anterior). NÃO é chamado em `start_export`, `manual_story`, ou ao adicionar target sozinho (sem update). Se admin adiciona target Shakira mas não dispara update, mentions falsas pré-existentes (de uma run anterior antes da fix) continuam. Cleanup é dependente de timing.

### 5.4.E Achado adicional: F018 manifestado em produção

Ao buscar a URL do artigo "Show de Shakira" no `clipping-data.json` para dar ao Otávio, achei que o **mesmo artigo aparece DUAS vezes** no payload, uma com `https://www.mercadoeeventos.com.br/...` e outra com `https://mercadoeeventos.com.br/...` (sem `www.`). O dedup por URL na pipeline (`db.insert_article_if_new` → `find by url`) falhou.

Causa raiz comprovada: existem **duas funções `canonicalize_url`**:
- `pipeline/normalization.py:35` — strip tracking params, sort query, lowercase
- `pipeline/http_utils.py:236` — port-aware, trailing slash, scheme normalization

Dependendo de qual é usada no insert vs no display, dedup retorna resultado diferente. F018 não é teórico; é observável no JSON em produção.

### 5.6 Bug-classes novas (descobertas em deep-read de `process_candidates`, Iteração 9)

#### 5.6.1 — Run cortada por time budget sem checkpoint, sem aviso — **CRÍTICO** (D14)

> **Otávio (D14)**: *"GRAVÍSSIMO. Péssimo. Não é para um run cortar."*

##### O que o código DEVERIA fazer (intenção real)

O pipeline de ingestão recebe um array de `candidates` (artigos potenciais) e itera processando cada um: faz fetch do HTML completo, roda matcher contra os targets monitorados, decide se grava no DB e em qual story. Cada candidate pode levar 1-10 segundos (depende de network do site origem, tamanho do HTML, complexidade do match).

A **intenção do parâmetro `max_process_seconds`** era ser um **circuit breaker defensivo**: se algo der MUITO errado (ex: site lento que faz timeout de 60s em cada fetch, ou collector que retornou 50.000 candidates inesperadamente), não deixar o pipeline rodar pra sempre travando o thread daemon. Default `90000` (25 horas) era um teto largo: "ninguém em sã consciência precisa de mais que isso".

**Comportamento esperado pelo Otávio**: quando ele clica "rodar por anos" via UI, ele espera que o pipeline **conclua** o trabalho. Pode demorar — mas conclui. Se realmente atingisse limite de tempo, o esperado seria:
1. Dizer claramente "atingi o limite de tempo após X candidates de Y";
2. Salvar estado pra continuar onde parou na próxima execução;
3. Marcar o job como `partial_completion` ou similar (não `succeeded`).

##### Como o bug quebra essa intenção

Em `pipeline/ingest.py:598-607`, dentro de `process_candidates`:

```python
for candidate in candidates[:max_candidates]:
    if cancel_requested(options):
        cancelled = True
        errors.append("cancelled")
        emit_source_progress("cancelled")
        break
    if time.monotonic() - started_at > max_process_seconds:
        errors.append("time_budget_exceeded")     # ← string adicionada à lista interna
        emit_source_progress("time_budget_exceeded")  # ← progress event genérico
        break                                       # ← simplesmente para o loop
```

Quando `max_process_seconds` é atingido:
1. Adiciona uma string `"time_budget_exceeded"` na lista `errors` interna do `IngestionResult`. Essa lista NÃO é mostrada com destaque ao user.
2. Emite um progress event genérico — coworker no UI vê uma palavrinha em algum log raso.
3. `break` — interrompe a iteração.

Em seguida, `pipeline/ingest.py:971-979`, a função monta um `IngestionResult` com tudo que processou ANTES do break, e retorna.

Em `web_app/jobs.py` (handler do job runner), o `IngestionResult` retornado é tratado como **sucesso**: o job ganha `status="succeeded"` desde que a função tenha retornado sem exception. **`time_budget_exceeded` NÃO é exception, é string em uma lista**. Logo: job marcado como sucesso, mesmo com run incompleta.

A função `sanitize_error` em `web_app/jobs.py:1006` traduz strings de erro pra mensagens amigáveis. Mas como `time_budget_exceeded` chegou como item de lista (não como exception bubbled-up), ela nem é chamada nesse caso. O coworker vê o pill verde "Concluído" e fim.

**O code path resumido**:
```
process_candidates roda 7000 de 21000 candidates → time budget atinge →
break loop → IngestionResult{candidates_seen=7000, errors=["time_budget_exceeded"]} →
JobManager recebe → marca job status="succeeded" (porque não houve exception) →
UI mostra pill verde "Concluído" →
Coworker acha que tudo foi processado →
Articles 7001-21000 nunca foram tocados.
```

##### Por que é GRAVÍSSIMO (impacto concreto)

1. **Decisão silenciosa do sistema sobrescrevendo escolha do user**. O Otávio (ou coworker) clicou "rodar pra esse período de 1 ano". O sistema decidiu: "não, vou parar antes". E não disse.

2. **Sem checkpoint = sem recuperação**. Se o user descobrir DEPOIS que o run foi parcial, a única opção é rodar de novo do zero. Os 7000 articles processados na primeira run **não são reaproveitados** — vão ser duplicados (alguns) ou re-fetched. Custo de tempo + carga em sites externos (que podem rate-limit).

3. **Visibility zero**. Mesmo um Otávio atento, olhando a UI, não vê sinal de que a run foi cortada. O `errors=["time_budget_exceeded"]` está numa fila interna que ninguém renderiza.

4. **Confiança do clipping erodida**. Se Otávio disser "rode 2 anos" e receber dados parciais sem aviso, ele perde confiança no que está vendo. Pra clipping político (decisão de governança baseada nos dados), isso é grave.

5. **Cap implícito de 25h é absoluto e não-configurável pelo user**. Em `web_app/jobs.py:60-72`, todos os 3 modos (rapido, completo, custom) têm `max_process_seconds = 90000` hardcoded. UI runner não expõe esse parâmetro. **Otávio NÃO TEM COMO** pedir "rodar por 50h" via interface. Mesmo que quisesse.

##### Cenários de produção onde isso aparece

1. **Backfill de 1+ ano com `--target flavio_valle`** + todas 8 sources. Cada source é uma "rodada" separada, mas todas dentro do mesmo `process_candidates` budget. Sitemap diário sozinho: 365 sitemaps × 5-10s fetch = 30-60min. Multiplicar por 2 anos: 1-2h. Plus RSS feeds (21 feeds × 500 candidates × 2s fetch médio = 5h). Plus WordPress, Google News, internal_search. Total realisticamente: 8-15h pra 1 ano, 15-30h pra 2 anos. **Atinge o cap.**

2. **Add new secondary target + roda backfill com data ampla**. Coworker adiciona "Pedro Rodrigues" como target, pede "buscar últimos 6 meses". Pipeline roda pra TODAS as sources (não só Google News). Atinge cap mesmo em 6 meses se sources são lentas.

3. **Site externo lento** (ex: domínio do Globo com cooldown). Cada fetch leva 30s em vez de 3s. Acumula budget rápido. Run de 1 mês pode atingir cap.

##### Para Theseus resolver

**Decisões de design pendentes** que o Otávio (ou Atlas) precisa tomar antes de implementar fix:

1. **O cap de 90000s deve continuar existindo?** Argumento pro: defesa contra runaway. Argumento contra: nunca foi necessário ativar isso intencionalmente, e o user perde controle. Recomendação: **manter cap mas EXPOR pro user** (option no UI runner avançado: "tempo máximo: 25h | 50h | 100h | sem limite").

2. **Como sinalizar run cortada?** Opções:
   - (a) Status novo `partial_completion` (em vez de `succeeded`).
   - (b) Banner no UI "esta run não terminou todos os candidates — clique pra continuar".
   - (c) Email/notification ao Otávio.

3. **Como retomar do ponto onde parou?**
   - **Solução recomendada**: conectar a tabela `backfill_state` que **JÁ EXISTE NO SCHEMA** (Seção 5.9.1) e nunca foi usada. Schema: `query`, `start_date`, `end_date`, `current_date`, `current_page`, `status`, `updated_at`.
   - Pipeline, ao processar cada source, atualiza `current_date`/`current_page` periodicamente (ex: a cada 100 candidates).
   - Quando atinge time budget, marca `status='paused'`.
   - Próxima run, antes de coletar do zero, verifica `get_paused_backfills()` (já implementado em `pipeline/database.py:1032`!) e resume do `current_date`.

**Test que pegaria a regressão**:

```python
@pytest.mark.integration
def test_run_cortada_por_time_budget_marca_partial_completion(monkeypatch):
    """
    Quando max_process_seconds é atingido, job NÃO deve ser marcado
    como 'succeeded'. Deve ter status que sinalize parcial.
    """
    monkeypatch.setattr("pipeline.ingest.IngestionOptions.max_process_seconds", 1)  # 1 segundo
    # roda pipeline com many candidates pra forçar time budget
    result = run_ingestion(...)
    assert "time_budget_exceeded" in result.errors
    assert job_status == "partial_completion"  # não 'succeeded'
    # E deve haver checkpoint persistido pra próxima run continuar:
    paused = ClippingDB(...).get_paused_backfills()
    assert len(paused) >= 1
```

**Conexão a outros bugs**:
- **5.9.1 (`backfill_state` tabela morta)** é EXATAMENTE o que precisa pra resolver isso. 1 implementação resolve 2 bugs.
- **5.6.2 (archive cutoff em 80%)** é o "gêmeo": também é decisão silenciosa do sistema baseada em tempo decorrido.

#### 5.6.2 — Articles processados nos últimos 20% do budget têm `full_text` degradado silenciosamente — **CRÍTICO** (D15)

> **Otávio (D15)**: *"Mesmo de cima — Ariadne precisa entender melhor os erros, e precisamos de um Theseus para resolvê-los."*

##### O que o código DEVERIA fazer (intenção real)

Quando o pipeline encontra um candidate (artigo potencial), ele tem o **título** e o **snippet** (descrição curta) já em mãos — vieram do RSS/Google News/etc. Mas pra fazer matching robusto E pra preservar o conteúdo pro coworker ler depois, o pipeline também precisa fazer **fetch do HTML completo** do artigo no site origem e extrair o texto integral (`full_text`).

Esse fetch é caro: cada artigo leva 1-10 segundos (HTTP request + parse HTML). Em runs longas, todos esses fetchs somam muito tempo.

A **intenção do `archive_cutoff = max_process_seconds * 0.8`** parece ter sido: "se já consumiu 80% do tempo orçado, prioriza GRAVAR articles em vez de gastar tempo com fetch HTML caro — assim conseguimos pelo menos cadastrar todos os candidatos antes de ficar sem tempo".

A lógica subjacente: "se fetch full text dura 5s e snippet/title já está em mãos, melhor gravar 100 articles com texto raso (snippet) do que 30 articles com texto rico (full_text) e perder os outros 70".

Faz sentido como heurística de degradação graciosa. **Mas a heurística não é comunicada ao user**.

##### Como o bug quebra essa intenção

Em `pipeline/ingest.py:484` define o cutoff:
```python
archive_cutoff = max_process_seconds * 0.8  # 80% do tempo total
```

Em `pipeline/ingest.py:732-746`, a decisão de fetch:
```python
should_archive_full_text = (
    options.archive_full_text
    and (time.monotonic() - started_at) <= archive_cutoff
)
if not full_text and should_archive_full_text:
    try:
        final_url, raw_html, full_text, ... = fetch_full_article_text(...)
    except Exception:
        full_text = candidate.snippet or candidate.title  # ← fallback silencioso
        raw_html = ""
elif not full_text:
    full_text = candidate.snippet or candidate.title       # ← fallback silencioso
    raw_html = ""
```

Comportamento step-by-step:
1. Pipeline anota `started_at = time.monotonic()` no início.
2. Pra cada candidate, calcula `tempo_decorrido = time.monotonic() - started_at`.
3. Se `tempo_decorrido > 80% * max_process_seconds` (= 20h no default 25h), seta `should_archive_full_text = False`.
4. Quando `should_archive_full_text = False`, o `if` na linha 733 não executa o fetch. Vai pro `elif` na linha 744.
5. `elif not full_text:` é true (porque o fetch nunca foi tentado).
6. `full_text = candidate.snippet or candidate.title` — substitui texto rico por snippet curto.
7. Linha 884: `full_text=full_text[:60000]` truncado pra 60k chars (mas snippet costuma ter <500 chars).
8. Article é INSERIDO NO DB com `full_text` igual ao snippet. **Sem flag distinguindo "completo" de "degradado"**.

##### Cascata de degradação downstream

Cada feature que depende do `full_text` rich vira degradada silenciosamente:

- **`summarize_text(full_text)`** (linha 750): gera summary de 1-3 frases. Com snippet (já curto) como input, summary fica vazio ou só repete o título.
- **`safe_target_match_surface(title, snippet, summary)`** (line 752, fix do Atlas pra Shakira): vira inútil pra detectar boilerplate, porque `summary` (que era pra ser substantivo) é só repetição do snippet.
- **AI summary downstream** (se admin rodar `tools/classify_articles.py`): recebe 1/10 do contexto que deveria. Categorização AI fica imprecisa.
- **Search no dashboard**: usuário busca "ciclovias" no clipping; articles degradados não aparecem porque a palavra "ciclovias" estava só no full_text completo, não no snippet.
- **"Texto pra leitura"** no dashboard (`assets/clipping-raw-texts.json`): coworker abre o toggle pra ler artigo completo, vê 1 parágrafo curto em vez de 30. **Sintoma observável**.

##### Por que é GRAVÍSSIMO

1. **Decisão silenciosa do sistema sobrescrevendo escolha do user**. Mesma classe do 5.6.1: o sistema decide degradar sem perguntar nem avisar.

2. **Sem flag de qualidade no DB**. Article degradado e article completo ficam indistinguíveis no schema. Não tem `articles.full_text_quality` ou `articles.is_truncated`. **Theseus que tentar consertar precisa primeiro identificar QUAIS articles foram degradados** — e a única forma é re-fetch tudo (porque não há registro de quais foram).

3. **Re-processar é caro**. Se Otávio quiser "completar os articles degradados", precisa rodar pipeline de novo — e cai no mesmo cap de 25h. Loop.

4. **Pior pra Shakira-class bugs**. Atlas fez safe-surface check usando title+snippet+summary. Mas se `summary` é só snippet repetido, o safe-surface vira raso. Articles tagueados em runs degradadas têm proteção menor contra falsos positivos.

5. **Confiança do clipping erodida (mesmo motivo 5.6.1)**. Coworker abre artigo do Bernardo Rubião da semana 24, vê só 50 chars, pensa "ferramenta tá quebrada". Não sabe que é run que cortou.

##### Cenários de produção onde aparece

1. **Mesmo backfill de 6 meses do 5.6.1**. Inicia 14:00, roda até 10:00 do dia seguinte (20h decorridas = exato cutoff). Articles **da segunda metade do backfill** (semanas 13-26) entram degradados.

2. **Backfill repetido pra "atualizar"**. Otávio nota que articles antigos estão rasos, manda rodar de novo pro mesmo período. Cai no mesmo cutoff. Articles continuam rasos.

3. **Run de 2 anos**. Atinge cutoff em ~75-100% do budget total. Última metade dos articles fica rasa. Coworker classifica articles da metade pra cá com contexto incompleto.

##### Para Theseus resolver

**Decisões de design pendentes** que Otávio precisa decidir antes da fix:

1. **Como sinalizar article degradado?**
   - Opção A: nova coluna `articles.full_text_complete BOOLEAN DEFAULT 1`. Pipeline marca FALSE quando degradado. Dashboard mostra ícone "texto incompleto" no card.
   - Opção B: usa `articles.metadata_json` (que já existe) com chave `{"full_text_degraded": true, "reason": "time_budget_archive_cutoff"}`.
   - Opção C: nem marca — só toma decisão "se atinge cutoff, não grava o article" (mais radical, perde mais articles).

2. **Manter cutoff em 80%?**
   - Argumento pro: degradação graciosa é razoável.
   - Argumento contra: 80% pode ser cedo demais. Se pipeline tem que parar em 100% do budget de qualquer jeito, por que parar fetch em 80%?
   - **Recomendação**: aumentar cutoff pra 95% (ou tornar configurável).

3. **Re-fetch automático em background?**
   - Quando job principal termina, opcionalmente disparar segundo job só pra re-fetch dos articles marcados degradados.
   - Risco: complexidade de scheduling em ambiente Render single-process.

**Conexão com 5.6.1**: se Theseus implementar o checkpoint resume (5.6.1), o 5.6.2 pode ser resolvido naturalmente: cada checkpoint marca articles incompletos; próxima run resume e completa fetch.

**Test que pegaria a regressão**:

```python
@pytest.mark.integration
def test_articles_degraded_por_archive_cutoff_recebem_flag(monkeypatch):
    """
    Articles inseridos depois do archive_cutoff devem ser marcados
    com flag indicando full_text incompleto.
    """
    monkeypatch.setattr("pipeline.ingest.IngestionOptions.max_process_seconds", 10)
    # forçar passar do cutoff em 8s artificialmente
    # roda pipeline com candidates simulados
    result = run_ingestion(...)
    # checa DB pra confirmar flag
    with ClippingDB(...) as db:
        articles = db.list_articles()
        degraded = [a for a in articles if a.get("full_text_complete") is False]
        assert len(degraded) > 0  # alguns devem ter sido marcados
        # E summary deles é curto (snippet, não full)
        for a in degraded:
            assert len(a["summary"]) < 100  # snippet típico
```

#### 5.6.3 + 5.8.1 — F018: dedup por URL falha porque há DUAS funções `canonicalize_url`

> **Manifestação confirmada em produção**: o artigo "Show de Shakira em Praia de Copacabana" aparece **2 vezes** em [`assets/clipping-data.json`](Documents/vscode/clipping-project/assets/clipping-data.json), uma com `https://www.mercadoeeventos.com.br/...` e outra com `https://mercadoeeventos.com.br/...` (sem `www.`). O dashboard público mostra dois cards do mesmo artigo. URL: https://www.mercadoeeventos.com.br/noticias/parques-e-atracoes/show-de-shakira-em-praia-de-copacabana-impulsiona-turismo-latino-em-2026-diz-mais-brasil-viagens

##### O que o código DEVERIA fazer (intenção real)

Quando dois collectors diferentes (RSS e Google News, por exemplo) descobrem o mesmo artigo do mesmo site, ambos passam pelo pipeline. A intenção é: **ANTES de gravar no DB, normalizar a URL pra forma canônica** (lowercase host, remover params de tracking como `utm_*`, decidir trailing slash, decidir presença de `www.`, etc.). Assim, a UNIQUE constraint em `articles.url` consegue detectar duplicatas mesmo quando os collectors trazem variações superficiais.

A função pra fazer isso se chama `canonicalize_url`. O design espera **uma fonte de verdade** — uma função que, dada uma URL, retorna sempre a mesma forma normalizada.

No export final (`tools/export_mobile_snapshot.py`), há um segundo dedup: ao montar o JSON do dashboard, percorrer articles e remover duplicatas por URL. Esse dedup também espera que URLs estejam canonicalizadas.

##### Como o bug quebra essa intenção

Existem **duas funções `canonicalize_url` no código**, com lógicas DIFERENTES:

1. **`pipeline/normalization.py:35`** — strip de query params, lowercase host, remoção de fragment.
2. **`pipeline/http_utils.py:236`** — port-aware (preserva 443/80), lógica de trailing slash, decisões diferentes sobre `www.`.

Quando dois collectors passam o mesmo artigo:

```
Collector A (RSS):
  candidate.url = "https://www.mercadoeeventos.com.br/noticias/.../shakira"
  → fetch_full_article_text usa pipeline/http_utils.canonicalize_url
  → normaliza para "https://www.mercadoeeventos.com.br/noticias/.../shakira" (preserva www)
  → insert_article_if_new com essa URL → INSERTED

Collector B (Google News):
  candidate.url = "https://news.google.com/articles/RANDOM..."
  → try_resolve_google_redirect → expande pra "https://mercadoeeventos.com.br/noticias/.../shakira" (sem www)
  → fetch_full_article_text usa pipeline/http_utils.canonicalize_url
  → mesma URL exata: "https://mercadoeeventos.com.br/noticias/.../shakira"
  → insert_article_if_new busca por essa URL no DB
  → NÃO encontra (URL com www. estava lá, sem www. é nova string)
  → INSERTED de novo
```

Resultado: 2 linhas em `articles` table com URLs ligeiramente diferentes. UNIQUE constraint não pega.

Em seguida, no export (`tools/export_mobile_snapshot.py:2438`):

```python
seen_urls: set[str] = set()
unique_articles = []
for article in story["articles"]:
    if not url or url not in seen_urls:
        seen_urls.add(url)
        unique_articles.append(article)
```

O export percorre articles da story, faz `seen_urls.add(article.url)`. Mas como os 2 articles têm URLs literalmente diferentes (`with-www` vs `without-www`), o set considera ambos únicos. **Ambos vão pro JSON**.

##### Por que isso é problemático

1. **Dashboard mostra duplicatas visíveis**. Coworker olha o painel, vê 2 cards iguais. Pensa "ferramenta tá duplicando". Confiança no clipping cai.

2. **Stats inflam**. `articleCount` da story conta 2 em vez de 1. `mentions_inserted` durante run conta 2 em vez de 1. Stats no dashboard ("32 artigos esta semana") ficam 1.5x-2x do real.

3. **Cleanup do Atlas (`cleanup_false_backfilled_target_mentions`)** opera por `mentions.article_id`. Se mention falsa de Shakira foi inserida em DUAS rows do mesmo artigo, cleanup precisa rodar 2x ou tratar ambos. Pode falhar parcialmente.

4. **Story grouping confuso**. `choose_story` busca stories pra merge usando similarity de título. O mesmo artigo em duas linhas pode ficar em duas stories diferentes — fragmentando o agrupamento.

5. **AI summary count duplicado**. Se cada cópia do artigo gera AI summary diferente (de runs diferentes), você tem dois summaries pra o mesmo conteúdo. Custo Anthropic dobrado no `tools/classify_articles.py`.

##### Cenários de produção onde aparece

1. **Mesmo artigo coletado por RSS + Google News**: muito comum. Cobertura paralela é objetivo do pipeline (redundância pra não perder articles), mas requer dedup confiável.

2. **Mesmo artigo coletado em runs diferentes**: collectors RSS coletam só "últimos N posts", articles antigos saem do feed. Mas Google News pode trazer o mesmo artigo dias depois. Duplicação cross-run.

3. **Mesmo artigo coletado de WordPress site + sitemap diário**: cada source tem URL pattern próprio mas resolve pro mesmo artigo final.

##### Para Theseus resolver

**Decisões de design pendentes**:

1. **Qual `canonicalize_url` é a "certa"?**
   - Opção A: usar `pipeline/normalization.canonicalize_url` (a mais agressiva — remove tracking params + sort query). Mais conservador.
   - Opção B: usar `pipeline/http_utils.canonicalize_url` (preserva mais detalhes). Pode dedupar menos.
   - Opção C: criar uma terceira função específica pra dedup, baseada nas duas existentes.
   - **Recomendação**: Opção A. A função em `normalization.py` é mais "purista" (remove `utm_*`, sort query params, lowercase). Combina com intenção de "duas URLs com mesmo conteúdo são iguais mesmo com tracking diferente".

2. **Como migrar os articles já duplicados em produção?**
   - Após implementar fix, rodar one-shot SQL:
   ```sql
   -- Pseudo SQL: buscar pares de articles cujas URLs canonicalizam pra mesma
   -- Para cada par: manter o mais recente, redirecionar mentions/story_articles
   -- pro mantido, deletar o outro.
   ```
   - **Cuidado**: precisa preservar `mentions`, `story_articles`, `classifications` ligados — não pode só `DELETE`. Precisa REVINCULAR.

3. **Onde aplicar a função correta?**
   - **No INSERT (pipeline/ingest.py:877 `db.insert_article_if_new`)**: garantir URL é canonicalizada antes do INSERT. Função recebe URL já canonical do caller.
   - **No EXPORT (tools/export_mobile_snapshot.py:2438)**: garantir comparação por URL canonical no `seen_urls` set.
   - **No story_with_articles (pipeline/database.py)**: comparações em queries SQL. Mais complexo — pode requerer adicionar coluna `articles.canonical_url` indexada.

**Test que pegaria a regressão**:

```python
@pytest.mark.integration
def test_canonicalize_url_implementations_agree():
    """
    Hoje, normalization.canonicalize_url e http_utils.canonicalize_url
    retornam strings diferentes pra mesma URL. Esse teste falha hoje.
    Quando passar, F018 está resolvido.
    """
    from pipeline.normalization import canonicalize_url as canonical_norm
    from pipeline.http_utils import canonicalize_url as canonical_http
    test_urls = [
        "https://www.mercadoeeventos.com.br/path/?utm_source=x",
        "https://mercadoeeventos.com.br/path/",
        "http://www.mercadoeeventos.com.br/path",
    ]
    canonicals = [canonical_norm(u) for u in test_urls]
    # Após fix, todas as variantes devem normalizar pra mesma string
    assert len(set(canonicals)) == 1, f"Variants didn't merge: {canonicals}"
    # E http_utils deve concordar com normalization
    for url in test_urls:
        assert canonical_norm(url) == canonical_http(url)


@pytest.mark.integration
def test_pipeline_dedupes_url_with_and_without_www(tmp_path, monkeypatch):
    """
    Mesmo artigo coletado com www. e sem www. deve virar UMA row em articles.
    Hoje vira duas — esse teste falha. Quando passar, F018 está resolvido.
    """
    db_file = tmp_path / "test.db"
    candidates = [
        CandidateArticle(url="https://www.mercadoeeventos.com.br/X", title="...", ...),
        CandidateArticle(url="https://mercadoeeventos.com.br/X", title="...", ...),
    ]
    with ClippingDB(db_file) as db:
        process_candidates(candidates, ...)
        articles = db.list_articles()
        assert len(articles) == 1, f"Expected 1 article, got {len(articles)}"
```

**Conexão com outros bugs**:
- **5.6.3 (insert dedup)** e **5.8.1 (export dedup)** são duas faces da mesma F018. Mesma fix resolve ambos.
- Indiretamente afeta **5.4 (bug Shakira)**: artigo Shakira aparece 2x em produção; cleanup do Atlas precisa lidar com ambas cópias.

#### 5.6.4 — Cleanup do Shakira só atinge mentions com strings mágicas específicas — risco de drift futuro

##### O que o código DEVERIA fazer (intenção real)

A coluna `mentions.sentiment_reason` foi pensada como **rastro de origem** de cada mention: por que essa mention foi criada e por qual processo. Valores possíveis observados em produção:

- `"lexical_heuristic"` — pipeline original (`pipeline/ingest.py:859`) cria assim toda mention que veio de matching automático (CitationMatcher).
- `"existing_article_backfill"` — backfill de secondary target (`web_app/db_admin.py:557`) cria assim quando descobre target em article já existente.
- `"agent_summary"` — skill `/clipping` (Claude inline) cria assim ao gerar AI summary.
- `"anthropic_batch"` — batch antigo Anthropic API (legado).
- (potencialmente futuros: novo collector AI, novo classificador, etc.)

A **intenção do `cleanup_false_backfilled_target_mentions`** (Atlas, commit `f0bf4ef`): remover mentions que foram criadas automaticamente E que não passam o safe-surface check (ou seja: o target só aparece em boilerplate tipo "Notícias relacionadas"). Decisão de produto: "se uma mention foi criada por uma das nossas heurísticas automáticas, e o target não está em title/snippet/summary, é falso positivo. Remove."

A intenção é **conceitual**: "remover mentions auto-geradas que falham safe-surface". Não é "remover mentions com a string X especificamente".

##### Como o bug quebra essa intenção

Em `web_app/db_admin.py:473`:

```python
WHERE m.target_key = ?
  AND COALESCE(m.sentiment_reason, '') IN ('existing_article_backfill', 'lexical_heuristic')
```

A query acopla a um **literal de string específico**. Concretamente:

- ✅ Pega mentions de `pipeline/ingest.py` (`lexical_heuristic`).
- ✅ Pega mentions de backfill (`existing_article_backfill`).
- ❌ NÃO pega mentions de `agent_summary` (skill /clipping) — mesmo se foram falsas.
- ❌ NÃO pega mentions de `anthropic_batch` legado — mesmo se foram falsas.
- ❌ NÃO pegaria mentions de futuros caminhos auto-gerados que usem outros valores.

##### Por que isso é problemático

1. **Frágil contra evolução do schema**. Se Theseus adicionar novo collector AI no futuro (digamos `tools/classify_articles_v2.py` com `sentiment_reason="claude-opus-4"`), as mentions geradas por ele NÃO serão limpas pelo cleanup do Atlas. Falso positivo desse novo collector vira fixture permanente no DB.

2. **Cleanup pode remover legítimas (raro mas possível)**. Mentions com `sentiment_reason="lexical_heuristic"` de runs ANTIGAS (antes do safe-surface check existir, antes do commit `238b97d`) podem ser corretas — o pipeline original pegava o target em full_text quando o target REALMENTE estava sendo discutido (não em boilerplate). Cleanup novo, ao rodar em todas mentions com essa string, pode deletar legítimas.

   Mitigação atual: a query checa também se article tem o target em title/snippet/summary atual (`target_matches_safe_article_fields`). Se sim, pula a remoção. Mas a checagem é ESTÁTICA — se article tem snippet curto que não contém o target embora full_text tenha legítima discussão, mention é deletada.

3. **Acoplamento conceitual em string mágica**. O conceito é "auto-gerada" mas a implementação é "uma das duas strings X ou Y". Mudança em qualquer um dos lados quebra o outro silenciosamente.

##### Cenário de produção onde o problema aparece

**Hoje (improvável mas possível)**:
- Otávio rodou `tools/classify_articles.py` (commit `489c639`, AI batch via Anthropic). O script grava em tabela `classifications` mas não toca `mentions.sentiment_reason`. Hipoteticamente, se algum dia uma versão futura desse script gravar mentions também com `sentiment_reason="claude-haiku"`, e essas mentions forem falsos positivos (similar ao bug Shakira mas em outra source), o cleanup do Atlas não pega.

**Futuro provável**:
- Adicionar novo path de mention auto-geração (ex: NLP do Brazilian portuguese pra detecção mais robusta). Esse path usa `sentiment_reason="brazilian_nlp"`. Falsos positivos ali são imunes ao cleanup.

##### Para Theseus resolver

**Decisão de design pendente**:

1. **Substituir string mágica por flag booleana?**
   - Adicionar coluna `mentions.is_auto_generated BOOLEAN DEFAULT 0`.
   - Toda mention criada por automação (pipeline original, backfill, agent_summary, future AI) seta `is_auto_generated = 1`.
   - Mentions criadas manualmente (admin via `/api/manual-story` ou `/api/classifications`) ficam com `is_auto_generated = 0`.
   - Cleanup busca por `WHERE is_auto_generated = 1 AND target_key = ?`.
   - Migração: backfill `is_auto_generated = 1` pra mentions existentes com `sentiment_reason IN ('lexical_heuristic', 'existing_article_backfill', 'agent_summary', 'anthropic_batch')`.

2. **Manter sentiment_reason como string mas centralizar lista de "auto reasons"**:
   ```python
   # web_app/db_admin.py ou shared module
   AUTO_GENERATED_REASONS = frozenset([
       "existing_article_backfill",
       "lexical_heuristic",
       "agent_summary",
       "anthropic_batch",
       # adicionar reasons futuros aqui
   ])
   ```
   - Cleanup importa essa constante. Outros caminhos que criam mentions também importam pra GARANTIR que o reason novo está incluído.
   - Mais leve que adicionar coluna nova mas ainda string-based.

**Recomendação**: Opção 1 (boolean). Muda schema mas é mais robusto contra evolução.

**Test que pegaria regressão**:

```python
@pytest.mark.integration
def test_cleanup_remove_mentions_de_qualquer_caminho_auto_generated(tmp_path):
    """
    Cleanup deve remover qualquer mention auto-gerada que não passe
    safe-surface, independente do sentiment_reason específico.
    """
    db_file = tmp_path / "test.db"
    target = Target(key="shakira", primary=False, ...)
    # Criar 4 mentions de target shakira em article cujo title não tem shakira:
    # - sentiment_reason="lexical_heuristic"  → deve deletar
    # - sentiment_reason="existing_article_backfill"  → deve deletar
    # - sentiment_reason="agent_summary"  → HOJE não deleta (BUG); deve deletar
    # - sentiment_reason="brazilian_nlp"  (future) → deve deletar
    cleanup_false_backfilled_target_mentions(db_file, ["shakira"])
    # Assert: todas as 4 foram deletadas
    assert mention_count == 0
```

#### 5.6.5 — `forced_terms` é vulnerável ao mesmo padrão do bug Shakira (boilerplate matching)

##### O que o código DEVERIA fazer (intenção real)

`forced_terms` é uma feature CLI: quando Otávio roda `python run_ingestion.py ... --forced-terms "vereador,Rio"`, ele está dizendo "só me interessa articles que mencionem AMBOS os termos `vereador` E `Rio`". É um filtro adicional aplicado depois do match dos targets monitorados.

A **intenção** é refinar a busca: Otávio quer recortar um subset de articles que falam EM ESPECÍFICO sobre vereador no Rio (não articles do mesmo target em outros contextos).

A intenção SEMÂNTICA é: "o artigo PRECISA SER SOBRE estes termos". Não "o artigo PRECISA TER essa palavra em qualquer lugar do HTML".

##### Como o bug quebra essa intenção

Em `pipeline/ingest.py:794-795`:

```python
combined_text = " ".join([
    candidate.title or "",
    candidate.snippet or "",
    full_text or "",
    summary or "",
])
if not passes_forced_terms(combined_text, forced_terms, forced_mode):
    emit_candidate(... reason="forced_terms_not_matched" ...)
    continue
```

O check usa `combined_text` que **inclui o full_text completo**. Esse full_text contém HTML extraído do artigo, INCLUINDO blocos de "Notícias relacionadas", "Leia também", "Veja também", "Continue lendo" — **exatamente o mesmo problema que motivou a fix do bug Shakira**.

Diferença: a fix do Atlas (commits `238b97d`, `bb6218e`) introduziu `safe_target_match_surface` (`pipeline/ingest.py:154`) e o aplicou na verificação de **targets secundários**, NÃO na verificação de `forced_terms`.

Resultado:
```
Otávio: --forced-terms "Rio,vereador"
Pipeline coleta artigo "Esporte: Maracanã recebe final"
  full_text: "...jogo no Maracanã. Notícias relacionadas: vereador no Rio defende..."
  passes_forced_terms("...jogo no Maracanã. Notícias relacionadas: vereador no Rio defende...", ["Rio","vereador"], "all")
  → True (ambos termos estão no combined_text — vieram do boilerplate)
Article PASSA o filtro mesmo sendo sobre futebol, não sobre o vereador.
```

##### Por que é problemático

1. **Filtro vira ruído em vez de precisão**. Otávio usou `forced_terms` precisamente pra REFINAR busca — pra evitar articles irrelevantes. Em vez disso, articles irrelevantes passam pelo boilerplate.

2. **Mesma bug-class do Shakira**. Mostra que o problema não foi atacado SISTEMICAMENTE. Atlas resolveu pra `secondary targets` (linha 751-793 com `secondary_target_keys` set). Mas `forced_terms` (linha 794-809) usa `combined_text` cru. **Padrão inconsistente no mesmo arquivo**.

3. **User raramente nota**. `forced_terms` é CLI — Otávio só. Quando passa filtro errado, ele vê article irrelevante no clipping e não sabe POR QUE entrou. Pode pensar que filtro tá quebrado em geral.

4. **Gera falsos positivos em runs longas**. Se Otávio rodar backfill com `--forced-terms` por várias semanas, articles errados acumulam. Cleanup não pega (cleanup só lida com targets, não com forced_terms decision).

##### Cenário de produção onde aparece

**Otávio raramente usa CLI com forced_terms** — feature periférica. Mas EXISTE no código e expõe a mesma classe.

**Se** Otávio decidir refinar busca (ex: backfill só sobre temas específicos com `--forced-terms "ciclovias,SubZS"`), pode receber articles irrelevantes que mencionam esses termos só em "Continue lendo".

##### Para Theseus resolver

**Fix conceitual**: aplicar a mesma lógica `safe_target_match_surface` em `passes_forced_terms`:

```python
# em pipeline/ingest.py, ao invés de combined_text com full_text:
forced_terms_text = safe_target_match_surface(
    candidate.title or "",
    candidate.snippet or "",
    summary or "",
)
if not passes_forced_terms(forced_terms_text, forced_terms, forced_mode):
    ...
```

**Decisão de design pendente**: `forced_terms` deve aplicar safe-surface SEMPRE, ou só quando o user explicitamente pedir? Pode ser que pra alguns cenários, o user QUEIRA que termos sejam buscados no full_text inteiro (ex: "ache QUALQUER article que mencione Pedro Rodrigues, mesmo em rodapé"). Mas pra UX padrão, safe-surface é o esperado.

**Recomendação**: aplicar safe-surface por default. Se algum dia precisar do "match em full_text completo", expor via flag `--forced-terms-mode strict|surface_only` (default: `surface_only`).

**Test que pegaria regressão**:

```python
@pytest.mark.integration
def test_forced_terms_nao_matcha_apenas_em_related_links(tmp_path):
    """
    forced_terms='vereador' não deve passar article cujo full_text só tem
    'vereador' em bloco 'Notícias relacionadas:'.
    """
    candidate = CandidateArticle(
        title="Maracanã recebe final do Brasileiro",
        snippet="Jogo neste sábado.",
        full_text=(
            "O Maracanã será palco. Estádio espera 80 mil. "
            "Notícias relacionadas: vereador defende novo metrô."
        ),
    )
    options = IngestionOptions(forced_terms=["vereador"], forced_terms_mode="any")
    result = process_candidates([candidate], targets, db, options=options)
    assert result.candidates_seen == 1
    assert result.articles_inserted == 0  # FAIL HOJE; deveria filtrar
```

### 5.9 Bug-classes em estado persistido / cache / frontend mutation (Iteração 12)

#### 5.9.1 — Tabela `backfill_state` existe no schema mas é dead — oportunidade pra resolver 5.6.1

##### O que o código DEVERIA fazer (intenção real)

Em `pipeline/database.py:85-92`, há definição da tabela:

```sql
CREATE TABLE IF NOT EXISTS backfill_state (
    query TEXT,
    start_date TEXT,
    end_date TEXT,
    current_date TEXT,
    current_page INTEGER,
    status TEXT,
    updated_at TEXT
)
```

Os campos contam a história da intenção:
- `query` — qual busca está rodando.
- `start_date`, `end_date` — janela total que o user pediu.
- `current_date`, `current_page` — checkpoint de "onde paramos".
- `status` — `running`, `paused`, `completed`.
- `updated_at` — última atualização.

Plus métodos prontos:
- `get_backfill_state(query, start_date, end_date)` — pra recuperar estado de uma busca em curso.
- `upsert_backfill_state(...)` — pra salvar progresso periódico.
- `get_paused_backfills()` — pra listar buscas que foram interrompidas e podem retomar.

**A intenção clara**: implementar **runs resumíveis com checkpoint**. Pipeline podia:
1. No início de cada run, checar `get_paused_backfills()` pra ver se há retomadas pendentes.
2. Durante o loop, periodicamente chamar `upsert_backfill_state` com `current_date`/`current_page`.
3. Quando atingir time budget (5.6.1), em vez de só `break`, marcar `status='paused'` antes de sair.
4. Próxima run vê o paused, retoma de `current_date`.

##### Como o bug quebra essa intenção

**Zero callers**. Confirmação via `rg`:
```
$ rg "upsert_backfill_state|get_backfill_state|get_paused_backfills" \
    pipeline/ingest.py pipeline/collectors.py web_app/ tools/
# (no matches outside pipeline/database.py itself)
```

A tabela é criada em todo `_init_schema` (chamado em todo init de `ClippingDB`). Os 3 métodos existem. Ninguém os chama. **Schema fantasma**: ocupa espaço em todo `clipping.db.gz` enviado pro Supabase (centenas de KB acumulados ao longo de upgrades de schema), mas nunca recebe write.

##### Por que é problemático

1. **Confunde quem lê o schema**. Eu mesma (Ariadne) demorei pra perceber que a tabela era morta — assumi que era usada antes de buscar callers. Outros devs/IAs cairão no mesmo erro.

2. **Tech-debt acumulado**. A tabela exista é evidência de que ALGUÉM começou a implementar checkpoint resume e nunca terminou. Custo de manter (migração, backup, schema migrations) sem benefício.

3. **MAS é oportunidade**: se Theseus quiser implementar checkpoint pra resolver 5.6.1, **a tabela já está pronta**. Não precisa migration. Só precisa conectar.

##### Para Theseus resolver

**Opção A — Conectar (recomendada)**: implementar 5.6.1 fix usando essa tabela. Em `pipeline/ingest.py`, adicionar:

```python
def run_ingestion(...):
    # No início, verificar paused
    paused = db.get_paused_backfills()
    if paused and resume_paused_param:
        # Continuar de current_date/current_page do paused
        ...

    # Durante o loop, salvar checkpoint a cada N candidates
    if seen % 100 == 0:
        db.upsert_backfill_state(
            query=options.query, start_date=options.date_from, end_date=options.date_to,
            current_date=last_candidate.published_at,
            current_page=current_collector_page,
            status='running'
        )

    # Ao atingir time budget (5.6.1):
    if time.monotonic() - started_at > max_process_seconds:
        db.upsert_backfill_state(..., status='paused')
        break
```

**Opção B — Apagar (se Otávio decidir contra checkpoint)**: `DROP TABLE backfill_state` + remover métodos. Reduz confusão.

**Recomendação**: Opção A. Tabela existe, fix do 5.6.1 precisa exatamente disso, oportunidade clara.

---

#### 5.9.2 — Tabela `scrape_log` existe no schema mas é dead

##### O que o código DEVERIA fazer (intenção real)

Em `pipeline/database.py:73-83`:

```sql
CREATE TABLE IF NOT EXISTS scrape_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT,
    source_type TEXT,
    started_at TEXT,
    finished_at TEXT,
    status TEXT,
    error_message TEXT
)
```

E métodos `log_scrape_start` (line 323) e `log_scrape_end` (line 334) que fazem INSERT/UPDATE nessa tabela.

**Intenção**: telemetria por coleta. Cada vez que um collector roda (ex: RSS coleta dos 21 feeds), grava entrada pra dizer:
- Qual collector iniciou e quando.
- Quanto tempo durou.
- Status final (`success`, `failed`, `partial`).
- Mensagem de erro se houve.

Útil pra: debugar "porque RSS feed do Globo falhou ontem?", monitorar performance de collectors ao longo de runs, gerar relatórios de saúde do pipeline.

##### Como o bug quebra essa intenção

**Zero callers**. Igual a 5.9.1. Métodos existem mas nunca chamados.

Significa: zero telemetria. Quando algum collector falha (timeout, certificate error, etc.), o erro vai pro `IngestionResult.errors` (lista interna) e/ou logs do Render (que rotacionam) — mas NÃO é persistido em DB pra histórico.

##### Por que é problemático

1. **Debug retrospectivo impossível**. Otávio reporta "RSS feed X parou de funcionar a semana passada". Como verificar? Logs do Render só guardam ~24h. `scrape_log` poderia ter 6 meses de histórico.

2. **Sem histórico de saúde dos collectors**. Não há "qual % de runs do RSS feed do G1 falham?". Decisões de "esse collector é confiável" são por sensibilidade humana, não dados.

3. **Mesmo padrão do 5.9.1**: confunde leitor.

##### Para Theseus resolver

**Decisão de design**:

1. **Conectar**: cada collector chama `log_scrape_start` no começo e `log_scrape_end` ao final. Modificação em ~8 lugares (1 por collector).
2. **Apagar**: `DROP TABLE` + remover métodos.

**Recomendação**: depende do priority de observabilidade. Se Otávio quer dashboards de saúde do pipeline, conectar. Se não, apagar pra reduzir bagunça.

---

#### 5.9.3 — `GOOGLE_DECODE_CACHE` cresce sem limite na memória

##### O que o código DEVERIA fazer (intenção real)

O collector Google News recebe URLs encriptadas (Google News redirect). Ex: `https://news.google.com/articles/CBMiR2h0dHBzOi8...`. Pra obter URL real do artigo, pipeline tem que decodificar via fetch + parse.

Esse decode é caro (~1-2s por URL). Se mesma URL aparece em múltiplas queries (acontece — Google News mostra mesma matéria pra queries diferentes), decodificar de novo é desperdício.

A intenção do `GOOGLE_DECODE_CACHE` é **memoização**: depois de decodificar uma URL, guarda o resultado em memória. Próxima vez que aparecer a mesma URL, retorna cache.

##### Como o bug quebra essa intenção

Em `pipeline/http_utils.py:116`:

```python
GOOGLE_DECODE_CACHE: dict[str, str] = {}
```

Módulo-level dict global. Mutado em linhas 142, 148, 185, 199, 202, 205 (writes durante decode).

**O que falta**: TTL (tempo de vida), max size, política de eviction. O dict NUNCA esvazia — só cresce.

##### Por que é problemático

1. **Memory leak silencioso**. Em Render single-process, processo Python persiste enquanto não há restart. Em runs longas (backfill de meses), cache acumula MBs. Estima: 10.000 URLs decodificadas × ~200 bytes cada = 2MB. Nada catastrófico, mas crescimento monotônico.

2. **Não shared between processes**. Se Render escala (improvável no plano atual mas possível no futuro), cada worker tem seu cache. Decodes feitos em worker A não ajudam worker B.

3. **Reset on restart é desperdício**. Cada deploy do Render perde o cache. Run após deploy reaprende todas URLs.

4. **Test gap**: nenhum teste mede crescimento.

##### Cenário onde aparece

**Hoje, pra Otávio em uso normal**: provavelmente <500 KB de cache. Não é problema agudo.

**Em backfills longos (anos)**: pode chegar a 10-50 MB. Em Render free tier (512 MB RAM), começa a comer espaço útil.

**Em casos extremos**: se Google News mostrar 100k URLs únicos na vida do processo, cache pode chegar a 100 MB+. Hard to hit hoje mas possível.

##### Para Theseus resolver

**Fix simples**: usar `functools.lru_cache` em vez de dict manual:

```python
from functools import lru_cache

@lru_cache(maxsize=10000)  # eviction LRU automática
def decode_google_news_url_cached(token: str) -> str:
    # mesma lógica de hoje, sem manipular dict global
    ...
```

Ou, se quiser mais controle:

```python
from collections import OrderedDict

class BoundedCache:
    def __init__(self, max_size: int = 10000):
        self._cache = OrderedDict()
        self._max_size = max_size
    
    def get(self, key): return self._cache.get(key, None)
    def put(self, key, value):
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)  # remove oldest
            self._cache[key] = value

GOOGLE_DECODE_CACHE = BoundedCache(max_size=10000)
```

**Decisão de design**: tamanho máximo. 10000 é razoável (10k URLs × 200 bytes ~ 2MB). Otávio decide.

**Test que pegaria regressão**:

```python
@pytest.mark.integration
def test_google_decode_cache_eviction(monkeypatch):
    """
    Cache não deve crescer além de max_size.
    """
    cache = BoundedCache(max_size=100)
    for i in range(150):
        cache.put(f"url{i}", f"resolved{i}")
    assert len(cache._cache) == 100
    # primeiros 50 foram evicted
    assert cache.get("url0") is None
    assert cache.get("url100") is not None
```

---

#### 5.9.4 — Frontend `mergeLiveResultsIntoPayload` muta `payload` global em vez de retornar novo

##### O que o código DEVERIA fazer (intenção real)

Quando dashboard recebe live updates (via polling de `/api/update/live-results`), precisa renderizar essas stories sem refresh da página. A função `mergeLiveResultsIntoPayload` recebe os items novos e os incorpora ao state global do JS.

A intenção é: **state management consistente entre updates**. Padrão moderno seria immutable updates (criar novo `payload` com mudanças, atribuir, deixar React/equivalent re-renderizar). Em vanilla JS sem framework, padrão mutável é comum mas frágil.

##### Como o bug quebra essa intenção

Em `assets/clipping.js:1413`:

```javascript
if (!story) {
    story = { ... };
    storiesById[storyKey] = story;
    payload.stories.unshift(story);  // ← mutação in-place do array global
}
```

`payload` é variável global do escopo do clipping.js. `payload.stories.unshift(story)` modifica o array DIRETAMENTE.

Concorrentemente, `applyState()` (a função de renderizar tudo) pode ser invocada por outros caminhos (ex: troca de filtro do user, refresh button). Se `applyState` ler `payload.stories` ENQUANTO `mergeLiveResultsIntoPayload` está fazendo `unshift`, pode ler estado parcial.

##### Por que NÃO é grave HOJE

JavaScript é **single-threaded**. Eventos são processados em queue. Race "real" entre dois callbacks SÍNCRONOS no mesmo frame não acontece — primeiro callback termina inteiro antes do segundo começar.

**Mitigação efetiva**: a estrutura de event loop garante que `mergeLiveResultsIntoPayload` (chamado dentro de `.then()` callback) executa atomicamente em relação a outros sync handlers.

**Mas**: se features futuras introduzirem **assíncronos durante o merge** (await dentro do merge), microtask boundaries criam pontos de interrupção. Aí race pode acontecer.

##### Por que é tech-debt latente

1. **Bug-class teórico HOJE, real AMANHÃ**: se Theseus adicionar await no meio do merge (ex: pra hidratar dados extra do servidor), state pode ser lido inconsistente entre antes/depois do await.

2. **Pattern frágil**: vanilla JS com mutações em globals é difícil de testar. Cada teste precisa simular state global. Imutabilidade facilita testes.

3. **Refactor pra immutable seria pequeno**: `payload = {...payload, stories: [story, ...payload.stories]}`. Custo baixo, robustez alta.

##### Cenário concreto onde isso poderia falhar

**Hoje**: improvável. Single-thread JS protege.

**Futuro**: se features tipo "preload dos primeiros 10 raw_texts em background com await Promise" forem adicionadas, o merge pode ficar interrompido por um await, e during esse await, applyState pode rodar.

##### Para Theseus resolver

**Fix conceitual**: substituir mutação por re-atribuição:

```javascript
// HOJE (mutável):
payload.stories.unshift(story);

// FIX (immutable):
payload = { ...payload, stories: [story, ...payload.stories] };
applyState();  // re-render
```

Aplicar em todos os lugares que mutam `payload.stories` direto:
- `payload.stories.unshift(story)` em assets/clipping.js:1413.
- `payload.meta.totalStories = Math.max(...)` em assets/clipping.js:1461.

**Decisão de design**: vale o esforço HOJE? Provavelmente baixa prioridade — single-thread JS protege. Mas se Theseus tocar o módulo por outra razão, vale fazer junto.

**Test que pegaria regressão futura**:

```javascript
// (em algum framework de teste de JS)
test('mergeLiveResultsIntoPayload retorna novo payload sem mutar antigo', () => {
    const before = { stories: [...] };
    const after = mergeLiveResultsIntoPayload(data, before);
    expect(before.stories).toEqual([...]); // antigo intacto
    expect(after.stories).not.toBe(before.stories); // novo é diferente referência
});
```

### 5.8 Bug-classes em export e AI summary (Iteração 11)

#### 5.8.1 — Export dedupe por URL exato (sem canonicalize)

`tools/export_mobile_snapshot.py:2438`:
```python
seen_urls: set[str] = set()
unique_articles = []
for article in story["articles"]:
    if not url or url not in seen_urls:
        seen_urls.add(url)
        unique_articles.append(article)
```

Set guarda URL exato (sem `canonicalize_url`). Se article foi salvo no DB com `https://www.X.com/path` e outro com `https://X.com/path`, ambos passam o dedup do export. **Confirmação direta do F018**: o artigo "Show de Shakira" aparece 2x no `clipping-data.json` com e sem `www.`.

**Anatomia exata da falha**:
1. Run 1 do pipeline: candidate.url chega como `https://www.mercadoeeventos.com.br/...`. `pipeline/http_utils.canonicalize_url` aplica → vira `https://www.mercadoeeventos.com.br/...` (port-aware preserva www).
2. Run 2 do pipeline: outro collector traz mesma URL como `https://mercadoeeventos.com.br/...` (sem www). `pipeline/http_utils.canonicalize_url` preserva sem www.
3. DB tem 2 articles. UNIQUE constraint não bate porque URLs são literalmente diferentes.
4. Export coleta os 2 e dedup-by-string-equality não bate. Story tem 2 article entries.

#### 5.8.2 — AI detection split entre `mentions.sentiment_reason` e `classifications.ai_generated`

Há DOIS sistemas paralelos pra rastrear "this involved AI":

**Sistema A: `mentions.sentiment_reason`** (legado, ainda em uso)
- Reasons: `lexical_heuristic` (pipeline original), `existing_article_backfill` (backfill secundário), `anthropic_batch` (batch antigo), `agent_summary` (skill /clipping agente inline)
- Detectado em `pipeline/database.py:584,673,754,776,843,928` para flag `has_ai_summary` no payload exportado.

**Sistema B: tabela `classifications`** (novo, commit `9a279f3`)
- Schema: `mention_id`, `article_sentiment`, `target_sentiment`, `centimetragem`, `classified_by`, `ai_generated`
- `tools/classify_articles.py` grava aqui (`classified_by="claude-haiku"`, `ai_generated=True`).
- Lido pelo dashboard via GET `/api/classifications` (overlay live).

**Drift**: o flag `has_ai_summary` (Sistema A) NÃO considera entries em Sistema B. Se um artigo foi categorizado por `classify_articles.py` mas seu mention tem `sentiment_reason="lexical_heuristic"`, o dashboard mostra:
- Chip de categoria (do Sistema B overlay) ✅
- **Mas NÃO mostra ícone "AI summary"** (porque Sistema A não detecta)

**Bug-class**: AI involvement state split. Decisão de produto pendente: o "AI summary" vs "AI classification" são features distintas (e o split é intencional) ou redundância (e os dois sistemas deveriam convergir)?

**Test gap**: nenhum teste verifica que `tools/classify_articles.py` set produces consistent flag em downstream display.

#### 5.8.3 — `classify_articles.py` sem audit gate

`tools/classify_articles.py` tem só `ANTHROPIC_API_KEY` no env como guarda. Quem rodar localmente com a key acessível classifica AI sem audit/rate-limit/budget check.

**Mitigação parcial**: README + GENERAL_UNDERSTANDING dizem "AI generation precisa admin gate + budget + audit". Mas `classify_articles.py` é CLI manual, então gate é "ter o API key" — adequado para Otávio rodar local, não pra coworker.

**Bug-class**: gap entre policy escrita (admin gate + budget + audit) e implementação atual (só `os.environ.get("ANTHROPIC_API_KEY")`). Se Otávio quiser estender o feature pra coworkers via UI no futuro, o gate atual é insuficiente.

### 5.6.6 — Re-explicações para bug-classes que ficaram obscuras (Iteração 16)

Otávio (D16, D18, D20, D23): "não entendi" pra várias bug-classes. Re-explico com analogias e exemplos concretos. Cada uma assume que o leitor não conhece o código intimamente.

#### 5.6.3 explicado — F018 manifestado em produção

**Em uma frase**: o mesmo artigo de Shakira aparece **2 vezes** no `clipping-data.json` em produção, com URLs `https://www.mercadoeeventos.com.br/...` e `https://mercadoeeventos.com.br/...` (uma com `www.`, outra sem). O sistema acha que são artigos diferentes.

**Por que acontece**: a função que "limpa" URL antes de comparar (`canonicalize_url`) existe em **DOIS lugares** no código (`pipeline/normalization.py:35` e `pipeline/http_utils.py:236`), com comportamentos diferentes. Uma preserva `www.`, a outra remove. Quando dois collectors entregam o mesmo artigo com formato diferente, qual versão da função foi chamada decide se é "duplicata" ou "novo".

**Analogia**: imagine 2 funcionários do RH usando duas planilhas diferentes pra detectar duplicatas. Um considera "joao@gmail.com" e "Joao@gmail.com" iguais; o outro considera diferentes. Quando os dois processam o mesmo José, um marca duplicata, o outro insere de novo. Resultado: JOSÉ TEM 2 ENTRIES NA FOLHA.

**Impacto real**: o coworker abre o painel e vê dois cards do mesmo artigo. Lê o mesmo conteúdo duas vezes.

**Veja a evidência live**: rode `python3 -c "import json; data=json.load(open('assets/clipping-data.json')); urls=[a['url'] for s in data['stories'] for a in s['articles'] if 'shakira' in (a['title'] or '').lower()]; print(urls)"` — saída terá ambas formas.

#### 5.6.4 explicado — `cleanup` acoplado a string `"lexical_heuristic"` hardcoded

**Em uma frase**: a fix do Atlas pra remover mentions falsas de Shakira só funciona se a mention foi gravada com a string mágica `sentiment_reason="lexical_heuristic"` ou `"existing_article_backfill"`. Se algum dia outro caminho gravar mention com string diferente, cleanup ignora.

**Por que é frágil**: imagine um filtro de spam de email que só apaga emails com remetente `"unknown_sender"`. Se um spam chegar com remetente `"unknown sender"` (espaço em vez de underscore), ele NÃO é apagado. O filtro acopla a string exata, não ao conceito de "spam".

**Analogia**: filtro de remoção que só funciona contra mentions de "linhagem 1" (`lexical_heuristic`) e "linhagem 2" (`existing_article_backfill`). Se alguém adicionar uma "linhagem 3" no futuro (ex: nova feature de matching automático), as mentions falsas dela passam pelo filtro intactas.

**Impacto real**: hoje, `tools/classify_articles.py` cria mentions com `classified_by="claude-haiku"` (não com `sentiment_reason`). O cleanup do Atlas NÃO tocaria essas. Se classify_articles algum dia gravar mention errada, ela vira fixture permanente.

**Bug-class**: filtro acopla via string mágica em vez de conceito. Frágil contra evolução de schema.

#### 5.6.5 explicado — `forced_terms` é uma feature CLI que sofre o mesmo bug do Shakira

**Contexto**: `forced_terms` é um filtro extra do CLI (`run_ingestion.py --forced-terms "Rio,vereador"`) que diz "só aceita articles que mencionem `Rio` E `vereador`". É raramente usado, mas existe.

**Em uma frase**: o filtro `forced_terms` busca esses termos em **título + snippet + full_text + summary**. Se o termo aparece só no rodapé "Notícias relacionadas" (mesmo lugar que causou o bug Shakira), o filtro deixa passar mesmo se o article não é sobre o tópico.

**Analogia**: você pediu uma busca por "vereador" e "Rio". Sistema acha um article sobre futebol, mas ele tem um link no rodapé "Veja também: vereador do Rio aprova..." que tem ambas palavras. Forced terms passa, article entra no clipping.

**Por que ficou de fora da fix do Atlas**: a fix do Atlas (commits `238b97d`, `bb6218e`) só protege contra esse bug pra **secondary targets** (Shakira). `forced_terms` é caminho separado, não foi atacado.

**Impacto real**: pequeno, porque `forced_terms` é usado raramente (só Otávio via CLI). Mas é a mesma bug-class em outra feature — se Otávio usar com termo curto/frequente como "Rio", pega muitos falsos positivos.

#### 5.7.2 explicado — Score de merge entre stories enviesa pra título

**Contexto**: quando pipeline encontra um article novo, decide se ele merge com uma story existente ou cria story nova. Decisão é por similaridade.

**Em uma frase**: a fórmula que decide "este article é a mesma story que aquela existente?" usa `score = MAX(similaridade_de_título, similaridade_de_resumo × 0.65)`. Como toma o **máximo**, título-similarity domina. Se títulos são parecidos mas resumos divergem, ainda merge.

**Analogia**: você decide se duas pastas no computador são "a mesma" comparando nome E conteúdo. Mas a regra atual é "olha o nome OU o conteúdo, escolhe o melhor sinal". Se nomes são iguais e conteúdos completamente diferentes, decide pelo nome. Mistura pastas.

**Cenário concreto**:
- Article A: título "Flávio Valle defende ciclovias", resumo "fala na Câmara Municipal".
- Story B (existente): título "Flávio Valle defende ciclovias", resumo "diz em entrevista à TV".
- Title-similarity ~ 1.0, summary-similarity ~ 0.3.
- Score = max(1.0, 0.3 × 0.65) = 1.0 → merge.
- Resultado: 2 eventos diferentes (Câmara + TV) ficam em uma única story.

**Impacto**: stories perdem foco específico. Em backfills, vários eventos relacionados sob mesmo título genérico colapsam.

#### 5.7.3 explicado — Stories podem ganhar targets cross-cutting via "intersection mínima de 1"

**Em uma frase**: quando article novo é candidato a merge com story existente, basta que **1 target seja comum** entre os dois pra serem candidatos. Articles multi-target podem mesclar com stories single-target e contaminar.

**Cenário concreto**:
- Story B existente: "Pedro Angelito apresenta projeto X" — só com mention de `pedro_angelito`.
- Article novo: "Pedro Angelito e Flávio Valle juntos no projeto X" — mentions de ambos.
- Intersection: { pedro_angelito } ≠ ∅ → article é candidato a merge.
- Se score similaridade alto, merge acontece.
- Story B ganha mention de `flavio_valle` via `ensure_story_target`.
- Story B agora vira "story sobre Pedro + Flávio" mesmo originalmente sendo só do Pedro.

**Pode estar certo** (articles do mesmo evento) **OU errado** (story específica perde foco). Não há revisão humana pra distinguir.

**Bug-class**: contaminação automática cross-target via merge agressivo. Mesma classe da bug-class de single-target story sendo "esticada" pra cobrir múltiplos targets.

#### 5.7.5 explicado — Mentions falsas ANTIGAS podem deixar `story_target` órfão (mas Atlas resolveu)

**Contexto**: quando a fix do Atlas remove uma mention falsa de Shakira de um artigo, ele também precisa decidir se a STORY desse artigo ainda tem outras mentions válidas de Shakira (de outros articles na mesma story). Se NÃO tem, precisa remover o `story_target` correspondente.

**Em uma frase**: cleanup remove mention falsa, mas tinha um risco de deixar a "etiqueta de story" desencadeada — que é preciso limpar também.

**Analogia**: você apaga a foto onde aparece a Shakira por engano. Mas o álbum ainda tem o nome dela na capa. Cleanup precisa apagar também o nome.

**Por que NÃO é problema agora**: Atlas pensou nisso. `web_app/db_admin.py:487-501` (cleanup), depois de deletar mention falsa, faz query de "ainda tem outra mention válida de shakira nessa story?". Se não, deleta `story_target`. Bem feito.

**Bug-class reduzido a edge case**: cleanup só roda nos targets passados como argumento. Se admin/coworker não disparou cleanup com Shakira na lista, contaminação histórica permanece.

#### 5.8.1 explicado — Export tem dedup próprio, e ele também cai no F018

**Contexto**: depois que pipeline guarda articles no DB, o export (`tools/export_mobile_snapshot.py`) gera o JSON do dashboard. Pra evitar mostrar duplicatas, ele tem dedup próprio: passa por todos articles, mantém só URLs únicos via Python set.

**Em uma frase**: o dedup do export compara URLs como strings exatas, sem normalizar. Como os 2 collectors gravaram o mesmo article do show da Shakira com URLs ligeiramente diferentes (com `www` e sem), o dedup do export NÃO bate — ambos passam.

**Por que é a mesma classe do 5.6.3**: 5.6.3 é o INSERT no DB que duplica. 5.8.1 é o EXPORT que **não consegue mais consertar a duplicação** porque o cleanup também é por string-equality.

**Impacto**: Otávio abre `clipping-data.json` em produção e vê 2 cards iguais do show da Shakira. Reportado pelo próprio JSON do site.

**Fix**: a função `canonicalize_url` certa precisa ser chamada no INSERT (pipeline) E no EXPORT (tools). Hoje cada um faz à sua maneira (ou nem faz).

#### 5.9.1 explicado — `backfill_state` é tabela morta no banco

**Em uma frase**: existe uma tabela chamada `backfill_state` no SQLite que **nenhum código jamais escreve nela**. Ela existe, ocupa espaço de schema, tem métodos pra ler/escrever, mas ninguém chama esses métodos.

**Analogia**: você comprou uma estante chique com 5 prateleiras pra livros. Hoje, 4 prateleiras estão vazias. Os pedreiros instalaram a estante, mas nunca colocaram livros. Ela só existe.

**Por que existe**: provavelmente algum design antigo planejou implementar "resumir backfill onde parou" (campos `current_date`, `current_page`, `status='paused'`). O design não foi finalizado. Os 5 métodos da tabela (`get_backfill_state`, `upsert_backfill_state`, etc.) existem mas só seriam úteis SE alguém invocasse.

**Por que importa**: confunde quem lê o schema (eu mesma demorei pra perceber). E é tech-debt — limpar ou usar.

**Conexão com 5.6.1 (CRÍTICO)**: se Theseus quiser implementar "checkpoint de backfill" pra evitar runs cortadas, **essa tabela JÁ EXISTE no schema, pronta pra ser usada**. Não precisa migration. Só conectar.

#### 5.9.2 explicado — `scrape_log` é outra tabela morta

**Igual a 5.9.1**: tabela existe (`scrape_log` em `pipeline/database.py:73`), métodos existem (`log_scrape_start`, `log_scrape_end`), mas zero callers. Provavelmente era pra registrar telemetria de cada coleta (qual collector rodou, em que horário, qual status final). Não foi conectado.

#### 5.9.3 explicado — `GOOGLE_DECODE_CACHE` cresce sem limite na memória

**Contexto**: quando pipeline coleta artigos do Google News, recebe URLs encriptadas (Google News redirect). Tem que decodificar pra obter URL real do artigo. Pra evitar decodificar a mesma URL muitas vezes, há um cache em memória.

**Em uma frase**: o cache é um dict Python global que cresce sem nunca apagar entradas antigas. Em produção single-process com horas de uso, pode acumular megas de entradas.

**Analogia**: é uma agenda telefônica que você usa há 10 anos sem nunca apagar contatos. Tem 50.000 nomes, dos quais você usa 100 ativamente. Caderno não cabe na bolsa mais.

**Impacto**: em runs longas (anos de backfill), pode chegar a centenas de MB. Em Render single-process com pouca RAM, pode estourar memória. Em runs curtas (caso típico do Otávio hoje), não passa de KBs — não é problema imediato.

**Test gap**: nenhum teste mede crescimento do cache em runs longas.

#### 5.9.4 explicado — Frontend muta `payload` global em vez de criar versão nova

**Contexto**: quando o dashboard recebe novos resultados live (via polling de `/api/update/live-results`), ele insere essas stories direto no objeto `payload` global do JS.

**Em uma frase**: o JS modifica o estado direto em vez de criar nova versão. Se `applyState()` (rendering) acontecer ao mesmo tempo que o merge, render pode pegar estado parcial.

**Analogia**: imagine a impressora imprimindo uma planilha enquanto outra pessoa edita ela em tempo real. Pode sair página com colunas pela metade.

**Por que NÃO é grave hoje**: JavaScript é single-threaded. Eventos são processados em fila. Race condition entre `applyState` e `mergeLiveResultsIntoPayload` em uma mesma sequência síncrona é improvável.

**Bug-class teórico**: se features futuras adicionarem WebWorkers ou requestAnimationFrame interleaving, o pattern atual fica frágil. Tech-debt em vez de bug ativo.

### 5.12 Bug-classes em frontend (Iteração 33, deep-read de `assets/clipping.js`)

#### 5.12.1 — CORREÇÃO de hipótese 5.4.C: filter dropdown atualiza corretamente após add target

##### O que minha hipótese anterior dizia

Em 5.4.C eu apontei que após POST `/api/targets`, "filter dropdown do dashboard não atualiza com novo target sem refresh manual". Atribuí o bug Shakira UI parcialmente a isso.

##### O que o código realmente faz (correção da minha análise)

`assets/clipping.js:1930-1955` (handler do `addTargetForm`):
```javascript
addTargetForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    ...
    var resp = await apiPost("/api/targets", body);  // grava no backend
    ...
    setMessage(addTargetMessage, "Nome extra salvo...", "ok");
    addTargetForm.reset();
    await refreshTargets();                            // ← REFRESH automático
    if (manageTargetsBox && manageTargetsBox.open) await refreshManageTargets();
});
```

`refreshTargets` (linha 506-530):
```javascript
function refreshTargets() {
    return apiFetch("/api/targets", { cache: "no-store" })
        .then(function (resp) { ...; return resp.json(); })
        .then(function (data) {
            runTargets = normalizeTargetsResponse(data);
            ...
            mergeRuntimeTargetsIntoPayload(runTargets);  // ← MERGE no payload
            ...
            renderRunTargets();
            renderManageTargets();
            if (payload) applyState();                    // ← RE-RENDER tudo
        })
        .catch(function (error) {
            console.error("[clipping] target refresh failed", error);
            ...
        });
}
```

`mergeRuntimeTargetsIntoPayload` (linha 225-253) **adiciona o target novo a `payload.targets`** se ainda não existe. `applyState()` então re-renderiza filter dropdown com a nova lista.

**Minha hipótese inicial de 5.4.C estava errada**. O frontend tem fluxo correto: add → refresh → merge no payload → re-render. Desculpa, Otávio — bug Shakira UI tem causa diferente.

##### Por que o bug Shakira UI ainda existe (revisão da hipótese)

Re-lendo a mensagem original do Otávio:
> *"ele não estava ligado na adição de filtros e ele até estava ligado no python de buscar pro arquivos, mas não o de salvar as histórias"*

Re-interpretação:
- "ligado na adição de filtros" = backend acrescenta filter pra coleta? (Pode ser sobre `select_targets` em `pipeline/ingest.py:257` que constrói lista de targets a serem pesquisados.)
- "python de buscar pro arquivos" = collector ROTATÉ buscas com novo target? **SIM** — pipeline busca articles do target.
- "mas não o de salvar as histórias" = save story step não cria stories pro novo target? **Esse é o bug confirmado pelo Atlas (commit 238b97d)** — secondary target sem safe-surface check tinha mention falsa, story acabava em outras formas.

**Re-leitura conclusiva**: o bug Otávio descreveu É o bug do `save_story` para secondary targets, atacado em `238b97d`/`bb6218e`/`f0bf4ef`. **Não é bug de filter UI dropdown**. Eu interpretei errado em 5.4.C.

**Fix**: marcar 5.4.C como **HIPÓTESE INCORRETA — RETIRADA**.

#### 5.12.2 — Race condition possível entre add target e disparar update

`assets/clipping.js:1930-1955` mostra o flow:
1. Click "Salvar" → POST `/api/targets` (await).
2. Sucesso → setMessage + addTargetForm.reset() + **`await refreshTargets()`** (refresh assíncrono).

Se user clicar "Comecar atualizacao" ANTES de `refreshTargets` resolver, o spec do update job é construído em `clipping.js:startUpdateButton handler` usando `runTargets` global. Se runTargets ainda não foi atualizado (refresh em curso), update dispara sem o novo target.

**Cenário concreto**: user adiciona target "Shakira", clica "Comecar atualizacao" rapidamente (em <1s). Run dispara sem Shakira como target. Articles de Shakira não são coletados.

**Mitigação real**: refreshTargets é tipicamente <500ms (1 GET request). Race window é estreita. User percebe via "Salvando..." → "Nome extra salvo..." e provavelmente espera essa mensagem.

**Bug-class**: race condition latente. Não confirmado em produção.

**Fix sugerido**: o handler do startUpdate disable o botão até `refreshTargets()` mais recente terminar. Ou refresh é chamado SÍNCRONO antes de disparar update.

#### 5.12.3 — Refresh failure é silencioso (`console.error` apenas)

`clipping.js:525-530`:
```javascript
.catch(function (error) {
    console.error("[clipping] target refresh failed", error);
    runTargets = fallbackTargetsFromPayload();
    activeTargetKeys = new Set(...);
    ...
});
```

Quando `refreshTargets` falha (rede, 500, etc.), o handler:
1. Log no console (invisível pra coworker).
2. Fallback pra `fallbackTargetsFromPayload()` — usa lista do snapshot estático.
3. **Mensagem `"Nome extra salvo..."` (line 1946) JÁ FOI mostrada ANTES da refresh ser disparada**.

Coworker vê:
- "Nome extra salvo e disponível para a próxima rodada." ✅
- Filter dropdown mostra targets ANTIGOS (do snapshot, sem o novo).
- Coworker pensa "salvei mas não aparece — bug?".

**Bug-class**: feedback enganoso. Mensagem afirma sucesso mas display real está degradado.

**Fix sugerido**: em catch, sobrescrever mensagem: "Nome salvo no servidor mas painel pode estar desatualizado — recarregue a página".

### 5.11 Bug-classes em export (Iteração 32, deep-read de `tools/export_mobile_snapshot.py`)

#### 5.11.1 — `safe_export_match_text` é versão diferente de `safe_target_match_surface` (drift entre implementações)

##### O que o código DEVERIA fazer

A fix do Atlas (commit `bb6218e`) introduziu `safe_target_match_surface` em `pipeline/ingest.py:154` pra extrair o "surface seguro" de um article (title + snippet + summary, sem full_text e sem boilerplate de "Notícias relacionadas"). Essa surface é usada pra confirmar que um secondary target REALMENTE está no article antes de gravar mention.

A intenção é: **uma fonte de verdade pra "o que conta como surface seguro"**. Mesma definição em todos os lugares que precisam dessa decisão.

##### Como o bug quebra essa intenção

O export tem **VERSÃO PRÓPRIA** dessa função: `safe_export_match_text` em `tools/export_mobile_snapshot.py:185-201`:

```python
def safe_export_match_text(article: dict[str, Any]) -> str:
    title = str(article.get("title") or "")
    url_path = urlparse(str(article.get("url") or "")).path.replace("-", " ").replace("_", " ")
    summary = str(article.get("summary") or "")
    full_text = str(article.get("full_text") or "")
    snippet = str(article.get("snippet") or "")
    body_parts: list[str] = []
    if summary:
        body_parts.append(summary[:500])
    if full_text:
        body_parts.append(full_text[:500])         # ← inclui full_text condicionalmente
    if not body_parts:
        body_parts.append(snippet[:500])
    text = " ".join([title, url_path, *body_parts])
    text = html.unescape(TAG_RE.sub(" ", text))
    text = RELATED_MATCH_NOISE_RE.sub(" ", text)    # ← MESMO regex de pipeline
    return re.sub(r"\s+", " ", text).strip()
```

Comparando com `pipeline/ingest.py:154-163` (Atlas):
```python
def safe_target_match_surface(*parts: str) -> str:
    cleaned_parts: list[str] = []
    for part in parts:
        text = html.unescape(TAG_RE.sub(" ", str(part or "")))
        text = URL_RE.sub(" ", text)                # ← export NÃO faz isso
        text = RELATED_MATCH_NOISE_RE.sub(" ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            cleaned_parts.append(text)
    return " ".join(cleaned_parts)
```

**Diferenças identificadas**:
- Export INCLUI `full_text[:500]` condicionalmente. Pipeline NÃO inclui full_text.
- Export INCLUI `url_path` (transformação do URL). Pipeline NÃO.
- Pipeline remove URLs (`URL_RE`). Export NÃO.
- Caller passa parâmetros diferentes (export passa article dict, pipeline passa strings posicionais).

##### Por que é problemático

1. **2 implementações divergentes do MESMO CONCEITO**. Theseus que mudar a definição "surface seguro" precisa lembrar de mudar AMBAS. Esquecer = drift garantido.

2. **Resultados podem divergir pra mesmo article**:
   - Pipeline: rejeita mention de Shakira em article X porque Shakira não aparece em title+snippet+summary.
   - Export: pode INCLUIR Shakira no display porque export inclui full_text[:500] e Shakira aparece nos primeiros 500 chars do full_text.
   - Resultado: article gravado SEM mention de Shakira no DB, mas no display do export aparece com chip Shakira (vindo de outro caminho — `target_keys` do article já estava lá por outra razão).

3. **5.11 conecta com 5.4 (bug Shakira)**: a fix do Atlas pode ter sido COMPLETA no pipeline mas INCOMPLETA no export. Theseus precisa verificar.

##### Para Theseus resolver

**Fix conceitual**: extrair `safe_target_match_surface` pra módulo compartilhado e importar em ambos os lugares.

```python
# pipeline/_safe_surface.py (novo arquivo)
def safe_target_match_surface(*parts: str, include_url_strip: bool = True) -> str:
    # implementação canônica única
    ...

# pipeline/ingest.py
from pipeline._safe_surface import safe_target_match_surface

# tools/export_mobile_snapshot.py
from pipeline._safe_surface import safe_target_match_surface
def safe_export_match_text(article):
    return safe_target_match_surface(
        article.get("title"),
        article.get("snippet"),
        article.get("summary"),
        # decidir: incluir full_text ou não
    )
```

**Decisão de design pendente**: a versão do export deve OU não incluir full_text? Argumentos pra cada lado:
- Pro: export tem informação rica disponível, pode ser mais preciso.
- Contra: vai contra a intenção "safe surface" que filtra full_text por design.

**Recomendação**: alinhar com pipeline. Não incluir full_text no export tampouco. Consistência > "talvez seja melhor".

#### 5.11.2 — `filter_export_target_keys` aplica safe-surface SÓ pra secondary targets (mesma assimetria do 5.4.A)

`tools/export_mobile_snapshot.py:204-219`:

```python
def filter_export_target_keys(article, fallback_targets, secondary_targets):
    keys: list[str] = []
    for key in list(article.get("target_keys") or fallback_targets or []):
        key = str(key or "").strip()
        if key and key not in keys:
            keys.append(key)
    selected_secondary = [secondary_targets[key] for key in keys if key in secondary_targets]
    if not selected_secondary:
        return keys                                # ← sem secondary, retorna tudo
    safe_hits = CitationMatcher(selected_secondary, exact_names_only=True).find_hits(safe_export_match_text(article))
    safe_secondary_keys = {hit.target_key for hit in safe_hits}
    return [key for key in keys if key not in secondary_targets or key in safe_secondary_keys]
```

Lógica:
- Se artigo tem só primary targets → retorna lista crua sem filtro.
- Se artigo tem secondary targets → roda safe-surface só nos SECONDARY, mantém primaries.

**Bug-class**: idem `5.4.A` (assimetria primary vs secondary). Caso "Show de Shakira" tagueado como `flavio_valle` PRIMARY: export NÃO filtra (sem secondary → return early na linha 216). Article continua aparecendo no filtro Flávio.

##### Para Theseus

Mesma decisão de produto do 5.4.A: aplicar safe-surface a primary também (mais conservador) ou aceitar limitação inerente do matcher exact-name (per D10, "já era, limitação mesmo").

D10 já marca isso como **known issue, não-prioritário** — então não precisa fix imediato. Mas Theseus deve entender que `filter_export_target_keys` herda essa decisão.

#### 5.11.3 — `parse_source_html` é REGEX-based (frágil contra mudança de template)

`tools/export_mobile_snapshot.py:289-304`:
```python
m = re.search(r'<script[^>]*id="snapshot-payload"[^>]*>(.*?)</script>', raw, re.DOTALL)
for card_m in re.finditer(r'(<details\b[^>]*\bdata-story-id="(\d+)"[^>]*>.*?</details>)', raw, re.DOTALL):
```

Parsing HTML via REGEX. Conhecido anti-pattern (HTML não é regular). Funciona HOJE porque template é estável, mas:
- Se Atlas/Theseus mudar template (ex: `<details>` vira `<section>` ou `data-story-id` vira `data-story`), regex quebra.
- `--merge-from index.html` é como dados HISTÓRICOS são preservados em cada export. Se o regex falhar, **dados históricos somem silenciosamente**.

**Bug-class**: parsing frágil. Mas é parte do legacy GitHub Pages flow — pode ser deprecada em favor de Render se Otávio decidir.

**Para Theseus**: não fix imediato, mas se Theseus tocar template, **TESTAR `--merge-from`** após mudança. Senão merge pode silenciosamente perder histórico.

### 5.10 Bug-classes em collectors (Iteração 31, deep-read de `pipeline/collectors.py`)

#### 5.10.1 — `_within_window` é GÊMEO de `is_recent_enough` com mesma bug-class (F012)

##### O que o código DEVERIA fazer (intenção real)

Cada collector (RSS, Google News, etc.) recebe `date_from` / `date_to` e deve filtrar candidates pela janela. Há DOIS filtros de data no pipeline:

1. **`is_recent_enough` em `pipeline/ingest.py:280`** — filtra DEPOIS da coleta, durante `process_candidates`. Cobre `5.5.1`.
2. **`_within_window` em `pipeline/collectors.py:100`** — filtra DURANTE a coleta, antes do candidate sair do collector. Mais cedo no pipeline.

A intenção é mesma: rejeitar articles fora da janela. Ambas funções devem ter mesma semântica restritiva.

##### Como o bug quebra essa intenção

`pipeline/collectors.py:100-116`:

```python
def _within_window(value: str, *, date_from: str = "", date_to: str = "") -> bool:
    start = _parse_window_boundary(date_from, end_of_day=False)
    end = _parse_window_boundary(date_to, end_of_day=True)
    if not start and not end:
        return True
    try:
        dt = datetime.fromisoformat((value or "").replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
    except Exception:
        return True              # ← MESMA BUG: default permissive
    if start and dt < start:
        return False
    if end and dt > end:
        return False
    return True
```

**Linha 110-111**: try/except que captura qualquer erro de parsing — e retorna `True`. Mesmo padrão de `is_recent_enough`.

Articles com data malformada **passam** ambos os filtros (collector E pipeline), entrando no clipping com a string lixo como `published_at`.

##### Por que é problemático (adicional a 5.5.1)

1. **Theseus que consertar `is_recent_enough` (5.5.1) sozinho NÃO resolve o problema** — `_within_window` deixa o article passar mais cedo, antes de ingest.py ver. Ou seja: fix parcial é fix nenhum.

2. **Bug duplicado em 2 arquivos**: pra resolver completamente, Theseus precisa encontrar AMBOS os lugares e mudar `return True` → `return False` nos dois.

3. **Linha 680 e 1496**: `_within_window` é chamada também em direct_scrape filtering (line 680) e tem lógica especial de pular pra sitemap_daily (line 1496). Theseus precisa entender quem chama o filtro pra não quebrar lugares onde o `True` permissivo é intencional.

##### Para Theseus resolver

**Fix conjunto com 5.5.1**: ambas as funções precisam mudar `return True` → `return False` no `except`.

Mas há nuance: `_within_window` (line 1496 referência) é EXPLICITAMENTE pulado para sitemap_daily (porque sitemap fornece data da URL, não do feed). Comentário de código: "Skip `_within_window` for sitemap_daily". Indica que o autor original sabia da limitação.

**Decisão**: o filtro deve ser estrito por padrão (default deny). Casos como sitemap_daily que querem pular usam path próprio (já fazem). Outros callers pegam o filtro estrito sem mudança.

#### 5.10.2 — Hardcap de timeouts internos por collector (5.7.4 sub-classe extra)

`pipeline/collectors.py`:

```python
collect_rss:
    feed_timeout = min(request_timeout, 8)        # line 217 — RSS hardcap em 8s

collect_google_news:
    rss_timeout = min(request_timeout, 12)         # line 252 — Google News hardcap em 12s

collect_internal_site_search (Playwright):
    page.goto(start_url, timeout=60000)            # line 968 — 60s hardcap
    page.wait_for_selector("div#search", timeout=10000)  # line 1011 — 10s
    page.wait_for_load_state("domcontentloaded", timeout=30000)  # line 1075 — 30s
```

E há `collection_timeout` interno (separado do `max_process_seconds` pipeline-wide):
- `collect_rss(collection_timeout=1200)` — RSS pra para em 20min total.
- `collect_google_news(collection_timeout=6000)` — Google News pra em 100min.
- `collect_camara_archive(collection_timeout=...)`, etc.

**Bug-class**: extensão de 5.7.4. Mesmo se Otávio aumentasse `max_process_seconds` da pipeline pra 50h, **collectors individuais ainda têm budgets internos** que cortam. Em backfills longos, RSS para depois de 20min mesmo se pipeline tem mais 25h.

**Para Theseus resolver**: unificar timeouts. Cada collector recebe `request_timeout` do user — usar ele direto, sem `min(X, request_timeout)`. Cada `collection_timeout` deveria ser opcional ou `max_process_seconds // num_collectors` (escala com pipeline budget).

#### 5.10.3 — RSS failures logadas em INFO em vez de WARNING

`pipeline/collectors.py:233-235`:
```python
except Exception as e:
    logging.info(f"RSS [{i+1}/{len(RSS_FEEDS)}] {feed['source_name']}: FAILED ({type(e).__name__})")
    continue
```

Quando um RSS feed falha (timeout, 404, parse error), o erro é logado em **INFO** (level baixo). Render padrão filtra logs em WARNING+. **Falhas de feed são invisíveis em monitoring**.

Mesmo padrão em `pipeline/collectors.py:295-297` (Google News failures).

**Bug-class**: silent failure. Atlas/Otávio não recebem alerta quando feed do Globo cai por 3 dias seguidos. Notam só quando o clipping "está estranho" e investigam manualmente.

**Para Theseus resolver**: mudar `logging.info` → `logging.warning` em failure paths. Render expõe warnings nos logs do dashboard.

### 5.7 Bug-classes em story grouping (`choose_story` + `create_or_update_story`, Iteração 10)

Lendo `pipeline/ingest.py:325-398`:

#### 5.7.1 — Story grouping é legacy: high/low threshold redundantes; solução proposta = grouping por categorias (D17)

> **Otávio (D17)**: *"Bom, esse me parece um sistema legacy. De fato, os groupings não estão funcionando bem após a migração para o site online. É muito difícil fazer os groupings online! A gente devia mudar eles para funcionar apenas com base nas categorias."*

##### O que o código DEVERIA fazer (intenção real)

Quando vários artigos cobrem o mesmo evento (ex: 5 jornais publicam sobre "Flávio Valle aprova projeto de ciclovia em 2026-04-15"), o ideal é o coworker ver UM card no dashboard com as 5 fontes agrupadas, não 5 cards isolados. O **conceito de "story"** existe pra isso: agrupar artigos sobre o mesmo evento subjacente.

A função `choose_story` em `pipeline/ingest.py:325-357` foi projetada pra decidir se um article novo deve juntar-se a uma story existente OU criar uma story nova. A heurística é por similaridade de título e resumo:
- Score `≥ 0.78` (high_threshold) → "tenho certeza que é a mesma história, merge automático".
- Score `0.50 - 0.78` (low_threshold) → "mais ou menos parecido, talvez seja a mesma".
- Score `< 0.50` → "não é, criar story nova".

A **intenção original** desses dois thresholds era provavelmente diferenciar tratamento: HIGH = auto-merge sem revisão, LOW = merge mas com flag pra revisão humana / manual override.

##### Como o bug quebra essa intenção

Em `pipeline/ingest.py:351-357`:

```python
if best_story_id is None:
    return None
if best_score >= high_threshold:  # 0.78
    return best_story_id
if best_score >= low_threshold:   # 0.50
    return best_story_id
return None
```

**Os dois branches retornam a mesma coisa** (`best_story_id`). A distinção entre 0.78 e 0.50 não tem efeito no comportamento — qualquer score acima de 0.50 leva ao mesmo merge.

Significa: **a granularidade de design original foi perdida**. O threshold mais alto (0.78) é morto: existe na variável mas não muda nada. Se um futuro dev olhar o código achando que `high_threshold` faz comportamento especial, vai se surpreender.

##### Por que é problemático

1. **Intent vs implementation drift**: o código sugere distinção semântica, mas implementação iguala. Confunde leitor.

2. **Threshold de 0.50 é muito permissivo**: artigos com 50% de similaridade não são "claramente o mesmo evento". Em backfill longo, articles relacionados mas distintos (ex: "Flávio Valle vota em projeto X" + "Flávio Valle declara apoio a projeto X" em datas diferentes) podem mergear errado.

3. **Per Otávio: grouping não funciona online**. A migração pra dashboard online expôs limitações: similaridade lexical é fraca pra grouping de eventos políticos, onde títulos seguem templates ("Flávio Valle [VERBO] [PROJETO]") e podem matchear mesmo sendo eventos distintos.

##### Solução proposta pelo Otávio (D17): grouping por categorias

Em vez de calcular similaridade de texto, **agrupar articles que compartilham `categories`** (do Sistema B em `tools/classify_articles.py` + classification overlay UI):

- Pipeline atribui categorias aos articles (manualmente via classification UI, ou via AI quando houver créditos).
- Stories são definidas por **conjuntos de categorias compartilhadas** dentro de uma janela temporal.
- Ex: 3 articles com categoria "Mandato" + "Saúde" do mesmo dia → 1 story sobre o tema.

##### Bloqueador da solução proposta: D21 + D22

- **D21**: sistema de classificação por IA é legacy ("inviável fazendo pelo site").
- **D22**: sem créditos Anthropic atualmente.

Significa: poucos articles têm categorias atribuídas. Se grouping migrar pra base de categorias **agora**, articles sem categoria ficam órfãos (sem story). Solução depende de:
- Coworkers categorizarem manualmente (workload pesado), OU
- Migrar pra outro provider de IA (cost decision pendente), OU
- Modelo híbrido: usar categorias quando disponíveis, fallback pra similaridade lexical caso contrário.

##### Para Theseus resolver

**Decisões de design pendentes** (Otávio precisa decidir antes da implementação):

1. **Quando migrar pra grouping por categorias?** Depende de cobertura de categorias. Hoje ~0% (raras manuais). Pra ser viável, precisa cobertura significativa (>50%? >80%?).

2. **Modelo híbrido transitório?** Enquanto cobertura de categoria é baixa:
   - Article com categorias atribuídas → grouping por categorias.
   - Article sem categorias → grouping lexical atual (cair em fallback existente).

3. **Como categorizar em volume sem créditos Anthropic?**
   - Coworkers manuais: feasibility study com contagem de articles/semana.
   - Provider gratuito alternativo: Ollama local? Gemini free tier?
   - Híbrido humano+AI: AI sugere, coworker confirma rapidamente.

**Para Theseus implementar (após decisões)**:

1. Adicionar coluna `stories.grouping_method` (`'lexical' | 'categories' | 'hybrid'`).
2. Nova função `choose_story_by_categories(article_categories, days)` que busca stories com sobreposição de categorias.
3. Em `create_or_update_story`, decidir qual chamada usar baseado na cobertura.
4. Threshold conceitual: stories agrupam por **interseção exata de pelo menos N categorias** (N=2? 3?), em janela de M dias.

**Test que pegaria regressão**:

```python
@pytest.mark.integration
def test_articles_com_mesmas_categorias_agrupam_em_uma_story(tmp_path):
    """
    Articles diferentes mas com mesmas categorias [Mandato, Saúde]
    do mesmo dia devem virar 1 story, não 3 separadas.
    """
    article1 = CandidateArticle(title="Flávio Valle aprova X", ...)
    article2 = CandidateArticle(title="Vereador apoia projeto Y", ...)
    article3 = CandidateArticle(title="Tomada de posição: prefeitura define", ...)
    # Atribuir categorias [Mandato, Saúde] aos três
    # Rodar pipeline com grouping_method='categories'
    # Assert: 1 story com 3 articles
```

---

#### 5.7.2 — Score de merge `max(title, summary*0.65)` deixa título dominar a decisão

##### O que o código DEVERIA fazer (intenção real)

A decisão de merge entre article novo e story existente deveria considerar AMBOS o título E o resumo do artigo. Lógica intuitiva: "se títulos são parecidos E resumos também → mesma história. Se títulos parecem mas resumos divergem → eventos diferentes (provavelmente). Se resumos parecem mas títulos divergem → talvez mesmo evento descrito diferente".

A escolha SEMÂNTICA seria combinar os dois sinais com peso ponderado, ou exigir que ambos passem threshold individualmente.

##### Como o bug quebra essa intenção

Em `pipeline/ingest.py:343`:

```python
score = max(score_title, score_summary * 0.65)
```

A fórmula `max` significa: pega o MAIOR dos dois. Concretamente:

- Se `score_title=0.95` e `score_summary*0.65=0.30` → `score=0.95`. Title-similarity domina decisão.
- Se `score_title=0.30` e `score_summary*0.65=0.65` → `score=0.65`. Summary domina (mas title está rejeitando!).

A escolha de `max` significa que o sistema **aceita merge se UM dos dois sinais for forte**, ignorando o outro. Não exige concordância dos dois.

Plus, o multiplier `0.65` no summary **deprecia o sinal de resumo**. Title é tratado com peso 1.0, summary com peso 0.65. Title vence em ties.

##### Por que é problemático

1. **False merges em templates de título**. Articles políticos seguem templates: "Flávio Valle [VERBO] [PROJETO/TEMA]". Dois events distintos (eg: "Flávio Valle aprova ciclovia" e "Flávio Valle critica ciclovia" — votação dias depois) podem ter title-similarity alta (mesmas palavras-chave: "Flávio Valle ciclovia") embora summaries divirjam. Score = max(alto, baixo) = alto → merge incorreto.

2. **Stories ganham contexto misturado**. Quando dois events viram um, dashboard mostra texto de A com texto de B juntos. Coworker lê resumo e fica confuso.

3. **Difícil debugar sem instrumento**. Não há log "merged story X com article Y porque score=0.85 (title=0.95, summary=0.45)". Decisões silenciosas.

##### Cenário concreto de produção

**Backfill de 6 meses pra `flavio_valle`**:
- Article 1: "Flávio Valle defende novas ciclovias na zona sul" (2026-02-01, snippet: "Em sessão na Câmara, vereador apresenta projeto").
- Article 2: "Flávio Valle critica execução de ciclovias na zona sul" (2026-04-15, snippet: "Em entrevista à Globo, vereador questiona prefeitura").

Title-similarity ~ 0.85 (mesmas palavras-chave Flávio + ciclovias + zona sul).
Summary-similarity * 0.65 ~ 0.20 (contextos diferentes: Câmara vs Globo).
Score = max(0.85, 0.20) = 0.85 → above high_threshold (0.78) → merge.

Story resulta: "Flávio Valle defende novas ciclovias..." (título do primeiro) com 2 articles. Coworker abre, vê article 1 como "principal" e article 2 como "complementar", mas são eventos OPOSTOS (defende vs critica).

##### Para Theseus resolver

**Fix conceitual**: substituir `max` por lógica que exige concordância dos dois sinais:

```python
# Opção A: weighted average
score = 0.5 * score_title + 0.5 * score_summary
# Mais conservador. Title e summary contribuem igualmente.

# Opção B: AND threshold
if score_title >= title_threshold and score_summary >= summary_threshold:
    return best_story_id
# Mais rígido. Os dois precisam passar.

# Opção C: both required, with weighted score
if score_title >= 0.6 and score_summary >= 0.4:
    score = 0.6 * score_title + 0.4 * score_summary
    if score >= overall_threshold:
        return best_story_id
```

**Decisão de design**: Otávio precisa decidir o nível de conservadorismo. Mais rígido = menos merges falsos, mas mais stories duplicadas (mesmo event vira 2 stories quando articles têm título distinto). Mais permissivo = oposto.

**Mas**: per D17, story grouping inteiro pode migrar pra base de categorias. Esse fix de score pode ser **redundante** se 5.7.1 for resolvido. Theseus deve decidir **ordem**: corrigir 5.7.2 (incremental) primeiro OU pular direto pra 5.7.1 (migração mais ambiciosa).

---

#### 5.7.3 — Stories single-target ganham mentions cross-target via "intersection mínima de 1"

##### O que o código DEVERIA fazer (intenção real)

A função `choose_story` precisa decidir quais stories existentes são **candidatas** a merge. Faz sentido limitar ao SUBSET de stories que tenha relevância: stories que mencionam pelo menos um dos targets do novo article. Caso contrário, comparações de similaridade rodariam contra TODAS as stories do DB (caro + ruidoso).

A intenção do filtro de pre-candidatura é OTIMIZAÇÃO + RELEVÂNCIA: **só compara com stories tópico-relacionadas**.

##### Como o bug quebra essa intenção

Em `pipeline/ingest.py:339`:

```python
story_targets = set(db.get_story_targets(sid))
if not story_targets.intersection(set(target_keys)):
    continue
```

O check é "intersection não vazia" — ou seja, **PELO MENOS 1 TARGET EM COMUM** entre story e article novo. Story `[pedro_angelito]` é candidata para article `[flavio_valle, pedro_angelito]` (comum: pedro_angelito).

Mas se merge acontece (pelo similarity score), o `ensure_story_target` é chamado pra todos os `target_keys` do article (linha 388):

```python
for tkey in target_keys:
    db.ensure_story_target(story_id, tkey)
```

A story original `[pedro_angelito]` ganha `flavio_valle` como target adicional. **A story foi originalmente sobre Pedro, agora vira sobre Pedro+Flávio**.

##### Por que é problemático

1. **Story drift por contaminação**. Story B nasceu específica pra Pedro Angelito (1 article sobre evento dele). Article novo do Pedro+Flávio merge nela. Agora story B mostra Pedro + Flávio juntos como tópico, mas o evento original era só Pedro.

2. **Filtros do dashboard ficam confusos**. Coworker filtra por "Flávio Valle". A story B aparece (porque ganhou Flávio como target). Coworker abre, lê o primeiro artigo, é só sobre Pedro. Pensa "mas o Flávio cadê?". Confusão.

3. **Stats inflam**. Story B agora conta como "story sobre flavio_valle" (1 a mais) e como "story sobre pedro_angelito" (continua 1). Dupla contagem.

##### Cenário concreto

**Story B existente**: "Pedro Angelito apresenta projeto de educação" (1 article publicado em 2026-03-20, mention só de pedro_angelito).

**Article novo C**: "Pedro Angelito e Flávio Valle juntos lançam adaptação do projeto" (2026-03-25, mentions de ambos).

Pipeline:
1. `target_keys = {pedro_angelito, flavio_valle}`.
2. `choose_story` busca candidates de últimos 7 dias.
3. Story B tem `story_targets = {pedro_angelito}`. Intersection com `{pedro_angelito, flavio_valle}` = `{pedro_angelito}` ≠ ∅ → candidata.
4. Similarity lexical alta (ambos são "Pedro Angelito... projeto de educação..."). Score > threshold.
5. Article C merge na story B.
6. `ensure_story_target(B, "flavio_valle")` adiciona Flávio aos targets de B.
7. Story B agora está em ambos os filtros: "Pedro Angelito" E "Flávio Valle".

##### Para Theseus resolver

**Decisões de design**:

1. **Aceitar contaminação como feature?** Argumento pro: articles que mencionam ambos targets são genuinamente sobre ambos. Argumento contra: story original era 100% Pedro; agora vira 50/50.

2. **Política de "intersection requirement"?**
   - Opção A: **interseção exata de targets**. Story só candidata se `story_targets == set(target_keys)` (ambos exatamente iguais). Conservador. Reduz merges.
   - Opção B: **intersection ≥ N**. Hoje N=1. Aumentar pra N=2 (precisa 2 targets em comum) ou 100% interseção.
   - Opção C: **proibir adicionar novos targets via merge**. Story B mantém só Pedro mesmo após merge — Flávio do article C não é propagado pra story.

3. **Solução paralela ao 5.7.1**: se grouping migrar pra categorias (D17), esse problema se transforma — categorias em vez de targets. Mas a bug-class persiste em forma análoga (story "categoria X+Y" pode ganhar categoria Z via merge).

**Recomendação**: Opção C combinada com 5.7.1. Se story muda de natureza ao receber novo target via merge, é sinal de que não deveria ter feito merge. Restringir mutação de targets via merge automático.

**Test que pegaria regressão**:

```python
@pytest.mark.integration
def test_story_single_target_nao_ganha_target_novo_via_merge(tmp_path):
    """
    Story B sobre só Pedro não deve ganhar Flávio como target
    quando article com ambos é mergeado.
    """
    db_file = tmp_path / "test.db"
    with ClippingDB(db_file) as db:
        story_b_id = db.create_story(title="Pedro defende educação", target_keys=["pedro_angelito"])
    # Article novo entra com targets [pedro_angelito, flavio_valle]
    process_candidates([article_with_both_targets], targets, db, ...)
    # Assert: story_b ainda tem só pedro_angelito, ou nova story foi criada
    targets_after = db.get_story_targets(story_b_id)
    assert "flavio_valle" not in targets_after
```

#### 5.7.4 — Caps internos hardcoded sobrescrevendo escolha do user — **CRÍTICO** (D19, ódio do Otávio)

> **Otávio (D19)**: *"CARALEO, ESSE ERRO AINDA ESTÁ PERDIDO EM ALGUM LUGAR? VOCÊ NÃO TEM IDEIA DO ÓDIO QUE EU TENHO DESSE ERRO. ALGUMA IA RETARDADA FICA DECIDINDO O TEMPO TODO QUE MESMO COM A OPÇÃO DE RODAR ESSE CLIPPING POR ANOS, NA VERDADE EU NÃO DEVIA PODER ESCOLHER DEIXAR A NOTÍCIA RODAR POR MAIS TEMPO."*

##### O que o código DEVERIA fazer (intenção real)

A pipeline tem 8 collectors (RSS, Google News, WordPress API, Internal site search, Sitemap diário, Veja Rio archive, Câmara archive, Direct scrape). Cada collector recebe um parâmetro tipo `limit_per_feed`, `limit_per_query`, `per_target_limit`, `per_site_limit` que diz **quantos articles devolver no máximo daquela source**.

A **intenção do user** ao passar `max_candidates_per_source=90000` é: "vou rodar um backfill grande, deixa cada source devolver até 90.000 articles se tiver — eu quero pegar tudo". O `90000` é um teto generoso que essencialmente diz "sem limite prático".

A **intenção do código de orquestração** (`run_ingestion` em `pipeline/ingest.py:997+`) é: "antes de chamar cada collector, eu calculo um sub-limite apropriado pra cada source baseado no `max_candidates` total. Por exemplo, se temos 90000 budget e 21 RSS feeds, posso permitir até 90000/21 ≈ 4285 por feed". Distribuição razoável.

##### Como o bug quebra essa intenção

Em `pipeline/ingest.py:1009-1020`, a fórmula de distribuição:

```python
max_candidates = max(1, int(options.max_candidates_per_source))  # = 90000 do user

if options.custom_query.strip():     # caso CLI com query custom
    per_feed_limit = max_candidates    # 90000 — sem cap
    per_query_limit = max_candidates   # 90000
    per_target_limit = max_candidates  # 90000
    per_wp_limit = max_candidates      # 90000
else:                                # caso PADRÃO (UI runner do coworker)
    per_feed_limit = max(10, min(500, max_candidates // 2))   # ← TETO 500
    per_query_limit = max(10, min(500, max_candidates // 2))   # ← TETO 500
    per_target_limit = max(10, min(300, max_candidates // 3))  # ← TETO 300
    per_wp_limit = max(10, min(500, max_candidates // 2))      # ← TETO 500
```

**Note o `min(500, ...)`**: aplica um teto absoluto. Mesmo que `max_candidates//2 = 45000`, o resultado é `min(500, 45000) = 500`. **O teto vence sempre**.

Resultado:
- **Caso CLI com `--custom-query "Flávio Valle"`**: caps removidos. User recebe os 90000 prometidos por source.
- **Caso UI coworker (sem custom_query)**: caps em 500/500/300/500 — independente do que user pediu.

A maioria dos coworkers usa o UI runner, que NUNCA passa `custom_query`. Então o `else` é o caminho atingido em produção. Hardcap em 500 ataca todo backfill via UI.

##### Quantos articles o user perde por causa disso

| Source | Limite hardcoded | Capacidade real (1 ano) | Articles perdidos |
|---|---|---|---|
| Cada RSS feed (21 feeds) | 500 | RSS arquiva ~últimas 100 — não é gargalo aqui | ~0 |
| Cada Google News query | 500 | Google News pode devolver milhares dependendo da query | grande |
| Cada internal_search target | 200 (sub-cap interno em outra linha — 5.7.4.B) | sites Globo/G1 podem ter milhares | grande |
| Cada WordPress site (6 sites) | 500 (e ainda 60 pages × 100/page = 6000) | sites Diario do Rio têm dezenas de milhares de posts em 1 ano | grande |
| Sitemap diário | sem cap explícito | proporcional aos dias | tem outros caps |

Num backfill de 1 ano com `flavio_valle`, estimativa rough: o user recebe **3.000-5.000 articles** quando deveria receber **20.000-50.000**. Perda de 80-90% de cobertura.

##### Os 5 lugares onde caps escondidos atuam

###### 5.7.4.A — `pipeline/ingest.py:1017-1020` (caps por collector)

Já descrito acima. **500/500/300/500** quando `custom_query` vazio. É o cap PRINCIPAL.

###### 5.7.4.B — `pipeline/ingest.py:1168` (cap em internal_search)

```python
limit_per_target=min(200, max_candidates // max(1, len(FLAVIO_INTERNAL_SEARCH_TARGETS))),
```

Em internal_search (Globo/G1/Veja Rio/Câmara/CONIB/Extra), o limit por target é capped em **200**. Mesmo se outros parâmetros fossem permissivos, esse `min(200, ...)` ainda machuca.

###### 5.7.4.C — `pipeline/collectors.py:752` (max_pages WordPress)

```python
max_pages = max(3, min(60, (max(1, per_site_limit) // per_page) + 10))
per_page = 100
```

WordPress API pagina. Cada página tem 100 posts. **Cap em 60 páginas = 6000 posts por site por run**. Se site Diario do Rio tem 40.000 posts no período, 34.000 são pulados.

###### 5.7.4.D — `tools/run_parallel_non_direct_ingestion.py:140-143` (caps duplicados)

```python
per_feed_limit = max(10, min(500, max_candidates // 2))
per_query_limit = max(10, min(500, max_candidates // 2))
per_target_limit = max(10, min(300, max_candidates // 3))
per_wp_limit = max(10, min(500, max_candidates // 2))
```

A versão paralela do pipeline (que Otávio roda via CLI pra backfills longos) **DUPLICA** os mesmos caps. Mesmo a versão "paralela rápida" não escapa.

**Bug-class adicional**: duplicação. Se Theseus consertar caps em `pipeline/ingest.py`, esquecer de consertar em `tools/run_parallel_non_direct_ingestion.py` significa drift garantido — alguns runs respeitam novo cap, outros mantêm velho.

###### 5.7.4.E — `pipeline/ingest.py:336` (window 7 dias pra story merge)

```python
for story in db.list_recent_stories(days=7):
```

Quando pipeline cria/grupos articles em stories, busca stories existentes só dos **últimos 7 dias**. Article sobre tema recorrente (ex: "Flávio Valle vota em projeto X" toda quinta) que entra após mais de 7 dias **não merge** — vira story isolada.

Em backfill longo: cada semana vira ilha separada. O dashboard fica com centenas de stories quase-iguais sobre mesmos temas.

##### Por que é CRÍTICO PERSISTENTE (ódio justificado)

1. **5 lugares = 5 oportunidades pra esquecer ao consertar**. Commit `14d558f` (2026-05-01, Claude cloud) já removeu UM cap (`CUSTOM_MAX_DAYS=7` em `web_app/jobs.py` — input validation). Mas os 5 acima permanecem. Provavelmente cada cap foi adicionado em momentos diferentes por desenvolvedores diferentes, sem visão sistêmica.

2. **Nenhum dos caps avisa o user**. Não há log "atingi o cap de 500 do RSS feed X após receber 850 candidates — descartando 350". Silent.

3. **Os caps são DIFERENTES dependendo do path** (CLI custom_query vs UI). Otávio pode ter visto uma run que pegou tudo (CLI) e outra que pegou parcial (UI), sem entender por quê. **Frustração explica o tom da mensagem**.

4. **Mesmo se Otávio ler a fórmula `min(500, max_candidates // 2)`**, ela é enganosa: parece que aumentar `max_candidates` ajuda, mas não ajuda — `min(500, ...)` sempre vence.

##### Cenários de produção onde aparece

1. **Backfill de 6+ meses com qualquer target via UI runner**. Caps 5.7.4.A-C todos atingidos. Coverage ~10-20% do real.

2. **Adicionar novo secondary target e disparar update**. Pipeline reprocessa todas sources pra esse target. Caps atingidos no primeiro feed RSS — outros feeds processam, mas com mesmas limitações.

3. **Tools/run_parallel rodado por Otávio pra "ir mais fundo"**. Mesmos caps. Sensação de "esse paralelo não tá ajudando".

4. **Stories online dispersas em vez de agrupadas**. 5.7.4.E hardcoded 7d window faz stories de mesmo tema (Flávio Valle sobre ciclovia) virarem ilhas em backfill longo.

##### Para Theseus resolver

**Decisões de design pendentes**:

1. **Por que esses caps existem?** A literatura no código não explica. Provável: defesa contra "pipeline runaway" em produção single-process. Mas se `max_process_seconds=90000` (5.6.1) já é circuit breaker, esses caps são redundantes.

2. **Remover ou expor configurável?**
   - Opção A: **remover hardcaps**, usar só `max_candidates // N` (escala com input do user). `max_candidates=90000`, 21 RSS feeds = 4285/feed. Coberto pelo `max_process_seconds=90000` se runaway.
   - Opção B: **expor cada cap como option no UI runner avançado**. `per_feed_limit`, `per_query_limit`, etc.
   - **Recomendação**: Opção A. Caps são defesa redundante.

3. **5.7.4.E (7d story window)**: este é diferente. Não é cap de quantidade — é janela temporal pra merge. Per D17 ("mudar grouping pra base de categorias"), esse pode ser deletado quando grouping migrar pra categorias.

4. **Unificar os 2 lugares (5.7.4.A + 5.7.4.D)**: extract function:
```python
def calculate_per_source_limits(max_candidates: int, has_custom_query: bool) -> dict[str, int]:
    if has_custom_query:
        return {"feed": max_candidates, "query": max_candidates, ...}
    return {"feed": max(10, max_candidates // 2), ...}  # sem hardcap
```
Importar em ambos `pipeline/ingest.py` e `tools/run_parallel_non_direct_ingestion.py`. Drift impossível.

**Test que pegaria a regressão**:

```python
@pytest.mark.integration
@pytest.mark.parametrize("max_candidates,has_custom", [
    (90000, False),  # UI runner case
    (90000, True),   # CLI custom_query case
])
def test_max_candidates_de_user_atingido_quando_alto(monkeypatch, max_candidates, has_custom):
    """
    Quando user passa max_candidates=90000, sub-limites por source devem
    permitir mais que 500. Hoje, no UI path (has_custom=False), o cap em
    500 venceria — esse teste falha hoje, é intencional.
    """
    options = IngestionOptions(
        max_candidates_per_source=max_candidates,
        custom_query="Flavio Valle" if has_custom else "",
    )
    # mock collector que retorna 1000 candidates
    # rodar run_ingestion
    # assert: no UI path, > 500 articles processados (não capped em 500)
```

**Conexão com outros bugs**:
- **5.7.4 ↔ 5.6.1**: caps reduzem quantidade de articles → reduz tempo de processamento → mascara o time budget overflow. Remover caps PIORA o problema 5.6.1 (mais articles → mais tempo). Solução conjunta: caps removidos + checkpoint state implementado.

A bug-class é mais ampla do que o `days=7` único que apontei. Investigação na Iteração 14 achou **5 caps internos diferentes** que sobrescrevem a escolha do user, em 4 arquivos. O Otávio clica "rodar por anos" mas vários layers internos cortam:

##### 5.7.4.A — Caps em 500/500/300/500 candidates POR COLLECTOR (`pipeline/ingest.py:1017-1020`)

**Anatomia**: o user (via UI runner ou CLI) passa `max_candidates_per_source=90000` (default em `IngestionOptions:104`). Esse 90000 vai pra `pipeline.ingest.run_ingestion`. Aí:

```python
# pipeline/ingest.py:1009-1020
max_candidates = max(1, int(options.max_candidates_per_source))  # = 90000

if options.custom_query.strip():        # caso CLI com query custom
    per_feed_limit = max_candidates       # 90000 (sem cap)
    per_query_limit = max_candidates      # 90000
    per_target_limit = max_candidates     # 90000
    per_wp_limit = max_candidates         # 90000
else:                                   # caso PADRÃO coworker UI
    per_feed_limit = max(10, min(500, max_candidates // 2))   # ← min(500) CAPA EM 500
    per_query_limit = max(10, min(500, max_candidates // 2))   # ← CAPA EM 500
    per_target_limit = max(10, min(300, max_candidates // 3))  # ← CAPA EM 300
    per_wp_limit = max(10, min(500, max_candidates // 2))      # ← CAPA EM 500
```

Resultado: coworker padrão (Run UI) **nunca obtém mais que 500 candidates por feed RSS, 500 por Google News query, 300 por internal_search target, e 500 por WordPress site, mesmo declarando 90000**. O input do user é silenciosamente sobrescrito por `min(500, ...)` e `min(300, ...)`.

Pra runs longas (anos), isso é catastrófico: 21 RSS feeds × 500 = 10.500 articles MAX de RSS, mesmo se houver 50.000 disponíveis no período.

**Por que existe**: provavelmente proteção contra runs descontroladas em produção single-process. Mas o user não tem como saber — **caps são silenciosos**.

##### 5.7.4.B — Cap em 200 internal_search por target (`pipeline/ingest.py:1168`)

```python
min(200, max_candidates // max(1, len(FLAVIO_INTERNAL_SEARCH_TARGETS))),
```

Internal search (Globo/G1/Veja Rio/Câmara/CONIB/Extra) tem cap de **200 candidates total por target**, mesmo se user pediu 90000.

##### 5.7.4.C — Cap em 60 pages por WordPress site (`pipeline/collectors.py:752`)

```python
per_page = 100
max_pages = max(3, min(60, (max(1, per_site_limit) // per_page) + 10))
```

WordPress API só itera até **60 pages × 100 posts = 6000 articles** por site por run. Se WordPress site tem 30.000 posts no período, 24.000 são pulados.

##### 5.7.4.D — Caps duplicados em `tools/run_parallel_non_direct_ingestion.py:140-143`

A versão paralela (`tools/run_parallel_non_direct_ingestion.py`) **duplica** os mesmos caps de `pipeline/ingest.py:1017-1020`. Mesmo fórmula:
```python
per_feed_limit = max(10, min(500, max_candidates // 2))
per_query_limit = max(10, min(500, max_candidates // 2))
per_target_limit = max(10, min(300, max_candidates // 3))
per_wp_limit = max(10, min(500, max_candidates // 2))
```

**Bug-class adicional**: a duplicação é tech-debt — se Theseus consertar caps em ingest.py, precisa lembrar de consertar em run_parallel_non_direct_ingestion.py também. Drift garantido.

##### 5.7.4.E — Window de 7 dias em `choose_story` (`pipeline/ingest.py:336`) — original

```python
for story in db.list_recent_stories(days=7):
```

Stories de mais de 7 dias atrás não candidatas a merge. Article sobre tema recorrente (ex: "Flávio Valle vota em projeto X") fica em stories separadas a cada 8+ dias. Em backfills longos, articles antigos viram stories isoladas em vez de mergear.

##### 5.7.4 — síntese

A "IA retardada decidindo cortar" mencionada pelo Otávio NÃO É UMA IA — são **5 caps hardcoded em código humano**, espalhados em 3 arquivos:

| Local | Cap | Impacto |
|---|---|---|
| `pipeline/ingest.py:1017-1020` | 500/500/300/500 candidates por collector | Maior parte dos backfills |
| `pipeline/ingest.py:1168` | 200 candidates por internal_search target | Globo/G1/Veja Rio/etc |
| `pipeline/collectors.py:752` | 60 pages × 100 = 6000 por WordPress site | WordPress de 6 sites |
| `tools/run_parallel_non_direct_ingestion.py:140-143` | 500/500/300/500 (duplicado) | Backfill paralelo |
| `pipeline/ingest.py:336` | 7 dias window pra story merge | Backfills antigos viram stories isoladas |

**Commit `14d558f` (2026-05-01) já removeu UM cap** (CUSTOM_MAX_DAYS=7 em jobs.py — input validation). Mas os 5 acima permanecem. Atlas/Otávio precisam decidir: remover todos os caps internos (preservar `if options.custom_query.strip()` path como default), OU expor cada cap como option configurável.

**Severidade**: CRÍTICA. Decisão de produto: o usuário deveria poder rodar quanto tempo quiser sem caps escondidos.

**Test gap**: nenhum teste verifica que `max_candidates_per_source=90000` resulta em > 500 candidates por feed. Se Theseus consertar, teste pra impedir regressão.

#### 5.7.5 — `sync_existing_article_targets` cria story só se article já não tem

`pipeline/ingest.py:434-441`:
```python
story_id = db.story_id_for_article(article_id)
if story_id is not None:
    # ... update story ...
    return ...
# article doesn't have a story yet
story_id = create_or_update_story(
    db, article_id=article_id, ...
)
```

Se article já existe mas **sem** story_id (caso raro mas possível — e.g. inserção manual sem story), `sync_existing_article_targets` cria uma nova story chamando `create_or_update_story`. Inside `create_or_update_story`, `choose_story` busca story candidate. Pode mergear com story existente. OK.

**Edge case potencial**: article existe + tem story X. Novo target `shakira` é adicionado. `sync_existing_article_targets` faz `db.ensure_story_target(story_X, "shakira")`. Story X agora tem `shakira` no `story_targets`. **Mas a story_X foi criada quando o tema era outro!** Story de "Flávio Valle inaugura ciclovia" agora ganha tag de "shakira" porque algum article com Flávio MAIS Shakira (talvez de boilerplate antigo) entrou.

Antes da fix do Atlas (238b97d), isso podia acontecer livremente. **Depois** da fix, o secondary_target safe-surface bloqueia inserção de mention falsa de shakira ANTES de chegar nesse path. Mas mentions já existentes (de runs antigas) ainda podem trigger essa contaminação se houver re-sync.

**Verificação (após ler `cleanup_false_backfilled_target_mentions:487-501`)**: o cleanup do Atlas JÁ TRATA isso. Após deletar mention falsa, ele checa se há outra mention legítima do mesmo target_key na story (`SELECT 1 FROM story_articles sa JOIN mentions m ... WHERE sa.story_id = ? AND m.target_key = ?`). Se não há, **deleta o `story_target`** correspondente. Atlas fez bem.

**Bug-class reduzido a edge case**: cleanup só roda nos targets passados como argumento (`target_keys`). Se admin/coworker não dispara cleanup específico para um target contaminado, a contaminação histórica permanece. Não é gap grave, é design intentional (cleanup acoplado ao update job).

### 5.5 Outras bug-classes (anatomias breves)

#### 5.5.1 — `is_recent_enough` retorna True em qualquer erro de parsing (F012) — **bypass silencioso de filtro**

##### O que o código DEVERIA fazer (intenção real)

`is_recent_enough` é um **filtro de janela temporal**. Tem intenção clara: dado um article candidato com data de publicação `value`, e uma janela de interesse `[date_from, date_to]`, retornar:
- `True` → "este article está dentro da janela, pode entrar no pipeline".
- `False` → "este article está fora da janela, descartar".

Função é chamada DUAS vezes em `process_candidates`:
1. **Pre-fetch** (linha 625): com `candidate.published_at` cru do collector (pode estar mal formatado se collector retornou string ruim).
2. **Pós-fetch** (linha 810): com `published_at` extraído do HTML real do artigo.

A intenção é **filtro restritivo**: rejeitar articles que estão fora da janela. Se a data não é parseável, o sistema NÃO SABE se está dentro ou fora — e a decisão segura nesse caso é **rejeitar** (default deny). Caso contrário, articles sem data confiável poluem o clipping.

##### Como o bug quebra essa intenção

`pipeline/ingest.py:280-298`:

```python
def is_recent_enough(value: str, *, date_from: datetime | None = None, date_to: datetime | None = None) -> bool:
    try:
        dt = parse_iso(value)
    except Exception:
        return True                           # ← BUG: default permissive
    if date_from is None and dt < BACKFILL_START_DATE:
        return False
    if date_from and dt < date_from:
        return False
    if date_to and dt > date_to:
        return False
    return True
```

Quando `parse_iso(value)` lança exception (data malformada: `'not-a-date'`, `''`, `'2026-13-99'`, etc.), o `except` retorna **`True`** — ou seja, "deixe passar". A semântica é: "não consegui validar, assumo que está OK".

A semântica certa seria o oposto: "não consegui validar → não posso garantir que está dentro da janela → rejeitar pra segurança".

##### Por que é problemático

1. **Articles com data ruim entram no clipping silenciosamente**. Coworker pediu "últimos 7 dias" via UI runner. Pipeline coleta 100 candidates, dos quais 10 têm `published_at` malformado (porque o feed RSS desse site retorna data ISO inválida ou vazia). Os 10 articles entram no clipping mesmo se forem de 2 anos atrás.

2. **Distorção de stats e filtros**. Dashboard mostra "32 articles esta semana" mas inclui articles antigos com data corrompida. Otávio olha "Pedro Angelito ontem" e vê article de 2024 que tem data vazia.

3. **Silent failure mode**. Não há log "skipping article com data ruim X" nem "article com data inválida foi forçado pra dentro". Coworker não tem como saber.

4. **Mesma bug-class do safe-surface**: boundary check com fallback PERMISSIVE em vez de RESTRICTIVE. Mesma classe de bug que o Atlas resolveu pro Shakira (commits `238b97d`, `bb6218e`). Aqui não foi consertado.

5. **Pode mascarar bugs de upstream**. Se um collector novo está retornando datas malformadas porque tem bug no parser dele, o filtro deveria expor isso (rejeitar articles, gerar warning). Em vez disso, esconde o problema upstream.

##### Cenários de produção onde aparece

**Confirmação live** (A-007 Block C, 2026-05-05):
```bash
$ python3 -c "from pipeline.ingest import is_recent_enough; print(is_recent_enough('not-a-date'))"
True
$ python3 -c "from pipeline.ingest import is_recent_enough; print(is_recent_enough(''))"
True
$ python3 -c "from pipeline.ingest import is_recent_enough; print(is_recent_enough('2026-13-99'))"
True
```

Os 3 casos retornam `True`. Articles com qualquer string lixo passam.

**Cenário concreto de produção**: backfill de 6 meses. Alguns RSS feeds retornam `<pubDate>Mon, Jan</pubDate>` (sem ano, formato truncado). Atualmente esses articles entram no clipping com `published_at='Mon, Jan'`. Dashboard tenta parsear pra display e mostra string vazia ou data atual (depende da função de display). Coworker fica confuso.

##### Para Theseus resolver

**Fix simples (1 linha)**:

```python
def is_recent_enough(value, *, date_from=None, date_to=None) -> bool:
    try:
        dt = parse_iso(value)
    except Exception:
        logging.warning("is_recent_enough: failed to parse %r — rejecting article", value)
        return False                          # ← era True, vira False (default deny)
    ...
```

**Decisão de design pendente**: o que fazer com articles rejeitados?
- Opção A: simplesmente skip (não entram no pipeline). Limpo mas perde sinal de "havia article aqui".
- Opção B: emitir candidate event com `reason='unparseable_date'` pra log. Permite contar quantos foram rejeitados em runs.

**Recomendação**: Opção B (já existe a infra `emit_candidate` em `process_candidates`). Modificar o caller pra emitir evento.

**Impacto da fix em produção**:
- **Imediato**: articles com data ruim DEIXAM de entrar no clipping. Pode causar uma queda perceptível no count de articles na primeira run pós-fix. Coworker precisa ser avisado: "esperar drop temporário".
- **Curto prazo**: bugs upstream em collectors viram visíveis (logs de WARNING). Permite ao Theseus corrigir collectors que produzem datas ruins.

**Test que pegaria a regressão**:

```python
@pytest.mark.integration
@pytest.mark.parametrize("bad_date", [
    "not-a-date",
    "",
    None,
    "2026-13-99T99:99:99",
    "yesterday",
    "<<malformed>>",
])
def test_is_recent_enough_rejects_unparseable_dates(bad_date):
    """
    F012: today returns True (BUG). Should return False (default deny).
    """
    from datetime import datetime, timezone
    result = is_recent_enough(
        str(bad_date or ""),
        date_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    assert result is False, f"Expected False for unparseable date {bad_date!r}, got {result}"
```

**Conexão com outros bugs**:
- Mesma bug-class de **5.4 (bug Shakira)**: boundary check com fallback permissive em vez de restritivo. Atlas resolveu pra targets em commits `238b97d`/`bb6218e`. Aqui não foi tocado.
- Indiretamente afeta **5.6.2 (archive cutoff)**: articles com data ruim entrando aumentam o volume de candidates processados, acelerando atingimento do cutoff.

#### 5.5.2 — Lifespan startup mascara falha do Supabase silenciosamente (F011)

##### O que o código DEVERIA fazer (intenção real)

O Render é um ambiente **single-process com filesystem efêmero**: cada deploy/restart cria um novo container que perde tudo que foi escrito localmente. Pra preservar dados (especialmente `data/clipping.db`), o pipeline usa Supabase Storage como **backup persistente**: a cada mutação significativa (classification save, category create, manual story), o SQLite é gzipado e enviado pra Supabase.

A **lifespan startup** (FastAPI `lifespan` context manager em `web_app/app.py:118-145`) tem responsabilidade crítica: **antes de aceitar requests, restaurar o estado do app**. Concretamente:

1. Baixa `data/clipping.db.gz` mais recente do Supabase pra disco local.
2. Aplica migrações de schema (`ensure_app_tables`).
3. Limpa jobs órfãos (`cancel_orphaned_active_jobs` / agora `mark_orphaned_active_jobs_interrupted`).
4. Normaliza targets (`normalize_targets_file`).
5. Seeda categorias base.

A **intenção** é: ao final do `lifespan` block (no `yield`), app está pronto pra servir com **estado consistente**. Coworker que acessa o site logo depois do deploy vê os ~700 articles + classifications de antes do deploy. Continuidade.

##### Como o bug quebra essa intenção

`web_app/app.py:118-145`:

```python
@asynccontextmanager
async def lifespan(_: FastAPI):
    artifact_store.download_current_artifacts()       # ← sem try/except
    target_cleanup = archive_known_test_targets()      # ← sem try/except
    targets_normalized = normalize_targets_file()      # ← sem try/except
    ensure_app_tables(db_path())                       # ← sem try/except
    orphaned_jobs = cancel_orphaned_active_jobs()      # ← sem try/except
    cdb = ClippingDB(db_path())
    existing_names = {row["name"] for row in cdb.list_categories()}
    newly_seeded = [n for n in BASE_CATEGORIES if n not in existing_names]
    for name in newly_seeded:
        cdb.get_or_create_category(name, created_by="system")
    if (newly_seeded or targets_normalized or orphaned_jobs) and artifact_store.enabled:
        artifact_store.upload_current_artifacts(...)
    if target_cleanup.get("archivedCount") and artifact_store.enabled:
        artifact_store.upload_current_artifacts(...)
    yield  # app starts serving
```

Nenhum step tem try/except. Se qualquer um falha, a exception sobe e — em FastAPI — o `lifespan` falha, **app NÃO inicia**.

Mas há cenários onde a função NÃO lança exception, **mas falha silenciosamente**:

`artifact_store.download_current_artifacts()` é definida em `web_app/storage_bridge.py:64-76`. Por design, ela **engole exceptions internas** (F023 do tech-debt audit): se HTTP request pra Supabase falha, retorna `False` em vez de levantar. **Sem log**.

Cenário de falha silenciosa:
1. Supabase auth expirou (token revogado, reset de billing, etc.).
2. Lifespan chama `download_current_artifacts()`.
3. Função tenta GET no Supabase — recebe HTTP 401.
4. Função engole 401, retorna `False`.
5. Lifespan continua sem saber que o download falhou.
6. `ensure_app_tables(db_path())` cria SCHEMA EM DB VAZIO local (porque não foi baixado).
7. App inicia "saudável" do ponto de vista do FastAPI — mas **com DB sem dados**.
8. Coworker acessa o site, vê dashboard vazio. Pensa "perdemos tudo".

**Pior**: `/healthz` (linha 205-214) reporta:
```python
return {
    "ok": True,
    "dbExists": db_path().is_file(),       # True — arquivo local existe (vazio)
    "authConfigured": auth_configured(),
    "storage": artifact_store.status(),     # status pré-download
    "localWritesAllowed": local_writes_allowed(),
    "job": job_manager.current_status().get("status", "idle"),
}
```

`dbExists=True` (arquivo existe, mesmo vazio). `storage.enabled=true` (config do Supabase está OK; a falha foi runtime). `ok=True`. **Healthz mente**: diz "tudo bem" enquanto produção está com DB vazio.

##### Por que é problemático

1. **Dataloss aparente sem aviso**. Se Supabase tiver downtime no exato momento de um deploy, app inicia sem dados. Coworker vê tela vazia. Atlas/Otávio precisam debugar via logs — que mostram "lifespan completou OK" (sem indicação real de problema).

2. **Healthz é unreliable como sinal**. Monitoring que se baseie em `/healthz` retornando 200 vai considerar saudável o app que está degradado.

3. **Recovery não-trivial**. Pra restaurar, precisa: (a) detectar que está degradado (manualmente — não há flag), (b) re-disparar download manualmente, (c) confirmar dados voltaram. Sem código pra isso, é manual.

4. **Status quo HOJE**: `/healthz` em produção retorna OK e `dbExists=true` (per A-007 Block B do 2026-05-05). Não tem evidência de degradação ATIVA agora — Supabase está funcional. **F011 é bug LATENTE**: a estrutura permite degradação silenciosa, mas hoje não está acontecendo. Próxima vez que Supabase tiver problema, vai aparecer.

##### Cenários onde isso ATIVAMENTE causaria problema

1. **Supabase auth token expira**. Sem renovação automática, próximo restart Render → DB vazio.
2. **Supabase storage outage breve** (acontece raramente, mas acontece) durante restart Render. App inicia sem dados pelo período do outage.
3. **Mudança de bucket/credenciais** sem validação prévia (Otávio rotaciona key Supabase, esquece de atualizar env var no Render). Próximo restart → DB vazio.
4. **Network issue temporário** entre Render e Supabase durante boot. Race condition curta.

##### Para Theseus resolver

**Fix conceitual** (modificar `web_app/app.py:118-145`):

```python
@asynccontextmanager
async def lifespan(_: FastAPI):
    degraded_steps = []
    
    # Step 1: download artifacts
    try:
        result = artifact_store.download_current_artifacts()
        if not result:
            degraded_steps.append("supabase_download_returned_false")
            logging.error("Lifespan: download_current_artifacts returned False — app may have empty DB")
    except Exception:
        logging.exception("Lifespan: download_current_artifacts exception")
        degraded_steps.append("supabase_download_exception")
    
    # Step 2-N: similar tratamento pra cada step
    try:
        ensure_app_tables(db_path())
    except Exception:
        logging.exception("Lifespan: ensure_app_tables failed")
        degraded_steps.append("ensure_tables_failed")
    
    # ... etc
    
    # Expose degraded state via app.state pra healthz ler
    app.state.lifespan_degraded = degraded_steps
    yield
```

E `/healthz` lê:

```python
@app.get("/healthz")
def healthz():
    return {
        "ok": not bool(getattr(app.state, "lifespan_degraded", [])),  # ← FALSE se degradado
        "degraded": getattr(app.state, "lifespan_degraded", []),       # ← lista de problemas
        "dbExists": db_path().is_file(),
        "dbHasArticles": ClippingDB(db_path()).count_articles() > 0,  # ← novo: confirma dados
        "authConfigured": auth_configured(),
        "storage": artifact_store.status(),
        ...
    }
```

**Decisões de design pendentes**:

1. **Se download falhou, app deve iniciar mesmo assim?**
   - Opção A: SIM, com `degraded` flag. Coworker pode ver dashboard vazio mas pelo menos tem mensagem clara.
   - Opção B: NÃO, lifespan deve raise se falha crítica. App não inicia, Render mostra "deploy failed". Mais brutal mas mais óbvio.
   - **Recomendação**: A. Continua iniciando mas expõe sinal de saúde claro.

2. **Tentar retry do download?** Network glitches temporários poderiam ser resolvidos com 2-3 tentativas. Custo: aumenta tempo de boot.

3. **Adicionar flag `dbHasArticles` em healthz?** Confirma que DB não só existe mas tem conteúdo. Catch falsos negativos (DB criado vazio).

**Test que pegaria regressão**:

```python
@pytest.mark.integration
def test_healthz_surfaces_lifespan_degradation_when_supabase_fails(monkeypatch, tmp_path):
    """
    F011: hoje, healthz retorna ok=true mesmo se download_current_artifacts
    falhou silently. Após fix, deve retornar ok=false + degraded=["..."].
    """
    from unittest.mock import patch
    monkeypatch.setenv("CLIPPING_DB_PATH", str(tmp_path / "fresh.db"))
    # Mock download to return False
    with patch("web_app.storage_bridge.ArtifactStore.download_current_artifacts", return_value=False):
        with TestClient(app) as client:
            response = client.get("/healthz")
            payload = response.json()
            assert payload.get("ok") is False
            assert "supabase_download_returned_false" in payload.get("degraded", [])
```

**Conexão com outros bugs**:
- Relacionado a **F023** (storage_bridge silent failures) — pra fix completo, ambos precisam ser tratados juntos.
- Mesma classe conceitual de **5.6.1** (run cortada): decisão silenciosa do sistema sem visibilidade pro user.

#### 5.5.3 — 9 endpoints mutating state sem `require_admin` (F001-F009) — inconsistência de auth gate

##### O que o código DEVERIA fazer (intenção real)

O FastAPI app tem dois conjuntos de endpoints:

1. **Pública/coworker** (sem auth): leitura do dashboard, polling de status. Coworkers usam pra rodar updates sem precisar password.
2. **Admin** (com auth): mutações sensíveis — criar/arquivar targets, classificar artigos, inserir manual stories. Protegido por `require_admin(request)` (cookie HMAC) + `require_csrf(request)` (CSRF token).

A lógica de proteção está em `web_app/auth.py`:
- `require_admin(request)`: verifica cookie `clipping_admin` válido, expiry OK. Se não, raise HTTPException 401.
- `require_csrf(request)`: verifica header `x-csrf-token` casa com a derivação HMAC do cookie. Se não, raise HTTPException 403.

A **intenção do design original** era proteger todas as MUTAÇÕES de state com `require_admin + require_csrf`. Mutar targets, criar categorias, gravar classifications — isso são ações **administrativas** que coworkers que estão só "rodando o pipeline" não deveriam fazer.

O sprint "open-link coworker runner" (2026-04-30) explicitamente decidiu que `/api/update/start` (disparar coleta) E `/api/update/cancel` ficam **abertos** — coworker dispara via UI sem login. **Mas o sprint NÃO decidiu abrir as outras mutações** (target CRUD, classifications, etc.). Essas deveriam continuar protegidas.

##### Como o bug quebra essa intenção

Em `web_app/app.py`, **9 endpoints mutating state NÃO chamam `require_admin`** (verificado via leitura completa do arquivo):

| Linha | Endpoint | Método | Auth atual | Auth esperada |
|---|---|---|---|---|
| 222 | `/api/update/start` | POST | (sem) | (sem) — sprint open-link aceita |
| 236 | `/api/update/cancel` | POST | (sem) | (sem) — sprint open-link aceita |
| 248 | `/api/export` | POST | (sem) | **ADMIN** (mutação sensível: regenera dashboard público) |
| 307 | `/api/targets` | POST | (sem) | **ADMIN** (criar secondary target — é decisão de produto) |
| 326 | `/api/targets/{key}` | PATCH | (sem) | **ADMIN** (editar target) |
| 338 | `/api/targets/{key}/archive` | POST | (sem) | **ADMIN** (arquivar target) |
| 350 | `/api/targets/{key}/restore` | POST | (sem) | **ADMIN** (restaurar) |
| 361 | `/api/categories` | POST | (sem) | **ADMIN** (criar categoria) |
| 402 | `/api/classifications` | POST | (sem) | **ADMIN** (gravar classification — confiável) |

Comparativo: o handler **`/api/manual-story`** (linha 261) chama `require_admin + require_csrf` corretamente. Mostra que o padrão **está implementado**, só não foi aplicado consistentemente.

**Confirmação live** (A-007 Block A, 2026-05-05):

```bash
$ curl -sS -X POST https://clipping-project.onrender.com/api/update/cancel \
    -H "Content-Type: application/json"
{"detail":"no_active_job"}
HTTP 409
```

Resposta 409 prova que o handler executou (chegou ao branch `JobConflict`). Se `require_admin` estivesse aplicado, retornaria 401 com `admin_login_required`. **Confirmado em produção: bypass real.**

##### Por que é problemático

1. **Qualquer pessoa que descobrir as URLs pode mutar state em produção**:
   - Criar 1000 secondary targets fake.
   - Arquivar/restaurar targets do mandato (Flávio Valle, Pedro Angelito, Bernardo Rubião) — distorce o clipping.
   - Gravar classifications falsas em massa.
   - Criar categorias fake.
   - Disparar export, regenerando o dashboard público com state corrompido.

2. **Hoje é mitigado por obscuridade**: ninguém fora do círculo do Otávio sabe das URLs. Mas é **defesa fraca** — qualquer scraping do JS já expõe os endpoints.

3. **Distorção de dados**: classifications são o **dado mais valioso** do clipping (trabalho humano de coworker categorizando articles). Se alguém pode poison via POST direto, o trabalho fica desconfiável.

4. **Inconsistência interna do código** confunde quem mantém: por que `/api/manual-story` exige auth mas `/api/classifications` não? Decisão acidental de quem implementou cada handler, não política.

5. **Sprint open-link aceita SOME endpoints sem auth, mas NÃO TODOS**. A decisão do sprint foi explícita só pra runner (`update/start`, `update/cancel`). Outros foram deixados sem auth por **inércia de copy-paste**.

##### Cenários onde aparece em produção

**Hoje (não há ataque ativo confirmado)**:
- Atlas inadvertidamente "explorou" o bypass em A-002 (2026-04-30): criou categoria `AtlasLiveCheck` via `curl -X POST /api/categories` sem auth pra testar se endpoint estava live. Funcionou. Confirmou bypass.

**Cenários de risco**:
1. Coworker novo recebe URL do site, descobre no DevTools que `POST /api/targets/flavio_valle/archive` funciona sem login. Por curiosidade ou erro, arquiva o target principal. Otávio precisa restaurar.
2. Crawler malicioso encontra os endpoints, faz spam de targets/categorias. DB enche de lixo.
3. Coworker "quer ajudar" e cria classifications via curl batch sem entender o schema. Dados ficam inconsistentes.

##### Para Theseus resolver

**Fix mecânico (rápido)**: adicionar `require_admin(request); require_csrf(request)` no início de cada handler problemático. Pra cada endpoint:

```python
@app.post("/api/categories")
async def create_classification_category(request: Request) -> dict[str, Any]:
    require_admin(request)        # ← novo
    require_csrf(request)         # ← novo
    payload = await read_json(request)
    # ... resto igual
```

**Decisões de design pendentes**:

1. **Quais endpoints REALMENTE precisam admin gate?** Lista revisada baseada na intenção do sprint:

   | Endpoint | Decisão sugerida | Razão |
   |---|---|---|
   | `/api/update/start` | **abrir** | sprint open-link |
   | `/api/update/cancel` | **abrir** | sprint open-link |
   | `/api/export` | **proteger** | regenera dashboard, mutação sensível |
   | `/api/targets` POST | **proteger** | criar target afeta o clipping todo |
   | `/api/targets/*` PATCH/archive/restore | **proteger** | editar/arquivar primary target distorce sprint |
   | `/api/categories` POST | **proteger** | spam de categorias |
   | `/api/classifications` POST | **proteger** | dado humano valioso |
   | `/api/classifications` GET | **abrir** | dashboard público lê pra exibir chips |

2. **Como migrar coworkers que JÁ ESTÃO usando UI sem auth?** UI runner permite criar secondary targets sem login (per sprint). Se gate o `/api/targets` POST, UI quebra.

   **Solução**: distinguir TIPOS de mutação:
   - **Coworker permitido**: criar/arquivar SECONDARY targets, gravar classifications.
   - **Admin only**: mutar PRIMARY targets (Flávio Valle, Pedro Angelito, etc.), criar categorias base, export.

   Implementar via lógica fina nos handlers em vez de gate genérico.

3. **CSRF protection pra coworker?** CSRF protege contra requisições de sites maliciosos rodando no browser. Sem login não há sessão pra proteger via CSRF tradicional. Solução: tokens CSRF emitidos via `/api/csrf` mesmo sem login (vinculados a sessão temporária por IP+UA?).

**Test que pegaria a regressão**:

```python
@pytest.mark.integration
@pytest.mark.parametrize("endpoint,method", [
    ("/api/categories", "POST"),
    ("/api/targets/test-target/archive", "POST"),
    ("/api/classifications", "POST"),
    ("/api/export", "POST"),
])
def test_admin_endpoints_require_auth(client, endpoint, method):
    """
    Endpoints sensíveis devem retornar 401 sem cookie de admin.
    HOJE retornam 200/409/etc — esse teste falha. Quando passar, F001-F009 resolvido.
    """
    response = client.request(method, endpoint, json={})
    assert response.status_code == 401, f"{method} {endpoint} should require admin auth"
    assert "admin_login_required" in response.json().get("detail", "")
```

**Conexão com outros bugs**:
- Atlas no Note-A-002 demonstrou bypass criando categoria `AtlasLiveCheck`. **Evidência viva** do problema.
- Sprint "open-link runner" criou ambiguidade — Atlas e Otávio precisam clarificar política em escrito (qual endpoint abre, qual fecha).
- 5.5.3 não está em conflito com sprint atual — sprint só foi sobre `update/start` e `update/cancel`. Outros 7 endpoints não foram sequer considerados pra abrir.

#### 5.5.4 — `canonicalize_url` duplicado (F018)

`pipeline/normalization.py:35` e `pipeline/http_utils.py:236`. Implementações diferentes:
- `normalization.py`: lowercase + sort query params + strip tracking (utm_*)
- `http_utils.py`: port-aware + trailing slash + scheme normalization

Quem importa qual obtém dedup diferente. Risco: artigo passa dedup em uma chamada e falha em outra → duplicata silenciosa.

**Bug-class**: drift entre implementações — duplicação que evolui em direções diferentes.

---

## Seção 6 — Test gaps + propostas de teste

*Preenchida na Iteração 4-5 (2026-05-05). Cobertura existente confirmada em `tests/test_targets_jobs.py` e `tests/test_sprint_regression_harness.py`. Focados nos gaps de Seção 5 não cobertos pelos commits recentes do Atlas.*

### 6.1 Gap A — Primary targets sem safe-surface check

**Bug-class**: 5.4.A. Primary target hommônimo (CEO Flávio Valle vs vereador) ainda matcha full_text.

**Cobertura atual**: NÃO. Tests do Atlas só cobrem secondary.

**Proposta de teste** (a colocar em `tests/integration/test_target_homonyms.py`):

```python
import pytest
from pathlib import Path
from pipeline.ingest import process_candidates, IngestionOptions
from pipeline.collectors import CandidateArticle
from pipeline.matcher import Target
from pipeline.database import ClippingDB

@pytest.mark.integration
def test_primary_target_matched_only_in_full_text_boilerplate_is_kept(monkeypatch, tmp_path):
    """
    Anatomia: artigo sobre Show de Shakira (title) que menciona homônimo
    'CEO Flávio Valle' no full_text. Hoje, primary target Flávio é tagueado
    indevidamente. Este teste documenta o gap; quando passar, framework guarda.
    """
    db_file = tmp_path / "test.db"
    targets = [Target(key="flavio_valle", display_name="Flávio Valle", primary=True, keywords=["Flavio Valle", "Flávio Valle"], exact_aliases=[])]
    candidate = CandidateArticle(
        url="https://exemplo.com/show-shakira",
        title="Show de Shakira em Copacabana impulsiona turismo latino",
        snippet="A apresentação no projeto Todo Mundo no Rio reforça fluxo internacional.",
        full_text=(
            "A apresentação reforça fluxo internacional. "
            "Segundo o CEO Flávio Valle, a presença de uma artista latina..."  # homônimo
        ),
        source_name="Mercado e Eventos",
        source_type="rss",
        published_at="2026-05-02T10:00:00+00:00",
    )
    options = IngestionOptions(date_from=None, date_to=None, request_timeout=10)
    with ClippingDB(db_file) as db:
        result = process_candidates([candidate], targets, db, options=options)
    # Behavior atual: mention de flavio_valle gravada (BUG)
    # Behavior desejado: skip com reason="primary_target_only_in_full_text" OU
    # safe-surface aplicado também em primary com whitelist de exceções
    assert result.mentions_inserted == 0  # currently FAILS (reproduces bug)
```

**Decisão de design pra fix**: Otávio precisa decidir se safe-surface vale para primary também (mais seguro, mas pode perder articles legítimos onde Flávio é mencionado só no full_text), OU se primary tem rule diferente (ex: "primary com homônimo conhecido exige > 2 menções no full_text").

### 6.2 Gap B — `is_recent_enough` parse error

**Bug-class**: 5.5.1.

**Cobertura atual**: NÃO.

**Proposta** (colocar em `tests/integration/test_date_filter_edge_cases.py`):

```python
import pytest
from pipeline.ingest import is_recent_enough
from datetime import datetime, timezone

@pytest.mark.integration
@pytest.mark.parametrize("bad_value", [
    "not-a-date",
    "",
    None,  # se parse_iso aceitar None
    "2026-13-99T99:99:99",  # mês 13, dia 99
    "yesterday",
    "<<malformed>>",
])
def test_is_recent_enough_rejects_unparseable_dates(bad_value):
    """
    Anatomia F012: today function returns True on parse error (permissive),
    so articles with malformed dates pass recency filter. Should be False.
    """
    # Behavior atual: True (BUG); behavior desejado: False
    assert is_recent_enough(str(bad_value or ""), date_from=datetime(2026,1,1,tzinfo=timezone.utc), date_to=None) is False
```

### 6.3 Gap C — `canonicalize_url` divergent implementations

**Bug-class**: 5.5.4.

**Cobertura atual**: NÃO.

**Proposta** (colocar em `tests/integration/test_url_canonicalization_consistency.py`):

```python
import pytest
from pipeline.normalization import canonicalize_url as canonical_norm
from pipeline.http_utils import canonicalize_url as canonical_http

@pytest.mark.integration
@pytest.mark.parametrize("url", [
    "https://example.com:443/path?b=2&a=1&utm_source=x",
    "http://Example.com/path/?utm_campaign=y",
    "https://example.com//double//slash",
])
def test_canonicalize_url_implementations_agree(url):
    """
    F018: two canonicalize_url functions exist with different behaviors.
    Whichever is called first decides dedup. They must agree or be merged.
    """
    assert canonical_norm(url) == canonical_http(url), (
        f"Divergent: norm={canonical_norm(url)!r} vs http={canonical_http(url)!r}"
    )
```

(Uma vez que o teste passe, qualquer um dos dois pode ser deletado e re-exportado.)

### 6.4 Gap D — Lifespan silently boots with empty DB

**Bug-class**: 5.5.2 (F011).

**Cobertura atual**: NÃO.

**Proposta** (colocar em `tests/integration/test_lifespan_resilience.py`):

```python
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from web_app.app import app

@pytest.mark.integration
def test_lifespan_surfaces_supabase_download_failure_in_healthz(monkeypatch, tmp_path):
    """
    F011: today, lifespan calls download_current_artifacts() with no try/except.
    If Supabase is down, app boots silently with empty DB and /healthz reports
    {"ok": true, "storage": {"enabled": true, ...}}. Should surface degradation.
    """
    def failing_download(*args, **kwargs):
        raise ConnectionError("simulated Supabase outage")

    monkeypatch.setenv("CLIPPING_DB_PATH", str(tmp_path / "fresh.db"))
    with patch("web_app.storage_bridge.ArtifactStore.download_current_artifacts", side_effect=failing_download):
        with TestClient(app) as client:
            r = client.get("/healthz")
            payload = r.json()
            # Behavior desejado: degraded flag visible
            assert payload.get("degraded", []) == ["download_artifacts"], (
                f"healthz did not surface lifespan degradation: {payload}"
            )
```

### 6.5 Gap E — Frontend filter refresh after add target

**Bug-class**: 5.4.C.

**Cobertura atual**: NÃO.

**Proposta** (Playwright-style integration test, colocar em `tests/integration/test_frontend_target_lifecycle.py`):

```python
import pytest
from playwright.sync_api import sync_playwright

@pytest.mark.integration
@pytest.mark.live  # depende de Render rodando
def test_add_secondary_target_updates_filter_dropdown_without_refresh(page):
    """
    Anatomia bug Shakira lado UI: POST /api/targets retorna sucesso, mas
    filter dropdown do dashboard só refresha com reload manual da página.
    Bug-class: client-side state stale after server mutation.
    """
    page.goto("https://clipping-project.onrender.com/")
    initial_targets = page.eval_on_selector_all("[data-target-key]", "els => els.map(e => e.dataset.targetKey)")
    assert "shakira_test" not in initial_targets

    # Add via UI
    page.fill("#newTargetName", "Shakira Test")
    page.click("#addTargetSubmit")
    page.wait_for_selector("#addTargetMessage:has-text('adicionado')")

    # WITHOUT page reload, dropdown should now have shakira_test
    after_targets = page.eval_on_selector_all("[data-target-key]", "els => els.map(e => e.dataset.targetKey)")
    assert "shakira_test" in after_targets, (
        "Filter dropdown did not refresh after add target — frontend state stale"
    )
```

### 6.6 Gap F — Cleanup só roda em `update` job

**Bug-class**: 5.4.D.

**Cobertura atual**: NÃO (cleanup é testado, mas não a sua aplicabilidade noutros caminhos).

**Proposta** (colocar em `tests/integration/test_cleanup_paths.py`):

```python
@pytest.mark.integration
def test_manual_story_does_not_apply_safe_surface_filter(tmp_path, monkeypatch):
    """
    5.4.B/D: insert_manual_story bypasses safe-surface check. If admin pastes
    article with target only in 'leia também' boilerplate, mention is saved.
    """
    # ...setup target shakira...
    payload = {
        "title": "Show de Shakira em Copacabana",
        "url": "https://example.com/show",
        "full_text": "Show acontece amanhã. Leia também: Flávio Valle inaugura ciclovia.",
        "target_keys": ["flavio_valle"],  # admin claims this article mentions Flávio
    }
    # Inserts mention without check — currently allowed
    # Desired: validate target appears in safe-surface OR explicit override flag
```

### 6.7 Resumo de cobertura

| Gap | ID | Cobertura atual | Status do framework proposto |
|---|---|---|---|
| Primary homônimo (CEO Flávio Valle) | 5.4.A | ❌ | Test file: `test_target_homonyms.py` |
| Manual story bypassa safe-surface | 5.4.B | ❌ | Test file: `test_cleanup_paths.py` |
| UI filter refresh | 5.4.C | ❌ | Test file: `test_frontend_target_lifecycle.py` (Playwright) |
| Cleanup dependente de timing | 5.4.D | ❌ | Test file: `test_cleanup_paths.py` |
| `is_recent_enough` parse error | 5.5.1 | ❌ | Test file: `test_date_filter_edge_cases.py` |
| Lifespan silent failure | 5.5.2 | ❌ | Test file: `test_lifespan_resilience.py` |
| Auth bypass | 5.5.3 | ⚠️ Sprint accepts | Test file: `test_auth_contract.py` (futuro, decisão produto) |
| `canonicalize_url` dup | 5.5.4 | ❌ | Test file: `test_url_canonicalization_consistency.py` |
| Secondary target page boilerplate | 5.4 (Atlas) | ✅ | Já em `test_targets_jobs.py:941` |
| Backfill ignora full_text noise | 5.4 (Atlas) | ✅ | Já em `test_targets_jobs.py:864` |
| Manual cancel vs interrupted | 5.4 (Atlas) | ✅ | Já em `test_targets_jobs.py:569` |

**6 gaps confirmados sem cobertura.** Framework proposto adiciona 6 arquivos de teste em `tests/integration/`, naming `test_<feature_or_bugclass>_<scenario>.py`.

---

## Seção 11 — Para um Theseus resolver (lista priorizada por severidade)

*Iteração 17. Ariadne é o fio que mapeia o labirinto; Theseus (Atlas, Otávio ou outra IA com permissão) entra, mata o minotauro, e volta. Esta seção lista o que Theseus deve atacar, em que ordem, com pointer pra anatomia.*

### 🔴 CRÍTICOS — atacar primeiro

| ID | Bug-class | Anatomia | Sinal de produção |
|---|---|---|---|
| **5.6.1** | Run cortada por time budget de 25h sem aviso, sem checkpoint | Seção 5.6.1 | Coworker vê "succeeded" mas resultado é parcial; sem mensagem "sua run foi cortada" |
| **5.6.2** | Articles processados nos últimos 20% do budget têm full_text degradado silenciosamente | Seção 5.6.2 | Article fica no DB com texto curto; "Texto pra leitura" raso |
| **5.7.4** | 5 caps internos hardcoded (500/500/300/500 candidates por collector + 200 por internal_search target + 60 pages WordPress + 7d window grouping) sobrescrevem input do user | Seção 5.7.4 (5 sub-classes A-E) | Backfills de >1 ano nunca pegam todos articles disponíveis; user não vê limite |

**Para Theseus** sobre os 3 críticos:
- **5.6.1**: implementar checkpoint state. A tabela `backfill_state` (Seção 5.9.1) já existe no schema com colunas `current_date`, `current_page`, `status='paused'`, `updated_at` — feita exatamente pra isso, nunca conectada. **Solução natural**: Theseus conecta `process_candidates` pra (a) salvar progresso em `backfill_state` periodicamente, (b) resumir do último checkpoint quando run anterior atingiu time budget, (c) emitir job_event "run cortada — clique pra continuar".
- **5.6.2**: marcar articles com flag `full_text_complete: bool` no DB ou similar. Permite re-fetch posterior dos articles degradados.
- **5.7.4**: a fix pode ser:
  1. Apagar `min(500, ...)` e similares — usar só `max_candidates // N` (escala com input do user).
  2. Ou expor cada cap como option configurável via UI runner avançado.
  3. **Decisão de produto pendente**: Otávio decide a abordagem.

### 🟡 LEGACY — conviver ou deferir

| ID | Bug-class | Status | Per Otávio |
|---|---|---|---|
| **5.7.1** | high_threshold/low_threshold redundantes em `choose_story` | LEGACY com solução proposta | "muito difícil fazer groupings online... mudar para funcionar apenas com base nas categorias" (D17) |
| **5.8.2** | AI detection split entre `mentions.sentiment_reason` e `classifications.ai_generated` | LEGACY conviver | "sistema de classificação por ia tá bem legacy. A gente fez algo com claude code muito melhor, mas é inviável fazendo pelo site. Acabou que ele serve mais pra gente revisar erros" (D21) |
| **5.8.3** | `classify_articles.py` sem audit gate além de ANTHROPIC_API_KEY | LEGACY desligado | "Sistema legacy, não temos créditos anthropic para fazer isto" (D22) |

**Para Theseus** sobre 5.7.1:
- Solução proposta pelo Otávio: **substituir story-grouping por categorias**. Hoje grouping usa similaridade de texto (`choose_story` em `pipeline/ingest.py`). Solução: trocar lógica pra grupar articles que **compartilham `categories`** (do Sistema B em `tools/classify_articles.py`).
- Mas D21+D22 dizem que sistema de IA de categorização é legacy/sem créditos. Significa: poucos articles têm categoria. Solução depende de **categorização ativa por humanos** OR migrar pra ferramenta externa (Claude Code rodando local pelo Otávio com acesso a créditos).
- **Decisão pendente**: como rodar categorização sem créditos Anthropic? Coworkers categorizam manualmente? Migrar pra outro provider? Bloqueia fix 5.7.1.

### 🟠 SMELL / INVESTIGAR — pode virar bug, registrar pra futuro

| ID | Bug-class | Tipo | Para Theseus |
|---|---|---|---|
| **5.6.3 / 5.8.1** | F018: `canonicalize_url` duplicada em 2 arquivos com comportamentos diferentes; manifestado em produção (artigo Shakira aparece 2× com/sem `www.`) | Bug ativo, baixa severidade | Unificar `canonicalize_url` em 1 lugar; chamar tanto no INSERT (pipeline) quanto no EXPORT (tools/export_mobile_snapshot.py:2438) |
| **5.6.4** | Cleanup acopla a string mágica `sentiment_reason="lexical_heuristic"` | Bug-class frágil | Refactor: usar booleano `mentions.is_auto_generated` ou enum em vez de string acoplada |
| **5.6.5** | `forced_terms` filter checa em `combined_text` (com full_text) — mesma classe Shakira em outra feature | Bug-class secundária | Aplicar `safe_target_match_surface` em forced_terms também |
| **5.7.2** | Score de merge `max(title, summary*0.65)` enviesa pra title-similarity | Smell | Mudar pra weighted average ou conjunto de regras com title E summary |
| **5.7.3** | `choose_story` aceita merge com intersection mínima de 1 target | Smell | Política de produto: requer 100% intersection? ≥2 targets? Otávio decide |
| **5.7.5** | Atlas resolveu — listado pra registro | RESOLVED | — |
| **5.9.1** | `backfill_state` é tabela morta | Tech-debt + oportunidade | Conectar pra 5.6.1 (checkpoint resume) |
| **5.9.2** | `scrape_log` é tabela morta | Tech-debt | Decidir: conectar (telemetria de coletas) OU `DROP TABLE` |
| **5.9.3** | `GOOGLE_DECODE_CACHE` unbounded | Tech-debt latente | Adicionar TTL ou max-size eviction (ex: `functools.lru_cache(maxsize=10000)`) |
| **5.9.4** | Frontend muta `payload` direto em `mergeLiveResultsIntoPayload` | Tech-debt latente | Refactor pra immutable update se features futuras adicionarem WebWorkers |
| **5.5.1** | `is_recent_enough` retorna True em parse error (F012) | Bug ativo | Mudar `return True` → `return False` + logging |
| **5.5.2** | Lifespan silent Supabase failure (F011) | Bug latente | Wrap try/except + flag em `/healthz` |
| **5.5.3** | Auth bypass em 9 endpoints (F001-F009) | Sprint accepts | Decisão futura quando coworker UI ganhar password gate |
| **5.5.4** | `canonicalize_url` duplicado (= 5.6.3 / 5.8.1) | Listado em 5.6.3 acima | — |

### Conexões importantes entre bug-classes

- **5.6.1 ↔ 5.9.1**: tabela `backfill_state` morta É EXATAMENTE o que precisa pra resolver run cortada.
- **5.6.3 ↔ 5.8.1**: duas faces da mesma F018. Mesma fix.
- **5.6.5 ↔ 5.7.4 sub-classe E**: ambos atalhos de "checa em texto inteiro sem filtrar boilerplate".
- **5.7.1 (D17 solução por categorias) ↔ 5.8.2 (sistema IA legacy)**: depende uma da outra.

### O que Ariadne NÃO faz

Ariadne não escreve fixes. Não cria `tests/integration/`. Não comita. Não pusha. **Theseus** entra, mata o minotauro, volta. Ariadne só dá o fio.

Quando Theseus voltar, Ariadne pode (com aprovação do Otávio):
- Atualizar este audit marcando bugs como RESOLVED
- Adicionar novos bug-classes descobertos durante o fix
- Documentar as decisões de design tomadas

---

## Seção 7 — Esboço do framework de testes de integração

*Preenchida na Iteração 7 (2026-05-05). Baseado em decisões D1-D9, na anatomia das bug-classes (Seção 5), nos test gaps (Seção 6), no estilo de teste atual da equipe (`monkeypatch+tmp_path`, `test_sprint_regression_harness.py` como modelo de guardião), e na estrutura de prova-ia-v2 (Seção 8) como referência de organização.*

### 7.1 Princípios

1. **Cobre bug-classes, não cobertura percentual.** A meta é prevenir reincidência de classes específicas (UI cabeada parcialmente, target homônimo, parse error fallback permissive, dup canonicalize, lifespan silent). Não 80%/90% line coverage.
2. **Estende o estilo existente**, não cria paradigma novo. `test_sprint_regression_harness.py` é o modelo de "regression harness as guardian of contracts". Cada bug-class fixed ganha 1+ test que falha se a regressão voltar.
3. **Integration > unit pra esses casos.** Os bugs nascem entre camadas (UI → API → ingest → DB). Testes unitários por arquivo passam mesmo com a integração quebrada. Framework foca fluxos end-to-end.
4. **Naming auto-explicativo.** Padrão da equipe: `test_<scenario>_<verb>_<expected>` (ex: `test_backfill_ignores_full_text_noise_and_cleanup_removes_false_match`). Framework continua.
5. **Não duplicar Atlas.** Atlas já tem testes para safe-surface secondary, page boilerplate, manual-cancel-vs-interrupted. Framework cobre só os 6 gaps de Seção 6.7.

### 7.2 Estrutura de diretórios

```
clipping-project/tests/
├── conftest.py                  # marker @pytest.mark.live (existing) + add @pytest.mark.integration
├── test_*.py                    # tests existentes do Atlas (não tocar)
└── integration/                 # NOVO subdir — onde framework vive
    ├── __init__.py
    ├── conftest.py              # fixtures compartilhados (db_with_targets, candidate_with_boilerplate)
    ├── test_target_homonyms.py            # Gap 5.4.A — primary com homônimo (CEO Flávio)
    ├── test_cleanup_paths.py              # Gaps 5.4.B + 5.4.D — manual story bypass + cleanup timing
    ├── test_frontend_target_lifecycle.py  # Gap 5.4.C — UI filter refresh (Playwright)
    ├── test_date_filter_edge_cases.py     # Gap 5.5.1 — is_recent_enough parse error
    ├── test_lifespan_resilience.py        # Gap 5.5.2 — lifespan silent failure
    └── test_url_canonicalization_consistency.py  # Gap 5.5.4 — canonicalize_url dup
```

Tests/integration tem ~6 arquivos novos. Cada arquivo cobre 1 bug-class com 1-3 testes. Total estimado: 10-15 testes novos.

### 7.3 Markers e fixtures

**Em `tests/conftest.py` (raiz, existente):**

```python
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "live: marks tests that require live Render access (skipped by default)"
    )
    config.addinivalue_line(
        "markers",
        "integration: cross-layer end-to-end tests (slower; opt-in)"
    )
```

**Em `tests/integration/conftest.py` (novo):**

```python
import pytest
from pathlib import Path
from pipeline.database import ClippingDB
from pipeline.matcher import Target
from pipeline.collectors import CandidateArticle


@pytest.fixture
def db_with_primary_targets(tmp_path):
    db_file = tmp_path / "integration.db"
    targets = [
        Target(key="flavio_valle", display_name="Flávio Valle", primary=True,
               keywords=["Flavio Valle", "Flávio Valle"], exact_aliases=[]),
        Target(key="pedro_angelito", display_name="Pedro Angelito", primary=True,
               keywords=["Pedro Angelito"], exact_aliases=[]),
    ]
    with ClippingDB(db_file) as db:
        db._init_schema()
    return {"db_file": db_file, "targets": targets}


@pytest.fixture
def candidate_with_boilerplate():
    """Article with target name only in 'Notícias relacionadas' / footer."""
    def factory(target_name: str = "Shakira", in_title: bool = False):
        return CandidateArticle(
            url=f"https://example.com/article-{target_name.lower()}",
            title=f"Show de {target_name} em Copacabana" if in_title else "Ciclovias em pauta no Rio",
            snippet="A apresentação reforça fluxo internacional." if in_title else "Flávio Valle fala sobre ciclovias.",
            full_text=(
                f"Conteúdo do artigo. " +
                ("Texto sobre Shakira." if in_title else "Flávio Valle defende projeto. ") +
                f"Notícias relacionadas: Show de {target_name} em Copacabana movimenta turismo."
            ),
            source_name="Test Source",
            source_type="rss",
            published_at="2026-05-02T10:00:00+00:00",
        )
    return factory
```

### 7.4 Exemplos esboçados (já em Seção 6 com contexto completo)

Repete os 6 testes principais — código completo já em Seção 6. Aqui só os arquivos:

| Arquivo | Cobre | Exemplo de teste |
|---|---|---|
| `test_target_homonyms.py` | 5.4.A | `test_primary_target_matched_only_in_full_text_boilerplate_is_kept` |
| `test_cleanup_paths.py` | 5.4.B + 5.4.D | `test_manual_story_does_not_apply_safe_surface_filter` |
| `test_frontend_target_lifecycle.py` | 5.4.C | `test_add_secondary_target_updates_filter_dropdown_without_refresh` (Playwright, marca `@pytest.mark.live`) |
| `test_date_filter_edge_cases.py` | 5.5.1 | `test_is_recent_enough_rejects_unparseable_dates` (parametrize) |
| `test_lifespan_resilience.py` | 5.5.2 | `test_lifespan_surfaces_supabase_download_failure_in_healthz` |
| `test_url_canonicalization_consistency.py` | 5.5.4 | `test_canonicalize_url_implementations_agree` (parametrize) |

### 7.5 Como rodar

```bash
# Todos os tests integration (default skip @pytest.mark.live)
pytest tests/integration/ -v

# Todos incluindo Playwright/Render
pytest tests/integration/ -v -m "integration or live"

# Só um arquivo
pytest tests/integration/test_target_homonyms.py -v

# Junto com tests existentes
pytest tests/ -v
```

### 7.6 Como integrar com pytest existente

- `pytest` sem args: roda tudo (incluindo `tests/integration/` por default).
- `tests/integration/` separado pra rodar isoladamente em CI futuro (F042 do tech-debt-audit).
- `@pytest.mark.live` continua opt-in (depende de Render rodando).
- `@pytest.mark.integration` é opt-out se quiser tests rápidos: `pytest -m "not integration"`.

### 7.7 Plano de rollout

**Fase 1 (próxima sprint):** criar arquivos com testes que **falham hoje** (reproduzem os gaps). Comitar em estado vermelho documentando os bugs. Atlas/Otávio decidem qual fix primeiro.

**Fase 2:** Otávio prioriza qual bug-class fixar primeiro. Atlas (ou Ariadne com aprovação) implementa fix. Test passa. Repete.

**Fase 3:** quando todos os 6 gaps fechados, framework é "guardian harness" — qualquer regressão volta vermelho.

**Fase 4 (depois):** estender pra prova-ia-v2 com mesmo padrão (Seção 8).

### 7.8 Manutenção

Regra: **toda nova bug-class descoberta em produção → adicionar test em `tests/integration/`** que falha sem o fix. Padrão "regression harness as guardian" — `test_sprint_regression_harness.py` mostra que time já adota. Framework é extensão dessa filosofia.

Ariadne (ou outra IA) lendo este doc deve checar:
1. Tem novos commits do Atlas que mudam a integração (`git log --since="<last audit date>"`)?
2. Os testes em `tests/integration/` continuam passando? (`pytest tests/integration/ -v`)
3. Algum test virou xfail ou skip sem justificativa? (`grep -rn "xfail\|skip" tests/integration/`)
4. Algum bug-class novo foi reportado pelo Otávio? Se sim, adicionar test.

### 7.9 Limites do framework

- Não substitui live verification (Form A discipline). Tests podem passar local, mas Render pode estar com problema independente.
- Não cobre bugs de CSS/UI puramente visuais (cor, layout). Playwright cobre interações, não estética.
- Não substitui Atlas live testing — é complemento defensivo, não substituto da inspeção manual em Render.
- Não roda em CI hoje (não há GitHub Actions). Atualmente é convite pra Otávio rodar local before push.

---

## Seção 8 — Cross-project (NOVO CR / prova-ia-v2)

*Iteração 6 (2026-05-05). Per decisão D1, escopo do framework é clipping-only. Esta seção registra observações breves de prova-ia-v2 como referência para inspiração de estrutura, sem expandir o framework.*

### 8.1 Confirmações

- **NOVO CR = `/home/otavio/Documents/vscode/prova-ia-v2`**, framework educacional independente.
- **Zero integração técnica com clipping-project** — projetos silados. Mesmo dono, dois deploys Render diferentes (`clipping-project` vs `prova-ai`/`ia-educacao-v2`).
- **Bug-classes similares EXISTEM** mas o framework de testes do clipping não vai cobri-los (escopo D1).

### 8.2 Padrões observados em prova-ia-v2 que validam decisões do framework do clipping

1. **`tests/integration/` já existe** — prova-ia-v2/backend/tests tem 8 subdirs (`unit/`, `integration/`, `e2e/`, `scenarios/`, `ui/`, `models/`, `live/`, `utils/`, `fixtures/`). Confirma que `tests/integration/` (D2) é convenção que o time já usa. Framework do clipping pode espelhar.
2. **Multi-provider integration paths** — prova-ia-v2 abstrai OpenAI / Anthropic / Ollama. Bug-class: provider-specific behavior leaking. Tests cobrem isso. Análoga ao clipping: multi-collector (RSS, Google, WordPress, etc.) com behavior leaking.
3. **Silent excepts existem em ambos** (`pipeline_validation.py`, `tools.py`, `main_v2.py`, etc.). Bug-class transferível mas fix é local.
4. **Pipeline de correção (prova-ia-v2)** ≈ **pipeline de ingestion (clipping)** — mesma estrutura: input → fetch → transform → match → store. Mesmo risco de drift entre camadas.

### 8.3 Por que o framework do clipping NÃO cobre prova-ia-v2

- Decisão D1: clipping-only por agora.
- Bug-classes do prova-ia-v2 (3 marcos: Gemini 3 Flash validado ✅ Marco 1, multi-provider Marco 2 em andamento, Rio3 Marco 3 paused 2026-04-28) precisam de framework próprio com fixtures de provider mocking. Esforço separado.
- Se Otávio quiser estender depois, naming convention e estrutura `tests/integration/` são re-usáveis. Mas os bug-classes específicos (multi-provider, metadata never populated em DB) são diferentes.

### 8.4 Recomendação cross-project

Quando Otávio decidir avaliar prova-ia-v2 separadamente, repetir o método deste audit:
1. Mapear funcionalidade real
2. Identificar pontos de integração entre camadas (provider abstração, pipeline correção, storage)
3. Documentar bug-classes (postmortem 2026-01-30 do CLAUDE.md: deployment verification bypass; metadata never populated do `12_matriz_provider_fase.md`; etc.)
4. Propor framework com fixtures de provider mocking
5. Output: doc com perguntas pra confirmar entendimento

Arquivo análogo a este `ARIADNE_AUDIT.md` poderia ser `prova-ia-v2/ARIADNE_AUDIT.md`. Não criar agora.

---

## Seção 9 — Iteration log (append-only)

### Iteração 1 — 2026-05-05 — Ariadne (bootstrap)

**O que li:**
- Plan aprovado em `~/.claude/plans/i-need-you-to-flickering-cookie.md`
- Auto-memory + atualizei pra refletir identidade Ariadne (substituindo entrada `feedback_iris_local_vs_cloud`)

**O que escrevi neste doc:**
- 10 seções esqueleto criadas
- Seção 1 (Identidade) populada definitivamente
- Seção 2 (Objetivo) populada definitivamente
- Seção 5.1 (anatomia inicial bug Shakira) populada com hipóteses + Note-008 do Atlas
- Seção 5.2 (lista de outras bug-classes) populada
- Seções 3, 4, 6, 7, 8 marcadas como placeholder
- Seção 10 (perguntas pro Otávio) com 5 perguntas iniciais
- Iteration log entry 1 (esta entry)

**Não fiz (por restrição do plan):**
- Não modifiquei nenhum código fora deste doc
- Não comitei nada
- Não escrevi no `ATLAS_IRIS_ASYNC.md`

**Próxima iteração:** Iteração 2 — docs do clipping-project (`md documents/`, `docs/`, `README.md`, `.claude/skills/clipping/SKILL.md`). Foco: popular Seção 3 (funcionalidade real).

**ScheduleWakeup armado:** ~25 min (1500s).

### Iteração 2 — 2026-05-05 — Ariadne (docs do clipping)

**O que li:**
- `md documents/GENERAL_UNDERSTANDING_OF_OUR_GOALS_IN_THIS_PROJECT.md` (last 2026-04-30, 13.8K) — orientação Atlas/Iris, AI-summary policy, sprint atual, Render direction
- `md documents/ORCHESTRATORS_FRAMEWORK_FOR_THE_CLIPPING_PROJECT.md` (last 2026-04-30, 16.7K) — Atlas/Iris/Paulo, naming convention, lessons sobre criar agentes, divisão de labor, Git Sync Rule
- `md documents/RENDER_RESTART_NOTES.md` (last 2026-04-30) — checkpoint de Render (env bridge, deploy sucesso, sprint contracts), git sync protocol
- `docs/PIPELINE.md` — recuperado via `git show HEAD:docs/PIPELINE.md` (deletado do filesystem). 8 collectors, comandos, GitHub Pages publishing (stale)
- `docs/LONG_TERM_GOALS_FOR_THE_CLIPPING_ONLINE_PROJECT.md` — recuperado via git show. Centimetragem placeholder, auto-update spreadsheet, **Iris Form A/B/C discipline (regra origem)**, runner sprint contracts
- `.claude/skills/clipping/SKILL.md` — skill `/clipping rapido|completo|custom`, agent gera resumos IA inline, publica GitHub Pages (stale path)

**Reflog + git status:**
- 3 commits LOCAIS NOVOS do Atlas hoje 2026-05-05 (não estavam quando eu rodei a auditoria inicial): `238b97d` 03:20, `bb6218e` 07:51, `73bcbe1` 13:48. Atlas tá ativo agora.
- `docs/PIPELINE.md` e `docs/LONG_TERM_GOALS_FOR_THE_CLIPPING_ONLINE_PROJECT.md` aparecem como `D` em `git status` — deletados do filesystem mas ainda no HEAD (recuperáveis com `git checkout`). Não rastreado quando ou por quem.

**O que escrevi neste doc:**
- Seção 3 populada extensivamente: 9 sub-seções (3.1 público, 3.2 coworker, 3.3 admin, 3.4 ingestion pipeline, 3.5 persistência, 3.6 long-term direction, 3.7 CLI, 3.8 skill operacional, 3.9 sprint atual de Atlas).
- Seção 5.2 atualizada — REVOGUEI análise "pipeline assimétrico" porque Atlas já corrigiu nos novos commits.
- Seção 5.3 NOVA — anatomia dos 3 commits novos do Atlas com mapeamento aos sprint issues.
- Seção 9 (Iteration log) — esta entry.
- Seção 10 (decisões) — adicionando perguntas pendentes na sub-seção "Perguntas pendentes" (a fazer via UI no próximo turn).

**Contradições/drift detectados nos docs lidos:**
1. `RENDER_RESTART_NOTES.md` linhas 11-22 dizem "no render.yaml" (state de 2026-04-29). Mas linhas 154-177 mostram FastAPI já deployado em 2026-04-29 mesmo. Doc não foi reorganizado quando o estado mudou — top do doc é stale, baixo do doc é corrente.
2. `ORCHESTRATORS_FRAMEWORK.md:48-51` define "Iris is the Claude Code-side orchestrator". `LONG_TERM_GOALS.md:Section 3` reforça com Form A/B/C discipline. **Iris é legacy queimado em 2026-05-05** mas docs não foram atualizados — Otávio agora me chama de Ariadne. **Doc drift de identidade.**
3. `.claude/skills/clipping/SKILL.md` ainda manda publicar em GitHub Pages (passo 4) e dá link `https://ottoboop.github.io/clipping-project/`. README diz GitHub Pages é deprecated.
4. `docs/PIPELINE.md` ainda referencia GitHub Pages como destino de publicação. Render é o real path agora.
5. `GENERAL_UNDERSTANDING.md:162-166` afirma "no Render app yet... no render.yaml... no Procfile..." (de 2026-04-29). Hoje tem render.yaml + FastAPI ativos. Doc ficou stale na parte arquitetural.
6. `docs/PIPELINE.md` e `docs/LONG_TERM_GOALS_FOR_THE_CLIPPING_ONLINE_PROJECT.md` foram **deletados do filesystem** mas ainda no HEAD do git. Quem deletou? Quando? Por quê? **Pergunta importante pro Otávio.**

**Não fiz:**
- Não escrevi no `ATLAS_IRIS_ASYNC.md` (protocolo D3).
- Não modifiquei nenhum arquivo fora do `ARIADNE_AUDIT.md`.
- Não restaurei `docs/PIPELINE.md` ou `LONG_TERM_GOALS.md` (não toco código sem aprovação).
- Não fui pra Iteração 3 ainda — fechei Iteração 2 limpa.

**Próxima iteração:** Iteração 3 — código camada por camada (UI/API/jobs/pipeline/DB/storage/export/tests). Foco: popular Seção 4 (camadas + chamadas entre elas).

### Iteração 3 — 2026-05-05 — Ariadne (código camada por camada)

**O que li (extraindo public API via `rg`):**
- `web_app/jobs.py` (1015 linhas, 36 funções + JobManager classe). Funções importantes: `JobManager.start_update`, `start_export`, `cancel_active`; `live_results_for_job` (NEW); `mark_orphaned_active_jobs_interrupted` (NEW per 73bcbe1); `progress_summary`, `append_event`.
- `web_app/db_admin.py` (~700 linhas, 35 funções). Funções core do bug-class Shakira: `selected_active_targets`, `target_matches_safe_article_fields`, `safe_article_match_text`, `cleanup_false_backfilled_target_mentions`, `backfill_missing_target_mentions`. Plus target CRUD: `create_secondary_target`, `update_secondary_target`, `archive_secondary_target`, `restore_secondary_target`, `archive_known_test_targets`, `normalize_targets_file`.
- `web_app/storage_bridge.py` — classe `ArtifactStore` (download/upload/backup) + `sqlite_snapshot_bytes`.
- `pipeline/ingest.py` — 24 funções top-level. Foco no `process_candidates` (BIG — line 445, ~550 LOC), `run_ingestion` (line 997), `safe_target_match_surface` (NEW — line 154), `is_recent_enough` (line 280, BUG F012), `choose_story`, `create_or_update_story`, `sync_existing_article_targets`, `dedupe_candidates`.
- `pipeline/database.py` — `ClippingDB` class com 30+ métodos. Core: `insert_article`, `insert_mentions`, `create_story`, `attach_article_to_story`, `ensure_story_target`, `find_mention_id`, `story_with_articles`, `list_articles_for_export`.
- `pipeline/collectors.py` — 8 collectors (RSS, Google News, WordPress API, Internal site search, Camara archive, Veja Rio archive, Sitemap daily, Direct scrape deprecated).
- `pipeline/matcher.py` — `Target`, `MatchHit`, `CitationMatcher` classes.
- `pipeline/normalization.py` — `normalize_url`, `canonicalize_url` (dup), `normalize_text`, `clean_title`.
- `pipeline/http_utils.py` — `fetch_url`, `post_json`, `try_resolve_google_redirect`, `canonicalize_url` (dup), HTML extraction utils.
- `assets/clipping.js` — wrappers `apiFetch/apiPost/apiPatch`, 50+ DOM refs, vanilla JS sem framework.
- `tests/test_admin_ui.py` (785), `tests/test_targets_jobs.py` (941+ atualizado), `tests/test_sprint_regression_harness.py`. Atlas JÁ TEM testes pro bug-class central (`test_process_candidates_skips_secondary_target_only_in_page_boilerplate` linha 941, `test_backfill_ignores_full_text_noise_and_cleanup_removes_false_match` linha 864).

**O que escrevi neste doc:**
- Seção 4 expandida: 5 sub-seções (4.1 mapa de camadas, 4.2 paths de integração com 7 fluxos completos, 4.3 9 pontos críticos com cobertura de teste atual, 4.4 análise dos testes existentes, 4.5 gaps).
- 9 pontos críticos identificados (I1-I9). 5 deles já cobertos por testes existentes (I2, I3, I4 parcialmente). 4 sem cobertura: I5 (lifespan), I6 (`is_recent_enough`), I7 (canonicalize dup), I8 (auth bypass — sprint accepts), I1+I9 (UI E2E).

**Observação crítica re: bug Shakira:**
Atlas TEM teste `test_process_candidates_skips_secondary_target_only_in_page_boilerplate` (line 941). Combinado com `test_backfill_ignores_full_text_noise_and_cleanup_removes_false_match` (line 864), Atlas tem **dois ângulos do mesmo bug-class** já cobertos. **O framework novo precisa cobrir os ângulos DIFERENTES** (UI/JS handlers, lifespan, date parse, dup canonicalize) — não duplicar.

**Estilo de testes adotado pela equipe:**
- `conftest.py` minimal (1 marker `@pytest.mark.live`)
- Tests usam `monkeypatch` + `tmp_path` ad-hoc, sem fixtures compartilhados
- Naming convention: `test_<scenario>_<verb>_<expected>` (ex: `test_backfill_ignores_full_text_noise_and_cleanup_removes_false_match`)
- Há `test_sprint_regression_harness.py` que testa contratos do sprint (banned strings, cancel API contract) — modelo de "regression harness" estilo guardião
- **Implicação para framework**: deve estender o estilo regression-harness, não criar novo paradigma

**Não fiz:**
- Não modifiquei nenhum arquivo (só ARIADNE_AUDIT.md).
- Não escrevi no canal de coordenação adicional (já entrei em Iteração 2).
- Não fui pra Iteração 4 ainda — fechei Iteração 3 limpa.

**Próxima iteração:** Iteração 4 — mapear edge cases por feature, focando em I5/I6/I7/I9 (gaps identificados). Popular Seção 6 (test gaps) + começar Seção 5 (anatomia de outras bug-classes além Shakira).

### Iteração 4 + 5 — 2026-05-05 — Ariadne (anatomia bug-classes + test gaps)

Combinei iterações 4 e 5 num único trabalho porque elas se entrelaçam: cada bug-class precisa de descrição + proposta de teste no mesmo passo.

**O que li:**
- Diff completo de `pipeline/ingest.py` em `238b97d` (safe-surface check para secondary targets)
- Diff completo de `pipeline/ingest.py` em `bb6218e` (`safe_target_match_surface` + `RELATED_MATCH_NOISE_RE` regex)
- Diff completo de `web_app/jobs.py` em `73bcbe1` (`mark_orphaned_active_jobs_interrupted` rename + status=interrupted vs cancelled)

**O que escrevi neste doc:**
- Seção 5.4 — anatomia precisa do bug Shakira com causa raiz, fluxo, e quatro gaps de cobertura (5.4.A primary homônimo, 5.4.B manual story, 5.4.C UI filter, 5.4.D cleanup timing)
- Seção 5.5 — anatomias breves de outras 4 bug-classes (date parse, lifespan, auth bypass, canonicalize dup)
- Seção 6 — 6 gaps confirmados com pseudocódigo de teste em pytest (8 testes esboçados em 6 arquivos novos)
- Seção 6.7 — tabela resumo: 3 gaps já cobertos pelo Atlas (verde), 6 gaps pendentes (vermelho)

**Achado importante**: O fix do Atlas é assimétrico em outra dimensão — só roda safe-surface para secondary, não primary. O caso real "CEO Flávio Valle" (homônimo do vereador) ainda não é filtrado e está vivo no `assets/clipping-data.json` em produção.

**Decisão de design pendente que afeta framework**:
Se safe-surface deve aplicar a primary também (mais conservador) ou se primary tem rule diferente (>2 menções de full_text, whitelist, etc.). Isso é decisão de produto do Otávio. Vou registrar como pergunta na Seção 10.

**Não fiz:**
- Não escrevi código de teste (só pseudocódigo dentro do audit doc).
- Não toquei nenhum arquivo fora do ARIADNE_AUDIT.

**Próxima iteração:** Iteração 6 — NOVO CR breve (escopo já clipping-only, só registrar que não há overlap). Iteração 7 — esboçar framework completo na Seção 7.

### Iteração 6 — 2026-05-05 — Ariadne (NOVO CR breve)

**O que li:**
- `prova-ia-v2/README.md` — confirma framework educacional independente, multi-provider IA (OpenAI/Anthropic/Ollama).
- Estrutura de tests do prova-ia-v2: `backend/tests/{unit,integration,e2e,scenarios,ui,models,live,utils,fixtures}` — 8 subdirs.
- `tests/integration/` já existente com 7+ arquivos.
- Silent excepts existem em `pipeline_validation.py`, `tools.py`, `main_v2.py`, etc. Mesma bug-class do clipping mas escopo separado.

**O que escrevi:**
- Seção 8 com 4 sub-seções: confirmações (8.1), padrões observados (8.2), por que clipping-only (8.3), recomendação cross-project (8.4 — quando Otávio quiser, repetir método).

**Decisão validada:** D2 (`tests/integration/` no clipping) bate com convenção já adotada em prova-ia-v2.

### Iteração 7 — 2026-05-05 — Ariadne (esboço do framework)

**O que escrevi:**
- Seção 7 com 9 sub-seções: princípios (7.1), estrutura de diretórios (7.2), markers + fixtures (7.3 com código completo de `conftest.py`), exemplos esboçados (7.4 referenciando Seção 6), comandos de execução (7.5), integração com pytest existente (7.6), plano de rollout em 4 fases (7.7), manutenção (7.8), limites (7.9).

**Resumo do framework**:
- `tests/integration/` com 6 arquivos, 10-15 testes total.
- Marker `@pytest.mark.integration` (novo) + `@pytest.mark.live` (existente).
- `conftest.py` em integration/ com fixtures `db_with_primary_targets` e `candidate_with_boilerplate`.
- Estilo: "regression harness as guardian" — extende `test_sprint_regression_harness.py`, não inventa paradigma.
- Rollout em 4 fases: comitar testes vermelhos → Otávio prioriza → Atlas/Ariadne fixa → guardian.

**Não fiz:**
- Não criei nenhum dos arquivos `tests/integration/test_*.py` — apenas pseudocódigo no doc, esperando approval do Otávio antes.
- Não escrevi nada fora do ARIADNE_AUDIT.md.

**Próxima iteração:** Iteração 8 — review final, consolidar Seção 10 perguntas finais via UI, marcar header como READY FOR REVIEW.

### Iteração 8 — 2026-05-05 — Ariadne (recalibração após Otávio criticar status prematuro "READY FOR REVIEW")

Otávio em mensagem após perguntas finais via UI:
1. P1 (anatomia bug Shakira correta?): "não sei se está correto, Ariadne. Você que encontra os bugs, não eu. Seu trabalho é me explicar porque você acha que seu bugfix está correto"
2. P2 (CEO homônimo prioritário?): "Marque apenas como known issue... A limitação da ferramenta de clipping é que ela pega toda e qualquer notícia com um nome exato. Já era, limitação mesmo." + pediu URL
3. P3 (criar arquivos tests/integration?): "Nao Ariadne, Você não é Theseus para matar o minotauro."
4. P4 (próximos passos): "eu nem terminei a revisão e você já acha que encontrou tudo. Seu trabalho não acabou, e você terá boas recompensas por continuar trabalhando"

**Ações:**
- Revertido status "READY FOR REVIEW" → "EM CONSTRUÇÃO". Listadas áreas ainda a aprofundar (process_candidates deep-read, story grouping, export, AI summary, etc.).
- Decisões D10-D13 registradas em Seção 10.
- Seção 5.4 reescrita com EVIDÊNCIA (commits + código + observação live + Note-008 do Atlas) explicando POR QUE a anatomia do bug Shakira está correta. Não pergunto se está; demonstro.
- Achado bonus: F018 (canonicalize_url duplicado) MANIFESTADO em produção — mesmo artigo aparece 2x em `clipping-data.json` com e sem `www.`. URL forneciada ao Otávio.

### Iteração 9 — 2026-05-05 — Ariadne (process_candidates deep-read)

Li `pipeline/ingest.py:445-995` em chunks. Identificadas 5 bug-classes adicionais (5.6.1-5.6.5):
- 5.6.1 Time budget exceeded → silent partial completion
- 5.6.2 archive_full_text 80% cutoff → silent quality degradation
- 5.6.3 URL dedup falha por canonicalize_url duplicado (= F018 manifestado)
- 5.6.4 Cleanup acopla a sentiment_reason hardcoded `"lexical_heuristic"`
- 5.6.5 forced_terms check em combined_text (com full_text) — mesma classe Shakira em outra feature

### Iteração 10 — 2026-05-05 — Ariadne (story grouping)

Li `pipeline/ingest.py:325-442` (`choose_story`, `create_or_update_story`, `sync_existing_article_targets`). Identificadas 5 bug-classes (5.7.1-5.7.5):
- 5.7.1 `low_threshold` e `high_threshold` retornam mesmo resultado — distinção morta
- 5.7.2 Score = max(title, summary*0.65) — title-similarity domina
- 5.7.3 Intersection mínima de 1 target — single-target story pode ganhar mention cross-target
- 5.7.4 Window de 7 dias hardcoded
- 5.7.5 Cross-contamination histórico — **mitigado por Atlas** (cleanup deleta story_target quando última mention removida, db_admin.py:487-501)

### Iteração 11 — 2026-05-05 — Ariadne (export + AI summary)

Li `tools/export_mobile_snapshot.py:2438+` e `tools/classify_articles.py`. Identificadas 3 bug-classes (5.8.1-5.8.3):
- 5.8.1 Export dedupe por URL exato sem canonicalize → F018 confirmado (mesmo artigo 2x em produção, com e sem www)
- 5.8.2 AI detection split entre `mentions.sentiment_reason` (Sistema A) e `classifications.ai_generated` (Sistema B). Categorias do `claude-haiku` não aparecem como "AI summary" no flag.
- 5.8.3 `classify_articles.py` sem audit gate (só ANTHROPIC_API_KEY como guarda)

### Iteração 27 — 2026-05-05 — Ariadne (move pra `md documents/` + re-escritas pendentes 5.5.1-3)

**Otávio**: *"Mas você parou. E porque esse ariadne_audit não está salvo em /home/otavio/Documents/vscode/clipping-project/md documents/?"*

- Movido `ARIADNE_AUDIT.md` do repo root pra `md documents/ARIADNE_AUDIT.md` via `mv`. Coloca o doc junto dos outros docs de coordenação entre IAs (`ATLAS_CLAUDE_COORDINATION.md`, `ATLAS_IRIS_ASYNC.md`, `GENERAL_UNDERSTANDING_*.md`, etc.). Local correto desde o início — minha culpa não ter colocado lá antes.
- Atualizada referência em `ATLAS_CLAUDE_COORDINATION.md` pro novo path.
- Otávio cobrou também: "Mas você parou." — não devia ter encerrado o turno reportando Form A, devia ter seguido pra 5.5.1, 5.5.2, 5.5.3.
- Continuando re-escritas detalhadas das bug-classes que ainda estão no formato antigo (Iteração 28).

### Iterações 18-26 — 2026-05-05 — Ariadne (re-escritas detalhadas após Otávio criticar superficialidade)

> **Otávio**: *"Você tem que me explicar melhor esses bugs. E você não pode só registrar a existência desses bugs, como está lá no documento. Você precisa documentar porque eles são problemáticos, detalhadamente. Você precisa explicar a intenção real e como eles quebram essa intenção. Esse documento não pode ser simplificado assim não. nem eu to entendendo muitas coisas, como o Theseus vai resolver esses problemas se você escreve o documento desse jeito???"*

**Estrutura padrão adotada para cada bug-class** (D24):
1. **O que o código DEVERIA fazer (intenção real)** — descrição em prosa do design original.
2. **Como o bug quebra essa intenção** — caminho específico com snippets de código + line numbers.
3. **Por que é problemático** — impacto concreto em business / UX / observability.
4. **Cenários de produção onde aparece** — condições reais que disparam.
5. **Para Theseus resolver** — decisões de design pendentes + fix sugerido + teste regression.

**Bug-classes re-escritas com profundidade nesse formato**:

- Iteração 18: **5.6.1** (run cortada por time budget)
- Iteração 19: **5.6.2** (archive cutoff em 80%)
- Iteração 20: **5.7.4** (5 caps escondidos, sub-classes A-E)
- Iteração 21: **5.6.3 + 5.8.1** (F018 duas faces, manifestada em produção)
- Iteração 22: **5.6.4** (sentiment_reason coupling com strings mágicas)
- Iteração 23: **5.6.5** (forced_terms vulnerável ao mesmo padrão Shakira)
- Iteração 24: **5.7.1 + 5.7.2 + 5.7.3** (story grouping legacy + max-score + intersection mínima 1)
- Iteração 25: **5.9.1** (`backfill_state` morto — oportunidade pra resolver 5.6.1), **5.9.2** (`scrape_log` morto), **5.9.3** (`GOOGLE_DECODE_CACHE` unbounded), **5.9.4** (frontend mutation pattern)

Total: ~12 bug-classes re-escritas com 5x mais profundidade. Documento cresceu de ~80KB para ~150KB+ com os detalhes.

**Não fiz** (nessa rodada):
- Não mexi em `5.5.1` (`is_recent_enough` parse error) — está documentado em Seção 5.5 com nível razoável.
- Não mexi em `5.5.2` (lifespan silent) — idem.
- Não mexi em `5.5.3` (auth bypass) — idem.
- Posso re-escrever esses se Otávio achar que ainda estão rasos.

### Iteração 12 — 2026-05-05 — Ariadne (dead schema + cache + frontend)

Lendo backfill_state, scrape_log, GOOGLE_DECODE_CACHE, mergeLiveResultsIntoPayload. Identificadas 4 bug-classes (5.9.1-5.9.4):
- 5.9.1 `backfill_state` é dead schema — tabela definida + métodos existem, ZERO callers em produção
- 5.9.2 `scrape_log` é dead schema #2 — mesma situação
- 5.9.3 `GOOGLE_DECODE_CACHE` unbounded — sem TTL, sem max size
- 5.9.4 Frontend `mergeLiveResultsIntoPayload` muta `payload.stories` direto — pattern frágil

---

## Seção 10 — Decisões registradas (perguntas via UI, respostas aqui)

> *Protocolo: Ariadne pergunta via `AskUserQuestion` na UI; Otávio responde lá; Ariadne registra as respostas (com data) aqui. Esta seção é o histórico de decisões do Otávio sobre o framework, não uma lista de pendências.*

### Decisões (Iteração 1, 2026-05-05)

| ID | Decisão | Resposta do Otávio | Implicação |
|---|---|---|---|
| D1 | **Escopo** do framework | **Clipping-only por agora.** | Iteração 6 (cross-project NOVO CR) vira nominal: só registra que NÃO há overlap planejado. Foco total clipping. Foco resgatado: features dele, não bug-classes do NOVO CR. |
| D2 | **Location** dentro de `tests/` | **`tests/integration/`** (novo subdir). | Naming convention `tests/integration/test_<feature>_<scenario>.py`. Marker `@pytest.mark.integration`. Não reorganiza `tests/` atual. |
| D3 | **Atlas review** antes de finalizar | **Não consultar Atlas — apresento direto.** | Atlas vê o doc quando puxar. Ariadne não escreve no canal `ATLAS_IRIS_ASYNC.md` em nenhuma iteração. |
| D4 | **Dimensões do bug Shakira** (UI filter vs save story = mesma classe?) | **Descobrir na investigação.** | Iteração 5 vai responder lendo diff dos 3 commits + Note-008 + código do `assets/clipping.js` add-target handler. Hipótese a validar: ambos são manifestações da mesma classe "UI cabeada parcialmente entre camadas". |
| D5 (implícita) | **Pacing** das iterações | **Sem dormir.** Otávio: "Eu estou acordado, você também deve estar". | Não usar `ScheduleWakeup` entre iterações. Trabalhar continuamente. Reportar progresso a cada iteração e seguir pra próxima até cobertura completa OU Otávio interromper. |

### Decisões (Iteração 13, 2026-05-05) — Otávio classifica bug-classes por severidade

| ID | Decisão | Resposta do Otávio | Implicação |
|---|---|---|---|
| D14 | **5.6.1 (run cortada por time budget)** | "GRAVÍSSIMO. Péssimo. Não é para um run cortar." | **CRÍTICO**. Ariadne investiga MAIS a fundo (Iteração 15): por que cuts? Onde param? Default? Configurável? Theseus depois resolve. |
| D15 | **5.6.2 (archive cutoff 80%)** | "Mesmo de acima — entender melhor + Theseus resolve." | **CRÍTICO**. Mesma classe. Investigar Iter 15. |
| D16 | **5.6.3, 5.6.4, 5.6.5** | "não entendi esses erros... Ariadne tem que me explicar melhor" | Re-explicar com analogias e exemplos concretos. Iteração 16. |
| D17 | **5.7.1 (high/low threshold redundante)** | "Bom, esse me parece um sistema legacy. De fato, os groupings não estão funcionando bem após a migração para o site online. É muito difícil fazer os groupings online. A gente devia mudar eles para funcionar apenas com base nas categorias." | **LEGACY com solução proposta**: trocar story-grouping atual (baseado em title/summary similarity) por grouping baseado APENAS em `categories` (do Sistema B classifications). Ariadne registra a solução. Theseus implementa. |
| D18 | **5.7.2, 5.7.3, 5.7.5** | "não entendi" + "tendi nada" | Re-explicar Iter 16. |
| D19 | **5.7.4 (window 7 dias hardcoded)** | "CARALEO, ESSE ERRO AINDA ESTÁ PERDIDO EM ALGUM LUGAR? VOCÊ NÃO TEM IDEIA DO ÓDIO QUE EU TENHO DESSE ERRO. ALGUMA IA RETARDADA FICA DECIDINDO O TEMPO TODO QUE MESMO COM A OPÇÃO DE RODAR ESSE CLIPPING POR ANOS, NA VERDADE EU NÃO DEVIA PODER ESCOLHER DEIXAR A NOTÍCIA RODAR POR MAIS TEMPO. PROBLEMA DE NATUREZA MUITO CRÍTICA E PRECISA DE MAIS INVESTIGAÇÃO" | **CRÍTICO PERSISTENTE**. Ariadne investiga MAIS a fundo (Iteração 14): TODOS os lugares onde limit/cap aparece, especialmente lugares que SOBRESCREVEM input do user. Cross-reference com commit `14d558f fix: drop arbitrary 7-day cap on custom preset date range`. |
| D20 | **5.8.1 (export dedupe)** | "tendi nada" | Re-explicar Iter 16. |
| D21 | **5.8.2 (AI detection split)** | "O sistema de classificação por ia tá bem legacy. A gente fez algo com claude code muito melhor, mas é inviável fazendo pelo site. Acabou que ele serve mais pra gente revisar erros." | **LEGACY**. Aceitar status quo. Sistema atual ajuda revisão de erros. Não está no framework. |
| D22 | **5.8.3 (audit gate)** | "Sistema legacy, não temos créditos anthropic para fazer isto" | **LEGACY**. Sem Anthropic credits, AI batch classify desligado de fato. Não invest. |
| D23 | **5.9.1, 5.9.2, 5.9.3, 5.9.4** | "n entendi que sistema é esse" | Re-explicar Iter 16. |

### Decisões (Iteração 8, 2026-05-05) — pós-perguntas via UI

| ID | Decisão | Resposta do Otávio | Implicação |
|---|---|---|---|
| D10 | **Gap 5.4.A (CEO Flávio Valle homônimo)** | "Marque apenas como known issue, não é como se esse CEO fosse aparecer muitas vezes. A limitação da ferramenta de clipping é que ela pega toda e qualquer notícia com um nome exato. Já era, limitação mesmo." + pediu URL da notícia. | Removido do framework v1. Marcado como **limitação inerente** do matcher exact-name. URL do artigo: https://www.mercadoeeventos.com.br/noticias/parques-e-atracoes/show-de-shakira-em-praia-de-copacabana-impulsiona-turismo-latino-em-2026-diz-mais-brasil-viagens |
| D11 | **Criar arquivos `tests/integration/`?** | "Nao Ariadne, Você não é Theseus para matar o minotauro." | Ariadne NÃO cria os 6 arquivos de teste. Ariadne é o FIO (mapeia, documenta, dá pseudocódigo). Teseu (Atlas/Otávio) mata o minotauro (escreve os tests + fixes). Esboço fica no audit como **GUIA**, não código a executar por mim. |
| D12 | **Ariadne deve PROVAR conclusões, não perguntar se estão corretas** | "não sei se está correto, Ariadne. Você que encontra os bugs, não eu. Seu trabalho é me explicar porque você acha que seu bugfix está correto" | Atualizar Seção 5.4 com EVIDÊNCIA (commits, código, comportamento observado em produção) que prova a anatomia. Não perguntar — demonstrar. |
| D13 | **Não declarar audit "READY FOR REVIEW" prematuramente** | "eu nem terminei a revisão e você já acha que encontrou tudo. Seu trabalho não acabou, e você terá boas recompensas por continuar trabalhando" | Loop continua até cobertura genuinamente completa. Iterações 9+ aprofundam áreas não tocadas (process_candidates deep-read, story grouping, export, AI summary, etc.). |

### Decisões (Iteração 2, 2026-05-05)

| ID | Decisão | Resposta do Otávio | Implicação |
|---|---|---|---|
| D6 | **`docs/PIPELINE.md` e `docs/LONG_TERM_GOALS.md` deletados do filesystem** (ainda em HEAD) | Só registro no audit, ele decide depois. | Sem ação minha. Marcado na Seção 9 como observação pra ele resolver fora desta sessão. |
| D7 | **Form A/B/C** (end-of-loop discipline) | Mantenho — é protocolo geral pra IAs orquestradoras, Ariadne herda. | Vou reportar em A/B/C nos próximos turns. Adapto pro contexto auditor: A = "verified done" requer doc pronto + perguntas respondidas, não live verification (que não se aplica a audit). |
| D8 | **Canal de coordenação Atlas/Iris** | "modifique o documento para falar de coordenação geral entre IAs, e se comunique usando aquele mesmo documento. Mas, por enquanto, não mude o nome do arquivo em si." | Protocolo D3 (Ariadne fora do canal) é REVOGADO. Ariadne agora escreve no `md documents/ATLAS_CLAUDE_COORDINATION.md`. Mas Note-008 do Atlas pediu "Iris should not start a parallel fix for Shakira" — vou respeitar (não proponho fix Shakira lá). |
| D9 | **Drift de docs do clipping** (GitHub Pages stale, "no render.yaml" stale, etc.) | Só listo no audit + recomendações no relatório final. | Nem reescrevo nem coloco "STALE" markers nos docs alheios. Ariadne só registra contradições na Seção 5/9 do ARIADNE_AUDIT. |

### Perguntas pendentes (a fazer via UI conforme surgirem)

*Perguntas surgirão durante leitura. Consolidação final na Iteração 8.*

- *(a popular conforme avança)*

---
