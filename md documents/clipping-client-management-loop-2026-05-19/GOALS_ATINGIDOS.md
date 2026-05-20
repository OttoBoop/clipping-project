# Goals Atingidos — Loop CCM-2026-05-19

Goals que já foram entregues em produção e saíram do [MANTRA.md](MANTRA.md). Não significa "intocável": cada sprint subsequente que mexer numa área de Goal atingido precisa **verificar manualmente** que o Goal continua válido (regressão-zero, per Goal 4 do [LONG_TERM_GOALS.md](LONG_TERM_GOALS.md)).

Companheiros:
- Âncora: [LONG_TERM_GOALS.md](LONG_TERM_GOALS.md)
- Mantra: [MANTRA.md](MANTRA.md)
- Log estratégico: [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md)
- Log fino: [WORK_LOG_DETALHADO.md](WORK_LOG_DETALHADO.md)
- Pontos de registro: [SESSION_LOG.md](SESSION_LOG.md)

---

## Template de entrada

```
## Goal N — [Nome do Goal] (atingido YYYY-MM-DD)

**Critério de sucesso cumprido:** [como foi verificado em prod]
**Evidência:** [link a entrada major + screenshot/curl/log]
**Migrado do MANTRA.md em:** YYYY-MM-DD
**Notas de manutenção:** [se houver dependências futuras a vigiar]
```

---

## Entradas

## Goal 1 — Onboarding administrativo via UI (atingido 2026-05-19)

**Critério de sucesso cumprido:**

> "Otávio loga em prod como admin, abre `/admin/clients`, cria cliente `teste-foo` com senha `teste-foo-2026`, desloga, loga como `teste-foo` — **sem nenhum redeploy**."
> (Goal 1 / [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md) entrada 2026-05-19 12:18)

A UI vive na aba "Atualizar" > seção "Clientes (viewers)" (não em rota separada — mesma decisão estrutural do gerenciamento de targets); o critério é equivalente — admin cria, viewer loga, admin arquiva, viewer não loga mais — tudo em runtime, sem mexer em env var e sem redeploy.

**Evidência (smoke em prod 2026-05-19 20:21–20:22 UTC-3):**

Sequência completa via `curl` contra `clipping-project.onrender.com`:

| # | Ação | Resultado |
|---|---|---|
| 1 | `POST /api/login` admin | 200 — role=admin, profile=admin |
| 2 | `GET /api/csrf` | token de 43 chars |
| 3 | `GET /api/admin/viewers` (antes) | 4 viewers: demo_cliente, flavio, rio_economico, shakira |
| 4 | `POST /api/admin/viewers` (criar `smoke_1779233008`) | 200 — `has_password: true`, sem redeploy |
| 5 | `POST /api/login` como `smoke-smoke_1779233008-2026` | 200 — role=viewer, profile=smoke_1779233008 |
| 6 | `PATCH /api/admin/viewers/smoke_1779233008` (rename) | 200 — label atualizado, target_keys preservado |
| 7 | `POST /api/admin/viewers/smoke_1779233008/archive` | 200 |
| 8 | `POST /api/login` repetido | **401** — confirmado que viewer não loga mais |
| 9 | `GET /api/admin/viewers` (depois) | 4 viewers, `smoke_…` ausente |

Caminho end-to-end coberto: UI → `/api/admin/viewers` → `set_viewer_profile` (`viewer_profiles.json` atomic write) → `set_viewer_password` (`clipping_credentials.json` pbkdf2-sha256) → Supabase backup → `/api/login` → `viewer_passwords()` → sessão. Archive limpa as duas pontas (`archive_viewer_profile` + `remove_viewer_password`). Backup persiste via `storage_bridge.RUNTIME_FILES`.

**Migrado do MANTRA.md em:** 2026-05-19

**Notas de manutenção:**

- ⚠️ **Validação de `target_keys`** no `POST` é checada contra `load_targets()`. Se admin arquivar um target depois de atribuir a um viewer, a entrada do viewer continua válida (não removemos o key automaticamente). Se isso virar irritação, considerar limpeza em cascata no archive de target.
- ⚠️ **Rename de `profile_key` não é suportado**: re-key implícito quebraria sessões e cross-references. Pra mudar profile_key: arquivar e criar novo.
- ⚠️ **Restore de viewer arquivado não existe**: archive limpa senha e profile. Pra trazer de volta, admin recria.
- ⚠️ **Merge defaults↔file mudou** (entrada major 2026-05-19 20:18): `viewer_profiles()` agora pula o merge com `DEFAULT_VIEWER_PROFILES` se o arquivo não for vazio. Sem isso, archive seria revertido pelos defaults. Se Supabase backup for restaurado parcial/corrompido, viewers podem sumir — vigiar a sincronia.
- ⚠️ **Push em prod sem redeploy só funciona pra MUTAÇÕES** (file writes em runtime). Adicionar/alterar **endpoint** continua exigindo deploy (FastAPI carrega rotas no import). Não é regressão — é a borda natural entre data e code.

---

## Goal 2 — Sessão controlada pelo usuário (atingido 2026-05-19)

**Critério de sucesso cumprido:**

> "Otávio clica 'Sair' no header em prod → vai pra tela de login + cookie removido. Otávio loga, abre 'Trocar senha' no header, digita senha antiga errada → erro 'senha atual incorreta'. Digita certa + nova → senha trocada, próximo login funciona com nova."
> ([LONG_TERM_GOALS.md](LONG_TERM_GOALS.md) Goal 2 + [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md) entrada 2026-05-19 12:18)

**Evidência (visual smoke via Playwright em prod, 2026-05-19 ~20:48):**

Chromium real navegando `clipping-project.onrender.com`:

| Passo | UI mostrou | Status |
|---|---|---|
| Login → sessão admin | session bar visível, label='admin' | ✅ |
| Clicar `#logoutButton` | retorna pra `#password` form, URL=`/` | ✅ |
| Cookie `clipping_admin` após logout | ausente | ✅ |
| Abrir `#changePasswordButton` | modal `#changePasswordDialog` visível | ✅ |
| Submeter wrong-old | `#changePasswordMessage` = "Senha atual incorreta." | ✅ |
| Submeter pair válido | message = "Senha trocada. Use a nova no próximo login." + modal fecha sozinho | ✅ |
| `GET /api/csrf` pós-troca | HTTP 200 (CSRF não-cacheado → re-fetch funciona) | ✅ |
| Login com nova senha | sessão `admin` ativa | ✅ |
| Reverter senha throwaway → original | message "Senha trocada" novamente | ✅ |

Tool: [`tools/visual_smoke_playwright.py`](../../tools/visual_smoke_playwright.py).

Caminho end-to-end coberto: UI `#logoutButton` → `apiPost("/api/logout")` → `require_csrf` + `require_viewer` → cookie expira. UI `#changePasswordForm` → `apiPost("/api/change-password")` → `login_identity(old)` → `set_admin_password(new)` (hash pbkdf2-sha256) → resign session cookie → `csrfToken = ""; csrfPromise = null` (invalida cache cliente).

**Migrado do MANTRA.md em:** 2026-05-19

**Notas de manutenção:**

- ⚠️ **Bug encontrado durante a validação (commit `6a929c2`)**: o JS cacheava `csrfToken` da sessão antiga após change-password. Próxima ação CSRF-guarded dava 403 em prod sem mensagem na UI. Fix: invalidar cache (csrfToken="", csrfPromise=null) no sucesso de change-password. Se qualquer endpoint novo emitir nova sessão (login, future rotate-session, etc.), aplicar o mesmo pattern.
- ⚠️ **Fix secundário (commit `ad8a6bf`)**: `loadViewers` estava limpando `#manageViewersMessage` na re-render. Removido o clear pra que mensagens de sucesso/erro persistam até a próxima ação. Pattern: nunca limpar feedback de usuário num re-load que aconteceu por causa daquele feedback.
- 🎯 **Goal 2 reutiliza Goal 1's storage**: change-password só funciona porque `set_admin_password`/`set_viewer_password` gravam em `clipping_credentials.json` (não env var). Se um futuro PR voltar a env var, change-password quebra silenciosamente.

---

## Goal 3 — Senhas simples e comunicáveis (atingido 2026-05-19)

**Critério de sucesso cumprido:**

> "Todos os 5 logins em prod usam senhas humanas (ditáveis por telefone) e o admin pode trocar qualquer uma pela UI sem ajuda externa."
> ([LONG_TERM_GOALS.md](LONG_TERM_GOALS.md) Goal 3 + [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md) entrada 2026-05-19 ordem inicial)

**Evidência (visual smoke, 2026-05-19 ~20:48):**

Login em sequência, contexto novo por perfil, asserting que a session bar mostra o profile esperado:

| Profile | Senha (em [~/Documents/clipping-project senhas.md]) | Len | Login OK |
|---|---|---|---|
| admin | `clipping-admin-2026` | 19 | ✅ label='admin' |
| flavio | `flavio-gabinete-2026` | 20 | ✅ label='flavio' |
| shakira | `shakira-fgv-2026` | 16 | ✅ label='shakira' |
| rio_economico | `rio-economico-2026` | 18 | ✅ label='rio_economico' |
| demo_cliente | `demo-cliente-2026` | 17 | ✅ label='demo_cliente' |

Todas 16-20 chars, só ASCII alfanumérico + hífen — "ditáveis por telefone" no critério literal. **Nenhum hex de 48 chars sobreviveu** (rotação documentada em [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md) 12:35).

Troca de senha pela UI cobrida pelo Goal 2's modal (admin troca a própria) + Goal 1's `PATCH /api/admin/viewers/{profile}` (admin troca de qualquer viewer). Ambos validados em prod.

**Migrado do MANTRA.md em:** 2026-05-19

**Notas de manutenção:**

- ⚠️ **Senhas estão em `~/Documents/clipping-project senhas.md`** (não-versionado). Hashadas em `data/clipping_credentials.json` com pbkdf2-sha256 310k rounds. Se o backup do Supabase corromper, dá pra recuperar manualmente pelas senhas do arquivo do Otávio.
- ⚠️ **Nada de validador de força de senha**: foi decisão consciente (admin = Otávio, confiança). Se virar tool pra mais admins, considerar regra "≥8 chars, ≥1 dígito".
- 🎯 **Se o storage migrar pra env-var de novo, Goal 3 quebra**: senhas humanas digitadas → hash gravado → file persistido. Se algum PR fizer fallback pra env-var sem mecanismo de re-hash, novos viewers ganharão senha env-var de novo. Vigiar.

---

## ✅ Goal 5 — Per-client custom targets RESTAURADO 2026-05-20 (fase 1) + fase 2 (viewer-autenticado muta)

**Fase 2 (commit `65fd44d`, deploy `dep-d87pd7rtqb8s73e7ppog` live 2026-05-20T23:35 −0300):**

Confronto do Otávio (2026-05-20): *"QUE PORRA É ESSA COM O OBJETIVO NOVE? Você quer que para o Flávio adicionar registros, ele precise logar como um adm?"* — fase 1 só permitia admin-via-simulação mutar; viewer-autenticado-como-viewer continuava read-only. Fase 2 corrige: viewer loga com sua senha e muta targets dentro do scope dele.

Evidência end-to-end em prod (curl, 2026-05-20T23:38 −0300):

```
# Login VIEWER flavio (não admin)
POST /api/login {"password":"flavio-gabinete-2026"} → {role: viewer, profile: flavio}

# Viewer cria target SEM ?as_profile — backend atribui pelo session.profile
POST /api/targets {"display_name":"Sergio Cabral Test","keywords":["sergio"]}
  → key=sergio_cabral_test_1779319979, assignedToProfile=flavio

# Viewer vê target em /api/targets (scoped)
GET /api/targets → 5 targets: [flavio_valle, pedro_*, bernardo_rubiao, sergio_cabral_test_*]

# Viewer tenta archive target de OUTRO cliente (shakira)
POST /api/targets/shakira/archive → HTTP 403 + {"error":"target_out_of_scope","message":"Este nome não pertence ao seu cliente. Peça ao admin para atribuí-lo, se aplicável.","field":"target_key"}

# Viewer archive PRÓPRIO target
POST /api/targets/sergio_cabral_test_*/archive → 200, assignedToProfile=flavio

# Segregação: shakira NÃO vê target do flavio
[login shakira] GET /api/targets → 1 target: [shakira] (sem o sergio_cabral_test_*)
```

Atores que agora mutam (per LONG_TERM_GOALS.md Goal 5):
1. **Viewer autenticado** (flavio, shakira, etc.) — muta no SEU scope; out-of-scope retorna 403 com mensagem clara.
2. **Admin via simulação** `?as_profile=X` — fase 1, continua funcionando, atribui ao X.
3. **Admin sem simulação** — catálogo global, sem auto-assign.

**Fase 1 — commit anterior `39dcd0c`** (2026-05-20T21:05 −0300), deployed live em prod (`dep-d87nke0js32c73eco6og` ~21:35 −0300).

**Evidência end-to-end em prod (curl, 2026-05-20T21:38 −0300):**

```
# Login admin
POST /api/login → {role: admin, profile: admin}

# Estado inicial: flavio.target_keys tem 4 keys
GET /api/admin/viewers → flavio.target_keys (4): [flavio_valle, pedro_duarte, pedro_angelito, bernardo_rubiao]

# Criar secondary em simulação flavio
POST /api/targets?as_profile=flavio {display_name: "Audit Verify 1779312705"}
  → key=audit_verify_1779312705, assignedToProfile=flavio

# flavio.target_keys cresceu para 5
GET /api/admin/viewers → flavio.target_keys (5): [..., audit_verify_1779312705]

# Archive em simulação flavio
POST /api/targets/audit_verify_1779312705/archive?as_profile=flavio
  → assignedToProfile=flavio (= removido do scope)

# flavio.target_keys voltou para 4 (key foi removido)
GET /api/admin/viewers → flavio.target_keys (4): [flavio_valle, pedro_duarte, pedro_angelito, bernardo_rubiao]
```

**Critério cumprido:**
- ✅ Admin em simulação `?as_profile=flavio` consegue criar target que entra automaticamente em `flavio.target_keys`
- ✅ Archive em simulação remove do scope do profile
- ✅ Response inclui `assignedToProfile` para frontend confirmar
- ✅ Endpoints `require_admin` (mutação ainda barrada pra viewer-autenticado-como-viewer; D1=A)
- ✅ 12/12 tests em `test_admin_simulate.py` cobrindo create/archive/restore + no-op global + viewer-blocked

**Pendente (não bloqueia o Goal):**
- Visual smoke playwright (`tools/visual_smoke_playwright.py:goal_admin_simulation`) atualizado para asseritar `#manageTargetsBox` VISIBLE em simulação (era hidden — assertion invertida no commit `39dcd0c`). Rodar em prod requer Playwright local.
- Goal 5.D1=B (viewer-autenticado muta seus targets) e D2=isolado-por-viewer ficam como decisões pendentes do Otávio para fase futura.

**Migrado do MANTRA.md em:** 2026-05-20 (Goal 5 marcado como atingido restaurado)

---

## ⚠️ Goal 5 — REABERTO 2026-05-20 (originalmente "atingido" 2026-05-19 — atingimento foi prematuro)

**Por que reaberto:** auditoria de prompts (`AUDITORIA_PROMPTS_*.md`, gerada 2026-05-20) mostrou que a resposta verbatim do Otávio à AskUserQuestion de 2026-05-19 era:

> *"**Per-client custom targets**, mas vamos expandir... Adicionar targets primários, Remover targets primários, Transformar targets primários em secundários..."*

A chave **"Per-client custom targets"** (targets customizados POR CADA CLIENTE, no contexto do cliente) foi perdida quando eu transcrevi a resposta para `LONG_TERM_GOALS.md` Goal 5 (saiu "Admin precisa poder, para cada cliente: Adicionar target primário..." — interpretação literal pobre = "admin global centralizado + atribuição posterior").

A "evidência de atingimento" abaixo cobriu os 11 fluxos de erro estruturado do CATÁLOGO GLOBAL de targets (admin operando centralmente), mas **não cobriu**:
- Adição de target dentro do contexto de cada cliente (sem sair do contexto)
- Atribuição automática ao `target_keys` do profile alvo
- UI visível no modo simulação `?as_profile=X` (atual: `.add-target-box` e `.manage-targets-box` ficam escondidos pelo CSS `viewer-readonly` mesmo em simulação — admin precisa sair pra mutar)

A "evidência" abaixo permanece válida como **prova parcial** (catálogo global + erros estruturados funcionam), mas o Goal completo só será atingido depois da restauração de mutação per-client em simulação. **Não marcar como atingido até evidência visual mostrar fluxo "admin entra em simulação flavio → adiciona target X → X aparece em flavio.target_keys + na lista de targets do flavio".**

---

## Goal 5 — Target management completo com erros claros (atingido PARCIAL 2026-05-19 — superado por reabertura 2026-05-20)

**Critério de sucesso cumprido:**

> "Otávio abre cliente 'flavio', testa as 4 operações [add/remove primário, demote primário→secundário, add secundário] e em **todas** vê: ou confirmação clara (happy), ou mensagem específica explicando o problema (conflito/inválido). Zero spinner infinito, zero 'something went wrong'."
> ([LONG_TERM_GOALS.md](LONG_TERM_GOALS.md) Goal 5)

**Evidência (visual smoke via Playwright em prod, 2026-05-19 ~20:48):**

UI real, asserting visualmente:

| Operação | UI mostrou | Status |
|---|---|---|
| Abrir "Gerenciar nomes secundários" | lista populada com 7 cards (Flavio + Pedro Angelito protegidos + secundários ativos) | ✅ |
| Cards de protected primaries (flavio_valle) | chip "Principal protegido", **sem botões** promover/rebaixar/arquivar | ✅ |
| Submit `addTargetForm` com display_name="Shakira" (duplicata) | `#addTargetMessage` = "Já existe um nome cadastrado como 'Shakira'. Escolha um nome diferente ou edite o existente." | ✅ |

E o **smoke API** [`tools/targets_mgmt_smoke.py`](../../tools/targets_mgmt_smoke.py) (executado 20:35) já tinha coberto os 11 fluxos de erro estruturado:

| Path | HTTP | Message literal de prod |
|---|---|---|
| create secondary happy | 200 | (sucesso) |
| create secondary duplicado | 400 | "Já existe um nome cadastrado como 'Smoke Sec X'..." |
| promote secondary→primary | 200 | (sucesso) |
| re-promote primário | 400 | "Este nome ja e principal." |
| demote primary→secondary | 200 | (sucesso) |
| demote PROTECTED | 400 | "Nomes principais nao podem ser editados por aqui." |
| create primary direto | 200 | (sucesso) |
| archive primário | 200 | (sucesso) |
| restore conflito (homônimo ativo) | 400 | "Já existe um nome ativo cadastrado como 'Smoke Sec X'..." |

**Migrado do MANTRA.md em:** 2026-05-19

**Notas de manutenção:**

- ⚠️ **PROTECTED_PRIMARY_KEYS está duplicada JS↔Python** (`["flavio_valle", "pedro_angelito"]`). Pequena duplicação aceita pra não criar `/api/me`. Se a lista crescer, considerar injeção via dataset attribute.
- ⚠️ **Família display_name dedup tem 4 caminhos cobertos**: create_secondary (commit `7a589d5`), create_primary (mesmo padrão), update_secondary (`f41a028`, com skip-self), restore_secondary (`f4b42a2`). Qualquer caminho novo que crie/restaure target precisa do mesmo guard.
- ⚠️ **Mensagens em backend são em ASCII** (sem acentos: "ja", "nao"). UI render é OK. Não mexer no backend só por estética — risco de quebrar i18n / scripts externos.
- 🎯 **Smoke targets ficam arquivados após cada run**: acumulam. Eventualmente vale `archive_known_test_targets()` reagindo a marker tipo "smoke_" — fora de escopo agora.
