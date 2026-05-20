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

Otávio handed over the full invitation body in Portuguese on 2026-05-20.
It's a formal invite from **Osmar Lima, Secretário Municipal de
Desenvolvimento Econômico da Prefeitura do Rio**, to alunos e
professores do **Programadores Cariocas**, for the **Claude Impact Lab
Rio** hackathon (primeira edição brasileira, patrocinado pela
Anthropic, realizado pela Taicor + João Lisboa).

The body is stored verbatim in `invite_template.txt` (sibling file).
The subject I chose for it: *"Convite — Claude Impact Lab Rio (24/05,
Maravalley)"* — easy to override at send time via `--subject "..."` if
Otávio wants something different.

**Event quick reference (from the body):**

- **Quando:** Domingo, 24 de maio de 2026, 9h–19h.
- **Onde:** Maravalley.
- **Sobre:** Hackathon de um dia, soluções com Claude para desafios
  reais da cidade nas áreas de Saúde ou Segurança Pública. Melhores
  soluções são doadas ao município.
- **Inscrições / agenda:** <https://luma.com/3i0rkczm>.
- **Patrocinador:** Anthropic. **Realização:** Taicor + João Lisboa
  (embaixador do Claude no Brasil). **Apoio:** Prefeitura do Rio /
  SMDE.

⏰ **Time pressure:** today is 2026-05-20; the event is in **4 days**.
Recipient list + sender Gmail need to land soon for the invite to be
useful.

## 3. Open fios (open threads)

| # | Fio                                                              | Status                                                 |
|---|------------------------------------------------------------------|--------------------------------------------------------|
| 1 | Capture the invitation body (subject + body text).               | **DONE** 2026-05-20 — see `invite_template.txt`.        |
| 2 | Capture the recipient list (alunos e professores do              | **Pending** — Otávio to provide the list, or point at  |
|   | Programadores Cariocas).                                         | wherever the addresses live.                            |
| 3 | Decide / wire up the sender Gmail (Otávio's "task 3" — log in   | **Pending** — Otávio flagged this as a separate task.   |
|   | with the appropriate email account).                             | Probably a Prefeitura / SMDE address given the signer.  |
| 4 | Drop the body into `invite_template.txt` + recipients into       | Partial — body done (#1). Recipients still blocked.     |
|   | `recipients.txt` inside this folder.                             |                                                        |
| 5 | Decide whether this send reuses the existing `send-invites.yml` | **Blocked** by #3 (different sender → different App     |
|   | workflow or gets its own (different sender = different repo      | Password = different repo secret or different OTS link).|
|   | secret / OTS link).                                              |                                                        |
| 6 | Fire the send. Read `last-run-status.md` to confirm outcome.    | **Blocked** by #2, #3.                                  |

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
