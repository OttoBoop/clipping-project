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

## Recurring Failure Classes To Avoid

- UI says a target exists, but backend config or ingestion does not use it.
- Backend saves an article, but base/filter/export never exposes it.
- Job state blocks unrelated target management without explaining why.
- A generic error hides validation, storage, job, or network detail.
- An agent starts coding before writing the loop memory and log.
- An agent treats local success, pending deploy, or pushed code as completion
  without verifying the user-visible behavior.

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
