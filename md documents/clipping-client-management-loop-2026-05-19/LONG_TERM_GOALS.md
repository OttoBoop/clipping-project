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

### Goal 5 — Per-client custom targets (gerenciamento per-cliente com erros claros)

**Resposta original do Otávio (verbatim, AskUserQuestion 2026-05-19):**

> *"Per-client custom targets, mas vamos expandir... Adicionar targets primários, Remover targets primários, Transformar targets primários em secundários. Além disso, eu vi bugs graves para adicionar targets secundários, precisamos de uma rodada completa de revisão... com erros claros"*

Chave: **"Per-client custom targets"** — cada cliente tem seus próprios targets primários e secundários, customizáveis **dentro do contexto do cliente** (não via tela admin separada que atribui depois).

O ator pode ser admin operando via simulação `?as_profile=X` (modelo single-admin atual; cada mutação atribui automaticamente ao profile alvo via `add_target_to_profile`) e/ou viewer autenticado-como-viewer (decisão pendente — exige restaurar password segregation que foi removida pelo codex em `6fd0bac` 2026-05-18).

**Operações requeridas** (cada uma no contexto do cliente):

- Adicionar **target primário** — cria target global + atribui ao `target_keys` do profile alvo
- Remover **target primário** — remove do `target_keys` (target global pode permanecer no catálogo)
- Transformar **target primário em secundário** (promote/demote) — opera global, mas a UI mostra resultado dentro do contexto do profile
- Adicionar **target secundário** — cria + atribui (essa parte teve bugs graves; revisão completa exigida)
- Arquivar/restaurar target — opera global, atribuição persiste

Cada operação precisa:

1. Funcionar end-to-end (UI → ingest → filtro → export — não só "aparecer na lista")
2. Atribuir automaticamente ao profile do contexto atual (`target_keys` patch atômico)
3. Produzir **mensagens de erro claras** (ex: "target já existe", "nome conflita com homônimo", "ingest não conseguiu encontrar nenhuma fonte pro nome X")
4. UI **visível no contexto do cliente** — quando admin entra em simulação `?as_profile=flavio`, o `.add-target-box` e `.manage-targets-box` ficam visíveis (não escondidos pelo CSS `viewer-readonly`)

**Failure cases:**
- clicar "adicionar target" e ver spinner infinito ou erro genérico "something went wrong" sem indicação de qual etapa falhou
- adicionar target no contexto de flavio e o target NÃO aparecer no `flavio.target_keys` (assinatura silenciosa de regressão da atribuição automática)
- admin em modo simulação `?as_profile=flavio` ver `.add-target-box` escondido → não consegue gerenciar targets do flavio sem sair do contexto (regressão atual em 2026-05-20, corrigida nesta rodada)

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
