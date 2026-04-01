from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

from .matcher import Target

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "clipping.db"
TARGETS_JSON_PATH = DATA_DIR / "targets.json"
BACKFILL_START_DATE = datetime(2025, 1, 1, tzinfo=timezone.utc)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)

DEFAULT_TARGETS: list[Target] = [
    Target(
        key="flavio_valle",
        display_name="Flavio Valle",
        priority=1,
        keywords=[
            "Flavio Valle",
            "vereador Flavio",
            "vereador Valle",
        ],
        exact_aliases=["Flavio Vale"],
    ),
    Target(
        key="pedro_angelito",
        display_name="Pedro Angelito",
        priority=2,
        keywords=[
            "Pedro Angelito",
            "subprefeito Pedro Angelito",
        ],
    ),
    Target(
        key="bernardo_rubiao",
        display_name="Bernardo Rubiao",
        priority=2,
        keywords=[
            "Bernardo Rubiao",
        ],
    ),
    Target(
        key="pedro_duarte",
        display_name="Pedro Duarte",
        priority=2,
        keywords=[
            "Pedro Duarte",
            "deputado Pedro Duarte",
        ],
    ),
]

TARGETS = DEFAULT_TARGETS

# Main media feeds for breadth-first coverage.
RSS_FEEDS: list[dict[str, str]] = [
    {"source_name": "VEJA", "url": "https://veja.abril.com.br/feed/"},
    {"source_name": "VEJA RSS", "url": "https://veja.abril.com.br/rss/"},
    {"source_name": "VEJA Politica", "url": "https://veja.abril.com.br/politica/feed/"},
    {"source_name": "VEJA Cidades", "url": "https://veja.abril.com.br/canal/cidades/feed/"},
    {"source_name": "Veja Rio", "url": "https://vejario.abril.com.br/feed/"},
    {"source_name": "G1", "url": "https://g1.globo.com/rss/g1/"},
    {"source_name": "G1 Politica", "url": "https://g1.globo.com/rss/g1/politica/"},
    {"source_name": "G1 Rio", "url": "https://g1.globo.com/rss/g1/rio-de-janeiro/"},
    {"source_name": "O Globo", "url": "https://oglobo.globo.com/rss.xml"},
    {"source_name": "Extra", "url": "https://extra.globo.com/rss.xml"},
    {"source_name": "Folha", "url": "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml"},
    {"source_name": "UOL", "url": "https://rss.uol.com.br/feed/noticias.xml"},
    {"source_name": "R7", "url": "https://noticias.r7.com/rss.xml"},
    {"source_name": "Band", "url": "https://www.band.uol.com.br/rss"},
    {"source_name": "Estadao", "url": "https://www.estadao.com.br/rss/ultimas.xml"},
    {"source_name": "Agencia Brasil", "url": "https://agenciabrasil.ebc.com.br/rss/geral/feed.xml"},
    {"source_name": "Diario do Rio", "url": "https://diariodorio.com/feed/"},
    {"source_name": "Tempo Real RJ", "url": "https://temporealrj.com/feed/"},
    {"source_name": "Agenda do Poder", "url": "https://agendadopoder.com.br/feed/"},
    {"source_name": "Conib", "url": "https://www.conib.org.br/feed/"},
    {"source_name": "Tribuna da Serra", "url": "https://tribunadaserra.com.br/feed/"},
]

# WordPress sites where RSS is shallow (usually ~30 most recent) but the REST API can backfill
# older content reliably by date window + search term.
WORDPRESS_API_SITES: list[dict[str, str]] = [
    {"source_name": "Diario do Rio", "base_url": "https://diariodorio.com"},
    {"source_name": "Tempo Real RJ", "base_url": "https://temporealrj.com"},
    {
        "source_name": "Agenda do Poder",
        "base_url": "https://agendadopoder.com.br",
        "query_variants": ["Flavio Valle", "Flávio Valle", "Valle"],
    },
    {"source_name": "Tribuna da Serra", "base_url": "https://tribunadaserra.com.br"},
    {"source_name": "Veja Rio", "base_url": "https://vejario.abril.com.br"},
    {"source_name": "VEJA", "base_url": "https://veja.abril.com.br"},
]

GOOGLE_NEWS_QUERIES: list[str] = [
    '"Flavio Valle"',
    '"Flavio Valle" vereador',
    '"Pedro Angelito"',
    '"Pedro Angelito" subprefeito',
    '"Bernardo Rubiao"',
    '"subprefeitura zona sul" Rio',
]

FLAVIO_QUERY_VARIANTS: list[str] = ["Flavio Valle", "Flávio Valle"]
FLAVIO_INTERNAL_SEARCH_QUERIES: list[str] = ["Flavio Valle", "Flávio Valle"]

SITEMAP_DAILY_SOURCES: list[dict[str, str]] = [
    {
        "source_name": "O Globo Sitemap",
        "host": "oglobo.globo.com",
        "sitemap_url_template": "https://oglobo.globo.com/sitemap/oglobo/{yyyy}/{mm}/{dd}_{page}.xml",
    },
    {
        "source_name": "G1 Sitemap",
        "host": "g1.globo.com",
        "sitemap_url_template": "https://g1.globo.com/sitemap/g1/{yyyy}/{mm}/{dd}_{page}.xml",
    },
    {
        "source_name": "CBN Sitemap",
        "host": "cbn.globo.com",
        "sitemap_url_template": "https://cbn.globo.com/sitemap/cbn/{yyyy}/{mm}/{dd}_{page}.xml",
    },
    {
        "source_name": "Extra Sitemap",
        "host": "extra.globo.com",
        "sitemap_url_template": "https://extra.globo.com/sitemap/extra/{yyyy}/{mm}/{dd}_{page}.xml",
    },
    {
        "source_name": "Veja Rio Sitemap",
        "host": "vejario.abril.com.br",
        "sitemap_url_template": "https://vejario.abril.com.br/sitemap.xml?yyyy={yyyy}&mm={mm}&dd={dd}",
    },
]

VEJARIO_ARCHIVE_TARGETS: list[dict[str, str]] = [
    {
        "source_name": "Veja Rio Lu Lacerda Archive",
        "host": "vejario.abril.com.br",
        "start_url": "https://vejario.abril.com.br/coluna/lu-lacerda/",
        "article_path_prefix": "/coluna/lu-lacerda/",
    },
    {
        "source_name": "Veja Rio Adriana Camargo Archive",
        "host": "vejario.abril.com.br",
        "start_url": "https://vejario.abril.com.br/autor/adriana-camargo/",
        "article_path_prefix": "/coluna/adriana-camargo/",
    },
]

CAMARA_ARCHIVE_TARGET: dict[str, str | int] = {
    "source_name": "Camara Rio Archive",
    "host": "camara.rio",
    "start_url": "https://camara.rio/comunicacao/noticias",
    "page_size": 10,
}

@dataclass(slots=True)
class InternalSearchTarget:
    source_name: str
    host: str
    mode: str
    search_url_template: str
    search_profile: str = ""
    recency_query_id: str = ""
    navigational_profile: str = ""
    navigational_query_id: str = ""
    live_profile: str = ""
    live_query_id: str = ""
    editorial_query_id: str = ""
    page_size: int = 10

FLAVIO_VERIFIED_HOSTS: list[str] = [
    "a3noticias.com.br",
    "ademi.org.br",
    "agendadopoder.com.br",
    "almapreta.com.br",
    "band.com.br",
    "bbc.com",
    "boletimrj.com.br",
    "camara.rio",
    "campos24horas.com.br",
    "canalvoxnoticias.com.br",
    "cbn.globo.com",
    "colunadogilson.com.br",
    "conib.org.br",
    "diariocarioca.com",
    "diariodorio.com",
    "enfoco.com.br",
    "errejotanoticias.com.br",
    "eurio.com.br",
    "extra.globo.com",
    "folhadoleste.com.br",
    "g1.globo.com",
    "gazetasulflu.com.br",
    "iclipping.com.br",
    "ilovecorrida.com.br",
    "mancheterio.com.br",
    "mercadoeeventos.com.br",
    "newmag.com.br",
    "noticias.r7.com",
    "odia.ig.com.br",
    "oglobo.globo.com",
    "portaltela.com",
    "povonarua.com.br",
    "temporealrj.com",
    "tnh1.com.br",
    "tribunadaserra.com.br",
    "tupi.fm",
    "vejario.abril.com.br",
    "www1.folha.uol.com.br",
    "youtu.be",
]

FLAVIO_INTERNAL_SEARCH_TARGETS: list[InternalSearchTarget] = [
    InternalSearchTarget(
        source_name="O Globo Internal Search",
        host="oglobo.globo.com",
        mode="globo_api",
        search_url_template="https://oglobo.globo.com/busca/?q={query}",
        search_profile="sp_oglobo_globo_com",
        recency_query_id="oglobo.info_query_recency",
        navigational_profile="navegacional_oglobo",
        navigational_query_id="oglobo.navigational_query",
        live_profile="conteudo_editorial_oglobo",
        live_query_id="oglobo.live_query",
        editorial_query_id="oglobo.pub_editorial_query",
        page_size=10,
    ),
    InternalSearchTarget(
        source_name="G1 Internal Search",
        host="g1.globo.com",
        mode="globo_api",
        search_url_template="https://g1.globo.com/busca/?q={query}",
        search_profile="sp_g1_globo_com",
        recency_query_id="g1.info_query_recency",
        navigational_profile="navegacional_g1",
        navigational_query_id="g1.navigational_query",
        live_profile="conteudo_editorial_g1",
        live_query_id="g1.live_query",
        editorial_query_id="g1.pub_editorial_query",
        page_size=10,
    ),
    InternalSearchTarget(
        source_name="Veja Rio Internal Search",
        host="vejario.abril.com.br",
        mode="html",
        search_url_template="https://vejario.abril.com.br/busca/?s={query}&orderby=date",
    ),
    InternalSearchTarget(
        source_name="Camara Rio Internal Search",
        host="camara.rio",
        mode="html",
        search_url_template="https://camara.rio/index.php?option=com_search&view=search&searchphrase=exact&ordering=newest&searchword={query}",
    ),
    InternalSearchTarget(
        source_name="Conib Internal Search",
        host="www.conib.org.br",
        mode="html",
        search_url_template="https://www.conib.org.br/pesquisar.html?searchword={query}&searchphrase=exact&ordering=newest",
    ),
    InternalSearchTarget(
        source_name="Extra Globo Internal Search",
        host="extra.globo.com",
        mode="globo_api",
        search_url_template="https://extra.globo.com/busca/?q={query}",
        search_profile="sp_extra_globo_com",
        recency_query_id="extra.info_query_recency",
        navigational_profile="navegacional_extra",
        navigational_query_id="extra.navigational_query",
        live_profile="conteudo_editorial_extra",
        live_query_id="extra.live_query",
        editorial_query_id="extra.pub_editorial_query",
        page_size=10,
    ),
]
# Note: O Dia is covered by DIRECT_SCRAPE_TARGETS, R7 by RSS_FEEDS

def google_news_rss_url(query: str) -> str:
    q = quote_plus(query)
    return f"https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"

SLUG_RE = re.compile(r"[^a-z0-9]+")

def slug_key(value: str) -> str:
    raw = (value or "").strip().lower()
    slug = SLUG_RE.sub("_", raw).strip("_")
    return slug or "target"

def _ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered

def build_google_queries_for_target(target: Target) -> list[str]:
    display_name = str(target.display_name or "").strip()
    if not display_name:
        return []
    if target.key == "flavio_valle":
        base_queries = [
            '"Flavio Valle"',
            '"Flávio Valle"',
            '"Flavio Valle" vereador',
            '"Flávio Valle" vereador',
        ]
        host_queries: list[str] = []
        for host in FLAVIO_VERIFIED_HOSTS:
            host_queries.extend(
                [
                    f'site:{host} "Flavio Valle"',
                    f'site:{host} "Flávio Valle"',
                ]
            )
        return _ordered_unique([*base_queries, *host_queries])
    return [f'"{display_name}"']

def build_direct_scrape_queries_for_target(target: Target) -> list[str]:
    if target.key == "flavio_valle":
        return ["Flavio Valle", "Flávio Valle"]
    keywords = target.keywords[:3] if target.keywords else [target.display_name]
    return _ordered_unique([str(keyword or "").strip() for keyword in keywords])

def build_wordpress_queries_for_target(target: Target) -> list[str]:
    display_name = str(target.display_name or "").strip()
    if not display_name:
        return []
    if target.key == "flavio_valle":
        return ["Flavio Valle", "Flávio Valle"]
    return [display_name]

def build_wordpress_queries_for_site(target: Target, site: dict) -> list[str]:
    """Per-site WordPress query list; falls back to target-level queries."""
    site_queries = site.get("query_variants")
    if isinstance(site_queries, list):
        normalized = [str(item or "").strip() for item in site_queries if str(item or "").strip()]
        if normalized:
            return _ordered_unique(normalized)
    return build_wordpress_queries_for_target(target)

def get_active_targets() -> list[Target]:
    if not TARGETS_JSON_PATH.exists():
        return list(DEFAULT_TARGETS)
    try:
        with TARGETS_JSON_PATH.open("r", encoding="utf-8-sig") as fh:
            payload = json.load(fh)
        if not isinstance(payload, list):
            return list(DEFAULT_TARGETS)
        targets: list[Target] = []
        for row in payload:
            if not isinstance(row, dict):
                continue
            label = str(row.get("label", "")).strip()
            if not label:
                continue
            key = str(row.get("key", "")).strip() or slug_key(label)
            priority = 1 if bool(row.get("primary", False)) else 2
            raw_keywords = row.get("keywords", [])
            if isinstance(raw_keywords, list):
                keywords = [str(item).strip() for item in raw_keywords if str(item).strip()]
            elif isinstance(raw_keywords, str):
                keywords = [part.strip() for part in raw_keywords.split(",") if part.strip()]
            else:
                keywords = []
            if label not in keywords:
                keywords = [label, *keywords]
            targets.append(
                Target(
                    key=key,
                    display_name=label,
                    priority=priority,
                    keywords=keywords,
                )
            )
        return targets or list(DEFAULT_TARGETS)
    except Exception:
        return list(DEFAULT_TARGETS)

@dataclass(slots=True)
class ScrapeTarget:
    source_name: str
    search_url_template: str

# These are intentionally simple and best-effort.
DIRECT_SCRAPE_TARGETS: list[ScrapeTarget] = [
    ScrapeTarget("VEJA", "https://veja.abril.com.br/busca/?s={query}&orderby=date"),
    ScrapeTarget("Diario do Rio", "https://diariodorio.com/?s={query}"),
    ScrapeTarget("O Dia", "https://odia.ig.com.br/busca/?q={query}"),
    ScrapeTarget("Jornal do Brasil", "https://www.jb.com.br/busca?q={query}"),
    ScrapeTarget("Extra", "https://extra.globo.com/busca/?q={query}"),
    ScrapeTarget("Tempo Real RJ", "https://temporealrj.com/?s={query}"),
    ScrapeTarget("Agenda do Poder", "https://agendadopoder.com.br/?s={query}"),
    ScrapeTarget("Veja Rio", "https://vejario.abril.com.br/busca/?s={query}&orderby=date"),
    ScrapeTarget("Camara Rio", "https://camara.rio/busca?q={query}"),
    ScrapeTarget("Conib", "https://www.conib.org.br/?s={query}"),
]


# ── Backward-compatibility aliases ──────────────────────────────────────
# The rewritten ingest.py and collectors.py (F2-T7, F2-T6) import these
# simplified names. These aliases bridge until those modules are restored
# from originals in F2-T6b/F2-T7b.
WORDPRESS_HOSTS = [site["base_url"].split("//")[-1].rstrip("/") for site in WORDPRESS_API_SITES]
SITEMAP_CONFIGS = [
    {
        "name": src.get("source_name", ""),
        "sitemap_url_template": src.get("sitemap_url_template", ""),
        "host": src.get("host", ""),
        "daily": True,
    }
    for src in SITEMAP_DAILY_SOURCES
]
def get_default_query(target_keywords):
    """Compatibility alias — rewritten ingest.py calls this."""
    if not target_keywords:
        return ""
    return target_keywords[0]
