# Programadores Cariocas Survey — Long-Term Plan

**Branch:** `claude/gmail-email-invitations-LzTmE`
**Started:** 2026-05-24.
**Convocada por:** Otavio.

---

## The goal (sudario)

Mass-email a survey (Google Form) to all Programadores Cariocas alumni
(Generation + Senac cohorts) to collect feedback via a questionnaire with
~22 sections / 153 questions. The boss's brief breaks this into three
steps: build the questionnaire, create the Google Form, and mass-email the
Form link to the alumni.

## Data sources

- **Questionnaire:** `Question_rio_Prog_Cariocas_NovaVers_oRev.Maira22052026.docx`
  (uploaded to session, not committed — contains the full 153-question
  survey revised by Maira on 2026-05-22).
- **Recipient list:** `Lista_Matriculados_Definitica_por_Ra_a_Genero.xlsx`
  (uploaded to session, not committed — contains PII).
  - 7 sheets: `Alunos Generation (Inscritos)`, `Alunos Generation (Alunos mes 12)`,
    `Alunos Senac (Inscritos)`, `Alunos Senac (Alunos mes 12)`,
    `Caracteristicas Base`, `Senac_Procv`, `Generation Procv`.
  - Generation sheets have emails directly (column A).
  - Senac sheets have CPF only — join to `Senac_Procv` by CPF to recover
    emails.
  - Known typo: many emails have `@gmailcom` (no dot) instead of
    `@gmail.com`. Same for `@hotmailcom`, `@outlookcom`. Must normalize.

## Steps

| # | Step | Status | Notes |
|---|------|--------|-------|
| 0 | Rewrite `INVITATION EMAIL/` as a generic mailing kit; scaffold this campaign subfolder. | **DONE** 2026-05-24 | This plan. See `prompt.md` for the original ask. |
| 1 | Extract questionnaire structure from the docx (sections, questions, options, branching). | **DONE** | Encoded directly into `create_form.gs`. |
| 2 | Create Google Form from the questionnaire spec. | **DONE** 2026-05-29 | Otávio pasted `create_form.gs` into script.google.com and ran it. Live link recorded in `form.md`. |
| 3 | Extract recipient emails from the xlsx. | **DONE** 2026-05-25 | `extract_emails.py` → 798 unique (112 Generation + 686 Senac, 0 overlap), all valid-format, deduped. PII in gitignored `recipients_all.local.txt`; aggregates in `stats.md`. |
| 4 | Email body + Form link. | **DONE** 2026-05-29 | Body provided by Otávio; written verbatim to `invite_body.txt` with the Form link substituted. Subject: "Questionário Programadores Cariocas". |
| 5 | Sender Gmail account + App Password. | **Pending hand-off** — App Password generated. | Personal Gmail. Hand off creds via a fresh OTS link per send, OR store as `GMAIL_USER`/`GMAIL_APP_PASSWORD` repo secrets once (preferred — no per-send link, no credential in git). Follow `HOW_TO_AUTH.md`. |
| 6 | Dry-run, then live send. | **Pipeline ready; pilot one human action away.** Committing the OTS URL is blocked by policy; use Actions dispatch or repo-secret trigger (Iteration 5 / open blocker). | Sandbox CANNOT send (SMTP 465/587 firewalled; only HTTP/HTTPS via proxy). Pilot runs on GitHub Actions; PII batches run on Otávio's machine. |

## Send plan (decided with Otávio 2026-05-29)

- **Subject:** `Questionário Programadores Cariocas`
- **From display name:** `Equipe Programadores Cariocas` (matches the body
  signature; a bare personal-Gmail From reads as spam to alumni).
- **Sender:** personal Gmail (≤500 recipients/day).
- **Volume split:** 798 total → **400 today (batch 1) + 398 tomorrow (batch 2)**,
  to stay under the daily cap. Batches are in gitignored
  `recipients_batch1.local.txt` (400) and `recipients_batch2.local.txt` (398);
  their union is exactly `recipients_all.local.txt` (verified lossless).
- **Pilot first:** send to the 6 test addresses in `mailer/recipients.txt`,
  verify rendering + Form link + From name, THEN run the batches.

### Sequence (each live send needs its OWN fresh OTS link — OTS burns on read)
1. Pilot → 6 test addresses (via GitHub Actions).
2. Batch 1 → 400 (day 1, on Otávio's machine).
3. Batch 2 → 398 (day 2, on Otávio's machine).

After Iteration 4, `mailer/stage_send.sh` collapses each step to one
command. Pilot:
```
bash "INVITATION EMAIL/mailer/stage_send.sh" pilot <FRESH_OTS_URL>
# then: git add the pending-send.url it wrote, commit, push
```
Batches (on Otávio's machine — SMTP is open there, PII never leaves disk):
```
bash "INVITATION EMAIL/mailer/stage_send.sh" batch1 <FRESH_OTS_URL>
# copy + run the python3 command it prints
```

### Hard constraint: the sandbox cannot send mail
SMTP egress (smtp.gmail.com:465 and :587) **times out** in the Claude sandbox —
only HTTP/HTTPS works (via the egress proxy). So `retrieve_and_send.py` must run
on a host with open SMTP. The split:
- **Pilot → GitHub Actions** (`.github/workflows/send-invites.yml`): the workflow
  was extended in Iteration 4 to read `template=`, `recipients=`, `from_name=`
  (and `subject=`) keys from the trigger file, so the survey body + display
  name are honored. The pilot's 6 test addresses are already committed
  (`mailer/recipients.txt`, the default), so no PII concern.
- **Batches → Otávio's machine**: the `recipients_batch{1,2}.local.txt` files
  are gitignored (PII) so the runner cannot see them. `stage_send.sh batch1`
  prints the local-run command — copy, paste, send.

## Privacy decisions

- **Recipient list:** NOT committed to this public repo. Extraction script
  and aggregate stats only. Real addresses stay in `recipients.local.txt`.
- **Xlsx source file:** NOT committed. Lives in session uploads only.
- **Questionnaire content:** OK to commit (no PII — it's a survey
  instrument, not respondent data).

## Open questions

- ~~Which Gmail account will send the survey?~~ **Resolved:** personal Gmail.
- ~~Who writes the email body? When?~~ **Resolved:** provided by Otávio
  2026-05-29; in `invite_body.txt`.
- ~~Form anonymous or tied to email?~~ **Resolved:** form already created by
  Otávio; whatever `create_form.gs` configured stands.
- ~~Send host?~~ **Resolved (Iteration 4):** pilot on GitHub Actions
  (`stage_send.sh pilot`), batches on Otávio's machine
  (`stage_send.sh batch{1,2}`).
- **OPEN — last blocker (revised 2026-06-01, Iteration 5):** the creds must
  reach the GitHub runner, and **committing the OTS URL into git is blocked by
  safety policy** (credential leakage). Two viable transports remain — each
  needs exactly one human action (there is no API to dispatch a workflow or to
  write Actions secrets):
  - **(A) now:** Actions → *Send Invites* → Run workflow → paste a fresh OTS
    URL into `secret_url`; set `template_path`
    =`INVITATION EMAIL/campaigns/programadores-cariocas-survey/invite_body.txt`
    and `from_name`=`Equipe Programadores Cariocas`. URL never enters git.
  - **(C) permanent:** store `GMAIL_USER` + `GMAIL_APP_PASSWORD` as repo
    secrets once (`HOW_TO_AUTH.md` → repo-secrets section); then a URL-less
    `pending-send.url` trigger fires the pilot with no credential in git — a
    Claude session can push that itself. Workflow gained repo-secret mode on
    2026-06-01.
  Batches (798) run on Otávio's machine either way (gitignored PII).
