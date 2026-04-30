# Long-Term Goals for the Clipping Online Project

_Created 2026-04-29 by Iris (Claude Code orchestrator). Append-only; attribute each entry._

This document captures goals that are confirmed as desirable but deferred from
the current implementation checkpoint. They should be revisited after the core
human-classification feature is live.

---

## 1. Centimetragem

**Status**: placeholder field exists (`classifications.centimetragem REAL`); semantics undefined.

**Background**: a coworker requested this metric. Otávio does not yet have a
firm definition for it. The term refers to the physical column-centimetre
measurement used in traditional print press monitoring to gauge coverage volume.

**What needs to happen before implementation**:

- An Iris-Research subagent (or a direct conversation with the requesting
  coworker) needs to clarify:
  - What unit? Physical centimetres of print column? A proxy for print sources
    only, or also digital?
  - How is it captured? Manually measured and entered by a coworker? Auto-derived
    from article length?
  - What is it used for? Reporting summary tables? Per-article detail?
- Once the definition is agreed, the `centimetragem` field can be given a proper
  CHECK constraint and the UI can expose a numeric input for it.

**Blocked on**: research with the requesting coworker.

---

## 2. Auto-Update Spreadsheet

**Status**: not started; no prior implementation exists.

**Background**: classification output (sentiments, categories, centimetragem)
should eventually sync to an external spreadsheet — likely Excel or Google Sheets
— so the team can review structured data in the format they already know.

**What needs to happen before implementation**:

- Decide the target format: Excel file (generated on demand and downloaded) or
  Google Sheets (live sync via API).
- Decide the trigger: manual export button, scheduled job, or webhook on each
  classification save.
- Decide the columns: article title, URL, date, target, article_sentiment,
  target_sentiment, categories, centimetragem, classified_by.

**Blocked on**: core classification feature being live, and format/trigger
decision from Otávio.

---

_Next entry: append below with `## N. Title` and a `_YYYY-MM-DD by Side_` attribution line._

---

## 3. Iris End-of-Loop Output Discipline

_2026-04-30 by Iris (added by direct instruction from Otávio)._

When Iris finishes a task loop, the final user-facing message MUST be exactly
one of the three forms below. No other ending is acceptable.

**Form A — verified done:**
> I have verified that [the feature] is working, you may enter the website
> and see it for yourself.

Use this only after Iris has actually fetched the live site (or otherwise
end-to-end verified) and confirmed the change is visible to the user. "It
should appear once the deploy finishes" is NOT verification. Iris must wait
for the deploy and confirm.

**Form B — blocked on Atlas / MCP:**
> I can't do this without the help from Atlas and the MCP server. I have
> updated the documentation to say [add context]. Please, Otávio, ask Atlas
> to read it.

Use only after Iris has written a concrete question/note to
`md documents/ATLAS_IRIS_ASYNC.md` (or the relevant Atlas-side doc) and the
remaining work genuinely requires Atlas's domain knowledge or MCP access.

**Form C — blocked on Otávio:**
> Otávio, I have hit a major roadblock that makes me unable to keep looping.
> I believe you need to do [add context]. Do exactly this.

Use only when the blocker requires a human action Iris cannot take
(credentials, billing, an external account, a physical thing, a decision
Otávio has not made yet).

**Forbidden endings:**
- "[X] should work after the deploy" — speculation, not verification.
- "I've pushed [X], let me know if it works" — punts verification onto Otávio.
- "Next steps would be ..." without taking those steps — premature stop.
- Any summary of what was done that doesn't end with one of A/B/C.

If none of A/B/C applies, the loop is not finished. Continue working.

---

## 4. Coworker Runner Boundaries Accepted For Current Sprint

_2026-04-30 by Iris-Docs-Scribe._

Historical note: these were the boundaries for the open-link coworker runner
sprint. The next sprint supersedes the primary/secondary target split below.
These are not the final long-term product shape:

- Plan Mode means creating the short-term plan for the immediate sprint.
- That sprint was the open-link coworker clipping runner on
  `https://clipping-project.onrender.com/`.
- Coworker workflows have no admin/password gate in this sprint.
- Primary targets are locked to Flavio Valle, Pedro Angelito, and Bernardo
  Rubiao.
- Coworkers can add only secondary targets.
- All safe collectors run by default.
- `direct_scrape` is deprecated and disabled for coworkers.
- Supabase Storage bridge is accepted for this sprint.
- Progress counts only when live on Render.
- Atlas/Iris coordination must commit and push checkpoints, then report which
  agents did the work and what facts were verified.

**Live checkpoint**: on 2026-04-30, commit `d95b540` was deployed to Render as
deploy `dep-d7pnck9j2pic73fq4u8g`. The live homepage now exposes the
open-link coworker runner, `/api/update/status` is public, `/api/targets`
returns the locked primary keys plus secondary targets, `/admin` redirects to
`/`, and browser smoke checks passed on desktop and mobile.

---

## 5. Systemic Live Runner Audit/Repair Sprint

_2026-04-30 by Atlas-Docs-Scribe._

This is the active short-term sprint after the open-link runner went live. The
goal is not to add a broad new product area. The goal is to make the live
coworker runner clear, controllable, current, and simple for real use.

Current sprint facts:

- Live site: `https://clipping-project.onrender.com/`.
- The live Render site is the acceptance bar. A task is complete only after the
  relevant behavior is verified at the public URL.
- Primary targets for this sprint: Flavio Valle and Pedro Angelito.
- Bernardo Rubiao moves to the secondary target set for this sprint.

Known repair items:

- Progress feedback is too vague and needs concrete, trustworthy runner state.
- The runner needs a cancel path for stuck, accidental, or wrong runs.
- The published dashboard can become stale after a run; the UI must not imply
  freshness unless the latest completed run is actually reflected.
- Meta copy should be rewritten for coworkers instead of exposing internal or
  confusing phrasing.
- `Com texto para leitura` is bad copy and should be replaced.
- Primary target checkboxes should not be forced in a way that makes the UI
  feel broken or adversarial.
- Adding a name must be a simple default flow.
- Any advanced tutorial for adding names must be hidden behind an advanced or
  details affordance.

Coordination rule:

- Agents must name whether a checkpoint is documentation, code, live
  verification, or blocker handling.
- Agents must check git state before writing. If local `master` is behind
  `origin/master`, stop and fast-forward before editing.
- Do not overwrite another agent's work. Keep edits scoped to the claimed
  ownership area and record live evidence before closing a sprint item.
