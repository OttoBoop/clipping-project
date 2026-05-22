# MANTRA — Loop CCM (Clipping Client Management)

**Companheiros:** [LONG_TERM_GOALS.md](LONG_TERM_GOALS.md) · [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md) · [WORK_LOG_DETALHADO.md](WORK_LOG_DETALHADO.md) · [GOALS_ATINGIDOS.md](GOALS_ATINGIDOS.md)

**REGRA-MÃE:** *"Não apareça só na UI, mas conectado a todos os sistemas secundários e primários."*

---

## 9 Regras (releitura silenciosa + repetição verbatim no output de cada turno)

1. **NÃO PARO** até Otávio Oliveira Bopp mandar parar OU créditos Anthropic acabarem. Fechou frente, abro a próxima.
2. **TRABALHO EM PRODUÇÃO** — chunk verde → push + Render deploy hook. Sem pedir autorização.
3. **RESPONDO MINHAS PRÓPRIAS PERGUNTAS** — táticas (layout, ordem, tradeoff local) são minhas. Pergunto só em ambiguidade estratégica genuína.
4. **NÃO EXISTE BARREIRA QUE EXIJA AJUDA DO OTÁVIO.** Playwright, WebFetch, WebSearch, Bash, pip. "Depende de você ver" = desisto disfarçado.
5. **LEIO E REPITO O MANTRA VERBATIM** após cada output substantivo. Repetição é a forcing function autoregressiva — sem ela, drift.
6. **TERMINO COM "Agora vou X" — E EXECUTO.** Última linha do output é ação imediata concreta, e a próxima ação do turno é fazer X.
7. **NUNCA COMMIT LOCAL.** Commit + push são uma operação atômica. Quota Render esgotada? Push mesmo assim — commit fica no GitHub pro próximo build.
8. **ANTES DE TOCAR AUTH/SCOPE/PERMISSÃO:** `git log --all -- <arquivo>` + reler AskUserQuestion answers em `AUDITORIA_PROMPTS_*.md`. "Destruir/tiraram/removeram" do Otávio é literal — existe commit de remoção.
9. **AUTO-AUDITORIA PERIÓDICA.** A cada 10 outputs substantivos OU antes de marcar Goal atingido: `python3 tools/auditar_prompts.py --since 2026-05-19` + contrastar contra `LONG_TERM_GOALS.md`. Pedido literal não-coberto = abrir Goal ou WORK_LOG entry. Otávio NÃO deve precisar pedir "leia todos os prompts" novamente.

10. **SMOKE PLAYWRIGHT EM PROD NUNCA RODA SOZINHO `goal2_change_password`.** Esse smoke muta a senha admin do file. Se crashar entre fase 2 (mudar senha) e `goal2_revert_password` (restaurar), admin trava. Em 2026-05-22 isso causou 1h+ de lockout que precisou de endpoint temporário de recovery via env var. Recovery: `~/Documents/clipping-project senhas.md` doc "Recovery: env var ainda tem a 48-hex original" + commit `16e8be3` (smoke grava throwaway em `/tmp/clipping_smoke_throwaway.txt`). Antes de rodar smoke completo em prod: validar que o sistema está estável (sem job massivo em curso, sem OOM no histórico recente).

---

## Goals do loop (atualizar quando migrar)

1. ✅ Onboarding admin via UI (2026-05-19)
2. ✅ Sessão controlada — logout + change-password (2026-05-19)
3. ✅ Senhas simples e comunicáveis (2026-05-19)
4. 🔄 Regressão-zero — meta contínua, nunca migra
5. ✅ Per-client custom targets — fase 1 (admin via simulação) + fase 2 (viewer-autenticado) (2026-05-20)
6. ✅ Visualização de registros de atividade (2026-05-22)

**Status:** 5 atingidos + Goal 4 contínuo. Próxima frente: abrir novas (auto-disparo via Regra 9) OU aprofundar Goal 4 (mais smokes proativos, áreas não testadas).

---

## Migração de Goal atingido

Quando critério visual em prod cumprido: (a) entrada em [GOALS_ATINGIDOS.md](GOALS_ATINGIDOS.md) com data + critério + evidência (curl/screenshot), (b) marcar ✅ na lista acima, (c) registrar no [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md).
