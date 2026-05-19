# Work Log — Detalhado (Sub-ações)

**Created:** 2026-05-19
**Loop:** Clipping Client Management (`md documents/clipping-client-management-loop-2026-05-19/`)
**Anchor:** [`LONG_TERM_GOALS.md`](LONG_TERM_GOALS.md)
**Mantra:** [`MANTRA.md`](MANTRA.md) · repetido a cada 5 respostas substantivas
**Companion doc (estratégico):** [`WORK_LOG_MAJOR.md`](WORK_LOG_MAJOR.md)
**Pontos de registro (review cronológico):** [`SESSION_LOG.md`](SESSION_LOG.md)
**Goals já entregues:** [`GOALS_ATINGIDOS.md`](GOALS_ATINGIDOS.md)

---

## Propósito

Rastreabilidade granular de **cada sub-ação** dentro de um sprint: comando rodado, arquivo editado, hipótese descartada, decisão pequena que poderia ser revertida. IAs futuras consultam aqui antes de repetir verificações ou diagnósticos.

**Não vai aqui:** decisões estratégicas de método (essas são do `WORK_LOG_MAJOR.md`).

---

## Quando adicionar uma entrada

- Cada comando significativo rodado (testes, deploys, leituras de log, smoke em produção)
- Cada arquivo editado (com motivo + linhas afetadas)
- Cada hipótese formulada e descartada (não só as que viraram fix)
- Cada decisão pequena que poderia ser revertida ("escolhi nome X em vez de Y porque Z")

---

## Template de entrada

```markdown
### YYYY-MM-DD HH:MM — [Sub-ação curta]

**Contexto (link pro major):** [link à entrada correspondente em WORK_LOG_MAJOR.md]
**Ação:** [comando, edit, leitura — concreto e curto]
**Resultado:** [output bruto resumido — código de status, número de testes, mensagem de erro literal]
**Interpretação:** [o que isso significa pra próxima sub-ação]
```

---

## Disciplina de leitura (obrigatória pra IAs)

- **Antes de re-rodar verificação ou repetir diagnóstico:** ler entradas recentes pra ver se já foi feito hoje
- **Se sub-ação é repetida legitimamente** (ex: re-rodar smoke pós-deploy): marcar `**re-execução de [entrada anterior]**` e dizer por quê
- **Nunca** rodar smoke/test/curl como ritual sem checar antes se o resultado já foi obtido

---

## Entradas

### 2026-05-19 11:36 — Login admin em prod via curl

**Contexto (link pro major):** [`WORK_LOG_MAJOR.md`](WORK_LOG_MAJOR.md) — entrada de método pro Goal 4 (baseline)
**Ação:** `curl POST https://clipping-project.onrender.com/api/login` com senha admin, salvando cookie em `/tmp/clipping_cookie.txt`
**Resultado:** HTTP 200, `{"ok":true,"role":"admin","profile":"admin"}`. Cookie `clipping_admin` salvo.
**Interpretação:** auth em prod operacional pro admin. Posso seguir pros GETs autenticados.

### 2026-05-19 11:37 — Mapa de endpoints via grep

**Contexto:** baseline Goal 4
**Ação:** `grep "@app.get|post|patch..." web_app/app.py`
**Resultado:** 25 rotas. Pra targets: GET `/api/targets`, POST `/api/targets`, PATCH `/api/targets/{key}`, POST `/api/targets/{key}/archive`, POST `/api/targets/{key}/restore`. **Nenhuma rota pra primary target.**
**Interpretação:** Goal 5 (admin add/remove/demote primário) NÃO tem backend hoje. Tem que ser construído. Add secundário tem.

### 2026-05-19 11:39 — GETs autenticados (healthz, status, targets, csrf)

**Contexto:** baseline Goal 4
**Ação:** 4 curls GET com cookie admin.
**Resultado:**

- `/healthz`: 200. `viewerAuthConfigured: true`, `loginConfigured: true`, `missingConfig: []`, `storage.enabled: true`, `job: idle`. Versão `2026-05-06-durable-source-ledger-wp-internal-v2`.
- `/api/update/status`: 200. `{"current":{"status":"idle"},"recent":[]}`.
- `/api/targets`: 200. 6 targets ativos. Primary: `flavio_valle`, `pedro_angelito`. Secondary: `pedro_duarte`, `bernardo_rubiao`, `shakira`, `vorcaro` (visto na resposta truncada, pode ter mais).
- `/api/csrf`: 200. Token: `-JcTxSbh9DuSY3cUW9tinrYQHWQhRV_Qb_usse7sCgc`.

**Interpretação:** prod está saudável e configurado. CSRF token disponível pra mutações.

### 2026-05-19 11:42 — POST /api/targets payload vazio (probing)

**Contexto:** baseline Goal 4 — testar shape do erro pra validar Goal 5 ("erros claros")
**Ação:** `curl POST /api/targets` com body `{}` e CSRF token
**Resultado:** HTTP 400. Body:

```json
{
  "error": "target_validation_error",
  "message": "Informe um nome de exibicao com pelo menos 3 caracteres.",
  "field": "display_name",
  "suggestion": "Digite um nome de exibicao com 3 caracteres ou mais.",
  "detail": { ... mesmo conteúdo ... }
}
```

**Interpretação:** **achado importante** — o backend já retorna o shape estruturado `{error, message, field, suggestion}` que o Goal 5 exige. Falha está em outro lugar (UI ou casos-edge).

### 2026-05-19 11:43 — POST /api/targets payload válido (cria target real)

**Contexto:** baseline Goal 4 — testar happy path
**Ação:** `curl POST /api/targets` com `{"label":"TESTE BASELINE"}` e CSRF
**Resultado:** HTTP 200. Target `teste_baseline` criado, sincronizado (sync uploaded 5 artifacts, updatedCount=0, mentionsInserted=0).
**Interpretação:** **happy path funciona end-to-end pelo backend.** Cria DB row, dispara sync que upa artifacts pro Supabase. O fato de `mentionsInserted=0` é esperado (target novo, sem articles históricos). **Bug reportado pelo Otávio NÃO é nessa rota pra esse caso.**

### 2026-05-19 11:44 — Cleanup do target de teste

**Contexto:** evitar poluir prod com target de teste
**Ação:** `curl POST /api/targets/teste_baseline/archive` com `{"reason":"limpeza baseline catalog"}`
**Resultado:** HTTP 200. `archived: true, archived_at: 2026-05-20T16:44:27Z, archive_reason: "limpeza baseline catalog"`.
**Interpretação:** archive funciona. Mas note que `archived_at` tá com **data de amanhã** (`2026-05-20`) enquanto hoje é `2026-05-19` no relógio local — possível issue de timezone do servidor (UTC vs America/Sao_Paulo, diferença +3h = 11:44 BRT vira 14:44 UTC, mas a marca 16:44 sugere outro fuso). **Watch item, não bloqueante agora.**

### 2026-05-19 11:46 — Leitura de db_admin.py linhas 340-440

**Contexto:** entender o que `create_secondary_target` faz por baixo
**Ação:** Read `web_app/db_admin.py` offset=340 limit=100
**Resultado:**

- `create_secondary_target` (`db_admin.py:356-376`): chama `clean_target_payload`, gera slug único, monta dict com `primary: False` hardcoded, escreve via `write_targets_atomic`. Source da verdade = `data/targets.json` (arquivo, não DB).
- `update_secondary_target` (`db_admin.py:379-400`): tem `ensure_secondary_mutable(row)` — provavelmente bloqueia mutar primary.
- `archive_secondary_target` (`db_admin.py:403-411`): também passa por `ensure_secondary_mutable`. Por isso primary não pode ser arquivado pelo endpoint.
- `restore_secondary_target` (`db_admin.py:414-426`): idem. Recusa restaurar "synthetic test target".

**Interpretação chave:** primary management = **bloqueado por design** via `ensure_secondary_mutable`. Pra Goal 5, vai precisar (a) adicionar endpoints novos pra primary OU (b) relaxar `ensure_secondary_mutable` quando role for admin + flag explícita.

### 2026-05-19 11:48 — Leitura de assets/clipping.js handler de add-target

**Contexto:** investigar hipótese (a) e (b) — UI pode estar mandando payload errado ou ignorando erro estruturado
**Ação:** grep + Read `assets/clipping.js:2150-2181` (handler do form) + `assets/clipping.js:314-345` (apiErrorMessage + friendlyError)
**Resultado:**

- Handler envia body `{display_name, keywords, exact_aliases}` — **bate com o que backend espera**
- `apiErrorMessage` (linha 318-320) extrai `detail.message + detail.suggestion` corretamente
- `friendlyError` (linha 343) retorna `raw` se for string normal — preserva o erro estruturado
- **No happy/sad path testado, UI mostra o erro do backend corretamente.** Hipótese (a) e (b) não se confirmam pra essa rota nessa configuração.

**Interpretação:** UI não é o culpado no caminho estruturado. Bug deve estar em (c): casos-edge não testados ainda. Próximo teste: conflito de nome duplicado.

### 2026-05-19 11:49 — POST /api/targets com nome duplicado (display_name="Shakira")

**Contexto:** testar caso-edge — backend deveria retornar 409 conflict ou mensagem clara
**Ação:** `curl POST /api/targets {"display_name":"Shakira"}` — nome já existe no sistema (target ativo)
**Resultado:** HTTP **200**. **Criou `shakira_2` silenciosamente**, com mesmo display_name e label "Shakira". Nenhum erro, nenhuma indicação de conflito.

```json
{"key":"shakira_2", "label":"Shakira", "display_name":"Shakira", ...}
```

**Interpretação:** **BUG GRAVE confirmado.** Backend não detecta duplicação de display_name. Cria slug único (`shakira_2`) mas mantém label/display_name idênticos — o usuário acaba com dois targets visualmente iguais. Não é "fake UI" no sentido clássico (a UI mostra a entrada, o backend cria de fato), mas é falha de validação semântica. Cai exato na failure class #4 do LONG_TERM_GOALS ("erro genérico em vez de mensagem específica" — aqui é PIOR: nem erro tem, é sucesso enganoso).

### 2026-05-19 11:50 — Cleanup shakira_2

**Contexto:** prod tem agora `shakira` + `shakira_2` (duplicata). Limpar.
**Ação:** `curl POST /api/targets/shakira_2/archive {"reason":"duplicata acidental do catalog Goal 4"}`
**Resultado:** HTTP 200, archived. `archived_at: 2026-05-20T16:48:28Z` (mesma discrepância de TZ — watch item 11:44).
**Interpretação:** archive funciona pra remover do listing ativo. Mas a row continua em `data/targets.json` com `archived: true`. Sem opção de hard-delete via API.

### 2026-05-19 11:52 — Leitura de infra de ValidationError + target_validation_payload

**Contexto:** Major 11:50 propôs fix da duplicata; preciso saber como o backend mapeia ValidationError pra resposta estruturada
**Ação:** Read `web_app/db_admin.py:1-100` (imports + classe `ValidationError`), Read `web_app/app.py:100-190` (`target_validation_payload`, `target_validation_response`)
**Resultado:**

- `ValidationError(ValueError)` — classe simples, só carrega `message` (via `str(exc)`)
- `target_validation_payload` (app.py:151-176): mapeia substring da mensagem → `field` + `suggestion`. Default `field="display_name"`, `suggestion="Revise o nome e tente novamente."`. Já trata 4 casos (3-chars, desconhecido, principais, restaure)
- `clean_target_payload` (db_admin.py:321-353): normaliza display_name via `normalize_text`, valida >= 3 chars, monta keywords/aliases

**Interpretação:** fix é simples — em `create_secondary_target` (db_admin.py:356) basta loop por `rows` ativas comparando `cleaned["display_name"].casefold()` com cada `existing.display_name`. Raise ValidationError com mensagem contendo "Já existe um nome cadastrado" pra disparar uma branch nova em `target_validation_payload`.

### 2026-05-19 11:55 — Implementação do fix (3 edits)

**Contexto:** [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md) entrada 11:50, frente próxima
**Ação:** 3 edits aplicados:

1. **`web_app/db_admin.py:356-376`** — `create_secondary_target` ganhou loop de validação que rejeita duplicata de display_name (case-insensitive, normalizado via `normalize_text`) contra rows não-arquivadas. Mensagem: `"Já existe um nome cadastrado como '<label>'. Escolha um nome diferente ou edite o existente."`
2. **`web_app/app.py:151-180`** — `target_validation_payload` ganhou branch `elif "Já existe um nome cadastrado" in message` → `suggestion = "Escolha um nome diferente. Para mudar o existente, use Editar em vez de criar."`
3. **`tests/test_targets_jobs.py`** — teste `test_create_secondary_target_writes_sanitized_non_primary_target_atomically` foi ajustado pra usar "Marina Costa" (não-colidente) em vez de "Ana Maria" (que colidia com setup). Preserva intent original (testar strip do flag primary). Adicionados 2 testes novos:
   - `test_create_secondary_target_rejects_duplicate_display_name`: testa rejeição em 4 variações (exato, lowercase, com espaços, UPPER)
   - `test_create_secondary_target_allows_duplicate_against_archived_row`: confirma que arquivado não bloqueia

**Resultado:** todos os 3 arquivos editados via Edit tool sem erro.

### 2026-05-19 11:56 — Pytest local: 249 passed, 13 deselected (live)

**Contexto:** confirmar não-regressão antes de propor deploy
**Ação:** `.venv_playwright/bin/pytest -x --no-header -q -m "not live"` em `/home/otavio/Documents/vscode/clipping-project`
**Resultado:** `249 passed, 13 deselected in 14.44s`. Zero falhas. Inclui suite `test_admin_ui.py` (88 testes que mexem com mock de `create_secondary_target` — todos verdes).
**Interpretação:** fix é seguro de mergear. Cobertura nova (2 testes adicionais) cobre o comportamento que estava silenciosamente quebrado em prod.

### 2026-05-19 12:05 — Goal 2 backend logout investigado em prod

**Contexto:** [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md) — abrir Goal 2 (sessão controlada)
**Ação:** curl POST /api/logout em prod com cookie de admin + CSRF token + flag `-c` pra capturar Set-Cookie response
**Resultado:** HTTP 200, body `{"ok":true}`, cookie `clipping_admin` removido do jar de saída.
**Interpretação:** backend de logout funciona corretamente. Set-Cookie com expira-no-passado limpa a sessão. Problema do "logout não funciona" relatado pelo Otávio é exclusivamente UI: grep em `assets/clipping.js` e `index.html` retornou ZERO referências a `/api/logout`, "Sair", "logout". A UI nunca chama o endpoint. Bug é UI ausente, não backend quebrado.

### 2026-05-19 12:08 — Adicionado session-bar em index.html + CSS + JS handler

**Contexto:** fix Goal 2 mini-frente A (logout UI)
**Ação:** 3 edits + 2 cp (sync templates):

1. **`index.html`** (linhas 11-25): adicionado `<header class="session-bar" id="sessionBar" hidden>` com placeholder pra profile/role + botão "Sair". Posicionado como primeiro filho de `<main id="app">`, antes do `<section class="runner-shell">`.
2. **`assets/clipping.css`** (após linha 1743): adicionados estilos `.session-bar`, `.session-info`, `.session-role-tag`, `.session-logout`. Usam tokens existentes (`--surface`, `--line`, `--gold`, `--chip-bg`, `--chip-ink`, `--shadow`) pra ficar coerente. Layout flex right-aligned, gap 12px, padding/radius coerentes com `.admin-card`.
3. **`assets/clipping.js`** (após `apiPatch` na linha 55): adicionado IIFE `setupSessionBar()` que (a) lê `app.dataset.clippingSessionProfile` (já injetado pelo backend em `app.py:332-339`), (b) lê `initialSessionRole`, (c) preenche labels, (d) mostra a barra (`bar.hidden = false`), (e) wira o click do botão Sair: `await apiPost("/api/logout", {})` (reusa CSRF token do `ensureCsrfToken`) + `window.location.href = "/"`.
4. **`tools/pages_assets/clipping.js`** + **`tools/pages_assets/clipping.css`**: `cp` do `assets/` (essas duas cópias precisam estar em sync com `assets/` pelo `test_export_bundle_uses_current_dashboard_javascript`).

**Resultado:** todas as 5 edições aplicadas sem erro. Backend não tocado (já funciona).

### 2026-05-19 12:11 — Pytest pós-logout UI: 249 passed (verde)

**Contexto:** garantir que mudanças de UI não quebraram nada
**Ação:** `.venv_playwright/bin/pytest -x --no-header -q -m "not live"`
**Resultado:** `249 passed, 13 deselected in 13.60s`. Primeira tentativa falhou em `test_export_bundle_uses_current_dashboard_javascript` (template `tools/pages_assets/clipping.js` desincronizado) — corrigido via `cp`, segunda tentativa verde.
**Interpretação:** UI de logout não introduziu regressão. Não foi possível smoke manual (sem browser), mas o endpoint backend já foi confirmado em prod (entrada 12:05) e o JS chama o mesmo endpoint do curl bem-sucedido.

### 2026-05-19 12:15 — Adicionada validação de duplicata em update_secondary_target + 2 testes novos

**Contexto:** [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md) — mesma família do create fix (commit `ed53026`); regressão-zero exige fechar o mesmo gap no update.
**Ação:** Edit em `web_app/db_admin.py:379-400` adicionando loop análogo ao do create — varre `rows` pulando o índice da própria row sendo editada e arquivadas. Edit em `tests/test_targets_jobs.py` adicionando 2 testes:

1. `test_update_secondary_target_rejects_renaming_to_existing_display_name`: tenta renomear "Vorcaro" → "Shakira" (que existe ativo), esperando ValidationError. Verifica que a row original NÃO foi mutada no arquivo (write_targets_atomic não foi chamado).
2. `test_update_secondary_target_allows_rename_to_own_current_name`: confirma que rename idempotente (Shakira → Shakira, com novo keyword) passa — necessário pra UX de "salvar mudanças" sem mudar o display_name.

**Resultado:** pytest local `tests/test_targets_jobs.py tests/test_admin_ui.py`: 90 passed in 2.68s. Full suite: 251 passed in 13.44s. Zero regressão. Commit `f41a028`.
**Interpretação:** ambos caminhos de mutação (create e update) agora têm a mesma garantia semântica. Goal 5 partes "add primário/remover/transformar" continuam abertos (sem endpoint backend), mas o caminho secondary tem agora contrato consistente.

### 2026-05-19 12:25 — Refactor PRIMARY_TARGET_KEYS → PROTECTED_PRIMARY_KEYS + is_primary(row)

**Contexto:** [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md) entry 12:18 — pra fazer admin criar primários sem env var, o constante hardcoded precisava virar derivado-de-dados.
**Ação:** Edits em `web_app/db_admin.py`:

- Renomeada `PRIMARY_TARGET_KEYS` → `PROTECTED_PRIMARY_KEYS` (semantica nova: keys que ficam primary forçado, não que excluem outros)
- Adicionada helper `is_primary(row)` que retorna `key in PROTECTED_PRIMARY_KEYS or bool(row.get("primary"))`
- `sanitize_target` usa `is_primary(row)` em vez de `key in PRIMARY_TARGET_KEYS`
- `maybe_auto_archive_synthetic_targets` usa `is_primary(row)`
- `public_targets` agora computa `primaryKeys` lendo a flag `primary` de cada row + concatenando PROTECTED garantidos
- `primary_target_keys()` retorna união dinâmica (flag + protected)
- `locked_primary_keys()` continua retornando só PROTECTED

**Resultado:** primeira execução do pytest falhou em 2 testes (`test_create_secondary_target_writes_sanitized_non_primary_target_atomically` e `test_normalize_targets_file_forces_current_primary_contract`) — ambos encodavam o policy antigo "só PROTECTED viram primary". Ajustei:

- `test_create_secondary_target_writes_sanitized...`: setup de `ana_maria` mudou de `primary: True` pra `primary: False` (preserva o intent — testar strip do flag primary no create — sem disparar o novo behavior)
- `test_normalize_targets_file_forces_current_primary_contract` renomeado pra `..._forces_protected_keys_primary_and_honors_promoted_flag` com docstring explicando o contrato novo

**Interpretação:** refactor é breaking change semântico (file flag agora honrado pra promoted primaries), mas backward-compatible pra protected (Flávio e Pedro continuam sempre primary). Risco identificado no MAJOR 12:18 mitigado: dataset corrupto não desliga os 2 protegidos.

### 2026-05-19 12:30 — create_primary_target + endpoint POST /api/targets/primary

**Contexto:** Goal 5 — admin precisa criar primary
**Ação:**

- Adicionada função `create_primary_target` em `db_admin.py` (paralela a `create_secondary_target`, mesma dedup, mas `primary=True`, `className="primary"`)
- Adicionado wrapper `create_primary_target` em `app.py:113` (mesmo padrão do `create_secondary_target` wrapper)
- Adicionado endpoint `POST /api/targets/primary` em `app.py` com `require_admin + require_csrf` + handling de ValidationError
- 2 testes novos: `test_create_primary_target_writes_primary_row...` (happy + verifica primaryKeys), `..._rejects_duplicate_display_name_against_secondary` (dedup cross-tipo: criar primary "Shakira" com secondary "Shakira" existente → rejeitado)

**Resultado:** 253 passed, 13 deselected. Commit `4efe9f3`.

### 2026-05-19 12:35 — promote/demote endpoints + branches específicas de erro

**Contexto:** completar backend Goal 5 (4 operações: add primário ✓, add secundário ✓, promote, demote)
**Ação:**

- `promote_target_to_primary(key)` em `db_admin.py`: bloqueia se archived ou já primary; muta `primary=True, className="primary"`
- `demote_target_to_secondary(key)` em `db_admin.py`: bloqueia se `key in PROTECTED_PRIMARY_KEYS` (Flávio/Pedro intocáveis), se archived, ou se já secondary; muta inverso
- 2 endpoints novos em `app.py`: `POST /api/targets/{key}/promote` e `POST /api/targets/{key}/demote`, ambos `require_admin + require_csrf`
- `target_validation_payload` ganhou 3 branches: "ja e principal", "ja e secundario", "antes de promover/rebaixar" — cada um com suggestion específica
- 5 testes novos: happy promote, promote idempotente (rejeita), happy demote, demote bloqueado em protected, demote idempotente (rejeita)

**Resultado:** 258 passed, 13 deselected. Commit `fcb2126`.
**Interpretação:** backend de Goal 5 ESTÁ COMPLETO no plano funcional (4/4 operações). Faltam: (a) UI pra expor os 4 endpoints novos, (b) smoke em prod pós-deploy, (c) handling de side effects (mentions ligadas a um target demoted continuam ligadas — verificar live-results e export).

### 2026-05-19 12:45 — UI primary mgmt (managedTargetCard + handlers + funções) + bug grave de quoting

**Contexto:** [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md) entrada 12:35 — completar UI pros endpoints novos
**Ação:** 5 edits em `assets/clipping.js`:

1. Adicionado `PROTECTED_PRIMARY_KEYS = ["flavio_valle", "pedro_angelito"]` + helper `isProtectedPrimaryKey(key)`
2. `managedTargetCard` reescrito: badge `chip-primary` ("Principal") ou `chip-protected` ("Principal protegido"); protected mostram nota informativa sem botões; secondary tem botão "Promover a principal"; non-protected primary tem botão "Rebaixar para secundário"
3. `renderManageTargets` mudou filtro de `!target.primary && !target.archived` pra só `!target.archived` (lista agora inclui primários)
4. Adicionadas `promoteManagedTarget(key)` e `demoteManagedTarget(key)` (mesma estrutura de `archiveManagedTarget`)
5. App-level click handler ganhou blocos pra `data-target-promote` e `data-target-demote`

E em `assets/clipping.css`: adicionadas classes `.chip-primary`, `.chip-protected`, `.manage-target-card.is-primary`, `.manage-target-card-head` (flex layout pra badge à direita).

**Bug encontrado (delta crítico):** primeira tentativa de pytest pós-edit teve 4 falhas em `tests/test_pages_performance.py::TestFunctionalSanity` — timeout esperando `loadingState.hidden === true` (30s). Pytest backend = 254 passed, mas page-performance = 4 failed.

**Diagnóstico (via Playwright Function() bisect):** browser console reportava `Invalid or unexpected token` sem linha. Bisect linha por linha apontou pra linha 795 em `assets/clipping.js`:

```js
actions += '<button type="button" ... data-target-archive-start="' + key + '"' + disabled + disabledAttr + ">Arquivar</button>';
```

Final: `">Arquivar</button>';` — abre string com `"` (double quote), termina com `'` (single quote). Mismatch. Lexer não encontra o `"` de fechamento, segue até newline, lança "Invalid or unexpected token" sem indicar linha (porque o bundle é minificado-like em uma linha lógica). Linhas 791 e 793 (promote/demote) foram corretas — `";` no fim. Apenas 795 (archive) ficou com `';` quando eu reescrevi.

**Fix:** trocar `'` por `"` no final da string da linha 795. 1 char.
**Pytest pós-fix:** 258 passed, 13 deselected (incluindo TestFunctionalSanity e TestPagesBenchmark — flakiness desaparecida).
**Sync templates** via cp.
**Commit `b4df434`.**
**Interpretação:** UI primary mgmt completa. Mas a falha de quoting é a 2ª vez nessa sessão que rodar pytest cedo me salvou de bug invisível no diff (a 1ª foi a desincronização do tools/pages_assets em commit anterior). Lição: pytest é cheap, rodar SEMPRE após edits de JS estrutural.

---

### 2026-05-19 20:00 — Pós-compactação: restauração de docs perdidos no cherry-pick rebase

**Contexto:** [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md) entrada 12:50 — fim do dia anterior. O Otávio voltou, viu que o mantra não estava sendo seguido e perguntou "Que porra é essa". Diagnóstico: os 6 arquivos do loop (LONG_TERM_GOALS, MANTRA, work logs, session log, goals atingidos) **não estavam em HEAD**.
**Ação:** `git checkout e138350 -- "md documents/clipping-client-management-loop-2026-05-19/"`. O commit `e138350` é o último com a versão completa dos docs (incluindo a regra prod-push e a regra de responder próprias perguntas no mantra). Cherry-pick rebase anterior (188-commit divergence) só trouxe commits de backend; docs foram esquecidos.
**Resultado:** 6 arquivos restaurados, commit `fd4184b`, pushed.
**Interpretação:** padrão a vigiar — cherry-picks seletivos podem deixar docs/configs órfãos. Quando rebase parcial, listar explicitamente o que NÃO veio.

---

### 2026-05-19 20:00–20:18 — Goal 1: implementação backend + UI completa

**Contexto:** [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md) entrada 20:18 — Goal 1 (onboarding admin via UI).

**Ações (sequência):**

1. **`web_app/segmentation.py`**: add `ViewerProfileError`, regex `PROFILE_KEY_RE`, `set_viewer_profile()`, `archive_viewer_profile()`, `_write_profiles_file()`, `_ensure_writable_profiles()`. Mudou semântica de `viewer_profiles()`: file não-vazio **substitui** defaults em vez de mergir (sem isso, archive seria revertido).
2. **`web_app/auth.py`**: add `remove_viewer_password()` e `has_viewer_password()`.
3. **`web_app/storage_bridge.py`**: add `viewer_profiles.json` aos `RUNTIME_FILES`.
4. **`web_app/app.py`**: add `_viewer_profile_error_response()`, `_viewer_listing()`, `_validate_target_keys_for_viewer()`, e 4 endpoints (`GET/POST/PATCH /api/admin/viewers` + `POST /archive`). Import block atualizado.
5. **`index.html`**: nova `<details class="manage-viewers-box">` após `manageTargetsBox` + `<dialog class="password-dialog" id="editViewerDialog">` pra edição.
6. **`assets/clipping.js`**: nova IIFE `setupAdminViewers()` com loadTargetOptions/renderTargetOptions/loadViewers/renderViewers/openEditDialog + handlers de submit/click.
7. **`assets/clipping.css`**: classes `.manage-viewers-box`, `.viewer-card*`, `.viewer-target-*`, `.add-viewer-*`, `.chip-ok`, `.chip-warn`, `.chip-primary-mini`.
8. **`tools/pages_assets/`**: sync via `cp assets/clipping.js assets/clipping.css tools/pages_assets/`.
9. **`tests/test_admin_viewers.py`**: 12 testes novos cobrindo happy, invalid key, duplicate, unknown target, update, password change, archive, 404, admin-pseudo, viewer-cannot-access.
10. **`tests/test_admin_ui.py`**: 1 update no `test_storage_current_files_are_runtime_mutable_only` pra incluir `data/viewer_profiles.json` na lista esperada.

**Resultado:** 369/369 pytest passed. Commits `81bd1bd` (backend) e `d3af727` (UI). Pushed.

**Smoke prod 20:21–20:22:** 9/9 etapas verdes (script `/tmp/smoke_admin_viewers.sh`). Goal 1 migrou pra `GOALS_ATINGIDOS.md` em `8fbbd86`.

---

### 2026-05-19 20:25 — Fix do último buraco da família display_name duplicate

**Contexto:** [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md) entrada 11:50 já tinha fechado dedup em `create_secondary_target`; 12:15 fechou em `update_secondary_target`. Faltava `restore_secondary_target`.

**Cenário do bug (4 passos):**
1. `create "Shakira"` → `key=shakira`
2. `archive shakira` (passa dedup no create porque dedup ignora arquivados)
3. `create "Shakira"` → `key=shakira_2`, display="Shakira" ativo
4. `restore shakira` → **dois rows ativos** com display "Shakira"

**Ação:** `restore_secondary_target` agora itera outras rows ativas (`other_idx != index`, `archived=False`), compara display_name normalizado+casefold, e levanta `ValidationError` se conflitar. `target_validation_payload` ganhou branch pra mensagem "Já existe um nome ativo cadastrado" → suggestion "Arquive ou renomeie o nome ativo conflitante antes de restaurar este".

**Testes adicionados (2):** block-on-conflict (verifica que archived stays archived) + allow-when-no-conflict.

**Pytest:** 87/87 nas suítes tocadas. Commit `f4b42a2`. Deploy disparado.

---
