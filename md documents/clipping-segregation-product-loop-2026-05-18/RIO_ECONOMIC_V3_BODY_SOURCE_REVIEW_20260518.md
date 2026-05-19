# Rio Economic V3 Body/Source Review - 2026-05-18

_Created 2026-05-18 by Atlas/Codex._

This is the first body/source review pass for the v3 Rio economic sample. It
uses the v3 dry-run artifact as the row source:

```text
data/reports/rio_economic_dry_run_20260518T234818Z.json
data/reports/rio_economic_dry_run_20260518T234818Z.csv
```

This review does **not** approve a production `rio_economico` target row. It
only reduces methodology uncertainty before the first narrow production run.

## Gate Result

```text
rows_reviewed=21
dimensions_covered=6/6
body_true_positive=16
body_useful_unclear=1
body_false_positive=2
body_duplicate=2
production_target_row_approved=false
```

The v3 sample passes the minimum body/source row count, but the production gate
is still blocked by:

```text
authenticated viewer proof must be fresh or explicitly accepted as blocked
row 15 hotel-jobs ambiguity needs query/source mitigation
row 27 state-government Fazenda leakage needs query exclusion
duplicate Shakira/Mercado Popular stories need grouping before dashboard use
Google News recency/source mismatch needs a date/source sanity check
```

## Reviewed Rows

| # | Dimension | Body Label | Source Checked | Body/Source Finding | Decision |
| --- | --- | --- | --- | --- | --- |
| 1 | tourism_events | body_useful_unclear | exact-title search found older Agencia Brasil/UOL-style text; dry-run source was Google News/Portal ABC | The body proves city hotel occupancy, but the direct body check exposed a possible recency/source mismatch against the Google News item. | Keep the query family, but require resolved canonical URL/date before production. |
| 3 | tourism_events | body_true_positive | Agencia Brasil | Body says Rio carnival hotel occupancy reached 99.02% in the capital, with neighborhood-level occupancy and HotéisRIO as source. | Strong tourism demand signal. |
| 4 | tourism_events | body_true_positive | Prefeitura do Rio | Body ties Shakira in Copacabana to city economic impact, visitor assumptions, tourism, ISS, jobs, and SMDE/Riotur study. | Strong event/tourism economic signal. |
| 6 | tourism_events | body_true_positive | Panrotas | Body reports Prefeitura/SMTUR/Riotur estimates for autumn visitors and R$ 7.6 billion potential impact. | Strong tourism season signal. |
| 8 | commerce_services | body_true_positive | Prefeitura do Rio | Body describes Mercado Popular da Uruguaiana, Centro, 1.6k boxes, R$ 74.2 million investment, reurbanization, and merchant continuity. | Strong commerce/services and urban economy signal. |
| 10 | commerce_services | body_duplicate | Radio Globo/Google News item; same Prefeitura story as row 8 | Same Mercado Popular da Uruguaiana launch already represented by row 8. | Deduplicate into one story cluster. |
| 11 | jobs_income | body_true_positive | JC Concursos | Body says Prefeitura/SMTE Central do Trabalhador offers 2,867 city jobs across regions and sectors. | Useful labor-market signal; prefer official SMTE URL when available. |
| 14 | jobs_income | body_true_positive | Panrotas | Body says Grand Hyatt Rio de Janeiro in Barra da Tijuca held hiring/career event for hotel positions. | Useful hotel labor signal, but watch date window. |
| 15 | jobs_income | body_false_positive | Hotelier News | Body is a generic hotel jobs roundup; the first visible opportunity is Sao Paulo and the title does not prove city-of-Rio specificity. | Exclude generic hotel jobs roundups unless title/body/source has Rio/Copacabana/Barra anchor. |
| 16 | jobs_income | body_true_positive | ABIH-RJ | Body says Hilton Copacabana and Hilton Barra opened a Rio hotel procurement-manager role. | Strong city hotel labor signal. |
| 17 | construction_real_estate | body_true_positive | Prefeitura/SMDU | Body says Prefeitura do Rio extended Mais Valia/Mais Valera regularization with up to 30% discount and online licensing process. | Strong municipal construction/licensing signal. |
| 20 | construction_real_estate | body_true_positive | Veja Real Estate | Body describes accelerated Rio real-estate launches, short-term rental investor demand, and city neighborhoods. | Useful private-market real-estate signal. |
| 22 | construction_real_estate | body_true_positive | ADEMI-RJ/Diario do Rio summary | Body says Rio Real Estate Capital Summit gathered Brookfield, BTG, Caixa, and Vinci around Rio projects, hotelaria, and Centro revitalization. | Strong investment/real-estate signal. |
| 23 | municipal_finance | body_true_positive | O Dia | Body says tourism record in Rio drove municipal ISS collection above R$ 300 million, based on Prefeitura/SMDE/SMTUR/Riotur data. | Strong municipal finance signal. |
| 25 | municipal_finance | body_true_positive | Prefeitura do Rio | Body says Rio collected 37.2% more real ISS revenue from airport-sector services in 2025 H1. | Strong municipal revenue/logistics signal. |
| 26 | municipal_finance | body_true_positive | Camara Municipal do Rio | Body says municipal Fazenda presented 2025 third-quadrimester results, with revenue, ISS, debt, and expenditure details. | Strong official municipal finance signal. |
| 27 | municipal_finance | body_false_positive | O Dia | Body is state government/Receita Estadual/PF/Claudio Castro/Refit; it is not Prefeitura/Camara Municipal finance. | Add state-government exclusions to the Fazenda/Camara query family. |
| 28 | municipal_finance | body_true_positive | Camara Municipal do Rio | Body says municipal Fazenda reported second-quadrimester revenue and ISS growth to the Camara do Rio. | Strong official municipal finance signal. |
| 29 | economic_development | body_true_positive | Prefeitura do Rio | Body says Invest.Rio represented the city at Web Summit Vancouver to attract investors, business, and innovation partnerships. | Strong business-attraction signal. |
| 31 | economic_development | body_true_positive | Prefeitura do Rio | Body says Invest.Rio/Maravalley organized Missao Lisboa with startups, executives, investor meetings, and innovation positioning. | Strong economic-development signal. |
| 33 | economic_development | body_duplicate | Poder360 | Body repeats the Shakira economic-impact story already captured by Prefeitura row 4, with added cost/political angle. | Keep only if dashboard wants source diversity; otherwise cluster with Shakira impact. |

## Source Links Checked

- Row 3: https://agenciabrasil.ebc.com.br/economia/noticia/2026-02/ocupacao-hoteleira-no-carnaval-supera-99-no-rio-de-janeiro
- Row 4: https://prefeitura.rio/desenvolvimento-economico/prefeitura-do-rio-show-de-shakira-deve-ter-impacto-economico-de-aproximadamente-r-800-milhoes-para-a-cidade/
- Row 6: https://www.panrotas.com.br/mercado/destinos/2026/03/rio-de-janeiro-espera-receber-35-milhoes-de-visitantes-durante-o-outono_227055.html
- Row 8: https://prefeitura.rio/noticias/prefeitura-do-rio-lanca-projeto-do-novo-mercado-popular-da-uruguaiana/
- Row 11: https://jcconcursos.com.br/noticia/empregos/prefeitura-do-rio-de-janeiro-inscricoes-abertas-para-2867-vagas-em-novo-seletivo-142707
- Row 14: https://www.panrotas.com.br/hotelaria/eventos/2025/10/grand-hyatt-rio-de-janeiro-recebe-potenciais-candidatos-para-vagas-de-emprego_222534.html
- Row 15: https://hoteliernews.com.br/vagas-abertas-reforcam-movimento-da-hotelaria-em-janeiro/
- Row 16: https://abihrj.com.br/noticias/hilton-copacabana-e-hilton-barra-abrem-vaga-para-gerente-de-compras-cluster-no-rio
- Row 17: https://desenvolvimentourbano.prefeitura.rio/noticias/prefeitura-do-rio-garante-30-de-desconto-para-quem-regularizar-obras-ate-2-de-marco/
- Row 20: https://veja.abril.com.br/coluna/real-estate/a-nova-onda-de-investimentos-no-mercado-imobiliario-do-rio-de-janeiro/
- Row 22: https://ademi.org.br/fundos-imobiliarios-discutem-novos-projetos-e-oportunidades-no-rio-de
- Row 23: https://odia.ig.com.br/economia/2026/03/7219443-turismo-recorde-no-rio-em-2025-faz-arrecadacao-do-iss-do-setor-superar-rs-300-milhoes.html
- Row 25: https://prefeitura.rio/cidade/rio-arrecadou-37-a-mais-no-1o-semestre-de-2025-com-servicos-ligados-ao-setor-aeroportuario/
- Row 26: https://camara.rio/comunicacao/noticias/3094-fazenda-apresenta-resultados-do-ultimo-quadrimestre-de-2025-em-audiencia-publica-na-camara-do-rio
- Row 27: https://odia.ig.com.br/rio-de-janeiro/2026/05/amp/7252479-governo-do-rio-faz-40-exoneracoes-apos-operacao-da-pf-que-teve-claudio-castro-como-alvo.html
- Row 28: https://camara.rio/item/2979-fazenda-presta-contas-a-camara-do-rio-sobre-o-2-quadrimestre-de-2025-do-poder-executivo
- Row 29: https://prefeitura.rio/cidade/invest-rio-leva-rio-ao-web-summit-2026-e-reforca-posicao-da-cidade-como-hub-de-inovacao/
- Row 31: https://prefeitura.rio/cidade/com-agenda-estrategica-de-negocios-invest-rio-e-maravalley-organizam-missao-lisboa-2025/
- Row 33: https://www.poder360.com.br/poder-cultura/prefeitura-do-rio-espera-movimentar-r-7762-milhoes-com-shakira/

## Mitigations Required Before Production

1. Add a canonical-date/source sanity check for Google News rows before they can
   be treated as fresh.
2. Narrow the hotel jobs query so a generic national hotel-jobs roundup does
   not pass without a Rio/Copacabana/Barra/Ipanema/Leblon/title/body anchor.
3. Narrow the municipal Fazenda query with exclusions for state-government
   stories:

```text
Governo do Rio
Receita Estadual
Claudio Castro
Cláudio Castro
Policia Federal
Polícia Federal
Palacio Guanabara
Palácio Guanabara
Refit
ICMS
```

4. Add story clustering before dashboard use so repeated Shakira and Mercado
   Popular articles do not look like separate economic events.
5. Keep Rio production blocked until a fresh Render smoke and authenticated
   profile proof are available or Otavio explicitly accepts the password
   limitation as a temporary blocker.
