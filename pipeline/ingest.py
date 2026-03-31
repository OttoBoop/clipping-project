# ============================================================================
# pipeline/ingest.py — RECOVERED from Codex session log
# Source: D:\recovery\YOUR_FILES\recovered_224598MB_63334KB.py
#
# Base extraction: offset 6118357 (verbatim Get-Content dump, 933 lines)
# select_targets: offset 1902603 (verbatim)
# Patches applied from multiple occurrences (offsets 2870767, 5301590, 5311452,
#   6453777): candidate_metadata, force_full_fetch, exact_body_only,
#   internal_site_search section, source_options in run_ingestion loop
#
# Lines marked [RECONSTRUCTED] were stitched from patch diffs, not verbatim.
# All other code is verbatim from the session log.
# ============================================================================
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from typing import Callable
from urllib.parse import urlparse

from .collectors import (
    CandidateArticle,
    collect_camara_archive,
    collect_direct_scrape,
    collect_google_news,
    collect_internal_site_search,
    collect_rss,
    collect_sitemap_daily,
    collect_vejario_archive,
    collect_wordpress_api,
    fetch_full_article_text,
)
from .database import ClippingDB
from .matcher import CitationMatcher
from .normalization import normalize_text
from .settings import (
    BACKFILL_START_DATE,
    CAMARA_ARCHIVE_TARGET,
    DB_PATH,
    FLAVIO_INTERNAL_SEARCH_QUERIES,
    FLAVIO_INTERNAL_SEARCH_TARGETS,
    SITEMAP_DAILY_SOURCES,
    VEJARIO_ARCHIVE_TARGETS,
    WORDPRESS_API_SITES,
    build_direct_scrape_queries_for_target,
    build_google_queries_for_target,
    build_wordpress_queries_for_target,
    get_active_targets,
)


SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
URL_RE = re.compile(r"https?://\S+")
SEARCH_NOISE_RE = re.compile(r"(resultado[s]?\s+da\s+pesquisa|wp-content|comments?)", re.IGNORECASE)

POSITIVE_MARKERS = {
    "apoio",
    "aprova",
    "elogia",
    "avanco",
    "beneficio",
    "melhora",
    "positivo",
}
NEGATIVE_MARKERS = {
    "critica",
    "irregularidade",
    "acusacao",
    "denuncia",
    "atraso",
    "problema",
    "negativo",
}

STOPWORDS = {
    "de", "da", "do", "das", "dos", "e", "a", "o", "em", "no", "na", "para", "com", "por", "uma",
    "um", "sobre", "ao", "aos", "as", "os", "que", "como", "mais", "menos", "sem", "se", "sua", "seu",
    "rio", "janeiro", "diario", "noticia", "prefeitura",
}


@dataclass(slots=True)
class IngestionResult:
    source_name: str
    source_type: str
    candidates_seen: int
    articles_inserted: int
    mentions_inserted: int
    stories_touched: int
    errors: list[str]


@dataclass(slots=True)
class IngestionOptions:
    max_candidates_per_source: int = 90
    max_process_seconds: int = 90
    request_timeout_seconds: int = 8
    custom_query: str = ""
    date_from: str = ""
    date_to: str = ""
    archive_full_text: bool = True
    forced_terms: list[str] | None = None
    forced_terms_mode: str = "any"
    target_keys: list[str] | None = None


ProgressCallback = Callable[[str, dict], None]


def summarize_text(text: str, max_sentences: int = 3) -> str:
    clean = (text or "").strip()
    if not clean:
        return ""
    clean = URL_RE.sub(" ", clean)
    parts = [p.strip() for p in SENTENCE_RE.split(clean) if p.strip()]
    if not parts:
        return clean[:420]
    selected: list[str] = []
    for p in parts:
        if SEARCH_NOISE_RE.search(p):
            continue
        if len(p.split()) < 6:
            continue
        selected.append(p)
        if len(selected) >= max_sentences:
            break
    if not selected:
        selected = parts[:max_sentences]
    return " ".join(selected)[:700]


def normalize_forced_terms(terms: list[str] | None) -> list[str]:
    if not terms:
        return []
    normalized: list[str] = []
    for term in terms:
        value = normalize_text(term)
        if len(value) >= 3:
            normalized.append(value)
    return normalized


def passes_forced_terms(text: str, terms: list[str], mode: str) -> bool:
    if not terms:
        return True
    normalized_text = normalize_text(text)
    hits = [t for t in terms if t in normalized_text]
    if mode == "all":
        return len(hits) == len(terms)
    return len(hits) > 0


def infer_sentiment(text: str) -> str:
    normalized = normalize_text(text)
    pos = sum(1 for w in POSITIVE_MARKERS if w in normalized)
    neg = sum(1 for w in NEGATIVE_MARKERS if w in normalized)
    delta = pos - neg
    if delta >= 3:
        return "very_positive"
    if delta > 0:
        return "positive"
    if delta <= -3:
        return "very_negative"
    if delta < 0:
        return "negative"
    return "neutral"


def similarity(a: str, b: str) -> float:
    na = normalize_text(clean_title(a))
    nb = normalize_text(clean_title(b))
    if not na or not nb:
        return 0.0
    seq = SequenceMatcher(None, na, nb).ratio()
    toks_a = significant_tokens(na)
    toks_b = significant_tokens(nb)
    jacc = (len(toks_a & toks_b) / len(toks_a | toks_b)) if (toks_a and toks_b) else 0.0
    overlap = len(toks_a & toks_b)
    # Penalize false grouping when overlap is weak and similarity comes from source boilerplate.
    if overlap < 2:
        seq *= 0.55
    return max(seq, jacc)


def significant_tokens(text: str) -> set[str]:
    return {t for t in normalize_text(text).split() if len(t) >= 4 and t not in STOPWORDS}


def parse_iso(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_date_boundary(value: str, *, end_of_day: bool) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        if len(raw) == 10:
            dt = datetime.strptime(raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if end_of_day:
                dt = dt + timedelta(days=1) - timedelta(microseconds=1)
            return dt
        return parse_iso(raw)
    except Exception:
        return None


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        items.append(item)
    return items


def select_targets(targets: list, target_keys: list[str] | None) -> list:
    requested = ordered_unique(target_keys or [])
    if not requested:
        return list(targets)
    target_map = {str(target.key): target for target in targets}
    missing = [key for key in requested if key not in target_map]
    if missing:
        raise ValueError(f"unknown_target_keys:{','.join(missing)}")
    return [target_map[key] for key in requested]


def dedupe_candidates(candidates: list[CandidateArticle]) -> list[CandidateArticle]:
    deduped: list[CandidateArticle] = []
    seen_urls: set[str] = set()
    for candidate in candidates:
        url = str(candidate.url or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        deduped.append(candidate)
    return deduped


def is_recent_enough(value: str, *, date_from: datetime | None = None, date_to: datetime | None = None) -> bool:
    try:
        dt = parse_iso(value)
    except Exception:
        return True
    # Backfill floor only applies when caller did not explicitly choose a lower bound.
    if date_from is None and dt < BACKFILL_START_DATE:
        return False
    if date_from and dt < date_from:
        return False
    if date_to and dt > date_to:
        return False
    return True


TITLE_SUFFIX_RE = re.compile(r"\s*-\s*(diario do rio.*|o globo.*|g1.*|agencia brasil.*)$", re.IGNORECASE)


def clean_title(value: str) -> str:
    title = clean_text(value)
    title = TITLE_SUFFIX_RE.sub("", title).strip(" -")
    return title


def clean_text(value: str) -> str:
    text = URL_RE.sub(" ", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_bad_article_quality(title: str, summary: str, url: str, *, allow_short_summary: bool = False) -> bool:
    normalized_title = normalize_text(clean_title(title))
    normalized_summary = normalize_text(summary)
    if not normalized_title or normalized_title == "(sem titulo)":
        return True
    if SEARCH_NOISE_RE.search(title) or SEARCH_NOISE_RE.search(summary):
        return True
    if "/search/" in url or "/page/" in url:
        return True
    # Guard against nav garbage.
    if not allow_short_summary and len(normalized_summary.split()) < 20:
        return True
    return False


def choose_story(
    db: ClippingDB,
    *,
    article_title: str,
    article_summary: str,
    target_keys: list[str],
    high_threshold: float = 0.78,
    low_threshold: float = 0.50,
) -> int | None:
    best_story_id: int | None = None
    best_score = 0.0
    for story in db.list_recent_stories(days=7):
        sid = int(story["id"])
        story_targets = set(db.get_story_targets(sid))
        if not story_targets.intersection(set(target_keys)):
            continue
        score_title = similarity(article_title, story["title"])
        score_summary = similarity(article_summary, story["summary"])
        score = max(score_title, score_summary * 0.65)
        overlap = len(significant_tokens(article_title) & significant_tokens(story["title"]))
        if overlap < 2 and score_title < 0.45:
            continue
        if score > best_score:
            best_score = score
            best_story_id = sid

    if best_story_id is None:
        return None
    if best_score >= high_threshold:
        return best_story_id
    if best_score >= low_threshold:
        return best_story_id
    return None


def story_temperature(article_count: int, unique_sources: int) -> float:
    temp = 22.0 + article_count * 9.0 + unique_sources * 6.0
    return float(max(0.0, min(100.0, temp)))


def create_or_update_story(
    db: ClippingDB,
    *,
    article_id: int,
    article_title: str,
    article_summary: str,
    source_name: str,
    target_keys: list[str],
) -> int:
    story_id = choose_story(
        db,
        article_title=article_title,
        article_summary=article_summary,
        target_keys=target_keys,
    )
    if story_id is None:
        story_id = db.create_story(
            title=article_title[:220] or "Nova historia",
            summary=article_summary[:800] or article_title[:220],
            temperature=34.0,
            target_keys=target_keys,
        )
    db.attach_article_to_story(story_id, article_id)
    for tkey in target_keys:
        db.ensure_story_target(story_id, tkey)

    # Recompute simple temperature without loading the full dashboard payload (which can be huge in backfills).
    try:
        article_count, unique_sources = db.story_article_stats(story_id)
        temp = story_temperature(article_count, unique_sources)
        db.update_story(story_id, temperature=temp)
    except Exception:
        db.update_story(story_id)
    return story_id


def process_candidates(
    source_name: str,
    source_type: str,
    candidates: list[CandidateArticle],
    *,
    options: IngestionOptions | None = None,
    progress_callback: ProgressCallback | None = None,
) -> IngestionResult:
    options = options or IngestionOptions()
    db = ClippingDB(DB_PATH)
    targets = select_targets(get_active_targets(), options.target_keys)
    if not targets:
        return IngestionResult(
            source_name=source_name,
            source_type=source_type,
            candidates_seen=0,
            articles_inserted=0,
            mentions_inserted=0,
            stories_touched=0,
            errors=[],
        )
    # Fase 1 (Ctrl+F) deve usar somente nomes exatos das figuras monitoradas.
    matcher = CitationMatcher(targets, exact_names_only=True)
    inserted = 0
    mentions_inserted = 0
    stories_touched = 0
    errors: list[str] = []
    seen = 0
    date_from = parse_date_boundary(options.date_from, end_of_day=False)
    date_to = parse_date_boundary(options.date_to, end_of_day=True)
    max_candidates = max(1, int(options.max_candidates_per_source))
    max_process_seconds = max(10, int(options.max_process_seconds))
    request_timeout = max(3, int(options.request_timeout_seconds))
    started_at = time.monotonic()
    archive_cutoff = max_process_seconds * 0.8
    forced_terms = normalize_forced_terms(options.forced_terms)
    forced_mode = (options.forced_terms_mode or "any").strip().lower()
    strict_window = bool(date_from or date_to)

    if progress_callback:
        progress_callback(
            "source_started",
            {
                "source_name": source_name,
                "source_type": source_type,
                "candidates_total": min(len(candidates), max_candidates),
                "max_candidates": max_candidates,
                "articles_inserted": 0,
                "mentions_inserted": 0,
                "stories_touched": 0,
                "candidates_seen": 0,
            },
        )

    def emit_candidate(
        *,
        candidate: CandidateArticle,
        status: str,
        reason: str,
        final_url: str,
        hits_for_candidate: list | None = None,
        title_value: str = "",
        published_value: str = "",
        summary_value: str = "",
        stage: str = "",
    ):
        if not progress_callback:
            return
        hit_list = hits_for_candidate or []
        progress_callback(
            "candidate_evaluated",
            {
                "source_name": source_name,
                "source_type": source_type,
                "candidate_url": final_url or candidate.url,
                "candidate_title": title_value or candidate.title or "",
                "published_at": published_value or candidate.published_at or "",
                "status": status,
                "reason": reason,
                "stage": stage or "processing",
                "matched_targets": sorted({h.target_key for h in hit_list}),
                "matched_keywords": sorted({h.keyword_matched for h in hit_list}),
                "summary_excerpt": (summary_value or "").strip()[:320],
            },
        )

    def is_google_news_redirect(url: str) -> bool:
        try:
            host = (urlparse(url or "").netloc or "").lower()
            return "news.google.com" in host
        except Exception:
            return False

    for candidate in candidates[:max_candidates]:
        if time.monotonic() - started_at > max_process_seconds:
            errors.append("time_budget_exceeded")
            if progress_callback:
                progress_callback(
                    "source_progress",
                    {
                        "source_name": source_name,
                        "source_type": source_type,
                        "candidates_seen": seen,
                        "articles_inserted": inserted,
                        "mentions_inserted": mentions_inserted,
                        "stories_touched": stories_touched,
                        "status": "time_budget_exceeded",
                    },
                )
            break
        seen += 1
        candidate_source_type = (candidate.source_type or source_type or "").strip().lower()
        # [RECONSTRUCTED] candidate_metadata enhancements from patch at offsets 5301590/6453777
        candidate_metadata = dict(candidate.metadata or {})
        force_full_fetch = bool(candidate_metadata.get("force_full_fetch"))
        exact_body_only = bool(candidate_metadata.get("exact_body_only"))
        require_published_extraction = bool(candidate_metadata.get("require_published_extraction"))
        # Direct-scrape candidates do not have reliable published_at; only enforce strict windows
        # after fetching the article and extracting a real date.
        needs_published_extraction = bool(
            require_published_extraction
            or (strict_window and candidate_source_type == "scrape")
            or (strict_window and candidate_source_type == "internal_search" and not candidate.published_at)
        )
        # [END RECONSTRUCTED]
        if not needs_published_extraction and not is_recent_enough(candidate.published_at, date_from=date_from, date_to=date_to):
            emit_candidate(
                candidate=candidate,
                status="skipped",
                reason="outside_date_window",
                final_url=candidate.url,
                hits_for_candidate=[],
                title_value=clean_title(candidate.title or ""),
                published_value=candidate.published_at,
                stage="date_filter",
            )
            continue
        # [RECONSTRUCTED] exact_body_only handling from patch at offset 6453777
        searchable = "" if exact_body_only else " ".join([candidate.title or "", candidate.snippet or ""])
        hits = [] if exact_body_only else matcher.find_hits(searchable)
        hits_from_preview = bool(hits)
        # [END RECONSTRUCTED]
        full_text = ""
        raw_html = ""
        final_url = candidate.url
        extracted_title = candidate.title or ""
        published_at = candidate.published_at
        extracted_published = ""
        # [RECONSTRUCTED] must_fetch_article from patch at offset 6453777
        must_fetch_article = bool(force_full_fetch or exact_body_only or not hits or needs_published_extraction)
        # [END RECONSTRUCTED]

        if must_fetch_article:
            try:
                final_url, raw_html, full_text, extracted_title, extracted_published = fetch_full_article_text(
                    candidate.url,
                    request_timeout=request_timeout,
                )
                if extracted_published:
                    published_at = extracted_published
                # [RECONSTRUCTED] exact_body_only branch from patch at offset 6453777
                if exact_body_only:
                    hits = matcher.find_hits(full_text)
                elif not hits:
                    hits = matcher.find_hits(" ".join([candidate.title, candidate.snippet, full_text]))
                # [END RECONSTRUCTED]
            except Exception as exc:
                exc_text = str(exc)
                if is_google_news_redirect(candidate.url) and (
                    "CERTIFICATE_VERIFY_FAILED" in exc_text or "certificate verify failed" in exc_text.lower()
                ):
                    emit_candidate(
                        candidate=candidate,
                        status="skipped",
                        reason="google_redirect_unresolved_ssl",
                        final_url=final_url,
                        hits_for_candidate=[],
                        stage="fetch",
                    )
                    continue
                errors.append(f"fetch_fail:{candidate.url}:{exc_text}")
                emit_candidate(
                    candidate=candidate,
                    status="skipped",
                    reason=f"fetch_fail:{exc_text}",
                    final_url=final_url,
                    hits_for_candidate=[],
                    stage="fetch",
                )
                continue

        if needs_published_extraction and not published_at:
            emit_candidate(
                candidate=candidate,
                status="skipped",
                reason="missing_published_at",
                final_url=final_url,
                hits_for_candidate=hits,
                title_value=clean_title(candidate.title or extracted_title or ""),
                published_value=published_at,
                stage="date_extraction",
            )
            continue

        if not hits:
            emit_candidate(
                candidate=candidate,
                status="skipped",
                reason="no_match_exact_name",
                final_url=final_url,
                hits_for_candidate=[],
                stage="exact_match",
            )
            continue

        # [RECONSTRUCTED] force_full_fetch/exact_body_only guard from patch at offset 6453777
        if (force_full_fetch or exact_body_only) and not str(full_text or "").strip():
            emit_candidate(
                candidate=candidate,
                status="skipped",
                reason="missing_body",
                final_url=final_url,
                hits_for_candidate=hits,
                title_value=clean_title(candidate.title or extracted_title or ""),
                published_value=published_at,
                stage="body_fetch",
            )
            continue
        # [END RECONSTRUCTED]

        should_archive_full_text = options.archive_full_text and (time.monotonic() - started_at) <= archive_cutoff
        if not full_text and should_archive_full_text:
            try:
                final_url, raw_html, full_text, extracted_title, extracted_published = fetch_full_article_text(
                    candidate.url,
                    request_timeout=request_timeout,
                )
                if extracted_published:
                    published_at = extracted_published
            except Exception:
                full_text = candidate.snippet or candidate.title
                raw_html = ""
        elif not full_text:
            full_text = candidate.snippet or candidate.title
            raw_html = ""

        title_for_article = (candidate.title or extracted_title or "").strip()
        title_for_article = clean_title(title_for_article)
        summary = summarize_text(full_text or candidate.snippet or title_for_article)
        combined_text = " ".join([candidate.title or "", candidate.snippet or "", full_text or "", summary or ""])
        if not passes_forced_terms(combined_text, forced_terms, forced_mode):
            emit_candidate(
                candidate=candidate,
                status="skipped",
                reason="forced_terms_not_matched",
                final_url=final_url,
                hits_for_candidate=hits,
                title_value=title_for_article,
                published_value=published_at,
                summary_value=summary,
                stage="forced_terms",
            )
            if progress_callback and (seen == 1 or seen % 5 == 0):
                progress_callback(
                    "source_progress",
                    {
                        "source_name": source_name,
                        "source_type": source_type,
                        "candidates_seen": seen,
                        "articles_inserted": inserted,
                        "mentions_inserted": mentions_inserted,
                        "stories_touched": stories_touched,
                    },
                )
            continue
        if not is_recent_enough(published_at, date_from=date_from, date_to=date_to):
            emit_candidate(
                candidate=candidate,
                status="skipped",
                reason="outside_date_window",
                final_url=final_url,
                hits_for_candidate=hits,
                title_value=title_for_article,
                published_value=published_at,
                summary_value=summary,
                stage="date_filter",
            )
            if progress_callback and (seen == 1 or seen % 5 == 0):
                progress_callback(
                    "source_progress",
                    {
                        "source_name": source_name,
                        "source_type": source_type,
                        "candidates_seen": seen,
                        "articles_inserted": inserted,
                        "mentions_inserted": mentions_inserted,
                        "stories_touched": stories_touched,
                    },
                )
            continue
        if is_bad_article_quality(
            title_for_article,
            summary,
            final_url,
            allow_short_summary=hits_from_preview,
        ):
            emit_candidate(
                candidate=candidate,
                status="skipped",
                reason="low_article_quality",
                final_url=final_url,
                hits_for_candidate=hits,
                title_value=title_for_article,
                published_value=published_at,
                summary_value=summary,
                stage="quality_filter",
            )
            if progress_callback and (seen == 1 or seen % 5 == 0):
                progress_callback(
                    "source_progress",
                    {
                        "source_name": source_name,
                        "source_type": source_type,
                        "candidates_seen": seen,
                        "articles_inserted": inserted,
                        "mentions_inserted": mentions_inserted,
                        "stories_touched": stories_touched,
                    },
                )
            continue

        sentiment = infer_sentiment(" ".join([candidate.title, candidate.snippet, full_text[:2500]]))
        mention_payload = []
        seen_targets: set[str] = set()
        for h in hits:
            if h.target_key in seen_targets:
                continue
            seen_targets.add(h.target_key)
            mention_payload.append(
                {
                    "target_key": h.target_key,
                    "target_name": h.target_name,
                    "keyword_matched": h.keyword_matched,
                    "sentiment": sentiment,
                    "sentiment_reason": "lexical_heuristic",
                    "context": "",
                }
            )
        if not mention_payload:
            emit_candidate(
                candidate=candidate,
                status="skipped",
                reason="no_mentions_after_dedup",
                final_url=final_url,
                hits_for_candidate=hits,
                title_value=title_for_article,
                published_value=published_at,
                summary_value=summary,
                stage="mention_dedup",
            )
            continue

        article_id, is_new = db.insert_article_if_new(
            url=final_url,
            title=(title_for_article or "(sem titulo)")[:500],
            source_name=candidate.source_name,
            source_type=candidate.source_type,
            published_at=published_at,
            snippet=(candidate.snippet or "")[:3000],
            full_text=full_text[:60000],
            raw_html=raw_html[:120000],
            summary=summary,
            metadata_json=json.dumps(candidate.metadata or {}, ensure_ascii=False),
        )
        if not is_new:
            emit_candidate(
                candidate=candidate,
                status="duplicate",
                reason="already_in_database",
                final_url=final_url,
                hits_for_candidate=hits,
                title_value=title_for_article,
                published_value=published_at,
                summary_value=summary,
                stage="stored",
            )
            if progress_callback and (seen == 1 or seen % 5 == 0):
                progress_callback(
                    "source_progress",
                    {
                        "source_name": source_name,
                        "source_type": source_type,
                        "candidates_seen": seen,
                        "articles_inserted": inserted,
                        "mentions_inserted": mentions_inserted,
                        "stories_touched": stories_touched,
                    },
                )
            continue

        db.insert_mentions(article_id, mention_payload)
        mentions_inserted += len(mention_payload)
        inserted += 1
        target_keys = sorted({h.target_key for h in hits})
        create_or_update_story(
            db,
            article_id=article_id,
            article_title=title_for_article or summary or "Historia",
            article_summary=summary,
            source_name=source_name,
            target_keys=target_keys,
        )
        stories_touched += 1
        emit_candidate(
            candidate=candidate,
            status="selected",
            reason="saved",
            final_url=final_url,
            hits_for_candidate=hits,
            title_value=title_for_article,
            published_value=published_at,
            summary_value=summary,
            stage="stored",
        )
        if progress_callback and (seen == 1 or seen % 3 == 0):
            progress_callback(
                "source_progress",
                {
                    "source_name": source_name,
                    "source_type": source_type,
                    "candidates_seen": seen,
                    "articles_inserted": inserted,
                    "mentions_inserted": mentions_inserted,
                    "stories_touched": stories_touched,
                },
            )

    result = IngestionResult(
        source_name=source_name,
        source_type=source_type,
        candidates_seen=seen,
        articles_inserted=inserted,
        mentions_inserted=mentions_inserted,
        stories_touched=stories_touched,
        errors=errors,
    )
    if progress_callback:
        progress_callback(
            "source_complete",
            {
                "source_name": source_name,
                "source_type": source_type,
                "candidates_seen": seen,
                "articles_inserted": inserted,
                "mentions_inserted": mentions_inserted,
                "stories_touched": stories_touched,
                "errors": errors[:3],
            },
        )
    return result


def run_ingestion(
    collector: str = "all",
    options: IngestionOptions | None = None,
    progress_callback: ProgressCallback | None = None,
) -> list[IngestionResult]:
    options = options or IngestionOptions()
    targets = get_active_targets()
    plans: list[tuple[str, str, list[CandidateArticle]]] = []
    max_candidates = max(1, int(options.max_candidates_per_source))
    # Backfill mode needs deeper pagination than the old hard cap of 30.
    if options.custom_query.strip():
        per_feed_limit = max_candidates
        per_query_limit = max_candidates
        per_target_limit = max_candidates
        per_wp_limit = max_candidates
    else:
        per_feed_limit = max(10, min(120, max_candidates // 2))
        per_query_limit = max(10, min(120, max_candidates // 2))
        per_target_limit = max(10, min(80, max_candidates // 3))
        per_wp_limit = max(10, min(120, max_candidates // 2))
    request_timeout = max(3, int(options.request_timeout_seconds))

    if collector in {"all", "rss"}:
        rss_candidates = collect_rss(
            limit_per_feed=per_feed_limit,
            request_timeout=request_timeout,
            date_from=options.date_from,
            date_to=options.date_to,
        )
        plans.append(("RSS", "rss", rss_candidates))
        if progress_callback:
            progress_callback(
                "source_collected",
                {"source_name": "RSS", "source_type": "rss", "candidates_total": len(rss_candidates)},
            )
    if collector in {"all", "google_news"}:
        if options.custom_query.strip():
            queries = [options.custom_query]
        else:
            queries = ordered_unique(
                [
                    query
                    for target in targets
                    for query in build_google_queries_for_target(target)
                ]
            )
        google_candidates = collect_google_news(
            queries=queries,
            date_from=options.date_from,
            date_to=options.date_to,
            limit_per_query=per_query_limit,
            request_timeout=request_timeout,
            resolve_timeout=max(2, request_timeout - 2),
        )
        plans.append(("Google News", "google_news", google_candidates))
        if progress_callback:
            progress_callback(
                "source_collected",
                {"source_name": "Google News", "source_type": "google_news", "candidates_total": len(google_candidates)},
            )
    if collector in {"all", "direct_scrape"}:
        direct_candidates: list[CandidateArticle] = []
        if options.custom_query.strip():
            direct_candidates.extend(
                collect_direct_scrape(
                    main_query=options.custom_query.strip(),
                    per_target_limit=per_target_limit,
                    request_timeout=request_timeout,
                )
            )
        else:
            queries = ordered_unique(
                [
                    query
                    for target in targets
                    for query in build_direct_scrape_queries_for_target(target)
                ]
            )
            for query in queries:
                direct_candidates.extend(
                    collect_direct_scrape(
                        main_query=query,
                        per_target_limit=per_target_limit,
                        request_timeout=request_timeout,
                    )
                )
        direct_candidates = dedupe_candidates(direct_candidates)
        plans.append(("Direct Scrape", "scrape", direct_candidates))
        if progress_callback:
            progress_callback(
                "source_collected",
                {"source_name": "Direct Scrape", "source_type": "scrape", "candidates_total": len(direct_candidates)},
            )

    if collector in {"all", "wordpress_api"}:
        wp_queries: list[str]
        if options.custom_query.strip():
            wp_queries = [options.custom_query.strip()]
        else:
            wp_queries = ordered_unique(
                [
                    query
                    for target in targets
                    for query in build_wordpress_queries_for_target(target)
                ]
            )

        for site in WORDPRESS_API_SITES:
            site_name = str(site.get("source_name") or "WordPress").strip() or "WordPress"
            base_url = str(site.get("base_url") or "").strip()
            if not base_url:
                continue

            combined: list[CandidateArticle] = []
            seen_urls: set[str] = set()
            for q in wp_queries:
                if len(combined) >= max(1, per_wp_limit):
                    break
                try:
                    batch = collect_wordpress_api(
                        q,
                        source_name=site_name,
                        base_url=base_url,
                        date_from=options.date_from,
                        date_to=options.date_to,
                        per_site_limit=per_wp_limit,
                        request_timeout=request_timeout,
                    )
                except Exception:
                    batch = []
                for item in batch:
                    if item.url in seen_urls:
                        continue
                    seen_urls.add(item.url)
                    combined.append(item)
                    if len(combined) >= max(1, per_wp_limit):
                        break

            plans.append((site_name, "wordpress_api", combined))
            if progress_callback:
                progress_callback(
                    "source_collected",
                    {"source_name": site_name, "source_type": "wordpress_api", "candidates_total": len(combined)},
                )

    # [RECONSTRUCTED] Internal site search section from patch at offset 5311452
    if collector in {"all", "internal_site_search"} and not options.custom_query.strip():
        target_keys = {str(target.key) for target in targets}
        if "flavio_valle" in target_keys:
            planned_urls = {candidate.url for _, _, batch in plans for candidate in batch if candidate.url}
            per_internal_adapter_limit = max(
                6,
                min(20, max_candidates // max(1, len(FLAVIO_INTERNAL_SEARCH_TARGETS))),
            )
            internal_candidates = collect_internal_site_search(
                queries=FLAVIO_INTERNAL_SEARCH_QUERIES,
                date_from=options.date_from,
                date_to=options.date_to,
                limit_per_adapter=per_internal_adapter_limit,
                max_pages_per_adapter=6,
                request_timeout=request_timeout,
            )
            filtered_internal: list[CandidateArticle] = []
            for item in dedupe_candidates(internal_candidates):
                if item.url in planned_urls:
                    continue
                planned_urls.add(item.url)
                filtered_internal.append(item)
            plans.append(("Internal Site Search", "internal_search", filtered_internal))
            if progress_callback:
                progress_callback(
                    "source_collected",
                    {
                        "source_name": "Internal Site Search",
                        "source_type": "internal_search",
                        "candidates_total": len(filtered_internal),
                    },
                )
    # [END RECONSTRUCTED]

    # Sitemap daily collectors (Globo family, CBN, Veja Rio)
    if collector in {"all", "sitemap_daily"}:
        sitemap_queries = [options.custom_query.strip()] if options.custom_query.strip() else list(FLAVIO_INTERNAL_SEARCH_QUERIES)
        planned_urls = {candidate.url for _, _, batch in plans for candidate in batch if candidate.url}
        sitemap_candidates = collect_sitemap_daily(
            queries=sitemap_queries,
            date_from=options.date_from,
            date_to=options.date_to,
            limit_per_source=max_candidates,
            request_timeout=request_timeout,
        )
        filtered_sitemap = [c for c in dedupe_candidates(sitemap_candidates) if c.url not in planned_urls]
        for c in filtered_sitemap:
            planned_urls.add(c.url)
        plans.append(("Sitemap Daily", "sitemap_daily", filtered_sitemap))
        if progress_callback:
            progress_callback("source_collected", {"source_name": "Sitemap Daily", "source_type": "sitemap_daily", "candidates_total": len(filtered_sitemap)})

    # Veja Rio archive collector
    if collector in {"all", "vejario_archive"}:
        planned_urls = {candidate.url for _, _, batch in plans for candidate in batch if candidate.url}
        vejario_candidates = collect_vejario_archive(
            date_from=options.date_from,
            date_to=options.date_to,
            limit_per_target=max(10, max_candidates // 2),
            request_timeout=request_timeout,
        )
        filtered_vejario = [c for c in dedupe_candidates(vejario_candidates) if c.url not in planned_urls]
        for c in filtered_vejario:
            planned_urls.add(c.url)
        plans.append(("Veja Rio Archive", "vejario_archive", filtered_vejario))
        if progress_callback:
            progress_callback("source_collected", {"source_name": "Veja Rio Archive", "source_type": "vejario_archive", "candidates_total": len(filtered_vejario)})

    # Camara Rio archive collector
    if collector in {"all", "camara_archive"}:
        planned_urls = {candidate.url for _, _, batch in plans for candidate in batch if candidate.url}
        camara_candidates = collect_camara_archive(
            date_from=options.date_from,
            date_to=options.date_to,
            limit_total=max(10, max_candidates // 2),
            request_timeout=request_timeout,
        )
        filtered_camara = [c for c in dedupe_candidates(camara_candidates) if c.url not in planned_urls]
        for c in filtered_camara:
            planned_urls.add(c.url)
        plans.append(("Camara Rio Archive", "camara_archive", filtered_camara))
        if progress_callback:
            progress_callback("source_collected", {"source_name": "Camara Rio Archive", "source_type": "camara_archive", "candidates_total": len(filtered_camara)})

    results: list[IngestionResult] = []
    if progress_callback:
        progress_callback(
            "run_started",
            {
                "collector": collector,
                "sources_total": len(plans),
                "candidates_total": sum(len(p[2]) for p in plans),
            },
        )
    for source_name, source_type, candidates in plans:
        # [RECONSTRUCTED] source_options from patch at offset 5312705
        source_options = options
        if source_type == "internal_search":
            source_options = replace(options, target_keys=["flavio_valle"], archive_full_text=True)
        # [END RECONSTRUCTED]
        results.append(
            process_candidates(
                source_name,
                source_type,
                candidates,
                options=source_options,
                progress_callback=progress_callback,
            )
        )
    if progress_callback:
        progress_callback(
            "run_complete",
            {
                "sources_total": len(plans),
                "articles_inserted": sum(r.articles_inserted for r in results),
                "mentions_inserted": sum(r.mentions_inserted for r in results),
                "stories_touched": sum(r.stories_touched for r in results),
            },
        )
    return results
