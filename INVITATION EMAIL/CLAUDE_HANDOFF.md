# Claude Handoff

Context for a future Claude session that has zero chat history with this
project. Read this first, then follow the links.

---

## What this folder is

A self-contained mass-email toolkit. It sends one identical email to a list
of recipients through Gmail SMTP, with credentials transported securely via
one-time-secret links. No pip dependencies — stdlib only.

## Where to start reading

1. [README.md](README.md) — overview, folder layout, security model.
2. [HOW_TO_AUTH.md](HOW_TO_AUTH.md) — how to generate a Gmail App Password
   and create an OTS credential link.
3. [HOW_TO_SEND.md](HOW_TO_SEND.md) — recipient format, template format,
   dry-run testing, local and CI send paths.
4. [HOW_TO_ADD_CAMPAIGN.md](HOW_TO_ADD_CAMPAIGN.md) — how to add a new
   campaign subfolder.

## Where the code is

- `mailer/retrieve_and_send.py` — the mailer script. Reads creds from an
  OTS URL (or `--secret-file` for offline testing), loads
  `invite_template.txt` and `recipients.txt` from its own directory, sends
  via `smtplib.SMTP_SSL`.
- `.github/workflows/send-invites.yml` — GitHub Actions workflow that runs
  the script on a hosted runner (for when local egress is blocked).

## Where each campaign's brief is

Each subfolder under `campaigns/` has a `brief.md` explaining the campaign's
purpose, recipient source, sender, and deadline. Start there to understand
what a specific mailing is about.

Current campaigns:
- `campaigns/claude-impact-lab-rio/` — hackathon invitation (2026-05-24).
- `campaigns/programadores-cariocas-survey/` — survey to Programadores
  Cariocas alumni (in progress).

## Conventions

- **Sequential commits.** One logical change per commit.
- **No PII in commits.** Recipient lists with real addresses use the
  `.local.txt` suffix (gitignored). Only commit the extraction script and
  aggregate stats — never the addresses themselves.
- **Credentials never in chat.** Always hand off via OTS link. See
  HOW_TO_AUTH.md.
- **Dry-run before live send.** Always validate with `--dry-run` first.
- **Campaign isolation.** Each mailing gets its own `campaigns/<slug>/`
  subfolder. Don't mix campaign-specific content into the kit root or the
  `mailer/` directory.
