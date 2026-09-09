#!/usr/bin/env python3
"""Explicit, read-only political snapshot in a NEW local directory.

Uses the existing clipping bundle schema and renderer in pages of 100 articles.
No publishing, uploads, schema changes, or existing asset writes occur. Full text
is opt-in and loaded one article at a time. Serve the directory over localhost
HTTP (python -m http.server --directory OUTPUT) to use browser fetch APIs.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import html
import json
from pathlib import Path
import shutil
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.export_mobile_snapshot import build_pages_shell_html
from web_app.political_corpus import PoliticalCorpusService

BATCH_SIZE = 100
MAX_SAFE_ID = (2**53 - 2) // 2


def scoped_targets(keys, roster=None):
    rows = roster if roster is not None else json.loads((ROOT / "data/targets.json").read_text())
    if isinstance(rows, dict):
        rows = rows.get("targets", [])
    requested = list(dict.fromkeys(str(key).strip() for key in keys if str(key).strip()))
    legacy_political = {"flavio_valle", "pedro_duarte", "pedro_angelito", "bernardo_rubiao"}
    known = {row["key"]: row for row in rows
             if row.get("political_roster_version") or row["key"] in legacy_political}
    if not requested or len(requested) > 25 or not set(requested) <= set(known):
        raise ValueError("select between 1 and 25 explicit existing target keys")
    return [{"key": key, "label": known[key].get("display_name") or known[key].get("label") or key,
             "primary": True} for key in requested]


def namespaced_id(value, *, story=False, orphan=False):
    value = int(value)
    if not 0 < value <= MAX_SAFE_ID:
        raise ValueError("political ID exceeds the static JavaScript-safe namespace")
    # Legacy SQLite IDs are positive. Political IDs occupy the negative range;
    # even story IDs are real and odd story IDs are unassociated article cards.
    return -(value * 2 + int(orphan)) if story else -value


def iter_batches(service, keys, *, date_from="", date_to=""):
    """Bounded server cursor, with a consistent read-only DB snapshot."""
    from psycopg.rows import dict_row
    where, params = service._article_filters(keys, date_from=date_from, date_to=date_to)
    with service._connect() as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        conn.execute("SET LOCAL statement_timeout = '60s'")
        with conn.cursor(name="political_static_export", row_factory=dict_row) as cursor:
            cursor.execute(f"""SELECT a.id,a.canonical_url,LEFT(a.title,2000) AS title,
                a.source_name,a.source_key,a.published_at,a.date_status,a.body_status,
                LEFT(a.snippet,1000) AS snippet,LEFT(a.summary,1000) AS summary,
                a.text_object_key,a.content_hash,sa.story_id,
                (sa.story_id IS NULL OR sa.story_id=(SELECT MIN(first_sa.story_id)
                    FROM political_story_articles first_sa WHERE first_sa.article_id=a.id)) AS first_story_association,
                ARRAY(SELECT m.target_key FROM political_mentions m
                      WHERE m.article_id=a.id AND m.target_key=ANY(%s) ORDER BY m.target_key) AS target_keys
                FROM political_articles a LEFT JOIN political_story_articles sa ON sa.article_id=a.id
                WHERE {where} ORDER BY sa.story_id NULLS LAST,a.id""", [keys, *params])
            while batch := cursor.fetchmany(BATCH_SIZE):
                classified = conn.execute("""SELECT article_id,target_key,payload,updated_at
                    FROM political_classifications WHERE article_id=ANY(%s) AND target_key=ANY(%s)
                    ORDER BY article_id,target_key""", ([row["id"] for row in batch], keys)).fetchall()
                by_article = {}
                for row in classified:
                    by_article.setdefault(row["article_id"], []).append(dict(row))
                for row in batch:
                    row["classifications"] = by_article.get(row["id"], [])
                yield batch


def _classification(row, article_id, keys):
    if row.get("target_key") not in keys:
        return None
    payload = row.get("payload") or {}
    if not isinstance(payload, dict):
        payload = {}
    return {**payload, "article_id": article_id, "target_key": row["target_key"],
            "updated_at": str(row.get("updated_at") or ""), "idNamespace": "political_postgresql"}


def article_record(row, keys, *, raw_key=None):
    targets = sorted(set(row.get("target_keys") or []) & set(keys))
    if not targets:
        raise ValueError("export row is outside explicit target scope")
    article_id = namespaced_id(row["id"])
    preview = str(row.get("snippet") or row.get("summary") or "")[:560]
    url = str(row["canonical_url"])
    if urlparse(url).scheme not in {"http", "https"}:
        url = ""
    return {"articleId": article_id, "politicalArticleId": int(row["id"]),
            "idNamespace": "political_postgresql", "title": str(row.get("title") or "Sem título"),
            "url": url, "sourceName": row.get("source_name") or "Fonte não identificada",
            "sourceHost": urlparse(url).hostname or "", "publishedAt": str(row.get("published_at") or ""),
            "publishedDisplay": str(row.get("published_at") or "Data de publicação desconhecida"),
            "dateStatus": row.get("date_status") or "unknown", "bodyStatus": row.get("body_status"),
            "targetKeys": targets, "summaryLabel": "Trecho da matéria" if preview else "Sem trecho disponível",
            "summaryPreview": preview, "rawTextKey": raw_key, "summarySource": "raw",
            "classifications": [result for item in row.get("classifications", [])
                                if (result := _classification(item, article_id, targets)) is not None]}


def page_payload(batch, target_rows, *, page_number, generated_at, text_keys):
    keys = [row["key"] for row in target_rows]
    stories = {}
    for row in batch:
        aid, sid = int(row["id"]), row.get("story_id")
        story_id = namespaced_id(sid or aid, story=True, orphan=not bool(sid))
        article = article_record(row, keys, raw_key=text_keys.get(aid))
        story = stories.setdefault(story_id, {
            "storyIdInt": story_id, "politicalStoryId": int(sid) if sid else None,
            "idNamespace": "political_postgresql", "title": article["title"], "summaryLabel": "Trecho da matéria",
            "summaryText": article["summaryPreview"], "temperature": 0, "firstPublishedAt": "",
            "lastPublishedAt": "", "articleCount": 0, "aiCount": 0, "rawCount": 0,
            "targetKeys": [], "articles": []})
        story["articles"].append(article)
        story["articleCount"] += 1
        story["rawCount"] += 1
        story["targetKeys"] = sorted(set(story["targetKeys"]) | set(article["targetKeys"]))
        dates = [item["publishedAt"] for item in story["articles"] if item["publishedAt"]]
        story["firstPublishedAt"], story["lastPublishedAt"] = (min(dates), max(dates)) if dates else ("", "")
    values = list(stories.values())
    title = f"Clipping político — página {page_number}"
    meta = {"pageTitle": title, "scopeTitle": title, "scopeKicker": "Exportação local",
            "scopeText": "Filtros e busca se aplicam à página atual. Use os links acima para navegar entre páginas.",
            "scopeValue": "Nomes explicitamente selecionados", "generatedAt": generated_at,
            "dbName": "Clipping político", "defaultTargetLabel": "Nomes selecionados",
            "totalStories": len(values), "totalArticles": len(batch), "totalAi": 0, "totalRaw": len(batch),
            "initialStoryCount": len(values), "initialArticleCount": len(batch), "initialAiCount": 0,
            "initialRawCount": len(batch), "exportedTextCount": len(text_keys), "idNamespace": "political_postgresql"}
    targets = [{**row, "storyCount": sum(row["key"] in story["targetKeys"] for story in values),
                "articleCount": sum(row["key"] in article["targetKeys"] for story in values for article in story["articles"])}
               for row in target_rows]
    return {"meta": meta, "targets": targets, "defaultTargets": keys, "stories": values}


def standalone_javascript():
    script = (ROOT / "tools/pages_assets/clipping.js").read_text(encoding="utf-8")
    before, separator, rest = script.partition("  function ensureRawTexts() {")
    _, end, after = rest.partition("  function showError(message) {")
    if not separator or not end or script.count("ensureRawTexts()") != 2:
        raise ValueError("static renderer text loader changed; compatibility review required")
    loader = """  function ensureRawTexts(rawKey) {
    return fetch(rawUrl.replace('{key}', encodeURIComponent(rawKey)), { cache: 'no-store' })
      .then(function (response) { if (!response.ok) throw new Error('Texto indisponível'); return response.json(); })
      .then(function (text) { var result = {}; result[rawKey] = text; return result; });
  }

"""
    result = (before + loader + end + after).replace("ensureRawTexts()", "ensureRawTexts(rawKey)")
    # The legacy raw count means non-AI records; it does not mean available text.
    existing = 'if (baseRawStat) baseRawStat.textContent = String(payload.meta.totalRaw || 0);'
    if result.count(existing) != 1:
        raise ValueError("static renderer text counter changed; compatibility review required")
    return result.replace(existing, 'if (baseRawStat) baseRawStat.textContent = String(payload.meta.exportedTextCount || 0);')


def export_snapshot(service, output, target_rows, *, include_text=False, date_from="", date_to=""):
    output = Path(output).expanduser().resolve()
    # Never overwrite even an empty existing directory or an existing symlink.
    output.mkdir(parents=True, exist_ok=False)
    assets = output / "assets"
    assets.mkdir()
    (output / "texts").mkdir()
    shutil.copyfile(ROOT / "tools/pages_assets/clipping.css", assets / "clipping.css")
    (assets / "clipping.js").write_text(standalone_javascript(), encoding="utf-8")
    keys = [row["key"] for row in target_rows]
    generated = datetime.now(timezone.utc).isoformat()
    manifest = {"version": 1, "scope": "politica_rj_2026", "status": "exporting", "generated_at": generated,
                "target_keys": keys, "date_from": date_from or None, "date_to": date_to or None,
                "page_size": BATCH_SIZE, "page_count": 0, "article_count": 0, "association_count": 0, "story_count": 0,
                "text_count": 0, "text_failures": 0, "include_text": include_text,
                "id_namespace": "negative political IDs; legacy positive IDs remain disjoint",
                "page_pattern": "page-{number:06d}.html", "uploaded": False,
                "limitations": ["Search and filters apply to each page, with at most 100 articles.",
                                "A story spanning pages keeps its original association and numeric ID.",
                                "This export contains only the explicitly selected political scope; existing snapshots remain separate."]}
    def save_manifest():
        (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save_manifest()
    previous_story = None
    try:
        for page_number, batch in enumerate(iter_batches(service, keys, date_from=date_from, date_to=date_to), 1):
            text_keys = {}
            for row in batch:
                identity = ("story", row["story_id"]) if row.get("story_id") else ("article", row["id"])
                if identity != previous_story:
                    manifest["story_count"] += 1
                    previous_story = identity
                if include_text and row.get("text_object_key"):
                    try:
                        key = f"political-article-{int(row['id'])}"
                        destination = output / "texts" / f"{key}.json"
                        # Repeated associations share one immutable article body.
                        # This path can only exist inside this run's new directory.
                        if destination.is_file():
                            text_keys[int(row["id"])] = key
                            continue
                        body = service._read_text(row["text_object_key"], row["content_hash"])
                        if body:
                            with destination.open("x", encoding="utf-8") as stream:
                                json.dump(body, stream, ensure_ascii=False)
                            text_keys[int(row["id"])] = key
                            manifest["text_count"] += 1
                        del body
                    except Exception as exc:
                        manifest["text_failures"] += 1
                        with (output / "text-failures.jsonl").open("a", encoding="utf-8") as stream:
                            stream.write(json.dumps({"political_article_id": row["id"], "error_type": type(exc).__name__}) + "\n")
            payload = page_payload(batch, target_rows, page_number=page_number, generated_at=generated, text_keys=text_keys)
            stem = f"page-{page_number:06d}"
            with (assets / f"{stem}.json").open("x", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False)
            shell = build_pages_shell_html(payload, css_url="assets/clipping.css", js_url="assets/clipping.js",
                                           data_url=f"assets/{stem}.json", raw_url="texts/{key}.json")
            navigation = f'<nav aria-label="Páginas da exportação" style="padding:20px"><a href="index.html">Índice da exportação</a> · '
            if page_number > 1:
                navigation += f'<a href="page-{page_number-1:06d}.html">Página anterior</a> · '
            navigation += f'Página {page_number} <a id="export-next" href="page-{page_number+1:06d}.html" hidden>Próxima página</a></nav>'
            navigation += '<script>fetch("manifest.json").then(r=>r.json()).then(m=>{document.getElementById("export-next").hidden=m.page_count<=' + str(page_number) + ';});</script>'
            shell = shell.replace("<body>", "<body>" + navigation, 1)
            (output / f"{stem}.html").write_text(shell, encoding="utf-8")
            manifest["page_count"] = page_number
            manifest["article_count"] += sum(bool(row.get("first_story_association", True)) for row in batch)
            manifest["association_count"] += len(batch)
        manifest["status"] = "complete_with_text_gaps" if manifest["text_failures"] else "complete"
    except Exception as exc:
        manifest["status"], manifest["error_type"] = "failed", type(exc).__name__
        raise
    finally:
        save_manifest()
    names = ", ".join(row["label"] for row in target_rows)
    first_link = '<p><a href="page-000001.html">Abrir notícias</a></p>' if manifest["page_count"] else '<p>Nenhuma notícia encontrada neste recorte.</p>'
    (output / "index.html").write_text('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Clipping político exportado</title><main style="max-width:800px;margin:40px auto;font:18px sans-serif"><h1>Clipping político exportado</h1>'
        f'<p>{html.escape(names)}</p><p>{manifest["article_count"]} notícias em {manifest["page_count"]} páginas.</p>' + first_link +
        '<p>A busca e os filtros se aplicam à página aberta. As classificações refletem o momento da exportação.</p>'
        '<p><a href="manifest.json">Detalhes da exportação</a></p></main></html>', encoding="utf-8")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--target", action="append", required=True, help="explicit target key; repeat for multiple targets")
    parser.add_argument("--database-url", default="")
    parser.add_argument("--date-from", type=date.fromisoformat)
    parser.add_argument("--date-to", type=date.fromisoformat)
    parser.add_argument("--include-text", action="store_true")
    args = parser.parse_args(argv)
    if args.date_from and args.date_to and args.date_from > args.date_to:
        parser.error("date-from must not exceed date-to")
    targets = scoped_targets(args.target)
    service = PoliticalCorpusService(database_url=args.database_url)
    if not service.configured:
        parser.error("configure POLITICAL_DATABASE_URL or RIO_CORPUS_DATABASE_URL")
    try:
        result = export_snapshot(service, args.output_dir, targets, include_text=args.include_text,
                                 date_from=str(args.date_from or ""), date_to=str(args.date_to or ""))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if not result["text_failures"] else 1
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
