# Invitation Email System

Self-contained mass-email toolkit for sending one identical email to a list
of recipients through Gmail SMTP, with credentials handed over securely via
a one-time-secret link.

Stdlib-only Python. No `pip install` needed. Tested on Python 3.10+.

---

## Quick start

1. **Auth** — [HOW_TO_AUTH.md](HOW_TO_AUTH.md): generate a Gmail App Password
   and stash it in a one-time-secret link.
2. **Send** — [HOW_TO_SEND.md](HOW_TO_SEND.md): point the mailer at your
   recipients, template, and OTS link. Dry-run first, then live send.
3. **New campaign** — [HOW_TO_ADD_CAMPAIGN.md](HOW_TO_ADD_CAMPAIGN.md): how
   to add a new campaign subfolder for a new mailing.

---

## Folder layout

```
INVITATION EMAIL/
├── README.md                 you are here
├── HOW_TO_AUTH.md             Gmail App Password + OTS credential handoff
├── HOW_TO_SEND.md             dry-run, recipients format, commands, troubleshooting
├── HOW_TO_ADD_CAMPAIGN.md     recipe for adding a new campaign
├── CLAUDE_HANDOFF.md          for a future Claude session with zero chat context
├── .gitignore
├── mailer/                    the reusable code
│   ├── retrieve_and_send.py    fetches creds from OTS, sends via SMTP
│   ├── invite_template.txt     generic stub template
│   ├── recipients.txt          example / test recipient list
│   ├── last-run-status.md      latest run outcome
│   └── HISTORICAL/             iteration history from the original build
└── campaigns/                 one subfolder per mailing
    ├── claude-impact-lab-rio/   past campaign (hackathon, 2026-05-24)
    └── programadores-cariocas-survey/   current task
```

---

## How it works (30-second version)

```
retrieve_and_send.py <OTS_URL>
  │
  ├─ POSTs to the OTS API → gets GMAIL_USER + GMAIL_APP_PASSWORD
  │   (link self-destructs on read; creds held in memory only)
  │
  ├─ Loads recipients.txt + invite_template.txt
  │
  ├─ Connects to smtp.gmail.com:465 (TLS)
  ├─ Logs in with the App Password
  ├─ Sends one message per recipient
  └─ Reports per-address success / failure
```

The GitHub Actions workflow (`.github/workflows/send-invites.yml`) can also
run it on a hosted runner — useful when your local machine has restricted
egress. See [HOW_TO_SEND.md](HOW_TO_SEND.md) for both paths.

---

## Security model

- **No plaintext password in chat.** Only a one-time URL is exchanged; it
  dies on first read.
- **Nothing on disk.** Credentials are local Python variables — no file
  writes, no environment leaks.
- **`.gitignore` blocks accidents.** `*.secret`, `*.env`, `credentials.*`,
  and `*.local.*` are pre-blocked from git.
- **App Password is revocable.** One click at
  <https://myaccount.google.com/apppasswords>. The Gmail account itself stays
  untouched.
- **Short TTL.** OTS link lifetime of 5–30 minutes means the window of
  exposure is tiny even if the URL leaks.
