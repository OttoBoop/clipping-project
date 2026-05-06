# Análise Individual — Show da Shakira

> Documento cumulativo de análise por artigo, conforme a Etapa 1 de
> `Show da Shakira/workflow-classificacao-shakira.md`.
>
> **Cada bloco abaixo corresponde a um artigo. ID no formato `a-{articleId}`,
> bate com o ID interno do snapshot `assets/clipping-data.json` e com a chave
> `article-{articleId}` em `assets/clipping-raw-texts.json`.**

## Status do loop

- **Persona ativa:** Penelope (`md documents/PENELOPE_CHARACTER_SHEET.md`).
- **Plano de execução:** `Show da Shakira/workflow-classificacao-shakira.md`,
  Etapa 1.
- **Fonte de dados ativa:** `tools/penelope-fetched/assets_clipping-data.json`
  + `assets_clipping-raw-texts.json`, baixados pelo workflow GitHub Actions
  `penelope-fetch-shakira.yml` em 2026-05-06 15:11 UTC, com `meta.generatedAt
  = 06/05/2026 00:03 UTC`. Foi como Penélope contornou o egress block do
  sandbox para `*.onrender.com` — ver §5 do canal vivo, run 8 do workflow.
- **Total real de artigos a analisar:** 243 (220 strict-tag + 23 indiretos
  via story-tag ou mention-em-texto). Otávio estimou 119 — esse é o número
  de **stories** (`stories[*]` com `'shakira' in targetKeys`); **artigos
  individuais** dentro dessas stories são 220 strict + alguns indiretos.
- **Artigos já concluídos:** 3 (a-116, a-633, a-325) — feitos antes do
  unblock do egress. Usaram dados do snapshot estático stale (13/04/2026).
  Resumos podem precisar de revisita se houver versões atualizadas no
  snapshot novo (mesma URL, mas o pipeline pode ter re-ingerido com mais
  contexto).
- **Restantes:** 240. Processar em ordem cronológica via
  `python3 tools/penelope_shakira_iter.py todo`.

---

## a-116 — Show de Shakira em Praia de Copacabana impulsiona turismo latino em 2026, diz Mais Brasil Viagens

**Fonte:** Mercado e Eventos (mercadoeeventos.com.br) — captado via Google News
**Data:** 13/02/2026
**URL:** https://www.mercadoeeventos.com.br/noticias/parques-e-atracoes/show-de-shakira-em-praia-de-copacabana-impulsiona-turismo-latino-em-2026-diz-mais-brasil-viagens

> **Nota de duplicata:** o mesmo URL aparece também sob `a-633` no banco
> (re-ingerido com `sourceName="Mercado e Eventos"` direto, sem o
> intermediador `"Google News"` do `a-116`). Análise única vale para os dois
> IDs.

### Resumo Narrativo

O artigo enquadra a confirmação do show de Shakira no Rio de Janeiro — marcado
para 2 de maio de 2026 dentro do projeto "Todo Mundo no Rio", na orla de
Copacabana — como vetor de turismo internacional, especialmente latino-
americano. O texto centra-se na fala do CEO da operadora Mais Brasil Viagens,
Flávio Valle, que posiciona a apresentação de uma artista latina em
Copacabana como continuidade do "protagonismo cultural" da região e como
oportunidade de receptivo qualificado para visitantes da Argentina, Chile,
Paraguai, Uruguai e Bolívia. A operadora cita o histórico de ter
recepcionado cerca de 500 passageiros para uma apresentação anterior da
artista no Brasil e prepara operação semelhante para um show de Bad Bunny
no Allianz Parque em fevereiro, com hospedagem premium e ambientação
temática.

A história é apresentada em chave celebratória e de oportunidade: o show é
descrito como mais uma atração internacional (em sequência a Madonna e Lady
Gaga) trazida pela Bonus Track com apoio da prefeitura, e como motor de
"crescimento imediato" na chegada de grupos organizados sul-americanos. Não
há contraponto crítico, menção a infraestrutura, segurança, mobilidade ou
custos públicos — o ângulo é estritamente positivo, focado em fluxo
turístico e posicionamento do Brasil como destino regional de entretenimento.
O peso do artigo recai sobre a Mais Brasil Viagens e seu CEO; o show de
Shakira funciona como gancho de notícia, não como objeto principal.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Turismo internacional / receptivo latino-americano | Apresentado como benefício direto e quantificável (~500 passageiros recepcionados em show anterior) trazido pela vinda da artista. | muito positivo |
| Posicionamento do Rio como destino cultural/musical | Destaca a sequência Madonna → Lady Gaga → Shakira na orla carioca como sinal de protagonismo da cidade no calendário internacional. | positivo |
| Identificação cultural latina como motor de viagem | Argumentação do CEO Flávio Valle de que a presença de artista latina (Shakira, Bad Bunny) gera deslocamento turístico regional. | positivo |
| Parceria público-privada (prefeitura + Bonus Track) | Mencionada de passagem como organizadora do evento; tratamento neutro-positivo, sem detalhamento. | positivo |
| Mercados emissores sul-americanos (AR/CL/PY/UY/BO) | Tratados como em expansão; o show é descrito como acelerador desse crescimento. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-633 — (Mesmo artigo de a-116 sob registro de fonte distinto)

**Fonte:** Mercado e Eventos (mercadoeeventos.com.br) — captado direto pela RSS/feed do veículo, sem `Google News` como source intermediário
**Data:** 13/02/2026
**URL:** https://mercadoeeventos.com.br/noticias/parques-e-atracoes/show-de-shakira-em-praia-de-copacabana-impulsiona-turismo-latino-em-2026-diz-mais-brasil-viagens

### Resumo Narrativo

Duplicata por URL do artigo `a-116` (uma única notícia ingerida duas vezes
pelo pipeline: uma via Google News e outra via coleta direta do veículo,
diferindo apenas na barra final do URL e em `sourceName`). O texto bruto
em `clipping-raw-texts.json["article-633"]` é byte-a-byte idêntico ao de
`article-116`. Ver bloco de `a-116` acima para a análise narrativa e
temática completa.

### Temas Identificados

Idêntico a `a-116`. Não repetido aqui.

### Classificação Geral

**Sentimento geral do artigo:** muito positivo
**Observação operacional:** este bloco é mantido para honrar o protocolo de
Etapa 1 ("não pular o artigo silenciosamente"), mas é uma **duplicata
estrutural** que provavelmente seria deduplicada por URL na Etapa 2
(`consolidacao-temas.md`). Recomendação para a próxima Penelope: aplicar
dedup `(url canonicalizada)` antes de contagem temática.

---

## a-325 — Barra da Tijuca se consolida como destino preferido dos latinos no Rio

**Fonte:** Diário do Rio (diariodorio.com) — captado via Google News
**Data:** 10/02/2025 17:13 UTC
**URL:** https://diariodorio.com/barra-da-tijuca-se-consolida-como-destino-preferido-dos-latinos-no-rio

### Resumo Narrativo

O artigo cobre o crescimento de 26,8% no turismo internacional do Rio em
2024 e o avanço da Barra da Tijuca como bairro preferido por turistas
sul-americanos (Argentina, Chile, Uruguai, Paraguai, Bolívia). A peça é
estruturada em torno de tarifas hoteleiras mais baixas na Barra,
infraestrutura moderna, proximidade do Riocentro e da feira FIT
Latinoamérica, e o testemunho da Mais Brasil Viagens de Flávio Valle, que
recepciona quase 500 turistas latinos para um show de Shakira no Estádio
Nilton Santos em 11 de fevereiro de 2025.

A menção ao show da Shakira aparece como exemplo de evento que catalisa
chegada de turistas — não como objeto central. O artigo é predominantemente
sobre o ecossistema hoteleiro da Barra, não sobre o show. A apresentação de
Shakira mencionada aqui é a do **Engenhão em fevereiro de 2025**, distinta
do show de Copacabana de **2 de maio de 2026** que é o foco da mission
Shakira definida em `md documents/05-05-26-Iris-Shakira goals.md` (período
01/04/2026 a 05/05/2026).

Por dois motivos — (a) a notícia trata principalmente de turismo
hoteleiro, não do show; (b) a apresentação citada é de 2025, anterior à
janela da mission — este artigo está **fora do escopo estrito** da análise
do show de 2026. Mantido no documento por aderência ao protocolo do plano
("não pular o artigo silenciosamente") e por contexto histórico útil
(mostra que Flávio Valle e a Mais Brasil Viagens já tinham padrão
estabelecido de receptivo de turistas latinos para shows da Shakira no Rio
um ano antes, o que ajuda a contextualizar `a-116`).

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Show da Shakira (2025, Estádio Nilton Santos) | Citado como exemplo de evento que mobiliza receptivo turístico — não é o objeto da matéria. | positivo |
| Crescimento do turismo internacional no Rio (2024) | Apresentado com dados oficiais SETUR/RJ; tom celebratório. | muito positivo |
| Barra da Tijuca como destino latino preferido | Tratamento positivo extenso, com dados de hotéis (room nights +113%), ofertas mais acessíveis. | muito positivo |
| Atuação da Mais Brasil Viagens / Flávio Valle | Posicionado como especialista de receptivo latino-americano, com operação ativa em torno de eventos. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo estrito**: trata de turismo hoteleiro carioca; o show de Shakira é apenas um exemplo periférico, e a apresentação citada é a de 2025 (Engenhão), não a de 2026 (Copacabana) que é o foco da mission. Bloco mantido por integridade do protocolo da Etapa 1.

---

---

## a-241 — Dove se torna patrocinadora do Todo Mundo no Rio, que terá show da Shakira

**Fonte:** O Globo Sitemap (oglobo.globo.com)
**Data:** 01/04/2026 09:00 UTC
**URL:** https://oglobo.globo.com/blogs/capital/post/2026/04/dove-se-torna-patrocinadora-do-todo-mundo-no-rio-que-tera-show-da-shakira.ghtml

### Resumo Narrativo

O Globo (coluna Capital, Rennan Setti) anuncia que a Dove, marca de higiene
pessoal da Unilever, entrou para o rol de patrocinadores do "Todo Mundo no
Rio" que organizará o show gratuito de Shakira em Copacabana em maio. O
texto detalha a campanha "#LobasVãoDeDove", criada pela DAVID em parceria
com BR Media Group, Tastemakers Brasil e Initiative Brasil, com ativações
in loco, distribuição de brindes, mídia OOH e frentes com influenciadores.
A executiva Mariana Krause, gerente de marketing de desodorantes, justifica
o ângulo conectando o antitranspirante aerossol ao público feminino do
festival — "em meio a coreografias, refrões em coro e momentos de euforia
coletiva, levantar os braços é inevitável", explica. A matéria também cita
pesquisa proprietária Dove segundo a qual 61% das brasileiras já deixaram
de levantar os braços por vergonha das axilas. Outros patrocinadores
listados: Corona (apresentadora), Santander, Latam, C&A, 99, Beats, Deezer.

O ângulo é estritamente comercial-publicitário: o show é tratado como
plataforma de marca, sem comentários sobre a artista, infraestrutura
pública ou impacto cidadão. O fandom "lobas" aparece como categoria de
consumidor. Tom positivo de "diversificação de portfólio" para a Dove.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Patrocínio comercial / branding ao redor do show | Apresentado como aposta estratégica de marca em festivais musicais; lista expansiva de patrocinadores (Dove, Corona, Santander, Latam, C&A, 99, Beats, Deezer). | positivo |
| Conexão público feminino × marca via fandom Shakira ("lobas") | Argumentado pela executiva Dove como ativação natural; pesquisa apoia o ângulo. | positivo |
| Show de Shakira como evento de massa | Mencionado como contexto; não detalhado. | neutro |
| Bonus Track / produção do Todo Mundo no Rio | Mencionada como organizadora; sem juízo. | neutro |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-237 — A um mês do megashow de Shakira, Rio aguarda 'invasão latina' com disparada de voos e reservas

**Fonte:** G1 (g1.globo.com)
**Data:** 02/04/2026 12:08 UTC
**URL:** https://g1.globo.com/rj/rio-de-janeiro/musica/show-shakira-rj/noticia/2026/04/02/a-um-mes-do-megashow-de-shakira-rio-aguarda-invasao-latina-com-disparada-de-voos-e-reservas.ghtml

### Resumo Narrativo

A reportagem do G1, assinada por Ana Paula Jaume, apresenta o show de
Shakira como motor de "invasão latina" no Rio: dados da Embratur indicam
que o número de colombianos que virão à cidade quase quadruplica em
relação a 2025 — o maior aumento registrado. Cerca de 8.500 passagens
aéreas internacionais foram reservadas para o período do evento, 80% a
mais que para o show de Madonna em 2024. A Latam aumentou em 22% o número
de voos em comparação com 2025 (ano de Lady Gaga), com origem
principalmente em Lima, Santiago e Buenos Aires. As buscas por hospedagem
para 1–3 de maio cresceram 34% na Booking após a confirmação do show.

A peça humaniza o fenômeno com três entrevistados: Gustavo Mayaute, fã
peruano que estima gastar US$ 3.500–4.000 (≈ R$ 20 mil) por pessoa;
Manuel Navarro, fã chileno que viaja em grupo de quase 20 pessoas; e
Welisom Myers, fã brasileiro de Guaratinguetá que reencontrará amiga
conhecida em show anterior. A diretora da Associação Brasileira de
Agências de Viagens, Cristina Fritsch, contextualiza como "onda latina"
puxada por artistas como Bad Bunny — turismo conectado à identidade
cultural, não apenas consumo de entretenimento. A expectativa final é
"repetir o sucesso de Madonna e Lady Gaga e reunir 2 milhões de pessoas".

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Turismo internacional / "invasão latina" | Boom quantificado (4× colombianos, 8.500 reservas, 80% mais que Madonna). Tom celebratório. | muito positivo |
| Aumento de oferta de voos (Latam +22%) | Apresentado como resposta à demanda; positivo para conectividade Brasil–América Latina. | positivo |
| Hospedagem / Booking (+34% buscas) | Sinal de demanda forte. | positivo |
| Identificação cultural latina como vetor turístico | Contextualizado como "onda latina" emocional, não apenas consumista. | positivo |
| Expectativa de público (2 milhões) | Comparado a Madonna/Lady Gaga; meta otimista. | positivo |
| Custo individual da viagem para os fãs | Citado como significativo (R$ 20 mil/pessoa peruana) sem juízo crítico — economia familiar/grupo de fãs. | neutro |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-242 — Música com Shakira, referências do candomblé: o que se sabe sobre o álbum de Anitta 'Equilibrivm'

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 06/04/2026 18:18 UTC
**URL:** https://oglobo.globo.com/cultura/musica/noticia/2026/04/musica-com-shakira-referencias-do-candomble-o-que-se-sabe-sobre-o-album-de-anitta-equilibrivm.ghtml

### Resumo Narrativo

O Globo cobre o lançamento do álbum "Equilibrivm" de Anitta (16 de abril)
e da faixa "Choka choka" (9 de abril), parceria com Shakira. O recorte é
sobre o álbum de Anitta — sua dupla estrutura (português e
inglês/espanhol), referências ao candomblé em "Meia-noite", e outros
feats com Luedji Luna ("Bemba") e Os Garotin ("Caso de Amor"). A
participação de Shakira aparece como destaque do projeto e é
explicitamente vinculada à apresentação gratuita da artista colombiana em
Copacabana no "Todo Mundo no Rio" em 2 de maio. Outras canções listadas:
"Pinterest", "Desgraça", "Mandinga", "Caminhador", "Ternura", "Deus
existe", "So Much Love", "Nanã", "Vai dar caô", "Ouro". A nota fecha
mencionando a estreia de Anitta no Saturday Night Live em 11 de abril.

Shakira é tratada como ativo de prestígio (cobranding entre as duas
artistas) e o show de Copacabana ganha menção contextual. Tom positivo,
sem crítica. Para o escopo da mission, o artigo é tangencialmente Shakira
mas direta e explicitamente conecta a canção "Choka choka" ao show de
maio — está dentro do escopo com peso médio.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Parceria musical Anitta × Shakira ("Choka choka") | Destaque positivo do álbum; cobranding internacional. | positivo |
| Show de Shakira em Copacabana (2/5/2026) | Mencionado como contexto temporal da release da faixa. | positivo |
| Álbum "Equilibrivm" de Anitta — escopo amplo | Foco principal da matéria; tom celebrativo. | muito positivo |
| Espiritualidade / candomblé na obra | Anitta cita "religiosidade em todas as suas vertentes". | positivo |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-243 — Shakira entra para o Guinness como a artista hispânica com maior bilheteria de todos os tempos

**Fonte:** O Globo / Coluna Ancelmo Gois (oglobo.globo.com)
**Data:** 07/04/2026 07:00 UTC
**URL:** https://oglobo.globo.com/blogs/ancelmo/post/2026/04/shakira-entra-para-o-guinness-como-a-artista-hispanica-com-maior-bilheteria-de-todos-os-tempos.ghtml

### Resumo Narrativo

A coluna Ancelmo Gois informa que o palco do show de Shakira em Copacabana
já está sendo montado, com números que "impressionam": **1.345 m² de
palco, passarela de 25 metros de comprimento, 500 m² de LED**, palco
elevado a 2,20 m da areia, **16 torres** com som e vídeo ao longo da praia
(cada telão LED de 45 m²). A informação é atribuída a Luiz Guilherme
Niemeyer, sócio da Bonus Track. A coluna também traz métricas de
engajamento: desde a confirmação do show em 11 de fevereiro até 31 de
março, **209 mil menções nas redes sociais por 77.900 usuários únicos**,
com alcance estimado de **366,2 milhões de pessoas**. Fecha registrando
que Shakira entrou para o Guinness como a artista hispânica de maior
bilheteria de todos os tempos, complementando com a residência na Espanha
(11 shows / 600 mil ingressos vendidos entre setembro e outubro).

Tom claramente celebratório e apoiado em métricas. Sem contraponto
crítico (segurança, mobilidade, custo público).

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Infraestrutura / palco do show | Especificações monumentais (1.345 m², 500 m² LED, 16 torres). Celebrado como "o maior já montado" em Copacabana. | muito positivo |
| Engajamento em redes sociais / hype | 209 mil menções, alcance de 366,2 mi pessoas. Apresentado como sucesso de comunicação. | muito positivo |
| Recorde Guinness de Shakira | Reforça aura de evento de classe mundial. | muito positivo |
| Bonus Track (produtora) | Citada como executora, sem crítica. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-239 — Shakira terá maior palco maior do que Lady Gaga e Madonna em show em Copacabana

**Fonte:** CBN (cbn.globoradio.globo.com)
**Data:** 07/04/2026 22:25 UTC
**URL:** https://cbn.globoradio.globo.com/cidades/rio-de-janeiro/2026/04/07/shakira-tera-maior-palco-maior-do-que-lady-gaga-e-madonna-em-show-em-copacabana.htm

### Resumo Narrativo

Nota da redação CBN informando que o palco para o show de Shakira em
Copacabana será maior que os de Madonna e Lady Gaga: **1.345 m² (vs.
1.260 m² de Lady Gaga em 2025)**, passarela de 25 m, 500 m² de LED, 16
torres de som e vídeo ao longo da praia, palco elevado a 2,20 m. A nota
remete também ao álbum de Anitta com participação de Shakira ("Choka
choka") como contexto musical. Conteúdo essencialmente igual ao de
`a-243` (mesma fonte de informação Bonus Track), mas em tom mais factual
de redação radiofônica, sem o ângulo "Guinness/recordes globais" e sem
métricas de redes sociais.

Trata-se essencialmente de re-publicação/repackage do release da
produtora; o ranking comparativo (maior que Madonna/Lady Gaga) é o
gancho que distingue esta versão.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Palco do show / superlativos comparativos | Maior que Madonna e Lady Gaga; positivo, factual. | muito positivo |
| Tecnologia do show (LEDs, torres) | Mencionada como diferencial; positivo. | positivo |
| Conexão com Anitta ("Choka choka") | Contexto musical; positivo. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-245 — 'Choka Choka': Música de Anitta e Shakira gera engajamento de quase 2 milhões nas redes

**Fonte:** O Globo / Coluna Lauro Jardim (oglobo.globo.com)
**Data:** 10/04/2026 18:22 UTC
**URL:** https://oglobo.globo.com/blogs/lauro-jardim/post/2026/04/choka-choka-musica-de-anitta-e-shakira-gera-engajamento-de-quase-2-milhoes-nas-redes.ghtml

### Resumo Narrativo

A coluna do Lauro Jardim documenta a explosão de engajamento digital da
parceria Anitta × Shakira: 1,9 milhão de interações até a manhã seguinte
ao lançamento de "Choka Choka". Levantamento da Nexus posiciona a música
em 2º lugar nos Trending Topics Brasil das últimas 24 horas (com "Anitta
e Shakira" em 3º) e 20º lugar nos Trending Topics Global. Análise
amostral de 140 mil menções em português indica alcance estimado de 14,8
milhões de impressões. A coluna sublinha a especulação de que Anitta
fará participação especial no show de Copacabana de 2 de maio. Termos
recorrentes na nuvem incluem "Spotify", "Brasil", "Equilibrivm", "Deus",
"Saturday Night Live" e "realeza latina".

A peça é puramente de métricas de marketing/engajamento; não traz
contraponto crítico. Tom celebratório.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Engajamento digital da colaboração Anitta × Shakira | Quantificado com métricas robustas (1,9M interações, 14,8M impressões); tom de "fenômeno". | muito positivo |
| Especulação de participação Anitta no show de Copacabana | Apresentada como expectativa positiva dos fãs. | positivo |
| "Realeza latina" como narrativa | Termo na nuvem de redes sociais; reforça posicionamento aspiracional. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-244 — O que significa 'Choka Choka', título de feat de Anitta e Shakira que rendeu milhões de interações nas redes

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 10/04/2026 21:10 UTC
**URL:** https://oglobo.globo.com/cultura/musica/noticia/2026/04/o-que-significa-choka-choka-titulo-de-feat-de-anitta-e-shakira-que-rendeu-milhoes-de-interacoes-nas-redes.ghtml

### Resumo Narrativo

Nota cultural-explicativa sobre o significado de "Choka Choka": a
expressão remete ao verbo "chocar" (em português e espanhol — bater,
encostar, colidir), mas no contexto da música funciona como onomatopeia
rítmica do reggaeton, semelhante a "Waka Waka" da própria Shakira. O
professor de espanhol Gabriel Bernardo Saraiva Pereira contextualiza a
função sensual e dançante do termo. A matéria também recapitula o
histórico de colaborações Anitta × Shakira (clipe de "Soltera"), e reforça
a expectativa de dueto ao vivo no show de Copacabana em 2 de maio. Lista
outras canções homônimas no pop latino (Chayanne ft. Ozuna, Kiko Rivera).

Tom positivo de jornalismo cultural; aproveita o momentum de "Choka
Choka" para dar contexto linguístico-musical.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Significado/contexto cultural do termo "Choka Choka" | Explicado de forma didática; positivo. | positivo |
| Expectativa de dueto Anitta × Shakira em Copacabana | Tratada como aposta positiva dos fãs. | positivo |
| Histórico de colaboração Anitta × Shakira ("Soltera") | Reforça legitimidade da parceria. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-246 — Shakira prova comidas típicas brasileiras a duas semanas de show no Rio

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 14/04/2026 12:03 UTC
**URL:** https://oglobo.globo.com/cultura/noticia/2026/04/shakira-prova-comidas-tipicas-brasileira-a-um-mes-de-show-no-rio.ghtml

### Resumo Narrativo

Matéria leve e promocional: Shakira publicou vídeo nas redes provando
coxinha (que comparou a "croquete espanhol"), pão de queijo (declarado
"uma das melhores coisas do Brasil") e brigadeiro. A nota retoma o
contexto do show — Copacabana, 2 de maio, expectativa de >2 milhões de
pessoas, sequência de Madonna e Lady Gaga — e cita Shakira em português
fluente: "Brasil, eu vou estar com vocês, em breve, no concerto mais
sonhado da minha vida". Tom afetivo, direcionado ao engajamento do
público brasileiro com a artista.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Engajamento afetivo Shakira × público brasileiro | Vídeo de aproximação cultural; tom muito positivo. | muito positivo |
| Marketing de antecipação do show | Contagem regressiva ("a duas semanas") como gancho. | positivo |
| Expectativa de público gigante | Citação de >2 milhões; positivo. | muito positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-51 — Projeto de naturalização da Lagoa Rodrigo de Freitas inicia nova fase

**Fonte:** Tempo Real (tempo-real.com)
**Data:** 14/04/2026 18:17 UTC
**URL:** https://tempo-real.com/post/projeto-de-naturalizacao-da-lagoa-rodrigo-de-freitas-inicia-nova-fase-e-intervencoes-chegam-ao-parque-dos-patins/

### Resumo Narrativo

Artigo fora de escopo — não trata do show da Shakira. A peça cobre o
projeto de naturalização da Lagoa Rodrigo de Freitas tocado pelo vereador
Flávio Valle (PSD) com o biólogo Mário Moscatelli — terceira e quarta
etapas com intervenções no Parque dos Patins e Corte do Cantagalo,
plantio de manguezal/restinga, reintrodução da Annona glabra, etc. A
única ocorrência de "Shakira" no texto é num bloco "Você pode gostar
também" listando notícias relacionadas ("Big Brother em Copacabana:
governo do estado contrata IA e reconhecimento facial para o show da
Shakira por R$ 15,9 milhões"). É exemplar do shape de falso-positivo via
related-link que o pipeline já filtra por safe-surface, mas que este
artigo capturou via story-tag herdado do tag de Flávio Valle.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| (Tema Shakira) | Aparece apenas em bloco "Você pode gostar" — não é objeto da matéria. | n/a |

### Classificação Geral

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo**: trata do projeto ambiental da Lagoa Rodrigo de Freitas; menção a Shakira é incidental em sidebar de artigos relacionados. Bloco mantido por integridade do protocolo.

---

## a-250 — Pabllo Vittar comanda festa no Jockey após megashow de Shakira

**Fonte:** O Globo / Rio Show (oglobo.globo.com)
**Data:** 15/04/2026 06:00 UTC
**URL:** https://oglobo.globo.com/rio-show/eventos/noticia/2026/04/todo-mundo-no-rio-pabllo-vittar-comanda-after-de-megashow-de-shakira.ghtml

### Resumo Narrativo

Matéria do Rio Show anuncia que Pabllo Vittar comandará a festa "after"
oficial do show de Shakira em Copacabana, no dia 2 de maio, com seu
projeto Club Vittar em parceria com a boate LGBTQIAPN+ Zig (de São Paulo).
A festa "Todo mundo na Zig com Club Vittar" acontece no EXC Rio (Jockey
Club), das 23h30 até 8h da manhã. Ingressos: R$ 80 (1º lote) a R$ 120 (4º
lote). A nota recapitula o histórico de Pabllo no "Todo Mundo no Rio":
abertura para Lady Gaga em 2025 e participação no show de Madonna em 2024.

Tom positivo, factual, com contexto de continuidade (Madonna → Lady Gaga
→ Shakira). Sem crítica.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Festa after-party do show / ecosistema de eventos paralelos | Apresentada como extensão natural da experiência do show. | positivo |
| Continuidade Pabllo Vittar × "Todo Mundo no Rio" | Histórico positivo (Madonna, Lady Gaga). | positivo |
| LGBTQIAPN+ inclusão no entorno do evento | Boate Zig sediando o after. | positivo |
| Preço do after-party (R$ 80–120) | Mencionado factualmente, sem juízo. | neutro |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-224 — Shakira no Rio: a 18 dias do show em Copacabana, saiba o que a colombiana anda fazendo

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 15/04/2026 07:01 UTC
**URL:** https://oglobo.globo.com/cultura/musica/noticia/2026/04/shakira-no-rio-a-18-dias-do-show-em-copacabana-saiba-o-que-a-colombiana-anda-fazendo.ghtml

### Resumo Narrativo

Recap da semana de Shakira a 18 dias do show: vídeo provando comidas
brasileiras, parceria "Choka Choka" com Anitta lançada em 9 de abril, e o
contexto da turnê "Las mujeres ya no lloran" (iniciada no Rio em fevereiro
de 2025). A turnê entrou para o Guinness como a de maior bilheteria de um
artista latino na história — US$ 421,6 milhões, 3,3 milhões de ingressos
em 86 shows. Após Copacabana (2 de maio), Shakira segue para EUA (junho/
julho), residência em Madri (11 datas em outubro), e shows no Catar,
Emirados Árabes e nas pirâmides de Gizé em novembro. Tom de "fenômeno
global em ascensão"; sem crítica.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Recap das movimentações pré-show de Shakira | Tratado como expectativa positiva. | positivo |
| Recordes da turnê (Guinness, US$ 421,6 mi) | Reforça posicionamento de classe mundial. | muito positivo |
| Calendário internacional pós-Copacabana | Apresentado como prestígio para o show carioca. | positivo |
| Conexão emocional com público brasileiro (vídeo das comidas) | Engajamento afetivo. | muito positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-249 — Leque 'shakidólar', bandeiras e camisetas: comércio na Saara lucra com expectativa pelo show de Shakira

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 15/04/2026 07:30 UTC
**URL:** https://oglobo.globo.com/rio/noticia/2026/04/leque-shakidolar-bandeiras-e-camisetas-comercio-na-saara-lucra-com-expectativa-pelo-show-de-shakira-em-copacabana.ghtml

### Resumo Narrativo

Reportagem multifacetada sobre o efeito-Shakira no comércio popular e na
infraestrutura. **Saara**: a loja Lix vende o "shakidólar" (leque com
rosto de Shakira em uma nota de US$ 100, R$ 79,90) — 800 das primeiras
mil unidades vendidas, principalmente online; coleção também tem copos
(R$ 24,90), camisetas (R$ 95), pochetes (R$ 64,90) e bandeiras (R$
129,90). **Praia/Copacabana**: 4 mil pessoas trabalham nos preparativos;
o palco será o maior dos três (1.345 m², passarela 25 m, 16 torres,
telão de 500 m²); painel gigante de 74,5 m × 10 m no Túnel Engenheiro
Coelho Cintra dá boas-vindas. Aulas de "Waka Waka" nos domingos 19 e 26
em frente ao palco. **Quiosques**: Morena (em frente à Praça do Lido)
cobra R$ 1.300/ingresso com bufê e bebida; Areia MPB e Nacho organizam
"Waka & Fiesta" pelo mesmo valor. **Hospedagem**: Embratur registra ~8,5
mil passagens internacionais (Argentina lidera com 3,5 mil, EUA com
753). HotéisRio (presidente Alfredo Lopes) projeta ocupação acima de 70%
na Zona Sul e 65% na cidade — abaixo dos 86,6% de Lady Gaga (público de
2,1 milhões), em parte por preços de passagens 32% mais altos pela
guerra no Oriente Médio e por Shakira já ter cantado no Engenhão em
fevereiro de 2025. **Segurança**: estratégia ainda não divulgada, mas
provavelmente similar à de Madonna/Lady Gaga (bloqueios, revistas,
detectores).

A reportagem é positiva no comércio e na expectativa cultural, mas
introduz a primeira nota cautelar dos hotéis (ocupação possivelmente
abaixo do recorde de Lady Gaga) — um contraponto sutil ao discurso de
boom universal.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Comércio popular da Saara lucrando ("shakidólar", camisetas, leques) | Caso celebrado, com números. | muito positivo |
| Magnitude da operação (4 mil trabalhadores, palco de 1.345 m²) | Apresentada como espetáculo de classe mundial. | muito positivo |
| Expectativa de ocupação hoteleira moderada (70% Zona Sul) | Contraponto cautelar; ressalva ao "Shakira-effect" universal. | neutro |
| Custo das passagens aéreas (+32% por guerra no Oriente Médio) | Citado como freio à demanda. | negativo |
| Quiosques de Copacabana com jantares premium (R$ 1.300) | Tratados como alta procura. | positivo |
| Marketing urbano (painel gigante no Túnel) | Reforça hype. | positivo |
| Aulas de "Waka Waka" para fãs nos domingos pré-show | Engajamento cultural-comunitário. | muito positivo |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-50 — Secretário de Ordem Pública vai à Câmara do Rio discutir políticas para ambulantes após ação violenta em Ipanema

**Fonte:** Tempo Real (tempo-real.com)
**Data:** 15/04/2026 18:10 UTC
**URL:** https://tempo-real.com/post/secretario-de-ordem-publica-vai-a-camara-do-rio-discutir-politicas-para-ambulantes-apos-acao-violenta-em-ipanema/

### Resumo Narrativo

Artigo fora de escopo — não trata do show da Shakira. Reportagem sobre
abordagem violenta da Seop contra a artesã Vitória Aguiar em Ipanema
(sábado 11/04), reunião extraordinária na Câmara do Rio em 30/04 para
discutir políticas para ambulantes, e afastamento dos agentes envolvidos.
Mencionados: Marcus Belchior (Seop), Andrea Riechert Senko (Fazenda),
prefeito Eduardo Cavaliere, vereadores Rosa Fernandes (PSD), Welington
Dias (PDT) e Flávio Valle (PSD). A única conexão Shakira é via sidebar
"Você pode gostar" — link para "Big Brother em Copacabana: governo do
estado contrata IA e reconhecimento facial para o show da Shakira por R$
15,9 milhões". Capturado pelo pipeline via tag de Flávio Valle, igual a
`a-51`.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| (Tema Shakira) | Aparece apenas em sidebar de artigos relacionados. | n/a |

### Classificação Geral

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo**: trata da ação da Seop contra ambulantes em Ipanema; menção a Shakira é incidental em sidebar. Bloco mantido por integridade do protocolo.

---

## a-248 — Show da Shakira em Copacabana: diárias no Rio podem até quintuplicar

**Fonte:** O Globo / Coluna Lauro Jardim (oglobo.globo.com)
**Data:** 15/04/2026 18:22 UTC
**URL:** https://oglobo.globo.com/blogs/lauro-jardim/post/2026/04/show-da-shakira-em-copacabana-diarias-no-rio-podem-ate-quintuplicar.ghtml

### Resumo Narrativo

Nota curta da coluna Lauro Jardim com estimativa do CEO do Trade
Imobiliário, Ramiro Delgado: o show pode fazer diárias quintuplicarem
dependendo da localização e tipo de imóvel; valorização média de 60%, e
ocupação acima de 90% em Copacabana, Ipanema e Barra da Tijuca. Estimativa
baseada em dados históricos, monitoramento em tempo real e inteligência
de campo. Tom puramente comercial-imobiliário; nenhum contraponto sobre
acessibilidade ou pressão sobre moradores.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Valorização de aluguel por temporada (até 5×) | Apresentada como benefício; ângulo de mercado imobiliário. | muito positivo |
| Ocupação >90% em Copacabana/Ipanema/Barra | Reforça boom. | muito positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-247 — A pouco mais de 2 semanas de show na Praia de Copacabana, Shakira lança vídeo de 'Algo Tú'

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 15/04/2026 21:59 UTC
**URL:** https://oglobo.globo.com/cultura/musica/noticia/2026/04/a-pouco-mais-de-2-semanas-de-show-na-praia-de-copacabana-shakira-lanca-clipe-de-algo-tu.ghtml

### Resumo Narrativo

Anúncio de lançamento do clipe "Algo Tú", parceria com Beéle, marcado
para 16 de abril às 13h após cerca de seis meses de produção. Matéria
posiciona o lançamento como movimento de marketing pré-show: aumenta
expectativa do setlist em Copacabana e alimenta especulação de
participação de Anitta. Tom positivo, factual.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Lançamento de clipe "Algo Tú" (parceria com Beéle) | Movimento de marketing pré-show; positivo. | positivo |
| Expectativa de setlist e participações especiais (Anitta) | Especulação dos fãs; positiva. | positivo |
| Estratégia de parcerias musicais recentes de Shakira | Apresentada como acerto. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-10 — Bar acusado de antissemitismo pode ter alvará cassado no Rio de Janeiro

**Fonte:** R7 (noticias.r7.com)
**Data:** 15/04/2026 23:19 UTC
**URL:** https://noticias.r7.com/rio-de-janeiro/bar-acusado-de-antissemitismo-pode-ter-alvara-cassado-no-rio-de-janeiro-entenda-15042026

### Resumo Narrativo

Artigo fora de escopo — não trata do show da Shakira. Cobre o início do
processo de cassação do alvará do bar Partisan na Lapa (acusado de
discriminação contra cidadãos de Israel e EUA), acionado pelo vereador
Flávio Valle. Shakira só aparece em link "Veja mais" no rodapé ("Show de
Shakira no Rio terá esquema especial de segurança e transporte"). Captura
via tag de Flávio Valle.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| (Tema Shakira) | Aparece apenas em link "Veja mais" no rodapé. | n/a |

### Classificação Geral

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo**: trata da cassação de alvará por antissemitismo; menção a Shakira é incidental em link relacionado.

---

## a-252 — 'Orgulhosa de saber que vou cantar no altar do planeta', diz Shakira

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 16/04/2026 00:01 UTC
**URL:** https://oglobo.globo.com/rio/noticia/2026/04/orgulhosa-de-saber-que-vou-cantar-no-altar-do-planeta-diz-shakira-que-se-apresenta-em-copacabana-em-2-de-maio.ghtml

### Resumo Narrativo

Recap do engajamento de Shakira nas redes sociais a duas semanas do show:
ela compartilha reportagem do Globo dizendo "Orgullosa de saber que voy a
cantar desde el altar del planeta", veste camisa da seleção brasileira,
prova coxinha/brigadeiro/pão de queijo, anuncia clipe "Algo Tú" com
Beéle, e recapitula a parceria "Choka Choka" com Anitta. Recapitulação
das especificações do palco (1.345 m², passarela 25 m, 16 torres, telão
500 m²), do painel gigante no Túnel Engenheiro Coelho Cintra, e das
aulas de "Waka Waka" nos domingos pré-show. Tom celebratório, sem
contraponto.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Marketing afetivo de Shakira × público brasileiro | Tom muito positivo. | muito positivo |
| Magnitude do palco e da operação | Reforço dos números monumentais. | muito positivo |
| Aulas comunitárias de "Waka Waka" | Engajamento cultural. | muito positivo |
| "Altar do planeta" como narrativa | Posicionamento aspiracional. | muito positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-251 — Efeito Shakira: Galeão receberá 314 mil passageiros

**Fonte:** O Globo / Coluna Ancelmo Gois (oglobo.globo.com)
**Data:** 16/04/2026 13:22 UTC
**URL:** https://oglobo.globo.com/blogs/ancelmo/post/2026/04/efeito-shakira-galeao-recebera-314-mil-passageiros.ghtml

### Resumo Narrativo

Nota curta com dados da concessionária do Aeroporto Galeão: estimativa
de **314 mil passageiros** entre 30 de abril e 5 de maio, **+14% vs.
2025 e +46% vs. 2024**. Principais destinos domésticos: São Paulo,
Porto Alegre, Vitória, Salvador, Curitiba. Internacionais: Buenos
Aires, Santiago, Bogotá, Lisboa, Cidade do Panamá. Tom factual-positivo
de "efeito Shakira" no fluxo aeroportuário.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Movimento aeroportuário (314 mil passageiros, +14%/+46%) | Apresentado como benefício direto. | muito positivo |
| Destinos sul-americanos (BA, Santiago, Bogotá) | Reforça narrativa "invasão latina". | positivo |
| Destinos lusófonos (Lisboa) e centro-americanos (Panamá) | Diversificação do fluxo. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-229 — Por que Shakira é chamada de 'Loba'? Entenda a origem do apelido

**Fonte:** Gshow (gshow.globo.com)
**Data:** 18/04/2026 07:02 UTC
**URL:** https://gshow.globo.com/musica/noticia/2026/04/por-que-shakira-e-chamada-de-loba-entenda-a-origem-do-apelido.ghtml

### Resumo Narrativo

Matéria cultural-explicativa do gshow contextualizando o apelido "Loba"
de Shakira a partir da música "She Wolf" (2009), do livro "Mulheres que
Correm com os Lobos" (Clarissa Pinkola Estés, 1992) e da retomada da
referência em "Bzrp Music Sessions Vol. 53" (2023, pós-Piqué). Resume a
importância simbólica do apelido como empoderamento feminino e conecta
ao show de Copacabana (2 de maio) e à proposta de quatro edições do
"Todo Mundo no Rio" para consolidar maio como vitrine global do Rio.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Origem cultural do apelido "Loba" | Tratado positivamente como símbolo de empoderamento. | muito positivo |
| Empoderamento feminino na narrativa Shakira | Reforça relevância cultural do show. | muito positivo |
| Estratégia de quatro anos do "Todo Mundo no Rio" | Apresentada como vitrine global da cidade. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-222 — Shakira no Rio: conheça as eras da cantora que marcaram mais de três décadas de carreira

**Fonte:** Gshow (gshow.globo.com)
**Data:** 20/04/2026 07:01 UTC
**URL:** https://gshow.globo.com/musica/noticia/2026/04/shakira-no-rio-conheca-as-eras-da-cantora-que-marcaram-mais-de-tres-decadas-de-carreira.ghtml

### Resumo Narrativo

Retrospectiva de carreira de Shakira em "eras" (Pies Descalzos 1995,
Laundry Service 2001, She Wolf 2009, Sale el Sol 2010, Shakira 2014, El
Dorado 2017, Las Mujeres Ya No Lloran 2024). Cada era descrita com hits
e estética. Conecta ao show de 2 de maio em Copacabana como evento que
"revisita as grandes fases" e ao "Todo Mundo no Rio" (3ª edição) com
proposta de quatro anos para consolidar maio como marco do calendário
carioca. Tom didático-celebratório.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Retrospectiva da carreira de Shakira | Trato celebratório-didático; positivo. | muito positivo |
| Show como revisitação de grandes fases | Reforça expectativa de setlist robusto. | positivo |
| Estratégia plurianual do Todo Mundo no Rio | Vitrine global da cidade. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

<!-- Próxima Penelope retoma aqui. Use python3 tools/penelope_shakira_iter.py todo
     para listar artigos restantes em ordem cronológica. -->

## Próxima Penelope — guia de retomada (curto)

1. `git pull && python3 tools/penelope_shakira_iter.py list`
   - Se `total > 3`, dados frescos chegaram. Caminho de chegada possível:
     a) Otávio commitou dump do Render disk em `assets/`;
     b) GitHub Action `penelope-fetch-shakira.yml` rodou e commitou em
        `tools/penelope-fetched/`. O helper detecta o segundo automaticamente.
2. `python3 tools/penelope_shakira_iter.py todo`
   - Mostra IDs ainda não-feitos.
3. Para cada ID:
   ```
   python3 tools/penelope_shakira_iter.py show a-NNN  # ler tudo
   # produzir bloco no formato Etapa 1 (ver acima)
   git commit -m "analise-shakira: a-NNN — ..."
   ```
   - Reportar a Otávio a cada 20 artigos concluídos.
4. Quando completar (ou parar): `python3 tools/penelope_consolida_temas.py`
   regenera `consolidacao-temas.md` (parte mecânica da Etapa 2). A síntese
   narrativa por categoria fica para a Penelope/classificador.
