#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = (
    ROOT
    / "data"
    / "parallel_runs"
    / "flavio_valle_plus_pedro_duarte_2026-04-03_2026-04-07_20260407T172006Z"
    / "clipping.db"
)
DEFAULT_OUTPUT_PATH = (
    ROOT
    / "data"
    / "reports"
    / "clipping_antissemitismo_flavio_pedro_2026-04-03_2026-04-07.html"
)

CLUSTER_ORDER = [
    "panorama",
    "partisan_reacao",
    "pedro_reacao",
    "mprj",
    "delly_gil",
    "porco_gordo",
    "xenofobia_3",
]

CLUSTERS = {
    "panorama": {
        "title": "Panorama Inicial Dos Casos",
        "summary": "Matérias que apresentam o quadro geral do Pessach no Rio: Delly Gil no Leblon, Partisan na Lapa e a primeira rodada de repercussões.",
    },
    "partisan_reacao": {
        "title": "Partisan: Multa E Reação Imediata",
        "summary": "Cobertura da autuação do Procon, da leitura pública do caso como discriminação e da resposta política imediata ao cartaz do bar da Lapa.",
    },
    "pedro_reacao": {
        "title": "Pedro Duarte: Notícia-Crime E B.O.",
        "summary": "Peças centradas nas providências de Pedro Duarte: ofícios, notícia-crime, boletim de ocorrência e pedidos ao Ministério Público.",
    },
    "mprj": {
        "title": "MPRJ E Enquadramento Criminal",
        "summary": "Matérias em que o Ministério Público passa a tratar os episódios como caso criminal e a atuação institucional ganha peso.",
    },
    "delly_gil": {
        "title": "Delly Gil E A Reação No Leblon",
        "summary": "Desdobramentos do caso da delicatessen no Leblon, já sob a narrativa de esclarecimento ou contestação da denúncia inicial.",
    },
    "porco_gordo": {
        "title": "Porco Gordo E A Terceira Ocorrência",
        "summary": "Cobertura da ampliação do ciclo com o terceiro caso e a leitura de que a semana gerou uma sequência de episódios de antissemitismo/xenofobia.",
    },
    "xenofobia_3": {
        "title": "Três Denúncias Em Dois Dias",
        "summary": "Fechamento do ciclo com matérias que consolidam três denúncias de xenofobia contra israelenses em dois dias no Rio.",
    },
}

DEDUPED_DUPLICATE_IDS = {6}
EXCLUDED_IRRELEVANT_IDS = {
    4,
    10,
    18,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    45,
    46,
}

MANUAL_REVIEW: dict[int, dict[str, str]] = {
    1: {
        "cluster": "panorama",
        "bucket": "both",
        "flavio_tone": "positive",
        "summary": "VEJA RIO consolida os estabelecimentos denunciados e apresenta as duas frentes políticas: Flávio Valle na Decradi/ordem pública e Pedro Duarte na notícia-crime.",
    },
    2: {
        "cluster": "partisan_reacao",
        "bucket": "both",
        "flavio_tone": "positive",
        "summary": "O Globo relata a multa do Procon ao Partisan e atribui o caso à denúncia de Pedro Duarte, enquanto também registra a pressão de Flávio Valle por medidas mais duras.",
    },
    3: {
        "cluster": "panorama",
        "bucket": "both",
        "flavio_tone": "positive",
        "summary": "Agenda do Poder reúne os dois primeiros episódios do Pessach, no Leblon e na Lapa, e cita tanto a reação de Pedro Duarte quanto a atuação institucional de Flávio Valle.",
    },
    5: {
        "cluster": "mprj",
        "bucket": "both",
        "flavio_tone": "positive",
        "summary": "CBN informa que o MPRJ passou a tratar os dois casos como crime; Pedro aparece via boletim de ocorrência e Flávio como presidente da frente que formalizaria a queixa.",
    },
    7: {
        "cluster": "partisan_reacao",
        "bucket": "flavio_only",
        "flavio_tone": "positive",
        "summary": "Portal Tela resume a multa do Procon e destaca Flávio Valle como a autoridade política que pediu a cassação do alvará do bar.",
    },
    8: {
        "cluster": "mprj",
        "bucket": "both",
        "flavio_tone": "positive",
        "summary": "Tribuna da Serra reproduz o enquadramento criminal do MPRJ e mantém os dois vereadores em cena: Pedro pelo B.O. e Flávio pela queixa e liderança da frente.",
    },
    9: {
        "cluster": "porco_gordo",
        "bucket": "both",
        "flavio_tone": "positive",
        "summary": "VEJA RIO amplia o foco para o Porco Gordo e mostra Valle e Pedro articulando uma apresentação conjunta de três casos às autoridades.",
    },
    11: {
        "cluster": "partisan_reacao",
        "bucket": "flavio_only",
        "flavio_tone": "neutral",
        "summary": "Poder360 trata a autuação do Partisan de forma breve e só registra Flávio Valle como autor do pedido de cassação do alvará, sem aprofundar sua atuação.",
    },
    12: {
        "cluster": "porco_gordo",
        "bucket": "both",
        "flavio_tone": "neutral",
        "summary": "Pleno.News perfila o dono do Partisan e menciona que as denúncias de Pedro Duarte e Flávio Valle antecederam a multa do Procon, mas sem desenvolver a atuação de nenhum dos dois.",
    },
    13: {
        "cluster": "partisan_reacao",
        "bucket": "both",
        "flavio_tone": "positive",
        "summary": "Agenda do Poder relata a autuação do bar e credita o disparo inicial a Pedro Duarte, registrando em paralelo a ofensiva de Flávio Valle pela cassação do alvará.",
    },
    14: {
        "cluster": "mprj",
        "bucket": "both",
        "flavio_tone": "positive",
        "summary": "Diário do Rio enquadra os episódios como caso criminal e mantém o papel dos dois: Pedro com o B.O. e Flávio com a queixa na frente anti-antissemitismo.",
    },
    15: {
        "cluster": "panorama",
        "bucket": "both",
        "flavio_tone": "positive",
        "summary": "O Globo faz o panorama dos dois casos do Pessach e coloca Pedro na linha do acionamento ao consumidor e Flávio na linha de pressão por cassação do alvará.",
    },
    16: {
        "cluster": "pedro_reacao",
        "bucket": "pedro_only",
        "summary": "Diário do Rio foca exclusivamente na notícia-crime protocolada por Pedro Duarte contra o Partisan e na argumentação jurídica apresentada por ele ao MPRJ.",
    },
    17: {
        "cluster": "panorama",
        "bucket": "both",
        "flavio_tone": "neutral",
        "summary": "Diário do Estado recompõe os dois casos do Pessach e menciona Pedro e Flávio apenas como autoridades acionadas, sem carga editorial adicional sobre nenhum deles.",
    },
    19: {
        "cluster": "partisan_reacao",
        "bucket": "both",
        "flavio_tone": "positive",
        "summary": "O Antagonista registra a multa do bar e apresenta Pedro Duarte como denunciante e Flávio Valle como vereador que acompanhou a fiscalização e pediu revisão do alvará.",
    },
    20: {
        "cluster": "pedro_reacao",
        "bucket": "pedro_only",
        "summary": "RL em Foco resume a notícia-crime de Pedro Duarte e destaca que ele trata o aviso do Partisan como xenofobia e antissemitismo passíveis de inquérito.",
    },
    21: {
        "cluster": "partisan_reacao",
        "bucket": "both",
        "flavio_tone": "positive",
        "summary": "Repórter Maceió reconta a multa do Partisan e conserva o mesmo desenho político: Pedro cobra resposta rápida e Flávio pede cassação do alvará.",
    },
    22: {
        "cluster": "pedro_reacao",
        "bucket": "pedro_only",
        "summary": "Diário do Centro do Mundo usa o caso do Partisan para criticar Pedro Duarte, mas a peça continua centrada somente nele e em sua iniciativa contra o bar.",
    },
    23: {
        "cluster": "porco_gordo",
        "bucket": "both",
        "flavio_tone": "positive",
        "summary": "Pleno.News apresenta o caso do Porco Gordo como a terceira ocorrência e informa que Flávio Valle e Pedro Duarte reuniriam os três episódios em uma frente única de denúncia.",
    },
    24: {
        "cluster": "panorama",
        "bucket": "both",
        "flavio_tone": "positive",
        "summary": "Repórter Maceió recompõe os dois episódios do Pessach e volta a registrar Pedro como denunciante inicial do Partisan e Flávio como articulador de cassação/queixa.",
    },
    34: {
        "cluster": "delly_gil",
        "bucket": "pedro_only",
        "summary": "Diário do Rio traz a versão defensiva da Delly Gil e menciona apenas Pedro Duarte como agente público acionado no pano de fundo da controvérsia.",
    },
    35: {
        "cluster": "partisan_reacao",
        "bucket": "pedro_only",
        "summary": "Diário do Rio cobre a primeira denúncia pública contra o Partisan e concentra toda a resposta institucional em Pedro Duarte e seu acionamento ao consumidor.",
    },
    36: {
        "cluster": "pedro_reacao",
        "bucket": "pedro_only",
        "summary": "Tempo Real RJ foca no boletim de ocorrência registrado por Pedro Duarte e no uso desse documento para reforçar a notícia-crime contra o bar.",
    },
    37: {
        "cluster": "pedro_reacao",
        "bucket": "pedro_only",
        "summary": "Tempo Real RJ cobre a notícia-crime de Pedro Duarte e destaca sua leitura de que o aviso do Partisan configura discriminação e crime.",
    },
    38: {
        "cluster": "partisan_reacao",
        "bucket": "pedro_only",
        "summary": "Tempo Real RJ registra o primeiro movimento de Pedro Duarte para pedir fiscalização do bar após o cartaz contra americanos e israelenses.",
    },
    39: {
        "cluster": "pedro_reacao",
        "bucket": "pedro_only",
        "summary": "Agenda do Poder noticia a atuação da Frente Parlamentar, mas o texto é encabeçado por Pedro Duarte e pelo pedido formal que ele apresenta ao MPRJ.",
    },
    40: {
        "cluster": "partisan_reacao",
        "bucket": "pedro_only",
        "summary": "Agenda do Poder acompanha o efeito rebote do caso Partisan e associa a fiscalização que abriu o episódio à denúncia original de Pedro Duarte.",
    },
    41: {
        "cluster": "delly_gil",
        "bucket": "pedro_only",
        "summary": "Tribuna da Serra repercute a defesa da Delly Gil e mantém apenas Pedro Duarte como autoridade citada no histórico recente do caso.",
    },
    42: {
        "cluster": "pedro_reacao",
        "bucket": "pedro_only",
        "summary": "Tribuna da Serra repete o eixo da notícia-crime e traz Pedro Duarte como único personagem político explicitamente citado na ofensiva contra o Partisan.",
    },
    43: {
        "cluster": "partisan_reacao",
        "bucket": "pedro_only",
        "summary": "Tribuna da Serra noticia a denúncia inicial contra o bar e ancora todo o enquadramento institucional em Pedro Duarte.",
    },
    44: {
        "cluster": "xenofobia_3",
        "bucket": "pedro_only",
        "summary": "O Globo amplia o ciclo para três denúncias de xenofobia contra israelenses em dois dias e, no trecho político do caso Partisan, cita apenas Pedro Duarte.",
    },
    47: {
        "cluster": "panorama",
        "bucket": "both",
        "flavio_tone": "positive",
        "summary": "Extra em link canônico reconta os dois casos iniciais do Pessach, preservando a dupla dinâmica: Pedro na denúncia ao consumidor e Flávio na cobrança por cassação.",
    },
    48: {
        "cluster": "xenofobia_3",
        "bucket": "pedro_only",
        "summary": "Extra fecha o ciclo com o consolidado de três denúncias e volta a usar apenas Pedro Duarte como referência política diretamente nomeada no caso Partisan.",
    },
}


def canonicalize_url(url: str) -> str:
    value = str(url or "").strip()
    if not value:
        return value
    value = value.replace("/google/amp/", "/")
    value = re.sub(r"\?amp=1$", "", value)
    value = re.sub(r"/amp/?$", "", value)
    return value


def parse_dt(raw: str) -> datetime | None:
    value = str(raw or "").strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def fmt_dt(raw: str) -> str:
    dt = parse_dt(raw)
    if not dt:
        return "Data não informada"
    return dt.astimezone(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")


def bucket_label(bucket: str) -> str:
    return {
        "both": "Misto",
        "flavio_only": "Só Flávio",
        "pedro_only": "Só Pedro",
    }.get(bucket, bucket)


def tone_label(tone: str) -> str:
    return {
        "positive": "Positivo para Flávio",
        "neutral": "Neutro para Flávio",
        "negative": "Negativo para Flávio",
        "mixed": "Misto/Incerto para Flávio",
    }.get(tone, "")


def load_articles(db_path: Path, article_ids: list[int]) -> dict[int, dict]:
    placeholders = ", ".join("?" for _ in article_ids)
    sql = f"""
        SELECT
            id,
            title,
            url,
            source_name,
            source_type,
            COALESCE(published_at, discovered_at) AS published_at,
            summary,
            full_text
        FROM articles
        WHERE id IN ({placeholders})
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, tuple(article_ids)).fetchall()
        return {int(row["id"]): dict(row) for row in rows}


def count_total_saved_articles(db_path: Path) -> int:
    with sqlite3.connect(db_path) as conn:
        return int(conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0])


def build_records(db_path: Path) -> list[dict]:
    article_ids = list(MANUAL_REVIEW)
    rows = load_articles(db_path, article_ids)
    records: list[dict] = []
    for article_id, review in MANUAL_REVIEW.items():
        row = rows.get(article_id)
        if not row:
            raise RuntimeError(f"manual review references missing article id: {article_id}")
        bucket = review["bucket"]
        mention_flavio = bucket in {"both", "flavio_only"}
        mention_pedro = bucket in {"both", "pedro_only"}
        records.append(
            {
                "article_id": article_id,
                "title": str(row["title"] or "").strip(),
                "url": canonicalize_url(str(row["url"] or "").strip()),
                "original_url": str(row["url"] or "").strip(),
                "source_name": str(row["source_name"] or "").strip(),
                "source_type": str(row["source_type"] or "").strip(),
                "published_at": str(row["published_at"] or "").strip(),
                "cluster": review["cluster"],
                "cluster_title": CLUSTERS[review["cluster"]]["title"],
                "bucket": bucket,
                "bucket_label": bucket_label(bucket),
                "mention_flavio": mention_flavio,
                "mention_pedro": mention_pedro,
                "flavio_tone": review.get("flavio_tone", ""),
                "flavio_tone_label": tone_label(review.get("flavio_tone", "")),
                "review_summary": review["summary"],
            }
        )
    records.sort(
        key=lambda item: (
            CLUSTER_ORDER.index(item["cluster"]),
            parse_dt(item["published_at"]) or datetime.min.replace(tzinfo=timezone.utc),
            item["article_id"],
        )
    )
    return records


def build_stats(records: list[dict], total_saved_articles: int) -> dict:
    total_included = len(records)
    mixed = sum(1 for item in records if item["bucket"] == "both")
    flavio_only = sum(1 for item in records if item["bucket"] == "flavio_only")
    pedro_only = sum(1 for item in records if item["bucket"] == "pedro_only")
    flavio_cited = sum(1 for item in records if item["mention_flavio"])
    pedro_cited = sum(1 for item in records if item["mention_pedro"])
    tone_counts = Counter(
        item["flavio_tone"] for item in records if item["mention_flavio"] and item["flavio_tone"]
    )
    cluster_counts = Counter(item["cluster"] for item in records)
    source_counts = Counter(item["source_name"] for item in records)
    return {
        "total_saved_articles": total_saved_articles,
        "deduped_amp_rows": len(DEDUPED_DUPLICATE_IDS),
        "excluded_irrelevant_rows": len(EXCLUDED_IRRELEVANT_IDS),
        "included_articles": total_included,
        "mixed_articles": mixed,
        "flavio_only_articles": flavio_only,
        "pedro_only_articles": pedro_only,
        "flavio_cited_articles": flavio_cited,
        "pedro_cited_articles": pedro_cited,
        "lead_gap": pedro_cited - flavio_cited,
        "tone_counts": tone_counts,
        "cluster_counts": cluster_counts,
        "source_counts": source_counts,
    }


def render_filters() -> str:
    coverage = [
        ("all", "Todos"),
        ("flavio_cited", "Flávio citado"),
        ("pedro_cited", "Pedro citado"),
        ("both", "Misto"),
        ("flavio_only", "Só Flávio"),
        ("pedro_only", "Só Pedro"),
    ]
    tone = [
        ("all", "Todos os tons"),
        ("positive", "Flávio positivo"),
        ("neutral", "Flávio neutro"),
        ("negative", "Flávio negativo"),
        ("mixed", "Flávio misto/incerto"),
    ]
    coverage_html = "".join(
        f'<button type="button" class="filter-chip{" active" if key == "all" else ""}" '
        f'data-filter-kind="coverage" data-filter-value="{key}">{label}</button>'
        for key, label in coverage
    )
    tone_html = "".join(
        f'<button type="button" class="filter-chip{" active" if key == "all" else ""}" '
        f'data-filter-kind="tone" data-filter-value="{key}">{label}</button>'
        for key, label in tone
    )
    return coverage_html, tone_html


def render_article_card(item: dict) -> str:
    badges = [
        f'<span class="chip chip-bucket">{html.escape(item["bucket_label"])}</span>',
    ]
    if item["flavio_tone_label"]:
        tone_class = f' chip-tone-{html.escape(item["flavio_tone"])}'
        badges.append(
            f'<span class="chip chip-tone{tone_class}">{html.escape(item["flavio_tone_label"])}</span>'
        )

    return f"""
    <article class="article-card"
      data-article-id="{item['article_id']}"
      data-bucket="{html.escape(item['bucket'])}"
      data-flavio="{1 if item['mention_flavio'] else 0}"
      data-pedro="{1 if item['mention_pedro'] else 0}"
      data-flavio-tone="{html.escape(item['flavio_tone'])}">
      <div class="article-top">
        <div>
          <h3><a href="{html.escape(item['url'])}" target="_blank" rel="noreferrer">{html.escape(item['title'])}</a></h3>
          <p class="article-meta">
            <span>{html.escape(item['source_name'])}</span>
            <span>{html.escape(fmt_dt(item['published_at']))}</span>
          </p>
        </div>
        <div class="chips">{"".join(badges)}</div>
      </div>
      <div class="summary-box">
        <div class="summary-label">Leitura editorial</div>
        <p>{html.escape(item['review_summary'])}</p>
      </div>
    </article>
    """


def render_cluster_section(cluster_key: str, items: list[dict]) -> str:
    meta = CLUSTERS[cluster_key]
    both = sum(1 for item in items if item["bucket"] == "both")
    flavio_only = sum(1 for item in items if item["bucket"] == "flavio_only")
    pedro_only = sum(1 for item in items if item["bucket"] == "pedro_only")
    articles_html = "".join(render_article_card(item) for item in items)
    return f"""
    <details class="panel cluster-card" id="cluster-{html.escape(cluster_key)}" data-cluster="{html.escape(cluster_key)}" open>
      <summary class="cluster-summary">
        <div class="cluster-head">
          <span class="story-toggle" aria-hidden="true"></span>
          <div>
            <p class="eyebrow">Núcleo editorial</p>
            <h2>{html.escape(meta['title'])}</h2>
            <p class="cluster-note">{html.escape(meta['summary'])}</p>
          </div>
        </div>
        <div class="cluster-stats">
          <div><strong>{len(items)}</strong><span>artigos</span></div>
          <div><strong>{both}</strong><span>mistos</span></div>
          <div><strong>{flavio_only}</strong><span>só Flávio</span></div>
          <div><strong>{pedro_only}</strong><span>só Pedro</span></div>
        </div>
      </summary>
      <div class="cluster-articles">
        {articles_html}
      </div>
    </details>
    """


def render_cluster_index(records: list[dict]) -> str:
    links: list[str] = []
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in records:
        grouped[item["cluster"]].append(item)
    for cluster_key in CLUSTER_ORDER:
        items = grouped.get(cluster_key, [])
        if not items:
            continue
        links.append(
            f'<a class="story-index-link" href="#cluster-{html.escape(cluster_key)}">'
            f'<strong>{html.escape(CLUSTERS[cluster_key]["title"])}</strong>'
            f'<span>{len(items)} artigo(s)</span></a>'
        )
    return "".join(links)


def build_html(records: list[dict], stats: dict, db_path: Path) -> str:
    coverage_filters, tone_filters = render_filters()
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in records:
        grouped[item["cluster"]].append(item)
    cluster_sections = "".join(
        render_cluster_section(cluster_key, grouped[cluster_key])
        for cluster_key in CLUSTER_ORDER
        if grouped.get(cluster_key)
    )
    cluster_index = render_cluster_index(records)
    generated_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    tone_counts = stats["tone_counts"]
    payload = {
        "includedArticles": stats["included_articles"],
        "flavioCited": stats["flavio_cited_articles"],
        "pedroCited": stats["pedro_cited_articles"],
        "mixedArticles": stats["mixed_articles"],
    }

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Antissemitismo | Flávio Valle vs Pedro Duarte</title>
  <style>
    :root {{
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
      --positive: #2a7a57;
      --positive-bg: #e8f4ed;
      --neutral: #6b7b8c;
      --neutral-bg: #edf2f7;
      --negative: #a83f3f;
      --negative-bg: #f8e9e9;
      --warning-bg: #fff6dc;
      --warning-ink: #6f5610;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at top left, rgba(246, 187, 27, 0.12), transparent 26%),
        radial-gradient(circle at top right, rgba(180, 196, 209, 0.24), transparent 28%),
        linear-gradient(180deg, var(--bg-deep) 0, var(--brand) 240px, var(--bg) 240px, var(--bg) 100%);
      color: var(--text);
      font-family: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      line-height: 1.6;
    }}
    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background:
        linear-gradient(160deg, rgba(255, 255, 255, 0.04), transparent 26%),
        radial-gradient(circle at 12% 12%, rgba(255, 255, 255, 0.08), transparent 16%);
      opacity: 0.9;
    }}
    a {{ color: inherit; }}
    main {{
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 48px;
      position: relative;
      z-index: 1;
    }}
    .hero, .panel {{
      border-radius: 28px;
      border: 1px solid rgba(180, 196, 209, 0.78);
      box-shadow: var(--shadow);
    }}
    .hero {{
      position: relative;
      overflow: hidden;
      padding: 30px;
      background:
        radial-gradient(circle at top right, rgba(246, 187, 27, 0.22), transparent 28%),
        linear-gradient(135deg, rgba(5, 37, 62, 0.98), rgba(11, 75, 127, 0.97));
      color: #ececec;
      box-shadow: var(--shadow-strong);
    }}
    .hero::after {{
      content: "";
      position: absolute;
      right: -70px;
      bottom: -90px;
      width: 260px;
      height: 260px;
      border-radius: 999px;
      background: radial-gradient(circle, rgba(246, 187, 27, 0.24), rgba(246, 187, 27, 0));
    }}
    .hero-lockup {{
      position: relative;
      z-index: 1;
      max-width: 820px;
    }}
    .hero-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 18px 0 0;
    }}
    .hero-tag {{
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
    }}
    .hero-tag--gold {{
      background: var(--gold);
      border-color: transparent;
      color: var(--bg-deep);
    }}
    .hero h1, .section-head h2, .cluster-head h2, .article-card h3 {{
      margin: 0;
      font-family: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      font-weight: 800;
      letter-spacing: -0.03em;
    }}
    .hero h1 {{
      font-size: clamp(32px, 5vw, 52px);
      line-height: 1.02;
      color: #ffffff;
    }}
    .hero p {{
      margin: 14px 0 0;
      max-width: 760px;
      color: rgba(236, 236, 236, 0.88);
      font-size: 16px;
    }}
    .meta-row {{
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
    }}
    .panel {{
      background: rgba(255, 255, 255, 0.98);
      margin-top: 18px;
      padding: 22px;
    }}
    .eyebrow {{
      margin: 0 0 10px;
      font-size: 12px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      font-weight: 800;
      color: var(--muted);
    }}
    .hero .eyebrow {{
      color: #b4c4d1;
    }}
    .stats {{
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 12px;
      margin-top: 24px;
    }}
    .stat {{
      min-height: 128px;
      padding: 16px;
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(180, 196, 209, 0.18);
      backdrop-filter: blur(8px);
    }}
    .stat span {{
      display: block;
      color: #b4c4d1;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }}
    .stat strong {{
      display: block;
      margin-top: 10px;
      font-size: clamp(26px, 4vw, 34px);
      line-height: 1.05;
      color: #ffffff;
    }}
    .stat small {{
      display: block;
      margin-top: 8px;
      color: rgba(236, 236, 236, 0.8);
      font-size: 12px;
    }}
    .section-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
      margin-bottom: 10px;
    }}
    .section-head h2 {{
      font-size: 24px;
      color: var(--bg-deep);
    }}
    .two-col {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 18px;
    }}
    .callout {{
      margin: 0;
      color: var(--muted);
      font-size: 14px;
    }}
    .insights {{
      display: grid;
      gap: 12px;
    }}
    .insight {{
      padding: 14px 16px;
      border-radius: 18px;
      background: var(--surface-soft);
      border: 1px solid var(--line);
    }}
    .insight strong {{
      display: block;
      margin-bottom: 6px;
      color: var(--bg-deep);
    }}
    .method-list {{
      display: grid;
      gap: 10px;
      margin-top: 14px;
    }}
    .method-item {{
      padding: 14px 16px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: var(--surface-soft);
    }}
    .method-item strong {{
      color: var(--bg-deep);
    }}
    .scoreboard {{
      display: grid;
      gap: 12px;
    }}
    .score-row {{
      display: grid;
      grid-template-columns: minmax(120px, 180px) 1fr auto;
      gap: 12px;
      align-items: center;
    }}
    .score-row span {{
      font-weight: 700;
      color: var(--bg-deep);
    }}
    .score-bar {{
      height: 16px;
      border-radius: 999px;
      overflow: hidden;
      background: #dfe7ef;
    }}
    .score-bar i {{
      display: block;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--gold), #ffd565);
    }}
    .score-bar--blue i {{
      background: linear-gradient(90deg, var(--brand), #4f88ba);
    }}
    .score-row strong {{
      font-size: 18px;
      color: var(--bg-deep);
    }}
    .filter-groups {{
      display: grid;
      gap: 14px;
    }}
    .filter-row {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .filter-chip {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 10px 14px;
      background: var(--surface-soft);
      color: var(--bg-deep);
      font-weight: 700;
      cursor: pointer;
      transition: transform 120ms ease, background 120ms ease, color 120ms ease;
    }}
    .filter-chip:hover {{
      transform: translateY(-1px);
    }}
    .filter-chip.active {{
      background: var(--brand);
      color: #fff;
      border-color: var(--brand);
    }}
    .active-filter {{
      margin: 0;
      color: var(--muted);
      font-size: 13px;
    }}
    .story-index {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      margin-top: 12px;
    }}
    .story-index-link {{
      display: block;
      padding: 14px 16px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: var(--surface-soft);
      color: inherit;
      text-decoration: none;
    }}
    .story-index-link strong {{
      display: block;
      color: var(--bg-deep);
    }}
    .story-index-link span {{
      display: block;
      margin-top: 6px;
      color: var(--muted);
      font-size: 12px;
    }}
    .cluster-card {{
      padding: 0;
      overflow: hidden;
      background: linear-gradient(180deg, #ffffff 0, #f9fbfd 100%);
    }}
    .cluster-summary {{
      list-style: none;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      padding: 22px;
      cursor: pointer;
    }}
    .cluster-summary::-webkit-details-marker {{
      display: none;
    }}
    .cluster-head {{
      display: flex;
      gap: 14px;
      align-items: flex-start;
      min-width: 0;
    }}
    .story-toggle {{
      width: 18px;
      height: 18px;
      margin-top: 8px;
      border-radius: 999px;
      border: 2px solid var(--brand);
      position: relative;
      flex: 0 0 auto;
    }}
    details[open] .story-toggle::after {{
      content: "";
      position: absolute;
      inset: 4px;
      border-radius: 999px;
      background: var(--gold);
    }}
    .cluster-head h2 {{
      font-size: 26px;
      color: var(--bg-deep);
    }}
    .cluster-note {{
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 14px;
      max-width: 720px;
    }}
    .cluster-stats {{
      display: grid;
      grid-template-columns: repeat(2, minmax(110px, 1fr));
      gap: 10px;
      min-width: 270px;
    }}
    .cluster-stats div {{
      padding: 12px 14px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: var(--surface-soft);
      text-align: center;
    }}
    .cluster-stats strong {{
      display: block;
      font-size: 22px;
      color: var(--bg-deep);
    }}
    .cluster-stats span {{
      display: block;
      margin-top: 4px;
      font-size: 12px;
      color: var(--muted);
    }}
    .cluster-articles {{
      padding: 0 22px 22px;
      display: grid;
      gap: 14px;
    }}
    .article-card {{
      padding: 18px;
      border-radius: 22px;
      border: 1px solid var(--line);
      background: #fffdfb;
      box-shadow: 0 10px 22px rgba(5, 37, 62, 0.05);
    }}
    .article-card[hidden] {{
      display: none !important;
    }}
    .article-top {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
    }}
    .article-card h3 {{
      font-size: 22px;
      line-height: 1.15;
    }}
    .article-card h3 a {{
      color: var(--bg-deep);
      text-decoration: none;
    }}
    .article-card h3 a:hover {{
      color: var(--link);
    }}
    .article-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px 12px;
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 13px;
    }}
    .chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
      max-width: 340px;
    }}
    .chip {{
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 0 12px;
      border-radius: 999px;
      background: var(--chip-bg);
      color: var(--chip-ink);
      font-size: 12px;
      font-weight: 700;
      text-align: center;
    }}
    .chip-bucket {{
      background: rgba(11, 75, 127, 0.11);
      color: var(--brand);
    }}
    .chip-canonical {{
      background: var(--warning-bg);
      color: var(--warning-ink);
    }}
    .chip-tone-positive {{
      background: var(--positive-bg);
      color: var(--positive);
    }}
    .chip-tone-neutral {{
      background: var(--neutral-bg);
      color: var(--neutral);
    }}
    .chip-tone-negative {{
      background: var(--negative-bg);
      color: var(--negative);
    }}
    .summary-box {{
      margin-top: 14px;
      padding: 14px 16px;
      border-radius: 18px;
      border: 1px solid rgba(180, 196, 209, 0.72);
      background: linear-gradient(180deg, #f7fbff 0, #f1f7fc 100%);
    }}
    .summary-label {{
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--muted);
    }}
    .summary-box p {{
      margin: 10px 0 0;
      color: var(--text);
      font-size: 15px;
    }}
    .footer-note {{
      margin-top: 18px;
      color: rgba(236, 236, 236, 0.84);
      font-size: 13px;
      text-align: center;
    }}
    [hidden] {{
      display: none !important;
    }}
    @media (max-width: 920px) {{
      .two-col {{
        grid-template-columns: 1fr;
      }}
      .cluster-summary {{
        flex-direction: column;
      }}
      .cluster-stats {{
        min-width: 0;
        width: 100%;
      }}
    }}
    @media (max-width: 720px) {{
      main {{
        width: min(100% - 16px, 100%);
      }}
      .article-top {{
        flex-direction: column;
      }}
      .chips {{
        justify-content: flex-start;
        max-width: none;
      }}
      .score-row {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <header class="hero">
      <div class="hero-lockup">
        <p class="eyebrow">Clipping comparativo | Antissemitismo</p>
        <h1>Flávio Valle vs Pedro Duarte nas matérias sobre antissemitismo</h1>
        <p>
          Recorte editorial feito a partir da execução do pipeline para <strong>Flávio Valle</strong> e <strong>Pedro Duarte</strong> entre
          <strong>03/04/2026</strong> e <strong>07/04/2026</strong>. O conjunto final abaixo não é bruto:
          eu li os textos das matérias salvas, removi ruído de homônimo, descartei o caso em que havia AMP e link canônico da mesma matéria e mantive apenas o ciclo realmente ligado aos casos de antissemitismo/xenofobia contra israelenses no Rio.
        </p>
        <div class="hero-tags">
          <span class="hero-tag hero-tag--gold">Análise interna</span>
          <span class="hero-tag">33 artigos incluídos</span>
          <span class="hero-tag">Misto conta para ambos</span>
          <span class="hero-tag">AMP/full deduplicado</span>
        </div>
        <div class="stats">
          <div class="stat"><span>Flávio citado</span><strong id="visibleFlavioStat">{stats['flavio_cited_articles']}</strong><small>Total revisado: {stats['flavio_cited_articles']}</small></div>
          <div class="stat"><span>Pedro citado</span><strong id="visiblePedroStat">{stats['pedro_cited_articles']}</strong><small>Total revisado: {stats['pedro_cited_articles']}</small></div>
          <div class="stat"><span>Artigos mistos</span><strong id="visibleMixedStat">{stats['mixed_articles']}</strong><small>Total revisado: {stats['mixed_articles']}</small></div>
          <div class="stat"><span>Artigos visíveis</span><strong id="visibleArticlesStat">{stats['included_articles']}</strong><small>Total revisado: {stats['included_articles']}</small></div>
        </div>
        <div class="meta-row">
          <span>Gerado em: {generated_at}</span>
          <span>Banco-base: {html.escape(db_path.name)}</span>
          <span>Linhas salvas no run: {stats['total_saved_articles']}</span>
          <span>Ruído excluído: {stats['excluded_irrelevant_rows']}</span>
        </div>
      </div>
    </header>

    <section class="panel">
      <div class="two-col">
        <div>
          <div class="section-head">
            <div>
              <p class="eyebrow">Leitura executiva</p>
              <h2>Placar editorial</h2>
            </div>
          </div>
          <div class="scoreboard">
            <div class="score-row">
              <span>Pedro Duarte</span>
              <div class="score-bar"><i style="width:{(stats['pedro_cited_articles'] / max(stats['pedro_cited_articles'], stats['flavio_cited_articles'])) * 100:.2f}%"></i></div>
              <strong>{stats['pedro_cited_articles']}</strong>
            </div>
            <div class="score-row">
              <span>Flávio Valle</span>
              <div class="score-bar score-bar--blue"><i style="width:{(stats['flavio_cited_articles'] / max(stats['pedro_cited_articles'], stats['flavio_cited_articles'])) * 100:.2f}%"></i></div>
              <strong>{stats['flavio_cited_articles']}</strong>
            </div>
          </div>
          <p class="callout" style="margin-top:14px;">
            No recorte revisado, <strong>Pedro Duarte aparece em {stats['pedro_cited_articles']} artigos</strong> e
            <strong>Flávio Valle em {stats['flavio_cited_articles']}</strong>. A diferença é de
            <strong>{stats['lead_gap']} artigos</strong>, puxada sobretudo pelos desdobramentos jurídicos e administrativos centrados em Pedro no caso Partisan.
          </p>
          <div class="method-list">
            <div class="method-item"><strong>{stats['mixed_articles']}</strong> artigos mistos contam para os dois lados no placar.</div>
            <div class="method-item"><strong>{stats['deduped_amp_rows']}</strong> duplicata AMP/full foi removida; permaneci com a URL canônica.</div>
            <div class="method-item"><strong>{stats['excluded_irrelevant_rows']}</strong> linhas salvas foram excluídas como ruído editorial ou homônimo de Pedro Duarte.</div>
            <div class="method-item"><strong>{tone_counts.get('positive', 0)}</strong> menções a Flávio foram lidas como positivas e <strong>{tone_counts.get('neutral', 0)}</strong> como neutras; não encontrei peça negativa no conjunto incluído.</div>
          </div>
        </div>
        <div>
          <div class="section-head">
            <div>
              <p class="eyebrow">Leitura analítica</p>
              <h2>Principais achados</h2>
            </div>
          </div>
          <div class="insights">
            <div class="insight">
              <strong>Pedro puxa o volume</strong>
              A dianteira de Pedro vem das matérias que transformam sua atuação em notícia principal: ofício ao consumidor, notícia-crime, boletim de ocorrência e pedidos ao MPRJ.
            </div>
            <div class="insight">
              <strong>Flávio aparece menos, mas em posição institucional forte</strong>
              Quando Flávio entra, quase sempre aparece como presidente da Frente Parlamentar de Combate ao Antissemitismo, associado a denúncia formal, cassação de alvará e articulação institucional.
            </div>
            <div class="insight">
              <strong>O ciclo tem sete núcleos editoriais claros</strong>
              O ruído de homônimo foi grande, mas as matérias realmente úteis se organizaram em poucos blocos: panorama, multa do Partisan, reação de Pedro, enquadramento do MPRJ, Delly Gil, Porco Gordo e o consolidado de três denúncias.
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="section-head">
        <div>
          <p class="eyebrow">Filtros</p>
          <h2>Explorar o conjunto revisado</h2>
        </div>
      </div>
      <div class="filter-groups">
        <div>
          <p class="callout">Cobertura</p>
          <div class="filter-row">{coverage_filters}</div>
        </div>
        <div>
          <p class="callout">Tom das menções a Flávio</p>
          <div class="filter-row">{tone_filters}</div>
        </div>
      </div>
      <p class="active-filter">Filtro ativo: <strong id="activeFilterText">Todos os artigos incluídos</strong></p>
    </section>

    <section class="panel">
      <div class="section-head">
        <div>
          <p class="eyebrow">Navegação</p>
          <h2>Núcleos editoriais</h2>
        </div>
      </div>
      <div class="story-index">{cluster_index}</div>
    </section>

    <section id="clusterStack">
      {cluster_sections}
    </section>

    <p class="footer-note">Relatório montado a partir da leitura manual dos textos salvos pelo run de 03/04/2026 a 07/04/2026 para Flávio Valle e Pedro Duarte.</p>
  </main>
  <script id="report-payload" type="application/json">{json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")}</script>
  <script>
    (function () {{
      const cards = Array.from(document.querySelectorAll(".article-card"));
      const clusters = Array.from(document.querySelectorAll(".cluster-card"));
      const buttons = Array.from(document.querySelectorAll("[data-filter-kind]"));
      const state = {{ coverage: "all", tone: "all" }};

      function coveragePass(card) {{
        const bucket = card.dataset.bucket || "";
        const flavio = card.dataset.flavio === "1";
        const pedro = card.dataset.pedro === "1";
        switch (state.coverage) {{
          case "flavio_cited": return flavio;
          case "pedro_cited": return pedro;
          case "both": return bucket === "both";
          case "flavio_only": return bucket === "flavio_only";
          case "pedro_only": return bucket === "pedro_only";
          default: return true;
        }}
      }}

      function tonePass(card) {{
        if (state.tone === "all") return true;
        return (card.dataset.flavioTone || "") === state.tone;
      }}

      function activeCoverageLabel() {{
        const map = {{
          all: "Todos os artigos incluídos",
          flavio_cited: "Somente artigos que citam Flávio Valle",
          pedro_cited: "Somente artigos que citam Pedro Duarte",
          both: "Somente artigos mistos",
          flavio_only: "Somente artigos só Flávio",
          pedro_only: "Somente artigos só Pedro"
        }};
        return map[state.coverage] || "Todos os artigos incluídos";
      }}

      function activeToneLabel() {{
        const map = {{
          all: "sem filtro de tom",
          positive: "tom positivo para Flávio",
          neutral: "tom neutro para Flávio",
          negative: "tom negativo para Flávio",
          mixed: "tom misto/incerto para Flávio"
        }};
        return map[state.tone] || "sem filtro de tom";
      }}

      function applyFilters() {{
        let visibleArticles = 0;
        let visibleFlavio = 0;
        let visiblePedro = 0;
        let visibleMixed = 0;

        cards.forEach((card) => {{
          const visible = coveragePass(card) && tonePass(card);
          card.hidden = !visible;
          if (!visible) return;
          visibleArticles += 1;
          if (card.dataset.flavio === "1") visibleFlavio += 1;
          if (card.dataset.pedro === "1") visiblePedro += 1;
          if ((card.dataset.bucket || "") === "both") visibleMixed += 1;
        }});

        clusters.forEach((cluster) => {{
          const clusterCards = Array.from(cluster.querySelectorAll(".article-card"));
          const anyVisible = clusterCards.some((card) => !card.hidden);
          cluster.hidden = !anyVisible;
        }});

        buttons.forEach((button) => {{
          button.classList.toggle("active", state[button.dataset.filterKind] === button.dataset.filterValue);
        }});

        document.getElementById("visibleArticlesStat").textContent = String(visibleArticles);
        document.getElementById("visibleFlavioStat").textContent = String(visibleFlavio);
        document.getElementById("visiblePedroStat").textContent = String(visiblePedro);
        document.getElementById("visibleMixedStat").textContent = String(visibleMixed);
        document.getElementById("activeFilterText").textContent =
          activeCoverageLabel() + " | " + activeToneLabel();
      }}

      buttons.forEach((button) => {{
        button.addEventListener("click", () => {{
          state[button.dataset.filterKind] = button.dataset.filterValue || "all";
          applyFilters();
        }});
      }});

      applyFilters();
    }})();
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an antisemitism comparison HTML for Flávio Valle vs Pedro Duarte."
    )
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db).expanduser()
    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = build_records(db_path)
    stats = build_stats(records, count_total_saved_articles(db_path))
    html_doc = build_html(records, stats, db_path)
    output_path.write_text(html_doc, encoding="utf-8")

    print(output_path)
    print(
        "included=%s flavio=%s pedro=%s mixed=%s deduped=%s excluded=%s"
        % (
            stats["included_articles"],
            stats["flavio_cited_articles"],
            stats["pedro_cited_articles"],
            stats["mixed_articles"],
            stats["deduped_amp_rows"],
            stats["excluded_irrelevant_rows"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
