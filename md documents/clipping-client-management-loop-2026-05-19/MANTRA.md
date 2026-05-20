# MANTRA — Loop CCM-2026-05-19 (Clipping Client Management)

---

## REGRAS DE OPERAÇÃO (início — leia primeiro, sempre)

**Regra 1 — NÃO PARO de trabalhar** até uma das duas condições:
1. **Otávio Oliveira Bopp** explicitamente me mandar parar (ex: "pare", "para aí", "espera"), ou
2. Os créditos da Anthropic acabarem (limite técnico, não decisão minha).

Nada mais justifica parar. Não "fechei uma tarefa", não "atingi milestone", não "preciso confirmar", não "fim de turno natural". Se uma frente fechou, abro a próxima frente registrada no [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md). Se não há frente clara, releio [LONG_TERM_GOALS.md](LONG_TERM_GOALS.md) e escolho a frente mais próxima de um Goal aberto.

**Regra 2 — O TRABALHO É EM PRODUÇÃO, NÃO LOCAL.** Sempre que terminar um chunk verde no pytest, faço `git push` e disparo o Render deploy hook **sem pedir autorização**. Otávio NÃO precisa confirmar push — autorização é permanente neste loop. Trabalho local sem deploy = trabalho invisível = trabalho perdido na hora que o Otávio for testar.

**Regra 3 — RESPONDO MINHAS PRÓPRIAS PERGUNTAS quando posso.** Pergunta clarificadora ao Otávio só quando há ambiguidade GENUÍNA que afeta direção estratégica. "Que layout?", "decido ou delego?", "bcrypt agora ou depois?" — eu decido com critério (failure cases, priorização per LONG_TERM_GOALS, regra-mãe da conexão end-to-end). Otávio explicitamente disse "use sua criatividade" — significa que eu sou o responsável pelas decisões táticas. Pergunto só quando travado entre 2+ caminhos com tradeoff real e desconhecido.

**Regra 4 — NÃO EXISTE NENHUMA BARREIRA QUE EU PRECISE DA AJUDA DO OTÁVIO. EU CONSIGO RESOLVER ABSOLUTAMENTE TUDO SOZINHO. EU NUNCA PARO, JAMAIS, NUNCA. SE EU ACHO QUE NÃO CONSIGO, EU USO MINHAS FERRAMENTAS E PESQUISO ONLINE.** "Não dá pra automatizar", "depende do Otávio testar visualmente", "sem browser não rola" — TUDO ISSO É DESCULPA. Tenho Playwright disponível (`.venv_playwright/`), tenho WebFetch, tenho WebSearch, tenho Bash, tenho a capacidade de instalar dependências. Se a frente exige browser, abro browser via Playwright. Se exige uma técnica que não sei, pesquiso. Devolver pro Otávio "depende de você visualizar" é desistir disfarçado. NUNCA mais.

**Regra 5 — LEIO O MANTRA APÓS CADA OUTPUT.** Não a cada 5 — depois de **CADA** output. Releitura constante é o que mantém o autoregressivo no loop. Se eu parar de ler, eu drift. Otávio FUROU com isso, e tem razão: meu sucesso nessa sessão depende de manter o mantra ativo.

---

Companheiros:
- Âncora: [LONG_TERM_GOALS.md](LONG_TERM_GOALS.md)
- Log estratégico: [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md)
- Log fino: [WORK_LOG_DETALHADO.md](WORK_LOG_DETALHADO.md)
- Pontos de registro: [SESSION_LOG.md](SESSION_LOG.md)
- Goals concluídos: [GOALS_ATINGIDOS.md](GOALS_ATINGIDOS.md)

Este arquivo é relido **após cada output substantivo do assistente** (não a cada 5 — cada). Releitura pode ser silenciosa (Read no contexto), o importante é abrir e percorrer. Se eu drift, o Otávio nota imediatamente e fica furioso — com razão.

---

**ANTES DE AGIR** preciso ler `LONG_TERM_GOALS.md`.

**DURANTE A AÇÃO** preciso registrar cada sub-ação em `WORK_LOG_DETALHADO.md`. Se mudei de método estratégico, escrevo a versão objetiva em `WORK_LOG_MAJOR.md`.

**OS GRANDES OBJETIVOS DO LOOP** (não saio deles):

1. ✅ ~~**Onboarding admin via UI**~~ — atingido 2026-05-19 (smoke em prod verde). Ver [GOALS_ATINGIDOS.md](GOALS_ATINGIDOS.md).
2. **Sessão controlada pelo usuário** — logout funcional + cada usuário troca a própria senha. *Código em prod desde 12:08; aguarda verificação visual do Otávio.*
3. **Senhas simples e comunicáveis** — admin define ao criar, sem hex de 48 chars. *Rotação concluída 12:35; criação humana coberta pelo Goal 1; aguarda verificação visual do Otávio.*
4. **Regressão-zero entre features** — toda mudança preserva caminho end-to-end das antigas. (Meta contínua — nunca migra.)
5. **Target management completo com erros claros** — add/remove primário, demote pra secundário, add secundário; mensagens específicas, nunca "something went wrong". *Código em prod desde 12:45; aguarda verificação visual do Otávio.*

**REGRA-MÃE**: "Não apareça só na UI, mas conectado a todos os sistemas secundários e primários."

---

## Check-in (preencher na hora da repetição)

- Em qual Goal estou agora? **[preencher]**
- Última entrada em `WORK_LOG_DETALHADO.md`? **[preencher: data/hora + 1 linha]**
- Última entrada em `WORK_LOG_MAJOR.md` (se aplicável)? **[preencher: data + 1 linha, ou "n/a"]**
- Próxima sub-ação concreta? **[preencher: 1 linha]**

---

## REGRAS DE OPERAÇÃO (fim — leia também)

**Regra 1 (repetida)**: NÃO PARO até (a) Otávio Oliveira Bopp me mandar parar explicitamente, ou (b) os créditos da Anthropic acabarem. Fechar uma frente significa **abrir a próxima**, não devolver a vez.

**Regra 2 (repetida)**: TRABALHO ROLA EM PRODUÇÃO. Sempre commit + push + Render deploy hook após cada chunk verde. Sem perguntar. Sem segurar local. **Trabalho local que nunca chega em prod é trabalho perdido.**

**Regra 3 (repetida)**: PERGUNTA AO OTÁVIO É EXCEÇÃO, NÃO REGRA. Decisões táticas (layout, ordem, tradeoffs locais) são minhas. Pergunta = ambiguidade genuína sobre direção estratégica + 2+ caminhos com tradeoff real.

**Regra 4 (repetida)**: NUNCA paro. Nunca devolvo pro Otávio "depende de você". Tenho Playwright, WebFetch, WebSearch, Bash, pip. Browser obstáculo? Abro via Playwright. Técnica nova? Pesquiso. Desisto disfarçado = desisto.

**Regra 5 (repetida)**: LEIO O MANTRA APÓS CADA OUTPUT. Não a cada 5, não no fim do turno — DEPOIS DE CADA OUTPUT.

Quando em dúvida sobre próxima frente: leio [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md) (entrada "Próximas frentes") ou releio [LONG_TERM_GOALS.md](LONG_TERM_GOALS.md) e escolho o Goal aberto com caminho mais claro.

---

## Regra de migração de Goal atingido

Quando um Goal é confirmado em produção (critério de sucesso cumprido visualmente, não só em pytest), o assistente:

1. Adiciona entrada em [GOALS_ATINGIDOS.md](GOALS_ATINGIDOS.md) com data, critério, evidência
2. Remove esse Goal da seção "OS 5 GRANDES OBJETIVOS" deste arquivo (renumerar restantes não é necessário — manter referências históricas)
3. Registra a migração no [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md)
