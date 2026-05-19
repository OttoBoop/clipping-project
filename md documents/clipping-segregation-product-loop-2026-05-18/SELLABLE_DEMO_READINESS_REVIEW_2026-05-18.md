# Sellable Demo Readiness Review - 2026-05-18

_Created by Atlas/Codex after the Rio read-only panel and Render operations
review were deployed._

This is a yes/no review for what Otavio can safely show to a political buyer
without exposing another client, overpromising, or creating fake UI.

## Current Decision

```text
controlled operator demo: yes
hands-on external password: only after dedicated demo/prospect profile setup
first paid-client onboarding: not automatic; needs real prospect scope and password rotation plan
Rio economic indicator as finished product: no
```

## What Is Safe To Show Now

Use Render:

```text
https://clipping-project.onrender.com/
```

Safe demo modes:

- operator screen-share of a known scoped viewer profile;
- login/privacy proof with a dedicated safe demo profile;
- explanation of how client profiles map to scoped targets;
- grouped stories, article links, and raw text only within the current profile;
- absence of update runner, target management, and classification editor in the
  viewer shell;
- Rio economic panel as an internal/read-only methodology preview only if the
  viewer is `rio_economico` or admin.

## What Is Not Safe To Share Broadly Yet

- Flavio, Shakira, Rio, or admin credentials;
- GitHub Pages, Wix, static export, or raw report file as private access;
- a live password for a prospect before offboarding is written;
- claims that the Rio economic indicator is finished;
- self-service target creation;
- realtime alerts;
- daily AI-written report as base offer;
- custom site/repo per client.

## Current Live Proof To Mention

Non-secret proof from recent Render smokes:

```text
GET / -> login page
GET /assets/clipping-data.json -> 401 viewer_login_required
GET /assets/clipping-raw-texts.json -> 401 viewer_login_required
GET /api/reports/rio-economic-topic -> 401 viewer_login_required
GET /api/targets -> 401 viewer_login_required
GET /api/classifications -> 401 viewer_login_required
GET /healthz -> viewerAuthConfigured=true, viewerProfilesConfigured=true, missingConfig=[]
```

Product proof:

- the private surface is the FastAPI app on Render;
- public static JSON payloads are not the paid-client surface;
- profile scopes live in reviewable config;
- passwords live outside Git;
- the Rio topic report is a scoped endpoint and read-only UI, not a normal
  target row.

## Demo Script For Tomorrow

Use this order:

1. Show the login page.
2. Explain that a password maps to a profile/workspace.
3. Log in by screen-share with a safe profile, or use a dedicated
   prospect/demo profile if one exists.
4. Show the small target/filter list for that profile.
5. Open a grouped story.
6. Open one article and raw text only if it belongs to that profile.
7. Show that client UI does not expose update runner, target management, or
   classification editing.
8. State the V1 pilot boundary:

```text
30 dias, ate 5 nomes/termos, 2 atualizacoes por semana, painel privado e 1
resumo semanal curto.
```

9. Ask what delivery format they would actually read: dashboard, WhatsApp,
   email, or lightweight PDF/screenshot.
10. If they ask for daily alerts, adversaries, custom sources, or Rio economic
    methodology, mark it as add-on validation, not base scope.

## Go / No-Go For Hands-On Access

Hands-on external access is allowed only when all are true:

```text
prospect/profile key chosen
allowed target keys written
offboarding date written
password generated outside Git/chat
Render CLIPPING_VIEWER_PASSWORDS updated with replace=false
logged-out JSON/API smoke passes after env change
profile payload/raw text proof passes
forbidden target_key live-results check passes
viewer write attempt returns 401 or 403
old access removal plan written
```

If any line is missing, use operator screen-share instead.

## Remaining Blockers

- This shell does not have viewer/admin passwords, so it cannot repeat positive
  authenticated browser proof.
- No real prospect/buyer conversation has happened in this repo, so final price
  remains undecided.
- No measured pilot exists yet in `V1_PILOT_OPERATING_LEDGER.md`, so operator
  time and AI/tool cost are still assumptions.
- Admin target-management/CSRF proof still needs operator credentials.

## Next Validation Needed

Record the first real buyer reaction in:

```text
BUYER_QUOTE_VALIDATION_TRACKER.md
```

Record the first real pilot/update-time measurements in:

```text
V1_PILOT_OPERATING_LEDGER.md
```

Do not expand the base offer until at least one demo reaction and one measured
operator run exist.
