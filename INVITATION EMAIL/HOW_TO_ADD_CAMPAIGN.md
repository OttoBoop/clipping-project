# How to Add a New Campaign

Each mailing (event invitation, survey link, announcement, etc.) gets its
own subfolder under `campaigns/`. This keeps campaign-specific content
(body text, recipient lists, briefs) separate from the reusable mailer code.

---

## Steps

### 1. Create the subfolder

```bash
mkdir -p "INVITATION EMAIL/campaigns/<slug>/"
```

Pick a short, descriptive slug: `claude-impact-lab-rio`,
`programadores-cariocas-survey`, `onboarding-batch-3`, etc.

### 2. Add a brief

Create `campaigns/<slug>/brief.md` with:

- **Purpose:** what this mailing is for.
- **Recipient source:** where the addresses come from (spreadsheet, CRM
  export, manual list, etc.).
- **Sender:** which Gmail account will send, and who controls it.
- **Signatory / tone:** who signs the email, formal vs. informal.
- **Deadline:** when the send needs to happen.
- **PII policy:** can the recipient list be committed, or must it stay
  local (`.local.txt`)?

### 3. Add the email body

Create `campaigns/<slug>/invite_body.txt` in the standard template format:

```
Subject: Your subject line

Body text here.
Multiple lines are fine.
```

### 4. Add the recipient list

Create one of:

- `campaigns/<slug>/recipients.txt` — if addresses are OK to commit
  (e.g. public mailing list, test addresses).
- `campaigns/<slug>/recipients.local.txt` — if addresses are PII.
  `.gitignore` covers `*.local.*` so it won't be committed.

Format: one email per line, `#` for comments, blank lines ignored.

### 5. Wire up the mailer

Before sending, copy (or symlink) the campaign's body and recipient list
into the mailer's working directory:

```bash
cp "INVITATION EMAIL/campaigns/<slug>/invite_body.txt" \
   "INVITATION EMAIL/mailer/invite_template.txt"
cp "INVITATION EMAIL/campaigns/<slug>/recipients.txt" \
   "INVITATION EMAIL/mailer/recipients.txt"
```

### 6. Dry-run

```bash
printf 'GMAIL_USER=fake@gmail.com\nGMAIL_APP_PASSWORD=xxxx\n' > /tmp/f.txt
python3 "INVITATION EMAIL/mailer/retrieve_and_send.py" \
    --secret-file /tmp/f.txt --dry-run
rm /tmp/f.txt
```

Confirm: correct subject, correct body, correct recipient count.

### 7. Live send

Follow [HOW_TO_SEND.md](HOW_TO_SEND.md) section 4 (local or CI).

### 8. Log the result

After the send, record the outcome in `campaigns/<slug>/loop_log.md`
(or create one if this is the first run). Include: date, recipient count,
success/failure counts, any issues encountered.
