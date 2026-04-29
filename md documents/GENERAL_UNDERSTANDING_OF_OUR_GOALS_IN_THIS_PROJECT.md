# General Understanding Of Our Goals In This Project

Last updated: 2026-04-29

This document is a compact orientation checkpoint for a future Claude Code
orchestrator collaborating with Atlas on `clipping-project`. It is not the giant
long-term roadmap. It exists so the next agent can understand the current tool,
the direction of travel, and the collaboration constraints before planning or
editing.

## Project Purpose

The project is a political news clipping system for monitoring mentions of
selected Rio de Janeiro political figures, especially Flavio Valle and the
current circle of related candidates.

The current goal is to move from an Otavio-operated local workflow into an
online tool that coworkers can use with less direct intervention from Otavio.
The intended online product should support reviewing collected news,
classifying items with human judgment, and publishing or sharing useful
clipping views.

## What The Current Tool Does

Today the system is a local/CLI ingestion pipeline plus SQLite plus static
GitHub Pages export.

Observed current flow:

1. Run ingestion from the command line with `run_ingestion.py`.
2. Collect candidates from RSS, Google News, WordPress APIs, internal site
   search, daily sitemaps, Camara archive, Veja Rio archive, and optionally
   direct scrape.
3. Match exact monitored names through the pipeline matcher.
4. Fetch article text when needed.
5. Insert articles, mentions, and grouped stories into `data/clipping.db`.
6. Export a static dashboard with `tools/export_mobile_snapshot.py`.
7. Serve `index.html` and `assets/` through GitHub Pages.

The current public/static dashboard supports filters by monitored name, recent
article view, grouped story view, existing AI-summary display, and lazy loading
of raw full text.

## Known Architecture

Important files:

- `docs/PIPELINE.md`: operational reference for collectors, targets, daily
  commands, export, and GitHub Pages publishing.
- `.claude/skills/clipping/SKILL.md`: current Claude operational skill for
  running ingestion, generating local agent summaries, exporting, committing,
  and publishing.
- `pipeline/database.py`: SQLite schema and query helpers. Core tables include
  `articles`, `mentions`, `stories`, `story_articles`, `story_targets`,
  `scrape_log`, and `backfill_state`.
- `pipeline/ingest.py`: collection orchestration, date filtering, exact-name
  matching, article quality checks, text summarization fallback, lexical
  sentiment, and story grouping.
- `tools/export_mobile_snapshot.py`: converts database and optionally existing
  snapshot data into the static Pages bundle.
- `tools/pages_assets/clipping.js`: browser-side rendering for filters,
  grouped/recent views, batching, stats, and raw-text hydration.

The static export currently matters because it preserves the published Pages
experience. It is not, by itself, the likely final coworker-facing application.

## Useful Memory-Map References

Read these before inventing a process from scratch:

- `/home/otavio/Documents/vscode/clipping-project/md documents/ORCHESTRATORS_FRAMEWORK_FOR_THE_CLIPPING_PROJECT.md`
  - Primary coordination document for Atlas, the future Claude Code
    orchestrator, and their subagents.
  - Explains what Paulo means, which previous projects matter, and how the
    orchestrators should avoid overwriting each other.
- `/home/otavio/Documents/vscode/clipping-project/md documents/ATLAS_ORCHESTRATOR_HANDOFF.md`
  - Preliminary Atlas checkpoint from before Otavio split the documentation
    into clearer documents.
  - Treat it as historical context, not the authority for the current
    orchestration structure.
- `/home/otavio/Documents/vscode/clipping-project/md documents/RENDER_RESTART_NOTES.md`
  - Render-specific restart note.
  - Records that no Render service scaffold exists yet in this repo, explains
    why Render is still the likely production direction, and defines the safe
    git sync protocol while Claude Code is active.
- `/home/otavio/Documents/vscode/relatorio sobre a survey/docs/06_fluxo_orquestracao_input_humano.md`
  - Key lesson: files do not replace live human checkpoints.
  - Workers produce evidence; the orchestrator asks the human when ambiguity
    affects meaning or priority.
- `/home/otavio/Documents/vscode/prova-ia-v2/docs/plano_pipeline/09_progresso_longo_prazo.md`
  - Model for long-running progress tracking and separating facts,
    inferences, pending decisions, and external-agent signals.
- `/home/otavio/Documents/vscode/prova-ia-v2/docs/plano_pipeline/13_plano_curto_paulo_rio3_render.md`
  - Model for Render-first, secret-safe planning.
  - Transferable rule: API keys, deploy hooks, tokens, headers, and key
    previews must not appear in chat, docs, frontend code, backend logs, or
    screenshots.
- `/home/otavio/Documents/vscode/prova-ia-v2/docs/workflow_analysis.md`
  - Explains why long projects need source-of-truth planning, decision
    capture, short checkpoints, and gap audits.

## Current Dirty Workspace Caveat

The `clipping-project` worktree is already dirty. Treat local changes as user
or other-agent work unless proven otherwise. Do not revert or overwrite them.

Observed dirty state on 2026-04-29:

- Modified tracked files include `data/clipping.db`, `pipeline/ingest.py`,
  `pipeline/settings.py`, `run_ingestion.py`, and multiple tracked
  `pipeline/__pycache__/*.pyc` files.
- Untracked files include `md documents/ATLAS_ORCHESTRATOR_HANDOFF.md`,
  `md documents/ORCHESTRATORS_FRAMEWORK_FOR_THE_CLIPPING_PROJECT.md`,
  `tools/build_antisemitism_comparison_report.py`, and
  `tools/run_parallel_non_direct_ingestion.py`.

Before any future edit, run a fresh status check and inspect the specific file
being edited. Parallel agents may exist.

## AI-Summary Policy

Current facts:

- The static dashboard can show AI summaries that already exist in the data.
- `database.py` marks summaries as AI-backed when mention `sentiment_reason` is
  `anthropic_batch` or `agent_summary`.
- `.claude/skills/clipping/SKILL.md` currently tells the local acting agent to
  generate short Portuguese summaries for pending articles and write them into
  SQLite.

Working policy for the online product:

- Existing AI summaries may be displayed.
- New AI-summary generation should not be available to ordinary coworker users
  by default.
- Any future AI-summary generation path needs explicit authorization, budget
  expectations, provider choice, audit logging, masking, and secret handling.
- No API key or key preview should be pasted into docs, chat, frontend code,
  backend logs, screenshots, or deploy output.

## Human Classification Is Core And Missing

The major missing feature is human classification. This is not a nice-to-have
around the edges; it is likely central to the coworker-facing v1.

Open design questions:

- Are classifications attached to articles, stories, or both?
- What labels are required?
- Who can classify, review, publish, or administer?
- Should classification output later sync to Excel or another reporting format?
- What audit trail is required for who classified what and when?

Do not silently decide these. Atlas or the Claude orchestrator should turn them
into clear human checkpoints.

## Likely Direction: Render

The likely production direction is a Render-backed website rather than only a
static GitHub Pages bundle.

Current repo fact as of 2026-04-29: there is not yet a Render app in this
repository. No `render.yaml`, `Procfile`, `Dockerfile`, `package.json`,
`pyproject.toml`, or service entrypoint was found. `server.py` is a static
snapshot generator, not a long-running web service. See
`md documents/RENDER_RESTART_NOTES.md` before planning implementation.

Render is attractive because the future app probably needs server-side state,
authentication or role boundaries, classification writes, scheduled or
triggered ingestion, and secret-safe provider configuration. GitHub Pages can
remain useful as a static publishing target or legacy snapshot, but it cannot
own the full coworker workflow alone.

Any Render plan should inherit the secret-safety rules from the Paulo/Rio 3
docs: store secrets server-side, keep them out of chat and docs, avoid public
forms for real provider keys until there is an admin gate, and verify deploy
state with safe metadata only.

## Explicitly Out Of Scope For This Checkpoint

This checkpoint does not:

- implement the Render app;
- choose the database for production;
- design authentication or roles;
- define the classification taxonomy;
- create classification UI or API routes;
- migrate SQLite data;
- schedule ingestion;
- add AI-provider integration;
- change the current GitHub Pages export;
- edit code or data files;
- publish, commit, or deploy anything.

The next useful step is a short working plan for the online clipping migration,
grounded in this orientation and the Atlas handoff, followed by human decisions
on v1 scope, classification labels, user roles, Render architecture, and
AI-summary governance.
