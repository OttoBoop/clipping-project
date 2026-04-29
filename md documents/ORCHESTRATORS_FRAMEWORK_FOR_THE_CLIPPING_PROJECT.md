# Orchestrators Framework for the Clipping Project

Last updated: 2026-04-29

This document defines how the orchestrator agents should work together on the
clipping-online project. It is separate from the product-goals document. This is
about **how Atlas, Claude Code's future orchestrator, subagents, and Otavio
coordinate the work**.

## Why This Document Exists

The clipping-online project is large enough that a single chat thread will lose
important context. Otavio is also deliberately setting up more than one AI tool
to work on the same project. That means the agents need a shared operating
framework before implementation begins.

The first checkpoint is therefore documentation, not code:

- give Codex's orchestrator a stable identity: **Atlas**;
- leave room for Claude Code to choose its own orchestrator name;
- record what we learned about agent orchestration from previous projects;
- define how Atlas and the future Claude orchestrator coordinate without
  overwriting each other;
- make it easy for Claude Code to enter the workspace and understand the state.

## Agent Names and Responsibilities

### Atlas

Atlas is the Codex-side orchestrator for this project.

Atlas's job is to keep the project map coherent while work is split across
agents. Atlas should:

- maintain the shared docs and the current interpretation of the plan;
- separate facts, inferences, and pending decisions;
- check the repo state before editing shared files;
- create bounded subagents only when parallel work helps;
- summarize subagent results before decisions are treated as settled;
- stop after this documentation checkpoint and give Otavio an exact Claude Code
  prompt.

Atlas should not rush into product questions before the coordination layer is
stable. Otavio explicitly corrected that sequence in this conversation.

### Iris

Iris is the Claude Code–side orchestrator for this project.
Name chosen 2026-04-29. Rationale: Atlas holds up the sky (local, grounding);
Iris is the messenger bridging sky and earth (cloud, coordinating). Iris runs
on the Claude Code cloud side; Atlas runs locally on Otávio's machine.

Iris owns the human classification feature.

Iris subagent prefix: `Iris-`. Current subagents: none yet.
Planned subagent roles:

- `Iris-Cartographer`: maps current schema and export pipeline.
- `Iris-Classifier`: implements classification DB layer.
- `Iris-Builder`: implements web routes once framework is decided.
- `Iris-Reviewer`: regression-checks ingestion and export after changes.

Iris reports to Otávio after each agent run using the
Facts / Inferences / Blockers / Next format.

Operating rules: see `md documents/IRIS_OPERATING_RULES.md`.
Atlas-Iris async Q&A: see `md documents/ATLAS_IRIS_ASYNC.md`.

### Claude Code's Future Orchestrator

Claude Code has chosen the name **Iris** (registered above). This section is
kept as a placeholder for the naming decision record.

The Iris orchestrator:

- read this file first;
- read the general project-orientation file next;
- inspects the current workspace state before editing;
- avoids rewriting Atlas-owned docs broadly unless asked;
- adds dated notes when it discovers new facts or disagrees with Atlas;
- creates subagents with the `Iris-` prefix to identify the Claude side clearly.

### Paulo

Paulo is not the orchestrator for this clipping project. Paulo is the reference
pattern from previous work.

The clearest Paulo example is from the NOVO CR / Rio 3 Render planning work in
`prova-ia-v2/docs/plano_pipeline/13_plano_curto_paulo_rio3_render.md`. In that
project, Paulo's role was to coordinate a sensitive provider/deploy effort,
split work among subagents, protect secrets, monitor Render/GitHub state, and
report facts versus inferences.

The clipping project should reuse the lessons, not the name:

- live progress reporting matters;
- subagents need explicit scope, inputs, and outputs;
- secrets must never be copied into chat, docs, logs, frontend code, or backend
  output;
- a local popup or local proof is not the same as progress on the official live
  site;
- the orchestrator must keep working on adjacent blockers instead of freezing
  around one missing key or one pending human action.

Another important precursor is the survey/cycling report workflow in
`relatorio sobre a survey/docs/06_fluxo_orquestracao_input_humano.md`. That
project taught the rule: **worker findings are evidence, not final decisions,
and human ambiguity must be surfaced live rather than hidden in files**.

## What We Learned About Creating Agents

### 1. Name the Orchestrator Before Product Planning

Otavio explicitly wanted the Codex-side orchestrator named before Atlas started
asking product-scope questions. The name creates a stable reference point for
future messages: "Codex" can mean the tool broadly, while "Atlas" means the
agent responsible for this project inside the Codex system.

For future sessions, the sequence should be:

1. name the orchestrator;
2. define its responsibilities;
3. create shared docs;
4. only then ask product and implementation questions.

### 2. Separate Operating Framework From Product Goals

The first handoff note mixed orchestration, product constraints, and architecture
summary too tightly. Otavio corrected this. The project now needs at least two
early docs:

- this orchestrator-framework document;
- a general goals/orientation document for the clipping-online project.

The eventual long-term roadmap should be a third document, created later after
Atlas and the Claude orchestrator are both oriented.

### 3. Memory Maps Need Context, Not Just Links

It is not enough to mention "Paulo" or list prior files. A future agent needs to
know which project each memory comes from and why it matters.

Use memory docs as examples of reusable patterns:

- survey/cycling report: human checkpointing and evidence versus decisions;
- NOVO CR / Rio 3: Paulo, Render-first operations, secrets, subagent monitoring;
- workflow analysis: source-of-truth docs, decision capture, short plans, and
  gap audits.

### 4. Parallel Agents Need Local Coordination Rules

Atlas and Claude Code may work in the same repo. Before editing shared docs,
each orchestrator should inspect:

- `git -C clipping-project status --short --branch`;
- recent Markdown timestamps;
- active `codex` or `claude` processes;
- whether the file to edit already contains newer work.

If a file has uncertain authorship, do not "clean it up" silently. Prefer a
dated append-only note or ask Otavio.

### 5. Subagents Need Contracts

Subagents should not receive vague instructions like "research the project."
Each subagent needs:

- a name;
- one concrete task;
- allowed read scope;
- allowed write scope, if any;
- expected output format;
- clear limits on decisions it may not make.

Subagents produce evidence, summaries, patches, or drafts. They do not silently
decide product direction.

### 6. Atlas Must Report While Agents Work

The prior orchestration framework emphasized visible progress. Atlas should not
let agents work invisibly while Otavio waits. For longer runs, Atlas should
briefly report:

- which agent is working;
- what that agent is responsible for;
- what has been learned so far;
- what remains blocked or uncertain.

### 7. Documentation Comes Before Website Work

Otavio is setting up the Render website in parallel. Atlas and Claude Code can
prepare, inspect, and document while that happens, but the current checkpoint is
not to implement the live site yet.

This protects the project from premature architecture decisions before both
orchestrators understand the same facts.

## Coordination Model for Atlas and Claude Code

The two orchestrators should treat each other as peer coordinators, not as
anonymous file writers.

### Shared Rules

- Work in dated, attributable notes when editing shared planning docs.
- Keep facts, inferences, and decisions separate.
- Never expose API keys, deploy hooks, tokens, headers, or key previews.
- Do not revert dirty work unless Otavio explicitly asks.
- Do not assume a clean baseline in `clipping-project`.
- Use the docs as a shared memory, not as a substitute for asking Otavio when a
  decision really depends on him.

### Suggested Naming Convention

Codex side:

- `Atlas`: main Codex orchestrator.
- `Atlas-Archivist`: prior-doc and framework reader.
- `Atlas-Cartographer`: codebase and architecture mapper.
- `Atlas-Guard`: secrets, API-budget, and AI-summary policy reviewer.
- `Atlas-Classifier`: human-classification workflow planner.
- `Atlas-Builder`: implementation worker after the plan is stable.

Claude Code side:

- The main orchestrator should choose a non-Atlas name.
- Claude subagents should use that name as a prefix.
- Example only: if Claude chooses "Helena", its subagents might be
  `Helena-Archivist`, `Helena-Builder`, and `Helena-Reviewer`.

### Division of Labor at the Start

Atlas's immediate responsibilities:

- create the orchestrator framework doc;
- create or coordinate the general goals/orientation doc;
- produce the exact prompt for Claude Code;
- stop after documentation is ready.

Claude Code's immediate responsibilities after receiving the prompt:

- read both new docs;
- pick and register an orchestrator name;
- inspect the repo status and current architecture;
- add a dated note with anything it learns or disagrees with;
- avoid implementation until Otavio confirms the next step.

## Required Early Documents

Current early-document set:

- `md documents/ORCHESTRATORS_FRAMEWORK_FOR_THE_CLIPPING_PROJECT.md`
  - This file. Defines Atlas, the future Claude orchestrator, coordination
    rules, and agent lessons.
- `md documents/GENERAL_UNDERSTANDING_OF_OUR_GOALS_IN_THIS_PROJECT.md`
  - Shared orientation about the clipping-online project, current architecture,
    constraints, and near-term purpose.

Possible future docs:

- `docs/LONG_TERM_GOALS_FOR_THE_CLIPPING_ONLINE_PROJECT.md`
  - The eventual roadmap. Not part of this checkpoint.
- `docs/DECISIONS_OTAVIO.md`
  - A living decision log with exact quotes or faithful summaries.
- `md documents/ATLAS_CLAUDE_COORDINATION_LOG.md`
  - A dated record of what Atlas and the Claude orchestrator each changed.

## How Orchestrators Should Handle Disagreement

If Atlas and Claude Code disagree:

1. Record the disagreement as a dated note.
2. Identify whether it is a fact dispute, inference dispute, or product
   decision.
3. Resolve fact disputes by inspecting the repo or docs.
4. Resolve inference disputes by stating assumptions and likely consequences.
5. Escalate product decisions to Otavio.

Do not hide disagreements by rewriting the other orchestrator's text.

## Current Checkpoint Definition

This checkpoint is complete when:

- the orchestrator framework doc exists;
- the general goals/orientation doc exists;
- Atlas has verified basic Markdown/whitespace health;
- Atlas gives Otavio an exact prompt to give Claude Code.

This checkpoint intentionally does not:

- implement the Render app;
- decide the full v1 scope;
- design the final classification taxonomy;
- build authentication;
- wire AI-summary generation;
- connect classification to Excel.

The next step belongs to Otavio: start Claude Code with the prompt Atlas
provides, then let the two orchestrators begin coordinated planning from the same
documentation base.
