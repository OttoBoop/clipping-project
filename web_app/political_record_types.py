"""Publisher-verified URL classes that must not enter the news corpus."""
from urllib.parse import unquote, urlparse
import re
import unicodedata

_ND_PROFILE_TITLE = re.compile(
    r".+ \d{2,6} - candidat[oa] a (?:governador(?:a)?|senador(?:a)?|deputad[oa] (?:estadual|federal)) "
    r"d[oa] [a-z]{2} pelo [a-z0-9 ]+ \| eleicoes 2026 - (?:ndmais\.com\.br|nd mais)"
)
_GAZETA_PROFILE_TITLE = re.compile(
    r".+ \d{2,6} \([a-z0-9 ]+\): candidat[oa] a (?:governador(?:a)?|senador(?:a)?|deputad[oa] (?:estadual|federal)) "
    r"pelo [a-z]{2} - (?:gazeta do povo|gazetadopovo\.com\.br)"
)


def non_news_reason(url: str, title: str = "") -> str:
    parsed = urlparse(str(url or ""))
    host = (parsed.hostname or "").lower().rstrip(".")
    if host in {"ndmais.com.br", "www.ndmais.com.br", "gazetadopovo.com.br", "www.gazetadopovo.com.br"} and unquote(parsed.path).startswith("/eleicoes/2026/candidatos/"):
        return "publisher_directory_not_news"
    if host == "news.google.com" and parsed.path.startswith(("/rss/articles/", "/articles/")):
        normalized = " ".join("".join(char for char in unicodedata.normalize("NFKD", str(title).casefold())
                                       if not unicodedata.combining(char)).split())
        # The exact publisher-labelled candidate-directory title is present in
        # the original feed even when Google's wrapper cannot resolve. Ordinary
        # ND Mais editorial headlines and other publishers remain eligible.
        if _ND_PROFILE_TITLE.fullmatch(normalized) or _GAZETA_PROFILE_TITLE.fullmatch(normalized):
            return "publisher_directory_not_news"
    return ""
