# V1 Add-On Menu And Boundaries

_Created 2026-05-18 by Atlas/Codex._

This converts the market-research and cost-discipline notes into a sales
boundary. It does not set final prices.

## Base Offer

The base V1 offer stays:

```text
30-day pilot
private scoped dashboard
up to 5 agreed targets/terms
2 operator-run updates per week
1 lightweight weekly summary
password/profile support
```

The base offer is intentionally narrow so it can fund the tool without becoming
unlimited political intelligence work.

## Add-Ons To Price Separately

| Add-On | Trigger | Why Separate |
| --- | --- | --- |
| Extra update run | More than 2 updates/week | Increases operator time and source failures. |
| Daily monitoring | Daily expected review/summary | Creates near-realtime expectation. |
| Extra target/topic | More than 5 agreed terms | Increases query noise, QA, and visual clutter. |
| Adversary monitoring | Opponent names or attack narratives | Higher political sensitivity and more false positives. |
| Custom source onboarding | New site/source beyond current collectors | Requires source debugging and maintenance. |
| WhatsApp/PDF report | Designed or repeated formatted delivery | Adds manual formatting/support time. |
| Human classification pass | Sentiment/category review for many articles | Requires judgment work, not just collection. |
| Rio economic topic report | Economic methodology or topic dashboard | Separate research/product track, not normal clipping. |
| Crisis alert mode | Fast alerts during controversy | Requires monitoring cadence outside V1. |

## Buyer Conversation Rule

If a buyer asks for an add-on, capture:

```text
requested_add_on:
reason:
frequency:
who_reads_it:
would_pay_more: yes/no/unclear
operator_time_risk: low/medium/high
```

Do not include the add-on in the base pilot unless it is explicitly part of a
paid experiment.

## Product Discipline

Before accepting an add-on, answer:

```text
Does it reuse existing scoped backend behavior?
Can it be verified without exposing another profile?
Can it be delivered manually in the pilot without breaking schedule?
Does it create recurring AI/tool cost?
Would at least two future clients likely pay for it?
```

If the answers are weak, keep it as a later custom proposal.

## What To Say In A Sales Call

Use this boundary:

```text
O piloto base e enxuto: painel privado, duas atualizacoes por semana e um
resumo semanal curto. Coisas como monitoramento diario, adversarios, fontes
customizadas, PDF/WhatsApp recorrente ou analise mais profunda entram como
modulos separados, porque mudam muito o custo de operacao.
```

## Link Back

Use with:

```text
V1_DELIVERY_SCOPE.md
V1_DELIVERY_FORMAT_DECISION.md
OPERATOR_COST_DISCIPLINE.md
BUYER_QUOTE_VALIDATION_TRACKER.md
MARKET_RESEARCH_POLITICAL_COMPETITOR_PASS_2026-05-18.md
```
