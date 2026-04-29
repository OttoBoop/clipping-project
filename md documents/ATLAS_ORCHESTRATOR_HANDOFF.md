# Atlas Orchestrator Handoff

Last updated: 2026-04-29

Status note: this was Atlas's first rough checkpoint. Otavio later clarified
that the project needs two cleaner starting documents. Use these as the current
entrypoints:

- `md documents/ORCHESTRATORS_FRAMEWORK_FOR_THE_CLIPPING_PROJECT.md`
- `md documents/GENERAL_UNDERSTANDING_OF_OUR_GOALS_IN_THIS_PROJECT.md`
- `md documents/RENDER_RESTART_NOTES.md`

This document is the shared starting checkpoint for the clipping-online project.
It is written so Codex, Claude Code, and future subagents can resume from the
same map without rereading the whole workspace.

## Atlas Identity

**Atlas** is the Codex-side orchestrator for turning the clipping tool from an
Otavio-operated local workflow into an online tool coworkers can run and review
without Otavio's direct intervention.

Paulo remains the prior/reference orchestrator pattern. Atlas inherits the Paulo
style of work:

- report facts, inferences, and pending decisions separately;
- keep the human in the loop before major product or governance decisions;
- give subagents narrow tasks, explicit limits, and expected outputs;
- assume parallel agents may exist and check local signals before editing shared
  documents;
- avoid overwriting user, Claude, or unknown-agent changes.

## Orchestration Memory Map

Read these first when reconstructing the framework:

- `relatorio sobre a survey/docs/06_fluxo_orquestracao_input_humano.md`
  - Core lesson: infrastructure files do not replace live human checkpoints.
  - Workers produce evidence, not final decisions.
  - Ambiguity should become a direct question to the human.
- `prova-ia-v2/docs/plano_pipeline/09_progresso_longo_prazo.md`
  - Defines Paulo's monitoring protocol.
  - Separates facts, inferences, pending decisions, and external-agent signals.
  - Says to detect parallel agents from local workspace evidence before asking.
- `prova-ia-v2/docs/plano_pipeline/13_plano_curto_paulo_rio3_render.md`
  - Useful model for secret-safe planning, Render-first thinking, and subagent
    role definition.
  - Key transferable rule: secrets must not appear in chat, docs, logs,
    frontend, or backend output.
- `prova-ia-v2/docs/workflow_analysis.md`
  - Explains why long projects need a source-of-truth plan, live decision
    capture, short-plan checkpoints, and gap audits.

## Current Clipping Architecture

The current clipping project is not yet a coworker-facing web app. It is a
local/CLI pipeline plus a static GitHub Pages dashboard.

Observed architecture:

- Ingestion entrypoint: `run_ingestion.py`.
- Pipeline package: `pipeline/`.
  - `pipeline/ingest.py` orchestrates collectors, full-text fetch, keyword
    matching, story grouping, and SQLite writes.
  - `pipeline/settings.py` defines monitored targets and query builders.
  - `pipeline/database.py` owns the SQLite schema and query helpers.
- Main storage: `data/clipping.db`.
  - Existing tables include `articles`, `mentions`, `stories`,
    `story_articles`, `story_targets`, `scrape_log`, and `backfill_state`.
- Published UI:
  - `tools/export_mobile_snapshot.py` exports the static bundle.
  - `index.html` plus `assets/clipping-data.json`,
    `assets/clipping-raw-texts.json`, `assets/clipping.css`, and
    `assets/clipping.js` are served by GitHub Pages.
  - `tools/pages_assets/clipping.js` renders filters, recent articles, grouped
    stories, existing AI summaries, and lazy raw-text loading in the browser.
- Operational Claude skill:
  - `clipping-project/.claude/skills/clipping/SKILL.md` documents the current
    run/export/publish flow.
  - That skill currently lets Claude/Codex generate summaries directly as the
    acting AI. Coworkers will not have that same local agent context.

## Current Workspace State

Freshness check on 2026-04-29:

- No new Markdown plan file for this clipping-online task was found under the
  workspace today.
- No active Claude Code process was visible from `ps`; only the Codex app server
  was visible.
- This is only a local signal check, not a guarantee that no external agent will
  write files later.

`clipping-project` is already dirty. Do not assume a clean baseline.

Tracked modified files observed:

- `data/clipping.db`
- `pipeline/ingest.py`
- `pipeline/settings.py`
- `run_ingestion.py`
- multiple tracked `pipeline/__pycache__/*.pyc` files

Untracked files observed:

- `tools/build_antisemitism_comparison_report.py`
- `tools/run_parallel_non_direct_ingestion.py`

Important existing diff theme:

- `pipeline/ingest.py`, `pipeline/settings.py`, and `run_ingestion.py` already
  contain work moving ingestion beyond a Flavio-only internal-search path.
- `run_ingestion.py` has a `--db` option in the dirty diff, useful for safer
  isolated runs.
- Preserve this work unless Otavio explicitly asks to revert it.

Restart correction on 2026-04-29:

- The `md documents/` folder is tracked locally and on `origin/master`.
- The cloud-side commit `6eb4314` uploaded the same three original Markdown
  files that local Atlas had created.
- Atlas created `backup/atlas-full-state-20260429-152318` before cleaning the
  local sync path, so the previous all-files local commit remains recoverable.
- A dedicated Render restart note now exists at
  `md documents/RENDER_RESTART_NOTES.md`.
- Current Render fact: this repo still has no deploy scaffold or service
  entrypoint. `server.py` is a static snapshot generator, not a Render web app.

## Product Constraints Already Known

Facts:

- Coworkers need an online tool they can run without Otavio directly operating
  the clipping workflow.
- The likely production direction is a Render-backed website, not only a static
  GitHub Pages bundle.
- Human classification of news is a core missing feature.
- Existing AI summaries that already exist in the dataset may be shown.

Policy inferences:

- New AI-summary generation should be blocked for regular users by default.
- Future API-key paths may exist, but they need budget, authorization, masking,
  and logging rules first.
- Testing summary generation with protected Google or other provider keys may be
  acceptable later, but should not imply public coworker access.
- API keys, deploy hooks, tokens, and key previews must not be pasted into docs,
  chat, frontend code, backend logs, or screenshots.

Longer-term idea:

- Connecting human classification output to Excel is desirable, but should be
  treated as a later phase after the online classification workflow exists.

## Atlas Protocol For This Project

Atlas should keep reports in this structure:

```text
Facts:
Inferences:
Pending decisions:
Next safe action:
```

Before editing shared docs or planning files, Atlas should check:

- `git status --short --branch` inside `clipping-project`;
- recent Markdown files modified today;
- active `codex` or `claude` processes;
- whether a file about to be edited already contains newer external-agent work.

Subagents should use the `Atlas-` prefix. Initial role names:

- `Atlas-Archivist`: reads prior orchestration docs and extracts reusable rules.
- `Atlas-Cartographer`: maps current clipping architecture and data flow.
- `Atlas-Guard`: owns secrets, API-key policy, AI-summary gating, and safe logs.
- `Atlas-Classifier`: designs human classification workflow and data model.
- `Atlas-Builder`: implements bounded code changes after the plan is stable.

Subagent rules:

- give each subagent a concrete question or file ownership boundary;
- state what it may read and what it may edit;
- require a short output with evidence, uncertainties, and changed files;
- do not let subagents make final product decisions silently.

## Claude Code Handoff

Claude Code should start here:

1. Read this document first.
2. Read the four orchestration memory docs listed above.
3. Run a fresh `git -C clipping-project status --short --branch`.
4. Check for newer Markdown documents and parallel-agent signals.
5. Do not rewrite this handoff broadly if another agent has edited it. Prefer a
   dated append-only note.
6. Preserve dirty user/agent work unless Otavio explicitly asks for cleanup.

Recommended next checkpoint after this handoff:

- create a short Atlas working plan for the online clipping migration;
- only then ask product questions about v1 scope, classification taxonomy,
  coworker roles, Render deployment shape, and AI-summary policy;
- do not start website implementation until the architecture and governance
  plan has been accepted.

## Immediate Next Questions For Atlas Later

These are not blockers for this handoff, but they are the next product decisions
Atlas should ask once the shared checkpoint is accepted:

- Who are the coworker roles: viewer, classifier, publisher, admin?
- What classification labels are required for news items?
- Should classification happen at article level, story level, or both?
- What is the first acceptable online v1: review-only, run-and-review, or full
  portal with scheduling?
- What database should back the Render app at v1: SQLite with backups, managed
  Postgres, or another hosted store?
- What exact AI-summary policy should apply to admins, regular users, and test
  environments?

## Non-Changes In This Checkpoint

This handoff does not implement the online website, database migration,
classification UI, API routes, authentication, Render deployment, or AI-summary
provider integration. It only establishes the shared Atlas starting map.
