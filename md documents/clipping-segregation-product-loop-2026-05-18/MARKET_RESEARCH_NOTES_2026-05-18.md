# Market Research Notes - 2026-05-18

_Initial sourced pass by Atlas/Codex. This is not final pricing._

## Scope

Question: what does the current market suggest about selling a segmented
political clipping dashboard to small political offices?

This pass used public web pages and public contract documents. It needs later
buyer interviews before pricing decisions.

## Evidence Table

| Source | Buyer / Positioning | Offer Evidence | Pricing Evidence | Notes |
| --- | --- | --- | --- | --- |
| [Legislatech](https://legisla.tech/) | Legislative/public-data monitoring and clipping | Monitors public bodies and press sources; plans include keywords, reports, private terms, realtime notifications, ChatGPT/integrations at higher tiers. | Public plans shown: free, R$ 9,90/mo, R$ 299/mo, R$ 999/mo. | Useful low/self-service benchmark. Their higher tiers include private terms, notifications, setup, integrations. |
| [Political Brain](https://politica.certameia.com.br/) | Mandates and campaigns in Brazil | Political-specific platform: media monitoring, crisis alerts, daily WhatsApp briefing, content generation, territorial intelligence. | Values are quote-based via WhatsApp. | Strong evidence that political offices are a named buyer category. Their offer is broader than clipping. |
| [Simpling](https://simpling.com.br/planos/) | Media monitoring/clipping plans | Channels plan covers TV, radio, newspapers, online; Monitoring adds AI, WhatsApp/email bulletins, sentiment, themes, PDF/XLSX reports, sharing. | Public "a partir" prices: R$ 159,90/mo and R$ 299,90/mo in one view; R$ 239,90/mo and R$ 449,90/mo in another payment mode. | Good benchmark for SMB-style monitoring with add-ons. |
| [CService](https://cservice.io/) | Corporate monitoring and intelligence | Offers monitoring across online/offline, email, portal, app, dashboards, qualitative/quantitative analysis, API/intranet integration. | No public price found in this pass. | Shows common enterprise feature language: dashboard, reports, valuation, API. |
| [Clipei](https://clipei.com.br/) | Clipping service / press monitoring | Daily email report with links/audio/video; monthly report for global view of citations. | No public price found in this pass. | Evidence that simple email + monthly report remains a recognizable clipping product. |
| [EBC/SECOM contract table](https://www.gov.br/secom/pt-br/acesso-a-informacao/licitacoes-e-contratos/contratos/vigentes/contratono042019comunicacaoempresabrasildecomunicacaosaebc.pdf) | Federal/government clipping and alerts | Package includes press, TV, radio, relevance selection, magazine briefing, archive; alert package includes WhatsApp and other government-focused alerts. | Shows unit values including R$ 822,24/month for a media-monitoring subscription and R$ 208,00/month for alerts, inside a large annual estimate. | Public-sector benchmark, not directly comparable to a small office. Useful for showing clipping is budgetable. |
| [Goiás SEINFRA term of reference](https://goias.gov.br/seinfra/wp-content/uploads/sites/6/2024/03/Termo-de-Referencia-Cliping-02-2024.pdf) | State government clipping procurement | Monitoring of printed, electronic and digital media for government-interest topics over 12 months. | Estimated unit value R$ 3.414,41 and total R$ 40.972,92 for 12 months. | Higher-touch public procurement benchmark. |
| [TJMA clipping tender](https://www.tjma.jus.br/financas/downacordo.php?acordo=pe_0062%2F2023&anodoc=2023&nrTermo=&tpAcordo=L) | Judiciary clipping and media measurement | Daily monitoring across TV, print, radio, portals/blogs, social networks, with collection, classification, compilation and availability. | Estimated unit value R$ 286,56 per clipping/day for 740 clippings. | Shows daily monitored clipping can be priced as a recurring service unit. |

## Initial Interpretation

The market seems to split into three bands:

1. **Low-cost self-service monitoring**: cheap keyword/report tooling with
   limited human service.
2. **SMB clipping/monitoring platforms**: dashboard, reports, alerts, sentiment,
   WhatsApp/email, often from around a few hundred reais per month.
3. **Public-sector/enterprise monitoring contracts**: broad media coverage,
   human curation, TV/radio/print/social, daily service and procurement pricing.

Otavio's current V1 should not try to compete with full enterprise clipping.
The plausible wedge is:

- political-specific context;
- private scoped dashboard;
- operator-curated setup;
- lightweight grouped stories;
- lower complexity than enterprise platforms;
- more personal/affordable than full agency contracts.

## Pricing Hypotheses To Validate

These are hypotheses, not recommendations:

- A very cheap price risks not covering AI/tooling/operator time.
- A price below broad enterprise contracts but above pure self-service may make
  sense if Otavio provides setup and review.
- A small-office V1 could be positioned as "private dashboard + weekly/daily
  monitored clipping", with WhatsApp/PDF as manual add-ons rather than default.

## Product Implications

- The first sellable package should emphasize private dashboard, scoped terms,
  grouped stories, and low operator friction.
- WhatsApp alerts, AI-generated posts, social listening, TV/radio, and custom
  reports should be add-ons or later tiers.
- "Terms privados" and "setup incluído" are important competitive concepts.
- A demo should show zero data contamination, because privacy is an explicit
  selling point in political products.

## Next Research Pass

- Search specifically for Brazilian political communication agencies offering
  clipping to vereadores/deputados. **Second pass started in
  `MARKET_RESEARCH_POLITICAL_COMPETITOR_PASS_2026-05-18.md`.**
- Gather 5-8 quote-based competitors and note their feature claims.
- Interview one press advisor or political staffer about current workflow and
  willingness to pay. Interview script now exists in `BUYER_INTERVIEW_GUIDE.md`.
- Update `FIRST_SELLABLE_PACKAGE.md` only after this broader pass.

## Second Pass Status

The political/communications competitor pass found direct or adjacent evidence
for:

```text
Political Brain
MonitoraBR
Conectare Politica
Values Comunicacao
Grupo Comunica
Lux Jornal
Simpling
iClipping
Notitia Comunicacao
Rede Clipping
```

Main implication: keep V1 narrow and affordable. Broader competitor claims
around crisis alerts, adversary monitoring, social/media intelligence, BI,
valuation, and daily briefings should be add-ons or later tiers.
