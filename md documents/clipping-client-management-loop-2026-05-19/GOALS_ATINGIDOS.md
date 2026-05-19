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
