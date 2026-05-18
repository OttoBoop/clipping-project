# Demo Script And Buyer Assumptions

_Created 2026-05-18 by Atlas/Codex._

Use this only after the FastAPI scoped login is deployed or available locally
for a controlled demo.

## Demo Goal

Show a political buyer that the product is private, focused, and useful without
claiming it is a full enterprise monitoring platform.

## Short Demo Script

1. "Este é um painel privado de clipping. Cada cliente entra com a própria
   senha."
2. "O ponto principal é que o cliente só vê os nomes e temas dele. Isso evita
   misturar assuntos de outros projetos."
3. Log in with the demo/client profile.
4. "Aqui estão as notícias agrupadas por assunto, não apenas uma lista solta de
   links."
5. Open one story and one article.
6. "Quando existe texto completo salvo, ele aparece dentro do próprio painel."
7. "Os controles de atualização e cadastro não aparecem para o cliente. Eu faço
   essa operação por trás, para manter a base limpa."
8. "A versão inicial serve para acompanhar menções, organizar narrativas e não
   perder assunto importante."
9. "Alertas, relatórios customizados e análise mais profunda podem entrar como
   pacote maior depois."

## What To Avoid Saying

- "É inteligência política completa."
- "Monitora tudo em tempo real."
- "Substitui assessoria de imprensa."
- "Já tem indicador econômico pronto."
- "Cada cliente terá um site próprio."
- "Pode usar GitHub Pages/Wix como área privada."

## Buyer Assumptions To Validate

- The buyer cares about not missing mentions.
- The buyer prefers a private dashboard over only receiving loose links.
- Grouped stories are easier to read than raw clipping lists.
- A staffer will accept Otavio/admin running updates instead of self-service.
- Weekly or daily updates are enough for V1.
- Manual WhatsApp/PDF summaries can be an add-on, not the default.
- A lower-complexity product is attractive if it is cheaper than large
  monitoring platforms.

## Demo Preconditions

- Use a profile with no cross-client leakage.
- For external buyers, create or choose a dedicated demo/client profile rather
  than exposing Flavio or Shakira credentials.
- Confirm logged-out JSON returns `401`.
- Confirm the profile view hides operator controls.
- Confirm the raw-text payload is scoped.
- Do not use a static export as the private demo.
- Rotate any demo password after a real sales conversation if access should
  expire.

## Questions To Ask After Demo

- "Como vocês acompanham clipping hoje?"
- "Quem lê isso no gabinete?"
- "Vocês preferem painel, WhatsApp, PDF ou todos?"
- "Qual frequência de atualização seria útil?"
- "O que faria vocês confiarem ou não confiarem no resultado?"
- "Que tipo de notícia seria ruído para vocês?"
- "Quanto tempo da equipe isso economizaria por semana?"
