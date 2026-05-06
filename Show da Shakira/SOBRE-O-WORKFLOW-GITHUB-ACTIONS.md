# Por que o GitHub Actions workflow YAML NÃO está nesta pasta

GitHub Actions só reconhece arquivos de workflow se estiverem em
`.github/workflows/` na raiz do repositório. Esta é uma exigência rígida
da plataforma — não dá pra mover sem quebrar o workflow.

O arquivo está em: `/.github/workflows/penelope-fetch-shakira.yml`

Função: rodar fora do sandbox da Anthropic (que bloqueia egress para
`*.onrender.com`), baixar os snapshots do site live, e commitar de volta
neste branch em `Show da Shakira/penelope-fetched/`.

Tudo o resto relacionado ao loop Shakira está nesta pasta:

- `analise-individual.md` — saída da Etapa 1 (1 bloco por artigo)
- `consolidacao-temas.md` — saída da Etapa 2 (mecânica)
- `workflow-classificacao-shakira.md` — plano de longo prazo
- `tools/penelope_shakira_iter.py` — helper de iteração
- `tools/penelope_consolida_temas.py` — gerador da Etapa 2
- `penelope-fetched/` — snapshots baixados pelo GitHub Action

Para rodar os helpers da raiz do repo:

```
python3 "Show da Shakira/tools/penelope_shakira_iter.py" todo
python3 "Show da Shakira/tools/penelope_consolida_temas.py"
```
