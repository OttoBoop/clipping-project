# Long-Term Goals - Clipping Segregation And Product Loop

_Created 2026-05-18 by Atlas/Codex. This is the long-term memory anchor for
turning the clipping tool into a password-gated, segmented, sellable product._

This document exists so future agents do not reduce the work to a narrow auth
patch or another visual filter. When the project gets noisy, blocked, or split
across agents, read this before planning implementation.

## Source Prompts From Otavio

These are the human instructions that define the loop:

> "Eu preciso criar um indicador economico baseado na minha clipping tool, para toda a cidade do Rio."

> "Mas acima disso, eu preciso fazer uma segregacao dos dados, pra nao sujar o site focado no Flavio."

> "Me recomendaram que eu fizesse uma versao segregada do site e vendesse para outros politicos."

> "A principal tarefa agora e conseguir segregar o site. A gente pode usar esse site como base e colocar um sistema de senhas, que permite que cada cliente veja apenas as noticias que lhe interessam."

> "No fundo, tudo tem o mesmo backend."

> "Para um bom loop, a gente precisa criar um documento com objetivos de longo prazo claros, pontos de revisao objetivos e sistemicos e um log de acoes ja testadas."

> "Muito do site foi feito com ias que nao ligaram bem os pontos. Entao, por exemplo, tem toda uma ui para adicionar novos candidatos, mas ela na verdade e falsa!"

## Goals That Must Survive Every Sprint

1. **Segregation is a product promise, not a frontend trick.**
   A viewer must only receive data allowed for that viewer. Hiding extra rows in
   the browser is not enough.

2. **The same backend may serve multiple products.**
   Flavio, Shakira, Rio economic monitoring, and future clients can share the
   pipeline, storage, and codebase, but their views must not visually or
   materially contaminate each other.

3. **Login must map to an explicit viewer profile.**
   A password is useful only if it identifies which profile/workspace the user
   belongs to and what targets/projects that profile may see.

4. **Visual cleanliness matters.**
   A huge list of secondary targets or filters makes the product feel broken.
   Segmentation must keep each profile's target list small and relevant.

5. **The product must be sellable.**
   Future political clients should receive a private, credible clipping view.
   The system should help Otavio fund the tool instead of creating more manual
   work and AI-tool cost.

6. **No fake UI.**
   If a button, filter, add-target form, update action, classification control,
   or export exists for a profile, it must be connected through UI, API,
   target config, ingestion, matcher, SQLite, live results, and payload
   rendering. If not connected, hide it or mark it unavailable.

7. **The Rio corpus is an active production track (superseded 2026-07-14).**
   The old goal of deriving a precise economic indicator from a small set of
   stories is no longer the ingestion objective. `rio_economico` now owns a
   high-recall, auditable municipal corpus from 2011 onward. Tourism, events,
   hotelaria and a future economic indicator are dimensions derived after
   collection; they must never be gates that discard the broad corpus.

8. **Docs and logs precede implementation.**
   Each technical loop starts with memory docs, a current short-term loop,
   a review checklist, and a work log. Code begins only after the loop can be
   understood by another agent.

9. **Coordinate with active AI work.**
   This repo is dirty and other agents may be active. Do not overwrite Shakira
   debug work, inherited diffs, or shared coordination files casually.

## Recurring Failure Classes To Avoid

- The dashboard loads all client data and relies on frontend filters to hide it.
- A profile sees targets, filters, classifications, raw texts, or live results
  outside its scope.
- Logged-out users can fetch JSON payloads directly.
- Adding a target creates UI state but does not affect collection, matching,
  saved mentions, stories, live results, export, or scoped payloads.
- A client view exposes operator controls that only Otavio/admins should use.
- A new repo/site is created before the current backend can prove segregation.
- Agents treat "it should work after deploy" as completion without tests or
  live verification.

## Short-Term Loop Rule

Each short-term loop must be derived from this file and written to
`CURRENT_SHORT_TERM_LOOP.md` before implementation. The short-term loop must
name:

- the product promise being protected;
- the system connections that must be proven;
- the user profiles or scopes involved;
- the APIs and payloads that must not leak data;
- the test or smoke evidence required before closing;
- the commit boundaries.

If a sprint discovers a new long-term concern, append it here or record it in
`WORK_LOG.md` with a clear "promote to long-term" note.

## Superseding Rio Corpus Decision - 2026-07-14

This section supersedes every older Rio document where the project is called a
"future track", a dry run, a six-story sample, or an indicator-first workflow.
Those files remain historical evidence, not current operating instructions.

The durable contract is:

1. `rio_economico` remains an isolated viewer profile and is not a row in
   `data/targets.json`.
2. `rio_city_corpus` is collected into a dedicated PostgreSQL ledger and queue.
   Existing political profiles remain on the legacy SQLite pipeline while the
   migration is staged.
3. Discovery observations, fetch attempts, canonical articles, content
   objects, geographic evidence, dimensions, and source-window coverage are
   separate records. Re-runs add observations without duplicating articles.
4. A source window is successful only when it is demonstrably exhausted or
   empty. Caps, partial pagination, blocked access and swallowed errors are not
   `complete`.
5. `body_extracted` requires article/API body text, `final_url_resolved`
   requires a vehicle URL, and `page_date_verified` requires page/API evidence.
   Feed dates and snippets remain explicitly weaker evidence.
6. City-focused sources are collected broadly. State sections are collected by
   editorial path and classified after body download. Other Rio de Janeiro
   municipalities provide negative evidence but are never automatic title
   blacklists.
7. Backfill work runs in a background worker with PostgreSQL leases and
   checkpoints. The web process starts and observes work; it does not own a
   year-long thread or upload the whole SQLite database on every checkpoint.
8. The Rio panel reads paginated corpus and coverage APIs, not a static JSON
   export capped at 20,000 articles.
9. Local tests protect implementation. Acceptance requires authenticated live
   Render evidence, including login/CSRF and the real password-change contract.
10. The operating target is at least 200,000 unique `confirmed + probable`
    municipal articles. A smaller exhausted universe is reported honestly and
    expanded with additional sources; duplicates never count toward the goal.
