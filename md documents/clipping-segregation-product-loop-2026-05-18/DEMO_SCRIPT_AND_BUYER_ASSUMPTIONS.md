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

## V1 Offer-Aligned Demo Script

Use this after `V1_DELIVERY_FORMAT_DECISION.md` is accepted as the current
package boundary.

Positioning:

```text
O piloto de 30 dias entrega um painel privado, duas atualizações operadas por
semana e um resumo semanal curto. A ideia é provar valor sem vender um produto
ilimitado ou em tempo real.
```

Flow:

1. Show the Render login page.
2. Explain that each client maps to a scoped profile, not a frontend-only
   filter.
3. Log in with a safe demo/prospect profile or screen-share an internal viewer
   profile without sharing credentials.
4. Show the small target/filter surface for that profile.
5. Open a grouped story and one article link.
6. Open raw text only if it is scoped to that profile.
7. Point out that update runner, target management, and classification controls
   are hidden from the viewer profile.
8. Explain the V1 rhythm:

```text
2 atualizações por semana
1 resumo semanal com 3 a 7 pontos
dashboard como fonte principal
WhatsApp/email/PDF simples só como entrega manual do resumo
```

9. Name the V1 boundary clearly:

```text
Não é alerta em tempo real.
Não é criação ilimitada de termos.
Não é site customizado por cliente.
Não é relatório político longo incluso no preço base.
```

10. Close by asking which format the buyer would actually read: dashboard,
    WhatsApp, email, or lightweight PDF/screenshot.

## V1 Demo Acceptance Bar

Before using this script with an external buyer:

```text
logged-out Render payload/API smoke passes
demo/prospect profile is dedicated or the buyer only sees operator screen-share
no Flavio/Shakira credentials are shared
profile scope has only approved target keys
weekly-summary promise is bounded to 3 to 7 bullets
password rotation/offboarding is planned for any hands-on access
```

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
- Follow `DEMO_PROFILE_STRATEGY.md`: empty demo for privacy proof, operator
  screen-share for real content, or a rotated prospect profile for serious
  hands-on access.
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
