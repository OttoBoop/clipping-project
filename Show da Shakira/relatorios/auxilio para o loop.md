# Auxílio para o loop — perguntas/respostas críticas

Documento interno de processo. Registra as perguntas que faço a
mim mesmo durante o loop de revisão visual + linguagem do
`relatorio-geral.pdf`, e as respostas que dou. Erros aqui ficam
como aprendizado para iterações futuras.

## Contexto

- Source of truth: `relatório final beta source of truth.md`
  (cópia congelada do conteúdo aprovado).
- Guard-rails do loop: formato + conteúdo do source of truth
  preservado + uma página A4.
- Público: chefe da prefeitura, leitura em até 5 min.
- Inspeção visual do PDF NÃO faz parte do loop — trabalho por
  princípios.

## Auditoria inicial (pré-iterações)

### P1. Onde ainda há jargão técnico no documento?

Varrendo cada bloco contra o filtro "isso faz sentido para um
chefe da prefeitura que não desenvolveu o sistema?":

- **Header**: "215 matérias publicadas em 25 veículos de
  comunicação nacionais entre 01/04/2026 e 05/05/2026
  (35 dias) · 12 categorias temáticas." — limpo. Talvez "12
  categorias temáticas" mereça mini-contexto. OK por ora.
- **Tabela de distribuição**: cabeçalhos "Muito +", "Positivo",
  "Neutro", "Negativo", "Muito −". Limpo, autoexplicativo.
- **Headline da distribuição**: "84,2% positiva ou
  muito-positiva · 9,3% neutra · 6,5% negativa · soma 100%".
  "Soma 100%" é redundante para leigo? Talvez. Avaliar.
- **Universo de 215** (parágrafo italic): "fora-de-escopo
  nominais (cobertura sobre abuso policial, voos comerciais e
  uma anomalia de 2025)" e "cobertura redundante do mesmo
  evento por portais de agregação automática, sem texto
  editorial próprio". "Anomalia de 2025" — jargão? "Portais
  de agregação automática" — jargão? Sim, ambos. Reescrever.
- **Como classificamos**: "eixos livres" e "valência" —
  termos técnicos do projeto. "Valência" é especialmente
  técnico/químico. Mas o público pode ler como "tom". Avaliar
  se trocar por "classificação" ou manter.
- **Exemplos a-239 / a-126**: usar IDs `a-239` é puro jargão
  interno. O leigo não sabe o que é. Substituir por descrição
  do tipo "(matéria da CBN sobre o palco, 07/04)". Manter o
  ID em pequeno como referência opcional.
- **Tabela síntese "Outros exemplos"**: idem, IDs `a-67`,
  `a-264`, `a-162` precisam ser apresentados de forma legível.
- **Os números que viraram manchete**: "MetrôRio 24h, 165 mil
  pax". "pax" é jargão de turismo/aviação. Trocar por
  "passageiros".
- **Pontos de cobertura mista**: Paes "(`a-192`)" — tirar o
  ID, deixar só o fato.
- **Bloco "Sobre as correções"**: já tirei nomes de arquivo
  e IDs internos. Conferir se ainda sobrou algo do tipo
  "matérias parseadas" / "fora-de-escopo nominais". Sim,
  "fora-de-escopo nominais" continua técnico. Reescrever.

### P2. Onde a hierarquia visual está confusa?

- **Header geral do documento**: título grande + subtítulo,
  OK.
- **Seções h2**: todas iguais (azul forte com sublinhado
  cinza). Sinaliza "seção", funciona.
- **Tabela de distribuição (na abertura)**: tem o mesmo estilo
  de qualquer outra tabela. Não sinaliza "esse é o número-headline
  do documento". Talvez merecesse destaque visual extra.
- **Bullets de "Os números que viraram manchete"**: cada bullet
  tem categoria em negrito + lista de fatos separados por ponto.
  Estrutura uniforme. Pode ficar denso visualmente. Avaliar
  espaçamento.
- **Sugestão de narrativa**: blockquote azul-claro com barra
  vermelha. Já se diferencia bem.
- **Pontos de cobertura mista**: bullets normais. OK.
- **Bloco "Sobre as correções"**: caixa creme com borda
  dourada. Diferenciado do resto.

### P3. O que pode ser cortado sem perder informação?

- "soma 100%" no headline da distribuição — implícito numa
  distribuição percentual.
- Dia-da-semana / detalhe excessivo no header? Não, está OK.
- Repetição de "84,2%" na narrativa pra imprensa? Está OK,
  reforça.
- Marca temporal "(08/05)" no bloco de correções — útil pra
  contextualizar, mas pode ser mais limpo. Manter.

### P4. A linguagem está consistente?

- "Sentimento" vs "valência" vs "classificação" — uso os três
  no documento. Padronizar.
- "matérias" vs "notícias" vs "publicações" — tudo aparece.
  Padronizar.
- "muito-positivo" vs "Muito +" vs "muito positivo" —
  inconsistente.

### P5. O que falta para o chefe ler em 5 min?

- Lead claro logo no topo: já está com 215/25/84,2%, bom.
- Estrutura visual que oriente o olho: precisa ser refinada.
- Linguagem natural, sem termos do projeto: precisa ser
  refinada.
- Bloco final sobre correções: precisa ser leigo.

### P6. O que fazer com a "valência"?

Termo técnico. Públicos não-técnicos podem estranhar. Mas é
o termo correto para "carga avaliativa de um discurso" e
está se popularizando em análise de mídia. **Decisão**: manter
"valência" mas adicionar uma frase que apresenta o termo
("a carga avaliativa de cada eixo, daqui em diante 'valência'").

Revisão posterior: na verdade, melhor SUBSTITUIR por
"classificação" — palavra do dia a dia, mesmo significado no
contexto, zero ambiguidade. Decidir na iteração de linguagem.

### P7. "Eixos livres" — jargão?

Sim, é. "Eixos" é metáfora geométrica/técnica. Para leigo,
"tópicos" ou "aspectos" funciona melhor. Mas a frase atual
"quebrada em eixos livres" tem um charme que "quebrada em
tópicos" perde. **Decisão**: substituir por "tópicos" para
acessibilidade.

### P8. IDs `a-239`, `a-126` etc — manter?

- Pró: dão rastreabilidade ("se quiser ver a matéria
  original, esse é o ID interno do levantamento").
- Contra: poluem visualmente, leigo não sabe o que são, parecem
  códigos de bug.
- **Decisão**: substituir o ID destacado por descrição da
  matéria + veículo + data. Mover ID para uma referência
  pequena entre parênteses depois ("matéria da CBN, 07/04 ·
  ref. a-239").

### P9. Bloco "Sobre as correções" — qual o tom certo?

- Atual: institucional formal, frase única longa, dois
  marcadores em negrito ("Versão preliminar", "Versão atual").
- Otávio aprovou esse tom. Manter.
- Mas precisa eliminar resíduos de jargão: "fora-de-escopo
  nominais", "cobertura redundante de mesmo evento".
- Reescrever: "4 que cobriam temas paralelos (não o show
  diretamente) e 24 que repetiam matérias já analisadas".

### P10. Quantas iterações esperar?

Otávio disse explicitamente "não vai sair certo de primeira".
Plano: rodar **pelo menos 5 iterações distintas**, cada uma
com foco diferente:
1. Linguagem (jargão fora, padronização de termos).
2. Estrutura do markdown (wrappers, espaçamento, headers).
3. CSS (hierarquia visual real, cores, badges, bordas).
4. Refinamento (consistência tipográfica, respiro).
5. Polimento final (revisão palavra-a-palavra).

Se ainda tiver coisa pra ajustar depois da 5ª, continuo.
Convergir só quando rodadas sucessivas pararem de produzir
melhorias significativas.

## Registro das iterações

- **Iteração 1 — linguagem:** removi jargão remanescente (italic
  da abertura, parágrafo "Como classificamos", labels dos
  exemplos, "framing", "pax" → "passageiros"). Substituí "eixos
  livres" por "tópicos" porque é palavra mais natural; mantive
  "valência" (termo distintivo no nível-tópico). Reescrevi o
  bloco de correções para tirar nomes de arquivo e expressões
  como "fora-de-escopo nominais" e "cobertura redundante por
  portais de agregação automática".
- **Iteração 2 — visual (CSS):** caixas das tabelas de exemplo
  ficaram muito mais visíveis (fundo azul-claro com borda azul
  forte para o exemplo principal, fundo cinza com borda cinza
  para o exemplo contrastante). Síntese ficou compacta com
  badges coloridos por valência. Headline da distribuição
  ganhou destaque (caixa azul-clara centralizada, fonte maior,
  bordas laterais azuis fortes). Bloco de correções com header
  dourado em maiúsculas dentro de caixa creme.
- **Iteração 3 — tipografia + respiro:** h2 mais forte (10pt,
  border 1.5px), bullets com marker triangular azul, espaço
  entre bullets aumentou. Pontos de cobertura mista ganharam
  fundo amarelo-claro com borda dourada lateral, distintos
  visualmente dos bullets de manchete.
- **Iteração 4 — manchetes em 2 colunas:** dividi os 8 bullets
  de "Os números que viraram manchete" em 2 colunas com
  separador vertical, para scan rápido pelo leitor.
- **Iteração 5 — polimento de tags e badges:** tags dos
  exemplos com mais respiro, code inline diferenciado,
  ex-ref pequeno em itálico cinza.
- **Iteração 6 — linguagem da metodologia:** segunda passada
  no parágrafo "Como classificamos" para fluência natural.
- **Iteração 7 — labels dos exemplos:** removi a numeração
  "1" e "2" das tags (bastava "EXEMPLO · descrição").
  Substituí "valência geral" por "classificação geral" no
  label da síntese (consistência com o restante do texto).
- **Iteração 8 — referências:** trouxe os IDs de referência
  para entre parênteses e em pequeno cinza-itálico, longe do
  fluxo de leitura principal.
- **Iteração 9 — bug crítico descoberto e corrigido:** o
  markdown não estava processando o conteúdo dentro dos
  `<div>` HTML, fazendo com que os asteriscos `**` aparecessem
  literais no PDF. Solução: ativar a extensão `md_in_html` no
  `markdown.markdown()` e adicionar `markdown="1"` em todos os
  divs com conteúdo markdown. Após a correção, todo o **negrito
  do documento passou a renderizar corretamente** — os números
  importantes (84,2%, 215, 226, 75,7%, etc.) agora aparecem em
  negrito como pretendido. **Esse foi o bug mais relevante da
  série de iterações.**
- **Iteração 10 — re-aperto:** a correção do bug de markdown
  fez o conteúdo crescer (negrito ocupa mais espaço), e o PDF
  passou a duas páginas. Ajustei body para 7.6pt, line-height
  1.20, margens 0.6cm/0.9cm, padding das caixas reduzido,
  tamanho do h1 reduzido para 14pt. Voltou a uma página com
  todos os elementos preservados.

### Convergência

Validação final:
- 1 página A4 ✓
- 0 asteriscos literais (markdown processado corretamente) ✓
- 71 tokens críticos do source of truth presentes ✓
- 0 palavras proibidas ✓
- Hierarquia visual diferenciada por seção:
  - Tabela de distribuição com headline destacada
  - Exemplos da metodologia em caixas com cores distintas
  - Manchetes em 2 colunas com marker triangular azul
  - Sugestão de narrativa em blockquote azul
  - Pontos mistos em caixas amarelo-douradas
  - Correções em caixa creme com header dourado

Próximas iterações produziriam apenas micro-ajustes que não
mudam significativamente a leitura. Convergi.
