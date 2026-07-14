from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GAZETTEER_PATH = PROJECT_ROOT / "data" / "rio_geography_v1.json"
WORD_RE = re.compile(r"[^a-z0-9]+")


def normalize_geo_text(value: str) -> str:
    folded = unicodedata.normalize("NFKD", str(value or ""))
    ascii_text = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return f" {WORD_RE.sub(' ', ascii_text.lower()).strip()} "


def _contains(text: str, phrase: str) -> bool:
    needle = normalize_geo_text(phrase).strip()
    return bool(needle and f" {needle} " in text)


def _matches(text: str, values: tuple[str, ...]) -> list[str]:
    return [value for value in values if _contains(text, value)]


@dataclass(frozen=True)
class GeographyDecision:
    status: str
    score: float
    evidence: tuple[dict[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        return {"status": self.status, "score": self.score, "evidence": [dict(row) for row in self.evidence]}


@dataclass(frozen=True)
class RioGazetteer:
    version: str
    strong_city_phrases: tuple[str, ...]
    city_institutions: tuple[str, ...]
    city_landmarks: tuple[str, ...]
    neighborhoods: tuple[str, ...]
    ambiguous_locations: tuple[str, ...]
    other_municipalities: tuple[str, ...]
    state_only_phrases: tuple[str, ...]
    dimensions: dict[str, tuple[str, ...]]

    @classmethod
    def load(cls, path: Path = DEFAULT_GAZETTEER_PATH) -> "RioGazetteer":
        payload = json.loads(path.read_text(encoding="utf-8"))

        def values(key: str) -> tuple[str, ...]:
            raw = payload.get(key) or []
            return tuple(str(item).strip() for item in raw if str(item).strip())

        raw_dimensions = payload.get("dimensions") if isinstance(payload.get("dimensions"), dict) else {}
        dimensions = {
            str(key): tuple(str(item).strip() for item in terms if str(item).strip())
            for key, terms in raw_dimensions.items()
            if isinstance(terms, list)
        }
        return cls(
            version=str(payload.get("version") or path.stem),
            strong_city_phrases=values("strong_city_phrases"),
            city_institutions=values("city_institutions"),
            city_landmarks=values("city_landmarks"),
            neighborhoods=values("neighborhoods"),
            ambiguous_locations=values("ambiguous_locations"),
            other_municipalities=values("other_municipalities"),
            state_only_phrases=values("state_only_phrases"),
            dimensions=dimensions,
        )

    def classify(
        self,
        *,
        title: str,
        body: str,
        final_url: str = "",
        geography_prior: str = "neutral",
    ) -> GeographyDecision:
        title_text = normalize_geo_text(title)
        body_text = normalize_geo_text(body)
        combined = f"{title_text}{body_text}"
        evidence: list[dict[str, Any]] = []
        score = 0.0

        def add(kind: str, value: str, weight: float, location: str) -> None:
            nonlocal score
            score += weight
            evidence.append({"kind": kind, "value": value, "weight": weight, "location": location})

        strong_title = _matches(title_text, self.strong_city_phrases)
        strong_body = [value for value in _matches(body_text, self.strong_city_phrases) if value not in strong_title]
        for value in strong_title:
            add("strong_city_phrase", value, 5.0, "title")
        for value in strong_body[:5]:
            add("strong_city_phrase", value, 4.0, "body")

        institution_hits = _matches(combined, self.city_institutions)
        landmark_hits = _matches(combined, self.city_landmarks)
        for value in institution_hits[:5]:
            add("city_institution", value, 3.0, "content")
        for value in landmark_hits[:5]:
            add("city_landmark", value, 2.5, "content")

        ambiguous_normalized = {normalize_geo_text(value).strip() for value in self.ambiguous_locations}
        neighborhood_hits = _matches(combined, self.neighborhoods)
        unambiguous_hits = [
            value for value in neighborhood_hits if normalize_geo_text(value).strip() not in ambiguous_normalized
        ]
        ambiguous_hits = [
            value for value in neighborhood_hits if normalize_geo_text(value).strip() in ambiguous_normalized
        ]
        for value in unambiguous_hits[:8]:
            add("city_neighborhood", value, 2.0, "content")

        prior = str(geography_prior or "neutral").strip()
        if prior in {"municipal_official", "city_focused"}:
            add("source_prior", prior, 4.0, "source")
        elif prior == "state_section":
            add("source_prior", prior, 0.75, "source")

        has_city_coevidence = bool(strong_title or strong_body or institution_hits or landmark_hits or unambiguous_hits)
        if prior in {"municipal_official", "city_focused"}:
            has_city_coevidence = True
        if has_city_coevidence:
            for value in ambiguous_hits[:5]:
                add("ambiguous_with_coevidence", value, 0.75, "content")
        else:
            for value in ambiguous_hits[:5]:
                evidence.append(
                    {"kind": "ambiguous_without_coevidence", "value": value, "weight": 0.0, "location": "content"}
                )

        other_hits = _matches(combined, self.other_municipalities)
        for value in other_hits[:8]:
            add("other_municipality", value, -1.5, "content")

        state_hits = _matches(combined, self.state_only_phrases)
        for value in state_hits[:5]:
            add("state_evidence", value, -0.5, "content")

        url_text = normalize_geo_text(final_url)
        if _contains(url_text, "rio de janeiro") or _contains(url_text, "rio"):
            add("editorial_path", final_url, 0.5, "url")

        positive_kinds = {
            "strong_city_phrase",
            "city_institution",
            "city_landmark",
            "city_neighborhood",
            "source_prior",
            "ambiguous_with_coevidence",
            "editorial_path",
        }
        has_positive = any(row["kind"] in positive_kinds and float(row["weight"]) > 0 for row in evidence)
        if has_positive and score >= 5.0:
            status = "confirmed"
        elif has_positive and score >= 2.5:
            status = "probable"
        elif other_hits:
            status = "other_city"
        elif state_hits or prior == "state_section":
            status = "state_only"
        else:
            status = "unknown"
        return GeographyDecision(status=status, score=round(score, 2), evidence=tuple(evidence))

    def classify_dimensions(self, *, title: str, body: str) -> dict[str, list[str]]:
        text = f"{normalize_geo_text(title)}{normalize_geo_text(body)}"
        return {name: _matches(text, terms) for name, terms in self.dimensions.items() if _matches(text, terms)}


_GAZETTEER: RioGazetteer | None = None


def rio_gazetteer() -> RioGazetteer:
    global _GAZETTEER
    if _GAZETTEER is None:
        _GAZETTEER = RioGazetteer.load()
    return _GAZETTEER
