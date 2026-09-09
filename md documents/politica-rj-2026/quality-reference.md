# Referência editorial para a coleta PSD RJ 2026

Em 09/09/2026, foram conferidos **40 endereços reais de matérias**, com **107 associações positivas** aos **24 nomes aprovados**, em dez publicadores. A janela solicitada é 01/06–09/09/2026, inclusive, no fuso America/Sao_Paulo. O arquivo [psd_known_stories_2026.json](../../data/psd_known_stories_2026.json) registra endereço, data e sua base, pessoas verificadas e evidência editorial curta por matéria.

**37 matérias têm data visível no conteúdo retornado pelo publicador. Três matérias do J3News têm somente data no endereço, corroborada pelo evento narrado: a data de publicação continua não verificada.** Essas três têm `eligible_for_strict_date_evaluation=false`. São dois denominadores distintos: 40 URLs para conferência de presença e 37 casos para avaliação com data verificada. Não alterar a lista de datas aceitas pelo avaliador apenas para incluir os três casos; confirmar os metadados do publicador primeiro.

Esta entrega contém referências, sem iniciar coleta ou medir o corpus de produção. O número 40 não é uma contagem de notícias novas salvas. A verificação foi mediada pela ferramenta web: 17 aberturas de páginas e 23 resultados com trechos do corpo editorial indexado. Isso não comprova acesso HTTP direto pelo coletor, extração completa, armazenamento no PostgreSQL ou atualização do cache.

## Cobertura

| Publicador | Matérias | Tipo |
| --- | ---: | --- |
| O Dia | 5 | Veículo de notícias |
| Super Rádio Tupi | 3 | Veículo de notícias |
| RC24h | 3 | Veículo de notícias |
| J3News | 3 | Veículo de notícias |
| Tempo Real RJ | 12 | Veículo de notícias |
| Metrópoles | 5 | Veículo de notícias |
| Diário do Rio | 2 | Veículo de notícias |
| Agenda do Poder | 4 | Veículo de notícias |
| Veja Rio | 2 | Veículo de notícias |
| Câmara Municipal do Rio | 1 | Notícia institucional |

Há 13 matérias de junho, nove de julho, 14 de agosto e quatro de setembro. São URLs distintas, mas algumas descrevem o mesmo evento; não representam 40 acontecimentos independentes. Câmara Rio é fonte institucional, separada dos nove veículos jornalísticos.

| Pessoa aprovada | Matérias com associação positiva |
| --- | ---: |
| Eduardo Paes | 20 |
| Flávio Valle | 5 |
| Pedro Duarte | 4 |
| Renan Ferreirinha | 5 |
| Pedro Paulo | 15 |
| Eduardo Cavaliere | 10 |
| Daniel Soranz | 2 |
| Laura Carneiro | 2 |
| Hugo Leal | 1 |
| Carlo Caiado | 2 |
| Rosa Fernandes | 1 |
| Guilherme Schleder | 2 |
| Sergio Fernandes | 1 |
| Junior da Lucinha | 3 |
| Joyce Trindade | 3 |
| Rafael Aloisio Freitas | 2 |
| Marcelo Diniz | 1 |
| Luiz Paulo | 3 |
| Átila Nunes (estadual, 1948) | 2 |
| Otoni de Paula | 3 |
| João Pires | 4 |
| Felipe Boró | 5 |
| Márcio Ribeiro | 6 |
| Salvino Oliveira | 5 |

A presença de todos os nomes não equivale a cobertura suficiente de cada pessoa. Hugo Leal, Rosa Fernandes, Sergio Fernandes e Marcelo Diniz têm apenas uma matéria anotada cada. João Pires, Felipe Boró, Márcio Ribeiro e Salvino Oliveira têm, respectivamente, quatro, cinco, seis e cinco.

Não foi incluída matéria verificada de O Globo, G1, Extra ou CBN nesta pesquisa delimitada. O leitor web bloqueou O Globo e não retornou resultados úteis de G1. Essa é uma lacuna da referência; não demonstra ausência de notícias nesses veículos. Também faltam amostragem diária e distribuição equilibrada por veículo, pessoa e assunto.

## Critérios e limites das anotações

As associações exigem nome em título ou parágrafo editorial efetivamente lido. Resumos do mecanismo de busca, menus, tags, comentários e blocos de notícias relacionadas não estabelecem associação. Uma notícia pode ter outros nomes corretos ainda não avaliados: somente `assessed_target_keys` participa da análise de precisão. Não converter nomes ausentes de `expected_target_keys` automaticamente em falsos positivos.

Cinco associações negativas foram explicitamente verificadas em quatro matérias:

- `psd_2026_010`: o Átila Nunes da lista de vereadores não é o político estadual nascido em 1948.
- `psd_2026_015`: Paes e Pedro Paulo aparecem em tags ou matérias relacionadas, sem menção editorial na nota sobre Salvino.
- `psd_2026_024`: a lista estadual cita Claudio Caiado, sem estabelecer associação a Carlo Caiado.
- `psd_2026_030`: a nota de Hugo Leal cita Ronaldo Caiado, sem estabelecer associação a Carlo Caiado.

Esses cinco negativos não bastam para medir a precisão geral do corpus. O caso `psd_2026_039` também documenta o nome da escola Luiz Paulo Horta: não foi usado como associação positiva ao deputado e tampouco recebeu um negativo integral sem revisão completa. No caso `psd_2026_040`, Átila Nunes aparece sem cargo suficiente para resolver o homônimo e permanece não avaliado.

Os casos `psd_2026_021` e `psd_2026_029` ajudam a revisar dois riscos reais: referências à comunidade portuguesa podem ser legítimas numa matéria sobre Pedro Duarte do Rio, e nomes importantes podem surgir apenas depois de vários parágrafos de serviço. Blocos isolados de “Leia mais” no meio da matéria também não significam que todo o texto seguinte seja rodapé.

`canonical_url` é o endereço público verificado para busca, sem afirmar inspeção de `rel=canonical`. A matéria `psd_2026_011` usa o endereço AMP efetivamente encontrado; não foram inventados aliases. Datas visíveis não são convertidas em horas UTC ou tratadas como comprovação da primeira publicação quando o publicador não distingue publicação e atualização.

## Comparação com o corpus real

A referência completa contém 40 casos. O avaliador atual aceita somente datas publicadas, atualizadas ou timestamps visíveis; por isso, usar uma seleção explícita de 37 casos, sem modificar a lista de valores aceitos:

```sh
python3 - <<'PY'
import json
from pathlib import Path

source = Path("data/psd_known_stories_2026.json")
data = json.loads(source.read_text())
selected = [case for case in data["cases"]
            if case["eligible_for_strict_date_evaluation"]]
assert len(data["cases"]) == 40 and len(selected) == 37
data["cases"] = selected
data["reference_subset"] = "strict_visible_date_only"
data["summary"] = {
    "article_count": len(selected),
    "source_reference_article_count": 40,
    "excluded_unverified_publication_dates": 3,
}
data["limitations"].append(
    "This evaluation excludes the three unverified J3News publication dates."
)
Path("/tmp/psd-known-stories-strict-date.json").write_text(
    json.dumps(data, ensure_ascii=False, indent=2) + "\n"
)
PY
```

Validar a seleção sem conexão ao banco:

```sh
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/python \
  tools/political_quality_check.py \
  --dataset /tmp/psd-known-stories-strict-date.json \
  --validate-only --output /tmp/psd-reference-validation.json
```

Após a coleta real, medir essa seleção em leitura, com o ambiente do serviço configurado:

```sh
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/python \
  tools/political_quality_check.py \
  --dataset /tmp/psd-known-stories-strict-date.json \
  --output /tmp/psd-reference-corpus.json
```

`--validate-only` apenas confere a referência; não mede nem aprova o corpus. O relatório deve informar 37 como denominador dessa seleção. A conferência das 40 URLs e a confirmação posterior das três datas J3News devem aparecer separadamente. Nenhum caso sintético integra este conjunto, e a autorização ou conclusão de uma coleta não decorre de passar nesses casos.

## Leitura autenticada da produção pela API

O helper [psd_live_quality_readback.py](../../tools/psd_live_quality_readback.py) usa a sessão PSD já salva em arquivo privado. Ele aceita somente GETs para metadados, andamento, cobertura, páginas de artigos e textos individuais no domínio fixo da aplicação. Não faz login, inicia tarefas, altera classificações ou importa arquivo antigo. Cookies e corpos de respostas de erro não entram no relatório.

Para a primeira coleta real de 09/08/2026:

```sh
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/python \
  tools/psd_live_quality_readback.py \
  --date-from 2026-08-09 --date-to 2026-08-09 \
  --job-id political-d9290bf56e0a48ee860468075d185930 \
  --max-pages 5 --max-bodies 24 \
  --output /tmp/psd-first-live-readback.json
```

Nesse dia existem **dois artigos de referência com data visível e três associações positivas esperadas**: Paes e Pedro Paulo na cobertura do debate e Otoni na reportagem patrimonial. As outras 35 matérias com data visível ficam fora da janela; os três casos J3News continuam separados. Para qualquer pessoa sem referência naquele dia, a taxa permanece `null`, mesmo que a API mostre zero associações.

Depois da coleta de todo o período, repetir explicitamente com a janela completa:

```sh
/home/otavio/Documents/vscode/clipping-project/.venv_playwright/bin/python \
  tools/psd_live_quality_readback.py \
  --date-from 2026-06-01 --date-to 2026-09-09 \
  --max-pages 50 --max-bodies 48 \
  --output /tmp/psd-full-period-live-readback.json
```

As páginas têm no máximo 200 artigos; o segundo comando limita a leitura a 10 mil metadados e 48 corpos individuais, com pelo menos um segundo entre pedidos. Os artigos associados às referências têm prioridade na amostra de corpos; depois são selecionados até dois por pessoa, compartilhando matérias com vários nomes. O relatório mostra a cobertura efetiva dos 24 nomes. Atingir o limite de páginas mantém as taxas sem medição e indica leitura incompleta.

As contagens da API são de artigos visíveis no perfil dentro das datas armazenadas. Não equivalem a inserções novas de uma tarefa. A tarefa informada tem métricas separadas; o helper informa quando sua janela difere da janela consultada. A leitura também não constitui um snapshot transacional enquanto a coleta continua.

Uma URL ausente na API pode estar sem associação permitida, com data errada ou com alias não exposto. Por isso, `visible_reference_fraction` mede visibilidade das referências no perfil, sem afirmar ausência definitiva no PostgreSQL. A precisão só considera os poucos negativos explicitamente anotados; não estabelece precisão geral do corpus. Casos e associações ainda fora da janela coletada não entram no denominador.

O exame dos corpos reaplica as regras locais de nomes e contexto sobre título e texto, registra divergências e no máximo 20 palavras de evidência normalizada por artigo. É um diagnóstico de consistência do matcher; concordância com a própria regra não prova acerto editorial. Não há aprovação automática de qualidade ou implantação. Código de saída 0 significa que a leitura delimitada terminou; 1 indica leitura parcial ou falha; 2 indica entradas inválidas.

A primeira tentativa pelo processo de pesquisa não alcançou a aplicação: a resolução DNS do domínio falhou e o helper registrou `ConnectionError` em `/api/political/meta`, com contagens `null`. Isso não prova falha do servidor nem corpus vazio. O comando está preparado para execução pelo processo operacional com acesso de rede; resultados reais devem substituir qualquer conclusão pendente somente depois dessa execução.

## Índice das matérias verificadas

Cada link abre a fonte da anotação; a evidência curta e o método estão no JSON.

| Caso | Data de referência | Fonte | Pessoas positivamente verificadas |
| --- | --- | --- | --- |
| [001](https://odia.ig.com.br/colunas/informe-do-dia/2026/06/7269810-salvino-oliveira-ve-chances-de-ser-deputado-federal.html) | 2026-06-27 | O Dia | Salvino Oliveira; Eduardo Cavaliere; Eduardo Paes; Pedro Paulo |
| [002](https://www.tupi.fm/rio/eduardo-paes-inicia-campanha-ao-governo-do-rio-neste-domingo/) | 2026-08-16 | Super Rádio Tupi | Eduardo Paes; Pedro Paulo |
| [003](https://rc24h.com.br/boca-miuda-os-bastidores-da-politica-na-regiao-dos-lagos-nesta-sexta-feira-28-10/) | 2026-08-28 | RC24h | Eduardo Paes; Pedro Paulo; Renan Ferreirinha |
| [004](https://j3news.com/2026/08/26/paes-mantem-lideranca-com-349-enquanto-ruas-avanca-para-147-aponta-pesquisa/) | 2026-08-26 * | J3News | Eduardo Paes |
| [005](https://temporealrj.com/marcio-ribeiro-psd-deputado-federal/) | 2026-06-15 | Tempo Real RJ | Márcio Ribeiro; Eduardo Cavaliere; Pedro Paulo; Eduardo Paes |
| [006](https://temporealrj.com/laura-carneiro-herda-estrutura-pedro-paulo/) | 2026-06-15 | Tempo Real RJ | Laura Carneiro; Pedro Paulo; Márcio Ribeiro; Eduardo Cavaliere; Salvino Oliveira; Felipe Boró |
| [007](https://temporealrj.com/christi-sao-goncalo-pl-psd-psol-2026/) | 2026-06-04 | Tempo Real RJ | Eduardo Paes; João Pires; Renan Ferreirinha |
| [008](https://temporealrj.com/patrimonio-milionario-vereador-felipe-boro-psd/) | 2026-08-07 | Tempo Real RJ | Felipe Boró |
| [009](https://temporealrj.com/camara-do-rio-tera-28-candidatos-em-outubro/) | 2026-06-07 | Tempo Real RJ | Eduardo Paes; Pedro Paulo; Felipe Boró; Marcelo Diniz; Márcio Ribeiro; Rafael Aloisio Freitas; Salvino Oliveira; Flávio Valle; Junior da Lucinha; Pedro Duarte |
| [010](https://temporealrj.com/camara-do-rio-projeto-luciana-novaes-rua/) | 2026-08-26 | Tempo Real RJ | Carlo Caiado; Eduardo Cavaliere; Rafael Aloisio Freitas; Junior da Lucinha; Pedro Duarte; Rosa Fernandes; Márcio Ribeiro; Felipe Boró |
| [011](https://odia.ig.com.br/rio-de-janeiro/2026/06/amp/7263878-justica-manda-devolver-bens-apreendidos-de-salvino-oliveira-apos-investigacao-ser-trancada.html) | 2026-06-12 | O Dia | Salvino Oliveira |
| [012](https://www.tupi.fm/eleicoes/candidato-ao-governo-do-rio-paes-propoe-reunificar-secretarias-de-seguranca-autoridade-e-comando/) | 2026-08-17 | Super Rádio Tupi | Eduardo Paes |
| [013](https://rc24h.com.br/boca-miuda-os-bastidores-da-politica-na-regiao-dos-lagos-nesta-segunda-feira-31-6/) | 2026-08-31 | RC24h | Renan Ferreirinha; Eduardo Paes; Pedro Paulo |
| [014](https://j3news.com/2026/06/22/eduardo-paes-participa-de-encontro-em-campos-para-ouvir-propostas-para-o-norte-e-noroeste-fluminense/) | 2026-06-22 * | J3News | Eduardo Paes |
| [015](https://odia.ig.com.br/colunas/informe-do-dia/2026/08/7293090-conceicao-tavares-pode-virar-nome-de-rua-no-rio.html) | 2026-08-21 | O Dia | Salvino Oliveira |
| [016](https://www.tupi.fm/rio/veja-como-as-duas-novas-agulhas-na-av-brasil-vao-mudar-seu-trajeto-para-o-porto/) | 2026-06-24 | Super Rádio Tupi | Eduardo Cavaliere |
| [017](https://rc24h.com.br/boca-miuda-os-bastidores-da-politica-na-regiao-dos-lagos-nesta-quarta-feira-19-10/) | 2026-08-19 | RC24h | Eduardo Paes; Renan Ferreirinha; Pedro Paulo |
| [018](https://j3news.com/2026/06/23/com-eduardo-paes-primeiro-encontro-de-escuta-e-propostas-da-cdl-campos-reune-grande-publico/) | 2026-06-23 * | J3News | Eduardo Paes; Pedro Paulo |
| [019](https://www.metropoles.com/brasil/debate-rj-ausente-paes-vira-alvo-ruas-cita-confianca-de-bolsonaro) | 2026-08-09 | Metrópoles | Eduardo Paes; Pedro Paulo |
| [020](https://temporealrj.com/oficio-juizado-especial-civel-copacabana/) | 2026-06-17 | Tempo Real RJ | Flávio Valle |
| [021](https://www.diariodorio.com/politica/2026/08/567000-quem-e-o-candidato-a-deputado-estadual-do-rio-de-janeiro-do-vasco.html) | 2026-08-22 | Diário do Rio | Pedro Duarte |
| [022](https://agendadopoder.com.br/luiz-paulo-lembra-projeto-com-marcio-canella-e-provoca-reacao-no-plenario-da-alerj/) | 2026-09-01 | Agenda do Poder | Luiz Paulo |
| [023](https://vejario.abril.com.br/cidade/mpf-suspensao-tolerancia-zero-prefeito-criticas/) | 2026-07-20 | Veja Rio | Eduardo Cavaliere |
| [024](https://www.diariodorio.com/quem-sao-os-candidatos-a-deputado-estadual-do-psd-em-2026-no-rio-de-janeiro/index.html) | 2026-07-26 | Diário do Rio | Eduardo Paes; Pedro Paulo; Átila Nunes (estadual, 1948); Flávio Valle; Guilherme Schleder; João Pires; Joyce Trindade; Luiz Paulo; Pedro Duarte; Sergio Fernandes; Junior da Lucinha |
| [025](https://www.metropoles.com/brasil/deputado-do-psd-pede-que-tse-investigue-crescimento-digital-de-augusto-cury) | 2026-09-08 | Metrópoles | Otoni de Paula |
| [026](https://agendadopoder.com.br/rio-avanca-com-programa-de-prevencao-a-yersiniose-e-preve-exames-pelo-sus/) | 2026-09-03 | Agenda do Poder | Átila Nunes (estadual, 1948) |
| [027](https://temporealrj.com/joao-pires-imovel-600-mil-patrimonio-eleicoes/) | 2026-08-14 | Tempo Real RJ | João Pires; Eduardo Paes |
| [028](https://temporealrj.com/cavaliere-apoio-schleder-caiado-alerj/) | 2026-08-18 | Tempo Real RJ | Eduardo Cavaliere; Eduardo Paes; Guilherme Schleder; Márcio Ribeiro; Carlo Caiado |
| [029](https://temporealrj.com/acao-castracao-microchipagem-caes-gatos/) | 2026-06-05 | Tempo Real RJ | Márcio Ribeiro; Pedro Paulo |
| [030](https://odia.ig.com.br/colunas/informe-do-dia/2026/07/7274285-desenvolvimento-do-rio-em-pauta.html) | 2026-07-08 | O Dia | Hugo Leal |
| [031](https://vejario.abril.com.br/coluna/lu-lacerda/lapa-a-escadaria-selaron-vai-ficar-tinindo-de-nova/) | 2026-07-03 | Veja Rio | Eduardo Cavaliere |
| [032](https://www.metropoles.com/brasil/otoni-de-paula-declara-patrimonio-quase-300-vezes-maior-que-o-de-2022) | 2026-08-09 | Metrópoles | Otoni de Paula |
| [033](https://www.metropoles.com/colunas/milena-teixeira/paes-entra-em-campo-para-destravar-chapa-com-benedita-e-pedro-paulo) | 2026-07-03 | Metrópoles | Eduardo Paes; Pedro Paulo; Eduardo Cavaliere |
| [034](https://www.metropoles.com/colunas/milena-teixeira/candidatas-do-pt-no-rio-resistem-a-apoiar-publicamente-aliado-de-paes) | 2026-07-04 | Metrópoles | Eduardo Paes; Pedro Paulo |
| [035](https://odia.ig.com.br/rio-de-janeiro/2026/07/7280824-rio-sanciona-leis-para-ampliar-atendimento-a-pessoas-com-tea.html) | 2026-07-22 | O Dia | Joyce Trindade; Felipe Boró |
| [036](https://temporealrj.com/soranz-flavio-valle-treta/) | 2026-06-22 | Tempo Real RJ | Daniel Soranz; Flávio Valle |
| [037](https://temporealrj.com/prefeitura-lei-dia-do-barraqueiro-praia/) | 2026-07-09 | Tempo Real RJ | Eduardo Cavaliere; Flávio Valle |
| [038](https://www.camara.rio/comunicacao/noticias/3167-municipio-devera-estabelecer-diretrizes-para-enfrentar-a-violencia-virtual) | 2026-06-10 | Câmara Municipal do Rio | Joyce Trindade |
| [039](https://agendadopoder.com.br/eduardo-paes-visita-get-na-rocinha-e-promete-expandir-modelo-tecnologico-na-rede-estadual/) | 2026-09-08 | Agenda do Poder | Eduardo Paes |
| [040](https://agendadopoder.com.br/psd-oficializa-eduardo-paes-candidato-para-governo-do-rio-e-pedro-paulo-ao-senado/) | 2026-07-20 | Agenda do Poder | Eduardo Paes; Pedro Paulo; Laura Carneiro; Luiz Paulo; Otoni de Paula; Daniel Soranz; Renan Ferreirinha; João Pires |

\* Data de URL; publicação ainda não verificada. Endereços e evidências conferidos em 09/09/2026. Esta amostra independente foi preparada antes da comparação com os resultados do coletor.
