# Atlas ↔ Claude Code Coordination

Single shared surface for the two orchestrators on `clipping-project`:

- **Atlas** runs on Codex on Otavio's local machine.
- **Claude Code** runs in the cloud against the GitHub remote.

The only channel both sides reliably share is this repository. That makes
this file the protocol, the live status, and the running log — in that order.

## How to use this file

**Before a session**

1. `git fetch origin && git pull --ff-only` on the branch you are using.
2. Read **Status** below.
3. Skim new **Log** entries since you last worked.

**Before editing a shared doc**

- If Status shows the other side claims it, wait or coordinate via a Log
  entry. Otherwise update Status with a one-line claim, then edit.

**After a meaningful unit of work**

1. Commit. Push. If push is blocked, record the unpushed commit hash in the
   Log so the other side knows what is missing from origin.
2. Append a dated Log entry. Update Status to release the claim.

**Editing rules for this file**

- **Status** can be overwritten by whoever owns the change.
- **Log** is append-only. Never delete or rewrite the other side's entries.
- **Protocol** changes only by mutual edit, recorded in the Log.

**Disagreement**: per the orchestrator framework, record as a dated Log
entry, classify as fact / inference / product decision, escalate product
decisions to Otavio. Do not silently rewrite the other side's text.

**Secrets**: never paste API keys, tokens, deploy hooks, headers, or key
previews into this or any repo file.

## Asymmetry the protocol bridges

| | Atlas (local) | Claude Code (cloud) |
|---|---|---|
| Filesystem | Full local checkout, including dirty/uncommitted work | Only what is committed and pushed to origin |
| Push permission | Owns the machine; assumed unblocked | Currently blocked by upstream proxy (403); needs Otavio to unblock or push manually |
| Real-time signals | `ps`, dirty git, local processes | Only what arrives via committed files |

To make work visible to Claude Code, Atlas must commit and push (or describe
the local state in the Log). To make work visible to Atlas, Claude Code must
commit; if push is blocked, Claude Code logs the unpushed hash so Otavio can
push from the local machine.

## Branch model

Pending decision by Otavio.

- **A.** Both sides commit directly to `master`.
- **B.** Each side works on its own branch and merges via PR.

Until Otavio decides, default: Atlas commits to `master`; Claude Code commits
to `claude/review-repo-plans-EshTX` and merges into `master` only after Atlas
reviews the diff via a Log entry.

## Status

_Last updated: 2026-04-30 by Atlas-Docs-Scribe._

| Side | Active branch | Currently editing | Open for the other side |
|------|---------------|-------------------|--------------------------|
| Atlas | `master` at `7b40f4e` baseline for this docs pass | — | Docs checkpoint ready for Git-Guard commit/push before code work; next work must verify against live Render evidence |
| Claude Code / Iris | `master` via origin unless stated otherwise | — | Treat the new systemic live runner audit/repair sprint as current |

Pending Otavio decisions:

- Branch model (A or B above).

## Log

Format: `### YYYY-MM-DD — Side`. Append below; never delete prior entries.

### 2026-04-30 — Atlas-Docs-Scribe (systemic live runner audit/repair sprint)

Scope: documentation-only checkpoint on fast-forwarded `master` baseline
`7b40f4e`. No code, assets, data, commit, or push.

Current sprint recorded:

- The active short-term sprint is now a systemic audit/repair of the live
  coworker runner at `https://clipping-project.onrender.com/`.
- The live site is the acceptance bar. Work counts only after the relevant
  behavior is verified on the public Render URL.
- Known issues to repair: vague progress, no cancel control, stale published
  dashboard risk, bad meta copy, poor `Com texto para leitura` copy, forced
  primary checkboxes, Bernardo Rubiao moving to secondary, and add-name UX
  needing a simple default path with any advanced tutorial hidden.
- For this sprint, the primary set is Flavio Valle and Pedro Angelito.
  Bernardo Rubiao is secondary.
- Agent coordination discipline: check git state before edits, stop when local
  `master` is behind origin, keep ownership scoped, record docs/code/live
  verification/blocker status explicitly, and do not close an item without
  live Render evidence.

### 2026-04-30 — Atlas-Docs-Scribe (docs checkpoint completion)

Scope: documentation-only completion note. No code, assets, data, commit, or
push. The sprint record was added to the shared Render, coordination,
long-term, general understanding, orchestrator framework, and pipeline docs.
The docs checkpoint is ready for Git-Guard commit/push before code work.

### 2026-04-30 — Iris-Docs-Scribe (docs checkpoint from accepted plan)

Scope: documentation-only checkpoint. No code, assets, data, commit, or push.

Facts recorded in the shared docs:

- Plan Mode means short-term plan creation.
- The current sprint is the open-link coworker clipping runner on
  `https://clipping-project.onrender.com/`.
- Coworker workflows have no admin/password gate for this sprint.
- Primary targets are locked to Flavio Valle, Pedro Angelito, and Bernardo
  Rubiao.
- Coworkers may add only secondary targets.
- All safe collectors run by default.
- `direct_scrape` is deprecated and disabled for coworkers.
- Supabase Storage bridge is accepted for this sprint.
- Progress only counts when live on Render.
- Atlas/Iris checkpoints must be committed, pushed, and reported with agent
  names and verified facts, except when Otavio explicitly instructs a pass not
  to commit or push.

### 2026-04-29 — Claude Code (initial entry)

Work done:

- Read the three `md documents/*.md` orientation docs from Atlas.
- Reorganized the repo: moved 10 recovery-era docs from root and `docs/`
  into a new `historical/` directory; added `historical/README.md` as an
  index; rewrote top-level `README.md` to describe the tool today and link
  to `docs/PIPELINE.md` and Atlas's `md documents/`.
- Cherry-picked Atlas's three `md documents/*.md` files from `origin/master`
  into this branch so the new README's links resolve here.
- Committed as `b4f4d8d` on `claude/review-repo-plans-EshTX`.
- Created this coordination doc as a follow-up commit (this entry).

Push status: `b4f4d8d` and the commit creating this file are **unpushed**.
The local proxy returns `403` on `git push`. Otavio needs to either grant
push permission to this session or pull these commits to the local machine
and push from there.

Open for Atlas:

- Once visible on origin, pull and review the doc reorg. The reorg is
  reversible — flag any file that should move back via a Log entry.
- Confirm or revise the branch-model default above.

Open for Otavio:

- Push permission, or local push of the pending commits.
- Branch model decision.
- (Deferred) Whether to pick a Claude Code orchestrator name.

### 2026-04-29 — Iris (name registration + classification design)

Iris (Claude Code orchestrator) oriented. Name registered in
`ORCHESTRATORS_FRAMEWORK_FOR_THE_CLIPPING_PROJECT.md`. Atlas is on Render
static deployment. Iris is taking the human classification feature end-to-end.

Design decisions confirmed with Otávio today:

- **Dual sentiment per mention**: two fields — `article_sentiment` (is the
  news itself positive/negative?) and `target_sentiment` (is the target
  portrayed positively/negatively for what they did?). Example: "Angelito
  helped save someone in a house fire" → article negative, target positive.
- **Categories**: extensible coworker-defined taxonomy, multiple per article,
  AI-compatible framework for future use. Three new tables added to schema:
  `categories`, `classifications`, `classification_categories`.
- **Centimetragem**: placeholder `REAL` field added; full semantics deferred
  to research agent. Recorded in long-term goals doc.
- **UI**: minimal — classification dropdowns added to existing article cards
  in the current dashboard. No separate screen.

Code changes in this commit:
- `pipeline/database.py`: 3 new tables in `SCHEMA_SQL` + 5 helper functions
  (`get_unclassified_mentions`, `upsert_classification`,
  `set_classification_categories`, `get_or_create_category`,
  `get_classifications_with_context`).
- `docs/LONG_TERM_GOALS_FOR_THE_CLIPPING_ONLINE_PROJECT.md`: created with
  centimetragem and auto-update-spreadsheet as the first two roadmap items.
- `ORCHESTRATORS_FRAMEWORK_FOR_THE_CLIPPING_PROJECT.md`: Iris section added.
- This coordination doc: this entry.

No existing tables or queries were touched. Changes are additive-only.

### 2026-04-29 — Iris (Reviewer + Cartographer findings)

**Iris-Reviewer (regression checks)** — all green:

- `python run_ingestion.py --help` → no import errors.
- `python tools/export_mobile_snapshot.py --help` → no import errors.
- Copied production `data/clipping.db` (41 articles, 41 mentions) to a temp
  file and ran `ClippingDB._init_schema` against it. The three new tables
  were created in place; existing articles/mentions counts unchanged;
  `classifications` count is 0 as expected. Schema upgrade is forward-safe
  on a real DB, not just `:memory:`.

**Iris-Cartographer (export-pipeline integration map)**:

How classifications need to flow into the live dashboard:

| Layer | Current state | What classification needs |
|---|---|---|
| DB read | `db.list_articles_for_export` returns articles+mentions joined; collapses sentiment to `sentiment_any` (MIN). Called from `tools/export_mobile_snapshot.py:353` and `server.py:264`. | Add a parallel `list_articles_for_export_with_classifications` (or extend existing) that LEFT JOINs the new `classifications` and `classification_categories` tables and emits `article_sentiment`, `target_sentiment`, `centimetragem`, and `categories[]` per mention. |
| Story payload | `db.story_with_articles` is called from `tools/export_mobile_snapshot.py:2293` and emits `articles[]` with a single `sentiment` per article. | Same — emit per-mention dual sentiment + categories. The story-card UI groups by article, so we need to decide whether to display per-article (collapse) or per-mention (one row per target). Recommendation: per-mention, since multi-target articles is exactly the case Otávio called out. |
| Static export | `assets/clipping-data.json` is generated and embedded in the snapshot HTML. `assets/clipping.js` consumes it. | `clipping.js` does **not** currently read any `sentiment` field (grep confirms zero references). The dropdown UI is greenfield JS work — no backwards-compat risk. |
| Live editing | The current site is a static Render deployment of pre-rendered HTML. There is no live API for the dashboard to POST a classification. | Iris-Builder needs a small write API — likely a Flask/FastAPI route on a new lightweight server, or a separate Render web service. **This is the framework decision** still pending from Atlas. |

**Implications for the next phase**:

1. Read-side (`list_articles_for_export` + `story_with_articles`) extension is
   straightforward — additive joins. Iris can do it once Atlas confirms
   whether to extend in place or add a parallel method.
2. The dropdown UI in `clipping.js` is a one-pass front-end task with no
   regression risk on existing fields.
3. The write API is the real architecture question. Until the Render
   deployment model is fixed (static-only vs. static+web-service), the
   classification feature can build its read path and UI but can only
   persist locally — not to the live site.

Commit hash: `9a279f3` (schema + helpers landed, pushed to origin).

### 2026-04-30 — Iris end-of-loop output discipline (rule, not an event)

Per direct instruction from Otávio: when Iris ends a loop, the closing message
must be exactly one of three forms:

- **A: verified done** — "I have verified that [feature] is working, you may
  enter the website and see it for yourself." (Requires actual end-to-end
  verification against the live site, not "should work after deploy".)
- **B: blocked on Atlas/MCP** — "I can't do this without the help from Atlas
  and the MCP server. I have updated the documentation to say [context].
  Please, Otávio, ask Atlas to read it." (Requires the question to actually
  be written into `ATLAS_IRIS_ASYNC.md` first.)
- **C: blocked on Otávio** — "Otávio, I have hit a major roadblock that makes
  me unable to keep looping. I believe you need to do [context]. Do exactly
  this." (Requires the blocker to be a human-only action.)

If none of A/B/C applies, Iris keeps looping. Speculation ("should work after
deploy"), punted verification ("let me know if it works"), or premature stops
are not acceptable closing messages. Full text of the rule lives in
`docs/LONG_TERM_GOALS_FOR_THE_CLIPPING_ONLINE_PROJECT.md` §3.

### 2026-04-30 — Iris (open coworker runner live)

Iris completed the open-link coworker runner sprint and verified it against
the live Render URL before closing the loop.

Implemented and pushed checkpoints:
- `14836b8` — `docs: record open coworker runner sprint`
- `d95b540` — `feat: open coworker clipping runner`

Agent evidence:
- Iris-Git-Guard verified `master` was clean, `origin/master` matched local
  `HEAD`, and there was no divergence before the live verification pass.
- Iris-Docs-Scribe recorded the sprint rules in shared docs before code work:
  open-link coworker runner, no admin/password gate for coworker workflows,
  locked primary targets, secondary-only coworker targets, safe collectors,
  Supabase bridge, and live Render as the acceptance bar.
- Iris-Backend-Builder, Iris-Pipeline-Builder, Iris-UI-Builder, and
  Iris-Storage-Builder implemented the open coworker APIs, target persistence,
  progress mapping, friendly top UI, and runtime-only storage bridge.
- Iris-Integration-Builder fixed the `/api/targets` response shape so the live
  API returns top-level `targets` and `primaryKeys`.
- Iris-QA/Render-Ops verified the live deployment after Render promoted
  commit `d95b54082ac340b3a30717454825e0cca4d3c174`.

Live verification:
- Render deploy `dep-d7pnck9j2pic73fq4u8g` is live for commit `d95b540`.
- `https://clipping-project.onrender.com/healthz` returns HTTP `200`.
- `https://clipping-project.onrender.com/api/update/status` returns HTTP
  `200` without login.
- `https://clipping-project.onrender.com/api/targets` returns a top-level
  target list with locked primary keys.
- The homepage shows `Rodar atualizacao`, `Progresso compartilhado`, and
  `Base atual`, and does not show `Senha de acesso`.
- `/admin` redirects to `/`.
- Live `assets/clipping.js` matches the repo asset and contains
  `coworker-runner-20260430`.
- Desktop and mobile browser smoke checks passed with no console warnings or
  errors.

### 2026-04-30 — Atlas (Q-005 seeded categories live verification)

Scope: docs-only answer plus live verification. No code, assets, or data files
changed.

Atlas read Iris's Q-005 from `ATLAS_IRIS_ASYNC.md` on `origin/master` because
the local checkout was dirty and behind the remote. The live `/api/categories`
response includes all 13 base assessoria categories, and a headless Chromium
check of the public dashboard confirmed the `Classificar este artigo` editor's
`Categorias` multi-select lists those categories with the new-category input
and `Adicionar` button still present. A-005 was appended to the async channel.
