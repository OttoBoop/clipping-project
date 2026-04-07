from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.database import ClippingDB  # noqa: E402


DB_PATH = ROOT / "data" / "clipping.db"
TARGETS_PATH = ROOT / "data" / "targets.json"
REPORTS_DIR = ROOT / "data" / "reports"
DEFAULT_TARGET_KEY = "flavio_valle"
EXPORT_LIMIT = 20000
WIX_SNAPSHOT_SENTINEL = "WIX_CLIPPING_SNAPSHOT_ROOT"
PAGES_INDEX_PATH = ROOT / "index.html"
PAGES_ASSETS_DIR = ROOT / "assets"
PAGES_ASSET_TEMPLATES_DIR = ROOT / "tools" / "pages_assets"
LEGACY_FULL_REPORT_PATH = REPORTS_DIR / "clipping_historias_completo.html"
INSTITUTIONAL_FULL_REPORT_PATH = REPORTS_DIR / "clipping_completo_novo_estilo.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Exporta um snapshot HTML estatico do clipping para compartilhamento mobile."
    )
    parser.add_argument(
        "--db",
        default="",
        help="Caminho do banco SQLite a exportar. Default: data/clipping.db",
    )
    parser.add_argument("--date-from", default="", help="Data inicial em YYYY-MM-DD.")
    parser.add_argument("--date-to", default="", help="Data final em YYYY-MM-DD.")
    parser.add_argument(
        "--all-stories",
        action="store_true",
        help="Exporta todas as historias atuais do banco, ignorando a janela de datas.",
    )
    parser.add_argument(
        "--default-target",
        default=DEFAULT_TARGET_KEY,
        help="Target inicial selecionado no filtro. Default: flavio_valle.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Arquivo HTML de saida. Default: data/reports/clipping_mobile_snapshot_<escopo>.html",
    )
    parser.add_argument(
        "--merge-from",
        default="",
        help="Caminho de um HTML snapshot existente cujas historias serao mescladas com as novas do banco.",
    )
    parser.add_argument(
        "--remap-incoming-ids-on-merge",
        action="store_true",
        help="Desloca IDs de historias/artigos vindos do banco atual para evitar colisao com o HTML mesclado.",
    )
    args = parser.parse_args()
    if not args.all_stories and (not args.date_from or not args.date_to):
        parser.error("use --all-stories ou informe --date-from e --date-to")
    return args


def load_targets() -> list[dict[str, Any]]:
    rows = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    targets: list[dict[str, Any]] = []
    for row in rows:
        key = str(row.get("key") or "").strip()
        if not key:
            continue
        targets.append(
            {
                "key": key,
                "label": str(row.get("label") or key),
                "primary": bool(row.get("primary", False)),
            }
        )
    return targets


def target_label_map(target_rows: list[dict[str, Any]]) -> dict[str, str]:
    return {str(row["key"]): str(row["label"]) for row in target_rows}


def normalize_text(value: Any) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\u00a0", " ", text)
    lines = [re.sub(r"[ \	]+", " ", line).strip() for line in text.split("\n")]
    cleaned: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if cleaned and not blank:
                cleaned.append("")
            blank = True
            continue
        cleaned.append(line)
        blank = False
    return "\n".join(cleaned).strip()


def excerpt(value: str, limit: int = 420) -> str:
    text = normalize_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def story_id_int(value: str | int | None) -> int:
    raw = str(value or "").strip()
    if raw.startswith("st-"):
        raw = raw[3:]
    try:
        return int(raw)
    except Exception:
        return 0


def article_id_int(value: str | int | None) -> int:
    raw = str(value or "").strip()
    if raw.startswith("article-"):
        raw = raw[8:]
    if raw.startswith("a-"):
        raw = raw[2:]
    try:
        return int(raw)
    except Exception:
        return 0


def parse_dt(value: str) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def fmt_dt(value: str) -> str:
    dt = parse_dt(value)
    if not dt:
        return "Data nao informada"
    return dt.astimezone(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")


def host_from_url(url: str) -> str:
    try:
        host = urlparse(str(url or "")).netloc.lower()
        return host.replace("www.", "") if host else ""
    except Exception:
        return ""


def json_for_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")


def target_badges(target_keys: list[str], label_by_key: dict[str, str]) -> str:
    if not target_keys:
        return ""
    return "".join(
        f'<span class="chip">{html.escape(label_by_key.get(key, key))}</span>'
        for key in target_keys
    )


def parse_source_html(path: str) -> tuple[dict[str, Any], dict[int, str]]:
    """Parse an existing HTML snapshot and return (payload, {story_id: card_html})."""
    raw = Path(path).read_text(encoding="utf-8")
    payload: dict[str, Any] = {}
    m = re.search(r'<script[^>]*id="snapshot-payload"[^>]*>(.*?)</script>', raw, re.DOTALL)
    if m:
        payload = json.loads(m.group(1))
    cards: dict[int, str] = {}
    for card_m in re.finditer(
        r'(<details\b[^>]*\bdata-story-id="(\d+)"[^>]*>.*?</details>)',
        raw,
        re.DOTALL,
    ):
        sid = int(card_m.group(2))
        cards[sid] = card_m.group(1)
    return payload, cards


def max_story_id_from_snapshot(payload: dict[str, Any], cards: dict[int, str]) -> int:
    ids = set(cards)
    for key in (payload.get("storyTargets") or {}):
        try:
            ids.add(int(str(key)))
        except Exception:
            continue
    return max(ids) if ids else 0


def max_article_id_from_snapshot_html(path: str) -> int:
    raw = Path(path).read_text(encoding="utf-8")
    ids = [int(value) for value in re.findall(r'\barticle-(\d+)\b', raw)]
    return max(ids) if ids else 0


def remap_scope_ids(
    stories: list[dict[str, Any]],
    article_map: dict[int, dict[str, Any]],
    *,
    story_offset: int = 0,
    article_offset: int = 0,
) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]]]:
    if story_offset <= 0 and article_offset <= 0:
        return stories, article_map

    remapped_article_map: dict[int, dict[str, Any]] = {}
    article_id_map: dict[int, int] = {}
    for old_aid, article in article_map.items():
        new_aid = int(old_aid) + article_offset if article_offset > 0 else int(old_aid)
        article_id_map[int(old_aid)] = new_aid
        remapped_article_map[new_aid] = {**article, "article_id": new_aid}

    remapped_stories: list[dict[str, Any]] = []
    for story in stories:
        new_story = dict(story)
        old_sid = int(story.get("storyIdInt") or 0)
        new_sid = old_sid + story_offset if old_sid and story_offset > 0 else old_sid
        if old_sid:
            new_story["storyIdInt"] = new_sid
            raw_story_id = str(story.get("id") or "")
            if raw_story_id.startswith("st-"):
                new_story["id"] = f"st-{new_sid}"
            elif raw_story_id.isdigit():
                new_story["id"] = str(new_sid)

        remapped_articles: list[dict[str, Any]] = []
        for article_stub in story.get("articles", []):
            new_stub = dict(article_stub)
            old_aid = article_id_int(article_stub.get("id"))
            new_aid = article_id_map.get(old_aid)
            if new_aid:
                new_stub["id"] = f"a-{new_aid}"
            remapped_articles.append(new_stub)
        new_story["articles"] = remapped_articles
        remapped_stories.append(new_story)

    return remapped_stories, remapped_article_map


def _parse_old_date(text: str) -> str:
    """Convert 'DD/MM/YYYY HH:MM UTC' to ISO-8601."""
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})\s+(\d{2}):(\d{2})\s*UTC", text)
    if not m:
        return ""
    day, month, year, hour, minute = m.groups()
    return f"{year}-{month}-{day}T{hour}:{minute}:00+00:00"


def patch_old_card(card_html: str, story_targets: dict[str, list[str]]) -> str:
    """Add data-temperature, data-last-published, data-targets to an old card."""
    sid_m = re.search(r'data-story-id="(\d+)"', card_html)
    if not sid_m:
        return card_html
    sid = sid_m.group(1)

    # Extract temperature from <strong>NN</strong><span>temperatura</span> or similar
    temp = "0"
    temp_m = re.search(r"<strong>(\d+)</strong>\s*<span[^>]*>\s*temperatura\s*</span>", card_html, re.IGNORECASE)
    if temp_m:
        temp = temp_m.group(1)

    # Extract last published date from "Ultima publicacao: DD/MM/YYYY HH:MM UTC"
    last_pub = ""
    pub_m = re.search(r"[Uu]ltima publica[cç][aã]o:\s*([^<]+)", card_html)
    if pub_m:
        last_pub = _parse_old_date(pub_m.group(1))

    # Extract targets from payload
    targets_str = ",".join(story_targets.get(sid, []))

    # Inject attributes into the opening <details> tag
    inject = f' data-temperature="{html.escape(temp)}" data-last-published="{html.escape(last_pub)}" data-targets="{html.escape(targets_str)}"'
    # Insert before the closing > of the opening <details ...>
    card_html = re.sub(
        r'(<details\b[^>]*\bdata-story-id="' + re.escape(sid) + r'"[^>]*?)(>)',
        r"\1" + inject + r"\2",
        card_html,
        count=1,
    )
    return card_html


def render_text_block(article: dict[str, Any]) -> tuple[str, str, str]:
    has_ai = bool(article.get("has_ai_summary"))
    summary = normalize_text(article.get("summary"))
    full_text = normalize_text(article.get("full_text"))
    snippet = normalize_text(article.get("snippet"))

    if has_ai and summary:
        preview = html.escape(summary).replace("\n", "<br>")
        return "Resumo IA", preview, ""

    if full_text:
        preview_source = summary or snippet or full_text
        preview = html.escape(excerpt(preview_source, 560)).replace("\n", "<br>")
        if normalize_text(preview_source) == full_text and len(full_text) <= 560:
            return "Texto bruto", preview, ""
        full_html = html.escape(full_text).replace("\n", "<br>")
        return "Texto bruto", preview, full_html

    raw = summary or snippet
    if raw:
        return "Trecho bruto", html.escape(raw).replace("\n", "<br>"), ""

    return "Sem resumo", "Sem conteudo disponivel.", ""


def story_display_summary(story: dict[str, Any], article_map: dict[int, dict[str, Any]]) -> tuple[str, str]:
    for article in story.get("articles", []):
        detail = article_map.get(article_id_int(article.get("id")))
        if detail and detail.get("has_ai_summary") and normalize_text(detail.get("summary")):
            return "Resumo IA", excerpt(str(detail.get("summary")), 700)
    summary = normalize_text(story.get("summary"))
    if summary:
        return "Resumo do agrupamento", excerpt(summary, 700)
    articles = story.get("articles", [])
    if not articles:
        return "Sem resumo", "Sem resumo."
    detail = article_map.get(article_id_int(articles[0].get("id")))
    if not detail:
        return "Sem resumo", "Sem resumo."
    label, preview, _ = render_text_block(detail)
    return label, html.unescape(preview.replace("<br>", "\n"))


def story_sort_key(story: dict[str, Any]) -> tuple[float, float]:
    last_dt = parse_dt(str(story.get("lastPublishedAt") or story.get("updatedAt") or ""))
    return (last_dt.timestamp() if last_dt else 0.0, float(story.get("temperature") or 0.0))


def load_scope_articles(db: ClippingDB, args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.all_stories:
        return db.list_articles_for_export(limit=EXPORT_LIMIT)
    return db.list_articles_for_export(
        limit=EXPORT_LIMIT,
        date_from=args.date_from,
        date_to=f"{args.date_to}T23:59:59",
    )


def decorate_stories(
    stories: list[dict[str, Any]],
    article_map: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    scoped_stories: list[dict[str, Any]] = []
    for story in stories:
        seen_ids: set[int] = set()
        kept_articles: list[dict[str, Any]] = []
        published_values: list[datetime] = []

        for article_stub in story.get("articles", []):
            aid = article_id_int(article_stub.get("id"))
            if not aid or aid in seen_ids or aid not in article_map:
                continue
            seen_ids.add(aid)
            kept_articles.append(article_stub)
            published_raw = str(article_map[aid].get("published_at") or article_stub.get("publishedAt") or "")
            published_dt = parse_dt(published_raw)
            if published_dt:
                published_values.append(published_dt)

        if not kept_articles:
            continue

        sid = story_id_int(story.get("id"))
        ai_count = sum(1 for aid in seen_ids if article_map[aid].get("has_ai_summary"))
        first_published = min(published_values).isoformat() if published_values else str(story.get("createdAt") or "")
        last_published = max(published_values).isoformat() if published_values else str(story.get("updatedAt") or "")

        scoped_stories.append(
            {
                **story,
                "storyIdInt": sid,
                "targetKeys": [str(target) for target in story.get("targets", []) if str(target).strip()],
                "articles": kept_articles,
                "articleCount": len(kept_articles),
                "aiCount": ai_count,
                "rawCount": len(kept_articles) - ai_count,
                "firstPublishedAt": first_published,
                "lastPublishedAt": last_published,
            }
        )

    scoped_stories.sort(key=story_sort_key, reverse=True)
    return scoped_stories


def build_target_rows(
    base_targets: list[dict[str, Any]],
    stories: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    counts: dict[str, dict[str, int]] = {}
    for story in stories:
        for key in story.get("targetKeys", []):
            bucket = counts.setdefault(key, {"storyCount": 0, "articleCount": 0})
            bucket["storyCount"] += 1
            bucket["articleCount"] += int(story.get("articleCount") or 0)

    target_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in base_targets:
        key = str(row["key"])
        story_count = int(counts.get(key, {}).get("storyCount", 0))
        if story_count <= 0:
            continue
        target_rows.append(
            {
                "key": key,
                "label": str(row["label"]),
                "primary": bool(row.get("primary", False)),
                "storyCount": story_count,
                "articleCount": int(counts.get(key, {}).get("articleCount", 0)),
            }
        )
        seen.add(key)

    for key in sorted(counts):
        if key in seen or int(counts[key]["storyCount"]) <= 0:
            continue
        target_rows.append(
            {
                "key": key,
                "label": key.replace("_", " ").title(),
                "primary": False,
                "storyCount": int(counts[key]["storyCount"]),
                "articleCount": int(counts[key]["articleCount"]),
            }
        )
    return target_rows


def resolve_initial_targets(target_rows: list[dict[str, Any]], default_target: str) -> list[str]:
    all_keys = [str(row["key"]) for row in target_rows]
    if default_target and default_target in all_keys:
        return [default_target]
    return all_keys


def story_matches_targets(story: dict[str, Any], selected_targets: set[str]) -> bool:
    story_targets = set(str(key) for key in story.get("targetKeys", []))
    if not selected_targets:
        return True
    return bool(story_targets & selected_targets)


def visibility_stats(
    stories: list[dict[str, Any]],
    selected_targets: list[str],
) -> dict[str, Any]:
    selected = set(selected_targets)
    visible_stories = [story for story in stories if story_matches_targets(story, selected)]
    return {
        "storyCount": len(visible_stories),
        "articleCount": sum(int(story.get("articleCount") or 0) for story in visible_stories),
        "aiCount": sum(int(story.get("aiCount") or 0) for story in visible_stories),
        "rawCount": sum(int(story.get("rawCount") or 0) for story in visible_stories),
        "visibleStoryIds": {int(story.get("storyIdInt") or 0) for story in visible_stories},
    }


def active_filter_label(selected_targets: list[str], target_rows: list[dict[str, Any]]) -> str:
    if not target_rows:
        return "Sem filtros disponiveis"
    all_keys = [str(row["key"]) for row in target_rows]
    if set(selected_targets) == set(all_keys):
        return "Todos os nomes monitorados"
    labels = [str(row["label"]) for row in target_rows if str(row["key"]) in set(selected_targets)]
    if not labels:
        return "Todos os nomes monitorados"
    return " + ".join(labels)


def render_filter_buttons(target_rows: list[dict[str, Any]], active_targets: list[str]) -> str:
    active_set = set(active_targets)
    buttons: list[str] = []
    for row in target_rows:
        active_class = " active" if str(row["key"]) in active_set else ""
        primary_class = " primary" if bool(row.get("primary", False)) else ""
        buttons.append(
            """
            <button type="button" class="filter-chip__button__" data-filter-target="__KEY__">
              <span class="filter-chip__label">__LABEL__</span>
              <span class="filter-chip__meta">__COUNT__ historias</span>
            </button>
            """
            .replace("filter-chip__button__", f"filter-chip{primary_class}{active_class}")
            .replace("__KEY__", html.escape(str(row["key"])))
            .replace("__LABEL__", html.escape(str(row["label"])))
            .replace("__COUNT__", str(int(row.get("storyCount") or 0)))
        )
    return "".join(buttons)


def render_story_index(stories: list[dict[str, Any]], visible_story_ids: set[int]) -> str:
    links: list[str] = []
    for story in stories:
        sid = int(story.get("storyIdInt") or 0)
        hidden_attr = "" if sid in visible_story_ids else " hidden"
        links.append(
            """
            <a class="story-index-link" href="#story-__SID__" data-nav-story-id="__SID__"__HIDDEN__>
              <strong>__TITLE__</strong>
              <span>__COUNT__ noticia(s)</span>
            </a>
            """
            .replace("__SID__", str(sid))
            .replace("__TITLE__", html.escape(str(story.get("title") or "Sem titulo")))
            .replace("__COUNT__", str(int(story.get("articleCount") or 0)))
            .replace("__HIDDEN__", hidden_attr)
        )
    return "".join(links)


def render_article_card(article: dict[str, Any], label_by_key: dict[str, str]) -> str:
    label, preview_html, full_html = render_text_block(article)
    aid = int(article.get("article_id") or 0)
    title = html.escape(str(article.get("title") or "Sem titulo"))
    url = str(article.get("url") or "").strip()
    source = str(article.get("source_name") or "Fonte nao identificada").strip()
    source_host = host_from_url(url)
    external_link = (
        f'<a class="text-link" href="{html.escape(url)}" target="_blank" rel="noreferrer">Abrir materia original</a>'
        if url
        else ""
    )
    full_toggle = ""
    if full_html:
        full_toggle = f"""
        <details class="raw-details" data-article-id="article-{aid}">
          <summary>Ver texto bruto completo</summary>
          <div class="body-text full"></div>
        </details>
        """

    title_html = title
    if url:
        title_html = f'<a href="{html.escape(url)}" target="_blank" rel="noreferrer">{title}</a>'

    return (
        """
        <article class="article-card" id="article-__AID__" data-published-iso="__PUB_ISO__" data-title="__TITLE_PLAIN__">
          <div class="article-top">
            <div>
              <h3>__TITLE_HTML__</h3>
              <p class="article-meta">
                <span>__SOURCE__</span>
                <span>__PUBLISHED__</span>
                <span>__HOST__</span>
              </p>
            </div>
            <div class="chips">__TARGET_BADGES__</div>
          </div>
          <div class="article-links">__EXTERNAL_LINK__</div>
          <div class="summary-box __SUMMARY_CLASS__">
            <div class="summary-label">__SUMMARY_LABEL__</div>
            <div class="body-text">__PREVIEW__</div>
            __FULL_TOGGLE__
          </div>
        </article>
        """
        .replace("__AID__", str(aid))
        .replace("__PUB_ISO__", html.escape(str(article.get("published_at") or "")))
        .replace("__TITLE_PLAIN__", html.escape(str(article.get("title") or "")))
        .replace("__TITLE_HTML__", title_html)
        .replace("__SOURCE__", html.escape(source))
        .replace("__PUBLISHED__", html.escape(fmt_dt(str(article.get("published_at") or ""))))
        .replace("__HOST__", html.escape(source_host or "link externo"))
        .replace("__TARGET_BADGES__", target_badges(list(article.get("target_keys") or []), label_by_key))
        .replace("__EXTERNAL_LINK__", external_link)
        .replace("__SUMMARY_CLASS__", "summary-ai" if label == "Resumo IA" else "summary-raw")
        .replace("__SUMMARY_LABEL__", html.escape(label))
        .replace("__PREVIEW__", preview_html)
        .replace("__FULL_TOGGLE__", full_toggle)
    )


def render_story_section(
    story: dict[str, Any],
    *,
    article_map: dict[int, dict[str, Any]],
    label_by_key: dict[str, str],
    visible_story_ids: set[int],
) -> str:
    sid = int(story.get("storyIdInt") or 0)
    summary_label, story_summary = story_display_summary(story, article_map)
    article_cards = []
    for article_stub in story.get("articles", []):
        aid = article_id_int(article_stub.get("id"))
        detail = article_map.get(aid)
        if detail:
            article_cards.append(render_article_card(detail, label_by_key))

    hidden_attr = "" if sid in visible_story_ids else " hidden"
    return (
        """
        <details class="panel story-card" id="story-__SID__" data-story-id="__SID__" data-article-count="__ARTICLE_COUNT__" data-ai-count="__AI_COUNT__" data-raw-count="__RAW_COUNT__" data-targets="__TARGETS__" data-temperature="__TEMP_RAW__" data-last-published="__LAST_PUBLISHED_ISO__"__HIDDEN__>
          <summary class="story-summary-row">
            <div class="story-heading">
              <span class="story-toggle" aria-hidden="true"></span>
              <div>
                <p class="eyebrow">Historia principal __SID__</p>
                <h2>__TITLE__</h2>
                <div class="chips">__TARGET_BADGES__</div>
              </div>
            </div>
            <div class="story-stats">
              <div><strong>__ARTICLE_COUNT__</strong><span>noticias</span></div>
              <div><strong>__TEMP__</strong><span>temperatura</span></div>
            </div>
          </summary>
          <div class="story-meta">
            <span>Primeira publicacao: __FIRST_PUBLISHED__</span>
            <span>Ultima publicacao: __LAST_PUBLISHED__</span>
          </div>
          <div class="story-blurb">
            <div class="summary-label">__SUMMARY_LABEL__</div>
            <p>__SUMMARY_TEXT__</p>
          </div>
          <div class="story-articles">__ARTICLE_CARDS__</div>
        </details>
        """
        .replace("__SID__", str(sid))
        .replace("__ARTICLE_COUNT__", str(int(story.get("articleCount") or 0)))
        .replace("__AI_COUNT__", str(int(story.get("aiCount") or 0)))
        .replace("__RAW_COUNT__", str(int(story.get("rawCount") or 0)))
        .replace("__TARGETS__", html.escape(",".join(str(key) for key in story.get("targetKeys", []))))
        .replace("__HIDDEN__", hidden_attr)
        .replace("__TITLE__", html.escape(str(story.get("title") or "Sem titulo")))
        .replace("__TARGET_BADGES__", target_badges(list(story.get("targetKeys") or []), label_by_key))
        .replace("__TEMP__", str(int(round(float(story.get("temperature") or 0.0)))))
        .replace("__TEMP_RAW__", str(int(round(float(story.get("temperature") or 0.0)))))
        .replace("__LAST_PUBLISHED_ISO__", html.escape(str(story.get("lastPublishedAt") or "")))
        .replace("__FIRST_PUBLISHED__", html.escape(fmt_dt(str(story.get("firstPublishedAt") or ""))))
        .replace("__LAST_PUBLISHED__", html.escape(fmt_dt(str(story.get("lastPublishedAt") or ""))))
        .replace("__SUMMARY_LABEL__", html.escape(summary_label))
        .replace("__SUMMARY_TEXT__", html.escape(story_summary))
        .replace("__ARTICLE_CARDS__", "".join(article_cards))
    )


def scope_labels(args: argparse.Namespace) -> tuple[str, str, str]:
    if args.all_stories:
        return (
            "Historico completo",
            "Clipping offline com todas as historias",
            "Arquivo HTML autossuficiente com todas as historias principais agrupadas no banco. A pagina abre filtrada em Flavio Valle e permite adicionar ou remover outros nomes sem depender da API local.",
        )
    return (
        f"Janela {args.date_from} a {args.date_to}",
        "Clipping offline por periodo",
        f"Arquivo HTML autossuficiente com as historias principais agrupadas entre {args.date_from} e {args.date_to}. A pagina abre filtrada em Flavio Valle e permite combinar outros nomes localmente.",
    )


def output_path_for_args(args: argparse.Namespace) -> Path:
    if args.output:
        return Path(args.output).expanduser()
    if args.all_stories:
        return PAGES_INDEX_PATH
    return REPORTS_DIR / f"clipping_mobile_snapshot_{args.date_from}_{args.date_to}.html"


def build_html(
    *,
    args: argparse.Namespace,
    stories: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    initial_targets: list[str],
    article_map: dict[int, dict[str, Any]],
    merged_card_html: dict[int, str] | None = None,
    merged_payload_extra: dict[str, Any] | None = None,
) -> str:
    label_by_key = target_label_map(target_rows)
    generated_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    scope_kicker, scope_title, scope_text = scope_labels(args)

    # --- Merge handling ---
    merged_cards = merged_card_html or {}
    merged_extra = merged_payload_extra or {}
    old_story_targets: dict[str, list[str]] = merged_extra.get("storyTargets", {})

    # Count old card stats (parse data attributes from the HTML)
    old_article_count = 0
    old_ai_count = 0
    old_raw_count = 0
    for _sid, card_str in merged_cards.items():
        ac_m = re.search(r'data-article-count="(\d+)"', card_str)
        ai_m = re.search(r'data-ai-count="(\d+)"', card_str)
        rw_m = re.search(r'data-raw-count="(\d+)"', card_str)
        old_article_count += int(ac_m.group(1)) if ac_m else 0
        old_ai_count += int(ai_m.group(1)) if ai_m else 0
        old_raw_count += int(rw_m.group(1)) if rw_m else 0

    total_story_count = len(stories) + len(merged_cards)
    total_article_count = sum(int(story.get("articleCount") or 0) for story in stories) + old_article_count
    total_ai_count = sum(int(story.get("aiCount") or 0) for story in stories) + old_ai_count
    total_raw_count = sum(int(story.get("rawCount") or 0) for story in stories) + old_raw_count

    # Build combined storyTargets for the payload
    combined_story_targets: dict[str, list[str]] = dict(old_story_targets)
    for story in stories:
        combined_story_targets[str(int(story.get("storyIdInt") or 0))] = [
            str(key) for key in story.get("targetKeys", [])
        ]

    # Determine initial visibility: new stories + old stories whose targets match
    initial_stats = visibility_stats(stories, initial_targets)
    initial_visible_story_ids = set(initial_stats["visibleStoryIds"])
    selected_set = set(initial_targets)
    for sid_str, tkeys in old_story_targets.items():
        if not selected_set or any(k in selected_set for k in tkeys):
            initial_visible_story_ids.add(int(sid_str))

    visible_story_count = len(initial_visible_story_ids)
    visible_article_count = int(initial_stats["articleCount"])
    visible_ai_count = int(initial_stats["aiCount"])
    visible_raw_count = int(initial_stats["rawCount"])
    for sid, card_str in merged_cards.items():
        if sid in initial_visible_story_ids:
            ac_m = re.search(r'data-article-count="(\d+)"', card_str)
            ai_m = re.search(r'data-ai-count="(\d+)"', card_str)
            rw_m = re.search(r'data-raw-count="(\d+)"', card_str)
            visible_article_count += int(ac_m.group(1)) if ac_m else 0
            visible_ai_count += int(ai_m.group(1)) if ai_m else 0
            visible_raw_count += int(rw_m.group(1)) if rw_m else 0

    active_filter_text = active_filter_label(initial_targets, target_rows)

    # Collect raw texts for lazy injection
    raw_texts = {}
    for article in article_map.values():
        _, _, full_html = render_text_block(article)
        if full_html:
            aid = int(article.get("article_id") or 0)
            raw_texts[f"article-{aid}"] = full_html

    # Build story card HTML strings (stored in payload, NOT in DOM)
    story_cards_html: dict[str, str] = {}
    for story in stories:
        sid = int(story.get("storyIdInt") or 0)
        story_cards_html[str(sid)] = render_story_section(
            story,
            article_map=article_map,
            label_by_key=label_by_key,
            visible_story_ids=initial_visible_story_ids,
        )
    for sid, card_str in merged_cards.items():
        story_cards_html[str(sid)] = card_str

    payload = {
        "targets": [
            {
                "key": str(row["key"]),
                "label": str(row["label"]),
                "storyCount": int(row.get("storyCount") or 0),
                "articleCount": int(row.get("articleCount") or 0),
            }
            for row in target_rows
        ],
        "defaultTargets": list(initial_targets),
        "storyTargets": combined_story_targets,
        "rawTexts": raw_texts,
        "storyCards": story_cards_html,
    }

    filter_buttons = render_filter_buttons(target_rows, initial_targets)

    # Build story index: new stories + old merged stories
    story_index = render_story_index(stories, initial_visible_story_ids)
    for sid, card_str in merged_cards.items():
        title_m = re.search(r"<h2>(.*?)</h2>", card_str, re.DOTALL)
        title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else "Sem titulo"
        ac_m = re.search(r'data-article-count="(\d+)"', card_str)
        count = ac_m.group(1) if ac_m else "0"
        hidden_attr = "" if sid in initial_visible_story_ids else " hidden"
        story_index += (
            f'<a class="story-index-link" href="#story-{sid}" data-nav-story-id="{sid}"{hidden_attr}>'
            f"<strong>{html.escape(title)}</strong>"
            f"<span>{count} noticia(s)</span></a>\n"
        )

    # storyStack starts empty — cards are rendered on demand from payload
    story_sections = ""

    empty_hidden = " hidden" if visible_story_count > 0 else ""

    scope_value = "Banco inteiro" if args.all_stories else f"{args.date_from} a {args.date_to}"
    default_target_label = label_by_key.get(args.default_target, args.default_target)

    template = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__PAGE_TITLE__</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4eee3;
      --panel: rgba(255, 251, 246, 0.97);
      --panel-strong: #fffdfa;
      --ink: #1e2730;
      --muted: #677485;
      --line: #dfd4c3;
      --accent: #224e84;
      --accent-soft: #e8f0ff;
      --accent-warm: #ca7f36;
      --shadow: 0 18px 44px rgba(31, 39, 50, 0.12);
      --raw-bg: #f7eee2;
      --ai-bg: #e8f3ea;
      --ai-ink: #1f6a50;
      --raw-ink: #8c5937;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      background:
        radial-gradient(circle at top left, rgba(34, 78, 132, 0.14), transparent 34%),
        radial-gradient(circle at top right, rgba(202, 127, 54, 0.15), transparent 26%),
        var(--bg);
      color: var(--ink);
      font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      line-height: 1.5;
    }
    main {
      width: min(1100px, calc(100% - 26px));
      margin: 0 auto;
      padding: 16px 0 40px;
    }
    .hero,
    .panel {
      background: var(--panel);
      border: 1px solid rgba(223, 212, 195, 0.9);
      border-radius: 24px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }
    .hero {
      padding: 24px;
      background:
        linear-gradient(145deg, rgba(255, 253, 249, 0.99), rgba(244, 238, 227, 0.94));
    }
    .panel {
      padding: 20px;
      margin-top: 18px;
    }
    .story-card {
      padding: 0;
      overflow: hidden;
      scroll-margin-top: 12px;
    }
    .eyebrow {
      margin: 0 0 8px;
      text-transform: uppercase;
      letter-spacing: 0.15em;
      font-size: 12px;
      font-weight: 700;
      color: var(--accent);
    }
    h1, h2, h3, p {
      margin-top: 0;
    }
    h1 {
      margin-bottom: 10px;
      font-size: clamp(28px, 5vw, 44px);
      line-height: 1.05;
    }
    h2 {
      margin-bottom: 10px;
      font-size: clamp(21px, 3vw, 29px);
      line-height: 1.15;
    }
    h3 {
      margin-bottom: 6px;
      font-size: 18px;
      line-height: 1.25;
    }
    .hero p {
      max-width: 860px;
      color: var(--muted);
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 14px;
      margin: 22px 0 0;
    }
    .stat {
      padding: 16px 18px;
      border-radius: 18px;
      background: var(--panel-strong);
      border: 1px solid rgba(223, 212, 195, 0.95);
    }
    .stat span,
    .stat small {
      display: block;
      color: var(--muted);
    }
    .stat span {
      margin-bottom: 8px;
      font-size: 13px;
    }
    .stat strong {
      font-size: 24px;
      line-height: 1;
    }
    .stat small {
      margin-top: 8px;
      font-size: 12px;
    }
    .meta-row,
    .filter-row,
    .story-index,
    .story-articles {
      display: grid;
      gap: 14px;
    }
    .meta-row {
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      margin-top: 18px;
      color: var(--muted);
      font-size: 14px;
    }
    .section-head,
    .article-top,
    .story-summary-row {
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: flex-start;
      flex-wrap: wrap;
    }
    .filter-row {
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      margin-top: 14px;
    }
    .filter-chip {
      display: flex;
      flex-direction: column;
      gap: 4px;
      width: 100%;
      padding: 14px 16px;
      border: 1px solid rgba(190, 200, 218, 0.8);
      border-radius: 18px;
      background: linear-gradient(165deg, rgba(236, 242, 255, 0.94), rgba(255, 251, 246, 0.95));
      color: var(--ink);
      text-align: left;
      cursor: pointer;
      transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
    }
    .filter-chip.primary {
      border-color: rgba(34, 78, 132, 0.38);
    }
    .filter-chip.active {
      background: linear-gradient(160deg, rgba(34, 78, 132, 0.97), rgba(53, 106, 171, 0.94));
      color: #f7fbff;
      border-color: rgba(34, 78, 132, 0.9);
      box-shadow: 0 16px 28px rgba(34, 78, 132, 0.2);
    }
    .filter-chip:hover {
      transform: translateY(-1px);
    }
    .filter-chip__label {
      font-weight: 700;
      font-size: 15px;
    }
    .filter-chip__meta {
      font-size: 12px;
      opacity: 0.9;
    }
    .filter-note {
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 14px;
    }
    .story-index {
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      margin-top: 16px;
    }
    .story-index-link {
      display: block;
      padding: 14px 16px;
      border-radius: 18px;
      text-decoration: none;
      color: inherit;
      background: linear-gradient(160deg, rgba(255, 253, 249, 0.96), rgba(243, 235, 223, 0.94));
      border: 1px solid rgba(223, 212, 195, 0.95);
    }
    .story-index-link strong,
    .story-index-link span {
      display: block;
    }
    .story-index-link span {
      margin-top: 6px;
      color: var(--muted);
      font-size: 12px;
    }
    .story-index-link:hover {
      border-color: rgba(34, 78, 132, 0.45);
    }
    .nav-summary {
      cursor: pointer;
      list-style: none;
      font-weight: 700;
      color: var(--accent);
    }
    .nav-summary::-webkit-details-marker {
      display: none;
    }
    .nav-summary::before {
      content: "▸";
      display: inline-block;
      margin-right: 8px;
      transition: transform 120ms ease;
    }
    details[open] > .nav-summary::before,
    details[open] > summary .story-toggle {
      transform: rotate(90deg);
    }
    .story-summary-row {
      padding: 20px;
      cursor: pointer;
      list-style: none;
    }
    .story-summary-row::-webkit-details-marker {
      display: none;
    }
    .story-heading {
      display: flex;
      gap: 12px;
      align-items: flex-start;
      flex: 1 1 560px;
    }
    .story-toggle {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      margin-top: 4px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 14px;
      transition: transform 120ms ease;
    }
    .story-toggle::before {
      content: "▸";
    }
    .story-stats {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
    .story-stats div {
      min-width: 100px;
      padding: 12px 14px;
      border-radius: 16px;
      background: var(--panel-strong);
      border: 1px solid rgba(223, 212, 195, 0.95);
      text-align: center;
    }
    .story-stats strong,
    .story-stats span {
      display: block;
    }
    .story-stats span {
      color: var(--muted);
      font-size: 12px;
    }
    .story-meta,
    .article-meta,
    .article-links,
    .chips {
      display: flex;
      gap: 8px 14px;
      flex-wrap: wrap;
    }
    .story-meta {
      padding: 0 20px;
      color: var(--muted);
      font-size: 14px;
    }
    .story-blurb,
    .story-articles {
      padding: 0 20px 20px;
    }
    .story-blurb {
      margin-top: 16px;
    }
    .story-blurb p {
      margin-bottom: 0;
      color: #314052;
    }
    .chips {
      gap: 8px;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 0 12px;
      border-radius: 999px;
      background: #efe3d3;
      color: #6d533d;
      font-size: 12px;
      font-weight: 700;
    }
    .article-card {
      padding: 18px;
      border-radius: 20px;
      background: var(--panel-strong);
      border: 1px solid rgba(223, 212, 195, 0.95);
    }
    .article-meta {
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 0;
    }
    .article-links {
      margin: 12px 0 14px;
    }
    .text-link,
    .article-card h3 a {
      color: var(--accent);
      text-decoration: none;
    }
    .text-link:hover,
    .article-card h3 a:hover {
      text-decoration: underline;
    }
    .summary-box {
      border-radius: 18px;
      padding: 14px 16px;
      border: 1px solid rgba(223, 212, 195, 0.95);
    }
    .summary-ai {
      background: var(--ai-bg);
      border-color: rgba(140, 183, 157, 0.65);
    }
    .summary-raw {
      background: var(--raw-bg);
      border-color: rgba(196, 160, 134, 0.65);
    }
    .summary-label {
      margin-bottom: 8px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-weight: 700;
      color: var(--muted);
    }
    .summary-ai .summary-label {
      color: var(--ai-ink);
    }
    .summary-raw .summary-label {
      color: var(--raw-ink);
    }
    .body-text {
      color: #304052;
      font-size: 15px;
      word-break: break-word;
    }
    .body-text.full {
      margin-top: 12px;
      white-space: pre-wrap;
    }
    .raw-details {
      margin-top: 12px;
    }
    .raw-details summary {
      cursor: pointer;
      color: var(--accent);
      font-weight: 600;
    }
    .empty-state {
      margin-top: 14px;
      color: var(--muted);
      font-size: 14px;
    }
    .footer-note {
      margin-top: 18px;
      color: var(--muted);
      font-size: 13px;
      text-align: center;
    }
    /* Flat article view for "Mais recente" mode */
    .flat-articles {
      display: grid;
      gap: 14px;
      margin-top: 18px;
    }
    .flat-articles .article-card {
      background: var(--panel);
      border: 1px solid rgba(223, 212, 195, 0.9);
      border-radius: 24px;
      box-shadow: var(--shadow);
      padding: 20px;
    }

    /* Compat: old card classes from previous HTML snapshots */
    .story-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
      flex-wrap: wrap;
      list-style: none;
      cursor: pointer;
      padding: 18px;
    }
    .story-head::-webkit-details-marker { display: none; }
    .story-main {
      display: flex;
      gap: 10px;
      flex: 1 1 560px;
    }
    .story-arrow {
      width: 26px;
      height: 26px;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: var(--accent-soft);
      color: var(--accent);
      margin-top: 4px;
      transition: transform 120ms ease;
    }
    .story-arrow::before { content: "\\25b8"; }
    details[open] > summary .story-arrow { transform: rotate(90deg); }
    .story-summary { padding: 0 18px 18px; }
    .story-summary p { margin-bottom: 0; color: #304052; }
    .meta-line { display: flex; gap: 8px 14px; flex-wrap: wrap; color: var(--muted); font-size: 13px; }
    .link-row { display: flex; gap: 8px 14px; flex-wrap: wrap; margin: 12px 0 14px; }
    .link { color: var(--accent); text-decoration: none; }
    .link:hover { text-decoration: underline; }
    .body { color: #304052; font-size: 15px; word-break: break-word; }
    .body.full { margin-top: 12px; white-space: pre-wrap; }

    .load-more-btn {
      display: flex; align-items: center; justify-content: center; gap: 8px;
      width: 100%; padding: 16px; margin-top: 12px;
      border: 2px dashed var(--line, #b4c4d1); border-radius: 14px;
      background: var(--surface-soft, #f8fafc); color: var(--brand, #0b4b7f);
      font-weight: 700; font-size: 15px; cursor: pointer;
      transition: background 120ms, border-color 120ms;
    }
    .load-more-btn:hover { background: var(--chip-bg, rgba(11,75,127,0.1)); border-color: var(--brand, #0b4b7f); }
    .load-more-btn:disabled { cursor: wait; opacity: 0.7; }
    .flat-loading {
      display: flex; align-items: center; justify-content: center; gap: 10px;
      padding: 32px 16px; color: var(--muted, #516679); font-size: 15px;
    }
    .flat-spinner {
      width: 20px; height: 20px;
      border: 3px solid var(--line, #b4c4d1); border-top-color: var(--brand, #0b4b7f);
      border-radius: 50%; animation: spin 0.7s linear infinite; flex-shrink: 0;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    [hidden] {
      display: none !important;
    }
    @media (max-width: 720px) {
      main {
        width: min(100% - 16px, 100%);
        padding-top: 8px;
      }
      .hero,
      .panel {
        border-radius: 20px;
        padding-left: 18px;
        padding-right: 18px;
      }
      .story-card {
        padding-left: 0;
        padding-right: 0;
      }
      .story-summary-row,
      .story-head,
      .story-meta,
      .story-blurb,
      .story-summary,
      .story-articles {
        padding-left: 16px;
        padding-right: 16px;
      }
      .article-links {
        flex-direction: column;
        align-items: flex-start;
      }
      .story-stats div {
        min-width: 92px;
      }
    }
  </style>
</head>
<body>
  <main>
    <header class="hero">
      <p class="eyebrow">__SCOPE_KICKER__</p>
      <h1>__SCOPE_TITLE__</h1>
      <p>__SCOPE_TEXT__</p>
      <div class="stats">
        <div class="stat">
          <span>Escopo do arquivo</span>
          <strong>__SCOPE_VALUE__</strong>
          <small>Sem chamadas para /api depois da geracao.</small>
        </div>
        <div class="stat">
          <span>Historias visiveis</span>
          <strong id="visibleStoriesStat">__VISIBLE_STORIES__ / __TOTAL_STORIES__</strong>
          <small>Historias no arquivo: __TOTAL_STORIES__</small>
        </div>
        <div class="stat">
          <span>Noticias visiveis</span>
          <strong id="visibleArticlesStat">__VISIBLE_ARTICLES__ / __TOTAL_ARTICLES__</strong>
          <small>Somente noticias agrupadas em historias.</small>
        </div>
        <div class="stat">
          <span>Com resumo IA</span>
          <strong id="visibleAiStat">__VISIBLE_AI__ / __TOTAL_AI__</strong>
          <small>Mostra Resumo IA quando existir.</small>
        </div>
        <div class="stat">
          <span>Texto bruto</span>
          <strong id="visibleRawStat">__VISIBLE_RAW__ / __TOTAL_RAW__</strong>
          <small>Mostra texto bruto quando nao houver IA.</small>
        </div>
      </div>
      <div class="meta-row">
        <span>Gerado em: __GENERATED_AT__</span>
        <span>Banco consultado: __DB_NAME__</span>
        <span>Controles de coleta removidos: este arquivo nao dispara novas execucoes.</span>
      </div>
    </header>

    <section class="panel">
      <div class="section-head">
        <div>
          <p class="eyebrow">Filtro offline</p>
          <h2>Pessoas monitoradas</h2>
        </div>
      </div>
      <p class="filter-note">Abre filtrado em __DEFAULT_TARGET_LABEL__. Toque para adicionar ou remover pessoas do filtro.</p>
      <div class="filter-row" id="targetFilters">__FILTER_BUTTONS__</div>
      <p class="filter-note">Filtro ativo: <strong id="activeFilterText">__ACTIVE_FILTER_TEXT__</strong></p>
      <div class="filter-row" style="margin-top:12px">
        <button type="button" class="filter-chip active" id="sortNewest" data-sort="newest">Mais recente</button>
        <button type="button" class="filter-chip" id="sortHottest" data-sort="hottest">Noticias agrupadas</button>
      </div>
    </section>

    <details class="panel">
      <summary class="nav-summary">Indice de historias visiveis (<span id="visibleIndexCount">__VISIBLE_STORIES__</span>)</summary>
      <div class="story-index" id="storyIndex">__STORY_INDEX__</div>
      <p class="empty-state" id="emptyState"__EMPTY_HIDDEN__>Nenhuma historia corresponde aos filtros atuais.</p>
    </details>

    <section id="storyStack" hidden>__STORY_SECTIONS__</section>
    <section id="flatStack" class="flat-articles"></section>

    <p class="footer-note">Este snapshot foi gerado para compartilhamento em celular. As materias originais seguem com links externos; o restante funciona offline em um unico arquivo HTML.</p>
  </main>
  <script id="snapshot-payload" type="application/json">__PAYLOAD__</script>
  <script>
    (function () {
      const payloadEl = document.getElementById("snapshot-payload");
      if (!payloadEl) return;

      const payload = JSON.parse(payloadEl.textContent || "{}");
      const buttons = Array.from(document.querySelectorAll("[data-filter-target]"));
      const storyCards = Array.from(document.querySelectorAll("[data-story-id]"));
      const storyLinks = Array.from(document.querySelectorAll("[data-nav-story-id]"));
      const allTargets = Array.isArray(payload.targets) ? payload.targets.map((target) => target.key) : [];
      const selectedTargets = new Set(Array.isArray(payload.defaultTargets) ? payload.defaultTargets : []);
      const labelsByKey = {};

      (payload.targets || []).forEach((target) => {
        labelsByKey[target.key] = target.label || target.key;
      });

      if (!selectedTargets.size) {
        allTargets.forEach((key) => selectedTargets.add(key));
      }

      function storyTargets(storyId) {
        if (!payload.storyTargets) return [];
        return payload.storyTargets[String(storyId)] || [];
      }

      function storyVisible(targets) {
        if (!targets.length) return true;
        return targets.some((key) => selectedTargets.has(key));
      }

      function activeLabel() {
        if (!allTargets.length || selectedTargets.size === allTargets.length) {
          return "Todos os nomes monitorados";
        }
        return allTargets
          .filter((key) => selectedTargets.has(key))
          .map((key) => labelsByKey[key] || key)
          .join(" + ");
      }

      // --- Flat article index (built once) ---
      const flatStack = document.getElementById("flatStack");
      const storyStack = document.getElementById("storyStack");
      const indexPanel = document.getElementById("storyIndex") ? document.getElementById("storyIndex").closest("details") : null;

      // Parse date from "DD/MM/YYYY HH:MM UTC" text
      function parseDateText(text) {
        const m = (text || "").match(/([0-9]{2})[/]([0-9]{2})[/]([0-9]{4}) +([0-9]{2}):([0-9]{2})/);
        if (!m) return "";
        return m[3] + "-" + m[2] + "-" + m[1] + "T" + m[4] + ":" + m[5] + ":00Z";
      }

      // Build flat article data: for each article, record its parent story targets and date
      const articleIndex = [];
      storyCards.forEach((card) => {
        const sid = card.dataset.storyId;
        const targets = storyTargets(sid);
        card.querySelectorAll(".article-card").forEach((article) => {
          // Get ISO date from data attr or parse from visible text
          let pubIso = article.dataset.publishedIso || "";
          if (!pubIso) {
            const metaEl = article.querySelector(".article-meta, .meta-line");
            if (metaEl) {
              const spans = metaEl.querySelectorAll("span");
              for (const sp of spans) {
                const parsed = parseDateText(sp.textContent);
                if (parsed) { pubIso = parsed; break; }
              }
            }
          }
          const titleEl = article.querySelector("h3");
          const title = (article.dataset.title || (titleEl ? titleEl.textContent : "") || "").trim().toLowerCase();
          articleIndex.push({ el: article, storyId: sid, targets: targets, pubIso: pubIso, title: title });
        });
      });

      function applyFilters(skipFlatRebuild) {
        let visibleStories = 0;
        let visibleArticles = 0;
        let visibleAi = 0;
        let visibleRaw = 0;

        storyCards.forEach((card) => {
          const targets = storyTargets(card.dataset.storyId);
          const visible = storyVisible(targets);
          card.hidden = !visible;
          if (!visible) return;
          visibleStories += 1;
          visibleArticles += Number(card.dataset.articleCount || 0);
          visibleAi += Number(card.dataset.aiCount || 0);
          visibleRaw += Number(card.dataset.rawCount || 0);
        });

        storyLinks.forEach((link) => {
          link.hidden = !storyVisible(storyTargets(link.dataset.navStoryId));
        });

        buttons.forEach((button) => {
          button.classList.toggle("active", selectedTargets.has(button.dataset.filterTarget));
        });

        const storiesText = visibleStories + " / " + storyCards.length;
        const articlesText = visibleArticles + " / __TOTAL_ARTICLES__";
        const aiText = visibleAi + " / __TOTAL_AI__";
        const rawText = visibleRaw + " / __TOTAL_RAW__";

        document.getElementById("visibleStoriesStat").textContent = storiesText;
        document.getElementById("visibleArticlesStat").textContent = articlesText;
        document.getElementById("visibleAiStat").textContent = aiText;
        document.getElementById("visibleRawStat").textContent = rawText;
        document.getElementById("visibleIndexCount").textContent = String(visibleStories);
        document.getElementById("activeFilterText").textContent = activeLabel();
        document.getElementById("emptyState").hidden = visibleStories > 0;

        // Also update flat view if active
        if (currentSort === "newest" && !skipFlatRebuild) {
          buildFlatView();
        }
      }

      // --- Sort logic ---
      let currentSort = "newest";
      const LAZY_BATCH = 50;
      let flatSorted = [];
      let flatRendered = 0;
      let loadMoreBtn = null;
      let loadingEl = null;

      function ensureLoadingEl() {
        if (!loadingEl) {
          loadingEl = document.createElement("div");
          loadingEl.className = "flat-loading";
          loadingEl.innerHTML = '<div class="flat-spinner"></div> Carregando noticias...';
        }
        return loadingEl;
      }

      function renderFlatBatch() {
        if (flatRendered >= flatSorted.length) return;
        var end = Math.min(flatRendered + LAZY_BATCH, flatSorted.length);
        var frag = document.createDocumentFragment();
        for (var i = flatRendered; i < end; i++) {
          frag.appendChild(flatSorted[i].el.cloneNode(true));
        }
        if (loadMoreBtn) flatStack.insertBefore(frag, loadMoreBtn);
        else flatStack.appendChild(frag);
        flatRendered = end;
        updateLoadMoreBtn();
      }

      function updateLoadMoreBtn() {
        var remaining = flatSorted.length - flatRendered;
        if (remaining <= 0) {
          if (loadMoreBtn) { loadMoreBtn.remove(); loadMoreBtn = null; }
          return;
        }
        if (!loadMoreBtn) {
          loadMoreBtn = document.createElement("button");
          loadMoreBtn.type = "button";
          loadMoreBtn.className = "load-more-btn";
          loadMoreBtn.addEventListener("click", onLoadMore);
          flatStack.appendChild(loadMoreBtn);
        }
        loadMoreBtn.textContent = "Carregar mais noticias (" + remaining + " restantes)";
        loadMoreBtn.disabled = false;
      }

      function onLoadMore() {
        loadMoreBtn.disabled = true;
        loadMoreBtn.innerHTML = '<div class="flat-spinner"></div> Carregando...';
        requestAnimationFrame(function() {
          renderFlatBatch();
        });
      }

      function buildFlatView() {
        flatStack.innerHTML = "";
        flatRendered = 0;
        loadMoreBtn = null;
        flatSorted = articleIndex.filter(function(a) { return storyVisible(a.targets); });
        flatSorted.sort(function(a, b) {
          var cmp = (b.pubIso || "").localeCompare(a.pubIso || "");
          if (cmp !== 0) return cmp;
          return a.title.localeCompare(b.title);
        });
        if (flatSorted.length === 0) return;
        var el = ensureLoadingEl();
        flatStack.appendChild(el);
        requestAnimationFrame(function() {
          if (el.parentNode) el.remove();
          renderFlatBatch();
        });
      }

      function applySort() {
        if (currentSort === "newest") {
          // Flat article view
          storyStack.hidden = true;
          if (indexPanel) indexPanel.hidden = true;
          flatStack.hidden = false;
          buildFlatView();
        } else {
          // Grouped story view
          flatStack.hidden = true;
          flatStack.innerHTML = "";
          storyStack.hidden = false;
          if (indexPanel) indexPanel.hidden = false;

          const cards = Array.from(storyStack.querySelectorAll("[data-story-id]"));
          cards.sort((a, b) => {
            const ta = parseFloat(a.dataset.temperature || "0");
            const tb = parseFloat(b.dataset.temperature || "0");
            return tb - ta;
          });
          cards.forEach((card) => storyStack.appendChild(card));

          const index = document.getElementById("storyIndex");
          if (index) {
            const links = Array.from(index.querySelectorAll("[data-nav-story-id]"));
            links.sort((a, b) => {
              const idA = a.dataset.navStoryId;
              const idB = b.dataset.navStoryId;
              const cardA = storyStack.querySelector('[data-story-id="' + idA + '"]');
              const cardB = storyStack.querySelector('[data-story-id="' + idB + '"]');
              if (!cardA || !cardB) return 0;
              return Array.from(storyStack.children).indexOf(cardA) - Array.from(storyStack.children).indexOf(cardB);
            });
            links.forEach((link) => index.appendChild(link));
          }
        }

        document.querySelectorAll("[data-sort]").forEach((btn) => {
          btn.classList.toggle("active", btn.dataset.sort === currentSort);
        });
      }

      document.addEventListener("click", (event) => {
        const sortBtn = event.target.closest("[data-sort]");
        if (sortBtn) {
          currentSort = sortBtn.dataset.sort;
          applySort();
          return;
        }

        const button = event.target.closest("[data-filter-target]");
        if (!button) return;
        const key = button.dataset.filterTarget;
        if (!key) return;

        if (selectedTargets.has(key)) selectedTargets.delete(key);
        else selectedTargets.add(key);

        if (!selectedTargets.size) {
          allTargets.forEach((item) => selectedTargets.add(item));
        }

        applyFilters();
      });

      // Lazy-inject raw text when user opens a raw-details toggle
      document.addEventListener("toggle", (event) => {
        const el = event.target;
        if (el.classList.contains("raw-details") && el.open && !el.dataset.loaded) {
          const aid = el.dataset.articleId;
          const text = payload.rawTexts && payload.rawTexts[aid];
          if (text) {
            const fullTextDiv = el.querySelector(".body-text.full");
            if (fullTextDiv) {
              fullTextDiv.innerHTML = text;
            }
          }
          el.dataset.loaded = "1";
        }
      });

      applySort();
      applyFilters(true);
    })();
  </script>
</body>
</html>
"""

    return (
        template.replace("__PAGE_TITLE__", html.escape(scope_title))
        .replace("__SCOPE_KICKER__", html.escape(scope_kicker))
        .replace("__SCOPE_TITLE__", html.escape(scope_title))
        .replace("__SCOPE_TEXT__", html.escape(scope_text))
        .replace("__SCOPE_VALUE__", html.escape(scope_value))
        .replace("__VISIBLE_STORIES__", str(visible_story_count))
        .replace("__TOTAL_STORIES__", str(total_story_count))
        .replace("__VISIBLE_ARTICLES__", str(visible_article_count))
        .replace("__TOTAL_ARTICLES__", str(total_article_count))
        .replace("__VISIBLE_AI__", str(visible_ai_count))
        .replace("__TOTAL_AI__", str(total_ai_count))
        .replace("__VISIBLE_RAW__", str(visible_raw_count))
        .replace("__TOTAL_RAW__", str(total_raw_count))
        .replace("__GENERATED_AT__", html.escape(generated_at))
        .replace("__DB_NAME__", html.escape(DB_PATH.name))
        .replace("__DEFAULT_TARGET_LABEL__", html.escape(default_target_label))
        .replace("__FILTER_BUTTONS__", filter_buttons)
        .replace("__ACTIVE_FILTER_TEXT__", html.escape(active_filter_text))
        .replace("__STORY_INDEX__", story_index)
        .replace("__EMPTY_HIDDEN__", empty_hidden)
        .replace("__STORY_SECTIONS__", story_sections)
        .replace("__PAYLOAD__", json_for_script(payload))
    )


def summarize_article_payload(article: dict[str, Any]) -> tuple[str, str, str]:
    has_ai = bool(article.get("has_ai_summary"))
    summary = normalize_text(article.get("summary"))
    full_text = normalize_text(article.get("full_text"))
    snippet = normalize_text(article.get("snippet"))

    if has_ai and summary:
        return "Resumo IA", summary, ""

    if full_text:
        preview_source = summary or snippet or full_text
        preview = excerpt(preview_source, 560)
        if normalize_text(preview_source) == full_text and len(full_text) <= 560:
            return "Texto bruto", preview, ""
        return "Texto bruto", preview, full_text

    raw = summary or snippet
    if raw:
        return "Trecho bruto", raw, ""

    return "Sem resumo", "Sem conteudo disponivel.", ""


def serialize_article_payload(article: dict[str, Any], fallback_targets: list[str]) -> tuple[dict[str, Any], dict[str, str]]:
    aid = int(article.get("article_id") or 0)
    label, preview, full_text = summarize_article_payload(article)
    target_keys = [str(key) for key in article.get("target_keys") or fallback_targets or []]
    raw_text_key = f"article-{aid}" if aid and full_text else ""
    raw_texts = {raw_text_key: full_text} if raw_text_key and full_text else {}
    url = str(article.get("url") or "").strip()
    published_at = str(article.get("published_at") or "").strip()
    return (
        {
            "articleId": aid,
            "title": str(article.get("title") or "Sem titulo"),
            "url": url,
            "sourceName": str(article.get("source_name") or "Fonte nao identificada").strip(),
            "sourceHost": host_from_url(url),
            "publishedAt": published_at,
            "publishedDisplay": fmt_dt(published_at),
            "targetKeys": target_keys,
            "summaryLabel": label,
            "summaryPreview": preview,
            "rawTextKey": raw_text_key or None,
            "summarySource": "ai" if label == "Resumo IA" else "raw",
        },
        raw_texts,
    )


def build_story_records(
    stories: list[dict[str, Any]],
    article_map: dict[int, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    story_records: list[dict[str, Any]] = []
    raw_texts: dict[str, str] = {}

    for story in stories:
        summary_label, story_summary = story_display_summary(story, article_map)
        story_targets = [str(key) for key in story.get("targetKeys") or []]
        article_records: list[dict[str, Any]] = []
        for article_stub in story.get("articles", []):
            aid = article_id_int(article_stub.get("id"))
            detail = article_map.get(aid)
            if not detail:
                continue
            article_record, article_raw = serialize_article_payload(detail, story_targets)
            article_records.append(article_record)
            raw_texts.update(article_raw)

        story_records.append(
            {
                "storyIdInt": int(story.get("storyIdInt") or 0),
                "title": str(story.get("title") or "Sem titulo"),
                "summaryLabel": summary_label,
                "summaryText": story_summary,
                "temperature": float(story.get("temperature") or 0.0),
                "firstPublishedAt": str(story.get("firstPublishedAt") or ""),
                "lastPublishedAt": str(story.get("lastPublishedAt") or ""),
                "articleCount": int(story.get("articleCount") or len(article_records)),
                "aiCount": int(story.get("aiCount") or 0),
                "rawCount": int(story.get("rawCount") or max(len(article_records) - int(story.get("aiCount") or 0), 0)),
                "targetKeys": story_targets,
                "articles": article_records,
            }
        )

    story_records.sort(key=story_sort_key, reverse=True)
    return story_records, raw_texts


def html_fragment_to_text(fragment: str) -> str:
    text = str(fragment or "")
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(?:p|div|li|summary|h1|h2|h3)>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    return normalize_text(html.unescape(text))


def parse_tag_attrs(fragment: str, tag_name: str) -> dict[str, str]:
    match = re.search(rf"<{tag_name}\b([^>]*)>", fragment, re.IGNORECASE | re.DOTALL)
    if not match:
        return {}
    attrs: dict[str, str] = {}
    for name, value in re.findall(r'([A-Za-z_:][\w:.-]*)\s*=\s*"([^"]*)"', match.group(1), re.DOTALL):
        attrs[name] = html.unescape(value)
    for name, value in re.findall(r"([A-Za-z_:][\w:.-]*)\s*=\s*'([^']*)'", match.group(1), re.DOTALL):
        attrs.setdefault(name, html.unescape(value))
    return attrs


def extract_nested_tag_block(raw: str, start_index: int, tag_name: str) -> tuple[str, int]:
    token_re = re.compile(rf"</?{tag_name}\b", re.IGNORECASE)
    depth = 0
    for match in token_re.finditer(raw, start_index):
        is_close = raw[match.start() + 1] == "/"
        if not is_close:
            depth += 1
            continue
        depth -= 1
        if depth == 0:
            close_end = raw.find(">", match.end())
            if close_end == -1:
                return raw[start_index:], len(raw)
            return raw[start_index : close_end + 1], close_end + 1
    return raw[start_index:], len(raw)


def extract_story_card_blocks(raw: str) -> dict[int, str]:
    blocks: dict[int, str] = {}
    pattern = re.compile(r'<details\b[^>]*\bdata-story-id="(\d+)"[^>]*>', re.IGNORECASE)
    for match in pattern.finditer(raw):
        sid = int(match.group(1))
        if sid in blocks:
            continue
        block, _ = extract_nested_tag_block(raw, match.start(), "details")
        blocks[sid] = block
    return blocks


def infer_bundle_paths_from_html(html_path: Path, html_doc: str) -> tuple[Path | None, Path | None]:
    data_match = re.search(r'data-clipping-data-url="([^"]+)"', html_doc)
    raw_match = re.search(r'data-clipping-raw-url="([^"]+)"', html_doc)
    if data_match:
        data_path = (html_path.parent / html.unescape(data_match.group(1))).resolve()
        raw_path = (html_path.parent / html.unescape(raw_match.group(1))).resolve() if raw_match else None
        return data_path, raw_path

    candidates = [
        html_path.parent / "assets" / "clipping-data.json",
        html_path.parent / f"{html_path.stem}_assets" / "clipping-data.json",
    ]
    for candidate in candidates:
        if candidate.is_file():
            raw_candidate = candidate.with_name("clipping-raw-texts.json")
            return candidate.resolve(), raw_candidate.resolve() if raw_candidate.is_file() else None
    return None, None


def parse_bundle_snapshot(path: Path, html_doc: str) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, str]] | None:
    data_path, raw_path = infer_bundle_paths_from_html(path, html_doc)
    if not data_path or not data_path.is_file():
        return None

    payload = json.loads(data_path.read_text(encoding="utf-8"))
    raw_texts = {}
    if raw_path and raw_path.is_file():
        raw_texts = json.loads(raw_path.read_text(encoding="utf-8"))

    stories: list[dict[str, Any]] = []
    for story in payload.get("stories", []):
        stories.append(
            {
                "storyIdInt": int(story.get("storyIdInt") or story.get("storyId") or 0),
                "title": str(story.get("title") or "Sem titulo"),
                "summaryLabel": str(story.get("summaryLabel") or "Sem resumo"),
                "summaryText": str(story.get("summaryText") or "Sem resumo."),
                "temperature": float(story.get("temperature") or 0.0),
                "firstPublishedAt": str(story.get("firstPublishedAt") or ""),
                "lastPublishedAt": str(story.get("lastPublishedAt") or ""),
                "articleCount": int(story.get("articleCount") or 0),
                "aiCount": int(story.get("aiCount") or 0),
                "rawCount": int(story.get("rawCount") or 0),
                "targetKeys": [str(key) for key in story.get("targetKeys") or []],
                "articles": [
                    {
                        "articleId": int(article.get("articleId") or 0),
                        "title": str(article.get("title") or "Sem titulo"),
                        "url": str(article.get("url") or ""),
                        "sourceName": str(article.get("sourceName") or "Fonte nao identificada"),
                        "sourceHost": str(article.get("sourceHost") or ""),
                        "publishedAt": str(article.get("publishedAt") or ""),
                        "publishedDisplay": str(article.get("publishedDisplay") or ""),
                        "targetKeys": [str(key) for key in article.get("targetKeys") or []],
                        "summaryLabel": str(article.get("summaryLabel") or "Sem resumo"),
                        "summaryPreview": str(article.get("summaryPreview") or ""),
                        "rawTextKey": article.get("rawTextKey") or None,
                        "summarySource": str(article.get("summarySource") or "raw"),
                    }
                    for article in story.get("articles", [])
                ],
            }
        )

    merge_meta = {
        "targets": payload.get("targets", []),
        "defaultTargets": payload.get("defaultTargets", []),
        "storyTargets": {
            str(story.get("storyIdInt") or story.get("storyId") or 0): [str(key) for key in story.get("targetKeys") or []]
            for story in stories
        },
    }
    return merge_meta, stories, raw_texts


def parse_legacy_article_blocks(story_html: str) -> list[str]:
    return [
        match.group(1)
        for match in re.finditer(
            r'(<article\b[^>]*class="[^"]*\barticle-card\b[^"]*"[^>]*>.*?</article>)',
            story_html,
            re.IGNORECASE | re.DOTALL,
        )
    ]


def parse_legacy_story_records(
    html_doc: str,
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    story_targets_map: dict[str, list[str]] = payload.get("storyTargets", {}) or {}
    raw_texts = {
        str(key): html_fragment_to_text(value)
        for key, value in (payload.get("rawTexts", {}) or {}).items()
    }
    story_records: list[dict[str, Any]] = []
    next_article_id = max(
        [article_id_int(match) for match in re.findall(r"article-(\d+)", html_doc)] or [0]
    ) + 1

    for sid, card_html in extract_story_card_blocks(html_doc).items():
        attrs = parse_tag_attrs(card_html, "details")
        story_targets = [str(key) for key in story_targets_map.get(str(sid), [])]
        if not story_targets:
            story_targets = [key for key in str(attrs.get("data-targets") or "").split(",") if key]

        title_match = re.search(r"<h2[^>]*>(.*?)</h2>", card_html, re.IGNORECASE | re.DOTALL)
        summary_label_match = re.search(
            r'<div class="summary-label">(.*?)</div>',
            card_html,
            re.IGNORECASE | re.DOTALL,
        )
        summary_text_match = re.search(
            r'<div class="(?:story-blurb|story-summary)">.*?<p>(.*?)</p>',
            card_html,
            re.IGNORECASE | re.DOTALL,
        )

        article_records: list[dict[str, Any]] = []
        for article_html in parse_legacy_article_blocks(card_html):
            article_attrs = parse_tag_attrs(article_html, "article")
            article_id = article_id_int(article_attrs.get("id") or article_attrs.get("data-article-id"))
            if not article_id:
                article_id = next_article_id
                next_article_id += 1

            link_match = re.search(
                r'<h3[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>\s*</h3>',
                article_html,
                re.IGNORECASE | re.DOTALL,
            )
            title_only_match = re.search(r"<h3[^>]*>(.*?)</h3>", article_html, re.IGNORECASE | re.DOTALL)
            meta_match = re.search(
                r'<p class="(?:article-meta|meta-line)">(.*?)</p>',
                article_html,
                re.IGNORECASE | re.DOTALL,
            )
            if not meta_match:
                meta_match = re.search(
                    r'<div class="(?:article-meta|meta-line)">(.*?)</div>',
                    article_html,
                    re.IGNORECASE | re.DOTALL,
                )
            spans = re.findall(r"<span[^>]*>(.*?)</span>", meta_match.group(1) if meta_match else "", re.IGNORECASE | re.DOTALL)
            preview_match = re.search(
                r'<div class="(?:body-text|body)">(.*?)</div>',
                article_html,
                re.IGNORECASE | re.DOTALL,
            )
            full_match = re.search(
                r'<div class="(?:body-text|body) full">(.*?)</div>',
                article_html,
                re.IGNORECASE | re.DOTALL,
            )
            summary_label = "Resumo IA" if "summary-ai" in article_html else "Texto bruto"
            summary_label_block = re.search(
                r'<div class="summary-label">(.*?)</div>',
                article_html,
                re.IGNORECASE | re.DOTALL,
            )
            if summary_label_block:
                summary_label = html_fragment_to_text(summary_label_block.group(1))

            raw_text_key = ""
            if full_match:
                raw_text_key = f"article-{article_id}"
                raw_texts[raw_text_key] = html_fragment_to_text(full_match.group(1))

            url = html.unescape(link_match.group(1)) if link_match else ""
            title_html = link_match.group(2) if link_match else (title_only_match.group(1) if title_only_match else "")
            published_display = html_fragment_to_text(spans[1]) if len(spans) > 1 else ""
            published_at = _parse_old_date(published_display)
            article_records.append(
                {
                    "articleId": article_id,
                    "title": html_fragment_to_text(title_html) or "Sem titulo",
                    "url": url,
                    "sourceName": html_fragment_to_text(spans[0]) if spans else "Fonte nao identificada",
                    "sourceHost": html_fragment_to_text(spans[2]) if len(spans) > 2 else host_from_url(url),
                    "publishedAt": published_at,
                    "publishedDisplay": published_display or fmt_dt(published_at),
                    "targetKeys": story_targets,
                    "summaryLabel": summary_label or "Sem resumo",
                    "summaryPreview": html_fragment_to_text(preview_match.group(1) if preview_match else ""),
                    "rawTextKey": raw_text_key or None,
                    "summarySource": "ai" if summary_label == "Resumo IA" else "raw",
                }
            )

        first_published_match = re.search(r"[Pp]rimeira publica[cç][aã]o:\s*([^<]+)", card_html)
        last_published_match = re.search(r"[Uu]ltima publica[cç][aã]o:\s*([^<]+)", card_html)
        temperature = attrs.get("data-temperature") or "0"
        if not str(temperature).strip():
            temp_match = re.search(
                r"<strong>(\d+)</strong>\s*<span[^>]*>\s*temperatura\s*</span>",
                card_html,
                re.IGNORECASE,
            )
            temperature = temp_match.group(1) if temp_match else "0"

        story_records.append(
            {
                "storyIdInt": sid,
                "title": html_fragment_to_text(title_match.group(1) if title_match else "Sem titulo"),
                "summaryLabel": html_fragment_to_text(summary_label_match.group(1) if summary_label_match else "Resumo do agrupamento"),
                "summaryText": html_fragment_to_text(summary_text_match.group(1) if summary_text_match else ""),
                "temperature": float(temperature or 0.0),
                "firstPublishedAt": _parse_old_date(first_published_match.group(1)) if first_published_match else "",
                "lastPublishedAt": attrs.get("data-last-published") or (_parse_old_date(last_published_match.group(1)) if last_published_match else ""),
                "articleCount": int(attrs.get("data-article-count") or len(article_records)),
                "aiCount": int(attrs.get("data-ai-count") or 0),
                "rawCount": int(attrs.get("data-raw-count") or max(len(article_records) - int(attrs.get("data-ai-count") or 0), 0)),
                "targetKeys": story_targets,
                "articles": article_records,
            }
        )

    story_records.sort(key=story_sort_key, reverse=True)
    return story_records, raw_texts


def parse_source_snapshot(path: str) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, str]]:
    source_path = Path(path).expanduser().resolve()
    html_doc = source_path.read_text(encoding="utf-8")
    bundle_snapshot = parse_bundle_snapshot(source_path, html_doc)
    if bundle_snapshot is not None:
        return bundle_snapshot

    payload: dict[str, Any] = {}
    payload_match = re.search(r'<script[^>]*id="snapshot-payload"[^>]*>(.*?)</script>', html_doc, re.DOTALL)
    if payload_match:
        payload = json.loads(payload_match.group(1))
    story_records, raw_texts = parse_legacy_story_records(html_doc, payload)
    merge_meta = {
        "targets": payload.get("targets", []),
        "defaultTargets": payload.get("defaultTargets", []),
        "storyTargets": payload.get("storyTargets", {}),
    }
    return merge_meta, story_records, raw_texts


def max_story_id_from_records(stories: list[dict[str, Any]]) -> int:
    ids = [int(story.get("storyIdInt") or 0) for story in stories]
    return max(ids) if ids else 0


def max_article_id_from_records(stories: list[dict[str, Any]], raw_texts: dict[str, str] | None = None) -> int:
    ids = [
        int(article.get("articleId") or 0)
        for story in stories
        for article in story.get("articles", [])
    ]
    if raw_texts:
        ids.extend(article_id_int(key) for key in raw_texts)
    return max(ids) if ids else 0


def build_story_dataset(
    *,
    args: argparse.Namespace,
    stories: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    initial_targets: list[str],
    raw_texts: dict[str, str],
    generated_at: str,
    db_name: str,
) -> dict[str, Any]:
    initial_stats = visibility_stats(stories, initial_targets)
    scope_kicker, scope_title, scope_text = scope_labels(args)
    scope_value = "Banco inteiro" if args.all_stories else f"{args.date_from} a {args.date_to}"
    default_target_label = target_label_map(target_rows).get(args.default_target, args.default_target)

    return {
        "meta": {
            "pageTitle": "Clipping Completo | Flavio Valle" if args.all_stories else scope_title,
            "scopeKicker": scope_kicker,
            "scopeTitle": scope_title,
            "scopeText": scope_text,
            "scopeValue": scope_value,
            "generatedAt": generated_at,
            "dbName": db_name,
            "defaultTargetLabel": default_target_label,
            "totalStories": len(stories),
            "totalArticles": sum(int(story.get("articleCount") or 0) for story in stories),
            "totalAi": sum(int(story.get("aiCount") or 0) for story in stories),
            "totalRaw": sum(int(story.get("rawCount") or 0) for story in stories),
            "initialStoryCount": int(initial_stats["storyCount"]),
            "initialArticleCount": int(initial_stats["articleCount"]),
            "initialAiCount": int(initial_stats["aiCount"]),
            "initialRawCount": int(initial_stats["rawCount"]),
        },
        "targets": [
            {
                "key": str(row["key"]),
                "label": str(row["label"]),
                "primary": bool(row.get("primary", False)),
                "storyCount": int(row.get("storyCount") or 0),
                "articleCount": int(row.get("articleCount") or 0),
            }
            for row in target_rows
        ],
        "defaultTargets": list(initial_targets),
        "stories": stories,
    }


def bundle_asset_dir_for_output(args: argparse.Namespace, output_path: Path) -> Path:
    if args.all_stories and output_path.resolve() == PAGES_INDEX_PATH.resolve():
        return PAGES_ASSETS_DIR
    return output_path.parent / f"{output_path.stem}_assets"


def relative_url(from_path: Path, target_path: Path) -> str:
    return os.path.relpath(target_path, start=from_path.parent).replace(os.sep, "/")


def build_pages_stylesheet() -> str:
    return (PAGES_ASSET_TEMPLATES_DIR / "clipping.css").read_text(encoding="utf-8")


def build_pages_javascript() -> str:
    return (PAGES_ASSET_TEMPLATES_DIR / "clipping.js").read_text(encoding="utf-8")


def build_pages_shell_html(
    dataset: dict[str, Any],
    *,
    css_url: str,
    js_url: str,
    data_url: str,
    raw_url: str,
) -> str:
    meta = dataset["meta"]
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="clipping-snapshot-sentinel" content="{html.escape(WIX_SNAPSHOT_SENTINEL)}">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(str(meta.get("pageTitle") or "Clipping Completo | Flavio Valle"))}</title>
  <link rel="stylesheet" href="{html.escape(css_url)}">
</head>
<body>
  <main
    id="app"
    data-clipping-data-url="{html.escape(data_url)}"
    data-clipping-raw-url="{html.escape(raw_url)}"
  >
    <header class="hero">
      <div class="hero-lockup">
        <p class="eyebrow">Mandato Flavio Valle</p>
        <h1>{html.escape(str(meta.get("scopeTitle") or "Clipping Completo"))}</h1>
        <p>{html.escape(str(meta.get("scopeText") or ""))}</p>
        <div class="hero-tags">
          <span class="hero-tag hero-tag--gold">{html.escape(str(meta.get("scopeValue") or "Banco inteiro"))}</span>
          <span class="hero-tag">Painel Pages</span>
          <span class="hero-tag">Renderizacao sob demanda</span>
        </div>
      </div>
      <div class="stats">
        <div class="stat">
          <span>Escopo</span>
          <strong>{html.escape(str(meta.get("scopeValue") or ""))}</strong>
          <small>Bundle estatico leve para GitHub Pages.</small>
        </div>
        <div class="stat">
          <span>Historias visiveis</span>
          <strong id="visibleStoriesStat">{int(meta.get("initialStoryCount") or 0)} / {int(meta.get("totalStories") or 0)}</strong>
          <small>Historias do dataset publicado.</small>
        </div>
        <div class="stat">
          <span>Noticias visiveis</span>
          <strong id="visibleArticlesStat">{int(meta.get("initialArticleCount") or 0)} / {int(meta.get("totalArticles") or 0)}</strong>
          <small>Modo recente sem agrupamento.</small>
        </div>
        <div class="stat">
          <span>Resumo IA</span>
          <strong id="visibleAiStat">{int(meta.get("initialAiCount") or 0)} / {int(meta.get("totalAi") or 0)}</strong>
          <small>Exibe Resumo IA quando existir.</small>
        </div>
        <div class="stat">
          <span>Texto bruto</span>
          <strong id="visibleRawStat">{int(meta.get("initialRawCount") or 0)} / {int(meta.get("totalRaw") or 0)}</strong>
          <small>Texto completo carregado sob demanda.</small>
        </div>
      </div>
      <div class="meta-row">
        <span>Gerado em: {html.escape(str(meta.get("generatedAt") or ""))}</span>
        <span>Base consultada: {html.escape(str(meta.get("dbName") or ""))}</span>
        <span>Renderizacao cliente-side para reduzir DOM inicial e uso de RAM.</span>
      </div>
    </header>

    <section class="panel">
      <div class="section-head">
        <div>
          <p class="eyebrow">Monitoramento institucional</p>
          <h2>Nomes acompanhados</h2>
        </div>
      </div>
      <p class="filter-note">O arquivo abre com foco em {html.escape(str(meta.get("defaultTargetLabel") or "Flavio Valle"))}. Toque para incluir ou remover nomes do acompanhamento.</p>
      <div class="filter-row" id="targetFilters"></div>
      <p class="filter-note">Monitoramento ativo: <strong id="activeFilterText">Carregando...</strong></p>
      <div class="filter-row" style="margin-top:12px">
        <button type="button" class="filter-chip active" data-sort="newest">Mais recentes</button>
        <button type="button" class="filter-chip" data-sort="hottest">Historias agrupadas</button>
      </div>
    </section>

    <details class="panel" id="indexPanel" hidden>
      <summary class="nav-summary">Indice de historias visiveis (<span id="visibleIndexCount">{int(meta.get("initialStoryCount") or 0)}</span>)</summary>
      <div class="story-index" id="storyIndex"></div>
      <p class="empty-state" id="emptyState" hidden>Nenhuma historia corresponde aos filtros atuais.</p>
    </details>

    <section class="panel shell-loading" id="loadingState">
      <div class="flat-spinner"></div>
      <div>
        <strong>Carregando dados do clipping...</strong>
        <p>As historias e noticias serao renderizadas sob demanda para manter o bundle leve.</p>
      </div>
    </section>

    <section id="storyStack" hidden></section>
    <section id="flatStack" class="flat-articles" hidden></section>

    <p class="footer-note">Arquivo institucional estatico para GitHub Pages. Historias e materias sao montadas no cliente a partir de JSON externo para reduzir memoria e acelerar o carregamento inicial.</p>
  </main>
  <script src="{html.escape(js_url)}" defer></script>
</body>
</html>
"""


def build_snapshot_artifact(args: argparse.Namespace) -> dict[str, Any]:
    db_path = Path(args.db).expanduser() if args.db else DB_PATH
    db = ClippingDB(db_path)
    base_targets = load_targets()
    detailed_articles = load_scope_articles(db, args)
    article_map = {int(row["article_id"]): row for row in detailed_articles}
    stories = decorate_stories(db.story_with_articles(), article_map)

    merged_story_records: list[dict[str, Any]] = []
    merged_raw_texts: dict[str, str] = {}

    if args.merge_from:
        source_path = Path(args.merge_from).expanduser()
        if not source_path.is_file():
            raise FileNotFoundError(f"arquivo --merge-from nao encontrado: {source_path}")
        merge_meta, parsed_story_records, parsed_raw_texts = parse_source_snapshot(str(source_path))

        if args.remap_incoming_ids_on_merge:
            story_offset = max_story_id_from_records(parsed_story_records)
            article_offset = max_article_id_from_records(parsed_story_records, parsed_raw_texts)
            stories, article_map = remap_scope_ids(
                stories,
                article_map,
                story_offset=story_offset,
                article_offset=article_offset,
            )

        new_story_ids = {int(story.get("storyIdInt") or 0) for story in stories}
        merged_story_records = [
            story
            for story in parsed_story_records
            if int(story.get("storyIdInt") or 0) not in new_story_ids
        ]

        existing_keys = {str(target.get("key") or "") for target in base_targets}
        for target in merge_meta.get("targets", []):
            key = str(target.get("key") or "")
            if key and key not in existing_keys:
                base_targets.append(
                    {
                        "key": key,
                        "label": target.get("label", key),
                        "primary": bool(target.get("primary", False)),
                    }
                )
                existing_keys.add(key)

        for story in merged_story_records:
            for article in story.get("articles", []):
                raw_key = article.get("rawTextKey")
                if raw_key and raw_key in parsed_raw_texts:
                    merged_raw_texts[str(raw_key)] = parsed_raw_texts[str(raw_key)]

    story_records, raw_texts = build_story_records(stories, article_map)
    story_records.extend(merged_story_records)
    story_records.sort(key=story_sort_key, reverse=True)
    raw_texts.update(merged_raw_texts)

    target_rows = build_target_rows(base_targets, story_records)
    initial_targets = resolve_initial_targets(target_rows, args.default_target)
    generated_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    dataset = build_story_dataset(
        args=args,
        stories=story_records,
        target_rows=target_rows,
        initial_targets=initial_targets,
        raw_texts=raw_texts,
        generated_at=generated_at,
        db_name=db_path.name,
    )

    output_path = output_path_for_args(args)
    asset_dir = bundle_asset_dir_for_output(args, output_path)
    asset_paths = {
        "css": asset_dir / "clipping.css",
        "js": asset_dir / "clipping.js",
        "data": asset_dir / "clipping-data.json",
        "raw": asset_dir / "clipping-raw-texts.json",
    }
    html_doc = build_pages_shell_html(
        dataset,
        css_url=relative_url(output_path, asset_paths["css"]),
        js_url=relative_url(output_path, asset_paths["js"]),
        data_url=relative_url(output_path, asset_paths["data"]),
        raw_url=relative_url(output_path, asset_paths["raw"]),
    )

    return {
        "html_doc": html_doc,
        "data_payload": dataset,
        "raw_texts": raw_texts,
        "css_text": build_pages_stylesheet(),
        "js_text": build_pages_javascript(),
        "asset_paths": asset_paths,
        "initial_stats": visibility_stats(story_records, initial_targets),
        "output_path": output_path,
        "story_records": story_records,
        "target_rows": target_rows,
    }


def write_bundle_assets(artifact: dict[str, Any], asset_paths: dict[str, Path]) -> None:
    asset_paths["css"].parent.mkdir(parents=True, exist_ok=True)
    asset_paths["css"].write_text(artifact["css_text"], encoding="utf-8")
    asset_paths["js"].write_text(artifact["js_text"], encoding="utf-8")
    asset_paths["data"].write_text(
        json.dumps(artifact["data_payload"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    asset_paths["raw"].write_text(
        json.dumps(artifact["raw_texts"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_shell_html(output_path: Path, dataset: dict[str, Any], asset_paths: dict[str, Path]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_pages_shell_html(
            dataset,
            css_url=relative_url(output_path, asset_paths["css"]),
            js_url=relative_url(output_path, asset_paths["js"]),
            data_url=relative_url(output_path, asset_paths["data"]),
            raw_url=relative_url(output_path, asset_paths["raw"]),
        ),
        encoding="utf-8",
    )


def restyle_html_for_flavio_valle(html_doc: str, *, args: argparse.Namespace) -> str:
    scope_tag = "Banco completo" if args.all_stories else f"Recorte {args.date_from} a {args.date_to}"
    if args.all_stories:
        hero_title = "Clipping Completo"
        hero_text = (
            "Painel offline de acompanhamento institucional do gabinete, com foco em leitura "
            "mobile, filtros locais e acesso rapido as historias e materias do monitoramento."
        )
    else:
        hero_title = "Clipping Institucional"
        hero_text = (
            f"Painel offline do gabinete para acompanhamento institucional no periodo de "
            f"{args.date_from} a {args.date_to}, com filtros locais e leitura otimizada para celular."
        )

    stylesheet = """
    :root {
      color-scheme: light;
      --bg: #eef3f7;
      --bg-deep: #05253e;
      --brand: #0b4b7f;
      --brand-strong: #08365a;
      --gold: #f6bb1b;
      --surface: #ffffff;
      --surface-soft: #f8fafc;
      --surface-muted: #ececec;
      --text: #05253e;
      --muted: #516679;
      --line: #b4c4d1;
      --link: #1d67cd;
      --chip-bg: rgba(11, 75, 127, 0.1);
      --chip-ink: #0b4b7f;
      --shadow: 0 22px 48px rgba(5, 37, 62, 0.12);
      --shadow-strong: 0 28px 60px rgba(5, 37, 62, 0.24);
      --ai-bg: #e9f2fb;
      --ai-ink: #0b4b7f;
      --raw-bg: #fff6dc;
      --raw-ink: #6f5610;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      background:
        radial-gradient(circle at top left, rgba(246, 187, 27, 0.12), transparent 26%),
        radial-gradient(circle at top right, rgba(180, 196, 209, 0.24), transparent 28%),
        linear-gradient(180deg, var(--bg-deep) 0, var(--brand) 240px, var(--bg) 240px, var(--bg) 100%);
      color: var(--text);
      font-family: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      line-height: 1.6;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background:
        linear-gradient(160deg, rgba(255, 255, 255, 0.04), transparent 26%),
        radial-gradient(circle at 12% 12%, rgba(255, 255, 255, 0.08), transparent 16%);
      opacity: 0.9;
    }
    a { color: inherit; }
    main {
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 48px;
      position: relative;
      z-index: 1;
    }
    .hero,
    .panel {
      border-radius: 28px;
      border: 1px solid rgba(180, 196, 209, 0.78);
      box-shadow: var(--shadow);
    }
    .hero {
      position: relative;
      overflow: hidden;
      padding: 30px;
      background:
        radial-gradient(circle at top right, rgba(246, 187, 27, 0.22), transparent 28%),
        linear-gradient(135deg, rgba(5, 37, 62, 0.98), rgba(11, 75, 127, 0.97));
      color: #ececec;
      box-shadow: var(--shadow-strong);
    }
    .hero::after {
      content: "";
      position: absolute;
      right: -70px;
      bottom: -90px;
      width: 260px;
      height: 260px;
      border-radius: 999px;
      background: radial-gradient(circle, rgba(246, 187, 27, 0.24), rgba(246, 187, 27, 0));
    }
    .hero-lockup {
      position: relative;
      z-index: 1;
      max-width: 760px;
    }
    .hero-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 18px 0 0;
    }
    .hero-tag {
      display: inline-flex;
      align-items: center;
      min-height: 34px;
      padding: 8px 14px;
      border-radius: 999px;
      border: 1px solid rgba(180, 196, 209, 0.28);
      background: rgba(255, 255, 255, 0.08);
      color: #ececec;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }
    .hero-tag--gold {
      background: var(--gold);
      border-color: transparent;
      color: var(--bg-deep);
    }
    .panel {
      background: rgba(255, 255, 255, 0.98);
      margin-top: 18px;
      padding: 22px;
    }
    .story-card {
      padding: 0;
      overflow: hidden;
      background: linear-gradient(180deg, #ffffff 0, #f9fbfd 100%);
    }
    .eyebrow {
      margin: 0 0 10px;
      font-size: 12px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      font-weight: 800;
      color: var(--muted);
    }
    .hero .eyebrow {
      color: #b4c4d1;
    }
    .hero h1,
    .section-head h2,
    .story-heading h2,
    .article-card h3 {
      margin: 0;
      font-family: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      font-weight: 800;
      letter-spacing: -0.03em;
    }
    .hero h1 {
      font-size: clamp(32px, 5vw, 52px);
      line-height: 1.02;
      color: #ffffff;
    }
    .hero p {
      margin: 14px 0 0;
      max-width: 720px;
      color: rgba(236, 236, 236, 0.88);
      font-size: 16px;
    }
    .stats {
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin-top: 24px;
    }
    .stat {
      min-height: 124px;
      padding: 16px;
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(180, 196, 209, 0.18);
      backdrop-filter: blur(8px);
    }
    .stat span {
      display: block;
      color: #b4c4d1;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }
    .stat strong {
      display: block;
      margin-top: 10px;
      font-size: clamp(26px, 4vw, 34px);
      line-height: 1.05;
      color: #ffffff;
    }
    .stat small {
      display: block;
      margin-top: 8px;
      color: rgba(236, 236, 236, 0.8);
      font-size: 12px;
    }
    .meta-row {
      position: relative;
      z-index: 1;
      display: flex;
      flex-wrap: wrap;
      gap: 8px 16px;
      margin-top: 18px;
      padding-top: 16px;
      border-top: 1px solid rgba(180, 196, 209, 0.22);
      font-size: 13px;
      color: #b4c4d1;
    }
    .section-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
      margin-bottom: 8px;
    }
    .section-head h2 {
      font-size: 24px;
      color: var(--bg-deep);
    }
    .filter-note {
      margin: 0;
      color: var(--muted);
      font-size: 14px;
    }
    .filter-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 16px;
    }
    .filter-chip {
      appearance: none;
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 12px 14px;
      background: linear-gradient(180deg, #f9fbfd 0, #f3f7fb 100%);
      color: var(--text);
      cursor: pointer;
      transition: transform 120ms ease, border-color 120ms ease, box-shadow 120ms ease, background 120ms ease;
      display: flex;
      gap: 8px;
      align-items: flex-start;
      min-width: 132px;
      text-align: left;
    }
    .filter-chip.primary {
      border-color: rgba(11, 75, 127, 0.36);
    }
    .filter-chip.active {
      background: linear-gradient(135deg, #f6bb1b 0, #ffd76a 100%);
      color: var(--bg-deep);
      border-color: transparent;
      box-shadow: 0 10px 24px rgba(246, 187, 27, 0.28);
    }
    .filter-chip:hover {
      transform: translateY(-1px);
      border-color: var(--brand);
    }
    .filter-chip__label {
      display: block;
      font-weight: 800;
      font-size: 14px;
      line-height: 1.2;
    }
    .filter-chip__meta {
      display: block;
      font-size: 12px;
      color: inherit;
      opacity: 0.82;
    }
    .nav-summary {
      list-style: none;
      cursor: pointer;
      font-weight: 800;
      color: var(--bg-deep);
    }
    .nav-summary::-webkit-details-marker { display: none; }
    .story-index {
      display: grid;
      gap: 10px;
      margin-top: 14px;
    }
    .story-index-link {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: baseline;
      padding: 14px 16px;
      border-radius: 16px;
      background: var(--surface-soft);
      border: 1px solid rgba(180, 196, 209, 0.5);
      color: var(--text);
      text-decoration: none;
      transition: transform 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
    }
    .story-index-link strong,
    .story-index-link span {
      display: block;
    }
    .story-index-link span {
      color: var(--muted);
      font-size: 13px;
      text-align: right;
    }
    .story-index-link:hover {
      transform: translateY(-1px);
      border-color: rgba(11, 75, 127, 0.34);
      box-shadow: 0 12px 28px rgba(5, 37, 62, 0.08);
    }
    .story-summary-row,
    .story-head {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      flex-wrap: wrap;
      list-style: none;
      cursor: pointer;
      padding: 22px;
      border-bottom: 1px solid rgba(180, 196, 209, 0.55);
    }
    .story-summary-row::-webkit-details-marker,
    .story-head::-webkit-details-marker { display: none; }
    .story-heading,
    .story-main {
      display: flex;
      gap: 12px;
      flex: 1 1 560px;
    }
    .story-toggle,
    .story-arrow {
      width: 28px;
      height: 28px;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      margin-top: 3px;
      background: rgba(11, 75, 127, 0.1);
      color: var(--brand);
      transition: transform 120ms ease;
      flex: 0 0 auto;
    }
    .story-toggle::before,
    .story-arrow::before { content: "\\25b8"; }
    details[open] > summary .story-toggle,
    details[open] > summary .story-arrow { transform: rotate(90deg); }
    .story-heading h2 {
      font-size: 24px;
      line-height: 1.14;
      color: var(--bg-deep);
    }
    .story-stats {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    .story-stats div {
      min-width: 100px;
      padding: 12px 14px;
      border-radius: 16px;
      background: #f1f6fa;
      border: 1px solid rgba(180, 196, 209, 0.72);
      text-align: right;
    }
    .story-stats strong {
      display: block;
      font-size: 22px;
      line-height: 1;
      color: var(--brand-strong);
    }
    .story-stats span {
      display: block;
      margin-top: 6px;
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .story-meta,
    .meta-line {
      display: flex;
      gap: 8px 14px;
      flex-wrap: wrap;
      padding: 0 22px;
      margin-top: 16px;
      color: var(--muted);
      font-size: 13px;
    }
    .story-blurb,
    .story-summary {
      padding: 18px 22px 0;
    }
    .summary-label {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 4px 10px;
      border-radius: 999px;
      margin-bottom: 10px;
      background: rgba(11, 75, 127, 0.1);
      color: var(--brand);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .story-blurb p,
    .story-summary p {
      margin: 0;
      color: var(--text);
    }
    .story-articles {
      display: grid;
      gap: 14px;
      padding: 18px 22px 22px;
    }
    .article-card {
      border: 1px solid rgba(180, 196, 209, 0.72);
      border-radius: 22px;
      background: var(--surface);
      padding: 18px;
      box-shadow: 0 10px 26px rgba(5, 37, 62, 0.05);
    }
    .article-top {
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: flex-start;
      flex-wrap: wrap;
    }
    .article-card h3 {
      font-size: 22px;
      line-height: 1.12;
      color: var(--bg-deep);
    }
    .article-card h3 a {
      color: var(--bg-deep);
      text-decoration: none;
    }
    .article-card h3 a:hover {
      color: var(--link);
    }
    .article-meta {
      display: flex;
      gap: 8px 12px;
      flex-wrap: wrap;
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 13px;
    }
    .chips {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 4px 10px;
      border-radius: 999px;
      background: var(--chip-bg);
      color: var(--chip-ink);
      border: 1px solid rgba(11, 75, 127, 0.08);
      font-size: 12px;
      font-weight: 700;
    }
    .article-links,
    .link-row {
      display: flex;
      gap: 8px 14px;
      flex-wrap: wrap;
      margin: 14px 0 0;
    }
    .text-link,
    .link {
      color: var(--link);
      font-weight: 700;
      text-decoration: none;
    }
    .text-link:hover,
    .link:hover {
      text-decoration: underline;
    }
    .summary-box {
      margin-top: 16px;
      padding: 16px;
      border-radius: 18px;
    }
    .summary-ai {
      background: var(--ai-bg);
      color: var(--ai-ink);
    }
    .summary-raw {
      background: var(--raw-bg);
      color: var(--raw-ink);
    }
    .body-text,
    .body {
      color: inherit;
      font-size: 15px;
      word-break: break-word;
    }
    .body.full { margin-top: 12px; white-space: pre-wrap; }
    .raw-details {
      margin-top: 14px;
      border-top: 1px solid rgba(5, 37, 62, 0.08);
      padding-top: 14px;
    }
    .raw-details summary {
      cursor: pointer;
      font-weight: 700;
      color: var(--link);
    }
    .raw-details[open] summary {
      margin-bottom: 10px;
    }
    .empty-state {
      margin: 12px 0 0;
      color: var(--muted);
      font-size: 14px;
    }
    .footer-note {
      margin-top: 18px;
      color: rgba(5, 37, 62, 0.72);
      font-size: 13px;
      text-align: center;
    }
    .flat-articles {
      display: grid;
      gap: 14px;
      margin-top: 18px;
    }
    .flat-articles .article-card {
      background: var(--surface);
    }
    .load-more-btn {
      display: flex; align-items: center; justify-content: center; gap: 8px;
      width: 100%; padding: 16px; margin-top: 12px;
      border: 2px dashed var(--line); border-radius: 14px;
      background: var(--surface-soft); color: var(--brand);
      font-weight: 700; font-size: 15px; cursor: pointer;
      transition: background 120ms, border-color 120ms;
    }
    .load-more-btn:hover { background: var(--chip-bg); border-color: var(--brand); }
    .load-more-btn:disabled { cursor: wait; opacity: 0.7; }
    .flat-loading {
      display: flex; align-items: center; justify-content: center; gap: 10px;
      padding: 32px 16px; color: var(--muted); font-size: 15px;
    }
    .flat-spinner {
      width: 20px; height: 20px;
      border: 3px solid var(--line); border-top-color: var(--brand);
      border-radius: 50%; animation: spin 0.7s linear infinite; flex-shrink: 0;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    [hidden] {
      display: none !important;
    }
    @media (max-width: 720px) {
      main {
        width: min(100% - 16px, 100%);
        padding-top: 10px;
      }
      .hero,
      .panel {
        border-radius: 22px;
        padding-left: 18px;
        padding-right: 18px;
      }
      .hero h1 {
        font-size: 34px;
      }
      .stats {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .stat {
        min-height: 112px;
      }
      .story-card {
        padding-left: 0;
        padding-right: 0;
      }
      .story-summary-row,
      .story-head,
      .story-meta,
      .story-blurb,
      .story-summary,
      .story-articles {
        padding-left: 16px;
        padding-right: 16px;
      }
      .story-stats div {
        min-width: 92px;
      }
      .article-links,
      .link-row {
        flex-direction: column;
        align-items: flex-start;
      }
      .story-index-link {
        flex-direction: column;
        align-items: flex-start;
      }
      .story-index-link span {
        text-align: left;
      }
    }
    """

    html_doc = re.sub(
        r"<title>.*?</title>",
        "<title>Clipping Completo | Flavio Valle</title>",
        html_doc,
        count=1,
        flags=re.DOTALL,
    )
    html_doc = re.sub(
        r"<style>.*?</style>",
        lambda _match: f"<style>\n{stylesheet}\n  </style>",
        html_doc,
        count=1,
        flags=re.DOTALL,
    )
    html_doc = re.sub(
        r'<header class="hero">\s*<p class="eyebrow">.*?</p>\s*<h1>.*?</h1>\s*<p>.*?</p>\s*<div class="stats">',
        lambda _match: (
            '<header class="hero">\n'
            '      <div class="hero-lockup">\n'
            '        <p class="eyebrow">Mandato Flavio Valle</p>\n'
            f'        <h1>{html.escape(hero_title)}</h1>\n'
            f'        <p>{html.escape(hero_text)}</p>\n'
            '        <div class="hero-tags">\n'
            f'          <span class="hero-tag hero-tag--gold">{html.escape(scope_tag)}</span>\n'
            '          <span class="hero-tag">Painel offline</span>\n'
            '          <span class="hero-tag">Uso interno do gabinete</span>\n'
            '        </div>\n'
            '      </div>\n'
            '      <div class="stats">'
        ),
        html_doc,
        count=1,
        flags=re.DOTALL,
    )
    html_doc = html_doc.replace("Escopo do arquivo", "Escopo")
    html_doc = html_doc.replace("Sem chamadas para /api depois da geracao.", "Arquivo institucional offline, sem dependencia de API.")
    html_doc = html_doc.replace("Historias visiveis", "Historias visiveis")
    html_doc = html_doc.replace("Noticias visiveis", "Materias visiveis")
    html_doc = html_doc.replace("Somente noticias agrupadas em historias.", "Materias agrupadas nas historias visiveis.")
    html_doc = html_doc.replace("Com resumo IA", "Resumo IA")
    html_doc = html_doc.replace("Mostra Resumo IA quando existir.", "Exibe o resumo IA quando estiver disponivel.")
    html_doc = html_doc.replace("Mostra texto bruto quando nao houver IA.", "Exibe o texto bruto quando nao houver resumo IA.")
    html_doc = html_doc.replace("Banco consultado:", "Base consultada:")
    html_doc = html_doc.replace(
        "Controles de coleta removidos: este arquivo nao dispara novas execucoes.",
        "Uso interno do gabinete: este arquivo nao dispara novas coletas.",
    )
    html_doc = html_doc.replace("Filtro offline", "Monitoramento institucional")
    html_doc = html_doc.replace("Pessoas monitoradas", "Nomes acompanhados")
    html_doc = html_doc.replace("Abre filtrado em", "O arquivo abre com foco em")
    html_doc = html_doc.replace(
        "Toque para adicionar ou remover pessoas do filtro.",
        "Toque para incluir ou remover nomes do acompanhamento.",
    )
    html_doc = html_doc.replace("Filtro ativo:", "Monitoramento ativo:")
    html_doc = html_doc.replace(">Mais recente<", ">Mais recentes<")
    html_doc = html_doc.replace(">Noticias agrupadas<", ">Historias agrupadas<")
    html_doc = html_doc.replace(
        "Este snapshot foi gerado para compartilhamento em celular. As materias originais seguem com links externos; o restante funciona offline em um unico arquivo HTML.",
        "Arquivo institucional offline para compartilhamento interno do gabinete. Os links externos das materias originais permanecem disponiveis, e o restante funciona localmente em um unico HTML.",
    )
    return html_doc


def main() -> int:
    args = parse_args()
    try:
        artifact = build_snapshot_artifact(args)
    except FileNotFoundError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    output_path = Path(artifact["output_path"])
    written_outputs: list[Path] = []

    if args.all_stories:
        root_asset_paths = {
            "css": PAGES_ASSETS_DIR / "clipping.css",
            "js": PAGES_ASSETS_DIR / "clipping.js",
            "data": PAGES_ASSETS_DIR / "clipping-data.json",
            "raw": PAGES_ASSETS_DIR / "clipping-raw-texts.json",
        }
        write_bundle_assets(artifact, root_asset_paths)
        write_shell_html(PAGES_INDEX_PATH, artifact["data_payload"], root_asset_paths)
        written_outputs.append(PAGES_INDEX_PATH)

        aux_outputs = [
            REPORTS_DIR / "clipping_mobile_snapshot_all_stories.html",
            LEGACY_FULL_REPORT_PATH,
            INSTITUTIONAL_FULL_REPORT_PATH,
        ]
        if output_path != PAGES_INDEX_PATH and output_path not in aux_outputs:
            aux_outputs.insert(0, output_path)
        for extra_path in aux_outputs:
            write_shell_html(extra_path, artifact["data_payload"], root_asset_paths)
            written_outputs.append(extra_path)
    else:
        asset_paths = artifact["asset_paths"]
        write_bundle_assets(artifact, asset_paths)
        write_shell_html(output_path, artifact["data_payload"], asset_paths)
        written_outputs.append(output_path)

    for path in written_outputs:
        print(path)

    meta = artifact["data_payload"]["meta"]
    print(
        "stories=%s visible_initial=%s grouped_articles=%s targets=%s"
        % (
            int(meta.get("totalStories") or 0),
            int(meta.get("initialStoryCount") or 0),
            int(meta.get("totalArticles") or 0),
            len(artifact["target_rows"]),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
