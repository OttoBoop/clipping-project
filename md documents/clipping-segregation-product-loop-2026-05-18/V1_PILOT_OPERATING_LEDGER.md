# V1 Pilot Operating Ledger

_Created 2026-05-18 by Atlas/Codex._

Use this during any first paid or serious trial client. The goal is to measure
whether the service funds the tool instead of becoming unpaid manual work.

Do not put passwords, private buyer phone numbers, or secrets in this file.

## Pilot Header

```text
client_or_prospect:
profile_key:
pilot_start:
pilot_end:
approved_targets:
update_frequency:
delivery_format:
operator:
```

## Per-Update Ledger

| Date | Profile | Action | Minutes | Targets Checked | Useful Stories | False Positives | Missed Items | AI/Tool Cost Note | Support Issue | Follow-Up |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| YYYY-MM-DD | profile_key | update_run / qa / summary / support / password_rotation | 0 | 0 | 0 | 0 | 0 | none | none | next action |

## Weekly Summary Ledger

| Week | Minutes To Prepare | Bullets Sent | Manual Screenshots/Exports | Buyer Reply | Renewal Signal | Scope Creep Risk |
| --- | --- | --- | --- | --- | --- | --- |
| YYYY-WW | 0 | 0 | none | none | unknown | none |

## Cost Discipline Review

At the end of the pilot, answer:

```text
average minutes per update:
average minutes per weekly summary:
support minutes:
number of target changes requested:
number of add-on requests:
collector/source problems:
AI/tool cost concerns:
minimum sustainable monthly price:
should this client renew:
what must be priced separately:
```

## Stop/Adjust Triggers

Escalate pricing, reduce scope, or stop the pilot if:

```text
client requests daily/realtime updates without add-on price
client requests unlimited targets or custom sources
weekly summary takes more than planned two weeks in a row
false positives require heavy manual review every update
password/support friction becomes recurring
static export or unscoped data is requested as private access
```

## Link Back To Product Rules

Use with:

```text
V1_DELIVERY_SCOPE.md
V1_DELIVERY_FORMAT_DECISION.md
OPERATOR_COST_DISCIPLINE.md
FIRST_CLIENT_ONBOARDING_CHECKLIST.md
DEMO_PROFILE_STRATEGY.md
```
