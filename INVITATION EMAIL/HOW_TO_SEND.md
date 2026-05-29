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
For a campaign-specific list, create `campaigns/<slug>/recipients.local.txt`
and point the script at it with `--recipients <path>`. Use the `.local.txt`
suffix for any real addresses (PII) — `.gitignore` covers `*.local.*`, so they
never get committed. **Do not** copy PII into the tracked `mailer/recipients.txt`.

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
campaign-specific body, create `campaigns/<slug>/invite_body.txt` and point the
script at it with `--template <path>` (no copying needed).

Runtime overrides:
- `--subject "..."` — override just the subject line.
- `--from-name "Equipe ..."` — set the From display name, so recipients see
  `Equipe ... <account@gmail.com>` instead of a bare address. Recommended for
  any outreach to people who don't already know the sending address.

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

Default files:
```bash
python3 "INVITATION EMAIL/mailer/retrieve_and_send.py" <OTS_URL>
```

Campaign-specific (PII-safe — recipients stay in a gitignored file):
```bash
python3 "INVITATION EMAIL/mailer/retrieve_and_send.py" \
  --recipients "INVITATION EMAIL/campaigns/<slug>/recipients_batch1.local.txt" \
  --template   "INVITATION EMAIL/campaigns/<slug>/invite_body.txt" \
  --from-name  "Equipe ..." \
  <OTS_URL>
```

Requires outbound access to:
- The OTS API (`https://*.onetimesecret.com`, port 443)
- Gmail SMTP (`smtp.gmail.com`, port 465)

> The Claude Code sandbox blocks SMTP (465/587 time out) — only HTTP/HTTPS
> works there. Run this on a machine with open SMTP, or use Option B.

### Option B — GitHub Actions (for restricted environments)

If your local machine can't reach those hosts (e.g. a sandboxed
environment), the GitHub Actions workflow can do the send on a hosted
runner.

**Limitation:** the runner only sees files that are *committed* to the
repo. A campaign that uses gitignored `*.local.txt` recipients (PII)
cannot run on CI — use Option A for those. The pilot recipients in
`mailer/recipients.txt` are committed and CI-safe.

**Manual dispatch:**
1. Go to the repo's **Actions** tab → **Send Invites** workflow.
2. Click **Run workflow**.
3. Paste the OTS URL into the `secret_url` input.
4. Optionally fill in:
   - `template_path` — e.g. `INVITATION EMAIL/campaigns/<slug>/invite_body.txt`
   - `recipients_path` — e.g. `INVITATION EMAIL/campaigns/<slug>/recipients.txt`
     (must be committed; gitignored files are not in the runner's checkout)
   - `from_name` — e.g. `Equipe Programadores Cariocas`
   - `subject_override` — overrides the subject line from the template
   - `dry_run` — parse and plan, but don't contact SMTP
5. Click **Run workflow**.

**Push-trigger dispatch:**

Write a `key=value` file at `INVITATION EMAIL/mailer/pending-send.url`,
commit, and push. The workflow triggers on push to that path.

Recognized keys (`url` is the only required one):
```
url=https://us.onetimesecret.com/secret/<KEY>
template=INVITATION EMAIL/campaigns/<slug>/invite_body.txt
recipients=INVITATION EMAIL/campaigns/<slug>/recipients.txt
from_name=Equipe <Sender Name>
subject=<override subject>
```

The legacy format (file contains only the bare URL) still works — the
workflow extracts the URL by regex.

After the run, the workflow deletes the trigger file and commits the
run output to `mailer/last-run-status.md`.

**Shortcut — `stage_send.sh`:**

The helper `mailer/stage_send.sh` writes the trigger for you:

```bash
# Pilot (writes pending-send.url with survey body + from-name pre-filled):
"INVITATION EMAIL/mailer/stage_send.sh" pilot https://us.onetimesecret.com/secret/<KEY>

# Batches (prints the LOCAL command — CI can't see the gitignored PII):
"INVITATION EMAIL/mailer/stage_send.sh" batch1 https://us.onetimesecret.com/secret/<KEY>
"INVITATION EMAIL/mailer/stage_send.sh" batch2 https://us.onetimesecret.com/secret/<KEY>
```

See also `mailer/pending-send.url.example` for the annotated trigger
format.

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
