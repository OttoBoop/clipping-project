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
