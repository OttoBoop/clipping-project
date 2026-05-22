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
- Visualização de registros de atividade dos clientes — quem logou, quando, quais mutações fez. *(Entrega dedicada no Goal 6; esta linha sinaliza que admin UI inclui isso como parte do onboarding completo.)*

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

**Atores que podem mutar** (fase 2 do Goal 5, 2026-05-20):

1. **Viewer autenticado-como-viewer** (cliente real loga com sua senha, ex: Flávio com `flavio-gabinete-2026`) — muta targets DENTRO do scope do `target_keys` dele. Backend `_validate_target_scope` retorna 403 `target_out_of_scope` se viewer tentar editar/arquivar target fora do scope. Novos targets criados pelo viewer entram automaticamente no scope dele.
2. **Admin via simulação `?as_profile=X`** — modelo single-admin para uso pelo dono do sistema operar no contexto de cada cliente. Mutação atribui ao profile alvo via `add_target_to_profile`. UI esconde `#manageViewersBox` em simulação.
3. **Admin sem simulação** — opera no catálogo global de targets. Nenhuma atribuição automática; usa `/api/admin/viewers` PATCH para atribuir manualmente quando necessário.

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
- admin em modo simulação `?as_profile=flavio` ver `.add-target-box` escondido → não consegue gerenciar targets do flavio sem sair do contexto (regressão de 2026-05-20 fase 1, corrigida em commit `39dcd0c`)
- **Flávio logar com `flavio-gabinete-2026` e NÃO conseguir adicionar/editar targets dele** — sentido absurdo "cliente precisa de senha de admin pra gerenciar seu próprio scope" (regressão de 2026-05-20 fase 1, corrigida na fase 2)
- viewer (ex: Flávio) editar/arquivar target de OUTRO cliente (ex: shakira) — deve retornar 403 `target_out_of_scope` com mensagem clara, não 500 nem sucesso silencioso

### Goal 6 — Visualização de registros de atividade

Admin (e eventualmente cada cliente sobre o próprio scope) consegue ver histórico de quem logou, quem mudou senha, quem criou/arquivou/promoveu/rebaixou target, quem criou/editou/arquivou cliente. Captura é estruturada em DB (tabela `activity_log`), API expõe via `GET /api/admin/activity` com filtros (action, profile, since, limit), UI mostra como seção do painel admin.

**Pedido literal do Otávio (2026-05-19T13:12, prompt #3):**

> *"Uma tela de registros também seria muito bom."*

**Atores que podem ler:**
1. **Admin** — vê tudo, todos os perfis, todas as ações.
2. **Viewer** *(pendência futura — não bloqueia atingimento da fase 1)* — vê só registros do seu próprio scope (read-only).

**Eventos capturados (mínimo):**

- `login.success` / `login.fail`
- `logout`
- `change_password`
- `target.create`, `target.create_primary`, `target.update`, `target.promote`, `target.demote`, `target.archive`, `target.restore` (com `assignedTo` / `removedFrom` quando aplicável)
- `viewer.create`, `viewer.update`, `viewer.archive`

**Failure cases:**

- admin abre painel e seção de registros não carrega
- mutação acontece mas não vira linha em `activity_log` (silent miss)
- filtros voltam resultado errado (`?profile=flavio` retornando ações de shakira)
- histórico pré-implementação está perdido — limitação aceita; documentar publicamente.

**Pendências fechadas (2026-05-22):**

- ✅ Capturar tentativas bloqueadas por scope (commit `7ed465e`)
- ✅ UI viewer-próprio-histórico read-only via `GET /api/me/activity` (commit `eb49dc0`)

**Pendência ainda aberta:**

- Política de retenção / rotation (hoje `activity_log` cresce indefinidamente)

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
