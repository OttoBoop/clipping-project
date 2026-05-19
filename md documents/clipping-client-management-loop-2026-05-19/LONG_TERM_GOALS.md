# Long-Term Goals — Clipping Client Management Loop

**Created:** 2026-05-19
**Purpose:** âncora invariante para todos os sprints derivados deste loop. Cada sprint deve referir um Goal específico daqui. Goals só mudam com aprovação explícita do Otávio — nunca unilateralmente por IA.

**Mantra do loop:** [MANTRA.md](MANTRA.md) · **Pontos de registro:** [SESSION_LOG.md](SESSION_LOG.md) · **Goals concluídos:** [GOALS_ATINGIDOS.md](GOALS_ATINGIDOS.md) · **Log estratégico:** [WORK_LOG_MAJOR.md](WORK_LOG_MAJOR.md) · **Log fino:** [WORK_LOG_DETALHADO.md](WORK_LOG_DETALHADO.md)

---

## Source Prompts From Otávio (citações diretas, 2026-05-19)

> "Eu quero adicionar a função de adicionar targets primários, remover targets primários, transformar targets primários em secundários."

> "Eu vi bugs graves para adicionar targets secundários, precisamos de uma rodada completa de revisão ao criar essa feature, com erros claros caso um problema surja."

> "Temos que ter muito cuidado para construir algo de fato completo, que não apareça só na UI, mas sim conectado a todos os sistemas secundários e primários."

> "As senhas estão hiper complicadas, precisam ser simplificadas, neste estágio inicial."

> "Estamos sem função de logout. Estamos sem função de trocar a senha."

---

## Goals That Must Survive Every Sprint

### Goal 1 — Onboarding administrativo via UI

Admin **gerencia clientes (viewers) sem editar env var nem fazer redeploy**. Inclui:

- Tela listando todos os clientes registrados (perfis ativos, role, último login se houver)
- Formulário de criação de novo cliente (nome do perfil, senha, targets que enxerga)
- Ação de arquivar/desativar cliente

**Failure case:** criar cliente novo exigir editar `CLIPPING_VIEWER_PASSWORDS` no Render Dashboard à mão e disparar redeploy.

### Goal 2 — Sessão controlada pelo próprio usuário

Cada usuário (admin e viewer) precisa poder:

- **Sair** (logout funcional na UI — não só endpoint backend)
- **Trocar a própria senha** sem assistência do dono

Estado atual: o endpoint `POST /api/logout` existe em `web_app/app.py:196` (per leitura do loop anterior), mas o Otávio relatou que logout não funciona — tratar como UI ausente ou quebrada. Trocar senha não existe em nenhuma camada.

**Failure case:** usuário pedindo ao Otávio por DM pra ele editar env var pra mudar a senha.

### Goal 3 — Senhas simples e comunicáveis

Senhas precisam caber em uma mensagem de WhatsApp e ser ditáveis por telefone. As atuais (`3a8fa8ed62fa1b322c98877e19ed05326e49d5a626239a8b` — 48 caracteres hex) violam isso.

Modo de simplificação confirmado pelo Otávio: **admin define a senha do cliente ao criar** (ex: `flavio-gabinete-2026`). Sem fluxo de email (a infraestrutura de email não está construída — não cabe no estágio atual). Sem reset self-service por enquanto.

**Failure case:** gerar senha aleatória de 48 chars hex pra um cliente novo e mandar pelo WhatsApp.

### Goal 4 — Regressão-zero entre features

Toda feature nova **preserva todo o caminho das antigas** (UI → API → ingest → DB → filtro → export → static artifact). Cada commit que mexe em um ponto da pipeline obriga verificar visualmente (não só com testes) que os pontos a jusante continuam funcionando.

O gatilho desse goal: o Otávio relatou que **adicionar novos targets gera erros** — regressão do sprint anterior de senhas/segregação, que mexeu em escopo de viewer sem auditar o fluxo de target-add.

**Failure case:** PR de senhas que muda o filtro de payload de viewer e quebra silenciosamente o `POST /api/targets` porque ninguém retestou esse caminho.

### Goal 5 — Gerenciamento completo de targets por cliente, com erros claros

Admin precisa poder, **para cada cliente**:

- Adicionar **target primário**
- Remover **target primário**
- Transformar **target primário em secundário**
- Adicionar **target secundário** (essa parte hoje tem bugs graves — exige revisão completa)

Cada uma dessas 4 operações precisa:

1. Funcionar end-to-end (UI → ingest → filtro → export — não só "aparecer na lista")
2. Produzir **mensagens de erro claras** quando algo dá errado (ex: "target já existe", "nome conflita com homônimo", "ingest não conseguiu encontrar nenhuma fonte pro nome X") — não erro genérico, não silêncio

**Failure case:** clicar "adicionar target" e ver spinner infinito ou erro genérico "something went wrong" sem indicação de qual etapa falhou.

---

## Recurring Failure Classes To Avoid

1. **Fake UI:** feature aparece na tela mas backend/ingest/export não recebe. Já aconteceu pelo menos 2x (caso Shakira, caso add-target).
2. **Regressão silenciosa entre sprints:** sprint N quebra fluxo do sprint N−1 sem ninguém perceber até cliente reclamar.
3. **Configuração escondida em env var:** features que exigem mexer no Render Dashboard pra cada cliente novo.
4. **Erro genérico em vez de mensagem específica:** "error", "something went wrong", spinner infinito — usuário não sabe se foi rede, conflito, validação, etc.
5. **Senha 48-hex tratada como UX aceitável:** artefato de geração `openssl rand -hex 24` jogado direto na cara do cliente.
6. **Dois fluxos pra mesma coisa:** ex: editar perfil via env var E via UI, sem fonte única de verdade.
7. **Goal sem failure case:** se uma IA futura escrever Goal novo aqui sem incluir "failure case", o Otávio não consegue auditar se o sprint cumpriu o Goal.

---

## Short-Term Loop Rule

Todo sprint derivado deste documento **deve**:

1. Citar qual(is) Goal(s) ele endereça
2. Especificar o caminho end-to-end que será preservado/criado (UI → API → DB → ingest → export)
3. Definir o teste de aceitação **observável pelo Otávio em produção** (não só pytest)
4. Atualizar `WORK_LOG_MAJOR.md` com o método **antes** de codificar
5. Não tocar este `LONG_TERM_GOALS.md` (só muda com aprovação explícita do Otávio)
