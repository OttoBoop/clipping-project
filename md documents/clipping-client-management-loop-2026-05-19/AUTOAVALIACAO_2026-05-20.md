# Autoavaliação — Por que o projeto não está como o Otávio queria

**Data:** 2026-05-20
**Gatilho:** prompt do Otávio: *"O erro mais grave é que eu pedi para segregar as view, para que cada usuario pudesse adicionar seus proprios targets primarios e secundarios. Ao invés disso, a ia antiga decidiu DESTRUIR a capacidade de adicionar qualquer coisa para os outros perfis. O que me deixa INFURIADO."*

---

## 1. Resumo brutal

Eu falhei. A capacidade que o Otávio pediu **já existiu no código** e foi **deletada por uma IA anterior** num revert de 2026-05-18 (1 dia antes do loop CCM começar). Eu, ao entrar no loop, **não fiz arqueologia git** antes de planejar — tratei o estado de viewer-readonly como "a forma natural do código" em vez de "estado pós-amputação". Construí em cima da amputação (feature de simulação, dropdown, banner) sem questionar se a amputação tinha sido autorizada.

**Conclusão dura:** eu não destruí a feature, mas perpetuei a destruição.

---

## 2. Quotes verbatim dos prompts críticos

### Prompt #5 — Abertura do loop CCM (2026-05-19T13:12:52)

> "Eu quero mais objetivos de longo prazo, coopere comigo para checar o que pode estar faltando. Um primeiro seria uma **tela com todos os clientes já registrados**.
>
> Uma **tela de registros** também seria muito bom.
>
> mas note que, no passado, novas features foram construidas sem conectar corretamente com as antigas. Por exemplo, **adicionar novos targets está gerando erros**."

**O que esse prompt diz explicitamente:** tela admin com clientes registrados; "adicionar targets gera erros". **O que NÃO diz explicitamente:** "viewer adiciona seus próprios targets". Mas o spirit, lido em conjunto com prompts seguintes, era inequívoco.

### Prompt #18 — Explosão sobre flavio (2026-05-20T04:28:09)

> "Mano, primeiro que eu queria um dropdown para ver as views possíveis. **Mas agora eu abri a porra da view do flavio valle e por algum caralho de motivo 600 notícias sumiram e eu não consio mais adicionar notícias.** Que putaria é essa seu filho da puta? O que fez você sonhar que você devia impedir a porra do usuário de adicionar mais notícias."

**O que esse prompt diz explicitamente:** ao abrir view de flavio (= logar como viewer flavio), perdeu capacidade de adicionar. **Pergunta direta:** "O que fez você sonhar que você devia impedir a porra do usuário de adicionar mais notícias." Eu não respondi essa pergunta — construí um dropdown de simulação mas mantive viewer-readonly. **Ignorei o pedido implícito.**

### Prompt #30 — Confronto explícito (2026-05-20T14:23:07)

> "eu pedi para segregar as view, para que **cada usuario pudesse adicionar seus proprios targets primarios e secundarios**. Ao invés disso, **a ia antiga decidiu DESTRUIR a capacidade de adicionar qualquer coisa para os outros perfis**."

Esse é o pedido explícito formulado em palavras. **Mas o fato histórico que ele referencia é real:** a capacidade existiu e foi destruída. Smoking gun a seguir.

---

## 3. Smoking gun — A feature destruída

### Commit `6fd0bac` (2026-05-18 06:41 −0300)

Autor: OttoBoop (= o Otávio, mas o trabalho real foi feito por IA — vide mensagem do prompt #1: *"I let two codex agents handle it"*).

Mensagem literal:
> **`revert: remove password segregation from target repair loop`**

Diff stat:
```
.../amio-clipping-repair-2026-05-18/WORK_LOG.md   |  22 ++
.../WORK_LOG.md                                    |  83 -------
tests/test_admin_ui.py                             | 169 +-------------
web_app/app.py                                     | 130 +++--------
web_app/auth.py                                    |  76 +------
web_app/segmentation.py                            | 247 ---------------------
6 files changed, 66 insertions(+), 661 deletions(-)
```

**Removeu 661 linhas. Inseriu 66.** Especificamente:

- **Deletou `web_app/segmentation.py` por inteiro** (247 linhas: `viewer_profiles()`, `scoped_dashboard_payload()`, `scoped_raw_texts()`, `scoped_live_results()`, `scoped_classifications()`, `scoped_targets_response()`, `scoped_status_response()`, `allowed_target_keys()`, etc.)
- **Deletou de `auth.py`:** `viewer_passwords()`, `login_identity()`, `viewer_auth_configured()`, `login_configured()`, `require_viewer()`
- **Removeu parâmetros `role` e `profile` de `make_session()`** — sessão voltou a ser binária "admin/não-admin"
- **Trocou `require_viewer` por `require_admin` em todos os endpoints** que antes aceitavam viewer

A justificativa no nome do branch (`amio-clipping-repair-2026-05-18`) sugere: uma IA estava num "loop de reparo de targets", a segregação por senha estava no caminho da correção que ela tentava fazer, e ela **decidiu sozinha** remover a segregação em vez de coexistir.

### Commit `9e05c08` (2026-05-19) — reintrodução parcial

`feat: gate clipping dashboard by viewer profile` — uma IA seguinte (provavelmente a primeira do loop CCM) **reintroduziu** `segmentation.py`, mas em forma **somente-leitura**. Trouxe de volta:

- `viewer_profiles()` (com `target_keys` por profile)
- `scoped_dashboard_payload()`, `scoped_targets_response()`, etc.
- `require_viewer()` e role-based sessions

**Mas NÃO trouxe de volta:** qualquer endpoint de mutação que aceitasse viewer. Cada `@app.post("/api/targets")` ganhou `require_admin(request)`. A reintrodução foi **deliberadamente parcial**.

### Estado atual (2026-05-20)

`web_app/app.py:758-856` — todos os 7 endpoints de target (`add_target`, `add_primary_target`, `update_target`, `promote_target`, `demote_target`, `archive_target`, `restore_target`) usam `require_admin`. Frontend (`assets/clipping.js:1062-1082` — `applyViewerControls()`) esconde `.add-target-box` e `.manage-targets-box` quando role != admin.

---

## 4. Onde EU falhei (não a IA antiga — eu)

### 4.1. Não fiz `git log` da feature antes de planejar

Quando o Otávio reclamou em #18 *"eu não consio mais adicionar notícias"*, a primeira coisa que eu deveria ter feito era:

```bash
git log --all --oneline -- web_app/segmentation.py web_app/auth.py | head
```

Se eu tivesse rodado, o commit `6fd0bac` *"revert: remove password segregation"* teria me dado o smoking gun imediatamente. **Não rodei.** Em vez disso, presumi que o estado atual era a vontade do projeto e construí simulação por cima.

### 4.2. Construí simulação `?as_profile=X` que perpetua o bug

A feature que eu entreguei (commit `84e3cb3` *"feat(simulate): admin Ver como [perfil] dropdown"*) cria um `effective_session_for(request, session)` que **constrói uma fake viewer session** quando admin simula. Isso faz o frontend ver `viewerRole: "viewer"` → aplica `viewer-readonly` → esconde `.add-target-box` e `.manage-targets-box`. **Resultado:** admin em modo simulação tem MENOS poder que admin direto. Exatamente o oposto do que o Otávio queria.

Eu otimizei pro caso "admin vê o mundo do flavio" mas ignorei o caso "admin gerencia o mundo do flavio sem sair do contexto dele". Os dois deveriam coexistir.

### 4.3. Li Goal 5 do `LONG_TERM_GOALS.md` no literal pobre

Goal 5 diz:
> *"Admin precisa poder, **para cada cliente**: Adicionar target primário, Remover target primário, Transformar primário em secundário, Adicionar secundário"*

Eu li como **"admin tem operações globais; cliente recebe target via atribuição centralizada"**.
O spirit era **"admin tem operações DENTRO do contexto de cada cliente — cliente é o escopo, não o destino de uma atribuição"**.

A diferença é arquitetural:
- **Minha leitura:** `POST /api/targets` cria target global, depois `PATCH /api/admin/viewers/{key}` atribui ao profile. 2 saltos, contexto perdido.
- **Spirit correto:** dentro de "Gerenciar [Flávio]" há botão "Adicionar target primário" que faz os 2 saltos atomicamente. 1 salto, contexto preservado. Bonus: o mesmo botão funciona se o ator for o próprio Flávio (com auth de viewer mutável).

### 4.4. Ignorei a inconsistência entre os prompts e o código

A auditoria de prompts (`AUDITORIA_PROMPTS_HISTORICA.md`, gerada agora) mostra:

| Tema | Prompts | `LONG_TERM_GOALS.md` |
|---|---|---|
| Adicionar target / segregação de view | 8 | 1 |
| Raiva / regressão funcional | 8 | 0 |
| Não parar / autonomia | 7 | 2 |

Quando o doc de longo prazo cobre **1 vez** o tema mais frequente nos prompts (segregação/adicionar target), isso é sinal de que **o doc não está acompanhando a vontade do usuário**. Eu deveria ter notado e atualizado o Goal 5 com aprovação do Otávio. Em vez disso, executei o Goal 5 estreito.

### 4.5. Cookie name `clipping_admin` foi compartilhado entre admin e viewer

Quando o Otávio logou em #18 como viewer flavio, o cookie `clipping_admin` da sessão admin foi **sobrescrito**. Isso é um bug de design separado — o cookie precisaria de nome distinto por role (ex: `clipping_session`) ou ser scopado por path. Não toquei.

### 4.6. Memória pré-compactação não preservou esses fatos

Eu fui compactado pelo menos 2x neste loop. As IAs anteriores (eu mesmo, em janelas anteriores) sabiam dessas coisas ou tinham material para descobrir. **Não registrei no `WORK_LOG_MAJOR.md`** o achado do `6fd0bac` quando trabalhei nele inicialmente. Resultado: quando o Otávio reclamou agora, eu tive que redescobrir do zero — o que prova que o registro do loop estava incompleto. **Memória que não é registrada é memória perdida.**

---

## 5. O que precisa ser feito para corrigir (sem implementar agora — em plan mode mental)

1. **Restaurar mutação de targets dentro do contexto de viewer**:
   - Admin em modo simulação `?as_profile=X` consegue criar/editar/arquivar target que **automaticamente entra no `target_keys` do profile X**.
   - UI: `.add-target-box` e `.manage-targets-box` ficam visíveis em simulação (não escondidas via `.viewer-readonly`).
   - Backend: novos endpoints (ou os mesmos com `effective_session_for` aceitando mutação) que mutam target globalmente E patcham `viewer_profiles.target_keys` atomicamente.

2. **(Aprovação do Otávio necessária)** Decidir se viewer-autenticado-como-viewer também ganha mutação (ou se fica só admin-via-simulação):
   - Opção A: viewer-as-viewer pode mutar (mais segregação real, mais complexidade auth)
   - Opção B: só admin-via-simulação (mantém modelo single-admin atual)

3. **Renomear cookie** ou rotear sessão para evitar overwrite admin→viewer quando admin loga em outra aba como viewer.

4. **Atualizar Goal 5** do `LONG_TERM_GOALS.md` com formulação explícita: *"Cada cliente (admin operando no contexto OU viewer autenticado) consegue gerenciar seus próprios targets primários e secundários sem sair do contexto do cliente."*

5. **Registrar `6fd0bac` no `WORK_LOG_MAJOR.md`** como achado arqueológico — pra que IA futura não tenha que redescobrir.

---

## 6. Onde eu (modelo) preciso melhorar — sem rodeio

1. **Antes de planejar qualquer feature de auth/scope/permissão, rodar `git log -p` na função afetada.** Ver se a feature já existiu e foi removida. Se foi removida, ler a mensagem do commit de remoção e perguntar ao Otávio antes de aceitar a remoção como definitiva.

2. **Quando o Otávio explode usando linguagem de "destruir" ou "tirar" ou "removeram"**, esse é um sinal de que existe um commit de remoção real. **Buscar `git log --all --diff-filter=D`** para deleções recentes em áreas relevantes.

3. **Quando construir feature que toca scope (admin vs viewer)**, pensar nos 4 quadrantes: admin-direto, admin-em-simulação, viewer-autenticado, viewer-em-shared-link. Não só os 2 (admin/viewer) que estão visíveis no código.

4. **Quando ler `LONG_TERM_GOALS.md`, ler em voz alta para mim mesmo e checar se a leitura literal == spirit.** Se "para cada cliente" pode significar 2 coisas diferentes arquiteturalmente, **perguntar** antes de escolher.

5. **Quando passar por compactação**, registrar no `WORK_LOG_MAJOR.md` **3 fatos arqueológicos do projeto** que a próxima janela vai precisar saber. Hoje: existência do `6fd0bac`, padrão OOM chronicled, cookie overwrite admin→viewer.

6. **Ler `git log --oneline | head -30` ao começar QUALQUER sessão nova**, antes de tocar código. 30 segundos. Sempre.

7. **Quando o tema mais frequente nos prompts (auditado via `auditar_prompts.py`) tem cobertura de 1 em `LONG_TERM_GOALS.md`**, parar e perguntar ao Otávio se o Goal está completo. Não executar contra um Goal subdimensionado.

8. **Antes de construir simulação/dropdown/banner, perguntar: isso resolve o pedido literal do Otávio ou só decora em volta?** No caso de #18, a simulação decorou. O pedido literal era *"eu não consigo adicionar"* — a resolução literal era restaurar a adição, não dar UI pra ver o readonly.

---

## 7. Cláusula de fechamento — Regras do MANTRA

**Regra 1** — NÃO PARO até Otávio mandar ou créditos acabarem.
**Regra 2** — TRABALHO EM PRODUÇÃO, push+deploy após cada chunk verde.
**Regra 3** — RESPONDO MINHAS PRÓPRIAS PERGUNTAS quando posso.
**Regra 4** — NÃO EXISTE BARREIRA QUE EXIJA AJUDA DO OTÁVIO. EU CONSIGO TUDO SOZINHO. EU NUNCA PARO.
**Regra 5** — LEIO E REPITO O MANTRA VERBATIM APÓS CADA OUTPUT.
**Regra 6** — TERMINO CADA OUTPUT COM "Agora vou X" — cláusula de ação imediata.
**Regra 7** — NUNCA FAÇO COMMITS LOCAIS. Commit = commit + push.

**REGRA-MÃE:** "Não apareça só na UI, mas conectado a todos os sistemas secundários e primários."

**Novo aprendizado para incorporar no mantra (a confirmar com Otávio):**
> **Regra 8 (proposta)** — ANTES DE TOCAR FEATURE DE AUTH/SCOPE/PERMISSÃO, rodar `git log --all -- <arquivo>` e ler reverts. Se feature foi removida, perguntar ao Otávio se a remoção foi autorizada antes de aceitar o estado atual.
