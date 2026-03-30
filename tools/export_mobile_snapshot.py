#!/usr/bin/env python3
"""Export clipping results to a self-contained HTML report."""
import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from pipeline.database import ClippingDB


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Clipping — {target_name} — {date_range}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #f5f5f5; color: #333; padding: 16px; max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 1.4rem; margin-bottom: 4px; color: #1a1a2e; }}
  .subtitle {{ color: #666; font-size: 0.85rem; margin-bottom: 16px; }}
  .stats {{ display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}
  .stat {{ background: #fff; border-radius: 8px; padding: 12px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
           flex: 1; min-width: 120px; text-align: center; }}
  .stat-value {{ font-size: 1.5rem; font-weight: 700; color: #1a1a2e; }}
  .stat-label {{ font-size: 0.75rem; color: #888; text-transform: uppercase; }}
  .article-card {{ background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 12px;
                   box-shadow: 0 1px 3px rgba(0,0,0,0.08); border-left: 4px solid #4a90d9; }}
  .article-card:hover {{ box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
  .article-title {{ font-size: 1rem; font-weight: 600; color: #1a1a2e; margin-bottom: 6px; }}
  .article-title a {{ color: inherit; text-decoration: none; }}
  .article-title a:hover {{ text-decoration: underline; }}
  .article-meta {{ font-size: 0.78rem; color: #888; margin-bottom: 6px; display: flex; gap: 12px; flex-wrap: wrap; }}
  .article-snippet {{ font-size: 0.85rem; color: #555; line-height: 1.5; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem;
            font-weight: 600; background: #e3f2fd; color: #1565c0; }}
  .badge-source {{ background: #f3e5f5; color: #7b1fa2; }}
  .badge-keyword {{ background: #fff3e0; color: #e65100; }}
  .section-header {{ font-size: 1.1rem; font-weight: 600; color: #1a1a2e; margin: 24px 0 12px;
                     padding-bottom: 6px; border-bottom: 2px solid #4a90d9; }}
  .empty {{ text-align: center; padding: 40px; color: #999; }}
  footer {{ text-align: center; padding: 20px; color: #aaa; font-size: 0.75rem; }}
  @media (max-width: 600px) {{ body {{ padding: 8px; }} .stats {{ flex-direction: column; }} }}
</style>
</head>
<body>
<h1>Clipping: {target_name}</h1>
<p class="subtitle">{date_range} — Gerado em {generated_at}</p>
<div class="stats">
  <div class="stat"><div class="stat-value">{total_articles}</div><div class="stat-label">Artigos</div></div>
  <div class="stat"><div class="stat-value">{total_sources}</div><div class="stat-label">Fontes</div></div>
  <div class="stat"><div class="stat-value">{total_mentions}</div><div class="stat-label">Menções</div></div>
</div>
{articles_html}
<footer>Clipping Project — Gabinete Flávio Valle / Lab Políticas Públicas EPGE-FGV<br>
Gerado automaticamente por pipeline de monitoramento de notícias</footer>
</body></html>"""


def format_date(date_str):
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return date_str[:10] if date_str else ""


def generate_html(articles, target_name, date_from, date_to):
    by_source = {}
    for a in articles:
        source = a.get("source_name", "Desconhecido")
        by_source.setdefault(source, []).append(a)

    sources = set(a.get("source_name", "") for a in articles)
    parts = []

    if not articles:
        parts.append('<p class="empty">Nenhum artigo encontrado para este período.</p>')
    else:
        for source, source_articles in sorted(by_source.items()):
            parts.append(f'<div class="section-header">{source} ({len(source_articles)})</div>')
            for a in source_articles:
                url = a.get("url", "#")
                title = a.get("title", "Sem título") or "Sem título"
                snippet = a.get("snippet", "") or ""
                pub_date = format_date(a.get("published_at", ""))
                source_type = a.get("source_type", "")
                keyword = a.get("keyword_matched", "")
                parts.append(f'''<div class="article-card">
  <div class="article-title"><a href="{url}" target="_blank" rel="noopener">{title}</a></div>
  <div class="article-meta">
    <span>{pub_date}</span>
    <span class="badge badge-source">{source_type}</span>
    {f'<span class="badge badge-keyword">{keyword}</span>' if keyword else ''}
  </div>
  {f'<div class="article-snippet">{snippet[:300]}{"..." if len(snippet) > 300 else ""}</div>' if snippet else ''}
</div>''')

    date_range = f"{date_from} a {date_to}" if date_from and date_to else "Todas as datas"
    return HTML_TEMPLATE.format(
        target_name=target_name, date_range=date_range,
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        total_articles=len(articles), total_sources=len(sources),
        total_mentions=len(articles), articles_html="\n".join(parts),
    )


def main():
    parser = argparse.ArgumentParser(description="Export clipping results to HTML")
    parser.add_argument("--db", default="data/clipping.db")
    parser.add_argument("--target", default="flavio_valle")
    parser.add_argument("--target-name", default="Flávio Valle")
    parser.add_argument("--date-from", default="")
    parser.add_argument("--date-to", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--all-stories", action="store_true")
    args = parser.parse_args()

    if not Path(args.db).exists():
        print(f"Database not found: {args.db}")
        sys.exit(1)

    with ClippingDB(args.db) as db:
        articles = db.list_articles_for_export(
            date_from=args.date_from, date_to=args.date_to, target_key=args.target,
        )

    print(f"Found {len(articles)} articles")
    html = generate_html(articles, args.target_name, args.date_from, args.date_to)

    if args.output:
        out_path = Path(args.output)
    else:
        out_dir = Path("data/reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = f"_{args.date_from}_{args.date_to}" if args.date_from else ""
        out_path = out_dir / f"clipping_snapshot{suffix}.html"

    out_path.write_text(html, encoding="utf-8")
    print(f"Saved: {out_path} ({len(articles)} articles)")


if __name__ == "__main__":
    main()
