# Plano de ação — segregação do projeto, indicador econômico e estratégia comercial

## Objetivo geral
Organizar a evolução do `OttoBoop/clipping-project` em frentes separadas para:
1. criar um **indicador econômico** usando a base da clipping tool com foco na cidade do Rio de Janeiro;
2. **segregar os dados e a apresentação** para não misturar o site político focado no Flávio com o projeto da prefeitura;
3. estruturar uma **segunda segregação comercial** para vender versões do produto para outros políticos, com controle de acesso;
4. realizar uma **pesquisa de mercado** para validar demanda, posicionamento e modelo de receita.

---

## Visão macro dos eixos

### Eixo A — Indicador econômico para o Rio
**Objetivo:** transformar clipping em um produto analítico com recorte territorial e temático claro.

#### Resultados esperados
- Definição do que o indicador mede.
- Lista de termos, entidades e temas monitorados.
- Critérios de relevância e classificação.
- Pipeline de coleta, limpeza, scoring e visualização.
- Primeira versão utilizável do indicador.

#### Perguntas-chave
- O indicador vai medir **atividade econômica**, **percepção econômica**, **pressão sobre serviços**, **obras/investimentos**, ou uma combinação disso?
- O recorte será por **cidade toda**, **região administrativa**, **bairro**, **tema** ou **secretaria**?
- Quais fontes entram e quais ficam fora?
- Como evitar que termos políticos contaminem o indicador econômico?

#### Plano de execução
- [ ] Definir a hipótese do indicador em 1 frase.
- [ ] Escolher 3 a 5 dimensões iniciais (ex.: emprego, comércio, obras, mobilidade, segurança econômica).
- [ ] Montar taxonomia de termos:
  - [ ] termos econômicos diretos;
  - [ ] termos indiretos/proxy;
  - [ ] entidades públicas e privadas relevantes;
  - [ ] localidades do Rio;
  - [ ] termos ambíguos que exigem desambiguação.
- [ ] Definir regras inteligentes de busca:
  - [ ] combinações por tema + local;
  - [ ] exclusões por ruído;
  - [ ] pesos por fonte;
  - [ ] pesos por recorrência e contexto.
- [ ] Criar critérios de classificação das matérias:
  - [ ] positiva;
  - [ ] neutra;
  - [ ] negativa;
  - [ ] estrutural;
  - [ ] evento pontual.
- [ ] Projetar fórmula inicial do indicador.
- [ ] Separar etapa de validação manual com amostra.
- [ ] Definir dashboard mínimo para acompanhamento.

#### Dependências
- Depende de entender o modelo atual de ingestão e classificação do repositório.
- Depende da segregação de dados para evitar mistura com o site político.
- Depende de uma estratégia de taxonomia e tagging mais robusta.

---

### Eixo B — Segregação do projeto da prefeitura
**Objetivo:** isolar dados, interface, regras e operação para que o projeto da prefeitura tenha identidade e base próprias.

#### Resultados esperados
- Dados separados do projeto atual.
- Ambiente separado de publicação.
- Regras de busca e classificação separadas.
- Branding e conteúdo separados.
- Menor risco de contaminação política no produto.

#### Decisão estrutural
**Recomendação inicial:** separar em camadas.

1. **Camada de core compartilhado**
   - scraping/coleta;
   - normalização;
   - utilitários de processamento;
   - componentes reaproveitáveis.

2. **Camada de dados por cliente/projeto**
   - fontes;
   - palavras-chave;
   - filtros;
   - scoring;
   - conteúdo editorial.

3. **Camada de apresentação por site**
   - tema visual;
   - páginas;
   - textos;
   - dashboards;
   - autenticação, se houver.

#### Estrutura sugerida
- [ ] Mapear o que hoje é acoplado ao projeto do Flávio.
- [ ] Separar o que é **core reutilizável** do que é **configuração específica**.
- [ ] Criar convenção de pastas/configuração por projeto, por exemplo:
  - `configs/flavio/`
  - `configs/prefeitura-rio/`
  - `data/flavio/`
  - `data/prefeitura-rio/`
  - `sites/flavio/`
  - `sites/prefeitura-rio/`
- [ ] Definir `.env` e segredos por ambiente.
- [ ] Separar banco/base/datasets por projeto.
- [ ] Separar pipeline de deploy por site.
- [ ] Separar analytics e logs.

#### Perguntas de implementação
- O site atual já suporta múltiplas configurações?
- O banco é arquivo, SQLite, JSON, ou outro formato?
- O conteúdo é gerado estaticamente ou servido dinamicamente?
- GitHub Pages é suficiente para todos os cenários?

#### Dependências
- Depende de um diagnóstico da arquitetura atual.
- Pode exigir refatoração de configuração, build e publicação.

---

### Eixo C — Segregação comercial para vender a outros políticos
**Objetivo:** transformar o projeto em um produto replicável, com isolamento por cliente e controle de acesso.

#### Resultados esperados
- Estrutura multi-site ou multi-tenant definida.
- Processo de onboarding de novo cliente.
- Controle de usuários/senhas.
- Kit mínimo de customização.
- Menor custo marginal para abrir uma nova operação.

#### Opções de arquitetura

##### Opção 1 — Um repositório/site por cliente
**Prós:**
- isolamento forte;
- menor risco de vazamento entre clientes;
- branding separado;
- deploy simples de entender.

**Contras:**
- mais manutenção operacional;
- duplicação de configuração;
- mais difícil evoluir tudo junto.

##### Opção 2 — Um core + múltiplos sites configuráveis
**Prós:**
- reaproveitamento alto;
- menor custo de manutenção;
- escala melhor.

**Contras:**
- exige arquitetura mais disciplinada;
- risco maior se a separação lógica ficar mal feita.

##### Opção 3 — Um único sistema com autenticação e áreas por cliente
**Prós:**
- melhor para operação SaaS;
- fácil vender como plataforma.

**Contras:**
- maior complexidade técnica;
- autenticação e autorização viram parte central;
- risco maior no começo.

#### Recomendação prática de curto prazo
Começar com **core compartilhado + sites segregados por cliente**, porque equilibra custo, rapidez e isolamento.

#### Plano de execução
- [ ] Definir modelo comercial inicial:
  - [ ] site institucional aberto;
  - [ ] painel fechado por senha;
  - [ ] relatórios sob demanda;
  - [ ] assinatura mensal.
- [ ] Definir nível de isolamento por cliente.
- [ ] Definir o que pode ser customizado sem alterar código-base.
- [ ] Criar checklist de onboarding:
  - [ ] nome do cliente;
  - [ ] branding;
  - [ ] temas monitorados;
  - [ ] fontes;
  - [ ] palavras-chave;
  - [ ] usuários autorizados;
  - [ ] domínio/subdomínio.
- [ ] Definir estratégia de autenticação.
- [ ] Criar política mínima de acesso e senhas.

#### Autenticação e acesso — recomendação geral
Se a ideia é começar barato:
- priorizar áreas fechadas simples;
- evitar construir auth complexa do zero no início;
- usar solução simples e controlável enquanto valida demanda.

#### Dependências
- Depende da segregação de dados e configuração.
- Depende de decidir se o produto será mais “serviço” ou mais “plataforma”.

---

### Eixo D — Pesquisa de mercado
**Objetivo:** validar se vale investir tempo e dinheiro para vender versões do produto.

#### Resultados esperados
- Perfil dos clientes-alvo.
- Problemas reais que eles pagariam para resolver.
- Concorrentes e alternativas atuais.
- Preço inicial plausível.
- Argumentos de venda e posicionamento.

#### Segmentos a pesquisar
- [ ] vereadores;
- [ ] deputados estaduais;
- [ ] deputados federais;
- [ ] equipes de gabinete;
- [ ] assessorias de comunicação;
- [ ] consultorias políticas;
- [ ] campanhas;
- [ ] órgãos públicos com foco territorial.

#### Perguntas de pesquisa
- [ ] Como hoje monitoram notícias e percepção?
- [ ] Quais ferramentas usam?
- [ ] O que falta nessas ferramentas?
- [ ] Pagariam por clipping territorial e temático com curadoria?
- [ ] Preferem painel, relatório, alerta ou resumo diário?
- [ ] Quanto pagariam por mês?
- [ ] Precisam de login por equipe?

#### Entregáveis
- [ ] Lista de concorrentes diretos e indiretos.
- [ ] Tabela comparativa de features.
- [ ] Hipóteses de preço.
- [ ] Proposta de valor por segmento.
- [ ] Script curto de entrevista comercial.
- [ ] Landing page ou apresentação de venda.

#### Dependências
- Pode começar já.
- Fica mais forte quando houver mockup ou piloto segregado.

---

## Ordem sugerida de execução

### Fase 1 — Diagnóstico e separação conceitual
- [ ] Mapear arquitetura atual do repositório.
- [ ] Identificar tudo que está acoplado ao projeto do Flávio.
- [ ] Definir fronteira entre core, dados e site.
- [ ] Escrever requisitos do projeto da prefeitura.

### Fase 2 — Segregação técnica mínima
- [ ] Separar configs, dados e saída do site.
- [ ] Preparar publicação independente do projeto da prefeitura.
- [ ] Garantir que o site do Flávio continue estável.

### Fase 3 — Prototipação do indicador econômico
- [ ] Definir taxonomia.
- [ ] Montar consultas.
- [ ] Testar amostra.
- [ ] Ajustar scoring.
- [ ] Publicar versão piloto.

### Fase 4 — Produto comercializável
- [ ] Padronizar template replicável para novos clientes.
- [ ] Adicionar autenticação simples onde necessário.
- [ ] Criar processo de onboarding.
- [ ] Definir proposta comercial.

### Fase 5 — Validação comercial
- [ ] Fazer entrevistas.
- [ ] Medir interesse.
- [ ] Testar preço.
- [ ] Fechar primeiros pilotos.

---

## Mapa de dependências

### Base estrutural
- [ ] Diagnóstico do repositório atual
  - desbloqueia segregação técnica
  - desbloqueia modelo multi-site
  - desbloqueia estimativa de esforço

### Segregação do projeto da prefeitura
- [ ] Separação de config/dados/site
  - desbloqueia indicador econômico limpo
  - desbloqueia piloto institucional separado

### Indicador econômico
- [ ] Taxonomia + regras de busca
  - desbloqueia scoring
  - desbloqueia dashboard
  - desbloqueia narrativa comercial

### Produto comercial
- [ ] Modelo replicável por cliente
  - desbloqueia novos sites
  - desbloqueia login/senhas
  - desbloqueia escala mínima

### Mercado
- [ ] Pesquisa de mercado
  - desbloqueia priorização de features
  - desbloqueia preço
  - desbloqueia pitch de venda

---

## Decisões que precisam ser tomadas cedo
- [ ] O projeto vai virar **produto**, **serviço**, ou híbrido?
- [ ] O indicador econômico será público, privado ou misto?
- [ ] Cada cliente terá seu próprio repo?
- [ ] Cada cliente terá seu próprio domínio/subdomínio?
- [ ] O acesso fechado será por senha simples, lista de usuários ou algo mais robusto?
- [ ] Qual parte será compartilhada e qual será exclusiva por cliente?

---

## Riscos principais
- [ ] Misturar dados políticos com dados institucionais/econômicos.
- [ ] Criar arquitetura complexa demais cedo demais.
- [ ] Gastar com ferramentas antes de validar demanda.
- [ ] Fazer buscas ruins e gerar indicador enviesado ou ruidoso.
- [ ] Ter custo operacional alto para cada novo cliente.

---

## Estratégia de baixo custo
- [ ] Reaproveitar o máximo possível do core atual.
- [ ] Separar por configuração antes de separar por código.
- [ ] Validar com 1 projeto da prefeitura + 1 piloto comercial antes de escalar.
- [ ] Evitar infra complexa no início.
- [ ] Usar autenticação simples no começo, desde que haja isolamento suficiente.
- [ ] Só abrir novos repositórios quando isso reduzir risco/complexidade de verdade.

---

## Próximos passos imediatos
- [ ] Revisar a arquitetura do `clipping-project` para identificar pontos de acoplamento.
- [ ] Decidir estrutura-alvo: monorepo configurável vs repositórios separados.
- [ ] Desenhar a taxonomia inicial do indicador econômico do Rio.
- [ ] Levantar requisitos mínimos do site da prefeitura.
- [ ] Definir como seria um piloto vendável para outro político.
- [ ] Iniciar a pesquisa de mercado com uma lista de segmentos e concorrentes.

---

## Sugestão de próximos documentos
- [ ] `docs/architecture-segregation.md`
- [ ] `docs/rio-economic-indicator.md`
- [ ] `docs/commercial-productization.md`
- [ ] `docs/market-research.md`

---

## Observação final
Antes de criar novos sites e novos repositórios, vale confirmar se o estado atual do projeto permite uma separação por configuração. Se não permitir, a prioridade deve ser uma refatoração arquitetural mínima para suportar múltiplos projetos sem duplicação desnecessária.
