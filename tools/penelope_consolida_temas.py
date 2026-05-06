#!/usr/bin/env python3
"""Penelope Etapa 2 helper: consolida temas from analise-individual.md.

Reads `Show da Shakira/analise-individual.md` and produces a
quantitative draft of `Show da Shakira/consolidacao-temas.md`.

This script does the **mechanical** part of Etapa 2:
- Extracts each finished article block (skips EM ANDAMENTO stubs).
- Parses the "Temas Identificados" markdown table per block.
- Groups thematically-similar tema names (string normalization +
  optional manual aliases in `tools/penelope_temas_aliases.json`).
- Computes counts per tema, sentiment distribution, and top rankings.
- Emits the draft consolidação file.

The classifier agent must then refine the **narrative synthesis** per
category (the prose paragraphs in each section), since clustering names
mechanically does not capture the editorial framing the workflow asks
for.

Usage:
  python3 tools/penelope_consolida_temas.py --dry-run   # print to stdout
  python3 tools/penelope_consolida_temas.py             # write the file
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALISE = ROOT / "Show da Shakira" / "analise-individual.md"
CONSOLIDA = ROOT / "Show da Shakira" / "consolidacao-temas.md"
ALIAS_PATH = ROOT / "tools" / "penelope_temas_aliases.json"

SENTIMENT_ORDER = [
    "muito negativo", "negativo", "neutro", "positivo", "muito positivo", "n/a",
]


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9 ]+", " ", s).lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_tema(s: str, aliases: dict[str, str]) -> str:
    raw = s.strip().strip('"').strip("'").strip()
    slug = slugify(raw)
    return aliases.get(slug, raw)


def normalize_sentiment(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("muitonegativo", "muito negativo")
    s = s.replace("muitopositivo", "muito positivo")
    if not s or s == "n/a" or s == "na":
        return "n/a"
    for k in SENTIMENT_ORDER:
        if k != "n/a" and k in s:
            return k
    return s


ARTICLE_BLOCK_RE = re.compile(
    r"^## (a-\d+) — (?!EM ANDAMENTO)(.+?)$(?P<body>.*?)(?=\n## |\Z)",
    re.MULTILINE | re.DOTALL,
)
TEMA_TABLE_RE = re.compile(
    r"^\| Tema \| Como é tratado \| Classificação \|.*?\n((?:^\|.*\n)+)",
    re.MULTILINE,
)
GERAL_RE = re.compile(
    r"\*\*Sentimento geral do artigo:\*\*\s*([^\n]+)", re.IGNORECASE
)


def parse_blocks(md: str, aliases: dict[str, str]) -> list[dict]:
    out = []
    for m in ARTICLE_BLOCK_RE.finditer(md):
        aid = m.group(1)
        title = m.group(2).strip()
        body = m.group("body")
        # Find tema table
        tt = TEMA_TABLE_RE.search(body)
        temas = []
        if tt:
            for row in tt.group(1).splitlines():
                cells = [c.strip() for c in row.strip("|").split("|")]
                if len(cells) < 3:
                    continue
                if cells[0].startswith("---"):
                    continue
                tema_name = normalize_tema(cells[0], aliases)
                tratamento = cells[1]
                sentiment = normalize_sentiment(cells[2])
                temas.append({"tema": tema_name, "tratamento": tratamento, "sentiment": sentiment})
        gm = GERAL_RE.search(body)
        geral = normalize_sentiment(gm.group(1)) if gm else None
        out.append({"id": aid, "title": title, "temas": temas, "geral": geral})
    return out


def build_consolida(blocks: list[dict]) -> str:
    lines = []
    n_total = len(blocks)
    n_off = sum(1 for b in blocks if b.get("geral") == "n/a")
    n_in_scope = n_total - n_off

    geral_dist = Counter(b.get("geral") or "n/a" for b in blocks)
    tema_articles = defaultdict(set)
    tema_sentiments = defaultdict(Counter)
    for b in blocks:
        for t in b["temas"]:
            tema_articles[t["tema"]].add(b["id"])
            tema_sentiments[t["tema"]][t["sentiment"]] += 1

    lines.append("# Consolidação Temática — Show da Shakira\n")
    lines.append(
        "> Documento gerado por `tools/penelope_consolida_temas.py` a partir\n"
        "> de `analise-individual.md`. As contagens e tabelas são mecânicas;\n"
        "> a **síntese narrativa** por categoria abaixo é placeholder e deve\n"
        "> ser preenchida manualmente pela Penelope/classificador na próxima\n"
        "> sessão.\n"
    )
    lines.append("## Sumário Quantitativo\n")
    lines.append(f"- Total de artigos analisados: **{n_total}**")
    lines.append(f"- Artigos em escopo: **{n_in_scope}**")
    lines.append(f"- Artigos fora de escopo: **{n_off}**")
    lines.append("")
    lines.append("**Distribuição geral de sentimento:**\n")
    lines.append("| Muito Negativo | Negativo | Neutro | Positivo | Muito Positivo | N/A |")
    lines.append("|---|---|---|---|---|---|")
    lines.append(
        "| {} | {} | {} | {} | {} | {} |".format(
            geral_dist.get("muito negativo", 0),
            geral_dist.get("negativo", 0),
            geral_dist.get("neutro", 0),
            geral_dist.get("positivo", 0),
            geral_dist.get("muito positivo", 0),
            geral_dist.get("n/a", 0),
        )
    )
    lines.append("")

    # Frequency ranking
    lines.append("## Temas (lista bruta — antes de agrupamento por categoria)\n")
    lines.append("> A próxima Penelope deve agrupar temas similares em **categorias**\n"
                 "> editoriais (ex.: `filas de entrada`, `banheiros`, `acessibilidade` →\n"
                 "> categoria `Infraestrutura do Evento`) e re-emitir esta seção. Por\n"
                 "> ora, lista bruta abaixo:\n")
    sorted_temas = sorted(tema_articles.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    for tema, articles in sorted_temas:
        sd = tema_sentiments[tema]
        dist_str = "/".join(
            str(sd.get(s, 0)) for s in SENTIMENT_ORDER if s != "n/a"
        )
        lines.append(
            f"- **{tema}** — {len(articles)} artigo(s); sentimentos "
            f"(MN/N/Ne/P/MP): {dist_str}; IDs: {', '.join(sorted(articles))}"
        )
    lines.append("")

    # Rankings
    def rank(metric_fn, n=10):
        return sorted(tema_articles.keys(), key=metric_fn, reverse=True)[:n]

    most_freq = rank(lambda t: len(tema_articles[t]))
    most_pos = rank(lambda t: tema_sentiments[t]["muito positivo"] * 2 + tema_sentiments[t]["positivo"])
    most_neg = rank(lambda t: tema_sentiments[t]["muito negativo"] * 2 + tema_sentiments[t]["negativo"])

    lines.append("## Rankings\n")
    lines.append("### Temas mais frequentes\n")
    for i, t in enumerate(most_freq, 1):
        lines.append(f"{i}. {t} ({len(tema_articles[t])} artigos)")
    lines.append("")
    lines.append("### Temas mais elogiados (peso 2× muito-positivo + 1× positivo)\n")
    for i, t in enumerate(most_pos, 1):
        sd = tema_sentiments[t]
        lines.append(f"{i}. {t} (MP={sd['muito positivo']}, P={sd['positivo']})")
    lines.append("")
    lines.append("### Temas mais criticados (peso 2× muito-negativo + 1× negativo)\n")
    for i, t in enumerate(most_neg, 1):
        sd = tema_sentiments[t]
        lines.append(f"{i}. {t} (MN={sd['muito negativo']}, N={sd['negativo']})")
    lines.append("")

    # Categorias placeholder
    lines.append("## Categorias Temáticas\n")
    lines.append("> Placeholder. Próxima Penelope agrupa os temas brutos acima\n"
                 "> em categorias e preenche cada `[Nome da Categoria]` com\n"
                 "> síntese narrativa conforme exigido pela Etapa 2 do plano.\n"
                 "> Cada categoria deve ter:\n"
                 "> - Lista dos temas componentes (slugs)\n"
                 "> - Frequência (N de artigos / % do total)\n"
                 "> - Distribuição de sentimento (tabela)\n"
                 "> - Síntese narrativa (parágrafo)\n")
    lines.append("### [Categoria — preencher]\n")
    lines.append("**Temas agrupados:** [...]\n\n"
                 "**Frequência:** N artigos (X%)\n\n"
                 "**Distribuição de sentimento:** [...]\n\n"
                 "**Síntese narrativa:** [...]\n")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="print, don't write")
    p.add_argument("--input", type=Path, default=ANALISE)
    p.add_argument("--output", type=Path, default=CONSOLIDA)
    p.add_argument("--aliases", type=Path, default=ALIAS_PATH)
    args = p.parse_args(argv[1:])

    if not args.input.exists():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 1

    aliases = {}
    if args.aliases.exists():
        with args.aliases.open() as f:
            aliases = json.load(f)

    md = args.input.read_text()
    blocks = parse_blocks(md, aliases)
    print(f"# parsed {len(blocks)} article blocks", file=sys.stderr)
    if not blocks:
        print("no finished blocks parsed; nothing to consolidate", file=sys.stderr)
        return 1

    out = build_consolida(blocks)
    if args.dry_run:
        print(out)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(out)
        print(f"# wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
