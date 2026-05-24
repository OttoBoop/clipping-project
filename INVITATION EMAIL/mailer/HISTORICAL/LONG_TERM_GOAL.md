# Mass Email Invites — Long-Term Goal

**Persona:** Penelope + CC (Opus 4.7, 1M).
**Branch:** `claude/gmail-email-invitations-LzTmE`.
**Started:** 2026-05-11.
**Convocada por:** Otávio.

---

## 1. The Sudário (Goal)

Build a small, self-contained tool inside this repo that lets Otávio:

1. Securely hand a Gmail address + Gmail **App Password** to Claude (no plaintext
   credentials in chat, no credentials persisted on disk).
2. Fire one identical invitation email from that Gmail address to a known list
   of contacts.
3. See exactly which sends succeeded and which failed, with no surprises.

The deliverable is a working Python tool committed to
`mass_email_invites/` on the branch above, plus clear instructions for Otávio
on how to (a) generate the App Password, (b) hand over credentials through a
one-time secret link, and (c) trigger the send.

---

## 2. The Six Fios (Task List)

Each fio is one commitable unit. Penelope weaves one at a time, in order.

| # | Fio                                                                                   | Done when                                                                       |
|---|---------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| 1 | Project skeleton: folder, `LONG_TERM_GOAL.md`, `loop_log.md`, `.gitignore`, `README.md` | Folder + 4 files exist, first commit pushed.                                    |
| 2 | Decide on secure credential transport, document trade-offs in `loop_log.md`            | Decision recorded; one mechanism chosen with concrete reasoning.                |
| 3 | `retrieve_and_send.py` — accepts a one-time-secret URL, fetches credentials in-process, sends emails, never writes credentials to disk | Script exists, has a `--dry-run` mode that prints what it would do without sending. |
| 4 | `invite_template.txt` + `recipients.txt`                                              | Template + the 6 emails from Otávio's prompt are in the file.                   |
| 5 | Dry-run end-to-end with a fake one-time secret (use a local fixture file path as the "URL" to short-circuit the HTTP fetch) | `python retrieve_and_send.py --dry-run --secret-file fixture.txt` prints 6 outgoing emails, 0 actual SMTP traffic. |
| 6 | `README.md` with the three steps Otávio needs (App Password / one-time link / run command), commit + push, then hand back | README exists, branch pushed, message to Otávio gives the exact paste target.   |

---

## 3. Operating Rules (inherited from PENELOPE_CHARACTER_SHEET.md)

- **No pausing for questions Otávio already answered.** Recipients are fixed,
  message body Otávio will draft himself or accept a generic stub, transport is
  Gmail SMTP. Anything else, Penelope decides.
- **One commit per fio.** Loop log updated each iteration.
- **An obstacle is not a block.** If `onetimesecret.com` API is unreachable,
  fall back to stdin-paste with `getpass`. Document the fallback in the log.
- **Credentials live only in memory.** No file write, no echo, no logging of
  passwords. The script reads → uses → exits → the process dies → secret gone.
- **Test before claiming done.** Each fio includes a verification step.

---

## 4. Out of Scope (do not weave these)

- Email tracking pixels, open-rate analytics — not requested.
- Templating engines (Jinja2, etc.) — overkill for one message body.
- Multiple sender accounts — one Gmail only.
- Scheduled / recurring sends — one-shot fire.
- Bounce-handling, retry queues — for 6 recipients, manual retry is fine.
- Anything outside `mass_email_invites/`.

---

## 5. Definition of Done

- Branch `claude/gmail-email-invitations-LzTmE` contains a working
  `mass_email_invites/` directory.
- Otávio has been given: (a) the URL of the one-time-secret service to use,
  (b) the exact format to paste, (c) the command he runs to make Penelope fire
  the emails.
- Otávio can complete the task end-to-end without writing any code himself.
