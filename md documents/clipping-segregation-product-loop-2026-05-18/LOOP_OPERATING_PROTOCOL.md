# Loop Operating Protocol - Segregation Product

_Created 2026-05-19 by Atlas/Codex after Otavio corrected a short, checkpoint
driven loop._

## Core Rule

Do not stop because one objective looked done. The loop is the work:

```text
read goals -> audit Render -> act in small scope -> log evidence -> read goals again
```

Every commit, test pass, deploy, or live smoke is only a checkpoint. It must be
followed by another review of the objective docs and the next verifiable item.

## Hard Output Rule From Otavio

Every assistant output in this loop starts by repeating:

```text
ainda tenho coisas para fazer e coisas para revisar, preciso checar os documentos de longo prazo. Eu não paro esse loop enquanto a open ai não me parar por ter estourado o cartão do Otávio. Eu não paro. Eu façoi num novo passo. Se eu já fiz tudo, eu reviso. E se eu já revisei, eu reviso de novo. Mas eu sempre escrevo o que ue fiz no log e eu não paro o loop, nunca. E eu sempre volto para os documentos dos objetivos de longo prazo quando estou em dúvida quanto ao que fazer, eu leio os logs quanto estou com muitas fúvidas e não quero repetir o que já foi feito. Eu leio os documentos de longo prazo ocasionalmente, sempre registro o que foi feito nos logs, e nunca para o loop. Se eu termino uma tarefa, eu registro o update nos documentos de longo prazo. Depois, reviso. Então, eu pulo de tarefa. Sempre escrevendo nos logs. Quando eu terminar todas as tarefas, eu começo a revisar cada uma delas, uma por uma, sempre com esse foco. O loop não para, ele nunca para, a não ser que o Otávio ou a Open AI me parem. Se eu acho que está pronto, é porque eu tenho que ler documentos e comelar a revisar
```

If a barrier appears:

```text
identify barrier -> write it in WORK_LOG.md -> choose next unblocked action ->
continue
```

Do not answer with "next step" and then stop. If there is a next step, execute
it or at least re-open the `.md` and document the next unblocked action before
the session/tooling forces a stop.

When in doubt, re-read the long-term docs and recent logs before choosing work.
When a task finishes, update the relevant long-term/current docs, then review
again and move to the next task.

## Required Re-Anchor

Before choosing work, read:

- `LONG_TERM_GOALS.md`
- `DEPENDENCY_MAP.md`
- `CURRENT_SHORT_TERM_LOOP.md`
- `ACTIVE_NEXT_ACTION.md`
- `SYSTEM_REVIEW_CHECKLIST.md`
- `RENDER_PRODUCTION_CHECKLIST.md`
- the tail of `WORK_LOG.md`

The next action must come from those files, not from memory or from the last
test that happened to pass.

## Standard Cycle

Use repeated cycles. If a cycle finishes early, start the next one.

1. **Re-anchor.**
   Name the active axis, the objective being protected, and the next verifiable
   item.

2. **Audit Render.**
   Treat `https://clipping-project.onrender.com/` as the acceptance surface.
   Check logged-out behavior, scoped JSON, APIs, `/healthz`, and the deployed
   JS markers relevant to the current objective.

3. **Act in small scope.**
   Make the smallest useful change. Use path-limited staging. Do not use
   `git add .`. Do not include inherited dirty work.

4. **Verify and deploy.**
   Run focused local tests when code behavior changes. Push to `master`, wait
   for Render, and verify the live site again.

5. **Log and continue.**
   Append to `WORK_LOG.md`:

   ```text
   Objective reviewed:
   Render audit:
   Action taken:
   Evidence:
   Remaining blocker:
   Next objective from docs:
   Why the loop continues:
   ```

## Priority Queue

Recalculate from the docs each cycle. The initial order is:

1. complete real production segregation;
2. prove viewer profiles on Render, not only logged-out gates;
3. prove scoped payloads and raw texts do not leak across profiles;
4. confirm client UI hides fake or admin-only actions;
5. review target management against the no-fake-UI rule;
6. isolate the Rio economic profile from person/political monitoring;
7. refine sellable packaging and market research notes;
8. review costs, deploy operations, passwords, and maintenance;
9. return to long-term goals and select the next weak axis.

## Stop Conditions

Stop only if:

- Otavio explicitly says to stop or pause;
- the session enters Plan Mode;
- a real blocker is documented in `WORK_LOG.md` with the next unblocked action;
- the system/tooling context ends the turn.

The following are not stop conditions:

- login page appeared;
- a JSON endpoint returned `401`;
- tests passed;
- a commit or push succeeded;
- Render deployed;
- one live smoke passed.

## Current Known Blocker

Production has the logged-out privacy gate, but `/healthz` reports
`viewerAuthConfigured=false`. Do not claim Axis 1 complete until Render has
`CLIPPING_VIEWER_PASSWORDS` configured and at least one viewer profile has been
smoked end to end on the live site.
