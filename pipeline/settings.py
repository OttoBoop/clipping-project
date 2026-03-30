"""Source configurations for the clipping pipeline."""
from dataclasses import dataclass


@dataclass
class InternalSearchTarget:
    name: str
    host: str
    search_url_template: str
    source_type: str = "internal_search"
    uses_globo_api: bool = False


# Globo family uses a JSON API at busca.globo.com
FLAVIO_INTERNAL_SEARCH_TARGETS = [
    InternalSearchTarget(
        name="O Globo", host="oglobo.globo.com",
        search_url_template="https://busca.globo.com/v1/search?q={query}&page={page}&sort=recent&source=oglobo",
        uses_globo_api=True,
    ),
    InternalSearchTarget(
        name="Extra", host="extra.globo.com",
        search_url_template="https://busca.globo.com/v1/search?q={query}&page={page}&sort=recent&source=extra",
        uses_globo_api=True,
    ),
    InternalSearchTarget(
        name="CBN", host="cbn.globo.com",
        search_url_template="https://cbn.globo.com/busca/?q={query}",
        uses_globo_api=False,
    ),
    InternalSearchTarget(
        name="O Dia", host="odia.ig.com.br",
        search_url_template="https://odia.ig.com.br/busca?q={query}&page={page}",
    ),
    InternalSearchTarget(
        name="R7", host="noticias.r7.com",
        search_url_template="https://busca.r7.com/search?q={query}&page={page}",
    ),
    InternalSearchTarget(
        name="CONIB", host="conib.org.br",
        search_url_template="https://www.conib.org.br/?s={query}&paged={page}",
    ),
    InternalSearchTarget(
        name="Diário do Rio", host="diariodorio.com",
        search_url_template="https://diariodorio.com/?s={query}&paged={page}",
    ),
]

# WordPress REST API hosts
WORDPRESS_HOSTS = [
    "agendadopoder.com.br",
]

# RSS feed sources: (name, url)
RSS_FEEDS = []

# CBN sitemaps use daily URLs: /sitemap/cbn/YYYY/MM/DD_1.xml
SITEMAP_CONFIGS = [
    {
        "name": "CBN",
        "sitemap_url_template": "https://cbn.globo.com/sitemap/cbn/{yyyy}/{mm}/{dd}_1.xml",
        "host": "cbn.globo.com",
        "daily": True,
    },
]


def get_default_query(target_keywords):
    """Build search query from target keywords."""
    if not target_keywords:
        return ""
    return target_keywords[0]
