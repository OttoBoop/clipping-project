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
| 1 | Extract questionnaire structure from the docx (sections, questions, options, branching). | **Pending** | Docx is in session uploads. Output: structured spec (JSON or Markdown) in this subfolder. |
| 2 | Create Google Form from the questionnaire spec. | **Pending** | Approach: Google Apps Script (`create_form.gs`) that Otavio pastes into script.google.com and runs. No GCP project needed. Fallback: manual form creation using the spec as a guide. |
| 3 | Extract recipient emails from the xlsx. | **Pending** | Script: `extract_emails.py` in this subfolder. Output: `recipients.local.txt` (gitignored). Also: `stats.md` with aggregate counts (committed). |
| 4 | Email body from "as meninas". | **Blocked** — waiting on external input. | The email body (what recipients see + the Form link) is not yet written. |
| 5 | Sender Gmail account + App Password. | **Blocked** — Otavio to provide. | Follow `HOW_TO_AUTH.md`. Hand off via OTS link. |
| 6 | Dry-run, then live send. | **Blocked** by 3, 4, 5. | Follow `HOW_TO_SEND.md`. Copy campaign recipients + body into `mailer/`, send via OTS URL. |

## Privacy decisions

- **Recipient list:** NOT committed to this public repo. Extraction script
  and aggregate stats only. Real addresses stay in `recipients.local.txt`.
- **Xlsx source file:** NOT committed. Lives in session uploads only.
- **Questionnaire content:** OK to commit (no PII — it's a survey
  instrument, not respondent data).

## Open questions

- Which Gmail account will send the survey? (Prefeitura/SMDE address, or
  Otavio's personal?)
- Who are "as meninas" writing the email body? When is it expected?
- Should the Form collect responses anonymously, or tied to the email
  address?
