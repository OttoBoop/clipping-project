"""Keyword matching for citation detection in article text."""
from dataclasses import dataclass, field
import re
import unicodedata
from urllib.parse import urlparse


TARGET_METADATA_FIELDS = (
    "political_roster_version", "group", "group_label", "role", "party",
    "verified_at", "sources", "preferred_for_political_run", "match_context",
    "collection_profiles",
)


def target_metadata(row: dict) -> dict:
    """Normalize optional roster metadata without changing legacy target records."""
    result = {}
    for key in TARGET_METADATA_FIELDS:
        if key not in row:
            continue
        value = row[key]
        if key == "preferred_for_political_run":
            result[key] = value is True
        elif key == "collection_profiles":
            result[key] = list(dict.fromkeys(
                item.strip() for item in (value if isinstance(value, list) else [])[:50]
                if isinstance(item, str) and re.fullmatch(r"[a-z0-9_]{1,80}", item.strip())
            ))
        elif key == "sources":
            result[key] = []
            for item in (value if isinstance(value, list) else [])[:20]:
                if not isinstance(item, dict):
                    continue
                url = str(item.get("url") or "").strip()
                try:
                    parsed = urlparse(url)
                except ValueError:
                    continue
                if parsed.scheme in {"http", "https"} and parsed.netloc:
                    result[key].append({"url": url, "note": str(item.get("note") or "")[:600]})
        elif key == "match_context":
            context = value if isinstance(value, dict) else {}
            normalized = {}
            for field_name in ("required_for", "any_of", "none_of", "exempt_aliases", "excluded_phrases"):
                values = context.get(field_name, [])
                normalized[field_name] = [str(item).strip() for item in values[:50] if str(item).strip()] if isinstance(values, list) else []
            try:
                window = int(context.get("window_chars", 220))
            except (TypeError, ValueError):
                window = 220
            normalized["window_chars"] = max(80, min(window, 1000))
            result[key] = normalized
        else:
            result[key] = str(value or "").strip()[:600]
    return result


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
    political_roster_version: str = ""
    group: str = ""
    group_label: str = ""
    role: str = ""
    party: str = ""
    verified_at: str = ""
    sources: list = field(default_factory=list)
    preferred_for_political_run: bool = False
    match_context: dict = field(default_factory=dict)
    collection_profiles: list = field(default_factory=list)


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
        self._keyword_map = {}  # (target key, normalized keyword) -> rule
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
                        self._keyword_map[(t.key, normalized_kw)] = (
                            t, kw_stripped, _phrase_pattern(normalized_kw)
                        )

    def find_hits(self, text):
        """Find all target keyword matches in text."""
        if not text:
            return []
        normalized_text = _normalize_match_text(text)
        hits = []
        seen = set()
        for (_, normalized_kw), (target, original_kw, pattern) in self._keyword_map.items():
            for match in pattern.finditer(normalized_text):
                pos = match.start()
                if not _context_matches(target, normalized_kw, normalized_text, pos, match.end()):
                    continue
                dedup_key = (target.key, normalized_kw)
                if dedup_key not in seen:
                    seen.add(dedup_key)
                    hits.append(MatchHit(
                        target_key=target.key,
                        target_name=target.display_name or target.label,
                        keyword_matched=original_kw,
                        position=pos,
                    ))
                break
        return hits


def _phrase_pattern(normalized: str):
    return re.compile(r"(?<!\w)" + re.escape(normalized) + r"(?!\w)")


def _has_phrase(text: str, phrase: str) -> bool:
    normalized = _normalize_match_text(phrase)
    return bool(normalized and _phrase_pattern(normalized).search(text))


def _context_matches(target: Target, keyword: str, text: str, start: int, end: int) -> bool:
    context = target_metadata({"match_context": target.match_context})["match_context"]
    # A namesake or attribution excludes only the overlapping occurrence. Apply
    # this before alias exemptions; another genuine mention remains eligible.
    for phrase in context["excluded_phrases"]:
        normalized_phrase = _normalize_match_text(phrase)
        if not normalized_phrase:
            continue
        left = max(0, start - len(normalized_phrase))
        for excluded in _phrase_pattern(normalized_phrase).finditer(text[left:end + len(normalized_phrase)]):
            if left + excluded.start() < end and left + excluded.end() > start:
                return False
    if any(_has_phrase(keyword, alias) for alias in context["exempt_aliases"]):
        return True
    # An inherited short keyword can still occur inside a verified full civil
    # name, without requiring us to overwrite the user's saved alias list.
    for alias in context["exempt_aliases"]:
        normalized_alias = _normalize_match_text(alias)
        if not normalized_alias:
            continue
        left = max(0, start - len(normalized_alias))
        for match in _phrase_pattern(normalized_alias).finditer(text[left:end + len(normalized_alias)]):
            if left + match.start() <= start and left + match.end() >= end:
                return True
    if not any(_has_phrase(keyword, alias) for alias in context["required_for"]):
        return True
    window = context["window_chars"]
    nearby = text[max(0, start - window):end + window]
    if any(_has_phrase(nearby, phrase) for phrase in context["none_of"]):
        return False
    return any(_has_phrase(nearby, phrase) for phrase in context["any_of"])


def _normalize_match_text(value) -> str:
    text = str(value or "").casefold()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()
