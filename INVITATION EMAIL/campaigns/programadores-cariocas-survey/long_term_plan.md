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
| 5 | Sender Gmail account + App Password. | **Pending** — Otávio to provide. | Personal Gmail. Hand off creds via a fresh OTS link per send (OTS burns on read). Follow `HOW_TO_AUTH.md`. |
| 6 | Dry-run, then live send. | **In progress** — see Send plan below. | Sandbox CANNOT send (SMTP 465/587 firewalled; only HTTP/HTTPS via proxy). Send runs on GitHub Actions or Otávio's machine. |

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
1. Pilot → 6 test addresses.
2. Batch 1 → 400 (day 1).
3. Batch 2 → 398 (day 2).

Command shape (run where SMTP is open — GitHub Actions or Otávio's machine):
```
python3 "INVITATION EMAIL/mailer/retrieve_and_send.py" \
  --recipients "<batch>.local.txt" \
  --template   "INVITATION EMAIL/campaigns/programadores-cariocas-survey/invite_body.txt" \
  --from-name  "Equipe Programadores Cariocas" \
  <FRESH_OTS_URL>
```

### Hard constraint: the sandbox cannot send mail
SMTP egress (smtp.gmail.com:465 and :587) **times out** in the Claude sandbox —
only HTTP/HTTPS works (via the egress proxy). So `retrieve_and_send.py` must run
on a host with open SMTP. Two options:
- **GitHub Actions** (`.github/workflows/send-invites.yml`): hands-off, but the
  workflow reads the *committed* `mailer/recipients.txt`. Real recipients are PII
  and must NOT be committed — so the workflow needs a PII-safe recipient source
  (e.g. a repo **Actions secret** the workflow writes to a temp file, or a second
  OTS link the script fetches). The pilot's 6 test addresses are already committed
  and non-sensitive, so the pilot works as-is.
- **Otávio's machine**: simplest + safest for PII (the `.local.txt` batches never
  leave his disk). Run the command above three times across two days.

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
- **OPEN — blocking the send:** Otávio's message referenced an OTS login link
  but none was included. Need a fresh OTS URL (creds) before any live send.
- **OPEN — send host:** GitHub Actions (needs PII-safe recipient delivery for
  the real batches) vs Otávio running locally. Awaiting Otávio's choice.
