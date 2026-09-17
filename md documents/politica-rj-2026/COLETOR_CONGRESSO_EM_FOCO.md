# Congresso em Foco: descoberta direta

O catálogo da conta PSD Rio 2026 executa consultas individuais dos nomes no endpoint público `https://front.congressoemfoco.com.br/Search/Query`, utilizado pela busca do próprio veículo. Cada consulta conserva o intervalo em São Paulo e retorna somente candidatos. O pipeline existente obtém o corpo, confere datas, aplica as regras congeladas dos nomes e grava os artigos e suas associações transacionalmente. Trechos destacados na busca não são textos de artigos.

A paginação observada no veículo repete a primeira página. O adaptador não usa essa paginação: respostas de 500 registros, `more` ou contadores que indiquem resultados incompletos dividem o período em tarefas persistentes até um dia. Um dia ainda saturado termina com lacuna explícita. Respostas vazias verificadas usam `results: null`, com contadores zero e ausência de erro. Respostas malformadas não são convertidas em sucesso vazio. Datas desconhecidas sobrevivem até a extração da página.

Google está desabilitado na geração inicial, nas alternativas após falha e nas tarefas antigas desse veículo. A fonte continua limitada ao perfil existente, sem expansão de permissões.

O sitemap anunciado foi preservado como mecanismo adiado no catálogo. Ele contém 24 partes e cerca de 116 mil endereços, incluindo acervo de 2007; a primeira parte contém 4.999 URLs com datas de modificação. Executar essa rota genérica consumiria buscas fora do intervalo sem provar datas editoriais. A rota ativa é a busca própria. Sua completude ainda depende de avaliação independente; conclusão das consultas não significa cobertura exaustiva do veículo.

Os testes incluem respostas e HTML reais preservados, menção apenas no corpo, limite de resultados, ausência de data, HTTP 429, resposta vazia, bloqueio de Google e gravação da descoberta antes da obtenção do artigo. Documentos de teste não entram nas contagens coletadas.

A execução de setembro de 2026 usa armazenamento local por decisão do usuário após o bloqueio do Supabase. Relatórios, linha de base, arquivos e comandos operacionais ficam em `clipping-live-operations/2026-09-16-congresso-direct/`. Implantação do código não restabelece por si só o armazenamento de produção.
