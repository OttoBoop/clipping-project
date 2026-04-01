#!/usr/bin/env python3
"""Static HTML snapshot generator for the clipping pipeline.

Reads articles/mentions/stories from the SQLite database and produces
a self-contained HTML file with:
- Story cards grouping related articles
- Target filter buttons with offline JS
- Stats (stories, articles, AI summaries)
- Expandable article details

Recovered from corrupted server.py fragments (original 313 lines).
The HTML template is reconstructed from the old snapshot + corrupted CSS/JS.
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pipeline.database import ClippingDB


# ── HTML Template (recovered from corrupted server.py + old snapshot) ──

HTML_TEMPLATE = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="clipping-snapshot-sentinel" content="WIX_CLIPPING_SNAPSHOT_ROOT">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Clipping — {title}</title>
  <style>
    :root {{ --bg:#f4eee3; --panel:#fffaf4; --ink:#1f2730; --muted:#67727f;
             --line:#dfd5c5; --accent:#224e84; --accent-soft:#e8f0ff;
             --raw:#f7eee2; --ai:#e8f3ea; --ai-ink:#2e6b47; --raw-ink:#6e543d; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--ink);
         font-family:"Segoe UI",Arial,sans-serif; }}
    main {{ width:min(1100px,calc(100% - 20px)); margin:0 auto; padding:16px 0 40px; }}
    .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:22px;
              box-shadow:0 14px 36px rgba(31,39,50,.08); margin-top:16px; padding:18px; }}
    .hero {{ padding:24px; }}
    .eyebrow {{ margin:0 0 8px; font-size:12px; font-weight:700; letter-spacing:.14em;
                text-transform:uppercase; color:var(--accent); }}
    h1 {{ margin:0 0 10px; font-size:clamp(28px,5vw,42px); }}
    h2 {{ margin:0 0 8px; font-size:clamp(21px,3vw,28px); }}
    .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
              gap:14px; margin-top:20px; }}
    .stat {{ padding:16px; border:1px solid var(--line); border-radius:18px; background:#fffdf9; }}
    .stat span {{ display:block; color:var(--muted); font-size:13px; margin-bottom:8px; }}
    .stat strong {{ font-size:24px; }}
    .filter-row {{ display:flex; gap:8px; flex-wrap:wrap; margin:14px 0; }}
    .filter-chip {{ border:1px solid #cad4e6; border-radius:18px; padding:14px 16px;
                    background:#f8fbff; color:var(--ink); cursor:pointer; }}
    .filter-chip.active {{ background:var(--accent); color:#fff; border-color:var(--accent); }}
    .filter-chip span {{ display:block; font-weight:700; }}
    .filter-chip small {{ display:block; margin-top:4px; opacity:.9; }}
    .story-card {{ margin-top:14px; overflow:hidden; }}
    .story-card[hidden] {{ display:none !important; }}
    .story-head {{ display:flex; justify-content:space-between; gap:12px; padding:18px;
                   cursor:pointer; list-style:none; }}
    .story-head::-webkit-details-marker {{ display:none; }}
    .story-stats {{ display:flex; gap:10px; flex-wrap:wrap; }}
    .story-stats div {{ min-width:96px; padding:12px 14px; border:1px solid var(--line);
                        border-radius:16px; background:#fffdf9; text-align:center; }}
    .story-stats strong {{ display:block; }} .story-stats span {{ display:block; color:var(--muted); font-size:12px; }}
    .story-meta,.story-articles {{ padding:0 18px 18px; }}
    .story-meta span {{ color:var(--muted); font-size:13px; margin-right:14px; }}
    .chips {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:8px; }}
    .chip {{ display:inline-flex; align-items:center; min-height:28px; padding:0 12px;
             border-radius:999px; background:#efe3d3; color:#6e543d; font-size:12px; font-weight:700; }}
    .article-card {{ padding:16px; border:1px solid var(--line); border-radius:18px;
                     background:#fffdf9; margin-top:12px; }}
    .article-card h3 a {{ color:var(--accent); text-decoration:none; }}
    .article-card h3 a:hover {{ text-decoration:underline; }}
    .article-meta {{ color:var(--muted); font-size:13px; margin-bottom:6px; }}
    .summary-box {{ padding:14px 16px; border-radius:16px; border:1px solid var(--line); margin-top:10px; }}
    .summary-ai {{ background:var(--ai); border-color:rgba(140,183,157,.65); }}
    .summary-raw {{ background:var(--raw); }}
    .summary-label {{ margin-bottom:8px; font-size:12px; text-transform:uppercase;
                      letter-spacing:.12em; font-weight:700; color:var(--muted); }}
    .body-text {{ color:#304052; font-size:15px; word-break:break-word; }}
    .footer-note {{ margin-top:18px; color:var(--muted); font-size:13px; text-align:center; }}
    .story-index {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
                    gap:14px; padding:14px; }}
    .story-link {{ display:block; padding:14px 16px; border:1px solid var(--line);
                   border-radius:18px; background:#fffdf9; color:inherit; text-decoration:none; }}
    .story-link span {{ display:block; margin-top:6px; color:var(--muted); font-size:12px; }}
    [hidden] {{ display:none !important; }}
    @media (max-width:720px) {{
      main {{ width:min(100% - 12px,100%); }}
      .story-head {{ flex-direction:column; }}
    }}
  </style>
</head>
<body>
  <main>
    <header class="hero panel">
      <p class="eyebrow">Clipping Pipeline</p>
      <h1>{title}</h1>
      <p>{subtitle}</p>
      <div class="stats">
        <div class="stat"><span>Historias</span><strong id="visibleStoriesStat">{total_stories}</strong></div>
        <div class="stat"><span>Noticias</span><strong id="visibleArticlesStat">{total_articles}</strong></div>
        <div class="stat"><span>Fontes</span><strong>{total_sources}</strong></div>
      </div>
      <div style="color:var(--muted);font-size:13px;margin-top:12px;">
        Gerado em: {generated_at} | Banco: {db_name}
      </div>
    </header>

    <section class="panel">
      <p class="eyebrow">Filtro offline</p>
      <h2>Pessoas monitoradas</h2>
      <div class="filter-row" id="targetFilters">{filter_buttons}</div>
      <p style="color:var(--muted);font-size:13px;">Filtro ativo: <strong id="activeFilterText">Todos</strong></p>
    </section>

    <details class="panel" open>
      <summary style="cursor:pointer;font-weight:600;">Indice de historias (<span id="visibleIndexCount">{total_stories}</span>)</summary>
      <div class="story-index" id="storyIndex">{story_index}</div>
    </details>

    <section id="storyStack">{story_sections}</section>

    <p class="footer-note">Snapshot gerado para compartilhamento offline.
    As materias originais seguem com links externos.</p>
  </main>
  <script id="snapshot-payload" type="application/json">{payload_json}</script>
  <script>
    (function () {{
      var payloadEl = document.getElementById("snapshot-payload");
      if (!payloadEl) return;
      var payload = JSON.parse(payloadEl.textContent || "{{}}")
      var buttons = Array.from(document.querySelectorAll("[data-filter-target]"));
      var storyCards = Array.from(document.querySelectorAll("[data-story-id]"));
      var storyLinks = Array.from(document.querySelectorAll("[data-nav-story-id]"));
      var allTargets = (payload.targets || []).map(function(t) {{ return t.key; }});
      var selectedTargets = new Set(allTargets);
      var labelsByKey = {{}};
      (payload.targets || []).forEach(function(t) {{ labelsByKey[t.key] = t.label || t.key; }});

      function storyTargets(sid) {{
        return (payload.storyTargets || {{}})[String(sid)] || [];
      }}
      function storyVisible(targets) {{
        if (!targets.length) return true;
        return targets.some(function(k) {{ return selectedTargets.has(k); }});
      }}
      function applyFilters() {{
        var vis = 0, arts = 0;
        storyCards.forEach(function(card) {{
          var targets = storyTargets(card.dataset.storyId);
          var show = storyVisible(targets);
          card.hidden = !show;
          if (show) {{ vis++; arts += Number(card.dataset.articleCount || 0); }}
        }});
        storyLinks.forEach(function(link) {{
          link.hidden = !storyVisible(storyTargets(link.dataset.navStoryId));
        }});
        buttons.forEach(function(btn) {{
          btn.classList.toggle("active", selectedTargets.has(btn.dataset.filterTarget));
        }});
        document.getElementById("visibleStoriesStat").textContent = vis;
        document.getElementById("visibleArticlesStat").textContent = arts;
        document.getElementById("visibleIndexCount").textContent = vis;
        var active = allTargets.filter(function(k) {{ return selectedTargets.has(k); }});
        document.getElementById("activeFilterText").textContent =
          active.length === allTargets.length ? "Todos" :
          active.map(function(k) {{ return labelsByKey[k] || k; }}).join(" + ");
      }}
      buttons.forEach(function(btn) {{
        btn.addEventListener("click", function() {{
          var key = btn.dataset.filterTarget;
          if (selectedTargets.has(key)) selectedTargets.delete(key);
          else selectedTargets.add(key);
          if (!selectedTargets.size) allTargets.forEach(function(k) {{ selectedTargets.add(k); }});
          applyFilters();
        }});
      }});
      applyFilters();
    }})();
  </script>
</body>
</html>"""


def _format_date(dt_str):
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return dt_str[:10] if dt_str else ""


def render_filter_buttons(target_rows, active_targets=None):
    """Generate HTML for target filter buttons."""
    parts = []
    for t in target_rows:
        key = t.get("key", "")
        label = t.get("label", key)
        active = "active" if (active_targets is None or key in active_targets) else ""
        parts.append(
            f'<button class="filter-chip {active}" data-filter-target="{key}">'
            f'<span>{label}</span></button>'
        )
    return "\n".join(parts)


def render_story_index(stories):
    """Generate HTML for the story navigation index."""
    parts = []
    for s in stories:
        sid = s["story_id"]
        title = s.get("title", "Historia")
        count = s.get("article_count", 0)
        parts.append(
            f'<a class="story-link" href="#story-{sid}" data-nav-story-id="{sid}">'
            f'<strong>{title}</strong>'
            f'<span>{count} noticias</span></a>'
        )
    return "\n".join(parts)


def render_article_card(article):
    """Generate HTML for a single article card."""
    url = article.get("url", "#")
    title = article.get("title", "Sem titulo")
    pub = _format_date(article.get("published_at", ""))
    source = article.get("source_name", "")
    snippet = article.get("snippet", "")
    targets = article.get("target_names", [])

    chips = ""
    if targets:
        names = targets if isinstance(targets, list) else str(targets).split(",")
        for name in names:
            name = name.strip()
            if name:
                chips += f'<span class="chip">{name}</span>'

    snippet_html = ""
    if snippet:
        short = snippet[:300] + ("..." if len(snippet) > 300 else "")
        snippet_html = f'<div class="summary-box summary-raw"><div class="summary-label">Trecho</div><div class="body-text">{short}</div></div>'

    return f'''<div class="article-card">
  <h3><a href="{url}" target="_blank" rel="noopener">{title}</a></h3>
  <p class="article-meta">{pub} — {source}</p>
  <div class="chips">{chips}</div>
  {snippet_html}
</div>'''


def prepare_snapshot(db_path="data/clipping.db", date_from="", date_to="",
                     target_keys=None, title="Clipping"):
    """Generate a self-contained HTML snapshot from the database.

    Returns the HTML string.
    """
    with ClippingDB(db_path) as db:
        articles = db.list_articles_for_export(
            date_from=date_from, date_to=date_to,
        )

    if not articles:
        # Return minimal HTML
        return HTML_TEMPLATE.format(
            title=title, subtitle="Nenhum artigo encontrado",
            total_stories=0, total_articles=0, total_sources=0,
            generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
            db_name=Path(db_path).name,
            filter_buttons="", story_index="", story_sections="",
            payload_json="{}",
        )

    # Group articles by story
    stories_map = {}
    article_map = {}
    for a in articles:
        article_map[a["article_id"]] = a

    # Query story_articles and story titles
    with ClippingDB(db_path) as db:
        rows = db.conn.execute(
            "SELECT article_id, story_id FROM story_articles"
        ).fetchall()
        story_titles = {}
        story_ids_needed = {row["story_id"] for row in rows if row["story_id"]}
        if story_ids_needed:
            ph = ", ".join("?" for _ in story_ids_needed)
            for sr in db.conn.execute(
                f"SELECT id, title FROM stories WHERE id IN ({ph})",
                tuple(story_ids_needed),
            ).fetchall():
                story_titles[int(sr["id"])] = sr["title"] or ""
        for row in rows:
            sid = row["story_id"]
            aid = row["article_id"]
            if sid not in stories_map:
                stories_map[sid] = {"story_id": sid, "articles": [], "targets": set(),
                                    "db_title": story_titles.get(sid, "")}
            if aid in article_map:
                stories_map[sid]["articles"].append(article_map[aid])
                for tn in (article_map[aid].get("target_names") or []):
                    if tn:
                        stories_map[sid]["targets"].add(tn)

    # Articles not in any story get their own story
    storied_aids = {row["article_id"] for row in rows}
    for a in articles:
        if a["article_id"] not in storied_aids:
            sid = f"auto-{a['article_id']}"
            stories_map[sid] = {
                "story_id": sid,
                "articles": [a],
                "targets": set(a.get("target_names") or []),
            }

    stories = sorted(stories_map.values(), key=lambda s: len(s["articles"]), reverse=True)

    # Build target list from articles
    all_targets = {}
    for a in articles:
        tkeys = a.get("target_keys") or []
        tnames = a.get("target_names") or []
        for i, tk in enumerate(tkeys):
            if tk and tk not in all_targets:
                tn = tnames[i] if i < len(tnames) else tk
                all_targets[tk] = {"key": tk, "label": tn}

    target_rows = list(all_targets.values())

    # Build story-to-target mapping for JS payload
    story_targets = {}
    for s in stories:
        tgt_keys = set()
        for a in s["articles"]:
            for tk in (a.get("target_keys") or []):
                if tk:
                    tgt_keys.add(tk)
        story_targets[s["story_id"]] = list(tgt_keys)

    # Enrich stories with metadata
    for s in stories:
        arts = s["articles"]
        s["title"] = s.get("db_title") or (arts[0].get("title", "Historia") if arts else "Historia")
        s["article_count"] = len(arts)

    # Render sections
    filter_buttons = render_filter_buttons(target_rows)
    story_index = render_story_index(stories)

    story_sections = []
    for s in stories:
        sid = s["story_id"]
        arts = s["articles"]
        article_count = len(arts)
        title_text = s["title"]
        target_chips = "".join(
            f'<span class="chip">{name}</span>'
            for name in s.get("targets", set()) if name
        )

        articles_html = "\n".join(render_article_card(a) for a in arts)

        story_sections.append(f'''
<details class="panel story-card" data-story-id="{sid}" data-article-count="{article_count}" open>
  <summary class="story-head">
    <div>
      <p class="eyebrow">Historia</p>
      <h2>{title_text}</h2>
      <div class="chips">{target_chips}</div>
    </div>
    <div class="story-stats">
      <div><strong>{article_count}</strong><span>noticias</span></div>
    </div>
  </summary>
  <div class="story-articles">
    {articles_html}
  </div>
</details>''')

    sources = set(a.get("source_name", "") for a in articles)

    payload = {
        "targets": target_rows,
        "defaultTargets": [t["key"] for t in target_rows],
        "storyTargets": story_targets,
    }

    return HTML_TEMPLATE.format(
        title=title,
        subtitle=f"{date_from} a {date_to}" if date_from and date_to else "Todas as datas",
        total_stories=len(stories),
        total_articles=len(articles),
        total_sources=len(sources),
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        db_name=Path(db_path).name,
        filter_buttons=filter_buttons,
        story_index=story_index,
        story_sections="\n".join(story_sections),
        payload_json=json.dumps(payload, ensure_ascii=False),
    )


def main():
    parser = argparse.ArgumentParser(description="Generate clipping HTML snapshot")
    parser.add_argument("--db", default="data/clipping.db")
    parser.add_argument("--title", default="Clipping")
    parser.add_argument("--date-from", default="")
    parser.add_argument("--date-to", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    html = prepare_snapshot(
        db_path=args.db, date_from=args.date_from, date_to=args.date_to,
        title=args.title,
    )

    if args.output:
        out_path = Path(args.output)
    else:
        out_dir = Path("data/reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = f"_{args.date_from}_{args.date_to}" if args.date_from else ""
        out_path = out_dir / f"clipping_snapshot{suffix}.html"

    out_path.write_text(html, encoding="utf-8")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
