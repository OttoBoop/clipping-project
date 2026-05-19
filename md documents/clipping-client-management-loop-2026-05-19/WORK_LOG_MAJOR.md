# Work Log — Major (Estratégico)

**Created:** 2026-05-19
**Loop:** Clipping Client Management (`md documents/clipping-client-management-loop-2026-05-19/`)
**Anchor:** [`LONG_TERM_GOALS.md`](LONG_TERM_GOALS.md)
**Mantra:** [`MANTRA.md`](MANTRA.md) · repetido a cada 5 respostas substantivas
**Companion doc (sub-ações detalhadas):** [`WORK_LOG_DETALHADO.md`](WORK_LOG_DETALHADO.md)
**Pontos de registro (review cronológico):** [`SESSION_LOG.md`](SESSION_LOG.md)
**Goals já entregues:** [`GOALS_ATINGIDOS.md`](GOALS_ATINGIDOS.md)

---

## Propósito

Registrar **decisões estratégicas**: que método já tentei, qual vou tentar agora, e por quê o anterior falhou (se falhou). Este log é o que IAs futuras leem **primeiro** ao retomar o loop — pra não repetir abordagens descartadas.

**Não vai aqui:** comandos, diffs, output de testes, decisões pequenas. Tudo isso é do `WORK_LOG_DETALHADO.md`.

---

## Quando adicionar uma entrada

- Ao começar um novo sprint que ataca um Goal
- Ao mudar de método dentro de um sprint ("tentei abordagem A, não rolou, vou tentar B")
- Ao concluir um sprint (resultado + se o Goal foi atingido em produção)

---

## Template de entrada

```markdown
## YYYY-MM-DD — [Título curto da ação estratégica]

**Goal endereçado:** Goal N (de LONG_TERM_GOALS.md)
**Método escolhido:** [1-2 frases descrevendo a abordagem]
**Por que esse método:** [racional curto — por que esse e não outro]
**Métodos já descartados:** [links a entradas anteriores se houver, ou "n/a"]
**Critério de sucesso:** [observável pelo Otávio em produção — não só pytest]
**Próxima sub-ação concreta:** aponta pra primeira entrada em `WORK_LOG_DETALHADO.md`
```

---

## Disciplina de leitura (obrigatória pra IAs)

- **Antes de propor método novo:** ler este arquivo inteiro pra checar se já foi tentado
- **Se método é o mesmo de antes:** marcar explicitamente `**retomando método X (entrada YYYY-MM-DD)** porque [novo contexto]`
- **Nunca** repetir método sem justificativa nova explícita

---

## Entradas

---

## 2026-05-19 — Ordem proposta entre os 5 Goals

**Goal endereçado:** meta (afeta todos)
**Método escolhido:** atacar os Goals nessa ordem: **4 → 1 → 3 → 2 → 5**.
**Por que esse método:**

- **Goal 4 (regressão-zero) primeiro** porque é meta-disciplina: sem baseline do que funciona/quebra hoje, qualquer fix pode ser regressão silenciosa. O Otávio relatou que "adicionar target gera erros" — precisamos catalogar onde, antes de mexer em mais coisa.
- **Goal 1 (onboarding admin via UI) segundo** porque destrava a fonte-de-verdade pra Goals 2 e 3. Hoje senhas vivem em env var; Goals 2 (trocar senha) e 3 (senha simples digitada por admin) precisam de storage mutável em tempo real.
- **Goal 3 (senhas simples) terceiro** — quase grátis depois do Goal 1 (mesmo form, mesmo storage). Resolve o pain WhatsApp.
- **Goal 2 (logout + trocar senha) quarto** — endpoint de logout já existe ([`web_app/app.py:196`](../../web_app/app.py)); falta UI e endpoint de change-password (que depende do storage do Goal 1).
- **Goal 5 (target management completo) por último** porque é o maior e mais delicado, e se beneficia de tudo acima (regressão sob controle, admin operacional, senhas previsíveis pra testar viewer).

**Métodos já descartados:** n/a (primeira entrada).
**Critério de sucesso:** Otávio aprovar essa ordem, OU propor outra; nesse caso eu reabro essa entrada.
**Próxima sub-ação concreta:** começar Sprint 1 = Goal 4 (regression baseline).

---

## 2026-05-19 — Sprint 1: Goal 4 — Baseline de regressão

**Goal endereçado:** Goal 4 (Regressão-zero entre features)
**Método escolhido:** rodar a UI atual em produção (clipping-project.onrender.com) com cada uma das 5 credenciais (admin + 4 viewers), exercitar manualmente os fluxos críticos (login, listar artigos, filtros, adicionar target, exportar) e gravar tudo num doc `REGRESSION_BASELINE_2026-05-19.md` dentro deste loop. Salvar screenshots dos erros que aparecerem.
**Por que esse método:**

- Pytest local passa (per loop anterior, "75 passed in 2.22s") mas Otávio relata erros em prod. Logo, baseline tem que ser **em prod**, não em pytest.
- Manual antes de Playwright/automação porque o objetivo é catalogar o que existe — automação vem depois quando soubermos o que é estável.
- Catalogar é barato e destrava decisões dos próximos sprints (saber se um fix bate em regressão exige conhecer o estado pre-fix).

**Métodos já descartados:**

- ❌ Playwright E2E completo agora — esforço alto antes mesmo de saber o que precisa proteger.
- ❌ Confiar só em pytest — passa mas não pega o bug de prod que o Otávio viu.
- ❌ Esperar bug aparecer no uso pra reagir — perde rastreabilidade entre sprints.

**Critério de sucesso:** existir um `REGRESSION_BASELINE_2026-05-19.md` listando, por área (login, listar, filtro, add-target, export):

- O que funciona
- O que quebra (com mensagem de erro literal + repro steps)
- Status: "esperado quebrado" vs "regressão a tratar"

E cada sprint subsequente abrir entrada major dizendo "baseline mantida" ou "baseline mudou em X".

**Próxima sub-ação concreta:** primeira entrada em `WORK_LOG_DETALHADO.md` = `curl /api/login` com cada senha + abrir browser e exercitar admin flow.

---

## 2026-05-19 — Sprint 2: Goal 1 — Onboarding admin via UI

**Goal endereçado:** Goal 1 (Onboarding administrativo via UI)
**Método escolhido:**

1. Mudar a fonte da verdade de credenciais: de env var `CLIPPING_VIEWER_PASSWORDS` para arquivo `data/viewer_credentials.json` (gitignored, persistido via mecanismo de Supabase backup que já existe pro `clipping.db`).
2. Adicionar `web_app/admin_clients.py` com endpoints: `GET /api/admin/clients` (listar), `POST /api/admin/clients` (criar), `PATCH /api/admin/clients/{profile}` (editar — inclui senha), `POST /api/admin/clients/{profile}/archive`.
3. Adicionar página `/admin/clients` na UI admin com tabela + form de criação.
4. Adaptar `web_app/auth.py:viewer_passwords()` pra ler do arquivo (mantendo fallback pro env var por 1 release como contingência).

**Por que esse método:**

- **Arquivo gitignored em vez de SQLite**: stage inicial, simples, sem migration. Já tem mecanismo de backup pro `clipping.db` no Supabase — reusar.
- **Manter fallback pro env var** durante 1 release: evita lock-out se algo der errado no arquivo (regressão-zero per Goal 4).
- **Endpoints separados em `admin_clients.py`** em vez de adicionar a `app.py`: facilita auditoria e teste isolado.

**Métodos já descartados:**

- ❌ Continuar com env var + UI que dispara redeploy via Render API — quebra o ciclo do produto.
- ❌ SQLite com migration — overkill pra 4-10 clientes na fase atual.
- ❌ Endpoint admin que chama Render API a cada mudança — muito acoplamento, depende de credencial pessoal.

**Critério de sucesso (observável em prod):** Otávio loga em prod como admin, abre `/admin/clients`, cria cliente "teste-foo" com senha "teste-foo-2026", desloga, loga como `teste-foo` — **sem nenhum redeploy**.

**Próxima sub-ação concreta:** depois do Sprint 1 fechar baseline, primeira entrada detalhada = ler `data/viewer_profiles.json` atual + decidir schema do `viewer_credentials.json`.

---

## 2026-05-19 — Sprint 3: Goal 3 — Senhas simples

**Goal endereçado:** Goal 3 (Senhas simples e comunicáveis)
**Método escolhido:** aproveitar o form de criação/edição do Sprint 2 — admin **digita** a senha em texto puro ao criar/editar cliente. Sem auto-geração, sem regras de força. Migração: depois do Sprint 2 estar em prod, Otávio abre cada cliente existente e troca a senha de 48-hex pra senha humana, manual.
**Por que esse método:**

- Otávio disse explicitamente "admin define ao criar".
- Migração manual de 4 clientes (1 admin + 4 viewers = 5 senhas) é mais rápido que script de migração + risco de bug.
- Não validar força de senha agora porque o admin é Otávio (não público) — confia.

**Métodos já descartados:**

- ❌ Diceware (palavras memoráveis tipo `apple-house-table`) — interessante mas adiciona complexidade sem usuário ainda pedindo.
- ❌ Regras de força (8 chars, símbolo) — exclui senhas humanas tipo "flavio2026" e atrapalha UX.
- ❌ Senhas geradas pelo sistema (mesmo que mais curtas, tipo `xkcd-style`) — Otávio quer escolher.

**Critério de sucesso:** todos os 5 logins em prod usam senhas humanas (ditáveis por telefone) e o admin pode trocar qualquer uma pela UI sem ajuda externa.

**Próxima sub-ação concreta:** integrar no form do Sprint 2 (não vira sprint separado de código, mas vira entrada major separada pra rastrear a migração das 5 senhas existentes).

---

## 2026-05-19 — Sprint 4: Goal 2 — Logout + trocar senha

**Goal endereçado:** Goal 2 (Sessão controlada pelo próprio usuário)
**Método escolhido:**

1. **Logout:** auditar o `POST /api/logout` existente em prod. Se backend funciona, adicionar botão "Sair" visível no header (admin e viewer). Se backend não funciona, corrigir + adicionar UI.
2. **Trocar senha:** novo endpoint `POST /api/change-password` (precisa `require_viewer`) que recebe `{old_password, new_password}`, valida old, atualiza credenciais (storage do Sprint 2), assina nova sessão. UI: modal/página `/me/password` acessível pelo header.

**Por que esse método:**

- Backend de logout já existe — não duplicar. Investigar por que o user diz que não funciona (pode ser ausência de UI, ou cookie não limpa direito).
- Trocar senha usa o storage do Sprint 2 — sem isso, mudaria env var (que requer redeploy = violação do Goal 1).
- `require_viewer` (não `require_admin`) pra change-password porque cada viewer troca a própria.

**Métodos já descartados:**

- ❌ Reset por email — sem infra de email, fora de escopo do estágio atual.
- ❌ Token de 1 uso pra change-password — complexidade desnecessária pra cliente logado.
- ❌ Forçar relogin após change-password — UX pior; melhor reassinar sessão com nova senha-hash.

**Critério de sucesso:**

- Otávio clica "Sair" no header em prod → vai pra tela de login + cookie removido.
- Otávio loga, abre "Trocar senha" no header, digita senha antiga errada → erro "senha atual incorreta". Digita certa + nova → senha trocada, próximo login funciona com nova.

**Próxima sub-ação concreta:** depende do Sprint 2; primeira sub-ação = `curl POST /api/logout` em prod com cookie válido pra ver se backend está OK.

---

## 2026-05-19 — Sprint 5: Goal 5 — Target management completo com erros claros

**Goal endereçado:** Goal 5 (Gerenciamento completo de targets por cliente)
**Método escolhido:** dividir em duas fases.

**Fase A — Diagnóstico (1 ciclo):** com a baseline do Sprint 1 em mãos, reproduzir cada um dos 4 fluxos de target em prod e catalogar o que quebra:

- Add primário: o fluxo que o Otávio disse que "gera erros" — descobrir onde (UI? API? ingest?).
- Remove primário, demote primário→secundário, add secundário: testar idem.

**Fase B — Implementação por operação (4 mini-sprints, 1 por operação):** cada operação ganha:

- Endpoint dedicado se ainda não existir, com retorno estruturado `{ok, error?: {code, message, field?, suggestion?}}`.
- UI: botão/form na tela de cliente (do Sprint 2) com tratamento de cada `error.code` traduzido em mensagem específica.
- 3 testes mínimos: happy path, conflito (já existe), falha (ingest vazio / nome inválido).

**Por que esse método:**

- Diagnóstico antes de mexer — sem saber o estado atual, qualquer fix é chute (e arrisca regressão).
- Uma operação por vez porque cada uma tem semântica própria (promote vs demote vs add primário vs add secundário) e o Otávio disse que pelo menos o add-secundário tem bugs **graves** que merecem revisão completa, não patch.
- Retorno estruturado `{error: {code, message, field}}` em vez de string solta — permite UI traduzir cada caso e atende failure class "erro genérico" da seção Recurring Failures.

**Métodos já descartados:**

- ❌ Reescrever toda lógica de target do zero — perde Shakira/Flavio que já funciona.
- ❌ Patch só na UI sem auditar backend — cai exato na failure class #1 (Fake UI).
- ❌ Tratar as 4 operações como uma feature só — esconde os bugs específicos de cada uma.

**Critério de sucesso (observável):** Otávio abre cliente "flavio", testa as 4 operações e em **todas** vê: ou confirmação clara (happy), ou mensagem específica explicando o problema (conflito/inválido). Zero spinner infinito, zero "something went wrong".

**Próxima sub-ação concreta:** depende de Sprints 1, 2, 3, 4. Primeira sub-ação da Fase A = abrir `web_app/app.py` e mapear quais endpoints respondem hoje pelas 4 operações.

---

## Notas pra IA futura

- **Esses 5 sprints são propostas, não decretos.** O Otávio aprova/edita antes de cada um começar.
- **Goal 4 (regressão-zero) é meta**: cada sprint subsequente (2, 3, 4, 5) abre entrada major aqui dizendo "baseline mantida" ou "baseline mudou em X".
- **Não pular pra Sprint 5 sem 1-4 fechados** — o pain de target management é exatamente sintoma do que está faltando nos outros 4.
- **NOTA 2026-05-19 (Otávio):** abandonar nomenclatura "Sprint N" — o termo induz a parar quando "sprint fecha". Trabalho é contínuo até Goal cair em GOALS_ATINGIDOS. As 5 entradas acima continuam válidas como **frentes de trabalho** por Goal, não como sprints discretos.

---

## 2026-05-19 11:46 — Achado: backend de secundário OK; primário sem endpoint; bug deve estar na UI

**Goal endereçado:** Goal 4 (catalog) + Goal 5 (target mgmt)
**Método escolhido:** investigação direta via curl em prod + leitura de `web_app/app.py` + `web_app/db_admin.py:340-426`
**Por que esse método:** antes de propor fix, saber onde o bug está. Catalog = pré-requisito de regressão-zero.

**Descobertas estratégicas (não detalhes — esses estão em DET 11:36–11:46):**

1. **Backend de secundário já atende Goal 5 no shape de erro**: `POST /api/targets {}` retorna `{error, message, field, suggestion}` estruturado. Happy path cria target + sync end-to-end (DB + Supabase artifacts). Mensagem em português, com `suggestion` acionável.
2. **Não há endpoint pra primary target**: nenhuma rota muta `primary: true`. A guarda `ensure_secondary_mutable(row)` em `db_admin.py:383, 407, 418` bloqueia por design. Pra Goal 5 (admin add/remove/demote primário), **será preciso construir endpoints novos** — não tem caminho existente que possa ser estendido sem mexer nessa guarda.
3. **Bug "add-target gera erros" reportado pelo Otávio NÃO é nas 2 rotas testadas hoje**. Hipóteses restantes:
   - (a) UI (assets/clipping.js) faz POST com payload em formato diferente do que o backend espera
   - (b) UI não trata o response 400 estruturado (mostra "something went wrong" em vez do `message`/`suggestion`)
   - (c) bug em outro caso-edge: nome com caractere especial, conflito de slug, target homônimo (caso Shakira)
4. **Watch item (não bloqueante):** archive retornou `archived_at: 2026-05-20T...` enquanto hoje é 2026-05-19. Aparente discrepância de fuso/data servidor.

**Métodos já descartados pra investigar UI:**

- ❌ Testes Playwright completos — esforço alto.
- ❌ Browser manual — não tenho browser disponível, só Bash/Read.

**Critério de sucesso:** identificar a hipótese correta entre (a), (b), (c) lendo `assets/clipping.js` na função de add-target + tratamento de erro.

**Próxima sub-ação concreta:** `grep` em `assets/clipping.js` por "targets" + ler o handler do formulário de add-target. Documentar achados em DET 11:50+ e fechar a hipótese.

---

## 2026-05-19 11:50 — Catalog Goal 4 fechado: bug grave isolado no backend de validação de duplicata

**Goal endereçado:** Goal 4 (catalog/baseline) + Goal 5 (target mgmt)
**Método consolidado:** investigação direta em prod via curl + leitura de UI handler + leitura de backend handler
**Resultado:** catalog do baseline está fechado pra add-target secundário. Achados:

1. **Backend secundário (caminho estruturado):** ✅ OK. Validation error retorna `{error, message, field, suggestion}`. Happy path cria DB row + sync end-to-end. UI extrai e mostra corretamente.
2. **Backend primário (todas as 4 operações do Goal 5):** ❌ NÃO EXISTE. Guarda `ensure_secondary_mutable` em `db_admin.py:383,407,418` bloqueia. Goal 5 vai precisar **endpoints novos** + UI nova.
3. **BUG GRAVE confirmado:** POST /api/targets com `display_name` já existente retorna **HTTP 200** e cria duplicata silenciosa (`shakira_2`). Não é fake UI — é validação semântica ausente. Esse é provavelmente o bug que o Otávio chamou de "graves" pro add-target secundário.
4. **Watch items (não bloqueantes):** (a) discrepância de TZ no `archived_at` (server marca 16:44 UTC quando hoje é 19/maio); (b) UI cai em fallback genérico quando backend retorna 5xx ou não-JSON (não testado mas inferido do código).

**Métodos já descartados na investigação:** 
- ❌ Hipóteses (a) UI manda payload errado e (b) UI ignora erro estruturado — refutadas pela leitura do código.
- ✅ Hipótese (c) caso-edge não tratado pelo backend — **confirmada** no caso de display_name duplicado.

**Critério de sucesso atingido:** identificada a hipótese correta (c) e o bug específico isolado.

**Próximas frentes de trabalho** (não chamar de "sprint"; trabalho contínuo até Goal cair em GOALS_ATINGIDOS):

- **Frente próxima (Goal 5, antes ainda do Goal 1):** consertar o bug de duplicata semântica de display_name. Adicionar validação no backend (`create_secondary_target` em `db_admin.py:356`) que checa `display_name` colidindo com row ativa não-arquivada, e retorna `target_validation_error` com `field: display_name` e mensagem clara. Cobertura E2E: tentar criar "Shakira" de novo deve dar 400 com mensagem.
- **Frente paralela (Goal 5 primário):** projetar endpoints novos pra primary target — `POST /api/targets/primary`, `POST /api/targets/{key}/demote`, etc. Definir contrato de erro estruturado igual ao secundário.
- **Frente derivada (Goal 4 baseline ampliado):** testar próximos casos-edge — nome com acentos diferentes (`José` vs `Jose`), nome só com espaços, payload sem `keywords`, simulação de 5xx (matar backend? não dá em prod).

---

## 2026-05-19 11:56 — Frente próxima (duplicata) IMPLEMENTADA local — pytest verde, aguarda deploy

**Goal endereçado:** Goal 5 (mensagens claras) + Goal 4 (regressão-zero verificado)
**Método executado:** validação inline em `create_secondary_target` (case-insensitive, normaliza com `normalize_text` igual ao input pra evitar matchar acentos diferentes como nomes diferentes), levantando ValidationError com mensagem específica que dispara branch nova em `target_validation_payload`.

**Por que esse método (e não outro):**

- ✅ **Validação no backend (não na UI)**: failure class "Fake UI" exige source-of-truth no backend. UI valida pra UX, backend valida pra integridade.
- ✅ **Comparação no nível normalizado**: usa `normalize_text` que `clean_target_payload` já chama. Garante que "  Shakira  " e "Shakira" e "shakira" sejam todos rejeitados, mas "José" e "Jose" continuem sendo distintos (já que `normalize_text` não strip acentos, conforme observação dos casos).
- ✅ **Bloqueia só contra ativos**: arquivado não conta. Permite reabilitar um nome após arquivar o original — fluxo válido.
- ✅ **Mensagem é informativa**: cita o label do conflitante. Usuário sabe imediatamente com qual target colidiu.

**Métodos descartados:**

- ❌ Comparar slugs (`unique_target_slug` já gera slug único): isso resolveria DB-level mas o usuário continuaria vendo dois rows com mesmo display_name na UI. O problema é semântico, não de schema.
- ❌ Strip de acentos antes de comparar: arriscaria conflitar nomes legitimamente diferentes (ex: "Mario" e "Mário" são pessoas diferentes).
- ❌ Atrelar validação ao slug duplicate (`unique_target_slug` já produz `_2`): mantém o bug que o usuário relatou — ele acaba com 2 entradas idênticas na lista.

**Critério de sucesso (parcial atingido):**

- ✅ Pytest local: 249 passed, 13 deselected. Zero regressão.
- ✅ Novos testes cobrem 4 variações de duplicata (exato, lowercase, espaços, UPPER) + 1 caso de arquivado (não bloqueia).
- ⏳ **Falta**: deploy em prod + smoke via curl confirmando que POST /api/targets {"display_name":"Shakira"} agora retorna 400 com mensagem clara em vez de criar `shakira_2`.

**Arquivos tocados (3):** `web_app/db_admin.py`, `web_app/app.py`, `tests/test_targets_jobs.py`. Diff staged mas **não commitado** nem pushed — decisão de commit/deploy fica com o Otávio.

**Próxima sub-ação concreta:** verificar `git status`, propor mensagem de commit, e abrir próxima frente paralela (Goal 1 admin UI OU primary endpoints) enquanto deploy aguarda decisão.

---

## 2026-05-19 12:08 — Goal 2 mini-frente A: logout UI adicionado, backend já existia

**Goal endereçado:** Goal 2 (sessão controlada pelo usuário) — parte logout
**Método executado:** adicionar **só UI** (session-bar com profile/role + botão Sair), reusando o endpoint `/api/logout` backend que já existe e funciona em prod (validado via curl 12:05).

**Por que esse método (e não outro):**

- ✅ **Não tocar backend**: já existe, já funciona. Mexer adicionaria risco sem ganho.
- ✅ **Reusar dataset attributes**: `dashboard_html_for_session` (`web_app/app.py:327-343`) já injeta `data-clipping-session-role` e `data-clipping-session-profile` no `<main id="app">`. JS lê direto, sem precisar de endpoint `/api/me` novo.
- ✅ **Reusar `apiPost`**: ele já cuida do CSRF token via `ensureCsrfToken`. Logout endpoint exige `require_csrf` — passou direto pela mesma plumbing do POST de target.
- ✅ **Session-bar como primeiro filho de `<main>`**: posição natural, não compete com layout existente, fica visível em todas as views (tabs run/progress/base) porque é irmão da runner-shell, não filho.

**Métodos descartados:**

- ❌ Adicionar endpoint `/api/me` pra retornar identidade: redundante, dataset attrs já cobrem.
- ❌ Mover backend de logout pra GET com redirect: quebra a regra de CSRF/idempotência (logout MUTA estado de sessão; POST é o correto).
- ❌ Posicionar botão dentro da `runner-head` específica de cada tab: quebra acessibilidade (logout some quando trocar de tab).

**Critério de sucesso (parcial atingido):**

- ✅ Pytest local: 249 passed (com sync de `tools/pages_assets/clipping.{js,css}`).
- ✅ Backend confirmado em prod (curl 12:05).
- ⏳ **Falta**: deploy + smoke manual no browser pra confirmar visual + comportamento real do clique.

**Arquivos tocados (5):** `index.html`, `assets/clipping.css`, `assets/clipping.js`, `tools/pages_assets/clipping.css`, `tools/pages_assets/clipping.js`. Não commitado ainda.

**Goal 2 mini-frente B (trocar senha) — análise:** trocar senha exige storage mutável em runtime. Hoje credenciais vivem em env var (`CLIPPING_VIEWER_PASSWORDS`, `CLIPPING_ADMIN_PASSWORD`) — imutável sem redeploy. Pra fazer trocar senha funcionar, precisa de **migração da fonte de verdade pra arquivo** (mesma migração que destrava Goals 1 e 3). Logo, Goal 2 part B depende dessa migração — não vai ser cumprido sem ela. Decisão registrada como próxima frente strategic.

**Próxima sub-ação concreta:** commit do logout (5 arquivos path-limited), depois abrir próxima frente. Candidatos imediatos sem precisar de storage migration: (a) adicionar validação de duplicata em `update_secondary_target` (mesma família do fix recente), (b) explorar `/api/me`-like polish, (c) começar a desenhar a migração de storage em entry MAJOR (planning, não código). Prioridade: (a) é a mais natural e produz 1 commit limpo.

---

## 2026-05-19 12:15 — Goal 5 mini-frente B: validação de duplicata fechada em update_secondary_target

**Goal endereçado:** Goal 5 (target mgmt com erros claros) + Goal 4 (regressão-zero verificado)
**Método executado:** copiar o padrão do fix recente em `create_secondary_target` pra `update_secondary_target`, pulando o índice da própria row (idempotência preservada).

**Por que esse método:**

- ✅ **Mesma família de bug**: se create silencia duplicata, update também silencia rename pra duplicata. Fechar os dois com mesmo padrão.
- ✅ **Idempotência preservada**: skip-self garante que admin pode "salvar" sem mudar o nome (caso real do UX — clica salvar pra alterar keywords mas display_name continua).

**Critério de sucesso atingido:** 251 passed, 13 deselected. 2 testes novos cobrem rejeição + idempotência. Commit `f41a028`.

**Status do Goal 5 (resumo):**
- ✅ Secondary create: shape estruturado + dedup
- ✅ Secondary update: dedup
- ✅ Secondary archive + restore: já existiam, sem bug
- ❌ Primary management (add/remove/demote primário): SEM ENDPOINT — próxima frente major

**Não vai pra GOALS_ATINGIDOS ainda** porque (a) o backend de primary não existe e (b) a UI tem outras superfícies a auditar (5xx fallback, possíveis casos-edge de acentos/whitespace além de display_name).

---

## 2026-05-19 12:18 — Design (não-implementação) dos endpoints de primary target — frente Goal 5 amplo

**Goal endereçado:** Goal 5 (3 dos 4 sub-itens: add primário, remover primário, demote primário → secundário)
**Método proposto:** projetar contrato de endpoints + sketch do código antes de codificar, pra evitar fake-UI + falhas semânticas.

### Contrato de endpoints propostos

| Método | Path | Auth | Operação | Body | Resposta sucesso | Resposta erro |
|---|---|---|---|---|---|---|
| POST | `/api/targets/primary` | admin + csrf | criar target primário | `{display_name, keywords?, exact_aliases?}` | 200 `{key, label, display_name, primary: true, className: "primary", ...}` | 400 `target_validation_error` |
| POST | `/api/targets/{key}/demote` | admin + csrf | primário → secundário | `{}` | 200 `{key, ..., primary: false, className: ""}` | 400 (não-primário, arquivado) ou 404 |
| POST | `/api/targets/{key}/promote` | admin + csrf | secundário → primário | `{}` | 200 `{key, ..., primary: true, className: "primary"}` | 400 (já primário, arquivado) ou 404 |
| POST | `/api/targets/{key}/archive` (existente) | admin + csrf | arquivar **agora também** primário | `{reason?}` | 200 `{...archived: true}` | 400 só pra arquivado já / 404 |

**Mudanças necessárias em `db_admin.py`:**

1. **`PRIMARY_TARGET_KEYS` deixa de ser tupla hardcoded** (`("flavio_valle", "pedro_angelito")` em `db_admin.py:23`). Vira função `primary_target_keys()` que lê de `data/targets.json` (campo `primary: true`). Razão: o conjunto de primários precisa ser dinâmico se admin pode criar/demote.
2. **`ensure_secondary_mutable` deixa de bloquear archive** (mas mantém bloqueio em create/update específicos). Reformular como `ensure_target_mutable(row, *, allow_primary=False)`.
3. **Nova função `create_primary_target(payload)`**: igual a `create_secondary_target` mas com `primary=True, className="primary"`. Mesma dedup.
4. **Nova função `demote_target(key)`** e **`promote_target(key)`**: mexem nos campos `primary` e `className`. Reusam `find_target_index`.
5. **`PRIMARY_TARGET_KEYS` ainda existe como cache lido?** Talvez mantar pra `normalize_targets` saber forçar `primary=True` no Flávio Valle e Pedro Angelito mesmo se o file estiver inconsistente. Decidir durante implementação.

**Mudanças necessárias em `app.py`:**

1. **3 endpoints novos** com mesma estrutura dos secondary (require_admin + require_csrf + try/except ValidationError + target_validation_response).
2. **`target_validation_payload` ganha branches** pra mensagens novas: "alvo já é primário" (idempotente), "alvo já é secundário" (idempotente).
3. **`scoped_targets_response` continua funcionando** porque ele opera sobre o array de rows, não depende de PRIMARY_TARGET_KEYS hardcoded.

**Mudanças necessárias na UI (assets/clipping.js + index.html):**

1. **No `manageTargetsList`** (lista de "Gerenciar nomes extras"), adicionar dropdown/botão `Promover a principal` e `Arquivar`. Talvez `Demover` na lista de primários.
2. **No `addTargetForm`**, adicionar checkbox/segmented "Tipo: Secundário | Principal" — chama endpoint correspondente baseado na escolha.
3. **Sincronizar `tools/pages_assets/clipping.{js,css}` via `cp`** após cada edit.

**Riscos identificados:**

- 🚨 **Migração de `PRIMARY_TARGET_KEYS` afeta normalização.** Hoje `normalize_targets` em `db_admin.py` força `primary=True` SOMENTE pra `flavio_valle` e `pedro_angelito`. Se isso for relaxado, qualquer mutação por engano pode "desligar" o primary deles. Mitigação: manter PRIMARY_TARGET_KEYS como "core protegido" + nova lista mutável pra add/demote.
- 🚨 **Demote de primary com mentions existentes**: `mentions` no DB referenciam o target via `target_key`. Demote muda só `primary`/`className`, não `key` — mentions continuam ligadas. **Verificar** que `live-results` e exports continuam funcionando após demote.
- 🚨 **Restore de primary arquivado**: hoje `restore_secondary_target` chama `ensure_secondary_mutable` que bloqueia. Vai precisar de função restore que não bloqueia.

**Métodos descartados:**

- ❌ **Endpoint genérico `PATCH /api/targets/{key}` mudando `primary: bool`**: fica idiomático mas mistura semânticas (rename + promote/demote). Mais fácil errar; mais difícil testar erro claro.
- ❌ **Sobrescrever `update_secondary_target` pra aceitar `primary: True`**: cai na failure class "Dois fluxos pra mesma coisa".

**Critério de sucesso:** Otávio abre admin, cria "Maria Silva" como primário direto, depois demove pra secundário, depois arquiva, em todas mensagens claras e UI refletindo. Smoke em prod cobre as 4 operações com sucesso.

**Próxima sub-ação concreta:** começar implementação pelos itens 1 e 3 de `db_admin.py` (função `create_primary_target` + ajuste de `PRIMARY_TARGET_KEYS` pra dinâmico via função). Testar isolado antes de mexer em demote/promote.

---

## 2026-05-19 12:35 — Goal 5 backend COMPLETO (4/4 operações) — local, aguarda deploy

**Goal endereçado:** Goal 5 (target management completo com erros claros)
**Método executado:** refactor `PROTECTED_PRIMARY_KEYS` + `is_primary` helper → `create_primary_target` + endpoint → `promote_target_to_primary` + endpoint → `demote_target_to_secondary` + endpoint → branches de erro em `target_validation_payload`.

**Por que esse método (e não o descartado):**

- ✅ **Manter PROTECTED como core**: Flávio Valle e Pedro Angelito ficam intocáveis (não podem ser demoted/archive por engano via API). Risco do MAJOR 12:18 mitigado.
- ✅ **Honrar `primary` no file pra outros rows**: única source-of-truth (data/targets.json). Sem segundo arquivo "promoted_list" — menos complexidade.
- ✅ **Endpoints separados por operação**: cada uma tem semântica própria (create vs promote vs demote vs archive) → mensagens de erro específicas → atende failure class "erro genérico".
- ✅ **promote/demote são idempotentes-com-erro**: tentar promote em algo já-primário retorna 400 com mensagem clara, não silenciosamente. Mesmo pra demote.

**Métodos descartados:** confirmados (PATCH /targets/{key} com `primary: bool`, sobrescrever `update_secondary_target`) — refutados por simplicidade e clareza de erro.

**Critério de sucesso atingido:**

- ✅ 258 tests passed (5 novos pra promote/demote + 2 pra create_primary + reformulações dos 2 antigos).
- ✅ PROTECTED_PRIMARY_KEYS preservados em todas as operações (Flávio/Pedro continuam primary, não podem ser demoted, não são alterados por sanitize).
- ✅ Erro estruturado em todas as 4 operações novas.
- ⏳ **Falta**: UI exposing the 4 endpoints + smoke em prod pós-deploy.

**Arquivos tocados nesta frente (3 commits acumulados desde 11:56):**

- `4efe9f3` feat(targets): allow admin to create primary targets via API (refactor + create_primary)
- `fcb2126` feat(targets): add promote/demote endpoints for primary management

**Status Goal 5 (atualizado):**
- ✅ Secondary create dedup + shape estruturado
- ✅ Secondary update dedup
- ✅ Primary create
- ✅ Primary→secondary demote (com PROTECTED guard)
- ✅ Secondary→primary promote
- ✅ Archive (já existia)
- ❌ UI: forms/buttons pra essas 4 operações novas
- ⏳ Goal 5 não migra pra GOALS_ATINGIDOS ainda — falta UI

**Próxima sub-ação concreta:**

- **Frente próxima preferida:** adicionar UI pros 4 endpoints novos em `assets/clipping.js` + `index.html` + sync `tools/pages_assets/`. Sem isso, Goal 5 funciona via curl mas não via dashboard — fake completion risk.
- **Frente alternativa:** abrir Goal 1 (admin clients UI) ou começar storage migration (que destrava Goal 1 + Goal 2 part B + Goal 3).
- **Frente bloqueada:** Goal 2 trocar senha — depende inteiramente da storage migration. Registrado entry abaixo.

---

## 2026-05-19 12:38 — Goal 2 trocar senha: BLOQUEADO por storage migration (documentado)

**Goal endereçado:** Goal 2 (sessão controlada — parte trocar senha)
**Método proposto e descartado por dependência:**

A implementação direta — endpoint `POST /api/change-password` que lê `old_password`, valida, atualiza nova — exige **storage mutável em runtime**. Hoje:

- `CLIPPING_ADMIN_PASSWORD` é env var (read-only em runtime do FastAPI)
- `CLIPPING_VIEWER_PASSWORDS` é env var JSON (idem)
- Mudar uma senha exige editar a env var no Render Dashboard + redeploy

**Implicações:**

- ❌ Não tem onde gravar a senha nova sem migrar pra arquivo/DB
- ❌ Migração de env-var → arquivo é a MESMA migração necessária pro Goal 1 (admin gerencia clientes via UI sem env var) e pro Goal 3 (admin define senha ao criar cliente)
- ✅ Logo, **Goal 2 part B fica naturalmente bloqueado por Goal 1's storage migration** — não duplicar esforço

**Próxima frente recomendada se Otávio escolher destravar Goal 2 part B:**

1. Implementar `data/viewer_credentials.json` como fonte da verdade (substituindo as env vars `CLIPPING_VIEWER_PASSWORDS` e `CLIPPING_ADMIN_PASSWORD`)
2. `web_app/auth.py:viewer_passwords()` e `auth.py:check_password()` leem do arquivo (com fallback pra env var durante migração)
3. Endpoint `POST /api/change-password` (`require_viewer`, valida `old_password`, grava `new_password`, reassina sessão)
4. Backup do arquivo via mecanismo Supabase existente
5. UI: modal/page acessível pelo botão na session-bar (já existe a session-bar)

**Risco crítico identificado:** se a migração der ruim, prod perde auth — ninguém entra. Mitigação obrigatória: fallback pra env var por **pelo menos 1 release** + alarme em `/healthz` se file storage falhar (assim Otávio percebe antes do cliente).

**Próxima sub-ação concreta:** decisão do Otávio sobre prioridade — destravar Goal 2 part B / Goal 1 / Goal 3 via storage migration (~2-3 horas de trabalho cuidadoso) OU adicionar UI pros endpoints de primary mgmt (~1-2 horas, completa Goal 5 sem novas dependências).

---

## 2026-05-19 12:45 — Goal 5 UI completo: dashboard expõe os 4 endpoints de primary mgmt

**Goal endereçado:** Goal 5 (target mgmt completo) — agora UI também
**Método executado:** estender `managedTargetCard` em `assets/clipping.js` pra incluir botões Promover/Rebaixar, criar funções `promoteManagedTarget`/`demoteManagedTarget`, adicionar handlers no app-level click delegator, exibir chips visuais pra Principal e Principal protegido. CSS coerente com tokens existentes.

**Por que esse método:**

- ✅ **Reusar `managedTargetCard`** em vez de criar lista separada: lista única "Nomes ativos" mostra tudo, com chips diferenciando — menos UI fragmentation.
- ✅ **PROTECTED_PRIMARY_KEYS duplicado no JS** (`["flavio_valle", "pedro_angelito"]`): pequena duplicação acceitável pra evitar criar `/api/me` ou injetar do backend. Trade-off documentado.
- ✅ **Protected primaries renderizam sem botões** (só nota explicativa): UI honra a guarda do backend — admin não pode tentar promover/demover/arquivar Flávio e Pedro, mesmo via inspector do navegador.

**Métodos descartados:**

- ❌ Lista separada "Principais" pra primárias e "Secundários" pra resto: fragmenta UI sem ganho real.
- ❌ Read `PROTECTED_PRIMARY_KEYS` from `/api/me` ou outro endpoint: adiciona dependência sem ganho em estágio inicial.
- ❌ Toggle "Cadastrar como principal" no addTargetForm: sai do escopo desta iteração (cria-secundário-e-promove cobre o caso).

**Bug grave encontrado e resolvido durante a iteração:** quote-mismatch em string template literal em `clipping.js:795` (`'>Arquivar</button>';` em vez de `'>Arquivar</button>";`). Browser falhava no parse com "Invalid or unexpected token" sem linha. **Pytest no full mode pegou** (TestFunctionalSanity::test_articles_visible_after_load timeout) — confirma o valor de não pular `-m "not live"` em mudanças de JS. Diagnóstico via Playwright bisect (`new Function(src)` + binary search em prefixos).

**Critério de sucesso atingido:**

- ✅ Pytest full suite: 258 passed, 13 deselected (incluindo TestFunctionalSanity e TestPagesBenchmark verdes).
- ✅ Botões Promover/Rebaixar/Arquivar/Editar exibidos por target type.
- ✅ Protected primaries (Flávio Valle, Pedro Angelito) sem botões, com nota explicativa.
- ⏳ **Falta**: smoke manual no browser em prod pós-deploy.

**Status do Goal 5 atualizado:**
- ✅ Backend: 4/4 operações (create secondary, create primary, promote, demote, + archive/restore reusando guards corretos)
- ✅ UI: chips + botões pros 4 endpoints novos
- ✅ Erros estruturados em todos os caminhos
- ⏳ Smoke em prod (depende de push + deploy autorizado)

**Goal 5 ESTÁ PRONTO PRA MIGRAR PRA `GOALS_ATINGIDOS.md`** assim que o Otávio (a) autorize push + deploy, (b) confirme manualmente em prod que as 4 operações funcionam no browser.

**Próxima sub-ação concreta:** atualizar SESSION_LOG, commitar docs, aguardar decisão do Otávio sobre próximo passo. Candidatos para enquanto ele revisa: começar storage migration (frente bloqueadora de Goals 1, 2-B, 3) OU mexer em casos-edge restantes do baseline (acentos diferentes, payload sem keywords, etc.).
