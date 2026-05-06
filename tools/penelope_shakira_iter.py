#!/usr/bin/env python3
"""Penelope's iteration helper for the Show da Shakira workflow.

Usage:
  # 1. With a fresh assets/clipping-data.json + clipping-raw-texts.json
  #    (either freshly committed by Otávio, or pulled by the GitHub Action
  #    in .github/workflows/penelope-fetch-shakira.yml):
  python3 tools/penelope_shakira_iter.py list
  python3 tools/penelope_shakira_iter.py show a-NNN
  python3 tools/penelope_shakira_iter.py todo  # IDs not yet in analise-individual.md
  python3 tools/penelope_shakira_iter.py stub a-NNN  # emit EM ANDAMENTO block

This script does NOT write the analysis itself — that requires the
classifier agent's judgment. It mechanizes the iteration bookkeeping
defined in `Show da Shakira/workflow-classificacao-shakira.md` Etapa 1.

Two data-source modes (auto-selected; first hit wins):
  1. tools/penelope-fetched/assets_clipping-data.json + ...raw-texts.json
     (when committed by the GitHub Action workaround)
  2. assets/clipping-data.json + assets/clipping-raw-texts.json
     (the standard committed snapshot)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALISE = ROOT / "Show da Shakira" / "analise-individual.md"
TARGET_KEY = "shakira"

DATA_PATHS = [
    (ROOT / "tools" / "penelope-fetched" / "assets_clipping-data.json",
     ROOT / "tools" / "penelope-fetched" / "assets_clipping-raw-texts.json"),
    (ROOT / "assets" / "clipping-data.json",
     ROOT / "assets" / "clipping-raw-texts.json"),
]


def load_data() -> tuple[dict, dict, Path]:
    for data_path, raw_path in DATA_PATHS:
        if data_path.exists():
            with data_path.open() as f:
                data = json.load(f)
            raw = {}
            if raw_path.exists():
                with raw_path.open() as f:
                    raw = json.load(f)
            return data, raw, data_path
    raise SystemExit(
        "No clipping-data.json found in either tools/penelope-fetched/ or "
        "assets/. Trigger the GitHub Action or wait for Otávio's commit."
    )


def shakira_articles(data: dict, raw: dict) -> list[dict]:
    """Yield one record per unique articleId that touches the Shakira target.

    Inclusion rule (broad):
      - article.targetKeys contains 'shakira', OR
      - story.targetKeys contains 'shakira' (article inherits via story), OR
      - 'shakira' (case-insensitive) appears in title / summaryPreview / raw text.

    The classifier later marks "fora de escopo" inside the analysis block
    if the article is only tangentially related (per workflow rule).
    """
    out: dict[int, dict] = {}
    for story in data.get("stories", []):
        story_keys = set(story.get("targetKeys") or [])
        story_in_scope = TARGET_KEY in story_keys
        for art in story.get("articles") or []:
            aid = int(art.get("articleId") or 0)
            if not aid or aid in out:
                continue
            article_keys = set(art.get("targetKeys") or [])
            article_in_scope = TARGET_KEY in article_keys
            rkey = art.get("rawTextKey") or ""
            rtext = raw.get(rkey, "") if rkey else ""
            haystack = " ".join([
                str(art.get("title") or ""),
                str(art.get("summaryPreview") or ""),
                rtext,
            ]).lower()
            mention_in_text = "shakira" in haystack
            if not (article_in_scope or story_in_scope or mention_in_text):
                continue
            out[aid] = {
                "id": f"a-{aid}",
                "articleId": aid,
                "title": art.get("title") or "",
                "url": art.get("url") or "",
                "sourceName": art.get("sourceName") or "",
                "sourceHost": art.get("sourceHost") or "",
                "publishedAt": art.get("publishedAt") or "",
                "publishedDisplay": art.get("publishedDisplay") or "",
                "rawTextKey": rkey,
                "rawText": rtext,
                "summaryPreview": art.get("summaryPreview") or "",
                "summaryLabel": art.get("summaryLabel") or "",
                "targetKeys": sorted(article_keys),
                "storyTitle": story.get("title") or "",
                "storyId": story.get("storyIdInt"),
                "storyInScope": story_in_scope,
                "articleInScope": article_in_scope,
                "mentionOnlyInText": (
                    mention_in_text and not (article_in_scope or story_in_scope)
                ),
            }
    return sorted(out.values(), key=lambda r: r["publishedAt"])


def already_done(text: str) -> set[str]:
    return set(re.findall(r"^## (a-\d+)\b", text, re.MULTILINE))


def in_progress(text: str) -> set[str]:
    return set(re.findall(r"^## (a-\d+) — EM ANDAMENTO", text, re.MULTILINE))


def emit_stub(rec: dict, agent: str = "Penelope") -> str:
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        f"\n---\n## {rec['id']} — EM ANDAMENTO\n"
        f"**Subagente:** {agent}\n"
        f"**Início:** {ts}\n"
    )


def cmd_list(data: dict, raw: dict) -> int:
    arts = shakira_articles(data, raw)
    print(f"shakira-touching articles: {len(arts)}")
    for r in arts:
        flag = "" if r["articleInScope"] else (" [story-only]" if r["storyInScope"] else " [text-only]")
        print(f"  {r['id']:>8s}  {r['publishedDisplay']:<22s}  {r['sourceName'][:30]:<30s}  {r['title'][:80]}{flag}")
    return 0


def cmd_show(data: dict, raw: dict, aid: str) -> int:
    aid = aid if aid.startswith("a-") else f"a-{aid}"
    arts = shakira_articles(data, raw)
    rec = next((r for r in arts if r["id"] == aid), None)
    if not rec:
        print(f"not found: {aid}", file=sys.stderr)
        return 1
    out = dict(rec)
    out["rawTextLen"] = len(rec["rawText"])
    out["rawTextPreview"] = rec["rawText"][:600]
    out.pop("rawText", None)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print("\n--- raw text (full) ---\n")
    print(rec["rawText"])
    return 0


def cmd_todo(data: dict, raw: dict) -> int:
    arts = shakira_articles(data, raw)
    if not ANALISE.exists():
        done = set()
        wip = set()
    else:
        text = ANALISE.read_text()
        done = already_done(text)
        wip = in_progress(text)
    todo = [r for r in arts if r["id"] not in done]
    print(f"total shakira articles available: {len(arts)}")
    print(f"already in analise-individual.md (any state): {len(done)}")
    print(f"in EM ANDAMENTO state: {len(wip)}")
    print(f"todo: {len(todo)}")
    for r in todo:
        print(f"  {r['id']}  {r['publishedDisplay']}  {r['title'][:90]}")
    return 0


def cmd_stub(data: dict, raw: dict, aid: str) -> int:
    aid = aid if aid.startswith("a-") else f"a-{aid}"
    print(emit_stub({"id": aid}))
    return 0


def emit_template(rec: dict) -> str:
    """Empty Etapa-1-shaped block ready to be filled in."""
    return f"""\n---\n## {rec['id']} — {rec['title']}

**Fonte:** {rec['sourceName']} ({rec['sourceHost']})
**Data:** {rec['publishedDisplay']}
**URL:** {rec['url']}

### Resumo Narrativo

[FILL: 1–3 parágrafos em prosa contextualizada descrevendo o
enquadramento, pontos centrais, e a história que o artigo conta. Sem
bullet points. Tom explicativo. Se off-scope: começar com "Artigo fora
de escopo — não trata do show da Shakira [de 2026]." e dar 1 parágrafo
curto de contexto.]

### Temas Identificados

| Tema | Como é tratado | Classificação |
|------|---------------|---------------|
| [tema 1] | [posicionamento] | [muito negativo / negativo / neutro / positivo / muito positivo] |
| [tema 2] | [...] | [...] |

### Classificação Geral

**Sentimento geral do artigo:** [muito negativo / negativo / neutro / positivo / muito positivo / N/A se off-scope]
"""


def cmd_template(data: dict, raw: dict, aid: str) -> int:
    aid = aid if aid.startswith("a-") else f"a-{aid}"
    arts = shakira_articles(data, raw)
    rec = next((r for r in arts if r["id"] == aid), None)
    if not rec:
        print(f"not found: {aid}", file=sys.stderr)
        return 1
    print(emit_template(rec))
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    data, raw, src = load_data()
    print(f"# data source: {src.relative_to(ROOT)} (generated {data.get('meta',{}).get('generatedAt')})", file=sys.stderr)
    cmd = argv[1]
    if cmd == "list":
        return cmd_list(data, raw)
    if cmd == "show" and len(argv) >= 3:
        return cmd_show(data, raw, argv[2])
    if cmd == "todo":
        return cmd_todo(data, raw)
    if cmd == "stub" and len(argv) >= 3:
        return cmd_stub(data, raw, argv[2])
    if cmd == "template" and len(argv) >= 3:
        return cmd_template(data, raw, argv[2])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
