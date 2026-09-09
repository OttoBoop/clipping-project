"""Publisher-verified URL classes that must not enter the news corpus."""
from urllib.parse import unquote, urlparse


def non_news_reason(url: str) -> str:
    parsed = urlparse(str(url or ""))
    host = (parsed.hostname or "").lower().rstrip(".")
    if host in {"ndmais.com.br", "www.ndmais.com.br"} and unquote(parsed.path).startswith("/eleicoes/2026/candidatos/"):
        return "publisher_directory_not_news"
    return ""
