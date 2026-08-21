/**
 * Questionário Circuito dos Botequins — Google Apps Script
 *
 * HOW TO USE:
 *   1. Go to https://script.google.com
 *   2. Click "New project"
 *   3. Delete the placeholder code and paste this entire file
 *   4. Click the Run button (play icon) — select createForm
 *   5. Google will ask for permission to manage Forms — grant it
 *   6. After it runs, check the Execution Log (View > Execution log)
 *      for the Form URL
 *   7. Open the URL, review, and share
 *
 * A pesquisa é conduzida pela Riotur e pela Secretaria Municipal de
 * Desenvolvimento Econômico (SMDE), no âmbito do programa Circuitos
 * do Patrimônio Cultural Carioca (IRPH).
 *
 * Branching logic:
 *   Q15 (contratação temporários) = "Sim" → pageTemporariosDetalhes
 *                                  = "Não" → pageTurismo
 *   Q17 (turistas estrangeiros) = "Sim, com frequência"
 *                               ou "Sim, ocasionalmente" → pageNacionalidades
 *                               demais → pageFornecedores
 */

function createForm() {
  var form = FormApp.create('Pesquisa Circuito dos Botequins – Riotur / SMDE');
  form.setDescription(
    'A Prefeitura do Rio – por meio da Riotur e da Secretaria Municipal de ' +
    'Desenvolvimento Econômico (SMDE) – está elaborando uma pesquisa com os ' +
    'bares, botequins e restaurantes pertencentes ao Circuito dos Botequins, ' +
    'que fazem parte do programa de Circuitos do Patrimônio Cultural Carioca, ' +
    'gerido pelo Instituto Rio Patrimônio da Humanidade (IRPH).\n\n' +
    'Suas respostas são fundamentais para avaliar o impacto econômico, ' +
    'turístico e cultural desses estabelecimentos para o Rio de Janeiro. ' +
    'Obrigado por participar!'
  );
  form.setIsQuiz(false);
  form.setCollectEmail(false);
  form.setAllowResponseEdits(true);
  form.setProgressBar(true);

  // =========================================================
  //  PAGE 1 — Identificação do Estabelecimento
  // =========================================================

  form.addTextItem()
    .setTitle('1) Nome do estabelecimento')
    .setRequired(true);

  form.addTextItem()
    .setTitle('2) Nome do dono ou responsável pelo estabelecimento e telefone para contato')
    .setRequired(true);

  form.addTextItem()
    .setTitle('3) Em que ano o estabelecimento foi fundado?')
    .setRequired(true);

  form.addTextItem()
    .setTitle('4) Em que ano o estabelecimento foi declarado Patrimônio Cultural Carioca?')
    .setRequired(true);

  // =========================================================
  //  PAGE 2 — Dados Econômicos
  // =========================================================

  form.addPageBreakItem()
    .setTitle('Dados Econômicos');

  form.addTextItem()
    .setTitle('5) Qual é o faturamento médio mensal do estabelecimento? (em R$)')
    .setHelpText('Caso não seja possível informar o valor exato, indique uma estimativa.')
    .setRequired(true);

  form.addTextItem()
    .setTitle('6) Qual é o ticket médio por cliente? (em R$)')
    .setRequired(true);

  form.addTextItem()
    .setTitle('7) Quantos clientes o estabelecimento recebe, aproximadamente, por mês?')
    .setHelpText('Resposta numérica.')
    .setRequired(true);

  // =========================================================
  //  PAGE 3 — Bebidas: Chope e Drinks
  // =========================================================

  form.addPageBreakItem()
    .setTitle('Bebidas: Chope e Drinks');

  form.addTextItem()
    .setTitle('8) Quantos chopes o estabelecimento vende, aproximadamente, por mês?')
    .setHelpText('Resposta numérica.')
    .setRequired(true);

  var q9 = form.addMultipleChoiceItem()
    .setTitle('9) Aproximadamente, qual percentual do faturamento mensal vem da venda de chope?');
  q9.setChoices([
    q9.createChoice('Até 10%'),
    q9.createChoice('11% a 25%'),
    q9.createChoice('26% a 50%'),
    q9.createChoice('51% a 75%'),
    q9.createChoice('Mais de 75%')
  ]);
  q9.setRequired(true);

  form.addTextItem()
    .setTitle('10) Quantos drinks o estabelecimento vende, aproximadamente, por mês?')
    .setHelpText('Resposta numérica.')
    .setRequired(true);

  var q11 = form.addMultipleChoiceItem()
    .setTitle('11) Aproximadamente, qual percentual do faturamento mensal vem da venda de drinks?');
  q11.setChoices([
    q11.createChoice('Até 10%'),
    q11.createChoice('11% a 25%'),
    q11.createChoice('26% a 50%'),
    q11.createChoice('51% a 75%'),
    q11.createChoice('Mais de 75%')
  ]);
  q11.setRequired(true);

  // =========================================================
  //  PAGE 4 — Pessoal e Cardápio
  // =========================================================

  form.addPageBreakItem()
    .setTitle('Pessoal e Cardápio');

  form.addTextItem()
    .setTitle('12) Quantas pessoas trabalham atualmente no estabelecimento?')
    .setHelpText('Inclua funcionários fixos e, se houver, trabalhadores temporários ou freelancers que atuem regularmente no estabelecimento. Resposta numérica.')
    .setRequired(true);

  form.addTextItem()
    .setTitle('13) Quantos trabalhadores são contratados em regime CLT?')
    .setHelpText('Resposta numérica.')
    .setRequired(true);

  form.addTextItem()
    .setTitle('14) Qual é o prato/petisco mais famoso (carro-chefe) e quantos saem por semana ou por mês?')
    .setRequired(true);

  // =========================================================
  //  PAGE 5 — Trabalhadores Temporários (branching question)
  // =========================================================

  form.addPageBreakItem()
    .setTitle('Trabalhadores Temporários');

  var q15 = form.addMultipleChoiceItem()
    .setTitle('15) Em períodos de maior movimento, como Carnaval, Réveillon e grandes eventos, o estabelecimento costuma contratar trabalhadores temporários ou freelancers?');
  // Choices with branching will be set after pages are created
  q15.setRequired(true);

  // =========================================================
  //  PAGE 6 — Detalhes sobre trabalhadores temporários (conditional: Q15 = Sim)
  // =========================================================

  var pageTemporariosDetalhes = form.addPageBreakItem()
    .setTitle('Detalhes sobre contratação temporária');
  pageTemporariosDetalhes.setHelpText('Responda apenas se contrata temporários em períodos de maior movimento.');

  form.addTextItem()
    .setTitle('15a) Se sim: quantas pessoas, aproximadamente?')
    .setHelpText('Resposta numérica.')
    .setRequired(false);

  // =========================================================
  //  PAGE 7 — Turismo
  // =========================================================

  var pageTurismo = form.addPageBreakItem()
    .setTitle('Turismo');

  var q16 = form.addMultipleChoiceItem()
    .setTitle('16) Aproximadamente qual percentual dos seus clientes é formado por turistas?');
  q16.setChoices([
    q16.createChoice('Até 10%'),
    q16.createChoice('11% a 25%'),
    q16.createChoice('26% a 50%'),
    q16.createChoice('51% a 75%'),
    q16.createChoice('Mais de 75%'),
    q16.createChoice('Não sabemos informar')
  ]);
  q16.setRequired(true);

  var q17 = form.addMultipleChoiceItem()
    .setTitle('17) Entre os turistas que frequentam o estabelecimento, há presença de turistas estrangeiros?');
  // Choices with branching will be set after pages are created
  q17.setRequired(true);

  // =========================================================
  //  PAGE 8 — Nacionalidades estrangeiras (conditional: Q17 = Sim)
  // =========================================================

  var pageNacionalidades = form.addPageBreakItem()
    .setTitle('Turistas Estrangeiros');
  pageNacionalidades.setHelpText('Responda apenas se há presença de turistas estrangeiros.');

  form.addTextItem()
    .setTitle('17a) Quais são as principais nacionalidades dos turistas estrangeiros?')
    .setHelpText('Pergunta opcional.')
    .setRequired(false);

  // =========================================================
  //  PAGE 9 — Fornecedores
  // =========================================================

  var pageFornecedores = form.addPageBreakItem()
    .setTitle('Fornecedores');

  form.addTextItem()
    .setTitle('18) Aproximadamente quanto o estabelecimento movimenta mensalmente com a compra de produtos e serviços de fornecedores? (em R$)')
    .setHelpText('Considere, por exemplo, bebidas, alimentos, produtos de limpeza, serviços de manutenção e outros fornecedores.')
    .setRequired(true);

  var q19 = form.addMultipleChoiceItem()
    .setTitle('19) Aproximadamente qual percentual dos fornecedores do estabelecimento está localizado na cidade do Rio de Janeiro?');
  q19.setChoices([
    q19.createChoice('Até 25%'),
    q19.createChoice('26% a 50%'),
    q19.createChoice('51% a 75%'),
    q19.createChoice('76% a 100%'),
    q19.createChoice('Não sabemos informar')
  ]);
  q19.setRequired(true);

  // =========================================================
  //  PAGE 10 — Impacto e Contribuição
  // =========================================================

  form.addPageBreakItem()
    .setTitle('Impacto e Contribuição');

  form.addParagraphTextItem()
    .setTitle('20) Na sua opinião, qual é a principal contribuição do seu estabelecimento para a economia, o turismo e a cultura do Rio?')
    .setRequired(false);

  // =========================================================
  //  SET BRANCHING
  //
  //  Q15: "Sim" → pageTemporariosDetalhes
  //       "Não" → pageTurismo
  //  pageTemporariosDetalhes → pageTurismo (skip nothing, next in sequence)
  //
  //  Q17: "Sim, com frequência" → pageNacionalidades
  //       "Sim, ocasionalmente" → pageNacionalidades
  //       others               → pageFornecedores
  //  pageNacionalidades → pageFornecedores
  // =========================================================

  q15.setChoices([
    q15.createChoice('Sim', pageTemporariosDetalhes),
    q15.createChoice('Não', pageTurismo)
  ]);

  // After temporários details, continue to turismo
  pageTemporariosDetalhes.setGoToPage(pageTurismo);

  q17.setChoices([
    q17.createChoice('Sim, com frequência', pageNacionalidades),
    q17.createChoice('Sim, ocasionalmente', pageNacionalidades),
    q17.createChoice('Raramente', pageFornecedores),
    q17.createChoice('Não', pageFornecedores),
    q17.createChoice('Não sabemos informar', pageFornecedores)
  ]);

  // After nacionalidades, continue to fornecedores
  pageNacionalidades.setGoToPage(pageFornecedores);

  // Log the URL
  var url = form.getPublishedUrl();
  var editUrl = form.getEditUrl();
  Logger.log('');
  Logger.log('=== FORM CREATED SUCCESSFULLY ===');
  Logger.log('');
  Logger.log('Published URL (share this with respondents):');
  Logger.log(url);
  Logger.log('');
  Logger.log('Edit URL (manage the form):');
  Logger.log(editUrl);
  Logger.log('');
  Logger.log('Total items: ' + form.getItems().length);
}
