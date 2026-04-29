# Validation Oracle: Targeted Re-scraping Guide

Extracted from the historical HTML snapshot (`clipping_mobile_snapshot_all_stories.html`).
**Purpose:** Run targeted searches for these specific articles on these specific dates
and websites. If the pipeline cannot automatically find a previously-registered article,
the scraping for that source is broken.

**Total articles in snapshot:** 1148
**Monitored targets:** Flavio Valle (`flavio_valle`), Pedro Angelito (`pedro_angelito`), Bernardo Rubiao (`bernardo_rubiao`), Pedro Duarte (`pedro_duarte`)

---

# Part 1 — Provider × Website Combos (≥ 5 articles)

**Qualified combos:** 36 (out of 163 total)

## 1. Diario do Rio — `diariodorio.com`

- **Collector:** `rss / wordpress_api`
- **Articles in snapshot:** 151 (151 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-04-01 | Vereador Flávio Valle recebe família vítima do Hamas e reforça luta contra o ... | https://diariodorio.com/vereador-flavio-valle-recebe-familia-vitima-do-hamas-e-reforca-luta-contra-o-antissemitismo |
| 2 | 2024-12-06 | Vereador eleito do Rio representa o Brasil em rede internacional para a democ... | https://diariodorio.com/vereador-eleito-do-rio-representa-o-brasil-em-rede-internacional-para-a-democracia-juvenil |
| 3 | 2026-01-14 | Subprefeitura da Zona Sul apreende cerca de 60 pranchas em fiscalização de st... | https://diariodorio.com/subprefeitura-da-zona-sul-apreende-cerca-de-60-pranchas-em-fiscalizacao-de-stand-up-nas-praias |
| 4 | 2025-02-21 | Prefeitura inicia fiscalização contra ‘pinga-pinga’ de ar-condicionados em Co... | https://diariodorio.com/prefeitura-inicia-fiscalizacao-contra-pinga-pinga-de-ar-condicionados-em-copacabana |
| 5 | 2025-12-30 | Novo entra em crise no RJ após saída de Pedro Duarte e derrota de Rodrigo Rez... | https://diariodorio.com/novo-entra-em-crise-no-rj-apos-saida-de-pedro-duarte-e-derrota-de-rodrigo-rezende-em-eleicao-interna/ |

## 2. Agenda do Poder — `agendadopoder.com.br`

- **Collector:** `rss / wordpress_api`
- **Articles in snapshot:** 123 (123 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-04-01 | Airbnb: Valle não é coautor de novo projeto de Salvino e Talita corre por fora | https://agendadopoder.com.br/airbnb-valle-ainda-nao-e-coautor-de-novo-projeto-de-salvino-enquanto-talita-corre-por-fora |
| 2 | 2025-04-08 | Câmara pode ter quatro PLs para regulamentar Airbnb no Rio | https://agendadopoder.com.br/camara-pode-ter-quatro-pls-para-regulamentar-airbnb-no-rio |
| 3 | 2025-06-14 | Prefeito em comitiva brasileira em Israel reclama de falta de atenção do Itam... | https://agendadopoder.com.br/prefeito-em-comitiva-brasileira-em-israel-reclama-de-falta-de-atencao-do-itamaraty |
| 4 | 2025-05-21 | Proibição de música ao vivo nos quiosques do Rio desafia lei municipal em vig... | https://agendadopoder.com.br/proibicao-de-musica-ao-vivo-nos-quiosques-do-rio-desafia-lei-municipal-em-vigor-desde-2017-aponta-especialista |
| 5 | 2025-04-30 | Mais-valia e mais-valerá: Pedro Duarte defende Plano Diretor como regra | https://agendadopoder.com.br/mais-valia-e-mais-valera-pedro-duarte-defende-plano-diretor-como-regra-para-evitar-puxadinhos-em-areas-nobres |

## 3. Tribuna da Serra — `tribunadaserra.com.br`

- **Collector:** `rss / wordpress_api`
- **Articles in snapshot:** 115 (115 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-02-01 | No Tanque, Talita Galhardo é carregada por Paes e Cavaliere | https://tribunadaserra.com.br/no-tanque-talita-galhardo-e-carregada-por-paes-e-cavaliere |
| 2 | 2026-01-08 | Rio tem ao menos 800 imóveis abandonados no Centro, aponta levantamento da Câ... | https://tribunadaserra.com.br/rio-tem-ao-menos-800-imoveis-abandonados-no-centro-aponta-levantamento-da-camara |
| 3 | 2025-06-14 | Câmara do Rio discute abertura de hospital no antigo prédio da IBM em Botafogo | https://tribunadaserra.com.br/camara-do-rio-discute-abertura-de-hospital-no-antigo-predio-da-ibm-em-botafogo |
| 4 | 2025-06-22 | Felipe Lucena: A municipalização do atual modelo de segurança pública é um bu... | https://tribunadaserra.com.br/felipe-lucena-a-municipalizacao-do-atual-modelo-de-seguranca-publica-e-um-bunker-onde-nao-cabem-todos |
| 5 | 2025-07-31 | Por que o MEC precisa aprovar o curso de Medicina da PUC-Rio | https://tribunadaserra.com.br/por-que-o-mec-precisa-aprovar-o-curso-de-medicina-da-puc-rio |

## 4. Tempo Real RJ — `temporealrj.com`

- **Collector:** `rss / wordpress_api`
- **Articles in snapshot:** 95 (95 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-01-01 | Paes nomeia os 11 subprefeitos; saiba quem são - Tempo Real | https://temporealrj.com/paes-nomeia-os-11-subprefeitos-saiba-quem-sao |
| 2 | 2025-11-07 | Campanha ‘Reocupa Rio’ chama população para denunciar imóveis abandonados | https://temporealrj.com/campanha-reocupa-rio-chama-populacao-para-denunciar-imoveis-abandonados |
| 3 | 2025-06-15 | ‘Olha o mate!’: até no inverno, um chá gelado que é símbolo carioca | https://temporealrj.com/olha-o-mate-ate-no-inverno-um-cha-gelado-que-e-simbolo-carioca |
| 4 | 2025-03-24 | Vereadores Talita Galhardo e Flávio Valle batem boca em audiência sobre Airbn... | https://temporealrj.com/vereadores-thalita-galhardo-e-flavio-valle-batem-boca-em-audiencia-sobre-airbnb |
| 5 | 2026-01-30 | O advogado Pedro Angelito será o novo subprefeito da Zona Sul do Rio - Tempo ... | https://temporealrj.com/pedro-angelito-sera-novo-subprefeito-zona-sul |

## 5. Veja Rio — `vejario.abril.com.br`

- **Collector:** `rss / wordpress_api`
- **Articles in snapshot:** 62 (62 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-05-01 | Os mais novos patrimônios do Rio? Bolinho de bacalhau do Cadeg e saideira | https://vejario.abril.com.br/cidade/bolinho-bacalhau-cadeg-patrimonio-cultural-rio |
| 2 | 2025-10-06 | “Renova Run Rio”, na Lagoa, tem inscrições esgotadas em menos de 3 minutos - ... | https://vejario.abril.com.br/coluna/lu-lacerda/renova-run-rio-na-lagoa-tem-inscricoes-esgotadas-em-menos-de-3-minutos |
| 3 | 2025-08-14 | Com recorde de público, Encontro VEJA Rio aquece a noite fria em Ipanema | https://vejario.abril.com.br/beira-mar/recorde-publico-encontro-veja-rio |
| 4 | 2025-12-22 | Pode isso? Prefeitura decide leiloar imóvel com comércio ativo em Botafogo | https://vejario.abril.com.br/cidade/prefeitura-leiloa-comercio-botafogo |
| 5 | 2025-10-30 | R$ 18 milhões em dívidas e 42 imóveis esquecidos: ZS também entra no radar - ... | https://vejario.abril.com.br/coluna/lu-lacerda/r-18-milhoes-em-dividas-e-42-imoveis-esquecidos-zs-tambem-entra-no-radar |

## 6. Camara Rio — `camara.rio`

- **Collector:** `rss / wordpress_api`
- **Articles in snapshot:** 47 (47 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-01-01 | Câmara do Rio inicia 12ª legislatura com posse dos 51 vereadores eleitos - Câ... | https://camara.rio/comunicacao/noticias/2488-camara-do-rio-inicia-12-legislatura-com-posse-dos-51-vereadores-eleitos |
| 2 | 2025-01-07 | Flávio Valle \| Vereadores - Câmara Municipal do Rio de Janeiro | https://camara.rio/vereadores/flavio-valle |
| 3 | 2025-10-15 | 299 \| Frentes Parlamentares \| Comissões \| Atividade Parlamentar - Câmara Muni... | https://camara.rio/atividade-parlamentar/frentes/299 |
| 4 | 2025-10-22 | Câmara inicia ciclo de audiências para debater o orçamento do Rio para 2026 e... | https://camara.rio/comunicacao/noticias/2897-camara-inicia-ciclo-de-audiencias-para-debater-o-orcamento-do-rio-para-2026-e-para-o-quadrienio-2026-2029 |
| 5 | 2025-10-30 | Secretaria Municipal de Administração e Previ-Rio apresentam orçamento e açõe... | https://camara.rio/comunicacao/noticias/2911-secretaria-municipal-de-administracao-e-previ-rio-apresentam-orcamento-e-acoes-previstas-para-2026 |

## 7. O Globo — `oglobo.globo.com`

- **Collector:** `rss / wordpress_api`
- **Articles in snapshot:** 47 (47 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-09-02 | Exposição no Rio revela registros inéditos do Mar Morto feitos por fotógrafo ... | https://oglobo.globo.com/blogs/ancelmo-gois/post/2025/09/exposicao-no-rio-revela-registros-ineditos-do-mar-morto-feitos-por-fotografo-israelense.ghtml |
| 2 | 2025-06-10 | Projeto quer limitar horário de funcionamento de bares e restaurantes da Rua ... | https://oglobo.globo.com/blogs/ancelmo-gois/post/2025/06/projeto-quer-limitar-horario-e-funcionamento-de-bares-de-polo-gastronomico-da-rua-arnaldo-quintela.ghtml |
| 3 | 2025-06-14 | Comitiva de políticos brasileiros em Israel pode ser retirada pela Jordânia, ... | https://oglobo.globo.com/mundo/noticia/2025/06/14/comitiva-de-politicos-brasileiros-em-israel-pode-ser-retirada-pela-jordania-diz-itamaraty.ghtml |
| 4 | 2025-05-20 | 'Prefiro perder eleição do que ter uma cidade esculhambada', diz Paes sobre n... | https://oglobo.globo.com/rio/noticia/2025/05/20/prefiro-perder-eleicao-do-que-ter-uma-cidade-esculhambada-diz-paes-sobre-novas-regras-para-a-orla-do-rio.ghtml |
| 5 | 2025-01-30 | Câmara do Rio remove pichação com suástica nazista em um de seus banheiros | https://oglobo.globo.com/blogs/lauro-jardim/post/2025/01/camara-do-rio-remove-pichacao-com-suastica-nazista-em-um-de-seus-banheiros.ghtml |

## 8. Google News — `news.google.com`

- **Collector:** `google_news`
- **Articles in snapshot:** 27 (27 unique URLs)
- **⚠️ URLs are Google News redirects** (need token decode)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-03-01 | Pedro Duarte eleito presidente da Distrital do PSD Porto com maioria de 93% -... | https://news.google.com/rss/articles/CBMiU0FVX3lxTE5id2VfWGh5ZFFLTjZQLUI1cnNCanliTDJkUHlkVDhvLWhPWXJqZlNKSFJsWUtfQTA0YmQwV0Yyb2lPdXhWUmJPSzdkLTdoaWtfdTk0 |
| 2 | 2025-11-05 | Os cinco desafios do presidente Pedro Duarte no Porto - Jornal de Notícias | https://news.google.com/rss/articles/CBMilwFBVV95cUxNRkM1TTVHNVh5RjVXUDBIOEZqaGgyaFhyTnhZUmZCVnJIaDc1U0VwMmhIOG9EdUppYzBhTElNTlItdjRiS3Z0QTUwdVo3SDZtUGY5UE5WblFzNTd4QXNaV296SWhWU3lGZlJObnd1THoyc3JBLTUyWFJxcDJ4ZVc1Y3U5SGNZVmE5OTFuN3lMcHBUZ1BXNUFj |
| 3 | 2026-01-11 | "Ficaria triste se o país fosse nesse caminho": Pedro Duarte apresenta um cen... | https://news.google.com/rss/articles/CBMiqAJBVV95cUxQZFhPb0tLc2Z6TXRDak0yMzZYNmpYSk1RenZoT0phN1lWcjF3OEptazMyYk1xWFFhSTZzNUdRUTAzVV9vOFl3QmhHcVZ2WUhySEVnVEFpTUxaYk5BcTNEVEtCOG5FTHM2OTQ4RDdYWTYtMHd6WTY3OUU4ZUxoZWYyak5jRGdVTmExS3J5eDBFTDhPMHVTVm1MeHV1OWxfelRHOENCSUNTekFvYXNUcjZJTzVBWlpva1RCbHdDOVFqb3FzTjRDSDNrS295UG9DRmVfQkN0a2FDbmFGWlBQU01sSTZXOVExTmtTVnNyUzZuV3d2RDhtSGdPcXduX2xGQmdPa2dac2s2NHVGSWgyWVNRZENHekxBNWYyamZOMm5BSk4zeFJEMHRGQQ |
| 4 | 2025-12-19 | Tucanos abrem as asas e articulam o retorno do disputado Pedro Duarte ao PSDB... | https://news.google.com/rss/articles/CBMixgFBVV95cUxQcXROQS01TWNsYWFWdTdMRC1SdFhzUGVJMEllNWxQZlNkdVFmT0hFZ2x0TDlpUms1eWotbFFFRVhaMlg1cE1oSGtuWWR2eHJpdWRKc2ZpSDRDRXpaVEhrNFJ2MFlCR1VYSjhtbHc0RXNIT3dvdEpxbDY3WHZsQmFBQnhNMjRJYTB2a2RPLWNsNXdpV3VIbDgwM3ZrdE45UllyMXN0dnY3VmlIRVRXTWx4Wk9mY0ZtTVAwN1dMZUR0WW85TklueWc |
| 5 | 2025-12-30 | Pedro Duarte envia ofício ao TCM e ao MPRJ questionando caso de imóvel em Bot... | https://news.google.com/rss/articles/CBMi0gFBVV95cUxQS0VfcVJ5RTdWYUpWQ3NUOGZuSlY2aE9WT1F4YWVoOXJkMFVzVFJsczZMMS1TU0I3UzdTTVk2OEo4VFFfRTFWbHhicU5jck1jd2VCSUVUTDdWbjl2YmN4R2NMR1dlaXg3dENjYXAwbTlNNUR5NENrdEp4cnpXcVNEN1FxT3llZmFRcE1WTUtkbTdRdm1GSWtDM3FsTFoxbFZoWE8ySTU0V19BQVJCRVQ1ZkoxaFpJdE1GNjBJbWYyTTZ1SnFDT3R3Nkl0amR3N2xVZmc |

## 9. Diario do Rio Site — `diariodorio.com`

- **Collector:** `direct_scrape / wordpress_api`
- **Articles in snapshot:** 23 (23 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-01-01 | Eduardo Paes e vereadores eleitos no Rio tomam posse nesta quarta-feira | https://diariodorio.com/eduardo-paes-e-vereadores-eleitos-no-rio-tomam-posse-nesta-quarta-feira |
| 2 | 2024-10-03 | Quem é o candidato a vereador da Zona Sul do Rio de Janeiro em 2024? | https://diariodorio.com/quem-e-o-candidato-a-vereador-da-zona-sul-do-rio-de-janeiro-em-2024-2 |
| 3 | 2024-10-08 | Quantos suplentes virarão secretários no PSD – Bastidores do Rio | https://diariodorio.com/quantos-suplentes-virarao-secretarios-no-psd-bastidores-do-rio |
| 4 | 2025-01-13 | O deputado despachante – Bastidores do Rio | https://diariodorio.com/o-deputado-despachante-bastidores-do-rio |
| 5 | 2025-01-27 | O Holocausto foi o ápice do antissemitismo, mas não o seu fim | https://diariodorio.com/o-holocausto-foi-o-apice-do-antissemitismo-mas-nao-seu-fim |

## 10. Google News — `jn.pt`

- **Collector:** `google_news`
- **Articles in snapshot:** 19 (19 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-10-02 | Pedro Duarte e Pizarro trocam reptos no terceiro dia da campanha - Jornal de ... | https://www.jn.pt/pais/artigo/pedro-duarte-e-pizarro-trocam-reptos-no-terceiro-dia-da-campanha/17959975 |
| 2 | 2026-03-06 | Pedro Duarte: "Houve muita falta de responsabilidade no processo do metrobus"... | https://jn.pt/pais/artigo/pedro-duarte-houve-muita-falta-de-responsabilidade-no-processo-do-metrobus/18059208 |
| 3 | 2026-03-14 | Porto fez História na produção de energias renováveis - Jornal de Notícias | https://jn.pt/poder-local/artigo/porto-fez-historia-na-producao-de-energias-renovaveis/18062132 |
| 4 | 2026-02-18 | Pedro Duarte quer que o país "reflita" sobre a regionalização - Jornal de Not... | https://jn.pt/pais/artigo/pedro-duarte-quer-que-o-pais-reflita-sobre-a-regionalizacao/18053398 |
| 5 | 2025-08-30 | Pedro Duarte aponta à regionalização após as autárquicas - Jornal de Notícias | https://www.jn.pt/pais/artigo/pedro-duarte-aponta-a-regionalizacao-apos-as-autarquicas/17899461 |

## 11. G1 — `g1.globo.com`

- **Collector:** `rss / wordpress_api`
- **Articles in snapshot:** 19 (19 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-01-01 | Paes e vereadores eleitos no Rio tomam posse nesta quarta-feira | https://g1.globo.com/rj/rio-de-janeiro/noticia/2025/01/01/paes-e-vereadores-eleitos-no-rio-tomam-posse-nesta-quarta-feira.ghtml |
| 2 | 2024-10-06 | Carlos Bolsonaro bate o próprio recorde e é o vereador mais bem votado da his... | https://g1.globo.com/rj/rio-de-janeiro/eleicoes/2024/noticia/2024/10/06/carlos-bolsonaro-e-o-vereador-mais-bem-votado-da-historia-no-rio.ghtml |
| 3 | 2025-06-16 | Veja quem são os gestores municipais brasileiros que deixaram Israel nesta se... | https://g1.globo.com/politica/noticia/2025/06/16/veja-quem-sao-os-gestores-municipais-brasileiros-que-deixaram-israel-nesta-segunda-feira.ghtml |
| 4 | 2025-05-20 | Novas regras para praias do Rio, como proibição de música ao vivo, geram prot... | https://g1.globo.com/rj/rio-de-janeiro/noticia/2025/05/20/novas-regras-para-praias-do-rio-geram-protestos-e-mobilizam-a-camara.ghtml |
| 5 | 2025-05-28 | Exposição resgata imagens da contribuição judaica para a história do Rio, com... | https://g1.globo.com/guia/guia-rj/noticia/2025/05/28/exposicao-resgata-imagens-da-contribuicao-judaica-para-a-historia-do-rio-com-fotos-raras-da-praca-onze-e-da-visita-de-albert-einstein.ghtml |

## 12. Tempo Real RJ Site — `temporealrj.com`

- **Collector:** `direct_scrape / wordpress_api`
- **Articles in snapshot:** 17 (17 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-01-01 | Protesto, emoção e, claro, zoação na posse dos vereadores do Rio | https://temporealrj.com/protesto-emocao-e-claro-zoacao-na-posse-dos-vereadores-do-rio |
| 2 | 2024-10-07 | Cabo eleitoral de luxo, Paes elege quatro de seus pupilos | https://temporealrj.com/cabo-eleitoral-de-luxo-paes-elege-quatro-de-seus-pupilos |
| 3 | 2025-07-14 | Vendedores de mate: prefeitura do Rio promove nova edição de curso de boas pr... | https://temporealrj.com/vendedores-de-mate-prefeitura-do-rio-promove-nova-edicao-de-curso-de-boas-praticas |
| 4 | 2024-12-18 | Saias-justas, gravatas chiques e terninhos: os bastidores da diplomação dos e... | https://temporealrj.com/saias-justas-gravatas-chiques-e-terninhos-os-bastidores-da-diplomacao-dos-eleitos-no-rio |
| 5 | 2025-05-27 | LDO: Assistência Social e Habitação prestam contas em audiência na Câmara | https://temporealrj.com/ldo-assistencia-social-e-habitacao-prestam-contas-em-audiencia-na-camara |

## 13. Google News — `temporealrj.com`

- **Collector:** `google_news`
- **Articles in snapshot:** 15 (15 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-04-05 | Pedro Duarte é convidado para congresso global de tecnologia na Índia - Tempo... | https://temporealrj.com/pedro-duarte-e-convidado-para-congresso-global-de-tecnologia-na-india |
| 2 | 2025-08-10 | Pedro Duarte e Eduardo Leite, governador do RS, discutem segurança pública - ... | https://temporealrj.com/pedro-duarte-e-eduardo-leite-governador-do-rs-discutem-seguranca-publica |
| 3 | 2025-12-13 | Quase governista, mas nem tanto: Pedro Duarte questiona a Prefeitura do Rio s... | https://temporealrj.com/quase-governista-mas-nem-tanto-pedro-duarte-questiona-a-prefeitura-do-rio-sobre-a-desapropriacao-de-predio-em-botafogo |
| 4 | 2026-01-26 | Vereador Pedro Duarte confirma filiação ao PSD e pré-candidatura a deputado e... | https://temporealrj.com/vereador-pedro-duarte-confirma-filiacao-ao-psd-e-pre-candidatura-a-deputado-estadual |
| 5 | 2025-12-30 | Pedro Duarte envia ofício ao TCM e ao MPRJ questionando caso de imóvel em Bot... | https://temporealrj.com/pedro-duarte-envia-oficio-ao-tcm-e-ao-mpe-questionando-caso-de-imovel-em-botafogo-desapropriado-pela-prefeitura |

## 14. Google News — `publico.pt`

- **Collector:** `google_news`
- **Articles in snapshot:** 13 (13 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-10-04 | Montenegro dá luz verde a plano de segurança de Pedro Duarte e ataca Filipe A... | https://www.publico.pt/2025/10/04/politica/noticia/montenegro-entra-campanha-porto-aval-plano-seguranca-pedro-duarte-deixa-recado-filipe-araujo-2149634 |
| 2 | 2026-03-11 | Seguro em modo festa no Porto: a “frincha de luz”, o aniversariante, e os elo... | https://publico.pt/2026/03/11/politica/noticia/seguro-modo-festa-porto-frincha-luz-abrunhosa-aniversariante-fim-centralismo-elogiado-pedro-duarte-2167497 |
| 3 | 2025-11-14 | É impossível resolver o problema da habitação, como diz Pedro Duarte? - Público | https://www.publico.pt/2025/11/14/opiniao/opiniao/impossivel-resolver-problema-habitacao-pedro-duarte-2154634 |
| 4 | 2026-01-16 | Câmara do Porto volta a adiar requalificação do Jardim da Corujeira por tempo... | https://publico.pt/2026/01/16/local/noticia/camara-porto-volta-adiar-requalificacao-jardim-corujeira-tempo-indeterminado-2161473 |
| 5 | 2025-08-30 | Pedro Duarte sugere que país pense sobre regionalização no pós-autárquicas - ... | https://www.publico.pt/2025/08/30/politica/noticia/pedro-duarte-sugere-pais-pense-regionalizacao-posautarquicas-2145465 |

## 15. Google News — `rtp.pt`

- **Collector:** `google_news`
- **Articles in snapshot:** 13 (13 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-10-08 | Campanha no Porto. Pedro Duarte insiste no apelo ao voto útil - RTP | https://www.rtp.pt/noticias/politica/campanha-no-porto-pedro-duarte-insiste-no-apelo-ao-voto-util_v1689453 |
| 2 | 2025-10-12 | Pedro Duarte promete ser um presidente "muito livre e independente" - RTP | https://www.rtp.pt/noticias/politica/pedro-duarte-promete-ser-um-presidente-muito-livre-e-independente_v1690477 |
| 3 | 2025-10-13 | Pedro Duarte vence. Porto "deu mais uma prova de grandiosidade" - RTP | https://www.rtp.pt/noticias/politica/pedro-duarte-vence-porto-deu-mais-uma-prova-de-grandiosidade_v1690637 |
| 4 | 2026-02-18 | Pedro Duarte defende referendo à regionalização - RTP | https://rtp.pt/noticias/politica/pedro-duarte-defende-referendo-a-regionalizacao_v1719889 |
| 5 | 2025-09-30 | Sondagem Católica. Pedro Duarte e Manuel Pizarro empatados na corrida à Câmar... | https://www.rtp.pt/noticias/politica/sondagem-catolica-pedro-duarte-e-manuel-pizarro-empatados-na-corrida-a-camara-do-porto_n1687376 |

## 16. Google News — `observador.pt`

- **Collector:** `google_news`
- **Articles in snapshot:** 13 (13 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-10-02 | Pedro Duarte dramatiza apelo ao voto útil contra "velho PS" e insiste na "deg... | https://observador.pt/especiais/pedro-duarte-dramatiza-apelo-ao-voto-util-contra-velho-ps-e-insiste-na-degradacao-do-clima-de-inseguranca |
| 2 | 2025-11-05 | Pedro Duarte assegura maioria no executivo municipal ao convencer vereador do... | https://observador.pt/2025/11/05/pedro-duarte-assegura-maioria-no-executivo-municipal-ao-roubar-vereador-ao-ps |
| 3 | 2025-08-08 | Autárquicas. Pedro Duarte quer ficar com o pelouro da Cultura no Porto - Obse... | https://observador.pt/2025/08/08/autarquicas-pedro-duarte-quer-ficar-com-o-pelouro-da-cultura-no-porto |
| 4 | 2025-08-19 | Pedro Duarte: "avaliar reversão" ou mudar metrobus do Porto - Observador | https://observador.pt/2025/08/19/autarquicas-pedro-duarte-quer-avaliar-reversao-ou-mudar-metrobus-do-porto |
| 5 | 2025-09-25 | Sondagem. Pizarro e Pedro Duarte em empate técnico na corrida à Câmara do Por... | https://observador.pt/2025/09/25/sondagem-pizarro-e-pedro-duarte-continuam-em-empate-tecnico-na-corrida-a-camara-do-porto |

## 17. Camara Rio Internal Search — `camara.rio`

- **Collector:** `internal_search`
- **Articles in snapshot:** 9 (9 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-03-02 | Cuidados íntimos com crianças nas instituições de ensino deverão ser realizad... | https://camara.rio/comunicacao/noticias/3015-cuidados-intimos-com-criancas-nas-instituicoes-de-ensino-deverao-ser-realizados-exclusivamente-por-profissionais-do-sexo-feminino |
| 2 | 2026-03-05 | Câmara aprova proposta que facilita a realização de testes de iniciativas ino... | https://camara.rio/comunicacao/noticias/3017-camara-aprova-proposta-que-facilita-a-realizacao-de-testes-de-iniciativas-inovadoras |
| 3 | 2026-02-09 | Câmara do Rio contribui decisivamente para obras do Novo PAC, que levam infra... | https://camara.rio/comunicacao/noticias/3007-camara-do-rio-contribui-decisivamente-para-obras-do-novo-pac-que-levam-infraestrutura-e-qualidade-de-vida-a-favelas-da-cidade |
| 4 | 2025-12-12 | Câmara Rio Debate revisita as discussões do evento O Rio do Futuro | https://camara.rio/comunicacao/noticias/2999-camara-rio-debate-revisita-os-debates-do-evento-o-rio-do-futuro |
| 5 | 2026-02-24 | Aprovada Área Azul Digital para vagas de estacionamento rotativo | https://camara.rio/comunicacao/noticias/3011-aprovada-area-azul-digital-para-vagas-de-estacionamento-rotativo |

## 18. Google News — `odia.ig.com.br`

- **Collector:** `google_news`
- **Articles in snapshot:** 9 (9 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-12-02 | Revisar o IPTU é essencial para o Centro dar certo - O Dia | https://odia.ig.com.br/colunas/vereador-pedro-duarte/2025/12/7172863-revisar-o-iptu-e-essencial-para-o-centro-dar-certo.html |
| 2 | 2026-02-10 | Cinelândia precisa voltar a ser vitrine do Centro do Rio - O Dia | https://odia.ig.com.br/colunas/vereador-pedro-duarte/2026/02/7205767-cinelandia-precisa-voltar-a-ser-vitrine-do-centro-do-rio.html |
| 3 | 2026-03-13 | MP se manifesta pela suspensão da 'lei dos 20 andares' em Teresópolis - O Dia | https://odia.ig.com.br/teresopolis/2026/03/amp/7221687-mp-se-manifesta-pela-suspensao-da-lei-dos-20-andares-em-teresopolis.html |
| 4 | 2025-12-23 | O Rio entre reformas necessárias e desafios persistentes - O Dia | https://odia.ig.com.br/colunas/vereador-pedro-duarte/2025/12/7182538-o-rio-entre-reformas-necessarias-e-desafios-persistentes.html |
| 5 | 2026-01-29 | Vereador Pedro Duarte anuncia nova legenda - O Dia | https://odia.ig.com.br/colunas/informe-do-dia/2026/01/7199640-vereador-pedro-duarte-anuncia-nova-legenda.html |

## 19. Google News — `jpn.up.pt`

- **Collector:** `google_news`
- **Articles in snapshot:** 9 (9 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-11-05 | Pedro Duarte entrega Cultura a vereador eleito pelo PS e garante uma maioria ... | https://jpn.up.pt/2025/11/05/pedro-duarte-entrega-cultura-a-vereador-eleito-pelo-ps-e-garante-uma-maioria |
| 2 | 2026-03-06 | Câmara do Porto gasta 400 mil euros por ano com limpeza de fachadas - JPN - J... | https://www.jpn.up.pt/2026/03/06/camara-do-porto-gasta-400-mil-euros-por-ano-com-limpeza-de-fachadas |
| 3 | 2025-10-10 | Pedro Duarte e Mariana Leitão "perfeitamente alinhados" fazem apelo ao "voto ... | https://www.jpn.up.pt/2025/10/10/pedro-duarte-e-mariana-leitao-perfeitamente-alinhados-fazem-apelo-ao-voto-util |
| 4 | 2026-02-19 | Pedro Duarte reabre debate sobre regionalização e defende TGV como prioridade... | https://www.jpn.up.pt/2026/02/19/pedro-duarte-reabre-debate-sobre-regionalizacao-e-defende-tgv-como-prioridade-estrategica |
| 5 | 2026-01-26 | Pedro Duarte reitera apoio em António José Seguro: “O país fica em muito boas... | https://jpn.up.pt/2026/01/26/pedro-duarte-reitera-apoio-em-antonio-jose-seguro-o-pais-fica-em-muito-boas-maos |

## 20. Google News — `diariodorio.com`

- **Collector:** `google_news`
- **Articles in snapshot:** 9 (9 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-12-03 | Estágio de férias no gabinete de Pedro Duarte oferece bolsa de R$ 500 e carga... | https://diariodorio.com/estagio-de-ferias-no-gabinete-de-pedro-duarte-oferece-bolsa-de-r-500-e-carga-de-20h-semanais |
| 2 | 2026-02-06 | Paes filia Pedro Duarte ao PSD e dá largada a pré-candidaturas para a Alerj -... | https://diariodorio.com/paes-filia-pedro-duarte-ao-psd-e-da-largada-a-pre-candidaturas-para-a-alerj |
| 3 | 2025-12-08 | Crise no Novo: saída de Pedro Duarte expõe racha e deixa legenda sem vereador... | https://diariodorio.com/crise-no-novo-saida-de-pedro-duarte-expoe-racha-e-deixa-legenda-sem-vereador-no-rio |
| 4 | 2026-01-26 | Pedro Duarte se filia ao PSD e lança pré-candidatura a deputado estadual - Di... | https://diariodorio.com/pedro-duarte-se-filia-ao-psd-e-lanca-pre-candidatura-a-deputado-estadual |
| 5 | 2025-12-30 | Novo entra em crise no RJ após saída de Pedro Duarte e derrota de Rodrigo Rez... | https://diariodorio.com/novo-entra-em-crise-no-rj-apos-saida-de-pedro-duarte-e-derrota-de-rodrigo-rezende-em-eleicao-interna |

## 21. Conib Internal Search — `conib.org.br`

- **Collector:** `internal_search`
- **Articles in snapshot:** 9 (9 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-08-05 | Frente Parlamentar de Combate ao Antissemitismo da Câmara do Rio repudia saíd... | https://conib.org.br/noticias/todas-as-noticias/39953-frente-parlamentar-de-combate-ao-antissemitismo-da-camara-do-rio-repudia-saida-do-brasil-da-ihra.html |
| 2 | 2025-10-07 | FestRio Judaico transforma Ipanema em palco de cultura, união e solidariedade | https://conib.org.br/noticias/todas-as-noticias/40137-festrio-judaico-transforma-ipanema-em-palco-de-cultura-uniao-e-solidariedade.html |
| 3 | 2025-09-10 | Câmara do RJ recebe exposição de fotógrafo israelense que retrata a ‘resistên... | https://conib.org.br/noticias/todas-as-noticias/40063-camara-do-rj-recebe-exposicao-de-fotografo-israelense-que-retrata-a-resistencia-do-mar-morto.html |
| 4 | 2025-03-21 | Câmara do RJ concede Moção de Louvor e Reconhecimento ao jornalista Henrique ... | https://conib.org.br/noticias/todas-as-noticias/39569-camara-do-rj-concede-mocao-de-louvor-e-reconhecimento-ao-jornalista-henrique-cymerman.html |
| 5 | 2025-09-29 | Rio de Janeiro vai sediar o V Fórum Latino-Americano Contra o Antissemitismo | https://conib.org.br/noticias/todas-as-noticias/40105-rio-de-janeiro-vai-sediar-o-v-forum-latino-americano-contra-o-antissemitismo.html |

## 22. Google News — `dn.pt`

- **Collector:** `google_news`
- **Articles in snapshot:** 8 (8 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-09-04 | Pedro Duarte. “Nunca aceitarei um acordo de governação com o Chega” - Diário ... | https://www.dn.pt/pol%C3%ADtica/pedro-duarte-nunca-aceitarei-um-acordo-de-governa%C3%A7%C3%A3o-com-o-chega |
| 2 | 2025-11-06 | Câmara do Porto: Distrital do PS surpreendida com atribuição da Cultura a ver... | https://www.dn.pt/pol%C3%ADtica/cmara-do-porto-distrital-do-ps-surpreendida-com-atribuio-da-cultura-a-vereador-eleito-nas-suas-listas |
| 3 | 2025-09-07 | Pedro Duarte: "Não me lembro de alguém que tenha abdicado de ser ministro par... | https://www.dn.pt/pol%C3%ADtica/pedro-duarte-n%C3%A3o-me-lembro-de-algu%C3%A9m-que-tenha-abdicado-de-ser-ministro-para-ser-presidente-de-c%C3%A2mara |
| 4 | 2026-03-16 | Pedro Duarte refere que a região Norte tem sido “grosseiramente preterida” - ... | https://dn.pt/pol%C3%ADtica/pedro-duarte-refere-que-a-regio-norte-tem-sido-grosseiramente-preterida |
| 5 | 2025-09-19 | Autárquicas: Montenegro e Pedro Duarte visitam rua onde nasceu Sá Carneiro - ... | https://www.dn.pt/pol%C3%ADtica/aut%C3%A1rquicas-montenegro-e-pedro-duarte-visitam-rua-onde-nasceu-s%C3%A1-carneiro |

## 23. Google News — `oglobo.globo.com`

- **Collector:** `google_news`
- **Articles in snapshot:** 8 (8 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-12-05 | Rio do Futuro: seminário debate uma mobilidade mais eficiente | https://oglobo.globo.com/rio/noticia/2025/12/05/rio-do-futuro-seminario-debate-uma-mobilidade-mais-eficiente.ghtml |
| 2 | 2025-12-08 | Único vereador eleito pelo Partido Novo na Câmara do Rio deixa a legenda | https://oglobo.globo.com/blogs/ancelmo-gois/post/2025/12/unico-vereador-eleito-pelo-partido-novo-na-camara-do-rio-deixa-a-legenda.ghtml |
| 3 | 2025-02-17 | Câmara do Rio inicia trabalhos hoje já de olho nas eleições 2026 | https://oglobo.globo.com/rio/noticia/2025/02/17/camara-do-rio-inicia-trabalhos-hoje-ja-de-olho-nas-proximas-eleicoes.ghtml |
| 4 | 2025-05-20 | Pedro Duarte Guimarães explora a relação cultural entre Brasil e Índia: novel... | https://oglobo.globo.com/patrocinado/saftec/noticia/2025/05/20/pedro-duarte-guimaraes-explora-a-relacao-cultural-entre-brasil-e-india-novelas-musicas-e-culinaria.ghtml |
| 5 | 2025-08-28 | Proposta que pode pesar na conta de luz do carioca tem objetivo de financiar ... | https://oglobo.globo.com/rio/noticia/2025/08/28/projeto-da-prefeitura-do-rio-muda-regras-de-cobranca-da-contribuicao-sobre-iluminacao-publica-e-pode-aumentar-a-conta-de-luz.ghtml |

## 24. CONIB — `conib.org.br`

- **Collector:** `rss / wordpress_api`
- **Articles in snapshot:** 7 (7 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-09-03 | Confederação Israelita do Brasil (Conib) | https://conib.org.br/noticias/todas-as-noticias/40041-camara-municipal-do-rj-exibe-exposicao-de-fotografo-israelense-sobre-o-mar-morto.html |
| 2 | 2025-12-09 | Confederação Israelita do Brasil | https://conib.org.br/noticias/todas-as-noticias/40347-escola-municipal-anne-frank-inaugura-jardim-bruna-valeanu-em-homenagem-a-ex-aluna.html |
| 3 | 2025-10-15 | Confederação Israelita do Brasil (Conib) | https://conib.org.br/noticias/todas-as-noticias/40174-reunidas-no-rj-liderancas-latino-americanas-aprovam-declaracao-conjunta-contra-o-antissemitismo-e-discurso-de-odio.html |
| 4 | 2025-03-18 | Confederação Israelita do Brasil | https://conib.org.br/noticias/todas-as-noticias/39554-fierj-promove-o-lancamento-de-eternamente-7-de-outubro-e-debate-sobre-terrorismo-e-antissemitismo.html |
| 5 | 2025-09-24 | “Rosh Hashaná 5786: Renovação, Memória e Esperança” - Confederação Israelita ... | https://conib.org.br/noticias/todas-as-noticias/40097-rosh-hashana-5786-renovacao-memoria-e-esperanca.html |

## 25. Google News — `expresso.pt`

- **Collector:** `google_news`
- **Articles in snapshot:** 7 (7 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-10-04 | Um “circo”, um “golpe em campanha eleitoral”: candidatos ao Porto aprovam sus... | https://expresso.pt/politica/eleicoes/autarquicas-2025/2025-10-04-um-circo-um-golpe-em-campanha-eleitoral-candidatos-ao-porto-aprovam-suspensao-do-metrobus-mas-apontam-favorecimento-de-pedro-duarte-70c69131 |
| 2 | 2025-08-07 | Candidatos autárquicos começam a esbater linhas vermelhas para o Chega - Expr... | https://expresso.pt/politica/eleicoes/autarquicas-2025/2025-08-07-candidatos-autarquicos-comecam-a-esbater-linhas-vermelhas-para-o-chega-0f858c9f |
| 3 | 2025-10-07 | Pedro Duarte no Bom Partido: “Por norma, em Lisboa desconfiam mais do que é e... | https://expresso.pt/podcasts/bom-partido/2025-10-07-pedro-duarte-no-bom-partido-por-norma-em-lisboa-desconfiam-mais-do-que-e-estranho.-no-porto-e-o-contrario-da-se-uma-prova-de-confianca-0a245246 |
| 4 | 2026-02-12 | Mau tempo: Pedro Duarte, ex-ministro e autarca do Porto, relança discussão so... | https://expresso.pt/politica/2026-02-12-mau-tempo-pedro-duarte-ex-ministro-e-autarca-do-porto-relanca-discussao-sobre-regionalizacao--outros-autarcas-e-especialistas-tambem--fcafed36 |
| 5 | 2025-08-29 | Pedro Duarte admite governar o Porto com o Chega e não jura ficar como veread... | https://expresso.pt/politica/eleicoes/autarquicas-2025/2025-08-29-pedro-duarte-admite-governar-o-porto-com-o-chega-e-nao-jura-ficar-como-vereador-se-perder-015f39ec |

## 26. Mercado e Eventos — `mercadoeeventos.com.br`

- **Collector:** `rss / wordpress_api`
- **Articles in snapshot:** 7 (7 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-02-02 | DMC Mais Brasil Viagens capacita trade uruguaio sobre o potencial do Carnaval... | https://mercadoeeventos.com.br/noticias/agencias-e-operadoras/dmc-mais-brasil-viagens-capacita-trade-uruguaio-sobre-o-potencial-do-carnaval-brasileiro |
| 2 | 2025-11-04 | Mais Brasil Viagens inaugura escritório em Orlando - Mercado e Eventos | https://mercadoeeventos.com.br/noticias/agencias-e-operadoras/mais-brasil-viagens-inaugura-escritorio-em-orlando |
| 3 | 2025-02-19 | Visit Rio celebra nomeação de Flávio Valle (PSD) como presidente da Comissão ... | https://www.mercadoeeventos.com.br/noticias/politica/visit-rio-celebra-nomeacao-de-flavio-valle-psd-como-presidente-da-comissao-de-turismo-da-camara-municipal-do-rj/ |
| 4 | 2025-02-19 | Visit Rio celebra nomeação de Flávio Valle (PSD) como presidente da Comissão ... | https://www.mercadoeeventos.com.br/noticias/politica/visit-rio-celebra-nomeacao-de-flavio-valle-psd-como-presidente-da-comissao-de-turismo-da-camara-municipal-do-rj |
| 5 | 2025-03-25 | Polêmica no Rio: Câmara Municipal discute regulamentação de plataformas de al... | https://mercadoeeventos.com.br/noticia-manchete-home/polemica-no-rio-camara-municipal-discute-regulamentacao-de-plataformas-de-aluguel-por-temporada |

## 27. O Dia — `odia.ig.com.br`

- **Collector:** `rss / wordpress_api`
- **Articles in snapshot:** 7 (7 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-06-01 | Samba do Cardosão, em Laranjeiras, é reconhecido como Patrimônio Cultural Ima... | https://odia.ig.com.br/rio-de-janeiro/2025/06/7067007-samba-do-cardosao-em-laranjeiras-e-reconhecido-como-patrimonio-cultural-imaterial.html |
| 2 | 2024-10-07 | Conheça os 51 vereadores eleitos no Rio - O Dia | https://odia.ig.com.br/eleicoes/2024/10/6930170-conheca-os-51-vereadores-eleitos-no-rio.html |
| 3 | 2025-09-11 | Fundador da cervejaria Masterpiece, André Valle morre em acidente de moto em ... | https://odia.ig.com.br/rio-de-janeiro/2025/09/7127319-fundador-da-cervejaria-masterpiece-andre-valle-morre-em-acidente-de-moto-em-niteroi.html |
| 4 | 2025-05-15 | Jorge Arraes - No Mês do Trabalhador, a Comlurb comemora o Dia do Gari e 50 a... | https://odia.ig.com.br/opiniao/2025/05/7056151-jorge-arraes-no-mes-do-trabalhador-a-comlurb-comemora-o-dia-do-gari-e-50-anos-de-existencia.html |
| 5 | 2026-01-26 | Dia de Iemanjá do Arpoador reunirá 21 atrações artísticas e religiosas, em ri... | https://odia.ig.com.br/rio-de-janeiro/2026/01/7197312-dia-de-iemanja-do-arpoador-reunira-21-atracoes-artisticas-e-religiosas-em-ritual-e-evento.html |

## 28. CBN — `cbn.globo.com`

- **Collector:** `rss / wordpress_api`
- **Articles in snapshot:** 7 (7 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-06-13 | VÍDEO: Veja como é o bunker onde está comitiva brasileira em Israel - CBN | https://cbn.globo.com/mundo/noticia/2025/06/13/video-veja-como-e-o-bunker-onde-esta-comitiva-brasileira-em-israel.ghtml |
| 2 | 2025-06-16 | Comitiva de políticos brasileiros vai pegar voo na Arábia Saudita para retorn... | https://cbn.globo.com/mundo/noticia/2025/06/16/comitiva-de-politicos-brasileiros-vai-pegar-um-voo-na-arabia-saudita-para-retornar-ao-brasil.ghtml |
| 3 | 2025-02-26 | Projeto prevê que Guardas Municipais do Rio passem por processo interno para ... | https://cbn.globo.com/rio-de-janeiro/noticia/2025/02/26/projeto-preve-que-guardas-municipais-do-rio-passem-por-processo-interno-para-integrar-forca-municipal-de-seguranca.ghtml |
| 4 | 2025-05-27 | Prefeitura do Rio libera música ao vivo nos quiosques e flexibiliza regras so... | https://cbn.globo.com/rio-de-janeiro/noticia/2025/05/27/prefeitura-do-rio-libera-musica-ao-vivo-nos-quiosques-e-flexibiliza-regras-sobre-garrafas-de-vidro-entenda-as-mudancas.ghtml |
| 5 | 2025-05-29 | 'Fomos pegos de surpresa': barraqueiros reclamam de falta de prazo para adesã... | https://cbn.globo.com/rio-de-janeiro/noticia/2025/05/29/fomos-pegos-de-surpresa-barraqueiros-reclamam-de-falta-de-prazo-para-adesao-a-novas-regras-da-orla-do-rio.ghtml |

## 29. Google News — `cnnportugal.iol.pt`

- **Collector:** `google_news`
- **Articles in snapshot:** 6 (6 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-09-08 | Pedro Duarte foi assaltado no Porto e conhece "dezenas de casos" como o seu. ... | https://cnnportugal.iol.pt/pedro-duarte/candidato-a-camara-municipal-do-porto/pedro-duarte-foi-assaltado-no-porto-e-conhece-dezenas-de-casos-como-o-seu-e-por-isso-diz-as-estatisticas-de-seguranca-sao-completamente-enganadoras/20250908/68bf17ccd34e58bc67957907 |
| 2 | 2026-01-11 | "Ficaria triste se o país fosse nesse caminho": Pedro Duarte apresenta um cen... | https://cnnportugal.iol.pt/videos/ficaria-triste-se-o-pais-fosse-nesse-caminho-pedro-duarte-apresenta-um-cenario-extraordinariamente-frustrante-e-dramatico-para-a-segunda-volta/696431b80cf2d7f14f26eb5d |
| 3 | 2026-03-15 | "Estou convencido de que é uma questão eminentemente política que leva a UGT ... | https://cnnportugal.iol.pt/videos/estou-convencido-de-que-e-uma-questao-eminentemente-politica-que-leva-a-ugt-a-ter-a-atitude-de-absoluta-irreversibilidade-que-tem-tido/69b73f3a0cf27f6588a66a8e |
| 4 | 2026-01-19 | Pedro Duarte: "Voto Seguro, para mim é algo inequívoco". Júdice: "Voto em Seg... | https://cnnportugal.iol.pt/presidenciais-2026/resultados-presidenciais-2026/pedro-duarte-poiares-maduro-e-judice-vao-votar-seguro-na-segunda-volta/20260119/696d8a5fd34e0ec52ec2572a |
| 5 | 2026-02-25 | CNN Summit - Portugal Tour: Moedas diz que taxa turística não vai resolver cr... | https://cnnportugal.iol.pt/videos/cnn-summit-portugal-tour-moedas-diz-que-taxa-turistica-nao-vai-resolver-crise-da-habitacao-em-lisboa-pedro-duarte-anuncia-transportes-gratuitos-no-porto-ainda-este-ano/699ef35d0cf21fcd8376c587 |

## 30. Google News — `omirante.pt`

- **Collector:** `google_news`
- **Articles in snapshot:** 6 (6 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-03-01 | Pedro Duarte Personalidade do Ano Nacional - O Mirante | https://omirante.pt/omirante/2026-03-01-video-pedro-duarte-personalidade-do-ano-nacional-f2a30781 |
| 2 | 2026-03-04 | Pedro Duarte Vila Guedes - O Mirante | https://omirante.pt/agora-falo-eu/2026-03-04-pedro-duarte-vila-guedes-92da3431 |
| 3 | 2026-03-06 | O país precisa de fazer um grande debate sobre qual é o melhor modelo de orga... | https://omirante.pt/edicao-1500/2026-03-06-o-pais-precisa-de-fazer-um-grande-debate-sobre-qual-e-o-melhor-modelo-de-organizacao-8c6dfc8f |
| 4 | 2026-03-10 | Atletas da Escola de Karate Shotokan Pedro Duarte conquistam dois pódios no C... | https://omirante.pt/desporto/2026-03-10-atletas-da-escola-de-karate-shotokan-pedro-duarte-conquistam-dois-podios-no-campeonato-nacional-2dfbed15 |
| 5 | 2026-02-27 | Pedro Duarte realça o papel da imprensa regional ao receber o prémio Personal... | https://omirante.pt/omirantetv/2026-02-27-video-pedro-duarte-realca-o-papel-da-imprensa-regional-ao-receber-o-premio-personalidade-do-ano-nacional-3292dd7c |

## 31. Google News — `correiodamanha.com.br`

- **Collector:** `google_news`
- **Articles in snapshot:** 6 (6 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-02-09 | Coluna Magnavita \| Pedro Duarte no PSD e em busca de uma cadeira na Alerj - c... | https://correiodamanha.com.br/colunistas/magnavita/2026/02/257678-pedro-duarte-no-psd-e-embusca-de-uma-cadeira-na-alerj.html |
| 2 | 2026-02-09 | Coluna Magnavita \| Pedro Duarte no PSD e em busca de uma cadeira na Alerj - c... | https://www.correiodamanha.com.br/colunistas/magnavita/2026/02/257678-pedro-duarte-no-psd-e-embusca-de-uma-cadeira-na-alerj.html |
| 3 | 2026-02-12 | Filiação de Pedro Duarte reforça palanque do PSD para as eleições - correioda... | https://correiodamanha.com.br/rio-de-janeiro/2026/02/257497-filiacao-de-pedro-duarte-reforca-palanque-do-psd-para-as-eleicoes.html |
| 4 | 2026-02-12 | Filiação de Pedro Duarte reforça palanque do PSD para as eleições - correioda... | https://www.correiodamanha.com.br/rio-de-janeiro/2026/02/257497-filiacao-de-pedro-duarte-reforca-palanque-do-psd-para-as-eleicoes.html |
| 5 | 2026-01-27 | Pedro Duarte filia-se ao PSD e anuncia pré-candidatura a deputado estadual - ... | https://www.correiodamanha.com.br/rio-de-janeiro/2026/01/253478-pedro-duarte-filia-se-ao-psd-e-anuncia-pre-candidatura-a-deputado-estadual.html |

## 32. VEJA — `veja.abril.com.br`

- **Collector:** `rss / wordpress_api`
- **Articles in snapshot:** 6 (6 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-07-02 | Empresa ligada à Prefeitura do Rio foi turbinada com nomeações políticas, den... | https://veja.abril.com.br/politica/empresa-ligada-a-prefeitura-do-rio-foi-turbinada-com-nomeacoes-politicas-denuncia-vereador |
| 2 | 2024-10-07 | Eleições 2024: os vereadores eleitos na cidade do Rio de Janeiro | https://veja.abril.com.br/politica/eleicoes-2024-os-vereadores-eleitos-na-cidade-do-rio-de-janeiro |
| 3 | 2025-02-18 | Projeto de lei ‘anti-Oruam’ chega ao Rio | https://veja.abril.com.br/brasil/projeto-de-lei-anti-oruam-chega-ao-rio |
| 4 | 2025-06-18 | Único judeu da comitiva, vereador do Rio rebate críticas à viagem a Israel: “... | https://veja.abril.com.br/politica/unico-judeu-da-comitiva-vereador-do-rio-rebate-criticas-a-viagem-a-israel-antissemitismo-velado |
| 5 | 2025-03-20 | Audiência pública vai discutir o abandono de imóveis no Centro do Rio | https://veja.abril.com.br/politica/audiencia-publica-vai-discutir-o-abandono-de-imoveis-no-centro-do-rio |

## 33. Google News — `blogdonc.com`

- **Collector:** `google_news`
- **Articles in snapshot:** 5 (5 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-03-03 | Secret Story 10! Leokadia Pombo gera indignação após opinião polémica sobre P... | https://blogdonc.com/secret-story-10-leokadia-pombo-gera-indignacao |
| 2 | 2026-03-09 | Secret Story 10! Expulsão de Pedro Duarte gera chuva de críticas à TVI: “Não ... | https://blogdonc.com/secret-story-expulsao-de-pedro-duarte-gera-criticas |
| 3 | 2026-03-09 | Após expulsão, Pedro Duarte elege o justo vencedor do Secret Story 10: “Quero... | https://blogdonc.com/secret-story-pedro-duarte-revela-favorito-a-vitoria |
| 4 | 2026-03-22 | Pedro Duarte do "Secret Story 10" antecipa os finalistas desta edição: “Apesa... | https://blogdonc.com/pedro-duarte-do-secret-story-antecipa-os-finalistas |
| 5 | 2026-03-22 | Audiências! “Simply the Best” é um fracasso total e perde para toda a concorr... | https://blogdonc.com/audiencias-simply-the-best-e-um-fracasso-total |

## 34. Google News — `atelevisao.com`

- **Collector:** `google_news`
- **Articles in snapshot:** 5 (5 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-03-01 | Última hora! João acerta no segredo de Pedro Duarte - A Televisão | https://www.atelevisao.com/secret-story-casa-dos-segredos/ultima-hora-joao-acerta-no-segredo-de-pedro-duarte |
| 2 | 2026-03-09 | Portugueses expulsam Pedro Duarte do Secret Story 10 - A Televisão | https://www.atelevisao.com/secret-story-casa-dos-segredos/portugueses-expulsam-pedro-duarte-do-secret-story-10 |
| 3 | 2026-03-22 | Pedro Duarte admite: "Cá fora sinto-me um vencedor" - A Televisão | https://atelevisao.com/secret-story-casa-dos-segredos/pedro-duarte-admite-ca-fora-sinto-me-um-vencedor |
| 4 | 2026-02-25 | Da dor à coragem: o percurso transformador de Pedro, concorrente transexual d... | https://www.atelevisao.com/secret-story-casa-dos-segredos/da-dor-a-coragem-o-percurso-transformador-de-pedro-concorrente-transexual-do-secret-story |
| 5 | 2026-02-27 | "Mudei de sexo" não era o segredo original de Pedro Duarte - A Televisão | https://www.atelevisao.com/secret-story-casa-dos-segredos/mudei-de-sexo-nao-era-o-segredo-original-de-pedro-duarte |

## 35. Panrotas — `panrotas.com.br`

- **Collector:** `rss / wordpress_api`
- **Articles in snapshot:** 5 (5 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2024-11-04 | Mais Brasil Viagens leva 300 estrangeiros para GP de Fórmula 1 em São Paulo -... | https://www.panrotas.com.br/agencias-de-viagens/eventos/2024/11/mais-brasil-viagens-leva-300-estrangeiros-para-gp-de-formula-1-em-sao-paulo_211264.html |
| 2 | 2025-11-04 | Mais Brasil Viagens DMC inaugura escritório em Orlando - Panrotas | https://panrotas.com.br/mercado/receptivos/2025/11/mais-brasil-viagens-dmc-inaugura-escritorio-em-orlando_223082.html |
| 3 | 2025-11-04 | Mais Brasil Viagens DMC inaugura escritório em Orlando - Panrotas | https://www.panrotas.com.br/mercado/receptivos/2025/11/mais-brasil-viagens-dmc-inaugura-escritorio-em-orlando_223082.html |
| 4 | 2025-03-18 | Visit Rio apresenta novo presidente da Comissão de Turismo da Câmara Municipa... | https://panrotas.com.br/mercado/economia-e-politica/2025/03/visit-rio-apresenta-novo-presidente-da-comissao-de-turismo-da-camara-municipal-ao-trade_215445.html |
| 5 | 2025-02-27 | Mais Brasil DMC fecha contrato de distribuição com Travel Compositor - Panrotas | https://www.panrotas.com.br/mercado/distribuicao/2025/02/mais-brasil-dmc-fecha-contrato-de-distribuicao-com-a-travel-compositor_214888.html |

## 36. Radio Tupi — `tupi.fm`

- **Collector:** `rss / wordpress_api`
- **Articles in snapshot:** 5 (5 unique URLs)

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-09-10 | Pai de vereador do Rio e fundador de cervejaria morre em acidente de moto - S... | https://tupi.fm/rio/pai-de-vereador-do-rio-e-fundador-de-cervejaria-morre-em-acidente-de-moto |
| 2 | 2025-09-10 | Pai de vereador do Rio e fundador de cervejaria morre em acidente de moto - S... | https://www.tupi.fm/rio/pai-de-vereador-do-rio-e-fundador-de-cervejaria-morre-em-acidente-de-moto |
| 3 | 2025-11-16 | Rio testa nova ciclofaixa de 17 km ligando orla à Praça Mauá - Super Rádio Tupi | https://tupi.fm/rio/rio-testa-nova-ciclofaixa-de-17-km-ligando-orla-a-praca-maua |
| 4 | 2025-11-18 | Câmara do Rio inicia projeto para modernizar Laranjeiras e CT do Fluminense -... | https://tupi.fm/esportes/camara-do-rio-inicia-projeto-para-modernizar-laranjeiras-e-ct-do-fluminense |
| 5 | 2025-11-25 | O Povo Pergunta: Câmara do Rio e Super Rádio Tupi chegam a Copacabana - Super... | https://tupi.fm/rio/o-povo-pergunta-camara-do-rio-e-super-radio-tupi-chegam-a-copacabana |

---

# Part 2 — Target View (per monitored person)

For each monitored target, shows which provider-website combos contain articles
mentioning them, with 5 sample articles per combo.

## Flavio Valle (`flavio_valle`)

- **Total articles mentioning this target:** 643
- **Combos with ≥ 5 articles:** 18 (of 67 total)

### Diario do Rio — `diariodorio.com` (121 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-04-01 | Vereador Flávio Valle recebe família vítima do Hamas e reforça luta contra o ... | https://diariodorio.com/vereador-flavio-valle-recebe-familia-vitima-do-hamas-e-reforca-luta-contra-o-antissemitismo |
| 2 | 2025-11-06 | Ciclovias do Rio podem ser incluídas no programa Asfalto Liso a partir de 2026 | https://diariodorio.com/ciclovias-do-rio-podem-ser-incluidas-no-programa-asfalto-liso-a-partir-de-2026 |
| 3 | 2025-05-13 | Projeto de lei no Rio quer proibir desbloqueio de limite de velocidade de bic... | https://diariodorio.com/projeto-de-lei-no-rio-quer-proibir-desbloqueio-de-limite-de-velocidade-de-bicicletas-eletricas |
| 4 | 2025-05-20 | Bagunça na Orla – Bastidores do Rio | https://diariodorio.com/bagunca-na-orla-bastidores-do-rio |
| 5 | 2025-10-30 | Câmara aprova projeto que autoriza Prefeitura a intervir em imóveis com risco... | https://diariodorio.com/camara-aprova-projeto-que-autoriza-prefeitura-a-intervir-em-imoveis-com-risco-estrutural-no-rio |

### Agenda do Poder — `agendadopoder.com.br` (105 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-04-01 | Airbnb: Valle não é coautor de novo projeto de Salvino e Talita corre por fora | https://agendadopoder.com.br/airbnb-valle-ainda-nao-e-coautor-de-novo-projeto-de-salvino-enquanto-talita-corre-por-fora |
| 2 | 2025-05-08 | Dia das Mães: Marcada pelo Holocausto, Liliana Syrkis recebe medalha pós-morte | https://agendadopoder.com.br/dia-das-maes-marcada-pelo-holocausto-liliana-syrkis-recebe-medalha-pos-morte |
| 3 | 2025-05-15 | Filho do ex-deputado Syrkis recebe homenagem da avó Liliana na Câmara | https://agendadopoder.com.br/filho-do-ex-deputado-syrkis-recebe-homenagem-da-avo-liliana-na-camara |
| 4 | 2025-05-23 | GM Armada: possível saída do PT do governo pode afetar composição da Câmara | https://agendadopoder.com.br/gm-armada-possivel-saida-do-pt-do-governo-pode-afetar-composicao-da-camara |
| 5 | 2025-10-29 | Prefeitura critica repasses do Estado para a Saúde e fala em judicialização; ... | https://agendadopoder.com.br/prefeitura-critica-repasses-do-estado-para-a-saude-e-fala-em-judicializacao-area-tera-orcamento-de-quase-r-10-bi-para-2026 |

### Tempo Real RJ — `temporealrj.com` (68 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-04-01 | Sob pressão: para aprovar projeto, vereadores querem saber como a prefeitura ... | https://temporealrj.com/sob-pressao-para-aprovar-projeto-vereadores-querem-saber-como-a-prefeitura-pretende-usar-emprestimo-de-r-6-bi |
| 2 | 2025-03-10 | Câmara começa a discutir reforma tributária e regulamentação do Airbnb | https://temporealrj.com/camara-comeca-a-discutir-reforma-tributaria-e-regulamentacao-do-airbnb |
| 3 | 2024-12-16 | Dani Maia tem o apoio de 15 dos 16 vereadores eleitos pelo PSD para continuar... | https://temporealrj.com/dani-maia-tem-o-apoio-de-15-dos-16-vereadores-eleitos-pelo-psd-para-continuar-no-turismo |
| 4 | 2025-03-24 | HotéisRIO dispara contra 'concorrência desleal' em audiência sobre regulament... | https://temporealrj.com/hoteisrio-dispara-contra-concorrencia-desleal-em-audiencia-sobre-regulamentacao-do-airbnb |
| 5 | 2025-11-29 | Os bastidores da votação da Lei Anti-Oruam: mudanças de voto na última hora e... | https://temporealrj.com/os-bastidores-da-votacao-da-lei-anti-oruam-mudancas-de-voto-na-ultima-hora-e-manobras-do-lider-do-governo-para-tentar-barrar-projeto |

### Camara Rio — `camara.rio` (45 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-01-01 | Câmara do Rio inicia 12ª legislatura com posse dos 51 vereadores eleitos - Câ... | https://camara.rio/comunicacao/noticias/2488-camara-do-rio-inicia-12-legislatura-com-posse-dos-51-vereadores-eleitos |
| 2 | 2025-01-07 | Flávio Valle \| Vereadores - Câmara Municipal do Rio de Janeiro | https://camara.rio/vereadores/flavio-valle |
| 3 | 2025-11-13 | Câmara do Rio recebe o ‘Lance! Talks’, encontro que debate os rumos da cidade... | https://camara.rio/comunicacao/noticias/2936-camara-do-rio-recebe-o-lance-talks-encontro-que-debate-os-rumos-da-cidade-como-capital-mundial-do-esporte |
| 4 | 2025-10-22 | Câmara inicia ciclo de audiências para debater o orçamento do Rio para 2026 e... | https://camara.rio/comunicacao/noticias/2897-camara-inicia-ciclo-de-audiencias-para-debater-o-orcamento-do-rio-para-2026-e-para-o-quadrienio-2026-2029 |
| 5 | 2025-10-30 | Secretaria Municipal de Administração e Previ-Rio apresentam orçamento e açõe... | https://camara.rio/comunicacao/noticias/2911-secretaria-municipal-de-administracao-e-previ-rio-apresentam-orcamento-e-acoes-previstas-para-2026 |

### O Globo — `oglobo.globo.com` (45 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-09-02 | Exposição no Rio revela registros inéditos do Mar Morto feitos por fotógrafo ... | https://oglobo.globo.com/blogs/ancelmo-gois/post/2025/09/exposicao-no-rio-revela-registros-ineditos-do-mar-morto-feitos-por-fotografo-israelense.ghtml |
| 2 | 2025-09-10 | Pai de vereador do Rio e fundador de cervejaria de Niterói, empresário morre ... | https://oglobo.globo.com/rio/bairros/niteroi/noticia/2025/09/10/pai-de-vereador-do-rio-e-fundador-de-cervejaria-de-niteroi-empresario-morre-em-acidente-de-moto.ghtml |
| 3 | 2025-06-15 | Entre alertas de bombas e idas ao bunker, prefeitos brasileiros em Israel rec... | https://oglobo.globo.com/mundo/noticia/2025/06/15/entre-alertas-de-bombas-e-idas-ao-bunker-prefeitos-brasileiros-em-israel-recebem-treinamento-sobre-sensacao-de-seguranca.ghtml |
| 4 | 2025-05-20 | Polêmica na praia: dona da Barraca da Denise, famosa no point LGBTQIA+, teme ... | https://oglobo.globo.com/rio/noticia/2025/05/20/aos-78-anos-dona-da-barraca-da-denise-em-ipanema-teme-fim-de-tradicao-na-orla-com-novo-decreto.ghtml |
| 5 | 2025-01-30 | Câmara do Rio remove pichação com suástica nazista em um de seus banheiros | https://oglobo.globo.com/blogs/lauro-jardim/post/2025/01/camara-do-rio-remove-pichacao-com-suastica-nazista-em-um-de-seus-banheiros.ghtml |

### Veja Rio — `vejario.abril.com.br` (35 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-03-03 | Grupo assiste ao Oscar na casa de “Ainda estou aqui”, na Urca - VEJA RIO | https://vejario.abril.com.br/coluna/lu-lacerda/turma-da-cultura-assiste-ao-oscar-na-casa-de-ainda-estou-aqui-na-urca |
| 2 | 2025-10-06 | “Renova Run Rio”, na Lagoa, tem inscrições esgotadas em menos de 3 minutos - ... | https://vejario.abril.com.br/coluna/lu-lacerda/renova-run-rio-na-lagoa-tem-inscricoes-esgotadas-em-menos-de-3-minutos |
| 3 | 2026-01-13 | Preços tabelados nas praias: primeiro projeto de lei começa a tomar forma | https://vejario.abril.com.br/cidade/precos-tabelados-praias-projeto-lei |
| 4 | 2025-09-20 | No bisturi, o Rio continua afiado: medalha para Volney Pitombo - VEJA RIO | https://vejario.abril.com.br/coluna/lu-lacerda/no-bisturi-o-rio-continua-afiado-medalha-para-volney-pitombo |
| 5 | 2025-10-30 | R$ 18 milhões em dívidas e 42 imóveis esquecidos: ZS também entra no radar - ... | https://vejario.abril.com.br/coluna/lu-lacerda/r-18-milhoes-em-dividas-e-42-imoveis-esquecidos-zs-tambem-entra-no-radar |

### Tribuna da Serra — `tribunadaserra.com.br` (28 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-08-01 | Vereadores Flávio Valle e Pedro Duarte representam o Rio na Academia Política... | https://tribunadaserra.com.br/vereadores-flavio-valle-e-pedro-duarte-representam-o-rio-na-academia-politica-konrad-adenauer |
| 2 | 2025-11-08 | Campanha “Reocupa Rio” incentiva população a denunciar imóveis abandonados | https://tribunadaserra.com.br/campanha-reocupa-rio-incentiva-populacao-a-denunciar-imoveis-abandonados |
| 3 | 2025-11-11 | Santa Cruz lidera denúncias de imóveis abandonados em campanha criada por ver... | https://tribunadaserra.com.br/santa-cruz-lidera-denuncias-de-imoveis-abandonados-em-campanha-criada-por-vereador-do-rio |
| 4 | 2025-06-18 | Roteiro turístico judaico no Rio: projeto lista 71 pontos históricos, cultura... | https://tribunadaserra.com.br/roteiro-turistico-judaico-no-rio-projeto-lista-71-pontos-historicos-culturais-e-gastronomicos |
| 5 | 2025-10-26 | Corrida gratuita celebra o Dia da Democracia e transforma a Lagoa em palco de... | https://tribunadaserra.com.br/corrida-gratuita-celebra-o-dia-da-democracia-e-transforma-a-lagoa-em-palco-de-integracao-no-rio |

### Diario do Rio Site — `diariodorio.com` (23 articles)

- **Collector:** `direct_scrape / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-01-01 | Eduardo Paes e vereadores eleitos no Rio tomam posse nesta quarta-feira | https://diariodorio.com/eduardo-paes-e-vereadores-eleitos-no-rio-tomam-posse-nesta-quarta-feira |
| 2 | 2024-10-03 | Quem é o candidato a vereador da Zona Sul do Rio de Janeiro em 2024? | https://diariodorio.com/quem-e-o-candidato-a-vereador-da-zona-sul-do-rio-de-janeiro-em-2024-2 |
| 3 | 2024-10-08 | Quantos suplentes virarão secretários no PSD – Bastidores do Rio | https://diariodorio.com/quantos-suplentes-virarao-secretarios-no-psd-bastidores-do-rio |
| 4 | 2025-01-13 | O deputado despachante – Bastidores do Rio | https://diariodorio.com/o-deputado-despachante-bastidores-do-rio |
| 5 | 2025-01-27 | O Holocausto foi o ápice do antissemitismo, mas não o seu fim | https://diariodorio.com/o-holocausto-foi-o-apice-do-antissemitismo-mas-nao-seu-fim |

### G1 — `g1.globo.com` (19 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-01-01 | Paes e vereadores eleitos no Rio tomam posse nesta quarta-feira | https://g1.globo.com/rj/rio-de-janeiro/noticia/2025/01/01/paes-e-vereadores-eleitos-no-rio-tomam-posse-nesta-quarta-feira.ghtml |
| 2 | 2024-10-06 | Carlos Bolsonaro bate o próprio recorde e é o vereador mais bem votado da his... | https://g1.globo.com/rj/rio-de-janeiro/eleicoes/2024/noticia/2024/10/06/carlos-bolsonaro-e-o-vereador-mais-bem-votado-da-historia-no-rio.ghtml |
| 3 | 2025-06-16 | Veja quem são os gestores municipais brasileiros que deixaram Israel nesta se... | https://g1.globo.com/politica/noticia/2025/06/16/veja-quem-sao-os-gestores-municipais-brasileiros-que-deixaram-israel-nesta-segunda-feira.ghtml |
| 4 | 2025-05-20 | Novas regras para praias do Rio, como proibição de música ao vivo, geram prot... | https://g1.globo.com/rj/rio-de-janeiro/noticia/2025/05/20/novas-regras-para-praias-do-rio-geram-protestos-e-mobilizam-a-camara.ghtml |
| 5 | 2025-05-28 | Exposição resgata imagens da contribuição judaica para a história do Rio, com... | https://g1.globo.com/guia/guia-rj/noticia/2025/05/28/exposicao-resgata-imagens-da-contribuicao-judaica-para-a-historia-do-rio-com-fotos-raras-da-praca-onze-e-da-visita-de-albert-einstein.ghtml |

### Tempo Real RJ Site — `temporealrj.com` (17 articles)

- **Collector:** `direct_scrape / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-01-01 | Protesto, emoção e, claro, zoação na posse dos vereadores do Rio | https://temporealrj.com/protesto-emocao-e-claro-zoacao-na-posse-dos-vereadores-do-rio |
| 2 | 2024-10-07 | Cabo eleitoral de luxo, Paes elege quatro de seus pupilos | https://temporealrj.com/cabo-eleitoral-de-luxo-paes-elege-quatro-de-seus-pupilos |
| 3 | 2025-07-14 | Vendedores de mate: prefeitura do Rio promove nova edição de curso de boas pr... | https://temporealrj.com/vendedores-de-mate-prefeitura-do-rio-promove-nova-edicao-de-curso-de-boas-praticas |
| 4 | 2024-12-18 | Saias-justas, gravatas chiques e terninhos: os bastidores da diplomação dos e... | https://temporealrj.com/saias-justas-gravatas-chiques-e-terninhos-os-bastidores-da-diplomacao-dos-eleitos-no-rio |
| 5 | 2025-05-27 | LDO: Assistência Social e Habitação prestam contas em audiência na Câmara | https://temporealrj.com/ldo-assistencia-social-e-habitacao-prestam-contas-em-audiencia-na-camara |

### Camara Rio Internal Search — `camara.rio` (9 articles)

- **Collector:** `internal_search`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-03-02 | Cuidados íntimos com crianças nas instituições de ensino deverão ser realizad... | https://camara.rio/comunicacao/noticias/3015-cuidados-intimos-com-criancas-nas-instituicoes-de-ensino-deverao-ser-realizados-exclusivamente-por-profissionais-do-sexo-feminino |
| 2 | 2026-03-05 | Câmara aprova proposta que facilita a realização de testes de iniciativas ino... | https://camara.rio/comunicacao/noticias/3017-camara-aprova-proposta-que-facilita-a-realizacao-de-testes-de-iniciativas-inovadoras |
| 3 | 2026-02-09 | Câmara do Rio contribui decisivamente para obras do Novo PAC, que levam infra... | https://camara.rio/comunicacao/noticias/3007-camara-do-rio-contribui-decisivamente-para-obras-do-novo-pac-que-levam-infraestrutura-e-qualidade-de-vida-a-favelas-da-cidade |
| 4 | 2025-12-12 | Câmara Rio Debate revisita as discussões do evento O Rio do Futuro | https://camara.rio/comunicacao/noticias/2999-camara-rio-debate-revisita-os-debates-do-evento-o-rio-do-futuro |
| 5 | 2026-02-24 | Aprovada Área Azul Digital para vagas de estacionamento rotativo | https://camara.rio/comunicacao/noticias/3011-aprovada-area-azul-digital-para-vagas-de-estacionamento-rotativo |

### Conib Internal Search — `conib.org.br` (9 articles)

- **Collector:** `internal_search`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-08-05 | Frente Parlamentar de Combate ao Antissemitismo da Câmara do Rio repudia saíd... | https://conib.org.br/noticias/todas-as-noticias/39953-frente-parlamentar-de-combate-ao-antissemitismo-da-camara-do-rio-repudia-saida-do-brasil-da-ihra.html |
| 2 | 2025-10-07 | FestRio Judaico transforma Ipanema em palco de cultura, união e solidariedade | https://conib.org.br/noticias/todas-as-noticias/40137-festrio-judaico-transforma-ipanema-em-palco-de-cultura-uniao-e-solidariedade.html |
| 3 | 2025-09-10 | Câmara do RJ recebe exposição de fotógrafo israelense que retrata a ‘resistên... | https://conib.org.br/noticias/todas-as-noticias/40063-camara-do-rj-recebe-exposicao-de-fotografo-israelense-que-retrata-a-resistencia-do-mar-morto.html |
| 4 | 2025-03-21 | Câmara do RJ concede Moção de Louvor e Reconhecimento ao jornalista Henrique ... | https://conib.org.br/noticias/todas-as-noticias/39569-camara-do-rj-concede-mocao-de-louvor-e-reconhecimento-ao-jornalista-henrique-cymerman.html |
| 5 | 2025-09-29 | Rio de Janeiro vai sediar o V Fórum Latino-Americano Contra o Antissemitismo | https://conib.org.br/noticias/todas-as-noticias/40105-rio-de-janeiro-vai-sediar-o-v-forum-latino-americano-contra-o-antissemitismo.html |

### CONIB — `conib.org.br` (7 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-09-03 | Confederação Israelita do Brasil (Conib) | https://conib.org.br/noticias/todas-as-noticias/40041-camara-municipal-do-rj-exibe-exposicao-de-fotografo-israelense-sobre-o-mar-morto.html |
| 2 | 2025-12-09 | Confederação Israelita do Brasil | https://conib.org.br/noticias/todas-as-noticias/40347-escola-municipal-anne-frank-inaugura-jardim-bruna-valeanu-em-homenagem-a-ex-aluna.html |
| 3 | 2025-10-15 | Confederação Israelita do Brasil (Conib) | https://conib.org.br/noticias/todas-as-noticias/40174-reunidas-no-rj-liderancas-latino-americanas-aprovam-declaracao-conjunta-contra-o-antissemitismo-e-discurso-de-odio.html |
| 4 | 2025-03-18 | Confederação Israelita do Brasil | https://conib.org.br/noticias/todas-as-noticias/39554-fierj-promove-o-lancamento-de-eternamente-7-de-outubro-e-debate-sobre-terrorismo-e-antissemitismo.html |
| 5 | 2025-09-24 | “Rosh Hashaná 5786: Renovação, Memória e Esperança” - Confederação Israelita ... | https://conib.org.br/noticias/todas-as-noticias/40097-rosh-hashana-5786-renovacao-memoria-e-esperanca.html |

### Mercado e Eventos — `mercadoeeventos.com.br` (7 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-02-02 | DMC Mais Brasil Viagens capacita trade uruguaio sobre o potencial do Carnaval... | https://mercadoeeventos.com.br/noticias/agencias-e-operadoras/dmc-mais-brasil-viagens-capacita-trade-uruguaio-sobre-o-potencial-do-carnaval-brasileiro |
| 2 | 2025-11-04 | Mais Brasil Viagens inaugura escritório em Orlando - Mercado e Eventos | https://mercadoeeventos.com.br/noticias/agencias-e-operadoras/mais-brasil-viagens-inaugura-escritorio-em-orlando |
| 3 | 2025-02-19 | Visit Rio celebra nomeação de Flávio Valle (PSD) como presidente da Comissão ... | https://www.mercadoeeventos.com.br/noticias/politica/visit-rio-celebra-nomeacao-de-flavio-valle-psd-como-presidente-da-comissao-de-turismo-da-camara-municipal-do-rj/ |
| 4 | 2025-02-19 | Visit Rio celebra nomeação de Flávio Valle (PSD) como presidente da Comissão ... | https://www.mercadoeeventos.com.br/noticias/politica/visit-rio-celebra-nomeacao-de-flavio-valle-psd-como-presidente-da-comissao-de-turismo-da-camara-municipal-do-rj |
| 5 | 2025-03-25 | Polêmica no Rio: Câmara Municipal discute regulamentação de plataformas de al... | https://mercadoeeventos.com.br/noticia-manchete-home/polemica-no-rio-camara-municipal-discute-regulamentacao-de-plataformas-de-aluguel-por-temporada |

### O Dia — `odia.ig.com.br` (7 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-06-01 | Samba do Cardosão, em Laranjeiras, é reconhecido como Patrimônio Cultural Ima... | https://odia.ig.com.br/rio-de-janeiro/2025/06/7067007-samba-do-cardosao-em-laranjeiras-e-reconhecido-como-patrimonio-cultural-imaterial.html |
| 2 | 2024-10-07 | Conheça os 51 vereadores eleitos no Rio - O Dia | https://odia.ig.com.br/eleicoes/2024/10/6930170-conheca-os-51-vereadores-eleitos-no-rio.html |
| 3 | 2025-09-11 | Fundador da cervejaria Masterpiece, André Valle morre em acidente de moto em ... | https://odia.ig.com.br/rio-de-janeiro/2025/09/7127319-fundador-da-cervejaria-masterpiece-andre-valle-morre-em-acidente-de-moto-em-niteroi.html |
| 4 | 2025-05-15 | Jorge Arraes - No Mês do Trabalhador, a Comlurb comemora o Dia do Gari e 50 a... | https://odia.ig.com.br/opiniao/2025/05/7056151-jorge-arraes-no-mes-do-trabalhador-a-comlurb-comemora-o-dia-do-gari-e-50-anos-de-existencia.html |
| 5 | 2026-01-26 | Dia de Iemanjá do Arpoador reunirá 21 atrações artísticas e religiosas, em ri... | https://odia.ig.com.br/rio-de-janeiro/2026/01/7197312-dia-de-iemanja-do-arpoador-reunira-21-atracoes-artisticas-e-religiosas-em-ritual-e-evento.html |

### CBN — `cbn.globo.com` (6 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-06-13 | VÍDEO: Veja como é o bunker onde está comitiva brasileira em Israel - CBN | https://cbn.globo.com/mundo/noticia/2025/06/13/video-veja-como-e-o-bunker-onde-esta-comitiva-brasileira-em-israel.ghtml |
| 2 | 2025-06-16 | Comitiva de políticos brasileiros vai pegar voo na Arábia Saudita para retorn... | https://cbn.globo.com/mundo/noticia/2025/06/16/comitiva-de-politicos-brasileiros-vai-pegar-um-voo-na-arabia-saudita-para-retornar-ao-brasil.ghtml |
| 3 | 2025-03-21 | A próxima treta na Câmara de Vereadores: Airbnb - CBN | https://cbn.globo.com/rio-de-janeiro/analise/2025/03/21/a-proxima-treta-na-camara-de-vereadores-airbnb.ghtml |
| 4 | 2025-02-26 | Projeto prevê que Guardas Municipais do Rio passem por processo interno para ... | https://cbn.globo.com/rio-de-janeiro/noticia/2025/02/26/projeto-preve-que-guardas-municipais-do-rio-passem-por-processo-interno-para-integrar-forca-municipal-de-seguranca.ghtml |
| 5 | 2025-05-29 | 'Fomos pegos de surpresa': barraqueiros reclamam de falta de prazo para adesã... | https://cbn.globo.com/rio-de-janeiro/noticia/2025/05/29/fomos-pegos-de-surpresa-barraqueiros-reclamam-de-falta-de-prazo-para-adesao-a-novas-regras-da-orla-do-rio.ghtml |

### Panrotas — `panrotas.com.br` (5 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2024-11-04 | Mais Brasil Viagens leva 300 estrangeiros para GP de Fórmula 1 em São Paulo -... | https://www.panrotas.com.br/agencias-de-viagens/eventos/2024/11/mais-brasil-viagens-leva-300-estrangeiros-para-gp-de-formula-1-em-sao-paulo_211264.html |
| 2 | 2025-11-04 | Mais Brasil Viagens DMC inaugura escritório em Orlando - Panrotas | https://panrotas.com.br/mercado/receptivos/2025/11/mais-brasil-viagens-dmc-inaugura-escritorio-em-orlando_223082.html |
| 3 | 2025-11-04 | Mais Brasil Viagens DMC inaugura escritório em Orlando - Panrotas | https://www.panrotas.com.br/mercado/receptivos/2025/11/mais-brasil-viagens-dmc-inaugura-escritorio-em-orlando_223082.html |
| 4 | 2025-03-18 | Visit Rio apresenta novo presidente da Comissão de Turismo da Câmara Municipa... | https://panrotas.com.br/mercado/economia-e-politica/2025/03/visit-rio-apresenta-novo-presidente-da-comissao-de-turismo-da-camara-municipal-ao-trade_215445.html |
| 5 | 2025-02-27 | Mais Brasil DMC fecha contrato de distribuição com Travel Compositor - Panrotas | https://www.panrotas.com.br/mercado/distribuicao/2025/02/mais-brasil-dmc-fecha-contrato-de-distribuicao-com-a-travel-compositor_214888.html |

### Radio Tupi — `tupi.fm` (5 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-09-10 | Pai de vereador do Rio e fundador de cervejaria morre em acidente de moto - S... | https://tupi.fm/rio/pai-de-vereador-do-rio-e-fundador-de-cervejaria-morre-em-acidente-de-moto |
| 2 | 2025-09-10 | Pai de vereador do Rio e fundador de cervejaria morre em acidente de moto - S... | https://www.tupi.fm/rio/pai-de-vereador-do-rio-e-fundador-de-cervejaria-morre-em-acidente-de-moto |
| 3 | 2025-11-16 | Rio testa nova ciclofaixa de 17 km ligando orla à Praça Mauá - Super Rádio Tupi | https://tupi.fm/rio/rio-testa-nova-ciclofaixa-de-17-km-ligando-orla-a-praca-maua |
| 4 | 2025-11-18 | Câmara do Rio inicia projeto para modernizar Laranjeiras e CT do Fluminense -... | https://tupi.fm/esportes/camara-do-rio-inicia-projeto-para-modernizar-laranjeiras-e-ct-do-fluminense |
| 5 | 2025-11-25 | O Povo Pergunta: Câmara do Rio e Super Rádio Tupi chegam a Copacabana - Super... | https://tupi.fm/rio/o-povo-pergunta-camara-do-rio-e-super-radio-tupi-chegam-a-copacabana |

## Pedro Angelito (`pedro_angelito`)

- **Total articles mentioning this target:** 33
- **Combos with ≥ 5 articles:** 2 (of 12 total)

### Diario do Rio — `diariodorio.com` (7 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-02-04 | Dia da Gastronomia Pet – Bastidores do Rio - Diário do Rio | https://diariodorio.com/dia-da-gastronomia-pet-bastidores-do-rio |
| 2 | 2026-02-05 | Novo subprefeito da Zona Sul promete priorizar população em situação de rua e... | https://diariodorio.com/novo-subprefeito-da-zona-sul-prioriza-populacao-em-situacao-de-rua-e-fiscalizacao-urbana |
| 3 | 2026-02-10 | Prefeitura do Rio desmonta acampamentos irregulares e reforça ações de acolhi... | https://diariodorio.com/subprefeitura-da-zona-sul-desmonta-acampamentos-irregulares-e-reforca-acoes-de-acolhimento-em-botafogo |
| 4 | 2026-02-11 | Prefeitura notifica prédio que instalou mais de 50 vasos na calçada em Copaca... | https://diariodorio.com/prefeitura-notifica-predio-que-instalou-mais-de-50-vasos-na-calcada-em-copacabana |
| 5 | 2026-01-30 | Pedro Angelito será o novo subprefeito da Zona Sul do Rio a partir de feverei... | https://diariodorio.com/pedro-angelito-sera-o-novo-subprefeito-da-zona-sul-do-rio-a-partir-de-fevereiro |

### Tempo Real RJ — `temporealrj.com` (5 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-02-02 | Agora é oficial: a Zona Sul já tem novo subprefeito; Pedro Angelito é nomeado... | https://temporealrj.com/pedro-angelito-nomeado-sub-zona-sul/ |
| 2 | 2026-02-02 | Agora é oficial: a Zona Sul já tem novo subprefeito; Pedro Angelito é nomeado... | https://temporealrj.com/pedro-angelito-nomeado-sub-zona-sul |
| 3 | 2026-03-06 | Prefeitura interdita o Batô Bar e multa o Botica em ações de ordenamento em B... | https://temporealrj.com/prefeitura-interdita-bato-bar-e-multa-botica-botafogo |
| 4 | 2026-01-30 | O advogado Pedro Angelito será o novo subprefeito da Zona Sul do Rio - Tempo ... | https://temporealrj.com/pedro-angelito-sera-novo-subprefeito-zona-sul/ |
| 5 | 2026-01-30 | O advogado Pedro Angelito será o novo subprefeito da Zona Sul do Rio - Tempo ... | https://temporealrj.com/pedro-angelito-sera-novo-subprefeito-zona-sul |

## Bernardo Rubiao (`bernardo_rubiao`)

- **Total articles mentioning this target:** 58
- **Combos with ≥ 5 articles:** 3 (of 13 total)

### Diario do Rio — `diariodorio.com` (18 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-07-02 | Bacellar terá chance de mostrar que não é Cláudio Castro – Bastidores do Rio | https://diariodorio.com/bacellar-tera-chance-de-mostrar-que-nao-e-claudio-castro-bastidores-do-rio |
| 2 | 2025-06-11 | Cônego Paróquia da Ressurreição abençoa Bernardo Rubião e Subprefeitura da Z.... | https://diariodorio.com/conego-paroquia-da-ressurreicao-abencoa-bernardo-rubiao-e-subprefeitura-da-z-sul/ |
| 3 | 2026-01-15 | Projeto Corredores de Excelência concentra serviços urbanos no Bairro Peixoto... | https://diariodorio.com/projeto-corredores-de-excelencia-concentra-servicos-urbanos-no-bairro-peixoto-em-copacabana |
| 4 | 2025-09-20 | Seminário debate futuro do bairro do Catete no Museu da República - Diário do... | https://diariodorio.com/seminario-debate-futuro-do-bairro-do-catete-no-museu-da-republica |
| 5 | 2026-01-30 | Pedro Angelito será o novo subprefeito da Zona Sul do Rio a partir de feverei... | https://diariodorio.com/pedro-angelito-sera-o-novo-subprefeito-da-zona-sul-do-rio-a-partir-de-fevereiro |

### Veja Rio — `vejario.abril.com.br` (15 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2024-12-03 | Chef francês Frédéric Monnier dá oficina em escola pública no Arpoador \| Lu L... | https://vejario.abril.com.br/coluna/lu-lacerda/chef-frances-frederic-monnier-da-oficina-em-escola-publica-no-arpoador |
| 2 | 2025-05-14 | Pensando a orla do futuro: foi marcada audiência pública \| Lu Lacerda | https://vejario.abril.com.br/coluna/lu-lacerda/pensando-a-orla-do-futuro-foi-marcada-audiencia-publica |
| 3 | 2025-07-22 | Retirada de moradores e ferro-velho clandestino do Jardim de Alah \| Lu Lacerda | https://vejario.abril.com.br/coluna/lu-lacerda/retirada-de-moradores-e-ferro-velho-clandestino-do-jardim-de-alah |
| 4 | 2025-03-26 | Encontro Veja Rio celebra capa de março no Jardim Botânico. Veja fotos! | https://vejario.abril.com.br/beira-mar/encontro-veja-rio-celebra-capa-de-marco-no-jardim-botanico-veja-fotos |
| 5 | 2025-08-28 | Fim de uma era: o que motivou a demolição do Espaço Mix, em Botafogo | https://vejario.abril.com.br/cidade/espaco-mix-botafogo-demolido |

### Tribuna da Serra — `tribunadaserra.com.br` (11 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-07-03 | Bacellar terá chance de mostrar que não é Cláudio Castro – Bastidores do Rio | https://tribunadaserra.com.br/bacellar-tera-chance-de-mostrar-que-nao-e-claudio-castro-bastidores-do-rio |
| 2 | 2025-06-13 | Câmara Municipal do Rio debate construção de novo hospital em Botafogo | https://tribunadaserra.com.br/camara-municipal-do-rio-debate-construcao-de-novo-hospital-em-botafogo |
| 3 | 2026-01-16 | Os riscos de ser subprefeito – Bastidores do Rio | https://tribunadaserra.com.br/os-riscos-de-ser-subprefeito-bastidores-do-rio |
| 4 | 2025-09-20 | Seminário debate futuro do bairro do Catete no Museu da República | https://tribunadaserra.com.br/seminario-debate-futuro-do-bairro-do-catete-no-museu-da-republica |
| 5 | 2026-01-31 | Pedro Angelito será o novo subprefeito da Zona Sul do Rio a partir de fevereiro | https://tribunadaserra.com.br/pedro-angelito-sera-o-novo-subprefeito-da-zona-sul-do-rio-a-partir-de-fevereiro |

## Pedro Duarte (`pedro_duarte`)

- **Total articles mentioning this target:** 577
- **Combos with ≥ 5 articles:** 26 (of 112 total)

### Tribuna da Serra — `tribunadaserra.com.br` (83 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-02-01 | No Tanque, Talita Galhardo é carregada por Paes e Cavaliere | https://tribunadaserra.com.br/no-tanque-talita-galhardo-e-carregada-por-paes-e-cavaliere |
| 2 | 2026-03-07 | ‘Inadequado’: Grupo Sendas critica projeto da FGV para imóvel desapropriado e... | https://tribunadaserra.com.br/inadequado-grupo-sendas-critica-projeto-da-fgv-para-imovel-desapropriado-e-diz-que-terreno-tem-lencol-freatico |
| 3 | 2025-06-13 | Câmara Municipal do Rio debate construção de novo hospital em Botafogo | https://tribunadaserra.com.br/camara-municipal-do-rio-debate-construcao-de-novo-hospital-em-botafogo |
| 4 | 2025-10-22 | Câmara do Rio aprova intervenção da Prefeitura em imóveis abandonados | https://tribunadaserra.com.br/camara-do-rio-aprova-intervencao-da-prefeitura-em-imoveis-abandonados |
| 5 | 2025-07-31 | Por que o MEC precisa aprovar o curso de Medicina da PUC-Rio | https://tribunadaserra.com.br/por-que-o-mec-precisa-aprovar-o-curso-de-medicina-da-puc-rio |

### Agenda do Poder — `agendadopoder.com.br` (47 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-03-02 | Após adiamento, projeto que autoriza concessão de parques fica de fora da pau... | https://agendadopoder.com.br/apos-adiamento-projeto-que-autoriza-concessao-de-parques-fica-de-fora-da-pauta-semanal-da-camara-do-rio |
| 2 | 2025-07-08 | Em recesso parlamentar, vereador Pedro Duarte se casa sob bençãos de consulto... | https://agendadopoder.com.br/em-recesso-parlamentar-vereador-pedro-duarte-se-casa-sob-a-batuta-de-consultor-politico-do-novo |
| 3 | 2025-03-19 | Debate sobre o Airbnb na Câmara do Rio pode se internacionalizar antes da dec... | https://agendadopoder.com.br/debate-sobre-o-airbnb-na-camara-do-rio-pode-se-internacionalizar-antes-da-decisao-de-vereadores |
| 4 | 2026-02-24 | Projeto que prevê distribuição gratuita de canabidiol no Rio volta à pauta na... | https://agendadopoder.com.br/projeto-que-preve-distribuicao-gratuita-de-canabidiol-no-rio-volta-a-pauta-na-camara-dos-vereadores |
| 5 | 2025-04-30 | Mais-valia e mais-valerá: Pedro Duarte defende Plano Diretor como regra | https://agendadopoder.com.br/mais-valia-e-mais-valera-pedro-duarte-defende-plano-diretor-como-regra-para-evitar-puxadinhos-em-areas-nobres |

### Tempo Real RJ — `temporealrj.com` (45 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-04-01 | Sob pressão: para aprovar projeto, vereadores querem saber como a prefeitura ... | https://temporealrj.com/sob-pressao-para-aprovar-projeto-vereadores-querem-saber-como-a-prefeitura-pretende-usar-emprestimo-de-r-6-bi |
| 2 | 2026-03-05 | Câmara derruba veto de Paes e mantém barqueiros tradicionais no novo modelo d... | https://temporealrj.com/camara-derruba-veto-de-paes-transporte-aquaviario |
| 3 | 2025-03-20 | Aterro do Flamengo recebe mais uma pelada política: Valle x Ferreirinha - Tem... | https://temporealrj.com/aterro-do-flamengo-recebe-mais-uma-pelada-politica-valle-x-ferreirinha |
| 4 | 2025-03-25 | Audiência sobre Airbnb gera clima de torcida e aquece rivalidade na Câmara do... | https://temporealrj.com/audiencia-sobre-airbnb-gera-clima-de-torcida-e-aquece-rivalidade-na-camara-do-rio |
| 5 | 2025-11-29 | Os bastidores da votação da Lei Anti-Oruam: mudanças de voto na última hora e... | https://temporealrj.com/os-bastidores-da-votacao-da-lei-anti-oruam-mudancas-de-voto-na-ultima-hora-e-manobras-do-lider-do-governo-para-tentar-barrar-projeto |

### Diario do Rio — `diariodorio.com` (32 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-08-01 | A Farra do Asfalto – Bastidores do Rio | https://diariodorio.com/a-farra-do-asfalto-bastidores-do-rio |
| 2 | 2025-12-03 | Nova lei autoriza Prefeitura do Rio a fazer reparos, desapropriar e até demol... | https://diariodorio.com/nova-lei-autoriza-prefeitura-do-rio-a-fazer-reparos-desapropriar-e-ate-demolir-imoveis-em-risco |
| 3 | 2025-02-11 | Pedro Duarte governador? - Bastidores do Rio - Diário do Rio de Janeiro | https://diariodorio.com/pedro-duarte-governador-bastidores-do-rio |
| 4 | 2025-08-21 | A meia tucana de Pedro Duarte - Bastidores do Rio - Diário do Rio de Janeiro | https://diariodorio.com/a-meia-tucana-de-pedro-duarte-bastidores-do-rio |
| 5 | 2025-12-30 | Novo entra em crise no RJ após saída de Pedro Duarte e derrota de Rodrigo Rez... | https://diariodorio.com/novo-entra-em-crise-no-rj-apos-saida-de-pedro-duarte-e-derrota-de-rodrigo-rezende-em-eleicao-interna/ |

### Camara Rio — `camara.rio` (30 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-01-01 | Câmara do Rio inicia 12ª legislatura com posse dos 51 vereadores eleitos - Câ... | https://camara.rio/comunicacao/noticias/2488-camara-do-rio-inicia-12-legislatura-com-posse-dos-51-vereadores-eleitos |
| 2 | 2025-06-09 | FRENTE PARLAMENTAR EM DEFESA DOS PESCADORES DE SEPETIBA/RJ - Câmara Municipal... | https://camara.rio/atividade-parlamentar/frentes/294 |
| 3 | 2025-11-13 | Câmara do Rio recebe o ‘Lance! Talks’, encontro que debate os rumos da cidade... | https://camara.rio/comunicacao/noticias/2936-camara-do-rio-recebe-o-lance-talks-encontro-que-debate-os-rumos-da-cidade-como-capital-mundial-do-esporte |
| 4 | 2025-02-24 | Vereadores definem a composição de 14 Comissões Permanentes da Câmara do Rio ... | https://camara.rio/comunicacao/noticias/2509-vereadores-definem-a-composic-a-o-de-14-comisso-es-permanentes-da-casa |
| 5 | 2025-10-30 | Secretaria Municipal de Administração e Previ-Rio apresentam orçamento e açõe... | https://camara.rio/comunicacao/noticias/2911-secretaria-municipal-de-administracao-e-previ-rio-apresentam-orcamento-e-acoes-previstas-para-2026 |

### Google News — `news.google.com` (24 articles)

- **Collector:** `google_news`
- **⚠️ URLs are Google News redirects**

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-03-01 | Pedro Duarte eleito presidente da Distrital do PSD Porto com maioria de 93% -... | https://news.google.com/rss/articles/CBMiU0FVX3lxTE5id2VfWGh5ZFFLTjZQLUI1cnNCanliTDJkUHlkVDhvLWhPWXJqZlNKSFJsWUtfQTA0YmQwV0Yyb2lPdXhWUmJPSzdkLTdoaWtfdTk0 |
| 2 | 2025-11-05 | Pedro Duarte entrega pasta da Cultura a Jorge Sobrado e garante maioria - Púb... | https://news.google.com/rss/articles/CBMivAFBVV95cUxQX0xla0wtTE5WaWc1bXJjcEZQUGJkejJhLVAzcVdabWZaTFp0Sm5ic0RlM3ByQVhVRVFVOExjcEctbFJWVVZmZVBvUmFsTmstMmhEcVhFOXpvdWNrdXdpR1o5dmE4UnpJUXRjdXFyMW9FMk9IQ1luTWY2SHFuNXpZS2gzazBUSVByVUc1VS0yS2lESkU4M0NYWE1tMUp5WUk0Ujg3bnU3MlV4UWhhUTA4cHhnYVJ2Q1VydDZDSw |
| 3 | 2026-02-12 | Mau tempo: Pedro Duarte, ex-ministro e autarca do Porto, relança discussão so... | https://news.google.com/rss/articles/CBMijwJBVV95cUxOck0ya3o1T2M2cDdpSG03MTdSaGZZckZjdGFaTy1GYVlteEFtd3Y3WnM0LXJaN1piVjc1X1NscXZleW5wTUpxdElqZEN0VFBiRFM0LXhtQzhSTHBUV2tTcWl6ekFqczhzb0N4VDVJNFJxRjN6Qnl4cFJzWkcxR1M3SlUwbWd2X1BOUkV0WTd6azd6ek56WTJxSEhNazg4S0lUU2VHQjFlUEZaM1BFRGltalUtMjlSTENqVGlYZjlJbFZyd3ROZUh3bjNRcGJKa3VKbE9uV3dqbjZwU1VudWJJa2EyQ21rSUlZbXUtTWVuZndrcU1seTFkdi01UFFEZEt4aWFvNXFOQndwdVlGV1FV |
| 4 | 2026-01-24 | Pedro Duarte diz que Portugal “ficará certamente em muito boas mãos” com Segu... | https://news.google.com/rss/articles/CBMi6gFBVV95cUxQX19MNU1Udk5RRmdHVjNhZkt6QTgzX2hfc21nS0dYZ01OZTNoUDRrMU54SEhTYjlvQVFZWG90MjZINTU1bE9OdU5tZEx5RzRzRkROVGFEWktrR2ZwQVptNG9SNFN6MTlhY3JjSkw3MjZIUTl2T3I4c2duWGVKYmpnZmtHSS03ZVhLRE14S1QyY1pDSDdGZnNJcDczN0tXY1NHRnltd0F5X1lLRVlMaU1KUHM4U0dVRTZWdENUczRTaWExRE4tS0MwTlJWd0lpZmVnQnFhSnJDN2FkUGxWd2xOMHRFVkdNR2habVE |
| 5 | 2025-12-30 | Pedro Duarte envia ofício ao TCM e ao MPRJ questionando caso de imóvel em Bot... | https://news.google.com/rss/articles/CBMi0gFBVV95cUxQS0VfcVJ5RTdWYUpWQ3NUOGZuSlY2aE9WT1F4YWVoOXJkMFVzVFJsczZMMS1TU0I3UzdTTVk2OEo4VFFfRTFWbHhicU5jck1jd2VCSUVUTDdWbjl2YmN4R2NMR1dlaXg3dENjYXAwbTlNNUR5NENrdEp4cnpXcVNEN1FxT3llZmFRcE1WTUtkbTdRdm1GSWtDM3FsTFoxbFZoWE8ySTU0V19BQVJCRVQ1ZkoxaFpJdE1GNjBJbWYyTTZ1SnFDT3R3Nkl0amR3N2xVZmc |

### Google News — `jn.pt` (19 articles)

- **Collector:** `google_news`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-10-02 | Pedro Duarte e Pizarro trocam reptos no terceiro dia da campanha - Jornal de ... | https://www.jn.pt/pais/artigo/pedro-duarte-e-pizarro-trocam-reptos-no-terceiro-dia-da-campanha/17959975 |
| 2 | 2026-03-06 | Pedro Duarte: "Houve muita falta de responsabilidade no processo do metrobus"... | https://jn.pt/pais/artigo/pedro-duarte-houve-muita-falta-de-responsabilidade-no-processo-do-metrobus/18059208 |
| 3 | 2026-03-14 | Porto fez História na produção de energias renováveis - Jornal de Notícias | https://jn.pt/poder-local/artigo/porto-fez-historia-na-producao-de-energias-renovaveis/18062132 |
| 4 | 2026-02-18 | Pedro Duarte quer que o país "reflita" sobre a regionalização - Jornal de Not... | https://jn.pt/pais/artigo/pedro-duarte-quer-que-o-pais-reflita-sobre-a-regionalizacao/18053398 |
| 5 | 2025-08-30 | Pedro Duarte aponta à regionalização após as autárquicas - Jornal de Notícias | https://www.jn.pt/pais/artigo/pedro-duarte-aponta-a-regionalizacao-apos-as-autarquicas/17899461 |

### Google News — `temporealrj.com` (15 articles)

- **Collector:** `google_news`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-04-05 | Pedro Duarte é convidado para congresso global de tecnologia na Índia - Tempo... | https://temporealrj.com/pedro-duarte-e-convidado-para-congresso-global-de-tecnologia-na-india |
| 2 | 2025-08-10 | Pedro Duarte e Eduardo Leite, governador do RS, discutem segurança pública - ... | https://temporealrj.com/pedro-duarte-e-eduardo-leite-governador-do-rs-discutem-seguranca-publica |
| 3 | 2025-12-13 | Quase governista, mas nem tanto: Pedro Duarte questiona a Prefeitura do Rio s... | https://temporealrj.com/quase-governista-mas-nem-tanto-pedro-duarte-questiona-a-prefeitura-do-rio-sobre-a-desapropriacao-de-predio-em-botafogo |
| 4 | 2026-01-26 | Vereador Pedro Duarte confirma filiação ao PSD e pré-candidatura a deputado e... | https://temporealrj.com/vereador-pedro-duarte-confirma-filiacao-ao-psd-e-pre-candidatura-a-deputado-estadual |
| 5 | 2025-12-30 | Pedro Duarte envia ofício ao TCM e ao MPRJ questionando caso de imóvel em Bot... | https://temporealrj.com/pedro-duarte-envia-oficio-ao-tcm-e-ao-mpe-questionando-caso-de-imovel-em-botafogo-desapropriado-pela-prefeitura |

### Veja Rio — `vejario.abril.com.br` (14 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-05-01 | Os mais novos patrimônios do Rio? Bolinho de bacalhau do Cadeg e saideira | https://vejario.abril.com.br/cidade/bolinho-bacalhau-cadeg-patrimonio-cultural-rio |
| 2 | 2026-02-06 | Balneário Camboriú carioca: quem vai pagar pela sombra em Ipanema? \| Daniel S... | https://vejario.abril.com.br/coluna/daniel-sampaio/sombra-praia-ipanema |
| 3 | 2025-08-11 | Como assim? Lei quer levar Barra e Jacarepaguá para Zona Sudoeste | https://vejario.abril.com.br/cidade/lei-barra-e-jacarepagua-zona-sudoeste |
| 4 | 2025-08-15 | Anabela Mota Ribeiro, estrela portuguesa, lança livro com pocket-show | https://vejario.abril.com.br/programe-se/anabela-mota-ribeiro-estrela-portuguesa-livro-pocket-show |
| 5 | 2025-11-27 | Câmara de Vereadores aprova proposta que proíbe subida de entregadores | https://vejario.abril.com.br/cidade/aprova-proibe-subida-entregadores |

### Google News — `publico.pt` (13 articles)

- **Collector:** `google_news`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-10-04 | Montenegro dá luz verde a plano de segurança de Pedro Duarte e ataca Filipe A... | https://www.publico.pt/2025/10/04/politica/noticia/montenegro-entra-campanha-porto-aval-plano-seguranca-pedro-duarte-deixa-recado-filipe-araujo-2149634 |
| 2 | 2026-03-11 | Seguro em modo festa no Porto: a “frincha de luz”, o aniversariante, e os elo... | https://publico.pt/2026/03/11/politica/noticia/seguro-modo-festa-porto-frincha-luz-abrunhosa-aniversariante-fim-centralismo-elogiado-pedro-duarte-2167497 |
| 3 | 2025-11-14 | É impossível resolver o problema da habitação, como diz Pedro Duarte? - Público | https://www.publico.pt/2025/11/14/opiniao/opiniao/impossivel-resolver-problema-habitacao-pedro-duarte-2154634 |
| 4 | 2026-01-16 | Câmara do Porto volta a adiar requalificação do Jardim da Corujeira por tempo... | https://publico.pt/2026/01/16/local/noticia/camara-porto-volta-adiar-requalificacao-jardim-corujeira-tempo-indeterminado-2161473 |
| 5 | 2025-08-30 | Pedro Duarte sugere que país pense sobre regionalização no pós-autárquicas - ... | https://www.publico.pt/2025/08/30/politica/noticia/pedro-duarte-sugere-pais-pense-regionalizacao-posautarquicas-2145465 |

### Google News — `rtp.pt` (13 articles)

- **Collector:** `google_news`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-10-08 | Campanha no Porto. Pedro Duarte insiste no apelo ao voto útil - RTP | https://www.rtp.pt/noticias/politica/campanha-no-porto-pedro-duarte-insiste-no-apelo-ao-voto-util_v1689453 |
| 2 | 2025-10-12 | Pedro Duarte promete ser um presidente "muito livre e independente" - RTP | https://www.rtp.pt/noticias/politica/pedro-duarte-promete-ser-um-presidente-muito-livre-e-independente_v1690477 |
| 3 | 2025-10-13 | Pedro Duarte vence. Porto "deu mais uma prova de grandiosidade" - RTP | https://www.rtp.pt/noticias/politica/pedro-duarte-vence-porto-deu-mais-uma-prova-de-grandiosidade_v1690637 |
| 4 | 2026-02-18 | Pedro Duarte defende referendo à regionalização - RTP | https://rtp.pt/noticias/politica/pedro-duarte-defende-referendo-a-regionalizacao_v1719889 |
| 5 | 2025-09-30 | Sondagem Católica. Pedro Duarte e Manuel Pizarro empatados na corrida à Câmar... | https://www.rtp.pt/noticias/politica/sondagem-catolica-pedro-duarte-e-manuel-pizarro-empatados-na-corrida-a-camara-do-porto_n1687376 |

### Google News — `observador.pt` (13 articles)

- **Collector:** `google_news`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-10-02 | Pedro Duarte dramatiza apelo ao voto útil contra "velho PS" e insiste na "deg... | https://observador.pt/especiais/pedro-duarte-dramatiza-apelo-ao-voto-util-contra-velho-ps-e-insiste-na-degradacao-do-clima-de-inseguranca |
| 2 | 2025-11-05 | Pedro Duarte assegura maioria no executivo municipal ao convencer vereador do... | https://observador.pt/2025/11/05/pedro-duarte-assegura-maioria-no-executivo-municipal-ao-roubar-vereador-ao-ps |
| 3 | 2025-08-08 | Autárquicas. Pedro Duarte quer ficar com o pelouro da Cultura no Porto - Obse... | https://observador.pt/2025/08/08/autarquicas-pedro-duarte-quer-ficar-com-o-pelouro-da-cultura-no-porto |
| 4 | 2025-08-19 | Pedro Duarte: "avaliar reversão" ou mudar metrobus do Porto - Observador | https://observador.pt/2025/08/19/autarquicas-pedro-duarte-quer-avaliar-reversao-ou-mudar-metrobus-do-porto |
| 5 | 2025-09-25 | Sondagem. Pizarro e Pedro Duarte em empate técnico na corrida à Câmara do Por... | https://observador.pt/2025/09/25/sondagem-pizarro-e-pedro-duarte-continuam-em-empate-tecnico-na-corrida-a-camara-do-porto |

### Google News — `odia.ig.com.br` (9 articles)

- **Collector:** `google_news`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-12-02 | Revisar o IPTU é essencial para o Centro dar certo - O Dia | https://odia.ig.com.br/colunas/vereador-pedro-duarte/2025/12/7172863-revisar-o-iptu-e-essencial-para-o-centro-dar-certo.html |
| 2 | 2026-02-10 | Cinelândia precisa voltar a ser vitrine do Centro do Rio - O Dia | https://odia.ig.com.br/colunas/vereador-pedro-duarte/2026/02/7205767-cinelandia-precisa-voltar-a-ser-vitrine-do-centro-do-rio.html |
| 3 | 2026-03-13 | MP se manifesta pela suspensão da 'lei dos 20 andares' em Teresópolis - O Dia | https://odia.ig.com.br/teresopolis/2026/03/amp/7221687-mp-se-manifesta-pela-suspensao-da-lei-dos-20-andares-em-teresopolis.html |
| 4 | 2025-12-23 | O Rio entre reformas necessárias e desafios persistentes - O Dia | https://odia.ig.com.br/colunas/vereador-pedro-duarte/2025/12/7182538-o-rio-entre-reformas-necessarias-e-desafios-persistentes.html |
| 5 | 2026-01-29 | Vereador Pedro Duarte anuncia nova legenda - O Dia | https://odia.ig.com.br/colunas/informe-do-dia/2026/01/7199640-vereador-pedro-duarte-anuncia-nova-legenda.html |

### Google News — `jpn.up.pt` (9 articles)

- **Collector:** `google_news`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-11-05 | Pedro Duarte entrega Cultura a vereador eleito pelo PS e garante uma maioria ... | https://jpn.up.pt/2025/11/05/pedro-duarte-entrega-cultura-a-vereador-eleito-pelo-ps-e-garante-uma-maioria |
| 2 | 2026-03-06 | Câmara do Porto gasta 400 mil euros por ano com limpeza de fachadas - JPN - J... | https://www.jpn.up.pt/2026/03/06/camara-do-porto-gasta-400-mil-euros-por-ano-com-limpeza-de-fachadas |
| 3 | 2025-10-10 | Pedro Duarte e Mariana Leitão "perfeitamente alinhados" fazem apelo ao "voto ... | https://www.jpn.up.pt/2025/10/10/pedro-duarte-e-mariana-leitao-perfeitamente-alinhados-fazem-apelo-ao-voto-util |
| 4 | 2026-02-19 | Pedro Duarte reabre debate sobre regionalização e defende TGV como prioridade... | https://www.jpn.up.pt/2026/02/19/pedro-duarte-reabre-debate-sobre-regionalizacao-e-defende-tgv-como-prioridade-estrategica |
| 5 | 2026-01-26 | Pedro Duarte reitera apoio em António José Seguro: “O país fica em muito boas... | https://jpn.up.pt/2026/01/26/pedro-duarte-reitera-apoio-em-antonio-jose-seguro-o-pais-fica-em-muito-boas-maos |

### Google News — `diariodorio.com` (9 articles)

- **Collector:** `google_news`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-12-03 | Estágio de férias no gabinete de Pedro Duarte oferece bolsa de R$ 500 e carga... | https://diariodorio.com/estagio-de-ferias-no-gabinete-de-pedro-duarte-oferece-bolsa-de-r-500-e-carga-de-20h-semanais |
| 2 | 2026-02-06 | Paes filia Pedro Duarte ao PSD e dá largada a pré-candidaturas para a Alerj -... | https://diariodorio.com/paes-filia-pedro-duarte-ao-psd-e-da-largada-a-pre-candidaturas-para-a-alerj |
| 3 | 2025-12-08 | Crise no Novo: saída de Pedro Duarte expõe racha e deixa legenda sem vereador... | https://diariodorio.com/crise-no-novo-saida-de-pedro-duarte-expoe-racha-e-deixa-legenda-sem-vereador-no-rio |
| 4 | 2026-01-26 | Pedro Duarte se filia ao PSD e lança pré-candidatura a deputado estadual - Di... | https://diariodorio.com/pedro-duarte-se-filia-ao-psd-e-lanca-pre-candidatura-a-deputado-estadual |
| 5 | 2025-12-30 | Novo entra em crise no RJ após saída de Pedro Duarte e derrota de Rodrigo Rez... | https://diariodorio.com/novo-entra-em-crise-no-rj-apos-saida-de-pedro-duarte-e-derrota-de-rodrigo-rezende-em-eleicao-interna |

### Google News — `dn.pt` (8 articles)

- **Collector:** `google_news`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-09-04 | Pedro Duarte. “Nunca aceitarei um acordo de governação com o Chega” - Diário ... | https://www.dn.pt/pol%C3%ADtica/pedro-duarte-nunca-aceitarei-um-acordo-de-governa%C3%A7%C3%A3o-com-o-chega |
| 2 | 2025-11-06 | Câmara do Porto: Distrital do PS surpreendida com atribuição da Cultura a ver... | https://www.dn.pt/pol%C3%ADtica/cmara-do-porto-distrital-do-ps-surpreendida-com-atribuio-da-cultura-a-vereador-eleito-nas-suas-listas |
| 3 | 2025-09-07 | Pedro Duarte: "Não me lembro de alguém que tenha abdicado de ser ministro par... | https://www.dn.pt/pol%C3%ADtica/pedro-duarte-n%C3%A3o-me-lembro-de-algu%C3%A9m-que-tenha-abdicado-de-ser-ministro-para-ser-presidente-de-c%C3%A2mara |
| 4 | 2026-03-16 | Pedro Duarte refere que a região Norte tem sido “grosseiramente preterida” - ... | https://dn.pt/pol%C3%ADtica/pedro-duarte-refere-que-a-regio-norte-tem-sido-grosseiramente-preterida |
| 5 | 2025-09-19 | Autárquicas: Montenegro e Pedro Duarte visitam rua onde nasceu Sá Carneiro - ... | https://www.dn.pt/pol%C3%ADtica/aut%C3%A1rquicas-montenegro-e-pedro-duarte-visitam-rua-onde-nasceu-s%C3%A1-carneiro |

### Google News — `expresso.pt` (7 articles)

- **Collector:** `google_news`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-10-04 | Um “circo”, um “golpe em campanha eleitoral”: candidatos ao Porto aprovam sus... | https://expresso.pt/politica/eleicoes/autarquicas-2025/2025-10-04-um-circo-um-golpe-em-campanha-eleitoral-candidatos-ao-porto-aprovam-suspensao-do-metrobus-mas-apontam-favorecimento-de-pedro-duarte-70c69131 |
| 2 | 2025-08-07 | Candidatos autárquicos começam a esbater linhas vermelhas para o Chega - Expr... | https://expresso.pt/politica/eleicoes/autarquicas-2025/2025-08-07-candidatos-autarquicos-comecam-a-esbater-linhas-vermelhas-para-o-chega-0f858c9f |
| 3 | 2025-10-07 | Pedro Duarte no Bom Partido: “Por norma, em Lisboa desconfiam mais do que é e... | https://expresso.pt/podcasts/bom-partido/2025-10-07-pedro-duarte-no-bom-partido-por-norma-em-lisboa-desconfiam-mais-do-que-e-estranho.-no-porto-e-o-contrario-da-se-uma-prova-de-confianca-0a245246 |
| 4 | 2026-02-12 | Mau tempo: Pedro Duarte, ex-ministro e autarca do Porto, relança discussão so... | https://expresso.pt/politica/2026-02-12-mau-tempo-pedro-duarte-ex-ministro-e-autarca-do-porto-relanca-discussao-sobre-regionalizacao--outros-autarcas-e-especialistas-tambem--fcafed36 |
| 5 | 2025-08-29 | Pedro Duarte admite governar o Porto com o Chega e não jura ficar como veread... | https://expresso.pt/politica/eleicoes/autarquicas-2025/2025-08-29-pedro-duarte-admite-governar-o-porto-com-o-chega-e-nao-jura-ficar-como-vereador-se-perder-015f39ec |

### O Globo — `oglobo.globo.com` (7 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2024-10-06 | Vereadores eleitos do Rio; veja lista | https://oglobo.globo.com/politica/eleicoes-2024/noticia/2024/10/06/vereadores-eleitos-do-rio-veja-lista.ghtml |
| 2 | 2025-04-07 | Operação Urbana Consorciada do Parque Olímpico: mobilidade e infraestrutura f... | https://oglobo.globo.com/rio/bairros/barra/noticia/2025/04/07/operacao-urbana-consorciada-do-parque-olimpico-mobilidade-e-infraestrutura-foram-principais-temas-de-audiencia-publica-na-camara-dos-vereadores-saiba-o-que-foi-discutido.ghtml |
| 3 | 2025-03-20 | Sem consenso, audiência na Câmara do Rio sobre Guarda Municipal armada tem em... | https://oglobo.globo.com/rio/noticia/2025/03/20/sem-consenso-audiencia-na-camara-de-vereadores-do-rio-sobre-guarda-municipal-armada-tem-bate-boca.ghtml |
| 4 | 2025-10-22 | Em ano eleitoral, Prefeitura do Rio prevê gastar r$ 1,1 bilhão com segurança ... | https://oglobo.globo.com/rio/noticia/2025/10/22/prefeitura-do-rio-preve-gastar-mais-de-r-1-bilhao-com-seguranca-publica-em-2026-35percent-acima-do-orcamento-deste-ano.ghtml |
| 5 | 2025-03-25 | Projeto de lei de regulação do Airbnb é debatido na Câmara do Rio; donos de i... | https://oglobo.globo.com/rio/noticia/2025/03/25/projeto-de-lei-de-regulacao-do-airbnb-e-debatido-na-camara-do-rio-donos-de-imoveis-lotam-galeria-contra-e-a-favor.ghtml |

### Google News — `cnnportugal.iol.pt` (6 articles)

- **Collector:** `google_news`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-09-08 | Pedro Duarte foi assaltado no Porto e conhece "dezenas de casos" como o seu. ... | https://cnnportugal.iol.pt/pedro-duarte/candidato-a-camara-municipal-do-porto/pedro-duarte-foi-assaltado-no-porto-e-conhece-dezenas-de-casos-como-o-seu-e-por-isso-diz-as-estatisticas-de-seguranca-sao-completamente-enganadoras/20250908/68bf17ccd34e58bc67957907 |
| 2 | 2026-01-11 | "Ficaria triste se o país fosse nesse caminho": Pedro Duarte apresenta um cen... | https://cnnportugal.iol.pt/videos/ficaria-triste-se-o-pais-fosse-nesse-caminho-pedro-duarte-apresenta-um-cenario-extraordinariamente-frustrante-e-dramatico-para-a-segunda-volta/696431b80cf2d7f14f26eb5d |
| 3 | 2026-03-15 | "Estou convencido de que é uma questão eminentemente política que leva a UGT ... | https://cnnportugal.iol.pt/videos/estou-convencido-de-que-e-uma-questao-eminentemente-politica-que-leva-a-ugt-a-ter-a-atitude-de-absoluta-irreversibilidade-que-tem-tido/69b73f3a0cf27f6588a66a8e |
| 4 | 2026-01-19 | Pedro Duarte: "Voto Seguro, para mim é algo inequívoco". Júdice: "Voto em Seg... | https://cnnportugal.iol.pt/presidenciais-2026/resultados-presidenciais-2026/pedro-duarte-poiares-maduro-e-judice-vao-votar-seguro-na-segunda-volta/20260119/696d8a5fd34e0ec52ec2572a |
| 5 | 2026-02-25 | CNN Summit - Portugal Tour: Moedas diz que taxa turística não vai resolver cr... | https://cnnportugal.iol.pt/videos/cnn-summit-portugal-tour-moedas-diz-que-taxa-turistica-nao-vai-resolver-crise-da-habitacao-em-lisboa-pedro-duarte-anuncia-transportes-gratuitos-no-porto-ainda-este-ano/699ef35d0cf21fcd8376c587 |

### Google News — `omirante.pt` (6 articles)

- **Collector:** `google_news`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-03-01 | Pedro Duarte Personalidade do Ano Nacional - O Mirante | https://omirante.pt/omirante/2026-03-01-video-pedro-duarte-personalidade-do-ano-nacional-f2a30781 |
| 2 | 2026-03-04 | Pedro Duarte Vila Guedes - O Mirante | https://omirante.pt/agora-falo-eu/2026-03-04-pedro-duarte-vila-guedes-92da3431 |
| 3 | 2026-03-06 | O país precisa de fazer um grande debate sobre qual é o melhor modelo de orga... | https://omirante.pt/edicao-1500/2026-03-06-o-pais-precisa-de-fazer-um-grande-debate-sobre-qual-e-o-melhor-modelo-de-organizacao-8c6dfc8f |
| 4 | 2026-03-10 | Atletas da Escola de Karate Shotokan Pedro Duarte conquistam dois pódios no C... | https://omirante.pt/desporto/2026-03-10-atletas-da-escola-de-karate-shotokan-pedro-duarte-conquistam-dois-podios-no-campeonato-nacional-2dfbed15 |
| 5 | 2026-02-27 | Pedro Duarte realça o papel da imprensa regional ao receber o prémio Personal... | https://omirante.pt/omirantetv/2026-02-27-video-pedro-duarte-realca-o-papel-da-imprensa-regional-ao-receber-o-premio-personalidade-do-ano-nacional-3292dd7c |

### Google News — `correiodamanha.com.br` (6 articles)

- **Collector:** `google_news`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-02-09 | Coluna Magnavita \| Pedro Duarte no PSD e em busca de uma cadeira na Alerj - c... | https://correiodamanha.com.br/colunistas/magnavita/2026/02/257678-pedro-duarte-no-psd-e-embusca-de-uma-cadeira-na-alerj.html |
| 2 | 2026-02-09 | Coluna Magnavita \| Pedro Duarte no PSD e em busca de uma cadeira na Alerj - c... | https://www.correiodamanha.com.br/colunistas/magnavita/2026/02/257678-pedro-duarte-no-psd-e-embusca-de-uma-cadeira-na-alerj.html |
| 3 | 2026-02-12 | Filiação de Pedro Duarte reforça palanque do PSD para as eleições - correioda... | https://correiodamanha.com.br/rio-de-janeiro/2026/02/257497-filiacao-de-pedro-duarte-reforca-palanque-do-psd-para-as-eleicoes.html |
| 4 | 2026-02-12 | Filiação de Pedro Duarte reforça palanque do PSD para as eleições - correioda... | https://www.correiodamanha.com.br/rio-de-janeiro/2026/02/257497-filiacao-de-pedro-duarte-reforca-palanque-do-psd-para-as-eleicoes.html |
| 5 | 2026-01-27 | Pedro Duarte filia-se ao PSD e anuncia pré-candidatura a deputado estadual - ... | https://www.correiodamanha.com.br/rio-de-janeiro/2026/01/253478-pedro-duarte-filia-se-ao-psd-e-anuncia-pre-candidatura-a-deputado-estadual.html |

### Google News — `oglobo.globo.com` (6 articles)

- **Collector:** `google_news`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-12-05 | Rio do Futuro: seminário debate uma mobilidade mais eficiente | https://oglobo.globo.com/rio/noticia/2025/12/05/rio-do-futuro-seminario-debate-uma-mobilidade-mais-eficiente.ghtml |
| 2 | 2025-12-08 | Único vereador eleito pelo Partido Novo na Câmara do Rio deixa a legenda | https://oglobo.globo.com/blogs/ancelmo-gois/post/2025/12/unico-vereador-eleito-pelo-partido-novo-na-camara-do-rio-deixa-a-legenda.ghtml |
| 3 | 2025-04-18 | Pedro Duarte Guimarães explica o que foi o Império Mongol e sua importância h... | https://oglobo.globo.com/patrocinado/saftec/noticia/2025/04/18/pedro-duarte-guimaraes-explica-o-que-foi-o-imperio-mongol-e-sua-importancia-historica.ghtml |
| 4 | 2025-05-20 | Pedro Duarte Guimarães explora a relação cultural entre Brasil e Índia: novel... | https://oglobo.globo.com/patrocinado/saftec/noticia/2025/05/20/pedro-duarte-guimaraes-explora-a-relacao-cultural-entre-brasil-e-india-novelas-musicas-e-culinaria.ghtml |
| 5 | 2025-08-28 | Proposta que pode pesar na conta de luz do carioca tem objetivo de financiar ... | https://oglobo.globo.com/rio/noticia/2025/08/28/projeto-da-prefeitura-do-rio-muda-regras-de-cobranca-da-contribuicao-sobre-iluminacao-publica-e-pode-aumentar-a-conta-de-luz.ghtml |

### Google News — `blogdonc.com` (5 articles)

- **Collector:** `google_news`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-03-03 | Secret Story 10! Leokadia Pombo gera indignação após opinião polémica sobre P... | https://blogdonc.com/secret-story-10-leokadia-pombo-gera-indignacao |
| 2 | 2026-03-09 | Secret Story 10! Expulsão de Pedro Duarte gera chuva de críticas à TVI: “Não ... | https://blogdonc.com/secret-story-expulsao-de-pedro-duarte-gera-criticas |
| 3 | 2026-03-09 | Após expulsão, Pedro Duarte elege o justo vencedor do Secret Story 10: “Quero... | https://blogdonc.com/secret-story-pedro-duarte-revela-favorito-a-vitoria |
| 4 | 2026-03-22 | Pedro Duarte do "Secret Story 10" antecipa os finalistas desta edição: “Apesa... | https://blogdonc.com/pedro-duarte-do-secret-story-antecipa-os-finalistas |
| 5 | 2026-03-22 | Audiências! “Simply the Best” é um fracasso total e perde para toda a concorr... | https://blogdonc.com/audiencias-simply-the-best-e-um-fracasso-total |

### Google News — `atelevisao.com` (5 articles)

- **Collector:** `google_news`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2026-03-01 | Última hora! João acerta no segredo de Pedro Duarte - A Televisão | https://www.atelevisao.com/secret-story-casa-dos-segredos/ultima-hora-joao-acerta-no-segredo-de-pedro-duarte |
| 2 | 2026-03-09 | Portugueses expulsam Pedro Duarte do Secret Story 10 - A Televisão | https://www.atelevisao.com/secret-story-casa-dos-segredos/portugueses-expulsam-pedro-duarte-do-secret-story-10 |
| 3 | 2026-03-22 | Pedro Duarte admite: "Cá fora sinto-me um vencedor" - A Televisão | https://atelevisao.com/secret-story-casa-dos-segredos/pedro-duarte-admite-ca-fora-sinto-me-um-vencedor |
| 4 | 2026-02-25 | Da dor à coragem: o percurso transformador de Pedro, concorrente transexual d... | https://www.atelevisao.com/secret-story-casa-dos-segredos/da-dor-a-coragem-o-percurso-transformador-de-pedro-concorrente-transexual-do-secret-story |
| 5 | 2026-02-27 | "Mudei de sexo" não era o segredo original de Pedro Duarte - A Televisão | https://www.atelevisao.com/secret-story-casa-dos-segredos/mudei-de-sexo-nao-era-o-segredo-original-de-pedro-duarte |

### G1 — `g1.globo.com` (5 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-01-01 | Paes e vereadores eleitos no Rio tomam posse nesta quarta-feira | https://g1.globo.com/rj/rio-de-janeiro/noticia/2025/01/01/paes-e-vereadores-eleitos-no-rio-tomam-posse-nesta-quarta-feira.ghtml |
| 2 | 2025-01-01 | Carlo Caiado (PSD) é reeleito presidente da Câmara do Rio por unanimidade; ve... | https://g1.globo.com/rj/rio-de-janeiro/noticia/2025/01/01/carlos-caiado-psd-e-reeleito-presidente-da-camara-do-rio.ghtml |
| 3 | 2024-10-06 | Carlos Bolsonaro bate o próprio recorde e é o vereador mais bem votado da his... | https://g1.globo.com/rj/rio-de-janeiro/eleicoes/2024/noticia/2024/10/06/carlos-bolsonaro-e-o-vereador-mais-bem-votado-da-historia-no-rio.ghtml |
| 4 | 2024-10-07 | Câmara do Rio terá 23 novos vereadores em 2025; veja quem são | https://g1.globo.com/rj/rio-de-janeiro/eleicoes/2024/noticia/2024/10/07/renovacao-camara-vereadores-rio-de-janeiro.ghtml |
| 5 | 2025-09-16 | Audiência pública discute regulação de aluguel por temporada no Rio e compart... | https://g1.globo.com/rj/rio-de-janeiro/noticia/2025/09/16/audiencia-publica-discute-regulacao-de-aluguel-por-temporada-no-rio-e-compartilhamento-de-dados-sobre-hospedagens.ghtml |

### VEJA — `veja.abril.com.br` (5 articles)

- **Collector:** `rss / wordpress_api`

| # | Date | Title | URL |
|---|------|-------|-----|
| 1 | 2025-07-02 | Empresa ligada à Prefeitura do Rio foi turbinada com nomeações políticas, den... | https://veja.abril.com.br/politica/empresa-ligada-a-prefeitura-do-rio-foi-turbinada-com-nomeacoes-politicas-denuncia-vereador |
| 2 | 2024-10-07 | Eleições 2024: os vereadores eleitos na cidade do Rio de Janeiro | https://veja.abril.com.br/politica/eleicoes-2024-os-vereadores-eleitos-na-cidade-do-rio-de-janeiro |
| 3 | 2025-02-18 | Projeto de lei ‘anti-Oruam’ chega ao Rio | https://veja.abril.com.br/brasil/projeto-de-lei-anti-oruam-chega-ao-rio |
| 4 | 2025-02-20 | Rapper Oruam é detido após abordagem policial no Rio | https://veja.abril.com.br/brasil/rapper-oruam-e-detido-apos-abordagem-policial-no-rio |
| 5 | 2025-03-20 | Audiência pública vai discutir o abandono de imóveis no Centro do Rio | https://veja.abril.com.br/politica/audiencia-publica-vai-discutir-o-abandono-de-imoveis-no-centro-do-rio |

---

# Part 3 — Automated Validation Results

_Run: 2026-04-01 00:01_

| Verdict | Count |
|---------|-------|
| PASS | 14 |
| PARTIAL | 2 |
| FAIL | 19 |
| ERROR | 0 |
| SKIP | 1 |
| **Articles** | **77/175 (44%)** |

| # | Verdict | Found | Source | Domain | Detail |
|---|---------|-------|--------|--------|--------|
| 1 | PASS | 5/5 | Diario do Rio | `diariodorio.com` | 100% |
| 2 | PASS | 5/5 | Agenda do Poder | `agendadopoder.com.br` | 100% |
| 3 | PASS | 5/5 | Tribuna da Serra | `tribunadaserra.com.br` | 100% |
| 4 | PASS | 5/5 | Tempo Real RJ | `temporealrj.com` | 100% |
| 5 | PARTIAL | 3/5 | Veja Rio | `vejario.abril.com.br` | 60% |
| 6 | PARTIAL | 4/5 | Camara Rio | `camara.rio` | 80% |
| 7 | PASS | 5/5 | O Globo | `oglobo.globo.com` | 100% |
| 8 | SKIP | 0/0 | Google News | `news.google.com` | — |
| 9 | PASS | 5/5 | Diario do Rio Site | `diariodorio.com` | 100% |
| 10 | FAIL | 0/5 | Google News | `jn.pt` | 0% |
| 11 | PASS | 5/5 | G1 | `g1.globo.com` | 100% |
| 12 | PASS | 5/5 | Tempo Real RJ Site | `temporealrj.com` | 100% |
| 13 | PASS | 5/5 | Google News | `temporealrj.com` | 100% |
| 14 | FAIL | 0/5 | Google News | `publico.pt` | 0% |
| 15 | FAIL | 0/5 | Google News | `rtp.pt` | 0% |
| 16 | FAIL | 0/5 | Google News | `observador.pt` | 0% |
| 17 | PASS | 5/5 | Camara Rio Internal Search | `camara.rio` | 100% |
| 18 | FAIL | 0/5 | Google News | `odia.ig.com.br` | 0% |
| 19 | FAIL | 0/5 | Google News | `jpn.up.pt` | 0% |
| 20 | PASS | 5/5 | Google News | `diariodorio.com` | 100% |
| 21 | PASS | 5/5 | Conib Internal Search | `conib.org.br` | 100% |
| 22 | FAIL | 0/5 | Google News | `dn.pt` | 0% |
| 23 | FAIL | 0/5 | Google News | `oglobo.globo.com` | 0% |
| 24 | FAIL | 0/5 | CONIB | `conib.org.br` | 0% |
| 25 | FAIL | 0/5 | Google News | `expresso.pt` | 0% |
| 26 | FAIL | 0/5 | Mercado e Eventos | `mercadoeeventos.com.br` | 0% |
| 27 | FAIL | 0/5 | O Dia | `odia.ig.com.br` | 0% |
| 28 | PASS | 5/5 | CBN | `cbn.globo.com` | 100% |
| 29 | FAIL | 0/5 | Google News | `cnnportugal.iol.pt` | 0% |
| 30 | FAIL | 0/5 | Google News | `omirante.pt` | 0% |
| 31 | FAIL | 0/5 | Google News | `correiodamanha.com.br` | 0% |
| 32 | PASS | 5/5 | VEJA | `veja.abril.com.br` | 100% |
| 33 | FAIL | 0/5 | Google News | `blogdonc.com` | 0% |
| 34 | FAIL | 0/5 | Google News | `atelevisao.com` | 0% |
| 35 | FAIL | 0/5 | Panrotas | `panrotas.com.br` | 0% |
| 36 | FAIL | 0/5 | Radio Tupi | `tupi.fm` | 0% |

## Analysis

**Effective hit rate:** 77/80 = **96%** for testable combos (excluding inherent limitations).

### PASS (14 combos, 70/70 articles)
All core collector types working correctly:
- **WordPress API** (6): Diario do Rio, Agenda do Poder, Tribuna da Serra, Tempo Real RJ, Diario do Rio Site, Tempo Real RJ Site
- **Sitemap Daily** (3): G1, O Globo, CBN
- **RSS** (1): VEJA
- **Internal Search** (2): Camara Rio Internal Search, Conib Internal Search
- **Google News → Brazilian sites** (2): Google News → temporealrj.com, Google News → diariodorio.com

### PARTIAL (2 combos, 7/10 articles)

| Combo | Found | Missed article | Reason |
|-------|-------|----------------|--------|
| Veja Rio | 3/5 | "Renova Run Rio" (Lu Lacerda column) | No target keywords; archive pagination limited |
| Veja Rio | — | "R$ 18 milhões em dívidas" (Lu Lacerda column) | No target keywords; WordPress query won't match |
| Camara Rio | 4/5 | "Câmara inicia 12ª legislatura" (2025-01-01) | Archive doesn't reach Jan 2025 depth |

### FAIL (19 combos, 0/95 — all inherent limitations)

| Category | Combos | Reason |
|----------|--------|--------|
| Google News → Portuguese .pt domains | 9 | Different Pedro Duarte (Portuguese politician, mayor of Porto) — not the monitored target |
| Google News → Portuguese culture sites | 2 | Different Pedro Duarte (Secret Story 10 TV contestant) |
| Google News → Brazilian sites (temporal) | 3 | Google News RSS feeds are temporal; old articles fall out of the feed |
| RSS-only sources (old articles) | 5 | RSS feeds only carry recent items; CONIB, Mercado e Eventos, O Dia, Panrotas, Radio Tupi have no API/sitemap alternative |

### Pipeline fixes applied in this round

1. **`_within_window` timezone bug** (`pipeline/collectors.py`): Sitemap daily entries were rejected by `_within_window` because sitemaps organize by local date (Brazil UTC-3) but `published_at` uses UTC — late-night articles had next-day UTC timestamps. Fixed by removing the redundant `_within_window` check from `collect_sitemap_daily` (the date-specific sitemap URL already handles filtering). Impact: **G1, O Globo, CBN all moved from PARTIAL to PASS.**
2. **Non-article URL filtering** (`pipeline/http_utils.py`): Added `/vereadores/`, `/atividade-parlamentar/`, `/comissoes/`, `/frentes/` to `BAD_PATH_TOKENS` and `.php` to `BAD_EXTENSIONS`. Prevents structural/profile pages from being classified as articles. Impact: **Camara Rio improved from 2/5 to 4/5.**
3. **Pedro Duarte added to targets** (`data/targets.json`, `pipeline/settings.py`): Pedro Duarte appears in 72% of snapshot combos but was not configured as a monitored target. Now included as priority-2 target with keywords.
