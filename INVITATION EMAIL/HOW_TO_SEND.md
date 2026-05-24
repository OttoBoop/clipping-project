# How to Send

Once you have an OTS URL with the Gmail credentials (see
[HOW_TO_AUTH.md](HOW_TO_AUTH.md)), you're ready to send. This guide covers
the recipient list format, the email template format, dry-run testing, and
both local and CI send paths.

---

## 1. Prepare your recipient list

Create a plain-text file with one email address per line:

```
alice@example.com
bob@example.com
# This line is a comment — ignored
charlie@example.com
```

Blank lines and `#`-comment lines are skipped.

**Where to put it:** by default the script reads `mailer/recipients.txt`.
For a campaign-specific list, create `campaigns/<slug>/recipients.txt` (or
`recipients.local.txt` if the addresses are PII that shouldn't be
committed — `.gitignore` covers `*.local.*`).

---

## 2. Prepare your email template

The template format is:

```
Subject: Your subject line here

Body text goes here.
It can be multiple lines.

Regards,
Sender Name
```

The first line must start with `Subject:`. The body begins after the first
blank line.

**Where to put it:** `mailer/invite_template.txt` is the default. For a
campaign-specific body, create `campaigns/<slug>/invite_body.txt` and
copy it into `mailer/invite_template.txt` before sending (or symlink it).

You can also override just the subject at runtime with `--subject "..."`.

---

## 3. Dry-run (always do this first)

### Local dry-run with a fixture file (no network, no OTS burn)

```bash
printf 'GMAIL_USER=fake@gmail.com\nGMAIL_APP_PASSWORD=xxxx\n' > /tmp/f.txt
python3 "INVITATION EMAIL/mailer/retrieve_and_send.py" \
    --secret-file /tmp/f.txt --dry-run
rm /tmp/f.txt
```

This validates: credential parsing, template loading, recipient loading,
and the send plan — without touching SMTP or burning a real OTS link.

### Dry-run with a real OTS URL (burns the link, but doesn't send)

```bash
python3 "INVITATION EMAIL/mailer/retrieve_and_send.py" <OTS_URL> --dry-run
```

This confirms the full credential-fetch path works end-to-end. The OTS
link is consumed (one-time), so you'll need a fresh one for the live send.

---

## 4. Live send

### Option A — Local machine

```bash
python3 "INVITATION EMAIL/mailer/retrieve_and_send.py" <OTS_URL>
```

Requires outbound access to:
- The OTS API (`https://*.onetimesecret.com`, port 443)
- Gmail SMTP (`smtp.gmail.com`, port 465)

### Option B — GitHub Actions (for restricted environments)

If your local machine can't reach those hosts (e.g. a sandboxed
environment), the GitHub Actions workflow can do the send on a hosted
runner.

**Manual dispatch:**
1. Go to the repo's **Actions** tab → **Send Invites** workflow.
2. Click **Run workflow**.
3. Paste the OTS URL into the `secret_url` input.
4. Optionally check **Dry-run** or fill in a **Subject override**.
5. Click **Run workflow**.

**Push-trigger dispatch:**
1. Write the OTS URL into `INVITATION EMAIL/mailer/pending-send.url`.
2. Commit and push. The workflow triggers automatically.
3. After the run, the workflow deletes the trigger file and commits the
   run status to `mailer/last-run-status.md`.

---

## 5. Monitoring

After every run (local or CI), check:

- **Console output** — the script prints `[ok]` or `[FAIL]` per recipient.
- **`mailer/last-run-status.md`** — the CI workflow writes full output here
  and commits it back to the branch.

---

## 6. Rate limits and batching

| Account type | Daily limit |
|---|---|
| Personal Gmail (`@gmail.com`) | 500 recipients |
| Google Workspace | 2 000 recipients |

If your list exceeds the daily limit, split it across multiple days or
multiple sender accounts. The script sends sequentially (one SMTP
connection, one message at a time) so it won't trip Gmail's burst
throttling — but it will hit the daily cap if the list is too long.

---

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `SMTPAuthenticationError` | Used real password instead of App Password, or App Password was revoked | See [HOW_TO_AUTH.md](HOW_TO_AUTH.md) Step 3 |
| `Could not retrieve the secret from any region` | OTS link already consumed or expired | Create a new OTS link |
| `[FAIL]` for specific addresses | Invalid address, or recipient's server rejected the message | Check the error message; remove or fix the address |
| Workflow says `DIR MISSING` | The `INVITATION EMAIL/mailer/` folder wasn't checked out | Ensure the workflow checkout step uses the correct branch |
| Script hangs | Firewall blocking port 465 outbound | Use the GitHub Actions path instead (Option B) |
