# Fontes e qualidade de extração

Auditoria documental realizada em 09/09/2026. Os exemplos abaixo demonstram cobertura entre 01/06/2026 e 09/09/2026. São evidências de pertinência editorial; uma página consultável não comprova que seu RSS ou API esteja habilitado, completo ou operacional no coletor.

| Fonte | Evidência recente | Uso e observação |
|---|---|---|
| O Dia | [Agendas dos candidatos — 02/09](https://odia.ig.com.br/rio-de-janeiro/2026/09/7298023-enchentes-e-servicos-publicos-pautam-agendas-de-candidatos-no-rio.html) | Notícias diárias sobre Paes e adversários; guardar autoria e distinguir texto próprio de agência. |
| Diário do Rio | [Perfil de Flávio Valle — 26/08](https://www.diariodorio.com/politica/2026/08/26/quem-e-o-candidato-a-deputado-estadual-da-zona-sul-do-rio-de-janeiro.html) | Cobertura municipal e de candidatos à Alerj; separar informação factual de caracterização editorial. |
| Tempo Real RJ | [Paes, Cavaliere e Luiz Ramos Filho — 08/09](https://temporealrj.com/candidato-deputado-estadual-panfleto-eduardo-paes/) | Política local frequente; a página extraída continha vários artigos adicionais depois do principal. Isolar o artigo antes de detectar nomes. |
| Super Rádio Tupi | [Entrevista com Paes — 17/08](https://www.tupi.fm/podcasts/podcobrar-1-com-eduardo-paes-candidato-ao-governo-do-rio-de-janeiro-pelo-psd/) | Rádio/vídeo; título e data confirmados no índice de busca. A abertura direta falhou nesta auditoria. Não pressupor transcrição disponível. |
| Correio da Manhã | [Agenda de Douglas Ruas — 31/08](https://www.correiodamanha.com.br/estado-do-rio/2026/08/amp/315322-douglas-ruas-lanca-aliados-a-camara-federal-e-a-alerj.html) | Complemento regional; normalizar versões AMP para evitar duplicatas. |
| Câmara do Rio | [Comissão de Assuntos Urbanos](https://www.camara.rio/atividade-parlamentar/comissoes/permanentes/assuntos-urbanos) | Fonte primária; identifica Pedro Duarte/PSD e reuniões em 1, 8, 15 e 22 de junho. Extração direta apresentou erro intermitente; indexação recuperou os registros. |
| PSD | [Parlamentares em destaque — 18/06](https://psd.org.br/noticias/psd-esta-entre-os-mais-influentes-do-congresso/) | Comunicação partidária sobre Laura Carneiro, Hugo Leal, Pedro Paulo e outros; rotular como fonte partidária. |
| UOL | [Candidaturas ao Governo do Rio — 07/09](https://noticias.uol.com.br/eleicoes/2026/09/07/veja-lista-dos-candidatos-a-governador-do-rio-de-janeiro-em-2026.ghtm) | Confere a composição de nove candidaturas e os partidos. É uma fotografia datada da situação dos registros. |
| TRE-RJ | [Orientação sobre DivulgaCandContas — 26/08](https://www.tre-rj.jus.br/comunicacao/noticias/2026/Agosto/consulta-as-candidaturas-nas-eleicoes-2026-esta-disponivel-no-divulgacandcontas-1) | O registro oficial é atualizado continuamente; conferir lá mudanças posteriores. A consulta direta ao sistema não concluiu nesta auditoria. |

## Regras de qualidade

- Aplicar o recorte à data própria da matéria, não à data de atualização da página, indexação ou notícias relacionadas. Matérias antigas da Câmara apareciam em buscas recentes por causa dos links laterais.
- Separar `news`, `official_record` e `party_release` na procedência, sem tratar uma nota partidária como reportagem independente.
- Preservar a URL e a razão de falha quando o texto não puder ser extraído; não rotular metadados como conteúdo integral arquivado.
- Consultas com nomes não devem pesquisar somente “PSD”: a sigla também identifica partidos fora do Brasil. Usar as variantes do cadastro e contexto adequado.
- CBN foi bloqueada por robots na ferramenta de pesquisa; não houve tentativa de contorno. A pertinência de futuras integrações exige um caminho permitido e verificável.
- O inventário de coletores efetivamente habilitados permanece nas configurações da aplicação; esta lista não habilita automaticamente fontes.

**Implantação, desempenho remoto, taxas de extração e cobertura total ainda não verificados.**

## Registro de estratégias implementado localmente

`data/political_sources_v1.json` registra 15 provedores com estratégias, evidência de configuração e restrições. O novo coletor usa páginas de sitemaps diários já configuradas para Globo/G1/Extra/CBN; varreduras WordPress por data para Diário do Rio, Tempo Real, Agenda do Poder e Veja Rio; arquivo paginado da Câmara; e consultas por domínio no Google News para fontes regionais adicionais.

Os caminhos de sitemap de O Dia e Tupi foram derivados de seus arquivos robots. Para Metrópoles, o caminho adotado é o sitemap de notícias indicado; endpoints `/wp-json`, `/api`, `/busca` e `/search` constam como vedados no robots e não são a estratégia adotada. Consultas históricas do Google dividem janelas de sete dias até um dia e registram a saturação no limite de 100 resultados como lacuna, em vez de afirmar cobertura integral.

Os caminhos novos exigem canário de operação. O registro habilitado localmente não comprova coleta ou implantação em produção. Verificar os testes e observações finais do subsistema de fontes antes de alterar este estado.
