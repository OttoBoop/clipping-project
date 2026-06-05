"""Keyword matching for citation detection in article text."""
from dataclasses import dataclass, field
import re
import unicodedata


@dataclass
class Target:
    key: str
    label: str = ""
    display_name: str = ""
    keywords: list = field(default_factory=list)
    exact_aliases: list = field(default_factory=list)
    className: str = ""
    primary: bool = False
    priority: int = 2


@dataclass
class MatchHit:
    target_key: str
    target_name: str
    keyword_matched: str
    position: int = 0


class CitationMatcher:
    """Match text against target keywords."""

    def __init__(self, targets, *, exact_names_only=False):
        self.targets = targets
        self.exact_names_only = exact_names_only
        self._keyword_map = {}  # normalized keyword -> (target, original_keyword)
        for t in targets:
            aliases = [str(a).strip() for a in (t.exact_aliases or []) if str(a).strip()]
            if exact_names_only:
                kws = [t.display_name or t.label] + list(t.keywords or []) + aliases
            else:
                kws = list(t.keywords or []) + aliases + [t.display_name or t.label]
            for kw in kws:
                kw_stripped = kw.strip()
                if kw_stripped:
                    normalized_kw = _normalize_match_text(kw_stripped)
                    if normalized_kw:
                        self._keyword_map[normalized_kw] = (t, kw_stripped)

    def find_hits(self, text):
        """Find all target keyword matches in text."""
        if not text:
            return []
        normalized_text = _normalize_match_text(text)
        hits = []
        seen = set()
        for normalized_kw, (target, original_kw) in self._keyword_map.items():
            pos = normalized_text.find(normalized_kw)
            if pos >= 0:
                dedup_key = (target.key, normalized_kw)
                if dedup_key not in seen:
                    seen.add(dedup_key)
                    hits.append(MatchHit(
                        target_key=target.key,
                        target_name=target.display_name or target.label,
                        keyword_matched=original_kw,
                        position=pos,
                    ))
        return hits


def _normalize_match_text(value) -> str:
    text = str(value or "").casefold()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()
