# How to Authenticate (Gmail App Password + OTS handoff)

This guide walks through the one-time setup for sending emails through a
Gmail account using this toolkit. Total time: ~5 minutes.

---

## Step 1 — Pick the sender Gmail account

Choose the Gmail account the emails will be sent **from**. This can be a
personal `@gmail.com` address or a Google Workspace `@yourdomain.com`
address.

Rate limits to keep in mind:
- **Personal Gmail:** 500 recipients per day.
- **Google Workspace:** 2 000 recipients per day.

You need login access to this account (or someone who can do the next steps
on your behalf).

---

## Step 2 — Enable 2-Step Verification

Google requires 2-Step Verification before it will let you create App
Passwords.

1. Sign into the sender Gmail account.
2. Go to <https://myaccount.google.com/security>.
3. Under **"How you sign in to Google"**, click **2-Step Verification**.
4. Follow the prompts (phone number, backup codes, etc.).
5. Once it shows **"2-Step Verification is ON"**, you're done.

If it was already on, skip to Step 3.

---

## Step 3 — Generate an App Password

1. Go to <https://myaccount.google.com/apppasswords>.
2. You may need to re-enter the account password.
3. Under **"App name"**, type anything descriptive (e.g. `Mailer script`).
4. Click **Create**.
5. Google shows a 16-character password formatted like:

   ```
   abcd efgh ijkl mnop
   ```

6. **Copy it now.** Google will never show it again. (If you lose it, just
   revoke it and create a new one — there's no limit.)

The spaces are cosmetic. The script accepts both `abcdefghijklmnop` and
`abcd efgh ijkl mnop`.

**Why App Passwords?** Gmail SMTP no longer accepts regular account
passwords. App Passwords are scoped to mail only — they can't change your
account settings, read your inbox, or do anything except send via SMTP.
Revoking one is instant and doesn't affect your account.

---

## Step 4 — Create the one-time-secret link

The App Password needs to reach whoever runs the mailer script (you, a
colleague, or a Claude session) without ever being pasted in plaintext into
a chat, email, or document.

1. Open <https://us.onetimesecret.com/> (or any region: `eu.`, `uk.`,
   `ca.`, `nz.`).
2. In the **"Secret content"** box, paste **exactly these two lines**:

   ```
   GMAIL_USER=sender@gmail.com
   GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
   ```

   Replace `sender@gmail.com` with the actual sender address, and the
   password with the one you just generated.

3. Set **Lifetime** to **5–30 minutes**. Shorter is better.
4. Leave the **Passphrase** field empty (adds friction for no security gain
   in this flow).
5. Click **Create a secret link**.
6. Copy the URL it gives you. It looks like:

   ```
   https://us.onetimesecret.com/secret/abc123def456...
   ```

**This URL is the only thing you share.** Paste it into the chat, the
workflow dispatch input, or wherever the script will read it from. The link
self-destructs the instant it's read — if someone intercepts the URL after
the script consumed it, they get nothing.

---

## Step 5 — After the send

Revoke the App Password if you don't need it again:

1. Go to <https://myaccount.google.com/apppasswords>.
2. Click the trash icon next to the one you created.

The Gmail account is unaffected. You can always create a new App Password
later for the next campaign.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `SMTPAuthenticationError` | Used the real Gmail password instead of the App Password, or the App Password was revoked. | Generate a new App Password (Step 3) and create a fresh OTS link. |
| App Passwords page says "This setting is not available" | 2-Step Verification is not enabled on the account. | Complete Step 2 first. |
| OTS link says "Unknown secret" | The link was already viewed (by you, by the script, or by someone else), or the TTL expired. | Create a new OTS link (Step 4) with a fresh copy of the same credentials. |
| `Could not retrieve the secret from any region` | The secret was created on one OTS region but the script tried a different one. | The script tries all regions automatically. If it still fails, the secret was likely already consumed. Create a new one. |
