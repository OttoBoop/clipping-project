"""
Batch-classify all unclassified articles using Claude Haiku.

For each article the model picks 1-3 categories from the 13 base assessoria
categories. The same category set is written to every mention of that article
so coworkers can review and override via the dashboard.

Usage:
    python tools/classify_articles.py [--limit N] [--dry-run] [--verbose]

Options:
    --limit N    Process only the N most-recent unclassified articles.
    --dry-run    Call Claude, print results, but write nothing to DB.
    --verbose    Print each article title and categories assigned.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import anthropic

from pipeline.database import ClippingDB
from web_app.config import db_path
from web_app.storage_bridge import artifact_store

CATEGORIES = [
    "Causa Animal",
    "Combate ao Antissemitismo",
    "Conservação",
    "Economia",
    "Esporte e Lazer",
    "Gabinete",
    "Mandato",
    "Meio Ambiente",
    "Ordenamento",
    "Sancionado",
    "Saúde",
    "Segurança",
    "Turismo",
]

CATEGORY_SET = set(CATEGORIES)

SYSTEM_PROMPT = (
    "Você é um assistente de assessoria de imprensa de um vereador do Rio de Janeiro. "
    "Sua tarefa é categorizar notícias segundo os temas abaixo.\n\n"
    "Categorias disponíveis:\n"
    + ", ".join(CATEGORIES)
    + "\n\n"
    "Regras:\n"
    "- Selecione de 1 a 3 categorias que melhor descrevem o tema da notícia.\n"
    '- Responda SOMENTE com um array JSON de strings. Exemplo: ["Saúde","Economia"]\n'
    "- Se nenhuma categoria se aplicar claramente, responda: []\n"
    "- Não invente categorias fora da lista."
)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s{2,}")


def _strip_html(text: str) -> str:
    text = _TAG_RE.sub(" ", text or "")
    return _WS_RE.sub(" ", text).strip()


def _article_text(row: dict) -> str:
    """Return the best short text available for an article."""
    snippet = (row.get("snippet") or "").strip()
    if snippet:
        return snippet[:700]
    full = _strip_html(row.get("full_text") or "")
    return full[:700]


def _classify(client: anthropic.Anthropic, source: str, title: str, text: str) -> list[str]:
    """Call Claude and return a list of valid category names."""
    user_msg = f"Fonte: {source}\nTítulo: {title}\nTexto: {text}"
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=128,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = msg.content[0].text.strip()
        # Extract JSON array — handle markdown code fences if present
        m = re.search(r"\[.*?\]", raw, re.DOTALL)
        if not m:
            return []
        parsed = json.loads(m.group())
        return [c for c in parsed if c in CATEGORY_SET]
    except Exception as exc:
        print(f"  [warn] Claude error: {exc}", file=sys.stderr)
        return []


def _fetch_articles_with_mentions(cdb: ClippingDB, limit: int) -> list[dict]:
    """Return unclassified articles (deduplicated), each with a 'mentions' list."""
    mentions = cdb.get_unclassified_mentions(limit=limit * 10)  # over-fetch, then dedupe
    seen: dict[int, dict] = {}
    for m in mentions:
        aid = m["article_id"]
        if aid not in seen:
            seen[aid] = {**m, "mentions": []}
        seen[aid]["mentions"].append(m)
    articles = list(seen.values())
    # Enrich with snippet/full_text from the DB directly
    if not articles:
        return []
    ids = [a["article_id"] for a in articles[:limit]]
    id_placeholders = ",".join("?" * len(ids))
    with cdb.connect() as conn:
        rows = conn.execute(
            f"SELECT id, snippet, full_text FROM articles WHERE id IN ({id_placeholders})",
            ids,
        ).fetchall()
    text_by_id = {r["id"]: {"snippet": r["snippet"], "full_text": r["full_text"]} for r in rows}
    result = []
    for a in articles[:limit]:
        extra = text_by_id.get(a["article_id"], {})
        result.append({**a, **extra})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, default=9999, help="Max articles to classify")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to DB")
    parser.add_argument("--verbose", action="store_true", help="Print each result")
    args = parser.parse_args()

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    cdb = ClippingDB(db_path())

    articles = _fetch_articles_with_mentions(cdb, args.limit)
    total = len(articles)
    print(f"Classifying {total} articles (dry_run={args.dry_run})…")

    success = 0
    skipped = 0

    for i, art in enumerate(articles, 1):
        title = art.get("title") or ""
        source = art.get("source_name") or ""
        text = _article_text(art)
        categories = _classify(client, source, title, text)

        if args.verbose:
            cats_str = ", ".join(categories) if categories else "(none)"
            print(f"  [{i}/{total}] {title[:70]!r} → {cats_str}")

        if not categories:
            skipped += 1
            continue

        if args.dry_run:
            success += 1
            continue

        cat_ids = [cdb.get_or_create_category(name, created_by="claude-haiku") for name in categories]
        for m in art["mentions"]:
            cls_id = cdb.upsert_classification(
                mention_id=m["mention_id"],
                article_sentiment=None,
                target_sentiment=None,
                classified_by="claude-haiku",
                ai_generated=True,
            )
            cdb.set_classification_categories(cls_id, cat_ids)
        success += 1

    print(f"Done. Classified {success}/{total} articles ({skipped} had no matching category).")

    if not args.dry_run and artifact_store.enabled:
        print("Uploading updated DB to Supabase…")
        uploaded = artifact_store.upload_current_artifacts(
            manifest={"kind": "ai-batch-classify", "articles": total, "classified": success},
            job_id="ai-batch-classify",
        )
        print(f"Uploaded {len(uploaded)} artifacts.")


if __name__ == "__main__":
    main()
