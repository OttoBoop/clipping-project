# Market Research Refresh - 2026-05-20

_Created by Atlas/Codex during the segregation product loop._

This is a current desk-research refresh. It does not set final pricing and does
not replace buyer interviews or pilot-time measurement.

## Scope

Question: after the segregation work and V1 package guardrails, does the public
market still support a narrow, private clipping pilot for political offices?

Evidence date:

```text
2026-05-20
```

## Sources Checked

| Source | Buyer / Positioning | Offer Evidence | Pricing Evidence | Product Implication |
| --- | --- | --- | --- | --- |
| [MonitoraBR](https://monitorabr.com.br/) | Candidates, campaign teams, parties, public-communication professionals | Political-specific monitoring: mentions, sentiment, news movement, social networks, competitors, crisis/opportunity alerts, automatic news clipping, shareable reports. | Plans are customized / consultative on the public page. | Direct proof that political clipping plus adversary/topic monitoring is a real category. Keep adversaries and crisis alerts as add-ons, not V1 base. |
| [Elege.AI](https://elege.ai/) | Advisors, campaigns, public figures and political clients | 24/7 monitoring of TV, radio, social networks, and news portals; real-time WhatsApp notifications; sentiment analysis; software plus WhatsApp summaries/notifications. | Public page offers a free demo/trial path, no fixed price captured. | Strong proof that buyers may expect WhatsApp and broadcast coverage; V1 should explicitly say it is not TV/radio/24/7. |
| [Knewin Comunique-se Clipping](https://www.knewin.com/clipping-ads/) | Corporate communications / reputation teams | Broad clipping across radio, TV, portals, blogs, social networks, and print; sentiment, valuation, retroactive clipping, alerts, report builder. | Quote/demo funnel, no fixed price captured on this page. | Enterprise benchmark: do not compete on breadth. Use Knewin as contrast for a smaller operated political dashboard. |
| [Buzzmonitor Dashboards](https://use.buzzmonitor.com.br/dashboards/) | Brands, agencies, marketing/social teams | Real-time dashboards, crisis dashboards, social/media monitoring, AI insights, customizable reports. | Public page shows plans starting at `R$ 1.590/mês`. | Useful upper benchmark for social/dashboard tooling; supports keeping Otavio's first pilot bounded below full social platform scope. |
| [Zeeng](https://zeeng.com.br/) | Brands and competitors / market intelligence | Clipping de noticias, real-time dashboard, benchmarking and competitor analysis. | Public page points to trial/contact; no fixed price captured here. | Reinforces dashboard + competitor framing, but V1 should avoid unlimited benchmarking. |
| [Cortex Brand](https://www.cortex-intelligence.com/brand/tendencias-na-midia) | Enterprise reputation / communication strategy teams | Customized topic monitoring, real-time alerts, trend/crisis detection, sentiment, more than 70 indicators, 8 media types, onboarding/support. | Demo/contact funnel; no fixed price captured. | Shows full intelligence suites are much broader than V1. Position Rio methodology and strategic indicators as later/add-on work. |

## Updated Interpretation

The 2026-05-20 refresh strengthens the prior conclusion:

```text
political monitoring exists as a named category
the broad market sells real-time, social, TV/radio, crisis, adversary, sentiment, valuation, BI, and reports
fixed public prices are rare in political/enterprise pages
the only public fixed price captured in this refresh is Buzzmonitor from R$ 1.590/month
```

Otavio's safer wedge remains:

```text
private scoped dashboard
small target list
operator-run updates
grouped stories
one short weekly summary
clear no-leak privacy proof
lower complexity than broad social/listening suites
```

## V1 Packaging Consequences

Keep in base:

```text
30-day pilot
up to 5 people/terms
2 updates per week
private Render dashboard
one short weekly summary
operator-managed target/profile changes
```

Keep out of base unless priced separately:

```text
adversary monitoring
crisis alerts
24/7 monitoring
TV/radio coverage
WhatsApp real-time notifications
custom PDF/BI reports
full sentiment/valuation methodology
Rio economic indicator
client self-service target creation
```

## Pricing Boundary

Do not set a final price from this refresh.

Use the refresh only as a positioning check:

```text
below enterprise/social suites in scope
above cheap self-service if Otavio is doing setup, QA, and weekly summary
final price still requires buyer rows plus measured operator time
```

Required before price decision:

```text
BUYER_QUOTE_VALIDATION_TRACKER.md has at least 3 real dated rows
V1_PILOT_OPERATING_LEDGER.md has at least 1 real update_run and 1 real weekly summary
tools/buyer_quote_tracker_check.py returns ok=true
tools/pilot_ledger_check.py returns ok=true
```

## Next Sales Action

The next useful non-code action is not more pricing speculation. It is one real
buyer conversation using:

```text
DEMO_SCRIPT_AND_BUYER_ASSUMPTIONS.md
SELLABLE_DEMO_READINESS_REVIEW_2026-05-18.md
BUYER_INTERVIEW_GUIDE.md
BUYER_QUOTE_VALIDATION_TRACKER.md
```

If a prospect asks for broad competitor/crisis/WhatsApp/TV coverage, record it
as add-on demand instead of expanding the base package.
