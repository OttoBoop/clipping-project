# Email Extraction Stats

Source file: Lista_Matriculados_Definitica_por_Ra_a_Genero.xlsx
Extraction date: 2026-05-25

## Counts

| Source | Unique emails |
|--------|--------------|
| Generation sheets | 112 |
| Senac (via CPF join to Senac_Procv) | 686 |
| Overlap (in both) | 0 |
| **Total (deduplicated)** | **798** |

## Data quality

- Malformed entries skipped: 0
- Senac CPFs with no email in Procv: 14

## How emails were extracted

- **Generation sheets** (`Alunos Generation (Inscritos)` and
  `Alunos Generation (Alunos mês 1[2])`): email is directly in
  column A. Normalized domain typos (`@gmailcom` -> `@gmail.com`).
- **Senac sheets** (`Alunos Senac (Inscritos)` and `Alunos Senac
  (Alunos mês 12)`): only have CPF (column A), no email. Joined
  each CPF to the `Senac_Procv` sheet (3663-row lookup table)
  where CPF is column A and email is column H.
- Deduplicated across all sources (case-insensitive).

## Domain normalization applied

Many entries had missing dots in domains:
- `@gmailcom` -> `@gmail.com`
- `@hotmailcom` -> `@hotmail.com`
- `@outlookcom` -> `@outlook.com`
- `@yahoocom` -> `@yahoo.com`
- etc.
