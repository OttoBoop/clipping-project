# Mass Email Invites

Fire one identical invitation email from a brand-new Gmail account to a known
list of recipients, with the Gmail credentials handed over through a
one-time-secret link so the password never appears in chat or on disk.

Built by Penelope on branch `claude/gmail-email-invitations-LzTmE`. See
`LONG_TERM_GOAL.md` for the plan and `loop_log.md` for what was tried.

---

## TL;DR — how to actually run this

You'll do **three things**: generate a Gmail App Password, stash it in a
one-time-secret link, and paste that link into chat. I'll do the send.

### 1. Generate a Gmail App Password (one minute)

1. On the new Gmail account, turn **2-Step Verification** on:
   <https://myaccount.google.com/security> → "2-Step Verification".
2. Then go to <https://myaccount.google.com/apppasswords>.
3. Create an app password. Name it anything ("Penelope invites" is fine).
4. Copy the 16-character password Google shows you. It looks like
   `abcd efgh ijkl mnop` (spaces optional, Gmail accepts both forms).

**Why:** Gmail SMTP no longer accepts your real account password. App
Passwords are revocable from that same page — if anything ever feels off,
revoke it with one click and nothing else about the account is exposed.

### 2. Put it in a one-time-secret link

1. Open <https://us.onetimesecret.com/> (or `eu.`, `uk.`, `ca.`, `nz.`
   region — pick whichever you trust).
2. In the "Secret content" box, paste **exactly two lines**:

   ```
   GMAIL_USER=youraccount@gmail.com
   GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
   ```

   (Quotes around the password are optional — both work.)
3. Set **Lifetime** to **5–30 minutes** (the shorter, the better).
4. Optional but recommended: leave the passphrase field empty — we want the
   link to work the first time I read it, no extra back-and-forth.
5. Click **Create a secret link**. Copy the URL it gives you. It looks
   like `https://us.onetimesecret.com/secret/<long-random-key>`.

### 3. Paste the URL to me in chat

Just paste the URL. I'll run:

```
python3 mass_email_invites/retrieve_and_send.py <THE_URL>
```

and that's it. The link self-destructs the moment my script reads it. If you
ever want me to do a dry-run first to confirm everything is wired up,
say so and I'll add `--dry-run` (it'll burn the secret without contacting
SMTP).

After the send, revoke the App Password at
<https://myaccount.google.com/apppasswords> if you don't need it again.

---

## What the script actually does

```
retrieve_and_send.py <URL>
  │
  ├─ POSTs to https://<region>.onetimesecret.com/api/v1/secret/<KEY>
  │   → gets back {"value": "GMAIL_USER=...\nGMAIL_APP_PASSWORD=..."}
  │
  ├─ Parses GMAIL_USER and GMAIL_APP_PASSWORD into local variables
  │   (never written to disk, never echoed)
  │
  ├─ Loads recipients.txt and invite_template.txt
  │
  ├─ Connects to smtp.gmail.com:465 over TLS (smtplib.SMTP_SSL)
  ├─ Logs in once
  ├─ Sends one message per recipient
  └─ Reports per-address success/failure
```

Stdlib only. No `pip install` needed. Tested on Python 3.10+.

---

## Files

| File                    | Purpose                                                                       |
|-------------------------|-------------------------------------------------------------------------------|
| `retrieve_and_send.py`  | The script. Reads creds from URL or `--secret-file`, sends via Gmail SMTP.    |
| `invite_template.txt`   | `Subject:` line + blank line + body. Edit before running if you want.         |
| `recipients.txt`        | One address per line. `#` comments allowed.                                    |
| `LONG_TERM_GOAL.md`     | The plan Penelope is executing.                                               |
| `loop_log.md`           | Iteration-by-iteration log of what was tried.                                 |
| `.gitignore`            | Blocks `*.secret`, `*.env`, `credentials.*` so nothing leaks by accident.     |
| `README.md`             | This file.                                                                    |

---

## Editing the email before sending

Open `invite_template.txt` and edit. The format is:

```
Subject: <one line of subject>
<blank line>
<body, as many lines as you like>
```

`recipients.txt` is one email per line, with `#` for comments. The current
list is the six Otávio dictated in 2026-05-11.

If you want a different subject without editing the template, pass
`--subject "..."` on the command line.

---

## Security notes

- **No plaintext password in chat.** The chat only ever sees a one-time URL
  which is dead after one read.
- **Nothing on disk.** The script parses the secret payload, holds it as a
  local string for the duration of the SMTP session, and lets the Python
  process exit — at which point the memory is reclaimed.
- **`.gitignore` blocks accidents.** Files matching `*.secret`, `*.env`,
  `credentials.*` are pre-blocked from git.
- **App Password is revocable.** If you ever feel paranoid, revoke it at
  <https://myaccount.google.com/apppasswords>. The Gmail account itself is
  untouched.
- **Short TTL on the link.** 5-30 minutes is more than enough; the shorter
  the better.

---

## Manual offline test

```
printf 'GMAIL_USER=fake@gmail.com\nGMAIL_APP_PASSWORD=xxxx\n' > /tmp/f.txt
python3 retrieve_and_send.py --secret-file /tmp/f.txt --dry-run
rm /tmp/f.txt
```

This is what Penelope used to validate the parsing and planning paths
without touching the network or SMTP.
