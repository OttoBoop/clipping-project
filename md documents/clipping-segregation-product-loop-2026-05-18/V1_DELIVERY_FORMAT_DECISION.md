# V1 Delivery Format Decision

_Created 2026-05-18 by Atlas/Codex._

This closes the first delivery-format question from `FIRST_SELLABLE_PACKAGE.md`
and `V1_DELIVERY_SCOPE.md`.

## Decision

The first sellable pilot is:

```text
private scoped dashboard
+ two operator-run updates per week
+ one weekly lightweight written summary
```

The weekly summary can be delivered as plain text, email, WhatsApp message, or a
small PDF/screenshot bundle depending on the buyer, but the base promise is the
content, not a custom designed report.

## Why Not Dashboard Only

Dashboard-only is technically simpler, but weaker commercially. A political
office may not remember to open the site, and the buyer needs a visible weekly
artifact to feel the service exists.

## Why Not Daily/Realtime

Daily or realtime updates are too expensive for V1 unless priced separately.
They increase operator burden, support expectations, and AI/tool usage before
the first client proves willingness to pay.

## Included Weekly Summary

Keep the weekly summary small:

```text
3 to 7 bullet points
links back to the private dashboard
important repeats or emerging story clusters
obvious false-positive/missed-story note when relevant
no long political analysis unless separately priced
```

## Delivery Channels

Allowed in V1:

```text
private dashboard as source of truth
plain text weekly summary
manual screenshot/export when useful
email or WhatsApp delivery by Otavio/operator
```

Not included in V1 base:

```text
custom branded PDF template
automated WhatsApp bot
client self-service report builder
daily AI narrative brief
realtime alerts
```

## Operating Rule

The weekly summary must be written from the scoped client view. Do not build it
from unscoped raw data or another client's dashboard.

Before sending any summary:

```text
confirm active profile
confirm targets are only approved target keys
confirm story links/raw texts are scoped
confirm no Flavio/Shakira/Rio material leaks into another client
log time spent so pricing can be calibrated
```

## Open Pricing Question

Price is still not final. Use the first pilot to measure:

```text
minutes per update run
minutes per weekly summary
number of target terms
number of useful stories
support/password friction
```
