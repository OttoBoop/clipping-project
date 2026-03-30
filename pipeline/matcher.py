"""Keyword matching for citation detection in article text."""
from dataclasses import dataclass, field


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
        self._keyword_map = {}  # lowercase keyword -> (target, original_keyword)
        for t in targets:
            aliases = [str(a).strip() for a in (t.exact_aliases or []) if str(a).strip()]
            if exact_names_only:
                kws = [t.display_name or t.label] + aliases
            else:
                kws = list(t.keywords or []) + aliases + [t.display_name or t.label]
            for kw in kws:
                kw_stripped = kw.strip()
                if kw_stripped:
                    self._keyword_map[kw_stripped.lower()] = (t, kw_stripped)

    def find_hits(self, text):
        """Find all target keyword matches in text. Case-insensitive."""
        if not text:
            return []
        text_lower = text.lower()
        hits = []
        seen = set()
        for kw_lower, (target, original_kw) in self._keyword_map.items():
            pos = text_lower.find(kw_lower)
            if pos >= 0:
                dedup_key = (target.key, kw_lower)
                if dedup_key not in seen:
                    seen.add(dedup_key)
                    hits.append(MatchHit(
                        target_key=target.key,
                        target_name=target.display_name or target.label,
                        keyword_matched=original_kw,
                        position=pos,
                    ))
        return hits
