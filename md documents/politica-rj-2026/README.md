# Monitoramento político do Rio — 2026

Cadastro verificado em **9 de setembro de 2026**. O recorte de novas buscas começa em **1º de junho de 2026**, inclusive. A disputa acompanhada é a eleição para governador do Rio; não se trata de uma disputa interna de indicação do PSD.

O perfil de conta **PSD RJ 2026**, aprovado em 09/09/2026, acompanha **24 pessoas**: os 12 nomes inicialmente discutidos e os 12 acréscimos abaixo. Sua chave é `psd_rj_2026`; a lista exata está em [data/psd_rj_2026_profile.json](../../data/psd_rj_2026_profile.json). Novas buscas partem de 1º de junho e terminam no dia da execução, inclusive, no fuso de São Paulo; dependem de uma solicitação manual. A inclusão no cadastro não inicia coletas nem revisão do arquivo.

O manifesto completo passa a 37 pessoas e preserva os 25 nomes políticos anteriores, inclusive adversários, aliados e referências nacionais. Com os registros herdados, `data/targets.json` contém 41 entradas. O marcador `collection_profiles: ["psd_rj_2026"]` identifica os 24 nomes aprovados; ele não concede permissões. As associações de acesso pertencem ao perfil de conta. As cinco preferências originais e as marcas de nome principal permanecem intactas.

Os grupos são filtros sobre o mesmo acervo. Uma notícia com várias pessoas deve ter um único registro de artigo e várias associações. Coleções anteriores e seus filtros continuam disponíveis.

## Documentação e evidências

- [Fontes e regras de qualidade](FONTES.md).
- [Implementação, contratos e checklist](IMPLEMENTACAO.md).
- [Operação: implantação, importação, canários e reversão](OPERACAO.md).
- [Relatório local de escala](validation/political-scale-benchmark.json) e [relatório local de navegador](validation/political-browser-smoke.json). Os limites das simulações estão descritos no checklist; os caminhos de screenshots no relatório apontam para arquivos temporários da sessão.

Este README descreve o cadastro aprovado e sua implementação local. O estado operacional deve ser registrado no [runbook de operação](OPERACAO.md); adicionar nomes aqui não comprova implantação nem coleta concluída.

| Grupo | Nome | Partido verificado | Papel público | Evidência |
|---|---|---|---|---|
| Nomes prioritários | Eduardo Paes | PSD | Ex-prefeito do Rio; candidato ao Governo do Estado em 2026 | [Fonte 1](https://psd.org.br/noticias/rio-convencao-confirma-candidatura-de-eduardo-paes/) |
| Nomes prioritários | Flávio Valle | PSD | Vereador do Rio de Janeiro | [Fonte 1](https://www.camara.rio/vereadores/flavio-valle) |
| Nomes prioritários | Pedro Duarte | PSD | Vereador do Rio de Janeiro | [Fonte 1](https://www.camara.rio/vereadores/pedro-duarte) |
| Nomes prioritários | Renan Ferreirinha | PSD | Ex-secretário municipal de Educação do Rio; atuação como deputado federal | [Fonte 1](https://www.camara.leg.br/deputados/225386?ano=2024); [Fonte 2](https://consec.org.br/noticia/consec-agradece-a-renan-ferreirinha-pela-lideranca-a-frente-do-conselho/) |
| Nomes prioritários | Pedro Paulo | PSD | Deputado federal/RJ; candidato ao Senado em 2026 | [Fonte 1](https://psd.org.br/noticias/rio-convencao-confirma-candidatura-de-eduardo-paes/); [Fonte 2](https://www.camara.leg.br/deputados/122158) |
| PSD no Rio | Eduardo Cavaliere | PSD | Prefeito do Rio de Janeiro desde março de 2026 | [Fonte 1](https://prefeitura.rio/cidade/eduardo-cavaliere-assume-a-prefeitura-com-o-compromisso-de-continuidade-da-gestao-eduardo-paes/); [Fonte 2](https://www.camara.rio/comunicacao/noticias/3138-decana-da-camara-rosa-fernandes-e-ovacionada-em-homenagem-no-plenario) |
| PSD no Rio | Daniel Soranz | PSD | Deputado federal/RJ | [Fonte 1](https://www.camara.leg.br/deputados/220614?ano=2026) |
| PSD no Rio | Laura Carneiro | PSD | Deputada federal/RJ | [Fonte 1](https://www.camara.leg.br/deputados/74856) |
| PSD no Rio | Hugo Leal | PSD | Deputado federal/RJ | [Fonte 1](https://psd.org.br/noticias/congresso-psd-agora-tem-13-senadores-e-49-deputados/) |
| PSD no Rio | Carlo Caiado | PSD | Presidente da Câmara Municipal do Rio | [Fonte 1](https://www.camara.rio/vereadores/carlo-caiado) |
| PSD no Rio | Rosa Fernandes | PSD | Vereadora do Rio de Janeiro | [Fonte 1](https://www.camara.rio/vereadores/rosa-fernandes) |
| PSD no Rio | Guilherme Schleder | PSD | Deputado estadual/RJ; ex-secretário municipal de Esportes | [Fonte 1](https://www.alerj.rj.gov.br/Deputados/PerfilDeputado/495?AspxAutoDetectCookieSupport=1&Legislatura=20); [Fonte 2](https://www.diariodorio.com/politica/2026/08/29/quem-e-o-candidato-a-deputado-estadual-do-eduardo-paes.html) |
| PSD no Rio | Sergio Fernandes | PSD | Deputado estadual/RJ; candidato a deputado estadual em 2026 | [Fonte 1](https://campanha.sergiofernandes.com.br/); [Fonte 2](https://correiopetropolitano.com.br/2026/07/22/psd-confirma-sergio-fernandes-como-candidato/) |
| PSD no Rio | Junior da Lucinha | PSD | Vereador do Rio; candidato a deputado estadual em 2026 | [Fonte 1](https://camara.rio/vereadores/liderancas-blocos-e-partidos); [Fonte 2](https://candidatos.nexojornal.com.br/2026/rj/junior-da-lucinha-190002538006/) |
| PSD no Rio | Joyce Trindade | PSD | Vereadora do Rio; candidata a deputada estadual em 2026 | [Fonte 1](https://www.camara.rio/vereadores/joyce-trindade); [Fonte 2](https://candidatos.nexojornal.com.br/2026/rj/joyce-trindade-190002538000/) |
| PSD no Rio | Rafael Aloisio Freitas | PSD | Vereador do Rio; candidato a deputado federal em 2026 | [Fonte 1](https://camara.rio/vereadores/liderancas-blocos-e-partidos); [Fonte 2](https://rafaelaloisiofreitas.com.br/); [Fonte 3](https://www.camara.rio/i-ciclo-de-palestras-nocoes-do-processo-legislativo) |
| PSD no Rio | Marcelo Diniz | PSD | Vereador do Rio; candidato a deputado federal em 2026 | [Fonte 1](https://camara.rio/vereadores/liderancas-blocos-e-partidos); [Fonte 2](https://candidatos.nexojornal.com.br/2026/rj/marcelo-diniz-190002540174/) |
| PSD no Rio | Luiz Paulo | PSD | Deputado estadual/RJ; ex-vice-governador do Rio | [Fonte 1](https://www.luizpaulo.net/) |
| PSD no Rio | Átila Nunes | PSD | Político estadual/RJ, nascido em 1948; atuação na ALERJ; distinto do vereador homônimo | [Fonte 1](https://www.alerj.rj.gov.br/Deputados/PerfilDeputado/510?Legislatura=20); [Fonte 2](https://www.meuvoto.org.br/candidato/190002538039.html) |
| PSD no Rio | Otoni de Paula | PSD | Deputado federal/RJ; candidato à reeleição em 2026 | [Fonte 1](https://www.camara.leg.br/deputados/204441?ano=2024); [Fonte 2](https://candidatos.nexojornal.com.br/2026/rj/otoni-de-paula-190002540158/); [Fonte 3](https://imagem.camara.leg.br/Imagem/d/pdf/DCD0020251010001940000.PDF) |
| PSD no Rio | João Pires | PSD | Ex-secretário de Proteção e Defesa do Consumidor do Rio; candidato a deputado estadual em 2026 | [Fonte 1](https://joaopiresrj.com.br/); [Fonte 2](https://candidatos.nexojornal.com.br/2026/rj/joao-pires-190002538031/) |
| PSD no Rio | Felipe Boró | PSD | Vereador do Rio; renúncia ao registro de candidatura a deputado federal em 2026 | [Fonte 1](https://camara.rio/vereadores/liderancas-blocos-e-partidos); [Fonte 2](https://candidatos.nexojornal.com.br/2026/rj/felipe-boro-190002540183/); [Fonte 3](https://www.camara.rio/comunicacao/noticias/330-felipe-boro-toma-posse-na-camara-do-rio); [Fonte 4](https://www.camara.rio/vereadores/anteriores) |
| PSD no Rio | Márcio Ribeiro | PSD | Vereador do Rio; candidato a deputado federal em 2026 | [Fonte 1](https://camara.rio/vereadores/marcio-ribeiro); [Fonte 2](https://marcioribeiro.rio/) |
| PSD no Rio | Salvino Oliveira | PSD | Vereador do Rio; candidato a deputado federal em 2026 | [Fonte 1](https://camara.rio/vereadores/liderancas-blocos-e-partidos); [Fonte 2](https://candidatos.nexojornal.com.br/2026/rj/salvino-oliveira-190002540180/) |
| Aliados de outros partidos | Jane Reis | MDB | Candidata a vice-governadora na chapa de Eduardo Paes | [Fonte 1](https://psd.org.br/noticias/rio-convencao-confirma-candidatura-de-eduardo-paes/) |
| Disputa pelo Governo do Rio | Douglas Ruas | PL | Candidato ao Governo do Rio em 2026 | [Fonte 1](https://noticias.uol.com.br/eleicoes/2026/09/07/veja-lista-dos-candidatos-a-governador-do-rio-de-janeiro-em-2026.ghtm); [Fonte 2](https://www.cnnbrasil.com.br/eleicoes/quem-sao-os-candidatos-a-governador-do-rio-de-janeiro-em-2026/) |
| Disputa pelo Governo do Rio | Anthony Garotinho | Republicanos | Candidato ao Governo do Rio em 2026 | [Fonte 1](https://noticias.uol.com.br/eleicoes/2026/09/07/veja-lista-dos-candidatos-a-governador-do-rio-de-janeiro-em-2026.ghtm); [Fonte 2](https://www.cnnbrasil.com.br/eleicoes/quem-sao-os-candidatos-a-governador-do-rio-de-janeiro-em-2026/) |
| Disputa pelo Governo do Rio | André Marinho | Novo | Candidato ao Governo do Rio em 2026 | [Fonte 1](https://noticias.uol.com.br/eleicoes/2026/09/07/veja-lista-dos-candidatos-a-governador-do-rio-de-janeiro-em-2026.ghtm); [Fonte 2](https://www.cnnbrasil.com.br/eleicoes/quem-sao-os-candidatos-a-governador-do-rio-de-janeiro-em-2026/) |
| Disputa pelo Governo do Rio | William Siri | PSOL | Candidato ao Governo do Rio em 2026 | [Fonte 1](https://noticias.uol.com.br/eleicoes/2026/09/07/veja-lista-dos-candidatos-a-governador-do-rio-de-janeiro-em-2026.ghtm); [Fonte 2](https://www.cnnbrasil.com.br/eleicoes/quem-sao-os-candidatos-a-governador-do-rio-de-janeiro-em-2026/) |
| Disputa pelo Governo do Rio | Coronel Busnello | Missão | Candidato ao Governo do Rio em 2026 | [Fonte 1](https://noticias.uol.com.br/eleicoes/2026/09/07/veja-lista-dos-candidatos-a-governador-do-rio-de-janeiro-em-2026.ghtm); [Fonte 2](https://candidatos.nexojornal.com.br/2026/rj/coronel-busnello-190002544120/) |
| Disputa pelo Governo do Rio | Cyro Garcia | PSTU | Candidato ao Governo do Rio em 2026 | [Fonte 1](https://noticias.uol.com.br/eleicoes/2026/09/07/veja-lista-dos-candidatos-a-governador-do-rio-de-janeiro-em-2026.ghtm); [Fonte 2](https://www.cnnbrasil.com.br/eleicoes/quem-sao-os-candidatos-a-governador-do-rio-de-janeiro-em-2026/) |
| Disputa pelo Governo do Rio | Juliete Pantoja | UP | Candidato ao Governo do Rio em 2026 | [Fonte 1](https://noticias.uol.com.br/eleicoes/2026/09/07/veja-lista-dos-candidatos-a-governador-do-rio-de-janeiro-em-2026.ghtm); [Fonte 2](https://www.cnnbrasil.com.br/eleicoes/quem-sao-os-candidatos-a-governador-do-rio-de-janeiro-em-2026/) |
| Disputa pelo Governo do Rio | Luan Monteiro | PCO | Candidato ao Governo do Rio em 2026 | [Fonte 1](https://noticias.uol.com.br/eleicoes/2026/09/07/veja-lista-dos-candidatos-a-governador-do-rio-de-janeiro-em-2026.ghtm); [Fonte 2](https://www.cnnbrasil.com.br/eleicoes/quem-sao-os-candidatos-a-governador-do-rio-de-janeiro-em-2026/) |
| PSD nacional | Gilberto Kassab | PSD | Presidente nacional do PSD; candidato a vice-presidente em 2026 | [Fonte 1](https://saopaulo.psd-sp.org.br/noticias/psd-confirma-candidaturas-de-caiado-e-kassab/) |
| PSD nacional | Ronaldo Caiado | PSD | Ex-governador de Goiás; candidato à Presidência em 2026 | [Fonte 1](https://agenciabrasil.ebc.com.br/politica/noticia/2026-08/eleicoes-2026-ronaldo-caiado-e-o-candidato-do-psd-presidencia) |
| PSD nacional | Antonio Brito | PSD | Deputado federal/BA; líder do PSD na Câmara | [Fonte 1](https://psdcamara.org.br/psd-define-comissoes-e-reconduz-antonio-brito-a-lideranca-do-partido-na-camara/) |
| PSD nacional | Otto Alencar | PSD | Senador pela Bahia | [Fonte 1](https://www25.senado.leg.br/web/senadores/senador/-/perfil/5523) |

## Interpretação e manutenção

- O perfil PSD RJ 2026 reúne os cinco nomes prioritários e os 19 nomes do grupo PSD no Rio. Adversários, Jane Reis e os quatro nomes do PSD nacional continuam no cadastro geral, fora desta seleção aprovada.
- Átila Nunes é **Átila Nunes Pereira Filho, nascido em 1948**, com atuação estadual na ALERJ. O vereador Átila Alexandre Nunes Pereira é outra pessoa e não foi acrescentado à seleção. O perfil biográfico da ALERJ não confirma sozinho o exercício atual de uma suplência.
- Felipe Boró permanece no monitoramento como vereador, embora o registro de sua candidatura federal de 2026 conste como **Renúncia**. Patriota e PRD aparecem em seu histórico oficial; notícias antigas conservam essas filiações.
- Candidaturas a deputado não são exercício desse cargo: Joyce Trindade e Junior da Lucinha disputam vaga estadual; Rafael Aloisio Freitas, Marcelo Diniz, Márcio Ribeiro e Salvino Oliveira disputam vaga federal. João Pires é candidato estadual e ex-secretário municipal de defesa do consumidor.
- Luiz Paulo, João Pires, Márcio Ribeiro, Marcelo Diniz e Sergio Fernandes exigem contexto pertinente quando o nome abreviado é usado. João Pires requer pistas de defesa do consumidor, Procon, São Gonçalo ou seu trabalho com Renan Ferreirinha. Átila Nunes exige contexto estadual e exclui identificações explícitas do vereador homônimo. Nomes civis verificados dispensam essas pistas.

- Jane Reis pertence ao MDB e fica no grupo de aliados de outros partidos. Os oito adversários disputam o Governo do Rio; eles não são membros do PSD por estarem neste cadastro.
- Pedro Duarte é identificado como PSD pela Câmara do Rio. Matérias antigas que o identificam como Novo não devem ser reescritas.
- Eduardo Paes é ex-prefeito; Eduardo Cavaliere é o prefeito do Rio. Renan Ferreirinha é ex-secretário de Educação. Cargos e filiações devem ser reconferidos antes de futuras atualizações.
- A lista de candidaturas de 7 de setembro não equivale a uma garantia de deferimento definitivo. O TSE pode atualizar a situação de registro.
- As fontes, a data de verificação, os aliases e as regras de contexto estão em `data/political_targets_v1.json`. Não acrescentar nomes abreviados como “Caiado”, “Paulo” ou “Duarte” isoladamente.
- Pedro Duarte exige contexto do Rio e rejeita referências próximas a Portugal/Porto. Pedro Paulo exige contexto político pertinente; Ferreirinha isolado exige contexto político/educacional. As regras excluem formulações comuns de homônimos do futebol.
- Aliases muito ambíguos podem produzir casos para revisão. Não usar nomes detectados em menus, rodapés ou artigos relacionados para associar pessoas.

## Preservação do cadastro em produção

`merge_political_roster()` deve rodar depois da restauração de artefatos e antes da normalização do cadastro. O manifesto adiciona registros ausentes e apenas campos de metadados que ainda não existem. Valores já salvos pela equipe, inclusive campos vazios, aliases, nomes alterados, arquivamento e marcações de principal, prevalecem. A operação é idempotente e não reativa nomes arquivados.

**Validação deste cadastro:** seleção, preservação dos registros existentes, limites de nomes e regras de homônimos são verificados localmente. Nenhuma notícia nova é contabilizada por esta alteração de cadastro.
