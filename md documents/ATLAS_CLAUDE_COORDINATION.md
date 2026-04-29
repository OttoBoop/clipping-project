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

_Last updated: 2026-04-29 by Claude Code._

| Side | Active branch | Currently editing | Open for the other side |
|------|---------------|-------------------|--------------------------|
| Atlas | `master` (assumed) | — | Review the Claude Code doc reorg in commit `b4f4d8d` once it lands on origin |
| Claude Code | `claude/review-repo-plans-EshTX` | — | Awaiting push permission so Atlas can see commits `b4f4d8d` and the next one creating this file |

Pending Otavio decisions:

- Push permission for Claude Code's session, or manual push of pending
  commits from the local machine.
- Branch model (A or B above).
- Whether to name the Claude Code orchestrator now or after the first joint
  planning round (deferred per Otavio).

## Log

Format: `### YYYY-MM-DD — Side`. Append below; never delete prior entries.

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
