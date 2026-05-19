# Buyer Quote Validation Tracker

_Created 2026-05-18 by Atlas/Codex._

Use this after each real buyer/prospect conversation. Do not set final pricing
from one conversation.

Do not record private phone numbers, passwords, or sensitive political strategy.

## Current Pricing Decision

```text
final_price_decided=false
real_buyer_conversation_count=0
hands_on_demo_reaction_count=0
measured_pilot_run_count=0
```

Reason: the product still needs buyer interviews plus operator-time data from a
pilot before a sustainable price can be set.

## Current Readiness - 2026-05-20

The product is ready for a controlled operator demo, but the tracker must remain
empty until a real buyer/prospect conversation happens.

Use:

```text
SELLABLE_DEMO_READINESS_REVIEW_2026-05-18.md
DEMO_SCRIPT_AND_BUYER_ASSUMPTIONS.md
V1_DELIVERY_SCOPE.md
V1_ADD_ON_MENU_AND_BOUNDARIES.md
```

Current no-fabrication rule:

```text
do not create a buyer row from assumptions
do not set a final price from desk research
do not record private contact details
do not turn an add-on request into base scope after one conversation
```

First valid row requires at least:

```text
real person or office type spoken to
current clipping process
pain stated in their words
desired frequency
preferred delivery format
quote signal or refusal
operator risk notes
follow-up action
```

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

Before treating `measured_pilot_run_count` as real, run:

```text
python3 -B tools/pilot_ledger_check.py
```

This prevents the template ledger rows or guessed operator time from becoming
fake pricing evidence.

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
