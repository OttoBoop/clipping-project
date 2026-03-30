"""Source configurations for the clipping pipeline."""
from dataclasses import dataclass


@dataclass
class InternalSearchTarget:
    name: str
    host: str
    search_url_template: str
    source_type: str = "internal_search"


# Brazilian news sites with search pages
FLAVIO_INTERNAL_SEARCH_TARGETS = [
    InternalSearchTarget(
        name="O Globo", host="oglobo.globo.com",
        search_url_template="https://oglobo.globo.com/busca/?q={query}&pagina={page}",
    ),
    InternalSearchTarget(
        name="Extra", host="extra.globo.com",
        search_url_template="https://extra.globo.com/busca/?q={query}&pagina={page}",
    ),
    InternalSearchTarget(
        name="O Dia", host="odia.ig.com.br",
        search_url_template="https://odia.ig.com.br/busca?q={query}&page={page}",
    ),
    InternalSearchTarget(
        name="R7", host="noticias.r7.com",
        search_url_template="https://busca.r7.com/search?q={query}&page={page}",
    ),
]

# WordPress REST API hosts
WORDPRESS_HOSTS = [
    "agendadopoder.com.br",
]

# RSS feed sources: (name, url)
RSS_FEEDS = []

# Sitemap sources for daily scanning
SITEMAP_CONFIGS = [
    {"name": "CBN", "sitemap_url": "https://www.cbn.globo.com/sitemap/sitemap-news.xml", "host": "cbn.globo.com"},
]


def get_default_query(target_keywords):
    """Build search query from target keywords. Uses shortest useful keyword."""
    if not target_keywords:
        return ""
    return target_keywords[0]
