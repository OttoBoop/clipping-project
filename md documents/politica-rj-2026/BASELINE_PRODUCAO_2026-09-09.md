# Baseline real de produção — 09/09/2026

Leitura somente de consulta por SSH em `2026-09-09T14:36:23.493974+00:00`, concluída em `2026-09-09T14:36:57.796825+00:00`. Serviço `clipping-project.onrender.com`; SQLite `/opt/render/project/src/data/clipping.db`. Recorte de publicação: 01/06/2026–09/09/2026, inclusive em America/Sao_Paulo.

**Esta é a situação anterior à coleta autorizada. Novos artigos salvos por esta execução: 0.** Contagens obtidas do banco real; nenhuma massa sintética foi usada nesta auditoria. As contagens abaixo não demonstram implantação nem conclusão da coleta.

## Acervo existente

- 12,902 registros de artigos e 12,902 URLs únicas após normalização de parâmetros de rastreamento. Isso não exclui duplicação de conteúdo em URLs distintas.
- 2,330 artigos no recorte solicitado, abrangendo todos os assuntos/clientes; o último registro tem publicação `2026-06-30T22:54:52+00:00`. Não há publicação registrada de julho a setembro.
- 13,028 associações, 6,076 histórias e 2 classificações no banco completo.
- 12,879 corpos armazenados com pelo menos 200 caracteres. Isto **não comprova texto integral**. 1,594 corpos são idênticos ao snippet, dos quais 530 estão no recorte.
- Uma associação órfã fora do escopo político: menção 1, chave `shakira`, artigo ausente 99999999. Preservar no backup; não apagar nem fabricar artigo. Outros vínculos órfãos examinados: zero.

## Associações existentes por pessoa

Zero significa ausência de associação persistida para a pessoa. Há textos já salvos com nomes sem associação; os candidatos de revisão abaixo usam apenas o nome completo e ainda exigem validação de contexto e extração. Não são notícias novas salvas.

| Pessoa | Artigos associados, todo o histórico | Associados no recorte | Candidatos sem associação no recorte |
|---|---:|---:|---:|
| Eduardo Paes | 0 | 0 | 33 |
| Flávio Valle | 236 | 0 | 14 |
| Pedro Duarte | 0 | 0 | 19 |
| Renan Ferreirinha | 0 | 0 | 4 |
| Pedro Paulo | 0 | 0 | 10 |
| Eduardo Cavaliere | 0 | 0 | 133 |
| Daniel Soranz | 0 | 0 | 17 |
| Laura Carneiro | 0 | 0 | 2 |
| Hugo Leal | 0 | 0 | 4 |
| Carlo Caiado | 0 | 0 | 15 |
| Rosa Fernandes | 0 | 0 | 13 |
| Guilherme Schleder | 0 | 0 | 1 |
| Jane Reis | 0 | 0 | 1 |
| Douglas Ruas | 0 | 0 | 50 |
| Anthony Garotinho | 0 | 0 | 2 |
| André Marinho | 0 | 0 | 4 |
| William Siri | 0 | 0 | 8 |
| Coronel Busnello | 0 | 0 | 0 |
| Cyro Garcia | 0 | 0 | 0 |
| Juliete Pantoja | 0 | 0 | 0 |
| Luan Monteiro | 0 | 0 | 0 |
| Gilberto Kassab | 0 | 0 | 1 |
| Ronaldo Caiado | 0 | 0 | 0 |
| Antonio Brito | 0 | 0 | 0 |
| Otto Alencar | 0 | 0 | 0 |

## Publicadores no acervo completo

Estes valores abrangem todos os assuntos do acervo. Os 25 nomes têm zero artigos com associação persistida no recorte inicial. As fontes novas já possuíam alguns registros herdados; isso não prova funcionamento dos novos coletores.

| Domínio | Artigos existentes | No recorte |
|---|---:|---:|
| g1.globo.com | 3779 | 230 |
| oglobo.globo.com | 933 | 247 |
| extra.globo.com | 359 | 78 |
| cbn.globo.com | 129 | 19 |
| diariodorio.com | 3119 | 751 |
| temporealrj.com | 777 | 180 |
| agendadopoder.com.br | 1491 | 372 |
| vejario.abril.com.br | 803 | 75 |
| camara.rio | 75 | 9 |
| odia.ig.com.br | 50 | 7 |
| tupi.fm | 20 | 1 |
| metropoles.com | 4 | 2 |
| rc24h.com.br | 0 | 0 |
| j3news.com | 0 | 0 |

## Evidência e continuidade

- Os relatórios JSON completos foram preservados em `/home/otavio/Documents/vscode/clipping-live-operations/2026-09-09/` com permissões locais restritas.
- A consulta SQL dos identificadores confirmou que `flavio_valle` é a única chave entre os 25 nomes com associações herdadas. Não se trata de variação de identificadores para os outros nomes.
- Antes do corte de escritas, criar e verificar backup; depois revisar associações em lotes, congelar snapshot final, importar e validar, implantar worker e executar canários reais com todos os 25 nomes.
- Não inferir aprovação dos critérios de recall, classificação ou qualidade de texto a partir destas contagens. Essas verificações continuam pendentes.
