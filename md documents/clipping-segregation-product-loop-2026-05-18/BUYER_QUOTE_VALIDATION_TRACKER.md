# Buyer Quote Validation Tracker

_Created 2026-05-18 by Atlas/Codex._

Use this after each real buyer/prospect conversation. Do not set final pricing
from one conversation.

Do not record private phone numbers, passwords, or sensitive political strategy.

## Current Pricing Decision

```text
final_price_decided=false
```

Reason: the product still needs buyer interviews plus operator-time data from a
pilot before a sustainable price can be set.

## Conversation Record Template

| Date | Buyer Type | Current Process | Pain | Desired Frequency | Target Count | Preferred Delivery | Quote Signal | Expected Extras | Operator Risk | Follow-Up |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| YYYY-MM-DD | vereador / assessor / consultor / campanha | manual / agency / none / tool | misses / noise / summary / speed | weekly / 2x-week / daily | 0 | dashboard / WhatsApp / email / PDF | low / viable / premium / unclear | alerts / adversaries / custom sources | low / medium / high | next action |

## Quote Signal Notes

Use ranges only as notes, not final price:

```text
too_low_for_operator_cost:
viable_for_bounded_v1:
expects_daily_or_custom_work:
needs_procurement_or_invoice:
would_pay_after_demo:
would_pay_after_30_day_pilot:
```

## Validation Rules

Before setting a permanent price, collect:

```text
at least 3 buyer conversations
at least 1 hands-on or screen-share demo reaction
at least 1 measured pilot/update run using V1_PILOT_OPERATING_LEDGER.md
operator time estimate for two updates/week + weekly summary
clear list of add-ons that must be priced separately
```

## Add-On Boundary

Treat these as add-ons unless the quote clearly covers them:

```text
daily updates
realtime alerts
adversary monitoring beyond agreed targets
custom source research
custom PDF/report design
social/TV/radio/print monitoring
Rio economic indicator methodology
client self-service target creation
```

## Post-Conversation Update

After each conversation:

1. Add a non-secret row to this tracker or a dated research note.
2. Compare requests against `OPERATOR_COST_DISCIPLINE.md`.
3. Update `V1_PILOT_OPERATING_LEDGER.md` only after actual pilot work.
4. Do not expand the base offer until repeated demand and price signal justify it.
