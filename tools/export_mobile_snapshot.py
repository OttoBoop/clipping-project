from __future__ import annotations

import argparse
import html
import json
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Exporta um snapshot HTML estatico do clipping para compartilhamento mobile."
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
        full_toggle = """
        <details class="raw-details">
          <summary>Ver texto bruto completo</summary>
          <div class="body-text full">__FULL_TEXT__</div>
        </details>
        """.replace("__FULL_TEXT__", full_html)

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
        return REPORTS_DIR / "clipping_mobile_snapshot_all_stories.html"
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

    # Render new story cards + append old merged cards
    story_sections = "".join(
        render_story_section(
            story,
            article_map=article_map,
            label_by_key=label_by_key,
            visible_story_ids=initial_visible_story_ids,
        )
        for story in stories
    )
    for sid, card_str in merged_cards.items():
        story_sections += card_str + "\n"

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
        const m = (text || "").match(/(\d{2})\/(\d{2})\/(\d{4})\s+(\d{2}):(\d{2})/);
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

      function applyFilters() {
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
        if (currentSort === "newest") {
          buildFlatView();
        }
      }

      // --- Sort logic ---
      let currentSort = "newest";

      function buildFlatView() {
        flatStack.innerHTML = "";
        const visible = articleIndex.filter((a) => storyVisible(a.targets));
        visible.sort((a, b) => {
          // Primary: date descending
          const cmp = (b.pubIso || "").localeCompare(a.pubIso || "");
          if (cmp !== 0) return cmp;
          // Secondary: title ascending
          return a.title.localeCompare(b.title);
        });
        visible.forEach((entry) => {
          flatStack.appendChild(entry.el.cloneNode(true));
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

      applySort();
      applyFilters();
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


def main() -> int:
    args = parse_args()
    output_path = output_path_for_args(args)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    db = ClippingDB(DB_PATH)
    base_targets = load_targets()
    detailed_articles = load_scope_articles(db, args)
    article_map = {int(row["article_id"]): row for row in detailed_articles}
    stories = decorate_stories(db.story_with_articles(), article_map)

    # --- Merge from existing HTML if requested ---
    merged_card_html: dict[int, str] | None = None
    merged_payload_extra: dict[str, Any] | None = None

    if args.merge_from:
        source_path = Path(args.merge_from).expanduser()
        if not source_path.is_file():
            print(f"ERRO: arquivo --merge-from nao encontrado: {source_path}", file=sys.stderr)
            return 1
        old_payload, old_cards = parse_source_html(str(source_path))
        old_story_targets = old_payload.get("storyTargets", {})

        # Deduplicate: remove old cards whose IDs collide with new DB stories
        new_story_ids = {int(story.get("storyIdInt") or 0) for story in stories}
        deduped_cards: dict[int, str] = {}
        for sid, card_str in old_cards.items():
            if sid not in new_story_ids:
                deduped_cards[sid] = patch_old_card(card_str, old_story_targets)

        # Merge old targets into base_targets so filter buttons include them
        old_target_rows = old_payload.get("targets", [])
        existing_keys = {str(t.get("key", "")) for t in base_targets}
        for ot in old_target_rows:
            if str(ot.get("key", "")) not in existing_keys:
                base_targets.append({"key": ot["key"], "label": ot.get("label", ot["key"]), "primary": False})

        merged_card_html = deduped_cards
        merged_payload_extra = old_payload
        print(
            f"merge: source={source_path.name} old_stories={len(old_cards)} "
            f"deduped={len(old_cards) - len(deduped_cards)} kept={len(deduped_cards)}"
        )

    # Rebuild target_rows with combined story data
    all_stories_for_targets = list(stories)
    if merged_card_html and merged_payload_extra:
        old_st = merged_payload_extra.get("storyTargets", {})
        for sid, card_str in merged_card_html.items():
            ac_m = re.search(r'data-article-count="(\d+)"', card_str)
            target_keys = old_st.get(str(sid), [])
            all_stories_for_targets.append({
                "storyIdInt": sid,
                "targetKeys": target_keys,
                "articleCount": int(ac_m.group(1)) if ac_m else 0,
                "aiCount": 0,
                "rawCount": 0,
            })

    target_rows = build_target_rows(base_targets, all_stories_for_targets)
    initial_targets = resolve_initial_targets(target_rows, args.default_target)

    html_doc = build_html(
        args=args,
        stories=stories,
        target_rows=target_rows,
        initial_targets=initial_targets,
        article_map=article_map,
        merged_card_html=merged_card_html,
        merged_payload_extra=merged_payload_extra,
    )
    output_path.write_text(html_doc, encoding="utf-8")

    total_stories = len(stories) + (len(merged_card_html) if merged_card_html else 0)
    print(output_path)
    print(
        "stories=%s visible_initial=%s grouped_articles=%s targets=%s"
        % (
            total_stories,
            visibility_stats(stories, initial_targets)["storyCount"] + (
                sum(1 for sid in (merged_card_html or {}) if sid in set(
                    int(s) for s in (merged_payload_extra or {}).get("storyTargets", {})
                    if any(k in set(initial_targets) for k in (merged_payload_extra or {}).get("storyTargets", {}).get(s, []))
                )) if merged_card_html else 0
            ),
            sum(int(story.get("articleCount") or 0) for story in stories),
            len(target_rows),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())