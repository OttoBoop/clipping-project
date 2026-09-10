"""Diário's advertised public Mostrar Mais archive, one bounded page per step."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin, urlparse

from . import political_discovery as discovery

ARCHIVE_URL = "https://www.diariodorio.com/ultimas-noticias"
EMPTY_MARKER = "<!-- PORTAL:FINISH -->"
CURSOR_VERSION = 1
MAX_PAGES = 1000
MAX_HTML_CHARS = 2 * 1024 * 1024
MAX_CARDS = 500
HOSTS = {"diariodorio.com", "www.diariodorio.com"}


def _day(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


class ArchiveCards(HTMLParser):
    """Associate each primary card's heading and visible day, ignoring sidebars."""
    def __init__(self, *, initial=False):
        super().__init__(convert_charrefs=True)
        self.initial = initial
        self.stack = []
        self.root_found = not initial
        self.raw_count = 0
        self.rows = []
        self.card = None
        self.card_depth = None
        self.heading_depth = None
        self.buttons = []

    def handle_starttag(self, tag, attrs):
        attrs = {key: value or "" for key, value in attrs}
        classes = set(attrs.get("class", "").split())
        blocked = (bool(self.stack) and self.stack[-1][2]) or tag in {"aside", "footer", "nav", "script", "style", "header"}
        inside = not self.initial or bool(self.stack and self.stack[-1][1]) or "td-ss-main-content" in classes
        main = bool(self.stack and self.stack[-1][3]) or "td-main-content" in classes
        if inside and not blocked:
            self.root_found = True
            if "td_module_wrap" in classes:
                self.raw_count += 1
                if self.card is None and self.raw_count <= MAX_CARDS:
                    self.card = {"url": "", "title": "", "days": []}
                    self.card_depth = len(self.stack)
            if self.card is not None:
                if tag == "h3" and {"entry-title", "td-module-title"} <= classes:
                    self.heading_depth = len(self.stack)
                if tag == "a" and self.heading_depth is not None and not self.card["url"]:
                    self.card["url"] = attrs.get("href", "")
                if tag == "time" and "td-module-date" in classes:
                    self.card["days"].append(attrs.get("datetime", ""))
        # The actual Mostrar Mais control is a sibling of td-ss-main-content,
        # within td-main-content; cards themselves remain scoped to the former.
        if (inside or main) and not blocked and tag == "a" and "ajax-load-more" in classes:
            self.buttons.append(attrs)
        if tag not in discovery._VOID_TAGS:
            self.stack.append((tag, inside, blocked, main))

    def handle_data(self, data):
        if self.card is not None and self.heading_depth is not None and self.stack and not self.stack[-1][2]:
            self.card["title"] += data

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in discovery._VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] != tag:
                continue
            if self.heading_depth is not None and index <= self.heading_depth:
                self.heading_depth = None
            if self.card_depth is not None and index <= self.card_depth:
                self.card["title"] = " ".join(self.card["title"].split())
                self.rows.append(self.card)
                self.card = self.card_depth = None
            del self.stack[index:]
            break


def _cursor(task):
    raw = task.get("cursor") or {}
    if not isinstance(raw, dict):
        raise ValueError("cursor must be an object")
    page = raw.get("page", 1)
    if type(page) is not int or not 1 <= page <= MAX_PAGES:
        raise ValueError("invalid archive page")
    seen = raw.get("seen_pages", [])
    if not isinstance(seen, list) or len(seen) != page - 1 or any(
        not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value) for value in seen
    ):
        raise ValueError("missing archive page evidence")
    if page > 1:
        if raw.get("version") != CURSOR_VERSION or not re.fullmatch(r"[0-9]{1,12}", str(raw.get("section_id", ""))):
            raise ValueError("missing public pagination configuration")
        if type(raw.get("page_size")) is not int or not 1 <= raw["page_size"] <= MAX_CARDS:
            raise ValueError("invalid archive page size")
        for name in ("ordered_pages", "older_pages", "unknown_dates", "parse_gaps"):
            if type(raw.get(name)) is not int or not 0 <= raw[name] <= MAX_PAGES * MAX_CARDS:
                raise ValueError("missing archive chronology evidence")
        if not isinstance(raw.get("chronology_gap"), bool):
            raise ValueError("missing archive chronology state")
        if not raw["chronology_gap"] and (not _day(raw.get("previous_oldest")) or raw["ordered_pages"] != page - 1):
            raise ValueError("missing uninterrupted archive ordering")
    return raw, page, list(seen)


def _gaps(state):
    reasons = []
    if state.get("parse_gaps"):
        reasons.append(f"unparsed_cards:{state['parse_gaps']}")
    if state.get("unknown_dates"):
        reasons.append(f"unknown_card_dates:{state['unknown_dates']}")
    if state.get("chronology_gap"):
        reasons.append("chronology_unproven")
    return "diario_archive_" + ";".join(reasons) if reasons else ""


def discover_archive(task, source, fetch):
    archive_url = task.get("url") or ARCHIVE_URL
    parsed_url = urlparse(archive_url)
    if source.get("key") != "diario_do_rio" or parsed_url.scheme != "https" or parsed_url.hostname not in HOSTS or parsed_url.path != "/ultimas-noticias" or parsed_url.query or parsed_url.fragment or parsed_url.username or parsed_url.port not in {None, 443}:
        return discovery._result(outcome="gap", gap_reason="diario_archive_unrecognized_public_url")
    try:
        cursor, page, seen = _cursor(task)
    except (TypeError, ValueError):
        return discovery._result(outcome="gap", gap_reason="diario_archive_invalid_cursor")
    cap = min(MAX_PAGES, max(1, int(source.get("archive_max_pages") or MAX_PAGES)))
    if page > cap:
        return discovery._result(outcome="gap", gap_reason="diario_archive_page_cap")
    url = archive_url if page == 1 else urljoin(archive_url, "/index.php") + "?" + urlencode({
        "id": "/readMore.php", "cd_sesit": cursor["section_id"], "p": page})
    raw = discovery._get(fetch, url).text
    if len(raw) > MAX_HTML_CHARS:
        return discovery._result(outcome="gap", gap_reason="diario_archive_response_too_large")
    if page > 1 and raw.strip() == EMPTY_MARKER:
        reason = _gaps(cursor)
        return discovery._result(outcome="gap" if reason else "complete", gap_reason=reason)
    if page > 1 and (not raw.rstrip().endswith(EMPTY_MARKER) or re.search(r"<!doctype|<html\b|<body\b", raw, re.I)):
        return discovery._result(outcome="gap", gap_reason="diario_archive_fragment_unrecognized")
    parser = ArchiveCards(initial=page == 1)
    parser.feed(raw)
    if not parser.root_found or not parser.raw_count:
        return discovery._result(outcome="gap", gap_reason="diario_archive_markup_or_exhaustion_unconfirmed")
    if page == 1:
        if len(parser.buttons) != 1:
            return discovery._result(outcome="gap", raw_count=parser.raw_count, gap_reason="diario_archive_public_button_missing")
        button = parser.buttons[0]
        if button.get("data-type") != "listao" or button.get("data-page") != "2" or not re.fullmatch(r"[0-9]{1,12}", button.get("data-sesit", "")):
            return discovery._result(outcome="gap", raw_count=parser.raw_count, gap_reason="diario_archive_public_button_changed")
        section = button["data-sesit"]
    else:
        section = cursor["section_id"]

    rows, page_dates, urls = [], [], set()
    parse_gaps = max(0, parser.raw_count - len(parser.rows))
    unknown_dates = 0
    for row in parser.rows:
        article_url = urljoin(archive_url, row["url"])
        if not row["title"] or not discovery._allowed_url(article_url, source, article=True):
            parse_gaps += 1
            continue
        article_url = discovery.canonicalize_url(article_url)
        if article_url in urls:
            parse_gaps += 1
            continue
        urls.add(article_url)
        published_day = _day(row["days"][0]) if len(row["days"]) == 1 else None
        page_dates.append(published_day)
        unknown_dates += published_day is None
        rows.append((article_url, row["title"], published_day))

    fingerprint = hashlib.sha256(json.dumps(sorted(urls), separators=(",", ":")).encode()).hexdigest()
    start, end = date.fromisoformat(task["date_from"]), date.fromisoformat(task["date_to"])
    candidates = [discovery._candidate(source, url, title, metadata={
        "collection_mode": "public_latest_archive", "archive_url": archive_url,
        "archive_page": page, "archive_section_id": section,
        "archive_card_day": day.isoformat() if day else "", "date_basis": "archive_visible_day_hint",
        "needs_date_review": True,
    }) for url, title, day in rows if day is None or start <= day <= end]
    # Card days are traversal hints. No midnight/noon publication timestamp is
    # synthesized; the fetch worker verifies the actual article-page date.
    if parser.raw_count > MAX_CARDS:
        return discovery._result(candidates, outcome="gap", raw_count=parser.raw_count, gap_reason="diario_archive_card_cap")
    if fingerprint in seen:
        return discovery._result(candidates, outcome="gap", raw_count=parser.raw_count, gap_reason="diario_archive_repeated_page")
    if page > 1 and parser.raw_count > cursor["page_size"]:
        return discovery._result(candidates, outcome="gap", raw_count=parser.raw_count, gap_reason="diario_archive_page_size_changed")

    fully_dated = not parse_gaps and bool(page_dates) and all(day is not None for day in page_dates)
    ordered = fully_dated and page_dates == sorted(page_dates, reverse=True)
    previous = _day(cursor.get("previous_oldest"))
    boundary_ordered = page == 1 or (previous is not None and fully_dated and max(page_dates) <= previous)
    chronological = ordered and boundary_ordered
    all_older = fully_dated and max(page_dates) < start
    state = {
        "version": CURSOR_VERSION, "page": page + 1, "section_id": section,
        "page_size": cursor.get("page_size", parser.raw_count), "seen_pages": seen + [fingerprint],
        "previous_oldest": min(page_dates).isoformat() if fully_dated else "",
        "ordered_pages": int(cursor.get("ordered_pages", 0)) + 1 if chronological else 0,
        "older_pages": int(cursor.get("older_pages", 0)) + 1 if chronological and all_older else 0,
        "unknown_dates": int(cursor.get("unknown_dates", 0)) + unknown_dates,
        "parse_gaps": int(cursor.get("parse_gaps", 0)) + parse_gaps,
        "chronology_gap": bool(cursor.get("chronology_gap")) or not chronological,
    }
    reason = _gaps(state)
    if state["older_pages"] >= 2 and not reason:
        return discovery._result(raw_count=parser.raw_count, next_cursor=state, outcome="complete")
    older_cap = min(MAX_PAGES, max(10, int(source.get("archive_older_page_cap") or 10)))
    if reason and state["older_pages"] >= older_cap:
        # A sticky earlier ordering gap must not send every narrow run through
        # the entire archive. This is an explicit coverage limit, not proof of
        # exhaustion; the independent domain/name searches remain scheduled.
        return discovery._result(candidates, raw_count=parser.raw_count, next_cursor=state, outcome="gap",
                                 gap_reason=reason + f";older_page_budget:{older_cap}")
    if page >= cap:
        return discovery._result(candidates, raw_count=parser.raw_count, next_cursor=state, outcome="gap",
                                 gap_reason="diario_archive_page_cap" + (";" + reason if reason else ""))
    return discovery._result(candidates, next_cursor=state, raw_count=parser.raw_count, gap_reason=reason)
