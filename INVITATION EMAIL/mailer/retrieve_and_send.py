#!/usr/bin/env python3
"""
retrieve_and_send.py — fetch Gmail credentials from a one-time-secret link
(or a local fixture file for testing) and send one identical invitation
email to every address in recipients.txt.

Credentials live in memory only. Nothing is written to disk.

Usage
-----
    # Real send
    python retrieve_and_send.py https://us.onetimesecret.com/secret/<KEY>

    # Real send with overridden subject
    python retrieve_and_send.py https://us.onetimesecret.com/secret/<KEY> \\
        --subject "Convite"

    # Dry run against a real URL (still fetches & burns the secret, just
    # doesn't talk to SMTP)
    python retrieve_and_send.py https://us.onetimesecret.com/secret/<KEY> \\
        --dry-run

    # Offline test using a local fixture file (no network)
    python retrieve_and_send.py --secret-file ./fixture.txt --dry-run

Secret payload format (whatever the one-time-secret contains, OR the
contents of --secret-file)::

    GMAIL_USER=youraccount@gmail.com
    GMAIL_APP_PASSWORD=abcd efgh ijkl mnop

Lines may be in any order. Blank lines and `#`-comment lines are ignored.
Values may be optionally wrapped in single or double quotes.

The Gmail password MUST be a Google **App Password**
(https://myaccount.google.com/apppasswords), not the regular account
password. Gmail SMTP does not accept account passwords anymore.
"""

from __future__ import annotations

import argparse
import json
import re
import smtplib
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR / "invite_template.txt"
RECIPIENTS_PATH = SCRIPT_DIR / "recipients.txt"

ONETIMESECRET_KEY_RE = re.compile(r"/secret/([A-Za-z0-9]{16,})")

# OTS has separate regional databases. A secret created on `us.` won't be
# visible from `eu.`. Browsers sometimes get routed to a region based on
# geo, but the displayed URL might not match the database the secret
# actually landed in. So we try all regions until one returns 200.
# A 404 from a region just means "not in this database" -- no burn.
OTS_REGIONS = [
    "us.onetimesecret.com",
    "eu.onetimesecret.com",
    "uk.onetimesecret.com",
    "ca.onetimesecret.com",
    "nz.onetimesecret.com",
    "onetimesecret.com",
]


def fetch_secret_from_url(url: str) -> str:
    """Retrieve the one-time secret value via the onetimesecret REST API.

    Tries the region in the URL first, then every other region. A
    successful 200 burns the secret in that region. 404s elsewhere are
    harmless.
    """
    m = ONETIMESECRET_KEY_RE.search(url)
    if not m:
        raise SystemExit(
            f"Could not parse a onetimesecret key from URL:\n  {url}\n"
            "Expected something like https://us.onetimesecret.com/secret/<KEY>."
        )
    key = m.group(1)
    parsed = urllib.parse.urlparse(url)
    primary_host = parsed.netloc or OTS_REGIONS[0]
    ordered = [primary_host] + [r for r in OTS_REGIONS if r != primary_host]

    diagnostic: list[str] = []
    for host in ordered:
        api_url = f"https://{host}/api/v1/secret/{key}"
        req = urllib.request.Request(
            api_url,
            method="POST",
            headers={"Accept": "application/json", "User-Agent": "penelope-invites/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
                status = resp.status
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace") if e.fp else ""
            diagnostic.append(f"  {host} -> HTTP {e.code}: {body[:200]}")
            continue
        except urllib.error.URLError as e:
            diagnostic.append(f"  {host} -> URLError: {e}")
            continue

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            diagnostic.append(f"  {host} -> HTTP {status}: non-JSON body: {raw[:200]}")
            continue

        value = payload.get("value")
        if value:
            print(f"[ots] retrieved secret from {host} (HTTP {status})")
            return value

        # 200 but no value -> some other OTS quirk (already viewed, requires passphrase, etc.)
        msg = payload.get("message") or "no value field"
        diagnostic.append(f"  {host} -> HTTP {status}: {msg}; keys={sorted(payload.keys())}")

    raise SystemExit(
        "Could not retrieve the secret from any onetimesecret region.\n"
        "Tried (in order):\n" + "\n".join(diagnostic) + "\n\n"
        "If every region says \"Unknown secret\", the link was already viewed "
        "or has expired. Generate a fresh one-time-secret and try again."
    )


def read_local_secret(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"--secret-file does not exist: {path}")
    return p.read_text(encoding="utf-8")


def parse_credentials(payload: str) -> tuple[str, str]:
    """Parse GMAIL_USER and GMAIL_APP_PASSWORD from a dotenv-like payload."""
    creds: dict[str, str] = {}
    for line in payload.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip().upper()
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
            v = v[1:-1]
        if k in ("GMAIL_USER", "GMAIL_APP_PASSWORD"):
            creds[k] = v

    user = creds.get("GMAIL_USER", "")
    pw = creds.get("GMAIL_APP_PASSWORD", "")
    if not user or not pw:
        raise SystemExit(
            "Secret payload must contain BOTH lines:\n"
            "  GMAIL_USER=youraccount@gmail.com\n"
            "  GMAIL_APP_PASSWORD=<16-char app password>\n"
            f"Got user={'set' if user else 'MISSING'}, "
            f"password={'set' if pw else 'MISSING'}."
        )
    return user, pw


def load_recipients(path: Path) -> list[str]:
    if not path.exists():
        raise SystemExit(f"recipients file not found at {path}")
    out: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    if not out:
        raise SystemExit(f"recipients file is empty: {path}")
    return out


def load_template(path: Path) -> tuple[str, str]:
    """Return (subject, body). Template format::

        Subject: <one line>
        <blank line>
        <body, possibly multi-line>
    """
    if not path.exists():
        raise SystemExit(f"template file not found at {path}")
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    subject = "Invitation"
    body_start = 0
    for i, line in enumerate(lines):
        if line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            body_start = i + 1
            break
    while body_start < len(lines) and not lines[body_start].strip():
        body_start += 1
    body = "\n".join(lines[body_start:]).rstrip() + "\n"
    return subject, body


def send_one(
    smtp: smtplib.SMTP_SSL,
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
    from_name: str | None = None,
) -> None:
    msg = EmailMessage()
    msg["From"] = formataddr((from_name, from_addr)) if from_name else from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    smtp.send_message(msg)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fire one invitation email to every address in recipients.txt.",
    )
    ap.add_argument(
        "url",
        nargs="?",
        help="Full onetimesecret URL: https://<region>.onetimesecret.com/secret/<KEY>",
    )
    ap.add_argument(
        "--secret-file",
        help="Read the credential payload from a local file instead (offline testing).",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and plan, but don't connect to SMTP.",
    )
    ap.add_argument(
        "--subject",
        help="Override the subject from the template.",
    )
    ap.add_argument(
        "--recipients",
        help="Path to the recipients file (default: mailer/recipients.txt). "
        "Point this at a gitignored *.local.txt to keep PII out of the repo.",
    )
    ap.add_argument(
        "--template",
        help="Path to the template file (default: mailer/invite_template.txt).",
    )
    ap.add_argument(
        "--from-name",
        help="Display name for the From header, e.g. 'Equipe Programadores Cariocas'. "
        "Renders as: From-Name <account@gmail.com>.",
    )
    args = ap.parse_args()

    if args.secret_file and args.url:
        ap.error("Pass either a URL OR --secret-file, not both.")
    if args.secret_file:
        payload = read_local_secret(args.secret_file)
    elif args.url:
        payload = fetch_secret_from_url(args.url)
    else:
        ap.error("Pass a onetimesecret URL, or --secret-file for offline testing.")

    user, password = parse_credentials(payload)
    payload = ""  # drop the reference; the local string above goes out of scope at return

    recipients_path = Path(args.recipients) if args.recipients else RECIPIENTS_PATH
    template_path = Path(args.template) if args.template else TEMPLATE_PATH
    recipients = load_recipients(recipients_path)
    subject, body = load_template(template_path)
    if args.subject:
        subject = args.subject

    from_display = formataddr((args.from_name, user)) if args.from_name else user
    print(f"[plan] from        : {from_display}")
    print(f"[plan] subject     : {subject}")
    print(f"[plan] recipients  : {len(recipients)}")
    for r in recipients:
        print(f"         - {r}")
    print(f"[plan] body preview:")
    print("---")
    print(body, end="" if body.endswith("\n") else "\n")
    print("---")

    if args.dry_run:
        print("[dry-run] not contacting SMTP. credentials were parsed but unused.")
        return 0

    print("[smtp] connecting to smtp.gmail.com:465 ...")
    ctx = ssl.create_default_context()
    successes: list[str] = []
    failures: list[tuple[str, str]] = []
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx, timeout=30) as smtp:
            smtp.login(user, password)
            for addr in recipients:
                try:
                    send_one(smtp, user, addr, subject, body, from_name=args.from_name)
                    successes.append(addr)
                    print(f"[ok]    {addr}")
                except Exception as e:
                    failures.append((addr, str(e)))
                    print(f"[FAIL]  {addr} -- {e}")
    except smtplib.SMTPAuthenticationError as e:
        raise SystemExit(
            "SMTP authentication failed.\n"
            "Make sure GMAIL_APP_PASSWORD is a 16-character App Password from\n"
            "https://myaccount.google.com/apppasswords (2-Step Verification must\n"
            f"be on for the account first).\nServer said: {e.smtp_error.decode('utf-8','replace') if isinstance(e.smtp_error, bytes) else e.smtp_error}"
        )

    print()
    print(f"[done] {len(successes)} sent, {len(failures)} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
