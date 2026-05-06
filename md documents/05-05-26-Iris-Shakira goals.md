# 05-05-26 Iris-Shakira Goals

_Created 2026-05-05 by Atlas, from Otavio's direct instruction._
_Updated 2026-05-06 by Theseus-Atlas-Codex._

This document is the living contract for the Shakira recovery loop. It exists
to stop the work from drifting whenever a new bug, interruption, or side-topic
appears. Each new discovery must be added to the loop without replacing the
unfinished goals.

Older project documents may contain useful context, but some are stale. For the
short-term Shakira mission, this document records the current loop to keep in
view while implementing, testing, and verifying on the public site.

## Mission

The public Render site must show real Shakira news in the correct `shakira`
filter for the period `01/04/2026` through `05/05/2026`.

This loop is now owned by `Theseus-Atlas-Codex`: a local Codex fixer following
the Ariadne audit thread. Theseus may close this mission only after public
Render verification, not after local tests, local exports, or unverified deploys.

The acceptance bar is the live site:

- `https://clipping-project.onrender.com/`
- `/api/update/status`
- `/api/update/live-results`
- `/assets/clipping-data.json`
- the visible public UI and screenshot evidence

Local tests, local exports, local pipeline runs, pushed commits, pending
deploys, and "should work" are not enough to close the loop.

## Loop Guard

Until acceptance is complete, every Atlas update and implementation pass must
keep these unfinished goals in view:

- Shakira news must be saved as soon as the pipeline confirms it.
- Shakira news must be published into the public panel, not only visible in a
  temporary live endpoint.
- The `shakira` filter must appear on the public site and show real Shakira
  stories.
- The verified period is `01/04/2026` through `05/05/2026`.
- The run and verification must happen through the public Render site, not a
  local pipeline pretending to be the site.
- If a new bug is found, fix or record it without dropping the Shakira save,
  publish, filter, and verification loop.

## Current Status

Already done:

- `shakira` exists as an active tracked target in the public `/api/targets`.
- The frontend/backend now has a live-results path for saved items during a
  run.
- The ingestion path was changed so an existing URL can receive a missing
  target mention instead of being discarded as a duplicate.
- The known `Notícias relacionadas` / related-link false-positive shape was
  identified and guarded against in code.
- Manual cancellation semantics were tightened so `cancelled` is reserved for
  an explicit human cancel action.
- A public export has published `shakira` into `assets/clipping-data.json` and
  the public UI now shows a `shakira` filter with saved stories for the target
  period.
- Live-saved Shakira stories are visible through `Base atual`, not only through
  a separate temporary progress panel.

Still incomplete:

- The public Shakira filter still needs quality cleanup for secondary-target
  false positives where `shakira` appears only as a late incidental mention
  rather than as the news subject.
- The exact public run for `01/04/2026` through `05/05/2026` has saved and
  published items, but long all-source runs have still been interrupted by the
  fragile Render web-worker model before every source completed cleanly.
- The difference between a true Render restart/redeploy edge case and an
  accidental local/off-site pipeline run still needs to be tested explicitly.
- Export/publication must remain observable and recoverable whenever a saved
  checkpoint needs to be republished after an interrupted run.
- Long sources must be checkpointed by source/query/page/day so the public
  Render job can resume and exhaust sources instead of restarting broad
  collection work from zero.
- Any visible source failure is a repair target, not an acceptable ending. The
  final state is every configured source completed, or a human-visible blocker
  for a truly unavailable external source.

### 2026-05-06 00:00 BRT

- `Theseus-Atlas-Codex` begins the durable-job implementation pass.
- The active role contract comes from `md documents/CHARACTER_SHEET.md`.
- The job thread is no longer allowed to be treated as the source of truth. The
  durable source ledger in the backend database/checkpoint is the source of
  truth for Shakira coverage.
- Public acceptance still requires Render endpoints, `assets/clipping-data.json`,
  visible UI, and screenshot evidence.

### 2026-05-06 13:00 BRT

- Public durable job `85c43d642782` started on Render for `shakira`,
  `01/04/2026` through `05/05/2026`, collector `all`.
- `/healthz` confirmed deployed version
  `2026-05-06-durable-source-ledger` before the run was started.
- The source ledger became visible in `/api/update/status`, confirming that
  this is a Render job with durable source rows, not a local run.
- The first real repair surfaced: configured RSS feeds for `R7`, `Band`, and
  `Estadao` returned `404`. Band and Estadão have current replacement feeds;
  R7 has no working RSS/sitemap endpoint in the probes performed so far and is
  being treated as disabled until a real source URL is found.
- A second RSS repair surfaced after resume: `Conib` returns an HTML page from
  its feed-like URLs instead of RSS/XML. The Conib RSS source is disabled until
  a real feed URL exists; the separate Conib internal-search source remains in
  the durable source plan.

### 2026-05-06 13:45 BRT

- The public job `85c43d642782` recovered from a temporary public `502` and
  continued running on Render; the job was not marked `cancelled`.
- `/api/update/live-results` continued showing saved Shakira items while the
  run processed `Diario do Rio`.
- `assets/clipping-data.json` still published the public `shakira` filter with
  121 stories / 231 articles, but `/api/update/status` still reported an old
  `publishedAt` because it only looked at finished jobs.
- Current code pass fixes that observability gap: incremental publish events
  now count as publication time, and status exposes source-run totals/counts so
  long-source coverage cannot be hidden behind the 80-row visible list.
- The redeploy also showed why a 100-item WordPress page is still too large for
  the Render web-worker model: `Diario do Rio` restarted page 1 multiple times.
  Current code pass reduces durable WordPress API chunks to 25 API items per
  page while preserving the previous overall page span, so checkpoints advance
  faster without silently skipping pages.

## Loop Log

### 2026-05-05 16:36 BRT

- Public Render payload check showed `shakira` published with 90 stories and
  170 unique articles.
- Public status showed the latest successful export `fbaee5c79633` after the
  Shakira update `04512a3f780d` was marked `interrupted`, not `cancelled`.
- The remaining immediate defect is quality: examples like `Projeto busca
  orientar mulheres...` are tagged because Shakira appears only late in a broad
  event-history context, not because the story is about Shakira.
- Current code pass tightens secondary-target matching to title plus the first
  500 characters of snippet/summary, and the cleanup/export path uses the same
  safe surface so stale incidental tags can be removed before publication.

### 2026-05-05 16:45 BRT

- Public export `ac02087a5fd3` succeeded and uploaded the current artifacts,
  but verification showed the static `assets/clipping-data.json` still had 170
  Shakira articles while the live/base endpoint showed 166 after cleanup.
- Root cause found in the cleanup rule: it still trusted `snippet` even when a
  saved article had authoritative `summary`/`full_text`. Search snippets can
  carry misleading related-item text.
- New rule for secondary targets: when `summary` or `full_text` exists, match
  the secondary target against title plus the early saved text; use snippet only
  when no saved text exists.

### 2026-05-05 16:58 BRT

- Public export `88de02b3b85e` succeeded, but `assets/clipping-data.json`
  still published 90 Shakira stories and 170 Shakira articles.
- The remaining publication bug is export-level resurrection: stale secondary
  `targetKeys` can survive into the static payload even after backend cleanup.
- Current code pass adds an export-level guard: article target keys for
  secondary targets are filtered through the saved-text safe surface, and story
  target keys are rebuilt from the filtered article keys before
  `clipping-data.json` is written.

### 2026-05-05 17:07 BRT

- Public export `6af2a01c0605` ran with the deployed health version visible,
  but the stale Shakira stories still appeared in `assets/clipping-data.json`.
- Root cause narrowed again: old story records merged from `index.html` bypassed
  the new database-story export filter and reintroduced stale secondary
  `targetKeys`.
- Current code pass applies the same secondary-target safe-surface filter to
  merged story records before target counts and `clipping-data.json` are built.

### 2026-05-05 17:20 BRT

- Public export `742b2c6207b1` verified the merge filter: Shakira dropped to 86
  stories / 166 articles, and the four known stale stories disappeared from
  `assets/clipping-data.json`.
- Public run `df7674bc73e0` saved one additional Shakira-related backfill and
  then was marked `interrupted`; export `37574d4cf298` published it, bringing
  the filter to 87 stories / 167 articles.
- A second monolithic `all` run reached `Veja Rio Archive`, hit a 502, and did
  not recover as current status. The short-term mitigation is to run public
  custom collector slices instead of one fragile all-in-one worker job.

### 2026-05-05 18:00 BRT

- Public `google_news` slice `83f80eafc052` completed and published
  successfully, raising Shakira to 88 stories / 172 articles.
- Public `sitemap_daily` slice `692b221ef72f` saved a large checkpoint before
  interruption; export `5e8851b21df2` published it, raising Shakira to 119
  stories / 220 articles.
- Public `vejario_archive` slice `5f1c4c1aba83` pushed the API into HTTP 500.
  Current code pass makes job-event payload reads tolerant so one bad/corrupt
  event cannot break `/healthz` and `/api/update/status`.
- Public `camara_archive` slice also pushed status endpoints into HTTP 500.
  Current code pass wraps `/healthz` and `/api/update/status` status reads so a
  job-status failure returns `status_unavailable` instead of taking down the API.

## Required Product Rules

- Confirmed news must be saved immediately when the pipeline accepts it.
- "Saved" means the item is durable in the backend database/checkpoint.
- "Published" means the static/current panel payload has been regenerated and
  the public UI can show the item through the correct filter.
- Live results are progress evidence, but live results alone are not final
  acceptance if the panel export does not publish.
- `shakira` is an active tracked target. It is secondary administratively, but
  secondary does not mean optional.
- "Primary" and "secondary" are administrative labels, not clipping priority
  labels.
- Primary targets are selected automatically by default in the run UI. That is
  the practical product difference.
- Secondary targets must not be described as "optional" in the UI. They are
  tracked names that can be selected for a run.
- The UI label for secondary targets is `Nomes secundários`.
- All tracked names must be treated as real monitored targets for ingestion,
  mentions, story targets, export, filters, and UI.
- Once selected for a run, a secondary target must follow the same save,
  mention, story target, export, filter, and verification contract as a primary
  target.
- Confirmed live-saved news must flow automatically into `Base atual`; the user
  should not need to wait for the whole clipping/export cycle to start seeing
  saved stories there.
- Do not create a separate public section called `Salvas, aguardando publicação`
  for interrupted jobs. The product should make saved stories visible in the
  current base instead of parking them in a separate waiting area.
- `cancelled` means a human manually pressed the cancel control.
- A Render restart, redeploy, crash, or worker loss must not be labeled
  `cancelled`; it must be labeled interrupted or equivalent.
- A local Atlas/Iris pause, terminal interruption, or local pipeline run must
  not be treated as the public site's clipping run.
- Pausing Atlas locally must not affect a Render clipping job.

## Context Compaction Rule

Every future compacted handoff or summary for this project must say explicitly:
the next Atlas must reread
`md documents/05-05-26-Iris-Shakira goals.md` before continuing the Shakira
loop. This document is the short-term memory anchor for the mission.

## Lessons Already Learned

- The site can know about `shakira` through `/api/targets` while the published
  `assets/clipping-data.json` still lacks the `shakira` filter.
- Seeing Shakira items in `/api/update/live-results` proves live-save progress,
  but does not prove the public panel is fixed.
- Render restart/redeploy interruption is an edge case to test and handle, but
  it must not be assumed to be the root cause of every failed Shakira run.
- A separate real failure mode is running or validating the pipeline locally
  instead of through the public Render site. Local activity can create confusing
  evidence, but it does not prove that the public site saved or published
  Shakira.
- The current in-process worker model is fragile: if the web process restarts,
  the running clipping thread dies.
- Durable source state must survive that fragility. Restart/redeploy should
  mark the job resumable and continue from the latest saved source cursor.
- False positives from page boilerplate or `Notícias relacionadas` must not tag
  unrelated articles as Shakira.
- The known false positive shape includes a non-Shakira article whose snippet or
  body only mentions Shakira inside related-link blocks such as `Notícias
  relacionadas`, `Leia também`, or `Veja também`.

## Atlas Must Not Repeat

- Do not declare success without verifying the public Render site.
- Do not treat a local pipeline run as proof that the public site worked.
- Do not treat live-results as final success if `assets/clipping-data.json` and
  the visible UI still lack Shakira.
- Do not let a new bug report replace the existing Shakira loop; add it to the
  loop and keep going.
- Do not continue after a context compaction without rereading this document.
- Do not invent requirements that were not present in Otavio's prompts.
- Do not stop at "plan made" when the requested outcome is a document update or
  a public-site verification.
- Do not call a job `cancelled` unless a human manually pressed the cancel
  control.

## Short-Term Execution Plan

1. Verify that the next Shakira run is started on the public Render site, with
   public endpoints used for monitoring.
2. Fix the minimum job durability needed for the Shakira mission on Render.
3. Preserve already-saved items and source cursors across restart through
   durable database checkpoints.
4. Ensure an interrupted job keeps saved items visible as saved, not lost or
   mislabeled as cancelled.
5. Separately test the Render restart/redeploy edge case instead of treating it
   as the assumed explanation for previous failures.
6. Make export/publication safe and observable enough that a saved checkpoint
   can be published without crashing the web app silently.
7. Run the Shakira clipping from `01/04/2026` to `05/05/2026` on the public
   Render site.
8. Monitor `/api/update/status` and `/api/update/live-results` while the run is
   active.
8.1. Confirm `/api/update/status` exposes `sourceRuns`, `coverageState`,
     `failedSources`, `resumeAvailable`, and `publishedAt`.
9. Verify `/assets/clipping-data.json` after publication contains:
   - target key `shakira`;
   - stories whose `targetKeys` include `shakira`;
   - no known false-positive stories such as the airplane article tagged only
     through related links.
10. Open the public UI, select the `shakira` filter, confirm real Shakira news
    is visible, and capture a screenshot if useful as final evidence.

## Acceptance Checklist

- The document exists at `md documents/05-05-26-Iris-Shakira goals.md`.
- The public `/api/targets` includes active `shakira`.
- The public live-results endpoint shows saved Shakira items during a run.
- Live-saved Shakira stories appear automatically in `Base atual`.
- The published `assets/clipping-data.json` includes `shakira` in targets.
- The published stories include real stories with `targetKeys` containing
  `shakira`.
- The public UI filter `shakira` shows real Shakira stories.
- The verified run covers `01/04/2026` through `05/05/2026`.
- No completion claim is made before live Render verification.
- The run UI does not describe secondary names as optional.
- The run UI labels secondary targets as `Nomes secundários`.
- Primary targets are selected by default; selected secondary targets are saved,
  published, filtered, and verified with the same contract.
- Future compacted handoffs instruct Atlas to reread this document before
  continuing.
