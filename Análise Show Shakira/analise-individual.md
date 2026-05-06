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

## a-49 — Câmara do Rio remarca reunião com secretário de Ordem Pública

**Fonte:** Tempo Real (tempo-real.com)
**Data:** 20/04/2026 15:38 UTC
**URL:** https://tempo-real.com/post/camara-do-rio-remarca-reuniao-com-secretario-de-ordem-publica-para-um-dia-apos-audiencia-publica-sobre-ambulantes-na-orla/

### Resumo Narrativo

Artigo fora de escopo — não trata do show da Shakira. Cobre o
remarcamento da reunião sobre ação da Seop contra ambulantes em Ipanema
para 6 de maio (após audiência pública em 5 de maio). Vereadores
mencionados incluem Flávio Valle (PSD). Shakira aparece apenas em link
"Veja mais" e em sidebar de "Últimas Notícias" ("Operação Shakira na
areia: Seop prende homem que tentou cobrar R$ 1,8 mil por caipirinha").
Capturado pelo tag de Flávio Valle.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| (Tema Shakira) | Aparece apenas em sidebar e link relacionado. | n/a |

### Classificação Geral

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo**: trata de reunião sobre ambulantes; menção a Shakira é incidental.

---

## a-254 — Efeito Shakira: supermercados projetam aumento de venda de até 30% em lojas de Copacabana e Leme

**Fonte:** O Globo / Coluna Míriam Leitão (oglobo.globo.com)
**Data:** 20/04/2026 16:47 UTC
**URL:** https://oglobo.globo.com/blogs/miriam-leitao/post/2026/04/efeito-shakira-supermercados-projetam-aumento-de-venda-de-ate-30percent-em-lojas-de-copacabana.ghtml

### Resumo Narrativo

Coluna Míriam Leitão / Luciana Casemiro reporta pesquisa da Asserj
(Associação de Supermercados do Estado do Rio de Janeiro) projetando
crescimento de até 30% em vendas em supermercados de Copacabana e Leme
durante a primeira semana de maio. Mesmo padrão do show de Lady Gaga
(+30%); Madonna teve impacto menor (+15%). Bebidas, biscoitos, prontos
para consumo são as categorias-chave. Gerentes do Pão de Açúcar (Marcílio
Santos) e Supermarket (Enderson Nascimento) descrevem reforço de estoque,
ampliação de horário, e bazar com cadeiras de praia, isopores e copos. Tom
celebratório, varejo-positivo.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Aumento de vendas em supermercados (+30%) | Apresentado como benefício direto. | muito positivo |
| Logística do varejo (estoque, horário ampliado) | Adaptação positiva ao megaevento. | positivo |
| Categorias beneficiadas (bebidas, prontos) | Tendência de consumo de evento. | positivo |
| Comparação com Madonna (+15%) e Lady Gaga (+30%) | Coloca Shakira no mesmo patamar de Lady Gaga. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-253 — Airbnb: cresce a procura de quartos no Rio de olho no show de Shakira

**Fonte:** O Globo / Coluna Ancelmo Gois (oglobo.globo.com)
**Data:** 20/04/2026 16:53 UTC
**URL:** https://oglobo.globo.com/blogs/ancelmo/post/2026/04/airbnb-cresce-a-procura-de-quartos-no-rio-de-olho-no-show-de-shakira-em-copacabana.ghtml

### Resumo Narrativo

Nota com dados do Airbnb mostrando aumento na procura de hospedagem no
Rio para o período do show. Origens domésticas: SP, BH, Campinas. América
Latina: Santiago, Buenos Aires, Montevidéu. Internacional (Europa/EUA):
Paris, Londres, Nova York. Detalhe relevante: estrangeiros têm
permanência média 2× maior que brasileiros. Tom factual-positivo.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Demanda Airbnb / hospedagem alternativa | Crescimento positivo. | muito positivo |
| Mistura de fluxos doméstico × internacional × latino-americano | Diversificação positiva. | positivo |
| Permanência mais longa de estrangeiros | Implícito ganho em pernoites turísticas. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-221 — Antes de Copacabana, Shakira reuniu 4 mil pessoas em show na Grande SP nos anos 90

**Fonte:** G1 Mogi das Cruzes (g1.globo.com)
**Data:** 21/04/2026 08:01 UTC
**URL:** https://g1.globo.com/sp/mogi-das-cruzes-suzano/noticia/2026/04/21/antes-de-copacabana-shakira-reuniu-4-mil-pessoas-em-show-na-grande-sp-nos-anos-90.ghtml

### Resumo Narrativo

Reportagem nostálgica do g1 Mogi das Cruzes recupera show de Shakira em
1997 na casa La Boom (shopping local), com 4 mil pessoas e ingresso de
~R$ 50. Inclui depoimentos do arquiteto Roberto Kimura (sócio da casa) e
do médico Luiz Antonio Ribeiro (dono do SPA da Serra do Itapeti onde
Shakira ficou hospedada após o show). Anedotas: feijoada, loção
hidratante esquecida, fãs na porta, segurança improvisada. Tom afetivo,
celebratório do passado da artista no Brasil.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Histórico Shakira × Brasil (1997, ~40 shows nos 90s) | Tratado nostalgicamente; positivo. | muito positivo |
| Conexão de longa data com público brasileiro | Reforça legitimidade do show de 2026. | muito positivo |
| Anedotas pessoais (SPA, feijoada, creme esquecido) | Humanizam a artista. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-256 — Shakira em Copacabana: Rodoviária do Rio se prepara para receber 215 mil passageiros no feriado

**Fonte:** O Globo / Coluna Ancelmo Gois (oglobo.globo.com)
**Data:** 21/04/2026 15:45 UTC
**URL:** https://oglobo.globo.com/blogs/ancelmo/post/2026/04/shakira-em-copacabana-rodoviaria-do-rio-se-prepara-para-receber-215-mil-passageiros-no-feriado.ghtml

### Resumo Narrativo

Nota factual da coluna Ancelmo Gois: Rodoviária do Rio espera 215 mil
passageiros no período do show. Origens principais: SP, MG, ES, Brasília.
Movimento turbinado pelo feriado de 1º de maio. Ressalva explícita: é
**abaixo** do volume de Lady Gaga (290 mil) e de Madonna (235 mil) — ainda
que próximo aos níveis do Carnaval. Tom factual-cauteloso; primeira nota
relevante de comparação **negativa** com edições anteriores no fluxo
rodoviário.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Movimento rodoviário (215 mil passageiros) | Apresentado como expressivo, mas explicitamente abaixo dos shows anteriores. | neutro |
| Comparação com Lady Gaga (290 mil) e Madonna (235 mil) | Mostra Shakira como o **menor** dos três no fluxo de ônibus. | neutro |
| Origem dos passageiros (SP/MG/ES/DF) | Diversificação doméstica. | positivo |
| Feriado de 1º de maio como turbinador | Conjuntura favorável. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** neutro

---

## a-255 — Shakira diz que 'Anitta é uma rainha'; e brasileira revela que foi convidada para show em Copacabana

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 21/04/2026 23:41 UTC
**URL:** https://oglobo.globo.com/rio/noticia/2026/04/shakira-diz-que-anitta-e-uma-rainha-e-brasileira-revela-que-foi-convidada-para-show-em-copacabana.ghtml

### Resumo Narrativo

Confirmação parcial do dueto Shakira × Anitta: Anitta revelou em
podcast (Charla Podcast) que foi convidada por Shakira para o show em
Copacabana — "vamos cantar juntas?" perguntou Shakira; "Choka Choka"
seria a música. Nem oficializado mas fortemente sinalizado. Shakira
elogiou Anitta ("uma rainha", "essa amizade é um presente") e declarou
expectativa de **2,5 milhões de pessoas** no show — "uma loucura".
Reforça relação de longa data com o Brasil ("aprendi a falar português
primeiro que o inglês"). Tom celebratório.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Confirmação parcial de dueto Anitta × Shakira | Apresentada como expectativa positiva. | muito positivo |
| Expectativa de público (2,5 milhões) | Tom de "loucura/recorde". | muito positivo |
| Relação afetiva Shakira × Brasil (40+ shows, fluência em português) | Reforça legitimidade. | muito positivo |
| Elogio público de Shakira a Anitta | Positivo bilateral. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-82 — Shakira em Copacabana: Cantora enfrenta 'maré de azar' e show no Brasil é decisivo (opinião)

**Fonte:** Estadão / Coluna Carol Prado (estadao.com.br)
**Data:** 22/04/2026 07:00 UTC
**URL:** https://www.estadao.com.br/cultura/shakira-em-copacabana-cantora-enfrenta-mare-de-azar-e-show-no-brasil-e-decisivo

### Resumo Narrativo

Coluna de opinião de Carol Prado no Estadão argumenta que o show de
Copacabana é decisivo para Shakira após uma "maré de azar" na turnê "Las
Mujeres Ya No Lloran": atraso em SP em 2025, cancelamento no Chile e nos
EUA por problemas técnicos, alerta de saúde nos EUA por sarampo de fã,
quedas no palco no Canadá e em El Salvador, internação por problema
estomacal no Peru. A colunista vê o Brasil como "terreno perfeito" para
redenção pela longa relação histórica (40 shows nos anos 90), e considera
"escolha acertada" a aposta do Brasil para a apresentação mais importante
da carreira. Mistura ângulo crítico ao reconhecimento da resiliência
artística — primeira matéria do corpus que articula explicitamente um
contraponto sobre a trajetória recente da artista.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Histórico problemático da turnê (cancelamentos, quedas, doenças) | Reconhecido como fato; "maré de azar" — ângulo crítico. | negativo |
| Brasil como terreno de redenção da carreira | Apresentado positivamente; "escolha acertada". | positivo |
| Relação histórica de Shakira com o público brasileiro | Reforça a aposta. | muito positivo |
| Pressão sobre a performance de Shakira em Copacabana | Tratada como decisiva. | neutro |

### Classificação Geral

**Sentimento geral do artigo:** neutro

---

## a-228 — Shakira terá palco maior que os de Madonna e Lady Gaga; veja as dimensões

**Fonte:** G1 / Globonews (g1.globo.com)
**Data:** 22/04/2026 12:22 UTC
**URL:** https://g1.globo.com/rj/rio-de-janeiro/noticia/2026/04/22/shakira-tera-palco-maior-que-os-de-madonna-e-lady-gaga-veja-as-dimensoes.ghtml

### Resumo Narrativo

Reportagem do Globonews atualizando as dimensões: o palco será de
**1.500 m²** (não 1.345 m² como anteriormente reportado — ampliação a
pedido da equipe da artista), maior que Madonna (812 m²) e Lady Gaga
(1.260 m²). Painéis de LED de 680 m² (também acima dos 500 m² antes
divulgados). Passarela de 25 m até a área em frente ao Copacabana
Palace. Show com transmissão pela TV Globo, Multishow e Globoplay.
Recapitula: 16 torres de 45 m² ao longo de Copacabana até o Leme,
expectativa de 2,5 milhões de pessoas (acima de Madonna 1,6 mi e Lady
Gaga 2,1 mi), histórico desde 1997 no Brasil, show gratuito no México em
março com 400 mil pessoas. Tom muito positivo, "mega-evento".

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Palco superlativo (1.500 m², painéis 680 m²) | Reforça classe mundial; "maior já montado". | muito positivo |
| Comparação com Madonna/Lady Gaga (palco e público) | Shakira supera ambas em projeção. | muito positivo |
| Transmissão TV Globo/Multishow/Globoplay | Amplifica alcance midiático. | positivo |
| Recorde de 400 mil pessoas no México (março) | Reforça aura de evento global. | muito positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-231 — Show de Shakira vai custar R$ 15 milhões para a Prefeitura do Rio

**Fonte:** Gshow (gshow.globo.com)
**Data:** 22/04/2026 17:05 UTC
**URL:** https://gshow.globo.com/musica/noticia/2026/04/show-de-shakira-vai-custar-r-15-milhoes-para-a-prefeitura-do-rio.ghtml

### Resumo Narrativo

Reportagem factual: a Prefeitura do Rio investirá **R$ 15 milhões** no
show de Shakira (mesmo valor de Lady Gaga em 2025, e R$ 5 mi acima dos
R$ 10 mi destinados a Madonna em 2024). Autorização publicada no DOM em
17 de abril; repasse para a Bonus Track. Expectativa: 2,5 milhões de
pessoas. Tom factual, sem ângulo crítico do gasto público, mas a peça
**explicita o custo** — primeira vez no corpus em que o investimento
público é objeto central da reportagem.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Custo público (R$ 15 milhões) | Tratado factualmente; sem questionamento explícito, mas exposto. | neutro |
| Comparação com Madonna (R$ 10 mi) e Lady Gaga (R$ 15 mi) | Shakira no mesmo patamar de Lady Gaga. | neutro |
| Expectativa econômica (movimentar a economia da cidade) | Justificativa positiva do gasto. | positivo |
| Bonus Track como destinatária do repasse | Citada sem juízo. | neutro |

### Classificação Geral

**Sentimento geral do artigo:** neutro

---

## a-223 — Shakira faz post em português dias antes de show: 'Deus me livre não ser latina'

**Fonte:** G1 (g1.globo.com)
**Data:** 22/04/2026 18:20 UTC
**URL:** https://g1.globo.com/rj/rio-de-janeiro/musica/show-shakira-rj/noticia/2026/04/22/shakira-faz-post-em-portugues-dias-antes-de-show-em-copacabana-deus-me-livre-nao-ser-latina.ghtml

### Resumo Narrativo

Recap promocional: Shakira posta nas redes com um boné "Deus me livre
não ser latina" em verde-amarelo-branco-vermelho. Recapitula a
infraestrutura do show (1.345 m² palco, 25 m passarela, 680 m² LED — vs
Madonna 812 m² / Lady Gaga 1.260 m²), a expectativa de 2,5 milhões, o
recorde de 400 mil no México em março, e a transmissão pela TV Globo /
Multishow / Globoplay. Tom muito positivo.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Post afetivo de Shakira em português | Engajamento positivo com o público brasileiro. | muito positivo |
| Identidade latina como bandeira | Reforça narrativa "onda latina" / "altar do planeta". | muito positivo |
| Recap de infraestrutura | Reforço do hype. | positivo |
| Transmissão multi-plataforma (TV Globo / Multishow / Globoplay) | Amplifica alcance. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-257 — Palco de Shakira terá quase o dobro do tamanho do de Madonna

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 22/04/2026 19:10 UTC
**URL:** https://oglobo.globo.com/rio/noticia/2026/04/palco-de-shakira-tera-quase-o-dobro-do-tamanho-do-de-madonna.ghtml

### Resumo Narrativo

Variação editorial sobre o palco recordista. Recapitula 1.500 m² (vs.
Madonna 812 m² — quase o dobro), passarela 25 m, telões 680 m², 16 torres,
expectativa 2 milhões. Inclui aulas de Waka Waka nos domingos pré-show e
as reservas premium dos quiosques (R$ 1,3 mil em Morena e Waka & Fiesta).
Esquema de segurança similar ao réveillon — bloqueio, revistas, detectores.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Palco superlativo (1.500 m², quase 2× Madonna) | Tom celebratório. | muito positivo |
| Aulas comunitárias de Waka Waka | Engajamento cultural. | muito positivo |
| Quiosques com jantar premium (R$ 1,3 mil) | Comércio aproveita demanda. | positivo |
| Esquema de segurança similar a réveillon | Sinaliza preparação adequada. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-260 — Galeão espera receber 314 mil passageiros na semana do show de Shakira

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 23/04/2026 06:00 UTC
**URL:** https://oglobo.globo.com/rio/noticia/2026/04/galeao-espera-receber-314-mil-passageiros-na-semana-do-show-de-shakira.ghtml

### Resumo Narrativo

Detalhamento dos números do Galeão: 314 mil passageiros (213 mil
domésticos + 101 mil internacionais), 1.990 voos (+13% vs 2025, +32% vs
2024), 32 voos extras domésticos. Argentina lidera origens internacionais
(31%), seguida por Chile (14%), EUA (8%), Portugal (7%), Colômbia (6%).
Santos Dumont também: 394 voos / 56.316 assentos entre 1–3 de maio. Tom
factual-celebratório.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Galeão: 314 mil passageiros (+14% / +46%) | Crescimento expressivo. | muito positivo |
| Distribuição de origens internacionais | Argentina/Chile dominam. | positivo |
| Santos Dumont (394 voos) | Aeroporto secundário também movimentado. | positivo |
| 1.990 voos (+13% vs 2025, +32% vs 2024) | Conectividade ampliada. | muito positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-259 — Efeito 'loba': ocupação hoteleira na Zona Sul atinge média de 80% dez dias antes do show

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 23/04/2026 10:00 UTC
**URL:** https://oglobo.globo.com/rio/noticia/2026/04/efeito-loba-ocupacao-hoteleira-na-zona-sul-atinge-media-de-80percent-dez-dias-antes-do-show-de-shakira-em-copacabana.ghtml

### Resumo Narrativo

HotéisRio (Alfredo Lopes) divulga: 80% de ocupação média na Zona Sul, 68%
em toda a cidade — atingidos dez dias antes do show. Lopes reconhece que
a alta nas passagens aéreas atrasou o crescimento da ocupação ("mas com
certeza esse índice vai aumentar"). Recapitula palco 1.500 m² e
expectativa 2 milhões. Tom positivo, com nuance cautelar (a ocupação
ainda está abaixo dos níveis de Lady Gaga implícitamente).

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Ocupação hoteleira (80% Zona Sul, 68% cidade) | Apresentada como forte mas com ressalva de demora. | positivo |
| Impacto da alta de passagens aéreas | Reconhecido como freio. | negativo |
| Movimentação econômica e imagem global do Rio | Reforço positivo do show. | muito positivo |
| Palco (1.500 m²) | Recapitulação positiva. | muito positivo |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-132 — Todo Mundo No Rio: palco do show de Shakira já está sendo montado

**Fonte:** CNN Brasil (cnnbrasil.com.br)
**Data:** 23/04/2026 10:45 UTC
**URL:** https://www.cnnbrasil.com.br/entretenimento/todo-mundo-no-rio-palco-do-show-de-shakira-ja-esta-sendo-montado/

### Resumo Narrativo

CNN Brasil cobre a montagem do palco com imagens de drone. Inclui
declaração de Luiz Guilherme Niemeyer (Bonus Track): "Esse é o maior
palco que já montamos na praia de Copacabana, com certeza vai
impressionar." Cita 1.345 m² (versão anterior, antes da expansão para
1.500 m²) e 500 m² LED. Apelido "Shakicabana" pelo governo do Rio.
Recapitula histórico: 30+ apresentações no Brasil em 1996/97. Show no
México atraiu 400 mil pessoas. Quase 80 milhões de ouvintes mensais no
Spotify.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Palco/recorde de estrutura | Tom celebratório. | muito positivo |
| Apelido "Shakicabana" (governo do Rio) | Marketing institucional. | positivo |
| Histórico Brasil-Shakira (anos 90) | Reforça legitimidade. | positivo |
| Recorde no México (400 mil pessoas) | Reforça aura global. | muito positivo |
| Audiência Spotify (~80 mi/mês) | Ratifica relevância da artista. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-258 — Shakira no Rio: rodoviária prepara show cover da cantora para receber fãs

**Fonte:** O Globo / Coluna Ancelmo Gois (oglobo.globo.com)
**Data:** 23/04/2026 11:00 UTC
**URL:** https://oglobo.globo.com/blogs/ancelmo/post/2026/04/shakira-no-rio-rodoviaria-prepara-show-cover-da-cantora-para-receber-fas.ghtml

### Resumo Narrativo

Rodoviária do Rio preparou recepção especial: cover ao vivo de Shakira
(Izlene Cristina, atriz/cantora lírica/bailarina) em 30 de abril das 7h
às 13h. Estimativa do período (30/4–5/5): 215,8 mil pessoas, 6.700 ônibus
(1.500 extras), 39 viações. Tom celebratório-promocional.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Recepção cultural na rodoviária (cover ao vivo) | Engajamento positivo. | muito positivo |
| Volume de ônibus (6.700, 1.500 extras) | Logística reforçada. | positivo |
| Movimentação rodoviária (215,8 mil) | Apresentada positivamente. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-264 — Efeito Shakira: estacionamento cobra R$ 250 por uma vaga em Copacabana

**Fonte:** O Globo / Coluna Ancelmo Gois (oglobo.globo.com)
**Data:** 24/04/2026 07:00 UTC
**URL:** https://oglobo.globo.com/blogs/ancelmo/post/2026/04/efeito-shakira-estacionamento-cobra-r-250-por-uma-vaga-em-copacabana.ghtml

### Resumo Narrativo

Coluna Ancelmo Gois denuncia inflação de preço de vaga: estacionamento
privado na Rua Barata Ribeiro cobrando R$ 250 fixos pelo dia do show
versus R$ 10 normais por 30 minutos. Tom crítico ("absurdo", "como se
estivesse na área VIP"). Primeira matéria explicitamente crítica de
gouging de preço pela alta demanda do show.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Inflação predatória de estacionamento (R$ 250 vs R$ 10/30min) | Crítica direta — "absurdo". | muito negativo |
| Especulação comercial em torno do show | Negativo, lado escuro do "efeito Shakira". | negativo |

### Classificação Geral

**Sentimento geral do artigo:** negativo

---

## a-128 — Custo de show de Shakira em Copacabana supera o de Madonna; entenda

**Fonte:** CNN Brasil (cnnbrasil.com.br)
**Data:** 24/04/2026 08:00 UTC
**URL:** https://www.cnnbrasil.com.br/entretenimento/custo-de-show-de-shakira-em-copacabana-supera-o-de-madonna-entenda/

### Resumo Narrativo

CNN Brasil confirma: show custará R$ 15 milhões à Prefeitura, contra R$
10 milhões para Madonna em 2024. Repasse à Bonus Track. DOM publicado em
17 de abril. Recapitula estrutura recorde (1.345 m² palco — versão
anterior à atualização para 1.500 m²; 16 torres). Tom factual; expõe o
gasto público sem questionamento explícito.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Custo público (R$ 15 mi vs R$ 10 mi de Madonna) | Tratado factualmente. | neutro |
| Repasse à Bonus Track | Citado sem juízo. | neutro |
| Estrutura recorde do palco | Justificativa positiva implícita. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** neutro

---

## a-263 — Além de Shakira, Joss Stone também faz show gratuito no Brasil em maio

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 24/04/2026 11:59 UTC
**URL:** https://oglobo.globo.com/cultura/musica/noticia/2026/04/alem-de-shakira-joss-stone-tambem-faz-show-gratuito-no-brasil-em-maio-saiba-mais.ghtml

### Resumo Narrativo

Matéria contextual: Joss Stone fará show grátis em Florianópolis em
16/05 no centenário da Ponte Hercílio Luz. Shakira é mencionada
introdutoriamente como referência ("Além da colombiana Shakira...") e o
palco de Copacabana (1.500 m²) é citado em parágrafo final. Show
principal da matéria é Joss Stone; Shakira é gancho/contexto. Marginal-
mente em escopo (informação útil para o panorama de eventos
musicais-gratuitos brasileiros de maio que cerca o show da Shakira).

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Show de Shakira como referência de "show gratuito de maio" | Contexto positivo. | positivo |
| Palco de Copacabana (1.500 m²) | Mencionado factualmente. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-262 — Jaé lança cartão personalizado para o show da Shakira

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 24/04/2026 12:25 UTC
**URL:** https://oglobo.globo.com/rio/noticia/2026/04/jae-lanca-cartao-personalizado-para-o-show-da-shakira.ghtml

### Resumo Narrativo

Jaé (cartão de transporte do Rio) lança edição limitada para
colecionadores: R$ 25 (R$ 15,80 em créditos + R$ 9,20 do casco). Pix.
Vendido das 8h às 18h em estações chave (Jardim Oceânico, Botafogo,
Central, Carioca, Largo do Machado), entre 24/04 e 2/05. Tom
positivo-promocional.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Merchandising oficial via cartão de transporte | Iniciativa criativa institucional. | positivo |
| Engajamento de colecionadores | Positivo cultural. | positivo |
| Pagamento via Pix | Modernidade. | neutro |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-217 — Palco de Shakira em Copacabana tem passarela de 25 metros montada em direção ao público

**Fonte:** G1 / RJ1 (g1.globo.com)
**Data:** 24/04/2026 16:05 UTC
**URL:** https://g1.globo.com/rj/rio-de-janeiro/noticia/2026/04/24/palco-de-shakira-em-copacabana-tem-passarela-de-25-metros-montada-em-direcao-ao-publico.ghtml

### Resumo Narrativo

Atualização visual da montagem: passarela de 25 m foi instalada na manhã
de 24/04. Recapitula palco maior que Lady Gaga e Madonna; 16 torres ao
longo da orla; 314 mil passageiros esperados no Galeão; transmissão TV
Globo / Multishow / Globoplay; "maior apresentação da carreira" segundo
Shakira. Tom muito positivo.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Passarela de 25 m em direção ao público | Aproximação artista-fã; positivo. | muito positivo |
| Marco de "maior apresentação da carreira" | Reforça aura aspiracional. | muito positivo |
| Recap de logística (Galeão, transmissão) | Reforço positivo. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-88 — Show da Shakira deve reunir 2,5 milhões de pessoas em Copacabana

**Fonte:** Brasil de Fato (brasildefato.com.br)
**Data:** 24/04/2026 16:33 UTC
**URL:** https://www.brasildefato.com.br/2026/04/24/show-da-shakira-deve-reunir-2-5-milhoes-de-pessoas-em-copacabana/

### Resumo Narrativo

Brasil de Fato cobre o show com perspectiva de "soft power": expectativa
de 2,5 milhões, palco 1.345 m², 16 torres, 314 mil passageiros no Galeão,
custo R$ 15 mi à Prefeitura, repasse via Secretaria de Cultura à Bonus
Track. Repertório esperado: clássicos + faixas de "Las Mujeres Ya No
Lloran". Cita possível dueto com Anitta. Tom positivo, sem crítica
significativa apesar do veículo ter perfil de esquerda — curiosamente
não problematiza o gasto público.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Expectativa de público (2,5 mi) | Tom celebratório. | muito positivo |
| Custo público (R$ 15 mi) | Citado factualmente. | neutro |
| Movimento turístico via Galeão | Positivo. | positivo |
| Dueto Anitta especulado | Reforça hype. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-104 — Shakira no Rio: veja se ainda dá tempo de ganhar experiência VIP em show

**Fonte:** CNN Brasil (cnnbrasil.com.br)
**Data:** 24/04/2026 17:43 UTC
**URL:** https://www.cnnbrasil.com.br/entretenimento/shakira-no-rio-veja-se-ainda-da-tempo-de-ganhar-experiencia-vip-em-show/

### Resumo Narrativo

CNN Brasil destaca campanhas comerciais para acesso VIP: Santander
"Todas as Sharás no Rio" (25 ingressos para brasileiras chamadas
Shakira), Beats "My Beats Don't Lie" (campanha TikTok com áudio Anitta
guiando recriação de poses do clipe "Hips Don't Lie", 9 vídeos vencedores
ganham par de ingressos para área de convidados). Inscrições até 27/04,
resultado 29/04. Tom positivo-promocional.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Marketing de patrocinadores (Santander, Beats) | Apresentado positivamente. | positivo |
| Acesso VIP exclusivo | Cobertura factual. | neutro |
| Engajamento via TikTok / desafios virais | Apresentado como inclusivo. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-261 — Faltando uma semana, Shakira lança compilação 'Shakira no Rio: As melhores'

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 24/04/2026 18:35 UTC
**URL:** https://oglobo.globo.com/cultura/musica/noticia/2026/04/faltando-uma-semana-para-show-em-copacabana-shakira-lanca-compilacao-de-musicas-inspirada-no-rio.ghtml

### Resumo Narrativo

Lançamento de playlist oficial "Shakira no Rio: As melhores" com 30
faixas selecionadas para aquecimento ("Whenever, wherever", "Estoy
aquí", "Hips don't lie", "La la la", "She wolf", "Waka waka"). Recap
palco 1.500 m². Tom positivo-promocional, marketing musical.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Lançamento de playlist oficial | Marketing positivo. | muito positivo |
| Repertório esperado no setlist | Reforça expectativa. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-269 / a-268 — Estilista brasileiro Dario Mitmann assina figurino de encerramento

**Fonte:** O Globo (oglobo.globo.com) — duplicada em dois IDs (a-269 e a-268, mesmo URL/conteúdo)
**Data:** 25/04/2026 07:01 UTC
**URL:** https://oglobo.globo.com/cultura/musica/noticia/2026/04/estilista-brasileiro-assina-figurino-que-shakira-vai-usar-no-encerramento-do-show-em-copacabana.ghtml

### Resumo Narrativo

Reportagem cultural sobre o estilista catarinense Dario Mitmann, que
assina o figurino de encerramento do show ("brilho, cores, visual
sexy", referências tribais, segunda-pele, persona "loba"). Histórico do
estilista: Casa de Criadores, London Fashion Week, SPFW; já vestiu
Anitta, Luísa Sonza, Ludmilla, Xamã, Linn da Quebrada, Gloria Groove.
Parceria com Shakira começou em trabalho publicitário; processo de 4
meses na primeira versão. Aviso: novos figurinos seguirão até a
apresentação nas Pirâmides do Egito em 28/11. Tom de "brasilianidade
exportada"; orgulho nacional positivo. **Bloco único cobre os dois IDs
duplicados.**

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Estilista brasileiro com figurino internacional | Orgulho nacional; muito positivo. | muito positivo |
| Persona "loba" / estética da turnê | Reforça narrativa visual. | positivo |
| Continuidade Shakira × moda brasileira | Bandeira de soft power. | positivo |
| Carreira do estilista (Anitta, Ludmilla, Gloria Groove) | Legitimação. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-267 — A mobilização para receber as 10 toneladas de equipamentos

**Fonte:** O Globo / Coluna Ancelmo Gois (oglobo.globo.com)
**Data:** 25/04/2026 12:00 UTC
**URL:** https://oglobo.globo.com/blogs/ancelmo/post/2026/04/a-mobilizacao-para-receber-as-10-toneladas-de-equipamentos-para-o-show-de-shakira-no-rio.ghtml

### Resumo Narrativo

Nota curta sobre logística aérea: 10 toneladas de equipamentos da
turnê desembarcaram no RIOgaleão Cargo via Atlas e American Airlines,
com destino a Copacabana. Tom factual-positivo, "engenharia da turnê".

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Logística aérea (10 toneladas) | Apresentada como magnitude impressionante. | muito positivo |
| Operações Atlas + American Airlines | Citadas factualmente. | neutro |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-103 — Shakira no Rio: saiba quando, onde assistir e o que esperar

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 25/04/2026 14:12 UTC
**URL:** https://oglobo.globo.com/cultura/musica/noticia/2026/04/shakira-no-rio-saiba-quando-sera-onde-assistir-e-o-que-esperar-do-show-da-cantora-em-copacabana.ghtml

### Resumo Narrativo

Guia completo do show: dia, hora, palco (1.500 m², passarela 25 m, 500
m² LED, 16 torres), expectativa 2 milhões, transmissão TV Globo /
Multishow / Globoplay, repertório esperado (clássicos + Las Mujeres),
possível convidado (Anitta), gratuidade, frase de Shakira "maior
concerto da minha vida". Tom muito positivo, formato de utilidade
pública.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Cobertura "tudo que precisa saber" | Tom muito positivo. | muito positivo |
| Gratuidade do show | Reforço positivo. | muito positivo |
| Transmissão multi-plataforma | Inclusiva. | positivo |
| Setlist esperado e surpresas Anitta | Hype. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-96 — Quando Shakira chega ao RJ? Em finalização, palco vira ponto de encontro de fãs

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 25/04/2026 14:24 UTC
**URL:** https://oglobo.globo.com/cultura/noticia/2026/04/quando-shakira-chega-ao-rj-em-finalizacao-palco-vira-ponto-de-encontro-de-fas.ghtml

### Resumo Narrativo

Reportagem ricamente narrativa: 4.000 profissionais trabalhando há
quase um mês na praia; estrutura básica termina hoje, cenografia
começa amanhã (instalação pela equipe da artista); Shakira chega "a
qualquer momento a partir de segunda-feira"; testes de som/luz na
quarta; passagem de som na sexta com a artista; hospedagem no
Copacabana Palace, com corredor suspenso até o palco. Boca de cena
**56 m de largura, altura 26 m**, 2 a mais que Madonna/Lady Gaga; 680
m² de painéis móveis de LED; passarela com 2 elevadores ocultos. 60
toneladas de lastro em pedras. Entrevistados (Victor Madeira, morador;
Hugo Alexandre, anestesiologista de Fortaleza; Cynthia Silva, autônoma
de Belém) — dão tons humanos. Cynthia: "Tem gente reclamando só porque
Shakira não é uma popstar americana — Queria ver a Beyoncé? Queria,
claro… mas só de ser de graça já está ótimo." Tom muito positivo, com
nota sutil sobre crítica popular ("não é americana") sendo desautorizada.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Magnitude da operação (4.000 trabalhadores, 60 t lastro) | Tom muito positivo. | muito positivo |
| Estrutura técnica detalhada (56×26 m, 2 elevadores) | Reforço de mega-evento. | muito positivo |
| Engajamento popular (turistas no calçadão) | Indica antecipação positiva. | positivo |
| Crítica popular ("não é americana") | Mencionada e desautorizada pela entrevistada. | neutro |
| Logística do hotel-palco (corredor suspenso) | Detalhe positivo da operação. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-107 — Palco da Shakira vai ficar ainda maior; entenda

**Fonte:** G1 / GloboNews (g1.globo.com)
**Data:** 25/04/2026 16:40 UTC
**URL:** https://g1.globo.com/rj/rio-de-janeiro/musica/show-shakira-rj/noticia/2026/04/25/palco-da-shakira-vai-ficar-ainda-maior-entenda.ghtml

### Resumo Narrativo

Atualização confirmando ampliação a pedido da equipe da artista: palco
de 1.345 → **1.500 m²**, painéis LED de 500 → **680 m²**, altura
mantida em 2,20 m, boca de cena 56 m, passarela 25 m. Expectativa de 2
milhões. Tom positivo-factual.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Ampliação do palco a pedido da artista | Reforça aura de exigência/qualidade. | muito positivo |
| Painéis LED expandidos (500 → 680 m²) | Investimento em qualidade visual. | positivo |
| Reforço comparativo (maior que Madonna/Gaga) | Posicionamento competitivo. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-34 — Projeto Horto Maravilha prevê reformas em comunidade do Jardim Botânico

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 25/04/2026 18:25 UTC
**URL:** https://oglobo.globo.com/rio/noticia/2026/04/projeto-horto-maravilha-preve-reformas-em-comunidade-que-ha-pouco-ganhou-o-direito-de-permanecer-no-jardim-botanico.ghtml

### Resumo Narrativo

Artigo fora de escopo — não trata do show da Shakira. Cobre o projeto
"Horto Maravilha" (R$ 9 mi de investimento da prefeitura na comunidade
do Horto/Jardim Botânico) com presença do prefeito Cavaliere e do
vereador Flávio Valle. Shakira aparece apenas no rodapé "Notícias do
Rio: Show de Shakira terá pulseira de retorno do metrô" e em link
relacionado sobre incidente trágico ("técnico que acionou botão que
causou morte de serralheiro em montagem para show de Shakira poderá
responder por homicídio culposo"). Capturado pelo tag de Flávio Valle.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| (Tema Shakira) | Aparece apenas em sidebar/rodapé. | n/a |

### Classificação Geral

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo**: trata do projeto Horto Maravilha; menção a Shakira é incidental. Bloco mantido por integridade do protocolo. **Note**: o link do rodapé revela existência de morte de serralheiro durante montagem do palco — fato grave que aparecerá em outros artigos do corpus (a buscar a-NNN específico).

---

## a-268 — (já coberto em a-269) Estilista brasileiro Dario Mitmann

Bloco redirecionador. O conteúdo de `a-268` é byte-identico ao de `a-269` (mesma matéria, IDs duplicados pela ingestão dual). Análise completa em `a-269` acima. **Sentimento geral do artigo:** muito positivo.

---

## a-266 — A uma semana de show, Shakira manda recado: 'Quase lá, Rio!'

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 25/04/2026 18:49 UTC
**URL:** https://oglobo.globo.com/cultura/musica/noticia/2026/04/a-uma-semana-de-show-na-praia-de-copacabana-shakira-manda-recado-para-os-fas-quase-la-rio.ghtml

### Resumo Narrativo

Shakira posta nas redes: "Quase lá, Rio! Preparando muitas surpresas:
artistas convidados, figurino novo, músicas que vocês vão adorar… no
altar do planeta!" Anitta curtiu. Mais de 100 mil curtidas. Recap das
dimensões do palco e gratuidade. Tom muito positivo.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Engajamento direto Shakira × fãs | Tom muito positivo. | muito positivo |
| Surpresas teasing (Anitta, figurino) | Hype crescente. | muito positivo |
| Recap palco/gratuidade | Reforço positivo. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-234 — Faixa em Botafogo avisa que acesso a Copacabana fechará às 18h

**Fonte:** G1 (g1.globo.com)
**Data:** 25/04/2026 19:15 UTC
**URL:** https://g1.globo.com/rj/rio-de-janeiro/musica/show-shakira-rj/noticia/2026/04/25/shakira-no-rio-faixa-em-botafogo-avisa-que-acesso-a-copacabana-fechara-as-18h.ghtml

### Resumo Narrativo

Faixa na Rua Pinheiro Guimarães (Botafogo) anuncia bloqueio de carros,
ônibus e motos a Copacabana às 18h do dia 2/05. Coletiva de imprensa do
prefeito Cavaliere e Riotur (Bernardo Fellows) marcada para 28/04. Recap
palco 1.500 m². Tom factual, positivo.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Bloqueio de acesso veicular (18h) | Sinalizado factualmente; logística adequada. | positivo |
| Coletiva oficial Prefeitura/Riotur | Comunicação institucional positiva. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-265 — Bebel Gilberto sonha em fazer parceria com Shakira

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 25/04/2026 20:17 UTC
**URL:** https://oglobo.globo.com/cultura/noticia/2026/04/e-esse-feet-bebel-gilberto-sonha-em-fazer-parceria-com-shakira.ghtml

### Resumo Narrativo

Nota cultural: Bebel Gilberto, em caixinha de perguntas no Instagram,
diz sonhar em fazer feat com Shakira ("ela me elogiou uma vez nos
Rolling Stones"). Bebel também elogia Anitta pela regravação de
"Cordeiro de Nanã" do pai João Gilberto. Tom positivo, fofo. Tangencial
ao show específico mas in-scope (Shakira-cultura).

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Reconhecimento de Shakira por Bebel Gilberto | Positivo, bilateral. | positivo |
| Cultura latina/brasileira em diálogo | Soft power positivo. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-274 — Show celebra a carreira de artista que abriu caminhos para o boom da música latina

**Fonte:** O Globo / Silvio Essinger (oglobo.globo.com)
**Data:** 26/04/2026 06:31 UTC
**URL:** https://oglobo.globo.com/cultura/musica/noticia/2026/04/shakira-no-rio-show-em-copacabana-celebra-a-carreira-de-artista-que-abriu-caminhos-o-atual-boom-da-musica-latina.ghtml

### Resumo Narrativo

Reportagem-perfil cultural muito rica de Silvio Essinger. Posiciona
Shakira como a artista que "abriu caminho" para o boom latino atual
(Bad Bunny, Karol G). Recapitula: "Hips don't lie" (2006), "Bzrp Music
Sessions Vol. 53" (2023, pós-Piqué) e "Las mujeres ya no lloran" (2024,
13º na parada americana, 1º em pop latino). Cita declaração de Niemeyer
(Bonus Track) sobre "latinidade" como valor curatorial e Bad Bunny no
Super Bowl como contexto. Estima 500 mil turistas no fim de semana,
"versão intensificada" de plano de segurança (mais câmeras de
reconhecimento facial, mais pessoas para revista). Tom muito positivo,
com profundidade jornalística.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Shakira como pioneira do boom latino global | Reverência cultural; muito positivo. | muito positivo |
| Rolagem da carreira (1995→2024) | Tom celebratório. | muito positivo |
| Latinidade como valor curatorial do Todo Mundo no Rio | Posicionamento positivo. | muito positivo |
| Estimativa de 500 mil turistas / segurança intensificada | Logística positiva, aviso de câmeras de reconhecimento facial. | positivo |
| Era pós-Piqué / superação | Reforça narrativa de empoderamento. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-273 — 'Hips don't lie' ou 'Girl like me'? Shakira pergunta qual música os fãs querem

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 26/04/2026 13:10 UTC
**URL:** https://oglobo.globo.com/cultura/musica/noticia/2026/04/hips-dont-lie-ou-girl-like-me-shakira-pergunta-qual-musica-fas-querem-ouvir-no-show-em-copacabana.ghtml

### Resumo Narrativo

Shakira faz enquete no Instagram em português ("Brasil, o que vocês
querem ouvir?") com 4 opções: "Hips don't lie", "Chantaje", "Can't
remember to forget you", "Girl like me". Recap palco/transmissão.
Engajamento positivo direto.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Engajamento bilateral artista × fãs | Muito positivo. | muito positivo |
| Recap padrão (palco/setlist) | Reforço. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-272 — Shakira 'vai' às compras na Saara, mas divulga show com réplica de leque

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 26/04/2026 13:58 UTC
**URL:** https://oglobo.globo.com/rio/noticia/2026/04/shakira-vai-as-compras-na-saaramas-divulga-show-com-replica-de-leque-entenda.ghtml

### Resumo Narrativo

Note cultural-curiosa: a equipe de Shakira encomendou 15 itens da loja
Lix (Saara) para Miami; o leque que Shakira mostra nas redes é
réplica/cópia, não original (não chegou a tempo). Lorrana Lica (dona da
Lix) reconhece o engano mas valoriza a divulgação. 5 dos 15 itens são
leques "lobacabana"; outros 10 "para se vestir". Tom positivo-comercial.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Comércio Saara × marketing internacional | Positivo, "soft power" comercial. | positivo |
| Leque "lobacabana" como símbolo | Rede de fãs apropria fenômeno. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-115 — Shakira exalta mulheres latinas e dedica show a elas (artigo no O Globo)

**Fonte:** G1 (g1.globo.com) — sobre artigo de Shakira no Jornal O Globo
**Data:** 26/04/2026 14:27 UTC
**URL:** https://g1.globo.com/rj/rio-de-janeiro/musica/show-shakira-rj/noticia/2026/04/26/shakira-exalta-mulheres-latinas-e-diz-que-show-em-copacabana-sera-dedicado-a-elas.ghtml

### Resumo Narrativo

G1 cobre artigo "Chorar já não basta" assinado por Shakira no Jornal O
Globo de domingo (26/04). Shakira exalta a "garra das mulheres latinas",
diz ter se surpreendido com o número de lares brasileiros chefiados por
mulheres ("mais de 40 milhões"), e dedica o show de 2 de maio a essas
mulheres. Compara Copacabana ao "altar do planeta" — "se o planeta
Terra tivesse um altar capaz de falar por si só, esse altar seria
Copacabana". Tom muito positivo, retórica de empoderamento feminino e
amor pelo Rio.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Empoderamento feminino latino-americano | Tom celebratório. | muito positivo |
| Identificação com mulheres brasileiras chefes de lar | Aproximação afetiva. | muito positivo |
| Copacabana como "altar do planeta" | Posicionamento aspiracional. | muito positivo |
| Show dedicado às mulheres latinas | Reforça narrativa social. | muito positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-271 — Fãs de Shakira reúnem-se em Copacabana para aprender coreografia de 'Waka Waka'

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 26/04/2026 14:56 UTC
**URL:** https://oglobo.globo.com/rio/noticia/2026/04/copacabana-vira-pista-de-danca-antes-de-show-de-shakira-e-fas-encaram-calor-para-aprender-passos-de-waka-waka.ghtml

### Resumo Narrativo

Reportagem-cobertura das aulas gratuitas de "Waka Waka" no Posto 3
(domingo 26/04, dois horários). Cerca de 60 pessoas resistem ao calor
de 30°C+. Professores Esther Lobo e Christian Bazano. Entrevistadas/os
ricos: Júlia Mello (cientista, fã desde criança, aprendeu espanhol com
Shakira), Thalia Cruz (fã exclusiva da música em espanhol), Paulo Reis
(mineiro residente no Rio há 10 anos, "presente de aniversário desses
anos no Rio"), Luciene Batista (48 anos, "se soltar"). Tom muito
positivo, comunidade-celebração.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Engajamento comunitário pré-show (aulas gratuitas) | Muito positivo. | muito positivo |
| Identificação cultural Shakira × fãs brasileiros | Profunda, multifacetada. | muito positivo |
| Inclusão (idades 28-48, várias regiões) | Diversidade positiva. | muito positivo |
| Calor extremo (30°C+) como obstáculo | Mencionado mas superado pelos fãs. | neutro |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-130 — Shakira no Rio: imagens da montagem do palco

**Fonte:** CNN Brasil (cnnbrasil.com.br)
**Data:** 26/04/2026 18:45 UTC
**URL:** https://www.cnnbrasil.com.br/entretenimento/shakira-no-rio-veja-imagens-da-montagem-do-palco-do-show-em-copacabana/

### Resumo Narrativo

CNN Brasil confirma com Bonus Track: estrutura 1.500 m² (vs 1.345 m²
anunciado anteriormente). 56 m altura total (não 26 m da boca de cena —
provável erro editorial), passarela 25 m, 16 telões de 45 m². 10
toneladas de equipamentos chegaram via Atlas e American Airlines. Show
apelidado "Lobacabana" pela própria cantora.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Recap de estrutura recorde | Tom muito positivo. | muito positivo |
| Logística aérea (10 t equipamentos) | Reforço. | positivo |
| Alcunha "Lobacabana" | Marketing positivo. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-270 — Funcionário morre após acidente durante montagem do palco do show da Shakira

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 26/04/2026 21:07 UTC
**URL:** https://oglobo.globo.com/rio/noticia/2026/04/funcionario-morre-apos-acidente-durante-montagem-do-show-da-shakira-em-copacabana.ghtml

### Resumo Narrativo

**Tragédia.** O serralheiro **Gabriel de Jesus Firmino, 28 anos**,
morreu na tarde de 26/04 durante a montagem do palco em Copacabana,
**esmagado por parte de uma estrutura** (sistema de elevação, segundo o
Corpo de Bombeiros). Socorrido ao Hospital Municipal Miguel Couto
(Gávea), não resistiu. Caso será investigado pela 12ª DP (Copacabana).
Vídeo nas redes sociais mostra colegas tentando socorrer com maquinário
hidráulico. Bonus Track lamentou em nota, "prestando todo apoio,
acolhimento e solidariedade à empresa responsável, sua equipe e aos
familiares da vítima". A reportagem fecha mencionando a magnitude do
palco (1.500 m², "quase o dobro do de Madonna") — composição editorial
que **justapõe** a tragédia ao espetáculo.

Este é o **primeiro evento muito negativo** do corpus. Marca uma virada
ética na cobertura: a empolgação midiática até aqui não tinha
contraponto humano profundo; agora, há uma morte vinculada à produção.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Morte do serralheiro Gabriel de Jesus Firmino | Reportagem factual; tom respeitoso/sério. | muito negativo |
| Segurança do trabalho na montagem do palco | Falha mortal exposta. | muito negativo |
| Resposta da Bonus Track (nota de pesar e apoio) | Reativa, sem assumir falha. | neutro |
| Investigação policial (12ª DP) | Apenas anunciada. | neutro |
| Magnitude do palco como contexto editorial | Justaposição inquietante. | neutro |

### Classificação Geral

**Sentimento geral do artigo:** muito negativo

---

## a-282 — Ipanema: Garcia D'Ávila vira 'calçadão' de luxo (off-scope)

**Fonte:** Veja Rio Archive (vejario.abril.com.br)
**Data:** 27/04/2026 06:30 UTC (data do snapshot; conteúdo é de 06/06/2025)
**URL:** https://vejario.abril.com.br/coluna/lu-lacerda/ipanema-garcia-davila-vira-calcadao-luxo-aposta-reurbanizacao-crise/

### Resumo Narrativo

Artigo fora de escopo — não trata do show da Shakira. Cobre projeto de
reurbanização da Rua Garcia D'Ávila (Ipanema) com calçadas alargadas e
fim das vagas, articulado pelo vereador Flávio Valle. Captura via tag
de Flávio Valle. Título do snapshot estava mal-classificado.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| (Tema Shakira) | Não aparece. | n/a |

### Classificação Geral

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo**: matéria sobre Ipanema/Garcia D'Ávila; não trata de Shakira.

---

## a-281 — Shakira deve movimentar economia carioca em quase R$ 800 milhões

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 27/04/2026 07:30 UTC
**URL:** https://oglobo.globo.com/rio/noticia/2026/04/shakira-deve-movimentar-economia-carioca-em-quase-r-800-milhoes-entenda.ghtml

### Resumo Narrativo

Estudo da Secretaria de Desenvolvimento Econômico + Riotur projeta
**R$ 776,2 milhões de impacto econômico**. Distribuição: 13,9% turistas
nacionais (278 mil), 1,6% internacionais (32 mil), 84,6% cariocas/RM
(1,7 mi). Ticket médio R$ 547,30/dia (BR), R$ 626,40/dia (estrangeiro), R$ 141,75/dia (local). Mídia espontânea estimada em US$ 250 milhões (~R$ 1,3 bi). Cita declaração de Shakira no Fantástico ("Copacabana, para mim, é um sonho"). Tom muito positivo, governamental.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Impacto econômico (R$ 776 mi) | Apresentado como sucesso. | muito positivo |
| Mídia espontânea internacional (US$ 250 mi) | Reforça posicionamento global. | muito positivo |
| Distribuição de público | Maioria carioca (84,6%). | positivo |
| Custo público (R$ 15 mi) | Citado factualmente. | neutro |
| Declaração de Shakira ("altar") | Engajamento afetivo. | muito positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-127 — Shakira no Rio deve movimentar R$ 800 milhões, impacto maior que Madonna e Lady Gaga

**Fonte:** G1 / GloboNews (g1.globo.com)
**Data:** 27/04/2026 08:41 UTC
**URL:** https://g1.globo.com/rj/rio-de-janeiro/musica/show-shakira-rj/noticia/2026/04/27/shakira-no-rio-deve-movimentar-r-800-milhoes-impacto-maior-que-os-dos-shows-de-madonna-e-lady-gaga.ghtml

### Resumo Narrativo

GloboNews replica e amplia o estudo: **R$ 776,2 mi** vs. **R$ 469 mi
(Madonna 2024)** e **R$ 592 mi (Lady Gaga 2025)** — recorde da série
Todo Mundo no Rio. Inclui depoimento de Niemeyer ("Shakira já colocou
esse evento como um altar da música"), de Cavaliere ("posicionamento
internacional"), e da empresária Jaqueline Cascardo (camisetas, +30%).
Tom muito positivo.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Impacto econômico recorde (R$ 776 mi vs. histórico) | Tom muito positivo. | muito positivo |
| Geração de empregos (4.000 na montagem) | Reforço positivo. | muito positivo |
| Pequenos negócios beneficiados | Inclusão econômica. | positivo |
| Estratégia de eventos como política pública | Apresentada positivamente. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-280 — Rua Arnaldo Quintela em Botafogo (off-scope)

**Fonte:** Veja Rio Archive (vejario.abril.com.br)
**Data:** 27/04/2026 11:48 UTC (snapshot; conteúdo de 04/11/2025)
**URL:** https://vejario.abril.com.br/coluna/lu-lacerda/arnaldo-quintela-pode-ganhar-projeto-requalificacao-urbana/

### Resumo Narrativo

Artigo fora de escopo. Trata de projeto de requalificação urbana da Rua
Arnaldo Quintela em Botafogo, articulado pelo vereador Flávio Valle.
Captura via tag.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| (Tema Shakira) | Não aparece no corpo do texto. | n/a |

### Classificação Geral

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo**.

---

## a-279 — 'Horror', 'Tragédia': imprensa internacional destaca morte de trabalhador

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 27/04/2026 13:52 UTC
**URL:** https://oglobo.globo.com/cultura/noticia/2026/04/tragico-horrivel-imprensa-internacional-destaca-morte-de-trabalhador-em-palco-de-shakira-no-rio.ghtml

### Resumo Narrativo

Repercussão internacional da morte de **Gabriel de Jesus Firmino**:
The Sun (UK) "Horror no palco", Page Six (US) "acidente horrível", NME
e News AZ (Azerbaijão) "trágico", France 24 e ENews citando AFP,
Toronto Sun (Canadá) reproduzindo notas oficiais, People reportando
silêncio inicial da Bonus Track. A reportagem documenta como a
tragédia ofuscou a expectativa internacional pelo show — primeira
peça do corpus a tratar a morte como **fato editorial dominante** na
cobertura externa.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Morte do serralheiro Gabriel Firmino | Tom respeitoso, factual. | muito negativo |
| Repercussão internacional negativa | Imprensa global enquadra como tragédia. | muito negativo |
| Silêncio inicial da Bonus Track na imprensa estrangeira | Crítica implícita à comunicação da produtora. | negativo |

### Classificação Geral

**Sentimento geral do artigo:** muito negativo

---

## a-94 — Prefeitura: show terá impacto econômico de R$ 800 mi

**Fonte:** Riotur — site oficial (riotur.rio)
**Data:** 27/04/2026 14:07 UTC
**URL:** https://riotur.rio/noticias/shakira-impacto-economico

### Resumo Narrativo

Comunicado oficial da Prefeitura/Riotur ratificando o estudo "Potenciais
Impactos Econômicos do Todo Mundo no Rio 2026 – Shakira": R$ 776,2 mi de
movimentação, 2 mi de público, US$ 250 mi de mídia espontânea, soma com
edições anteriores R$ 2,7 bi de visibilidade. Cita Cavaliere, Bernardo
Fellows (Riotur), e o secretário Osmar Lima. Inclui dados de
arrecadação ISS (maio 2025: R$ 66,8 mi vs. maio 2023: R$ 54,3 mi). Tom
oficial-celebratório, "vitrine global".

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Comunicação institucional do impacto econômico | Tom institucional positivo. | muito positivo |
| Arrecadação ISS turística (+23,2% real) | Validação fiscal do investimento. | muito positivo |
| Estratégia plurianual (2024-2028) | Continuidade reforçada. | positivo |
| UNESCO Patrimônio Mundial | Reforço aspiracional. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-278 — Após morte de operário, Polícia Civil realiza perícia

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 27/04/2026 14:20 UTC
**URL:** https://oglobo.globo.com/rio/noticia/2026/04/apos-morte-de-operario-durante-montagem-de-palco-para-show-de-shakira-em-copacabana-policia-civil-realiza-pericia.ghtml

### Resumo Narrativo

Reportagem detalhada da perícia da 12ª DP, com depoimento do delegado
Ângelo Lages: dois elevadores adjacentes, vítima soldando entre eles
quando elevador 1 subiu e a estrutura inferior esmagou Gabriel sobre o
elevador 2 (espaço de 6 cm). "Foi uma morte muito cruel." Norma de
segurança proibia operação com funcionário dentro. Bonus Track (Cenoart
/ MG Coutinho como subcontratada) pode responder por homicídio culposo
ou omissão. Local desinterditado e montagem retomada após perícia.
Apenas um produtor executivo da Bonus Track prestou depoimento. Tom
factual-investigativo, sério.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Perícia oficial e investigação policial | Tom rigoroso. | negativo |
| Possível homicídio culposo / omissão | Crítica grave à segurança do trabalho. | muito negativo |
| Subcontratação (Bonus Track → MG Coutinho/Cenoart) | Cadeia de responsabilidade exposta. | negativo |
| Detalhes graves do acidente (esmagamento, gritos) | Tratamento humano-respeitoso. | muito negativo |

### Classificação Geral

**Sentimento geral do artigo:** muito negativo

---

## a-28 — Muro da Praça Sarah Kubitschek demolido (off-scope)

**Fonte:** Tempo Real (tempo-real.com)
**Data:** 27/04/2026 15:09 UTC
**URL:** https://tempo-real.com/post/muro-da-praca-sarah-kubitschek-e-demolido-em-copacabana/

### Resumo Narrativo

Artigo fora de escopo. Trata da demolição do muro da Praça Sarah
Kubitschek em Copacabana (vereador Flávio Valle). Shakira aparece
apenas em sidebar "Você pode gostar" + artigo anterior referenciado no
título ("Todo Mundo no Rio até 2028: prefeitura garante investimento de
R$ 45 milhões para Shakira e outros megashows").

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| (Tema Shakira) | Aparece apenas em sidebar. | n/a |

### Classificação Geral

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo**.

---

## a-97 — Riotur (rep): show prevê impacto de R$ 800 mi (replicado)

**Fonte:** Riotur — site oficial (riotur.rio)
**Data:** 27/04/2026 15:58 UTC
**URL:** https://riotur.rio/noticias/shakira-impacto-economico-rio (re-publicação)

### Resumo Narrativo

Replicação do comunicado oficial Riotur (mesmo conteúdo de `a-94`),
publicado novamente algumas horas depois. Mesmos números, mesmas
declarações. Bloco mantido por integridade do protocolo. Marca o caso
de **republicação institucional** quando o veículo é o próprio
ente público.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Comunicação institucional repetida | Mesma análise de `a-94`. | muito positivo |

### Classificação Geral

**Sentimento geral do artigo:** muito positivo

---

## a-277 — Operário deixa mulher e dois filhos; perícia segue

**Fonte:** O Globo (oglobo.globo.com)
**Data:** 27/04/2026 20:00 UTC
**URL:** https://oglobo.globo.com/rio/noticia/2026/04/operario-que-morreu-durante-montagem-de-palco-para-show-de-shakira-deixa-mulher-e-dois-filhos.ghtml

### Resumo Narrativo

Reportagem segue cobrindo a tragédia com o ângulo humano: Gabriel de
Jesus Firmino, 28 anos, natural de Magé, deixa mulher (26 anos) e dois
filhos. Funcionário da MG Coutinho Serviços Cenográficos (Cenoart) há
mais de três anos. Detalhes da perícia repetidos. Inclui declaração
nova: **"Shakira entrou em contato com a organização assim que soube
do ocorrido e tem mantido contato constante com nossa equipe… está
muito profundamente comovida"** (Bonus Track). MG Coutinho não
respondeu. Tom respeitoso, humano.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| Detalhes humanos da vítima (família, origem) | Tom respeitoso. | muito negativo |
| Resposta de Shakira ("profundamente comovida") | Humaniza o lado da artista. | neutro |
| Subcontratação Cenoart | Foco na responsabilidade trabalhista. | negativo |
| Contraste com magnitude do palco | Justaposição editorial inquietante. | negativo |

### Classificação Geral

**Sentimento geral do artigo:** muito negativo

---

## a-276 — Ex-BBB Samira na cobertura do show para Multishow/Globoplay

**Fonte:** O Globo (oglobo.globo.com)  **Data:** 27/04/2026 20:01 UTC
**URL:** https://oglobo.globo.com/cultura/noticia/2026/04/ex-bbb-samira-vai-participar-de-cobertura-de-megashow-de-shakira-para-multishow-e-globoplay.ghtml

### Resumo Narrativo

Ex-BBB 26 Samira anunciada na cobertura do show pela Multishow/Globoplay,
com vídeo trocadilho usando seus chorôs no reality e o refrão "Las
mujeres ya no lloran, las mujeres facturan". Marketing de transmissão.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---|---|
| Cross-promo Globo (Samira × Shakira) | Marketing positivo. | positivo |
| Transmissão Multishow/Globoplay | Reforço alcance. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-165 — Shakira está 'comovida' com morte de serralheiro, diz produtora

**Fonte:** G1 (g1.globo.com)  **Data:** 27/04/2026 20:30 UTC
**URL:** https://g1.globo.com/rj/rio-de-janeiro/musica/show-shakira-rj/noticia/2026/04/27/shakira-esta-comovida-com-morte-de-serralheiro-em-montagem-do-palco-em-copacabana-diz-produtora.ghtml

### Resumo Narrativo

GloboNews/G1 amplifica a nota da Bonus Track sobre Shakira "comovida".
Detalhes técnicos da perícia: elevador acionado a 25 m de distância;
vítima estava dentro do equipamento (proibido por norma de segurança).
Bonus Track diz que cronograma segue. Polícia investiga homicídio
culposo. Tom muito negativo.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---|---|
| Resposta institucional Shakira/Bonus Track | Tom de respeito. | neutro |
| Detalhes da negligência (elevador a 25m) | Crítica grave. | muito negativo |
| Investigação policial em curso | Sério. | negativo |

### Classificação Geral

**Sentimento geral do artigo:** muito negativo

---

## a-275 — Cuidados para não perder documentos no show

**Fonte:** O Globo (oglobo.globo.com)  **Data:** 27/04/2026 21:56 UTC
**URL:** https://oglobo.globo.com/rio/noticia/2026/04/shakira-em-copacabana-veja-os-cuidados-para-nao-perder-documentos.ghtml

### Resumo Narrativo

Nota utilitária do 15º Ofício de Notas: levar cópias autenticadas em
vez de originais para evitar transtornos com furto. Para crianças,
Autorização de Viagem para Menores. Tom positivo-utilidade.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---|---|
| Orientação anti-furto | Preventiva positiva. | positivo |
| Aglomerações como risco | Reconhecido factualmente. | neutro |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-35 / a-9 — Painel de Millôr Fernandes em muro demolido (Sarah Kubitschek) (off-scope)

**Fonte:** O Globo (a-35) / Extra (a-9), mesma matéria por Henrique Barbi
**Datas:** 28/04/2026 08:03 / 10:00 UTC
**URLs:** oglobo.globo.com/.../painel-de-millor-fernandes... / extra.globo.com/...

### Resumo Narrativo

Artigo fora de escopo — duplicado em dois IDs, mesmo conteúdo. Trata da
demolição do muro da Praça Sarah Kubitschek (Copacabana) e replicação
do mural de Millôr Fernandes em escola, articulada por Flávio Valle.
Shakira aparece em sidebar. Bloco único cobre os dois IDs.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---|---|
| (Tema Shakira) | Sidebar apenas. | n/a |

### Classificação Geral

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo** (revitalização Praça Sarah Kubitschek). Bloco cobre `a-35` + `a-9`.

---

## a-39 / a-11 — Bar Partisan na Lapa cassado (off-scope)

**Fonte:** Tempo Real (a-39) / O Dia (a-11)
**Datas:** 28/04/2026 11:56 / 12:46 UTC
**URLs:** tempo-real.com/.../prefeitura-do-rio-cancela-registro... / odia.ig.com.br/.../bar-na-lapa-tem-cadastro-cancelado...

### Resumo Narrativo

Artigos fora de escopo — duas variações da mesma cobertura. Cancelamento
do alvará do Bar Partisan na Lapa após placa antissemita/contra-EUA;
articulação do vereador Flávio Valle. Captura via tag.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---|---|
| (Tema Shakira) | Não aparece no corpo. | n/a |

### Classificação Geral

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo**. Bloco cobre `a-39` + `a-11`.

---

## a-227 — Show de Shakira terá reforço de quase 8 mil agentes

**Fonte:** G1 (g1.globo.com)  **Data:** 28/04/2026 15:01 UTC
**URL:** https://g1.globo.com/rj/rio-de-janeiro/musica/show-shakira-rj/noticia/2026/04/28/show-de-shakira-tera-reforco-no-policiamento-com-quase-8-mil-agentes.ghtml

### Resumo Narrativo

Detalhamento do esquema de segurança pelo Governo RJ: **7.927 agentes**
(3.700 PMs +14% vs Lady Gaga; 2.200 guardas municipais; 1.500 polícia
civil; 176 bombeiros; 150 Segurança Presente; 110 Lei Seca). 18 pontos
de interceptação com detectores de metal e reconhecimento facial. 78
torres de observação, 6 drones, 175 viaturas. Operação Tatuí (busca de
material cortante na areia) começa 29/04. Lista de 16 vias bloqueadas
("ninguém passa") e 16 vias de acesso. Tom factual-positivo, "operação
de réveillon".

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---|---|
| Segurança pública massiva (7.927 agentes) | Apresentada como reforço positivo. | positivo |
| Câmeras de reconhecimento facial e drones | Tecnologia de ponta. | positivo |
| Bloqueios extensos de vias | Restrição inevitável; tom factual. | neutro |
| Operação Tatuí (revista da areia) | Preventivo positivo. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-288 — Momo Gelato cria sabor em homenagem a Shakira

**Fonte:** O Globo / Coluna Saideira (oglobo.globo.com)  **Data:** 28/04/2026 17:34 UTC
**URL:** https://oglobo.globo.com/blogs/saideira/post/2026/04/momo-gelato-cria-sabor-em-homenagem-a-shakira.ghtml

### Resumo Narrativo

Momo Gelato lança gelato "Shakira no Rio" (R$ 27 / 100 g) com cacau e
café colombianos + brigadeiro. Disponível na unidade Copacabana Palace
(perto do palco) e demais lojas do Rio. Tom positivo-promocional.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---|---|
| Comércio criativo aproveitando o show | Positivo, "marketing local". | positivo |
| Diálogo Brasil × Colômbia (cacau/café/brigadeiro) | Soft power gastronômico. | positivo |

### Classificação Geral

**Sentimento geral do artigo:** positivo

---

## a-26 — Prefeitura volta atrás na cassação do Bar Partisan (off-scope)

**Fonte:** O Globo (oglobo.globo.com)  **Data:** 28/04/2026 17:59 UTC
**URL:** https://oglobo.globo.com/rio/noticia/2026/04/apos-cassar-alvara-de-funcionamento-de-bar-na-lapa-em-que-teve-aviso-contra-clientes-de-eua-e-israel-prefeitura-volta-atras.ghtml

### Resumo Narrativo

Artigo fora de escopo — atualização do caso Bar Partisan. Prefeitura
voltou atrás na cassação do alvará após recurso. Shakira aparece
apenas em sidebar/links relacionados.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---|---|
| (Tema Shakira) | Sidebar apenas. | n/a |

### Classificação Geral

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo**.

---

## a-287 — Pedro Angelito assume Subprefeitura da Zona Sul (off-scope)

**Fonte:** O Globo Zona Sul (oglobo.globo.com)
**Data:** 28/04/2026 18:17 UTC (snapshot; conteúdo de 05/02/2026)
**URL:** https://oglobo.globo.com/rio/zona-sul/noticia/2026/02/novo-subprefeito-da-zona-sul-diz-que-populacao-em-situacao-de-rua-sera-o-principal-foco-de-sua-gestao.ghtml

### Resumo Narrativo

Artigo fora de escopo — perfil do novo subprefeito da Zona Sul Pedro
Angelito (foco em população em situação de rua). Shakira não
mencionada. Captura via tag de Flávio Valle / Pedro Angelito.

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---|---|
| (Tema Shakira) | Não aparece. | n/a |

### Classificação Geral

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo**.

---

## a-9 — (= a-35) Painel Millôr Fernandes (off-scope)

Mesma matéria de `a-35`. Bloco redirecionador. **Sentimento geral do artigo:** N/A — fora de escopo.

---

## a-11 — (= a-39) Bar Partisan na Lapa cassado (off-scope)

Mesma matéria de `a-39`. Bloco redirecionador. **Sentimento geral do artigo:** N/A — fora de escopo.

---

## a-286 — Sony Music: promoção VIP para 100 fãs

**Fonte:** O Globo (oglobo.globo.com)  **Data:** 28/04/2026 19:24 UTC

Sony Music Brasil oferece 100 vagas VIP via cadastro em vamoscomlaloba.com.br (texto sobre admiração por Shakira). Inscrições 14h 28/04 — 14h 30/04. Marketing VIP positivo.

| Tema | Como é tratado | Classificação |
|---|---|---|
| Promoção VIP via gravadora | Marketing positivo. | positivo |
| Engajamento de fãs (texto) | Inclusão criativa. | positivo |

**Sentimento geral do artigo:** positivo

---

## a-285 — Taxistas poderão cobrar preços fixos pós-show

**Fonte:** O Globo (oglobo.globo.com)  **Data:** 28/04/2026 19:26 UTC

Prefeitura tabela tarifas fixas (R$ 35 a R$ 361 conforme destino) para corridas de táxi do bolsão da Rua Siqueira Campos pós-show, das 24h de 02/05 às 6h de 03/05. Evita preços abusivos. Tom positivo-utilidade pública.

| Tema | Como é tratado | Classificação |
|---|---|---|
| Tabelamento anti-abuso | Regulação positiva. | positivo |
| Logística pós-show | Organização preventiva. | positivo |

**Sentimento geral do artigo:** positivo

---

## a-284 — Rodrigo Lemos é o novo presidente da Ocyan (off-scope)

**Fonte:** Petronotícias (petronoticias.com.br)  **Data:** 28/04/2026 20:24 UTC (snapshot; conteúdo de 02/04/2025)

Artigo fora de escopo — não trata do show. Notícia corporativa de óleo & gás (presidência da Ocyan), capturada por homonímia com "Flávio Valle" (presidente do Conselho da Ocyan, mesmo nome do vereador, pessoas distintas).

| Tema | Como é tratado | Classificação |
|---|---|---|
| (Tema Shakira) | Não aparece. | n/a |

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo** (confusão de homonímia "Flávio Valle"; pessoa diferente do vereador).

---

## a-15 — Comissão sobre veículos elétricos (off-scope)

**Fonte:** Tempo Real (tempo-real.com)  **Data:** 28/04/2026 20:43 UTC

Artigo fora de escopo — disputa interna do PSD na Câmara do Rio. Shakira não mencionada.

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo**.

---

## a-283 — Paes recua sobre garrafas de vidro nos quiosques (off-scope)

**Fonte:** O Globo (oglobo.globo.com)  **Data:** 28/04/2026 20:55 UTC (snapshot; conteúdo de 27/05/2025)

Artigo fora de escopo — regulamentação de quiosques na orla, anterior ao show. Shakira não mencionada.

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo**.

---

## a-25 — Seop suspende cancelamento do Bar Partisan (off-scope)

**Fonte:** O Dia (odia.ig.com.br)  **Data:** 29/04/2026 01:19 UTC

Artigo fora de escopo — atualização do caso Bar Partisan (Seop recua). Shakira em sidebar.

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo**.

---

## a-232 — Quando, que horas e onde assistir ao show

**Fonte:** Gshow (gshow.globo.com)  **Data:** 29/04/2026 03:00 UTC

Recap final pré-show: dia 02/05, Praia de Copacabana, transmissão TV Globo após novela Três Graças, Globoplay/Multishow a partir das 21h20. Apresentadores: Ana Clara, Dedé Teicher, Kenya Sade, Laura Vicente. Tom positivo.

| Tema | Como é tratado | Classificação |
|---|---|---|
| Cobertura multi-plataforma Globo | Reforço positivo. | muito positivo |
| Programação detalhada | Engajamento positivo. | positivo |

**Sentimento geral do artigo:** positivo

---

## a-155 — Quem vai abrir o show: DJ Maz e Vintage Culture

**Fonte:** G1 / GloboNews (g1.globo.com)  **Data:** 29/04/2026 08:49 UTC

GloboNews revela exclusivo: DJ Maz (afro-house, 2,5 mi ouvintes/mês Spotify) e Vintage Culture (eletrônica, 8 mi ouvintes/mês) farão o esquenta na areia. Patrocínio Corona via Sunset. Tom positivo.

| Tema | Como é tratado | Classificação |
|---|---|---|
| Abertura com brasileiros (DJ Maz, Vintage Culture) | Soft power nacional. | muito positivo |
| Continuidade da fórmula Corona Sunset | Patrocínio reforça. | positivo |

**Sentimento geral do artigo:** muito positivo

---

## a-44 — Seop recua e cancela punição ao bar Partisan (off-scope)

**Fonte:** Tempo Real (tempo-real.com)  **Data:** 29/04/2026 10:23 UTC

Artigo fora de escopo — Seop recua após recurso do bar. Shakira em sidebar.

**Sentimento geral do artigo:** N/A — **Artigo fora de escopo**.

---

## a-649 / a-21 — Câmara do Rio aprova plataforma de apoio a mulheres vítimas de violência (off-scope)

**Fontes:** Câmara Municipal do Rio (a-649) e re-publicação (a-21). 29/04/2026.

Artigos fora de escopo — não tratam do show. Aprovação de plataforma digital municipal. Capturados via tag de Flávio Valle. Bloco único cobre os dois IDs.

**Sentimento geral do artigo:** N/A — **Artigos fora de escopo**.

---

## a-98 — Shakira chega ao Rio para show e faz 'coração' para fãs

**Fonte:** G1 (g1.globo.com)  **Data:** 29/04/2026 13:51 UTC

Shakira desembarca no Rio na quarta-feira pré-show, faz "coração" para fãs em registro do TV Globo. Pequena mas afetiva nota. Tom muito positivo.

| Tema | Como é tratado | Classificação |
|---|---|---|
| Chegada da artista no Rio | Tom muito positivo. | muito positivo |
| Engajamento de fãs no aeroporto | Positivo. | positivo |

**Sentimento geral do artigo:** muito positivo

---

## a-105 — Horário do show e recap

**Fonte:** CNN Brasil (cnnbrasil.com.br)  **Data:** 29/04/2026 14:26 UTC

Recap utilitário pré-show: 02/05, 21h45 início, transmissão TV Globo/Multishow/Globoplay, esquema de segurança, palco. Tom positivo.

**Sentimento geral do artigo:** positivo

---

## a-83 / a-236 — Prefeitura apresenta planejamento operacional

**Fontes:** Riotur oficial (a-83) / O Globo (a-236).  **Data:** 29/04/2026 16:33 / 19:42 UTC

Coletiva oficial Cavaliere + Riotur (Bernardo Fellows): detalha esquema de transporte, segurança (7.927 agentes), interdições, pulseiras de retorno do metrô, presença reforçada em hospitais. Bloco único cobre os dois IDs.

| Tema | Como é tratado | Classificação |
|---|---|---|
| Planejamento operacional municipal | Tom oficial-positivo. | positivo |
| Detalhes pulseiras retorno metrô | Logística positiva. | positivo |
| Reforço segurança/saúde | Preventivo positivo. | positivo |

**Sentimento geral do artigo:** positivo

---

## a-99 — Interdições no bairro de Copacabana começam 0h sábado

**Fonte:** O Globo (oglobo.globo.com)  **Data:** 29/04/2026 17:05 UTC

Detalhamento do esquema de trânsito: bloqueios começam 0h de 02/05 e duram até 8h de 03/05. Tom factual-positivo.

| Tema | Como é tratado | Classificação |
|---|---|---|
| Interdições viárias prolongadas | Tom factual; sem crítica. | neutro |
| Comunicação preventiva | Positiva. | positivo |

**Sentimento geral do artigo:** neutro

---

## a-163 — Quanto o show custará à Prefeitura (Rolling Stone)

**Fonte:** Rolling Stone Brasil (rollingstone.com.br)  **Data:** 29/04/2026 17:22 UTC

Replicação do dado R$ 15 mi. Tom factual. Veículo internacional-musical adicionando à cobertura.

**Sentimento geral do artigo:** neutro

---

## a-154 — CNN Brasil: programação do Todo Mundo no Rio

**Fonte:** CNN Brasil (cnnbrasil.com.br)  **Data:** 29/04/2026 18:31 UTC

Recap completo CNN: dia, hora, palco, abertura DJ Maz/Vintage Culture, transmissão. Tom positivo.

**Sentimento geral do artigo:** positivo

---

## a-173 / a-233 — O que está proibido em Copacabana / o que não levar

**Fontes:** O Globo (a-173) / Gshow (a-233)  **Datas:** 29/04/2026 20:49 / 23:32 UTC

Lista de itens proibidos no show: garrafas de vidro, latas, capacete, guarda-chuva grande, bebidas alcoólicas pesadas, mochilas grandes, equipamentos de som, drones, armas. Tom utilidade pública positiva. Bloco único cobre ambos IDs (mesmo conteúdo).

| Tema | Como é tratado | Classificação |
|---|---|---|
| Lista de itens proibidos | Utilidade preventiva. | positivo |
| Esquema rigoroso de revista | Tom factual. | neutro |

**Sentimento geral do artigo:** positivo

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
