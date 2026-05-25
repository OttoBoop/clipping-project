/**
 * Questionario Programadores Cariocas — Google Apps Script
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
 * The script creates the form with all 26 questions, conditional
 * page branching for the employment section, and proper Portuguese text.
 */

function createForm() {
  var form = FormApp.create('Questionário Programadores Cariocas');
  form.setDescription(
    'Pesquisa com alunos e ex-alunos do programa Programadores Cariocas. ' +
    'Suas respostas são importantes para avaliar o impacto do programa e ' +
    'melhorar futuras edições. Obrigado por participar!'
  );
  form.setIsQuiz(false);
  form.setCollectEmail(false);
  form.setAllowResponseEdits(true);
  form.setProgressBar(true);

  // =========================================================
  //  PAGE 1 — Dados Pessoais
  // =========================================================

  form.addTextItem()
    .setTitle('1) Nome completo')
    .setRequired(true);

  form.addTextItem()
    .setTitle('2) Idade (em anos)')
    .setRequired(true);

  var q3 = form.addMultipleChoiceItem()
    .setTitle('3) Gênero');
  q3.setChoices([
    q3.createChoice('Feminino'),
    q3.createChoice('Masculino'),
    q3.createChoice('Prefiro não dizer')
  ]);
  q3.showOtherOption(true);
  q3.setRequired(true);

  form.addTextItem()
    .setTitle('4) Bairro onde reside atualmente')
    .setRequired(true);

  // =========================================================
  //  PAGE 2 — Formação no Programa
  // =========================================================

  form.addPageBreakItem()
    .setTitle('Formação no Programa');

  var q5 = form.addMultipleChoiceItem()
    .setTitle('5) Você concluiu o ensino médio em:');
  q5.setChoices([
    q5.createChoice('Escola pública'),
    q5.createChoice('EJA (Educação de Jovens e Adultos)'),
    q5.createChoice('Não concluí')
  ]);
  q5.setRequired(true);

  var q6 = form.addMultipleChoiceItem()
    .setTitle('6) Em qual bairro você frequentou o curso dos Programadores Cariocas?');
  q6.setChoices([
    q6.createChoice('Bangu'),
    q6.createChoice('Centro'),
    q6.createChoice('Centro Politécnico'),
    q6.createChoice('Jacarepaguá'),
    q6.createChoice('Senac Bonsucesso'),
    q6.createChoice('Senac Campo Grande'),
    q6.createChoice('Senac Irajá'),
    q6.createChoice('Senac Madureira')
  ]);
  q6.setRequired(true);

  var q6a = form.addMultipleChoiceItem()
    .setTitle('6.a) Você concluiu o curso?');
  q6a.setChoices([
    q6a.createChoice('Sim'),
    q6a.createChoice('Não')
  ]);
  q6a.setRequired(true);

  var q6b = form.addMultipleChoiceItem()
    .setTitle('6.b) Se a resposta anterior foi "Não", por qual motivo não concluiu o curso?');
  q6b.setChoices([
    q6b.createChoice('Trabalhava, estava procurando trabalho ou conseguiu trabalho durante o curso'),
    q6b.createChoice('O auxílio dado durante o programa não foi suficiente para a sua manutenção durante o período necessário para a conclusão (transporte, material escolar etc)'),
    q6b.createChoice('Por ter que cuidar dos afazeres domésticos ou de crianças ou idoso ou pessoa com necessidades especiais'),
    q6b.createChoice('Dificuldade em entender o conteúdo e/ou falta de interesse. Não gostei da profissão'),
    q6b.createChoice('Esperava mais do curso, não ficou satisfeito com a qualidade oferecida e resolveu sair, apesar do interesse na área')
  ]);
  q6b.showOtherOption(true);
  q6b.setRequired(false);
  q6b.setHelpText('Preencha apenas se NÃO concluiu o curso.');

  var q7 = form.addMultipleChoiceItem()
    .setTitle('7) Qual foi o seu eixo de formação?');
  q7.setChoices([
    q7.createChoice('Full Stack (Front-end e Back-end)'),
    q7.createChoice('Front-end'),
    q7.createChoice('Back-end'),
    q7.createChoice('Mobile')
  ]);
  q7.showOtherOption(true);
  q7.setRequired(true);

  // =========================================================
  //  PAGE 3 — Avaliação do Curso
  // =========================================================

  form.addPageBreakItem()
    .setTitle('Avaliação do Curso');

  var q8 = form.addMultipleChoiceItem()
    .setTitle('8) Como você avalia a qualidade do conteúdo técnico do curso?');
  q8.setChoices([
    q8.createChoice('Excelente'),
    q8.createChoice('Bom'),
    q8.createChoice('Regular'),
    q8.createChoice('Ruim'),
    q8.createChoice('Péssimo')
  ]);
  q8.setRequired(true);

  var q9 = form.addMultipleChoiceItem()
    .setTitle('9) E sobre os instrutores/professores?');
  q9.setChoices([
    q9.createChoice('Muito bons'),
    q9.createChoice('Bons'),
    q9.createChoice('Regulares'),
    q9.createChoice('Ruins'),
    q9.createChoice('Péssimos')
  ]);
  q9.setRequired(true);

  var q10 = form.addMultipleChoiceItem()
    .setTitle('10) O curso contribuiu para desenvolver suas competências comportamentais (soft skills) (ex: trabalho em equipe, comunicação)?');
  q10.setChoices([
    q10.createChoice('Sim, muito'),
    q10.createChoice('Sim, em parte'),
    q10.createChoice('Pouco'),
    q10.createChoice('Não')
  ]);
  q10.setRequired(true);

  // =========================================================
  //  PAGE 4 — Situação Antes e Depois (Maira's additions)
  // =========================================================

  form.addPageBreakItem()
    .setTitle('Situação Antes e Depois do Programa');

  var q11 = form.addMultipleChoiceItem()
    .setTitle('11) Antes de participar do programa, qual era sua situação de trabalho?');
  q11.setChoices([
    q11.createChoice('Trabalhava na área de tecnologia com carteira assinada'),
    q11.createChoice('Trabalhava em outra área com carteira assinada'),
    q11.createChoice('Trabalhava na área de tecnologia sem carteira assinada/freelancer'),
    q11.createChoice('Trabalhava em outra área sem carteira assinada'),
    q11.createChoice('Procurava trabalho (desempregado)'),
    q11.createChoice('Não trabalhava nem procurava trabalho')
  ]);
  q11.showOtherOption(true);
  q11.setRequired(true);

  var q12 = form.addMultipleChoiceItem()
    .setTitle('12) Antes de participar do programa, você estudava?');
  q12.setChoices([
    q12.createChoice('Não estudava'),
    q12.createChoice('Curso técnico/profissionalizante'),
    q12.createChoice('Ensino superior em tempo integral'),
    q12.createChoice('Ensino superior em tempo parcial'),
    q12.createChoice('Pós-graduação')
  ]);
  q12.showOtherOption(true);
  q12.setRequired(true);

  var q13 = form.addMultipleChoiceItem()
    .setTitle('13) Atualmente, qual é sua situação de trabalho?');
  q13.setChoices([
    q13.createChoice('Trabalho na área de tecnologia com carteira assinada'),
    q13.createChoice('Trabalho em outra área com carteira assinada'),
    q13.createChoice('Trabalho na área de tecnologia sem carteira assinada/freelancer'),
    q13.createChoice('Trabalho em outra área sem carteira assinada'),
    q13.createChoice('Estou procurando trabalho'),
    q13.createChoice('Não trabalho nem procuro trabalho')
  ]);
  q13.showOtherOption(true);
  q13.setRequired(true);

  var q14 = form.addMultipleChoiceItem()
    .setTitle('14) Atualmente, você estuda?');
  q14.setChoices([
    q14.createChoice('Não estudo'),
    q14.createChoice('Curso técnico/profissionalizante'),
    q14.createChoice('Ensino superior em tempo integral'),
    q14.createChoice('Ensino superior em tempo parcial'),
    q14.createChoice('Pós-graduação')
  ]);
  q14.showOtherOption(true);
  q14.setRequired(true);

  // =========================================================
  //  PAGE 5 — Resultados Profissionais (branching question)
  // =========================================================

  form.addPageBreakItem()
    .setTitle('Resultados Profissionais');

  var q15 = form.addMultipleChoiceItem()
    .setTitle('15) Você já conseguiu algum trabalho ou remuneração na área de formação do curso após concluir?');
  // Choices with branching will be set after all pages are created
  q15.setRequired(true);

  // =========================================================
  //  PAGE 6 — Working in tech (conditional: Q15 = Sim)
  // =========================================================

  var pageYes = form.addPageBreakItem()
    .setTitle('Detalhes sobre seu trabalho na área de tecnologia');
  pageYes.setHelpText('Responda estas perguntas caso esteja trabalhando na área de tecnologia.');

  form.addTextItem()
    .setTitle('16.a) Qual é o nome da(s) empresa(s) ou plataforma(s)?')
    .setRequired(false);

  form.addTextItem()
    .setTitle('16.b) Qual o seu cargo?')
    .setRequired(false);

  var q16c = form.addMultipleChoiceItem()
    .setTitle('16.c) As empresas ou trabalhos freelancer (temporários) são:');
  q16c.setChoices([
    q16c.createChoice('Nacionais'),
    q16c.createChoice('Internacionais'),
    q16c.createChoice('Ambos')
  ]);
  q16c.setRequired(true);

  var q16d = form.addMultipleChoiceItem()
    .setTitle('16.d) Você foi contratado como resultado direto do programa (ex: via indicações, parcerias etc.)?');
  q16d.setChoices([
    q16d.createChoice('Sim'),
    q16d.createChoice('Não')
  ]);
  q16d.setRequired(true);

  var q16e = form.addMultipleChoiceItem()
    .setTitle('16.e) Quanto tempo após o término do curso você conseguiu seu primeiro trabalho/remuneração na área?');
  q16e.setChoices([
    q16e.createChoice('Antes mesmo de concluir o curso'),
    q16e.createChoice('Em até 3 meses'),
    q16e.createChoice('De 3 a 6 meses'),
    q16e.createChoice('Mais de 6 meses')
  ]);
  q16e.setRequired(true);

  // =========================================================
  //  PAGE 7 — NOT working in tech (conditional: Q15 = Não)
  // =========================================================

  var pageNo = form.addPageBreakItem()
    .setTitle('Para quem ainda não está trabalhando na área de tecnologia');
  pageNo.setHelpText('Responda estas perguntas caso NÃO esteja trabalhando na área de tecnologia.');

  form.addTextItem()
    .setTitle('16.f) Há quanto tempo você concluiu o curso? (responda em número de meses)')
    .setRequired(false);

  var q16g = form.addMultipleChoiceItem()
    .setTitle('16.g) Qual tem sido sua maior barreira?');
  q16g.setChoices([
    q16g.createChoice('Falta de vagas'),
    q16g.createChoice('Falta de conhecimento adquirido no curso'),
    q16g.createChoice('Dificuldades nas entrevistas'),
    q16g.createChoice('Falta de inglês')
  ]);
  q16g.showOtherOption(true);
  q16g.setRequired(true);

  var q16h = form.addMultipleChoiceItem()
    .setTitle('16.h) Chegou a trabalhar em algum momento entre o período do curso e o atual?');
  q16h.setChoices([
    q16h.createChoice('Não'),
    q16h.createChoice('Sim, mas fui demitido(a)'),
    q16h.createChoice('Sim, mas quis trocar de emprego na mesma área e ainda estou buscando'),
    q16h.createChoice('Sim, mas quis trocar de área')
  ]);
  q16h.setRequired(true);

  // =========================================================
  //  PAGE 8 — Impacto do Programa
  // =========================================================

  var pageImpact = form.addPageBreakItem()
    .setTitle('Impacto do Programa');

  var q17 = form.addMultipleChoiceItem()
    .setTitle('17) Em relação à sua situação antes do curso, como você avalia sua situação financeira atual?');
  q17.setChoices([
    q17.createChoice('Melhorou muito'),
    q17.createChoice('Melhorou'),
    q17.createChoice('Não mudou'),
    q17.createChoice('Piorou')
  ]);
  q17.setRequired(true);

  var q18 = form.addMultipleChoiceItem()
    .setTitle('18) Em relação à sua situação antes do curso, de quanto foi o seu aumento em ganho salarial?');
  q18.setChoices([
    q18.createChoice('Mais de R$ 5 mil'),
    q18.createChoice('Entre R$ 3 mil e R$ 5 mil'),
    q18.createChoice('Entre R$ 1 mil e R$ 3 mil'),
    q18.createChoice('Entre R$ 500 e R$ 1 mil'),
    q18.createChoice('Menos de R$ 500'),
    q18.createChoice('Diminuiu')
  ]);
  q18.setRequired(true);

  var q19 = form.addMultipleChoiceItem()
    .setTitle('19) Em relação à sua situação antes do curso, como você avalia sua confiança em conseguir um novo emprego hoje?');
  q19.setChoices([
    q19.createChoice('Melhorou muito'),
    q19.createChoice('Melhorou'),
    q19.createChoice('Não mudou'),
    q19.createChoice('Piorou')
  ]);
  q19.setRequired(true);

  var q20 = form.addMultipleChoiceItem()
    .setTitle('20) Em relação à sua situação antes do curso, como você avalia sua autoestima e motivação em trabalhar na área hoje?');
  q20.setChoices([
    q20.createChoice('Melhorou muito'),
    q20.createChoice('Melhorou'),
    q20.createChoice('Não mudou'),
    q20.createChoice('Piorou')
  ]);
  q20.setRequired(true);

  var q21 = form.addMultipleChoiceItem()
    .setTitle('21) Em relação à sua situação antes do curso, como você avalia seu relacionamento com a tecnologia hoje?');
  q21.setChoices([
    q21.createChoice('Melhorou muito'),
    q21.createChoice('Melhorou'),
    q21.createChoice('Não mudou'),
    q21.createChoice('Piorou')
  ]);
  q21.setRequired(true);

  // =========================================================
  //  PAGE 9 — Feedback
  // =========================================================

  form.addPageBreakItem()
    .setTitle('Feedback');

  form.addParagraphTextItem()
    .setTitle('22) O que mais te marcou positivamente no programa?')
    .setRequired(false);

  form.addParagraphTextItem()
    .setTitle('23) O que poderia ser melhorado?')
    .setRequired(false);

  var q24 = form.addMultipleChoiceItem()
    .setTitle('24) Você recomendaria o programa a outras pessoas?');
  q24.setChoices([
    q24.createChoice('Sim'),
    q24.createChoice('Talvez'),
    q24.createChoice('Não')
  ]);
  q24.setRequired(true);

  form.addParagraphTextItem()
    .setTitle('25) Deixe uma mensagem para a equipe do programa, se desejar')
    .setRequired(false);

  // =========================================================
  //  SET BRANCHING: Q15 -> pageYes (Sim) or pageNo (Não)
  //                 pageYes -> pageImpact (skip pageNo)
  // =========================================================

  q15.setChoices([
    q15.createChoice('Sim', pageYes),
    q15.createChoice('Não', pageNo)
  ]);

  // After the "working in tech" page, skip to Impact (don't show "not working" page)
  pageNo.setGoToPage(pageImpact);

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
