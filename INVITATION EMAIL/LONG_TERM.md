# Invitation Email — Long-Term Goal

**Persona:** Penelope + CC (Opus 4.7, 1M ctx).
**Branch:** `claude/gmail-email-invitations-LzTmE` (for now — folder will
likely migrate to `OttoBoop/Automatic-Emails` later).
**Started:** 2026-05-20.
**Convocada por:** Otávio.

---

## 1. The sudário (goal)

Send one invitation email — body copy still pending — to a recipient
list still pending, from a sender Gmail account still to be wired up.
This folder collects the assets for that send so it can be triggered
through the same proven pattern in `mass_email_invites/`
(one-time-secret URL → push-trigger → GitHub-hosted runner → Gmail
SMTP).

## 2. What Otávio handed over

Verbatim from the chat that opened this task:

> I want to send the following invitation email. The text is below.
>
> *(the code block in the chat was empty — body copy not yet pasted)*
>
> Here is a link with the invitation and stuff: <https://luma.com/3i0rkczm>

The luma page returned **HTTP 403** when I tried to fetch it from this
sandbox, so I have not been able to capture the event details (title,
host, date/time, location, body copy) automatically. Either Otávio
pastes the body text directly into this folder later, or someone with
browser access pulls it off the luma page.

## 3. Open fios (open threads)

| # | Fio                                                              | Status                                                 |
|---|------------------------------------------------------------------|--------------------------------------------------------|
| 1 | Capture the invitation body (subject + body text).               | **Pending** — code block was empty in the prompt.       |
| 2 | Capture the recipient list (who gets the invite).                | **Pending** — not yet specified.                        |
| 3 | Decide / wire up the sender Gmail (Otávio's "task 3" — log in   | **Pending** — Otávio flagged this as a separate task.   |
|   | with the appropriate email account).                             |                                                        |
| 4 | Drop the body into `invite_template.txt` + recipients into       | **Blocked** by #1, #2.                                  |
|   | `recipients.txt` inside this folder.                             |                                                        |
| 5 | Decide whether this send reuses the existing `send-invites.yml` | **Blocked** by #3 (different sender → different App     |
|   | workflow or gets its own (different sender = different repo      | Password = different repo secret or different OTS link).|
|   | secret / OTS link).                                              |                                                        |
| 6 | Fire the send. Read `last-run-status.md` to confirm outcome.    | **Blocked** by #1–#5.                                   |

## 4. The luma link

<https://luma.com/3i0rkczm>

(Worth Otávio confirming whether this is the canonical link to share
inside the email body, or just a reference for me / Penelope to pull
event details from. If the latter, paste the resolved details into
this file under "## Event details".)

## 5. Operating rules (inherited)

Same as `mass_email_invites/LONG_TERM_GOAL.md`:

- Credentials never typed in chat plaintext — always one-time-secret
  link or repo secret.
- Credentials never touch disk on the runner.
- Each fio = one commit.
- `loop_log.md` (sibling file) records what was tried.
- A technical obstacle is not a block; a missing-decision is.
- Status reported back to Otávio after each meaningful unit, not after
  every commit.
