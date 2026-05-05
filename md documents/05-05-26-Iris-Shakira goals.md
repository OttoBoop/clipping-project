# 05-05-26 Iris-Shakira Goals

_Created 2026-05-05 by Atlas, from Otavio's direct instruction._

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
3. Preserve already-saved items across restart through durable database
   checkpoints.
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
