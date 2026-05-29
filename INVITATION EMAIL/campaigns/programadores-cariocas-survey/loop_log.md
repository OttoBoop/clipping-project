# Loop Log — Programadores Cariocas Survey

## Iteration 1 (2026-05-24)

**Goal:** Step 0 — rewrite INVITATION EMAIL/ as a generic mailing kit,
scaffold this campaign subfolder.

**What was done:**
- Moved `mass_email_invites/` contents into `INVITATION EMAIL/mailer/`
  (via `git mv` to preserve history).
- Moved hackathon-specific content into
  `campaigns/claude-impact-lab-rio/`.
- Wrote generic docs: README.md, HOW_TO_AUTH.md, HOW_TO_SEND.md,
  HOW_TO_ADD_CAMPAIGN.md, CLAUDE_HANDOFF.md.
- Updated `.github/workflows/send-invites.yml` paths (all shell references
  properly quoted for the space in `INVITATION EMAIL/`).
- Created this campaign subfolder with prompt.md, long_term_plan.md, and
  this loop_log.md.

**Outcome:** Step 0 complete. Ready for Steps 1-3.

## Iteration 2 (2026-05-25 → 2026-05-29)

**Goal:** Steps 1-3 — questionnaire, Google Form, recipient extraction.

**What was done:**
- Encoded the questionnaire into `create_form.gs` (Apps Script).
- 2026-05-29: Otávio ran `create_form.gs` in script.google.com; Form is live.
  Link recorded in `form.md`.
- `extract_emails.py` → 798 unique recipients (112 Generation + 686 Senac,
  0 overlap), normalized domain typos, deduped. PII in gitignored
  `recipients_all.local.txt`; aggregates in `stats.md`.

**Outcome:** Steps 1-3 complete.

## Iteration 3 (2026-05-29)

**Goal:** Step 4 (email body) + plan and stage the send.

**What was done:**
- Wrote `invite_body.txt` (verbatim body from Otávio + Form link). Subject:
  "Questionário Programadores Cariocas". From-name: "Equipe Programadores Cariocas".
- Enhanced `mailer/retrieve_and_send.py` with `--recipients`, `--template`,
  `--from-name` (backward-compatible) so a campaign can send from its gitignored
  `.local.txt` without copying PII into the tracked `mailer/recipients.txt`.
- Split recipients into `recipients_batch1.local.txt` (400) +
  `recipients_batch2.local.txt` (398); verified union == all 798.
- Dry-run of the pilot passed: From/subject/body/link all render correctly.
- **Finding:** sandbox SMTP is firewalled (smtp.gmail.com:465/587 time out) —
  confirmed the send must run on GitHub Actions or Otávio's machine.

**Outcome:** Step 4 done; send fully staged. **Blocked on:** (1) a fresh OTS
creds link from Otávio, (2) choice of send host (Actions vs local).

## Iteration 4 (2026-05-29)

**Goal:** Get the send pipeline to actually fire when an OTS URL arrives —
the iteration-3 staging exposed a gap: the workflow only passed the URL to
the script, so the survey body / from-name / template-path would have been
ignored even with valid creds.

**What was done:**
- Extended `.github/workflows/send-invites.yml`:
  - `workflow_dispatch` now accepts `template_path`, `recipients_path`,
    and `from_name` inputs (in addition to the existing `secret_url`,
    `dry_run`, `subject_override`).
  - Push-trigger path now parses `pending-send.url` as a `key=value` file
    with optional `template=`, `recipients=`, `from_name=`, `subject=`
    keys. The bare-URL legacy format still works (extracted by regex).
  - Resolved values are passed through to `retrieve_and_send.py` as the
    corresponding `--template` / `--recipients` / `--from-name` /
    `--subject` flags.
- Added `mailer/pending-send.url.example` — an annotated trigger template
  pre-filled with the survey body path and from-name. Copy → fill URL →
  commit → push.
- Added `mailer/stage_send.sh` — one-shot helper that writes the trigger
  file for the pilot (CI-safe) or prints the local-run command for the
  PII batches (gitignored, CI cannot see them):
  ```
  ./stage_send.sh pilot   <OTS_URL>   # CI: 6 test addresses
  ./stage_send.sh batch1  <OTS_URL>   # LOCAL: 400 alumni
  ./stage_send.sh batch2  <OTS_URL>   # LOCAL: 398 alumni
  ```
- Validated: workflow YAML parses, helper passes `bash -n`, end-to-end
  fake-URL stage produces a trigger file with the expected three keys.
- Re-ran the pilot dry-run with the survey template + from-name — output
  matches Iteration 3: "Equipe Programadores Cariocas <user@gmail.com>",
  subject "Questionário Programadores Cariocas", Form link intact, 6
  test recipients listed.

**Outcome:** **Pilot is one OTS-URL paste away.** Two paths now:
- **Send pilot via CI:** Otávio runs
  `bash "INVITATION EMAIL/mailer/stage_send.sh" pilot <fresh OTS URL>`,
  then commits + pushes the resulting `pending-send.url`. CI fires the
  send to the 6 test addresses, deletes the trigger, records output in
  `mailer/last-run-status.md`.
- **Batches (after pilot looks good):** Otávio runs `stage_send.sh
  batch1 <fresh OTS URL>` on his machine and pastes the printed
  `python3 ...` command. Same for batch2 the next day. The PII never
  leaves his disk.

**Still blocked on:** a fresh OTS creds link from Otávio. Nothing else
is in the way.
