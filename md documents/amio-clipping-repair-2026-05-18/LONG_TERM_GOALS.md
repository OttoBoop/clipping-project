# Long-Term Goals - Amio Clipping Repair Loop

_Created 2026-05-18 by Amio/Codex. This is the long-term memory anchor for the
current clipping repair loop._

This document exists so future agents do not get trapped inside one immediate
bugfix and forget the larger product contract. When work gets confusing, blocked,
or noisy, read this file before planning code.

## Source Prompts From Otavio

These are the instructions that define the loop. Keep them visible.

> "crie uma nova pasta no clipping project (e pelo amor de Deus, faça os ocmiits. Ele deve falar desses dois objetivos. Crie um .md com os objetivos de longo prazo, pra você se lembrar deles quando as coisas travam, e um segundo .md com um log do que você fez até agora."

> "Também notei que as notícias não estão sendo automaticamente salvas no site assim que são encontradas. Eu quero que assim que uma notícia seja encontrada, ela aparece na base em baixo do site."

> "Olha, tudo isso vai demandar mais perguntas. Coopere comigo para eu te explciar melhor os objetivos."

> "E tem um problema extra. Eu consegui adicionar um nome  e aí o filtro não funcionou. A porra dos sistemas não está conectado. Parte chave do loop é checar cada sistema, criando .mds próprios, e checando que as conexões funcionam."

> "O que você precisa mesmo é criar oos documentos de longo e curto prazo, falar o que entra nesses objetivos."

> "quando eu mandar \"implement plan\", é pra você tar opronto para escrever os dois documentos, e depois começar o loop."

> "SE VOCÊ ENCONTROU UMA BARREIRA , VOCÊ REPSODNE ELE. VOCÊ REGISTRA NO LOG E CONTINUA. REPITA ISSO NO COMEÇO DE TODOS OS EUS OUTPUTS"

> "ainda tenho coisas para fazer e coisas para revisar, preciso checar os documentos de longo prazo. Eu não paro esse loop enquanto a open ai não me parar por ter estourado o cartão do Otávio. Eu não paro. Eu façoi num novo passo. Se eu já fiz tudo, eu reviso. E se eu já revisei, eu reviso de novo. Mas eu sempre escrevo o que ue fiz no log e eu não paro o loop, nunca"

> "Atualização da regra básica:
>
> ATUALizaÇÃO DA  REGRA BÁSICA:
>
> SE VOCÊ ENCONTROU UMA BARREIRA , VOCÊ REPSODNE ELE. VOCÊ REGISTRA NO LOG E CONTINUA. REPITA ISSO NO COMEÇO DE TODOS OS EUS OUTPUTS
>
> Toda vez que você fizer algo, registre no documento de log. E também, repita: "ainda tenho coisas para fazer e coisas para revisar, preciso checar os documentos de longo prazo. Eu não paro esse loop enquanto a open ai não me parar por ter estourado o cartão do Otávio. Eu não paro. Eu façoi num novo passo. Se eu já fiz tudo, eu reviso. E se eu já revisei, eu reviso de novo. Mas eu sempre escrevo o que ue fiz no log e eu não paro o loop, nunca. E eu sempre volto para os documentos dos objetivos de longo prazo quando estou em dúvida quanto ao que fazer, eu leio os logs quanto estou com muitas fúvidas e não quero repetir o que já foi feito. Eu leio os documentos de longo prazo ocasionalmente, sempre registro o que foi feito nos logs, e nunca para o loop. Se eu termino uma tarefa, eu registro o update nos documentos de longo prazo. Depois, reviso. Então, eu pulo de tarefa. Sempre escrevendo nos logs. Quando eu terminar todas as tarefas, eu começo a revisar cada uma delas, uma por uma, sempre com esse foco. O loop não para, ele nunca para, a não ser que o Otávio ou a Open AI me parem. Se eu acho que está pronto, é porque eu tenho que ler documentos e comelar a revisar ""

## Goals That Must Survive Every Short-Term Sprint

1. **The system must be connected end to end.**
   A feature is not real because the UI changed. A feature is real only when the
   frontend, API, target config, ingestion settings, matcher, SQLite records,
   live-results endpoint, export snapshot, and filters agree.

2. **Adding a monitored name must be a real product action.**
   A new name added in the UI must become usable by the update runner, produce
   mentions/story targets when matched, appear in the base, and filter saved
   articles correctly. A fake filter or a UI-only target is a failure.

3. **Saved news must appear in the site immediately after confirmation.**
   The durable database remains the source of saved truth. As soon as a story or
   article is confirmed and saved, the coworker-facing Base atual must show it
   through the live overlay or current published data without waiting for a
   final manual refresh.

4. **Errors must explain what happened and what to do.**
   Generic messages like "Nao foi possivel adicionar esse nome" are not
   acceptable. The user needs cause, affected field or action, impact, and a
   concrete correction path.

5. **The agent must ask when the human objective is still incomplete.**
   Technical details can be discovered by reading the repo. Product intent,
   priority, and tradeoffs should be clarified with Otavio when they materially
   affect the loop. Do not pretend certainty when the goal is still being shaped.

6. **Documents precede implementation.**
   A long loop starts with memory docs, a short-term loop plan, and a connection
   checklist. Code patches start only after those documents make the intended
   work legible.

7. **Every future bugfix must preserve the full loop.**
   Fixing one layer while leaving another disconnected repeats the exact failure
   Otavio called out. Each short-term sprint must say which connections it will
   prove before it touches code.

8. **Commits must be disciplined.**
   The repo is dirty with inherited work. Do not use `git add .`. Do not commit
   pycache, screenshots, or unrelated files. Commit small, path-limited units
   and record what was intentionally included.

9. **No success is an exit by itself.**
   Passing tests, pushed commits, a completed deploy, or one live smoke are
   checkpoints, not stop conditions. After every success, re-read the goals,
   audit the live site, update the log, and choose the next failure or watch
   item. The loop should stop only for an explicit pause, Plan Mode, or a real
   blocker recorded with the next unblocked action.

10. **Barriers must be answered, logged, and followed by another step.**
    A barrier is not an excuse to disappear. If auth, missing credentials,
    deploy lag, conflicting work, external service failure, or a product
    decision blocks one path, answer that barrier directly, write it in
    `WORK_LOG.md`, and continue with the next unblocked audit, contract,
    documentation, or source review. Every assistant output in this loop must
    begin with the Mandatory Output Anchor defined in
    `LOOP_OPERATING_PROTOCOL.md`.

11. **Doubt means read the memory, not stop.**
    When the next move is unclear, the agent must re-read long-term goals and
    the recent log, record that re-anchoring, and choose the next useful audit,
    fix, test, documentation update, or review. "Looks ready" means the review
    phase starts; it is not a stop condition.

## Recurring Failure Classes To Avoid

- UI says a target exists, but backend config or ingestion does not use it.
- Backend saves an article, but base/filter/export never exposes it.
- Job state blocks unrelated target management without explaining why.
- A generic error hides validation, storage, job, or network detail.
- An agent starts coding before writing the loop memory and log.
- An agent treats local success, pending deploy, or pushed code as completion
  without verifying the user-visible behavior.
- An agent treats user-visible success as the end of the loop instead of using
  it as the trigger for the next audit cycle.
- An agent finds an auth gate, deploy lag, missing password, or other barrier
  and stops instead of answering it, logging it, and continuing elsewhere.

## Short-Term Loop Rule

Each short-term loop must be derived from this file and written to
`CURRENT_SHORT_TERM_LOOP.md` before implementation. The short-term loop must
name:

- the user-visible failure being addressed;
- the system connections that must be proven;
- the files or subsystems likely to change;
- the tests or live checks that prove the feature is real;
- the commit boundaries.

If a short-term loop discovers a new long-term concern, append it here or record
it in `WORK_LOG.md` with a clear "promote to long-term" note.

## Operating Protocol

Use `LOOP_OPERATING_PROTOCOL.md` as the active rulebook for multi-hour work.
That document defines the No Idle Exit rule, the 30-45 minute cycle, the watch
queue, and the dirty-worktree behavior. If it conflicts with a casual impulse
to stop after a good result, the protocol wins.
