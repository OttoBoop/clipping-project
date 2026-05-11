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
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR / "invite_template.txt"
RECIPIENTS_PATH = SCRIPT_DIR / "recipients.txt"

ONETIMESECRET_KEY_RE = re.compile(r"/secret/([A-Za-z0-9]{16,})")


def fetch_secret_from_url(url: str) -> str:
    """Retrieve the one-time secret value via the onetimesecret REST API.

    The share URL looks like https://<region>.onetimesecret.com/secret/<KEY>.
    The API endpoint is the same host with /api/v1/secret/<KEY>, POST.
    """
    m = ONETIMESECRET_KEY_RE.search(url)
    if not m:
        raise SystemExit(
            f"Could not parse a onetimesecret key from URL:\n  {url}\n"
            "Expected something like https://us.onetimesecret.com/secret/<KEY>."
        )
    key = m.group(1)
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc or "us.onetimesecret.com"
    api_url = f"https://{host}/api/v1/secret/{key}"

    req = urllib.request.Request(
        api_url,
        method="POST",
        headers={"Accept": "application/json", "User-Agent": "penelope-invites/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace") if e.fp else ""
        raise SystemExit(
            f"HTTP {e.code} from {api_url}.\n"
            "Likely causes: the secret was already viewed, has expired, or the URL is wrong.\n"
            f"Server response: {body[:500]}"
        )
    except urllib.error.URLError as e:
        raise SystemExit(f"Network error talking to onetimesecret: {e}")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise SystemExit(
            f"Unexpected non-JSON response from {api_url}:\n{raw[:500]}"
        )

    value = payload.get("value")
    if not value:
        raise SystemExit(
            f"Onetimesecret returned no 'value' field. Full response keys: "
            f"{sorted(payload.keys())}. The secret may have already been read."
        )
    return value


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


def load_recipients() -> list[str]:
    if not RECIPIENTS_PATH.exists():
        raise SystemExit(f"recipients.txt not found at {RECIPIENTS_PATH}")
    out: list[str] = []
    for raw in RECIPIENTS_PATH.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    if not out:
        raise SystemExit("recipients.txt is empty.")
    return out


def load_template() -> tuple[str, str]:
    """Return (subject, body). Template format::

        Subject: <one line>
        <blank line>
        <body, possibly multi-line>
    """
    if not TEMPLATE_PATH.exists():
        raise SystemExit(f"invite_template.txt not found at {TEMPLATE_PATH}")
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
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
) -> None:
    msg = EmailMessage()
    msg["From"] = from_addr
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
        help="Override the subject from invite_template.txt.",
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

    recipients = load_recipients()
    subject, body = load_template()
    if args.subject:
        subject = args.subject

    print(f"[plan] from        : {user}")
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
                    send_one(smtp, user, addr, subject, body)
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
