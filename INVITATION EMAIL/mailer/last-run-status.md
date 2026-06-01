# Last send-invites run

- run_id: 26777854396
- run_number: 7
- trigger sha: 866597221657677e7b251f9bece2f749b2e0b7d9
- script exit code: 0
- timestamp (UTC): 2026-06-01T19:45:36Z

## Run output (stdout + stderr)

```
[diag] event=push
[diag] source=push_trigger_file
[diag] template=INVITATION EMAIL/campaigns/programadores-cariocas-survey/invite_body.txt
[diag] recipients=<default mailer/recipients.txt>
[diag] from_name=Equipe Programadores Cariocas
[diag] subject=<from template>
[diag] dry_run=false
[diag] auth=ots (url length 98)
[diag] launching mailer...
[ots] retrieved secret from us.onetimesecret.com (HTTP 200)
[plan] from        : Equipe Programadores Cariocas <issneutro@gmail.com>
[plan] subject     : Questionário Programadores Cariocas
[plan] recipients  : 6
         - otaviobopp@gmail.com
         - otavio2809@gmail.com
         - otavio0999@gmail.com
         - otavio0999@hotmail.com
         - robaynasafra@gmail.com
         - steamargentina585@gmail.com
[plan] body preview:
---
Olá!
Você participou do Programadores Cariocas, uma iniciativa voltada à formação em tecnologia e geração de oportunidades profissionais. Agora, queremos ouvir você!
Estamos realizando uma pesquisa rápida com ex-alunos para entender como foi sua experiência no programa e acompanhar os impactos do curso na trajetória profissional e educacional dos participantes.
Sua resposta é muito importante para:
✅ avaliar os resultados do programa;
✅ identificar pontos de melhoria;
✅ fortalecer futuras iniciativas de formação e empregabilidade em tecnologia.
O questionário é simples, leva menos de 10 minutos para ser respondido e suas respostas serão tratadas de forma confidencial, sendo utilizadas apenas para fins de avaliação do programa.
📌 Acesse a pesquisa aqui: https://docs.google.com/forms/d/e/1FAIpQLSfQmMIgjqt0abvXYGw1ZO2Tl65ZKH8k0GNnGi_V70zR9Vw_xw/viewform
Sua participação faz diferença e nos ajuda a construir oportunidades ainda melhores para outros jovens e profissionais da cidade.
Agradecemos pela sua colaboração!
Atenciosamente,
Equipe Programadores Cariocas
---
[smtp] connecting to smtp.gmail.com:465 ...
[ok]    otaviobopp@gmail.com
[ok]    otavio2809@gmail.com
[ok]    otavio0999@gmail.com
[ok]    otavio0999@hotmail.com
[ok]    robaynasafra@gmail.com
[ok]    steamargentina585@gmail.com

[done] 6 sent, 0 failed.
[diag] mailer exit code: 0
```
