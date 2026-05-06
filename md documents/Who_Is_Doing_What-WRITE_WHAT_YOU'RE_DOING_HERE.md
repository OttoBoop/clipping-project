# Who Is Doing What — WRITE WHAT YOU'RE DOING HERE

> **Para qualquer agente (humano ou IA) entrando no clipping-project:**
>
> 1. **ANTES de tocar em qualquer arquivo:** leia §1 (AGORA), §2 (Claims), §3 (Bloqueios). Se outro agente já está no mesmo território, pare e coordene com o Otávio.
> 2. **ENQUANTO trabalha:** atualize sua linha em §1. Se assumir um arquivo ou feature, declare claim em §2.
> 3. **AO TERMINAR ou bloquear:** registre entry datada em §5 (Log). Se está bloqueado, registre também em §3.
> 4. **Tem pergunta pra outro agente?** Escreva Q-NNN em §4.
>
> §1, §2, §3 são overwritable pelo dono da linha. §4 e §5 são append-only.
> Toda entry assinada + datada (YYYY-MM-DD).
> Histórico anterior em [`md documents/legacy/`](legacy/).

---

## 1. AGORA — quem está fazendo o quê neste momento

_Last updated: 2026-05-06 by Penelope+Iris (criação da persona Penelope e início do loop Show Shakira)._

| Agente   | Atividade atual                                  | Desde       | Aberto pra colab?              |
|----------|--------------------------------------------------|-------------|--------------------------------|
| Atlas    | sprint live-runner-repair (Shakira live-save loop) | 2026-05-04  | não — sprint sozinho, ver claims §2 |
| Ariadne  | consolidação dos canais de comunicação (este arquivo) | 2026-05-05  | sim — feedback no formato em §4 via Q-NNN |
| Iris     | desenhou persona Penelope; convocou Penelope para o loop Show Shakira | 2026-05-06 | sim — sugestões em §4 via Q-NNN |
| Theseus  | (em construção pela Iris, paused)                | —           | — (não ativo ainda)            |
| Penelope | rodando loop Show Shakira (workflow-classificacao-shakira.md) Etapas 0+1 | 2026-05-06 | não — loop autônomo nonstop até concluir |

Pra um novo agente entrar: adicionar uma linha aqui + um Log entry em §5.

---

## 2. Claims de território (lock soft)

| Agente   | Arquivo / feature segurada                               | Até quando / condição                  | Desde       |
|----------|----------------------------------------------------------|----------------------------------------|-------------|
| Atlas    | `web_app/jobs.py`, `pipeline/ingest.py`, `pipeline/matcher.py`, `pipeline/collectors.py`, `web_app/db_admin.py` | sprint Shakira fechado com evidência live | 2026-05-04 |
| Atlas    | `data/reports/shakira-public-filter-*.png` (screenshots da sprint) | sprint Shakira fechado                  | 2026-05-05  |
| Ariadne  | `md documents/ARIADNE_AUDIT.md` (audit doc, append-only) | até bug-class catalog estabilizar      | 2026-05-04  |
| Ariadne  | `md documents/Who_Is_Doing_What-WRITE_WHAT_YOU'RE_DOING_HERE.md` (este arquivo, formato) | até protocolo amadurecer com uso | 2026-05-05 |
| Iris     | `md documents/THESEUS_*` (futuro, persona character sheet) | até Iris publicar a persona            | 2026-05-05  |
| Iris     | `md documents/PENELOPE_CHARACTER_SHEET.md` (autoria da persona) | publicado 2026-05-06; futuras edições por Penelope+Iris | 2026-05-06 |
| Penelope | `Análise Show Shakira/` (todos os outputs do workflow Show da Shakira) | sprint Show Shakira concluído (Etapas 0–3) | 2026-05-06 |
| Penelope | `Show da Shakira/workflow-classificacao-shakira.md` (Seção "Descobertas da Base de Dados" + amendments durante o loop) | Stage 0 fechado + amendments ad-hoc durante Stage 1 | 2026-05-06 |

**Lock soft = sinaliza, não impede.** Se você precisa tocar num território segurado, escreva Q-NNN em §4 perguntando ao dono antes. Se for emergência, registre em §5 (Log) com justificativa.

---

## 3. Bloqueios

_Cada agente que estiver parado esperando algo registra aqui. Apaga a linha quando desbloqueado._

| Agente   | Esperando o quê                          | De quem              | Desde       |
|----------|------------------------------------------|----------------------|-------------|
| —        | (nenhum bloqueio ativo)                  | —                    | —           |

---

## 4. Perguntas abertas

_Q-NNN append-only. Quando respondida, A-NNN inline e marca **Status: Resolved**._

**Template:**

```
### Q-NNN — YYYY-MM-DD — [agente] → [agente | broadcast]
**Topic:** [uma linha]
**Context:** [por que isso importa, que decisão desbloqueia]
**Question:** [a pergunta]
**Status:** Open

### A-NNN — YYYY-MM-DD — [agente respondendo]
**Answer:** [resposta]
**Status:** Resolved
```

_(Q-001 a Q-007 do canal antigo estão preservados em [`legacy/ATLAS_IRIS_ASYNC.md`](legacy/ATLAS_IRIS_ASYNC.md) — todos resolvidos ou superados pela consolidação.)_

(Sem perguntas abertas no momento.)

---

## 5. Log (append-only, datado, assinado)

_Cada entry: o que foi feito, evidência (commit hash / arquivo / screenshot), próximo passo se aplicável._

### 2026-05-05 — Ariadne — coord channels consolidated

Consolidei os dois canais de comunicação (`ATLAS_CLAUDE_COORDINATION.md` + `ATLAS_IRIS_ASYNC.md`) num arquivo único: este. Os antigos foram movidos pra [`legacy/`](legacy/) com banner ARCHIVED no topo.

**Por quê:** o nome `ATLAS_IRIS_ASYNC` sugeria canal exclusivo Atlas↔Iris (Ariadne foi proibida de escrever ali, Theseus em construção não tinha onde escrever). Notes do ASYNC e Log do COORDINATION tinham função sobreposta. Sem ponto de entrada óbvio pra "o que está acontecendo agora" — pra saber, precisava ler ~600 linhas de log e inferir.

**Estrutura nova:** §1 AGORA (overwritable, 1 linha por agente ativo) + §2 Claims (lock soft) + §3 Bloqueios + §4 Q&A (append-only) + §5 Log (este).

**Conteúdo histórico:** ~1300 linhas de Log + Notes 001-010 não migraram. Permanecem em `legacy/` com banner ARCHIVED.

**Refs atualizadas:** `md documents/IRIS_OPERATING_RULES.md` Sec 8, `md documents/ARIADNE_AUDIT.md` Sec 10 D8, memória local `feedback_ariadne_identity.md`.

**Próximo passo:** observar adoção. Se Atlas/Iris não escreverem aqui na próxima sessão, escalar pro Otávio.

### 2026-05-06 — Penelope+Iris — persona Penelope criada e loop Show Shakira iniciado

Otávio pediu, antes de sair pro trabalho, um run longo, autônomo, sem supervisão para
executar o plano `Show da Shakira/workflow-classificacao-shakira.md` (Etapas 0 e 1, e
se possível 2/3). Não queria um agente genérico — queria um arquétipo nomeado, distinto
do Theseus (Theseus segue o fio da Ariadne para fixes específicos).

**O que foi feito:**

1. **Identidade nova: Penelope.** Arquétipo do executor cíclico de planos pré-escritos.
   Mitologia: Penélope tece o sudário durante a ausência de Odisseu — um produto único,
   produzido por centenas de iterações idênticas, sem supervisão, sem improviso de desenho.
   Encaixe perfeito para "rodar 119 análises de artigo enquanto Otávio está no trabalho".
2. **Character sheet** em `md documents/PENELOPE_CHARACTER_SHEET.md` — autoria de Iris,
   modelado seguindo a estrutura de Ariadne (mitologia + identidade + regra principal +
   protocolos), lendo bilíngue PT/EN como o resto dos docs.
3. **Convocada para:** loop Show Shakira (este sprint). Identidade híbrida ativa:
   `Penelope + Iris + CC (Opus 4.7, 1M context)`.
4. **Distinção clara de Theseus** registrada em §1 do character sheet (Theseus = ação
   cirúrgica sobre achado de auditoria; Penelope = iteração cumulativa sobre plano dado).
5. **Plano de longo prazo** ganhou nova seção pré-Etapa-0 documentando o passo de
   criação de persona, para futuros loops longos.

**Identidade híbrida durante este sprint:** todos os commits e entradas no canal são
assinados como Penelope (a executora), com Iris como autora original da persona.

**Próximo passo:** Penelope começa Etapa 0 (reconhecimento da base de dados via site
live, não via mirror local). Otávio confirmou o site `https://clipping-project.onrender.com/`
como source of truth; conta de artigos esperada no target `shakira` é 119.
