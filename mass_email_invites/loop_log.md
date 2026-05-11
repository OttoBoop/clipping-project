# Loop Log — Mass Email Invites

Penelope's weaving log. One entry per iteration. What was tried, what worked,
what didn't, what got committed.

Newest entries at the bottom.

---

## 2026-05-11 — Session start

**Persona:** Penelope + CC (Opus 4.7, 1M ctx).
**Branch:** `claude/gmail-email-invitations-LzTmE` (already checked out, fresh
from master).
**Working dir:** `/home/user/clipping-project/mass_email_invites/`.

**Note:** Otávio's prompt referenced `/home/otavio/Documents/vscode/mass firing
of emails`. That path doesn't exist in this sandbox. Decision: keep the work
inside the clipping-project repo so it lands on the designated branch and is
versioned. If Otávio wants it moved to his local Documents folder later, he can
just `git clone` or copy the directory.

---

## Iteration 1 — Project skeleton

**Goal:** create folder, `LONG_TERM_GOAL.md`, this file, `.gitignore`,
placeholder `README.md`. First commit.

**Done:** commit `973f9ed` — `mass_email_invites: scaffold the Penelope loop`.

---

## Iteration 2 — Pick credential transport

**Options considered:**

1. **One-time-secret link (chosen).** Otávio pastes credentials into
   `https://us.onetimesecret.com/`, sets a short TTL + optional passphrase,
   gets back a URL that self-destructs on first view. He pastes the URL
   into chat. The script `POST`s to
   `https://<region>.onetimesecret.com/api/v1/secret/<KEY>` to retrieve the
   `value` field, keeps it in memory, and exits.
   *Pros:* no plaintext in chat; secret destroyed after one read; works
   from any browser; no extra tooling for Otávio.
   *Cons:* the secret does pass through my script's process — but only
   in-memory, never on disk, and never echoed.
2. **GPG/age encrypted file.** Requires Otávio to install tooling and
   generate a keypair for me to publish — overkill for a one-shot send.
3. **stdin getpass.** Would require Otávio to run the script himself,
   which contradicts his request ("I can paste a secure link"). Kept as a
   fallback `--secret-file` mode for testing only.
4. **Environment variables.** Same problem as stdin: Otávio runs it, not
   me. And env vars leak into logs more easily than process memory.

**Decision:** option 1. Live API test from sandbox is blocked
(`Host not in allowlist`), so script will be written defensively: clear
error messages on HTTP failure, and a `--secret-file` testing mode that
short-circuits the network for offline validation.

**Defence in depth:**
- `.gitignore` already excludes `*.secret`, `*.env`, `credentials.*`.
- Script never writes credentials to a file or to stdout.
- README will tell Otávio to set a 5–15 min TTL and revoke the Gmail
  App Password after the send if he no longer needs it.

**Done.**

---

## Iteration 3 — Build `retrieve_and_send.py`

**Goal:** stdlib-only Python script with the contract:

    python retrieve_and_send.py <onetimesecret_url> [--dry-run] [--subject "X"]
    python retrieve_and_send.py --secret-file FILE [--dry-run]     # testing

Credentials parsed in `KEY=VALUE` dotenv-ish format from the secret payload.
SMTP via `smtplib.SMTP_SSL` to `smtp.gmail.com:465`. One email per recipient
in `recipients.txt`, body+subject from `invite_template.txt`.

**Done.** Script is stdlib-only (Python 3.10+). 4 error paths verified:

| Scenario                        | Result                                                                 |
|---------------------------------|------------------------------------------------------------------------|
| Valid quoted payload, dry-run   | Parses, plans, exits 0.                                                |
| Unquoted password value         | Accepted (regex strips matching quotes only if both ends match).       |
| Missing `GMAIL_APP_PASSWORD`    | Exit 1, message names the missing field.                               |
| URL that doesn't match key regex| Exit 1, message says "expected /secret/<KEY>".                         |
| Both URL and `--secret-file`    | Exit 2 via argparse with explicit message.                             |

---

## Iteration 4 — Template + recipients

Wrote `invite_template.txt` with a placeholder generic test message in
Portuguese (Otávio can edit before send). Wrote `recipients.txt` with the
6 addresses he dictated:

- otaviobopp@gmail.com
- otavio2809@gmail.com
- otavio0999@gmail.com
- otavio0999@hotmail.com
- robaynasafra@gmail.com
- steamargentina585@gmail.com

**Done.**

---

## Iteration 5 — End-to-end dry-run

Ran `python3 retrieve_and_send.py --secret-file /tmp/f.txt --dry-run`
against a fixture. Output showed: correct sender, correct subject from
template, all 6 recipients enumerated, body preview matching the template,
and `[dry-run] not contacting SMTP`. Exit 0.

**Done.**

---

## Iteration 6 — README + hand-back

Rewrote `README.md` with the three steps Otávio actually needs: (a)
generate App Password, (b) paste two-line payload into onetimesecret with
short TTL, (c) paste URL into chat. Plus security notes and offline-test
recipe.

**Status:** about to commit and push.

