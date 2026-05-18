# Demo Profile Strategy

_Created 2026-05-19 by Atlas/Codex._

This document exists because the product is now technically close to demoable,
but an unsafe demo can still break the core promise: no client should see
another client's data.

## Rule

Do not demo with Flavio or Shakira credentials for an external buyer.

Use a dedicated demo/prospect profile, rotate its password after the
conversation, and keep the profile scope reviewable in `data/viewer_profiles.json`.

## Current State

```text
profile: demo_cliente
scope: []
real viewer passwords configured on Render
public empty-demo fallback: disabled while real viewer passwords exist
```

The empty demo profile proves login/session/scoping behavior, but it does not
sell product value because it has no stories.

## Demo Options

### Option A - Privacy Proof Demo

Use `demo_cliente` with an empty scope.

Best for:

- showing the login gate;
- proving that an empty profile does not fall back to all data;
- proving operator controls are hidden.

Weakness:

- it does not show useful clipping content.

### Option B - Controlled Operator Demo

Otavio logs in locally or on Render with an internal viewer profile and shares
screen only. Do not share credentials with the buyer.

Best for:

- showing real grouped stories;
- avoiding password leakage;
- keeping Flavio/Shakira data under operator control.

Weakness:

- the buyer cannot explore alone.

### Option C - Dedicated Prospect Profile

Create a named profile only for that conversation:

```text
profile key: prospect_<short_name>
allowed targets: explicitly agreed safe target keys
password: generated in Render env only
expiry/rotation: immediately after demo unless buyer continues
```

Best for:

- serious buyer conversation;
- limited hands-on demo;
- verifying actual client onboarding flow.

Requirements:

- no Flavio/Shakira target keys unless explicitly safe and approved;
- no static export as access layer;
- no target-management/admin controls for the prospect;
- logged-out JSON/API checks before sharing;
- password rotation/offboarding plan written before the call.

## Recommended Next Demo Path

For the first external sales conversation:

1. Use Option B for the main walkthrough.
2. Use Option A only as a privacy proof if needed.
3. Create Option C only when the prospect is serious enough to justify password
   setup and rotation.

## Pre-Demo Checklist

```text
GET /healthz -> viewerAuthConfigured=true
GET /assets/clipping-data.json logged out -> 401
GET /assets/clipping-raw-texts.json logged out -> 401
profile payload contains only approved targets
raw texts contain only approved article keys
viewer POST /api/targets -> 401/403
operator controls hidden in viewer shell
static export not used
password rotation/offboarding noted
```

## Do Not Promise

- self-service target creation;
- a separate website per buyer;
- live alerts or daily AI summaries in the base package;
- a finished Rio economic indicator;
- access to any existing private client profile.
