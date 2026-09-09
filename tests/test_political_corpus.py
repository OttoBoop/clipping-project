from __future__ import annotations

import gzip
import hashlib
import threading
from datetime import datetime, timezone

import pytest

from web_app.political_corpus import (
    FetchProblem, PoliticalAccessDenied, PoliticalCorpusService, _date_window,
    _confirmed_publisher, _scope, decode_cursor, encode_cursor, match_targets, parse_date,
)
from tools.political_worker import worker_loop


def test_authorization_is_explicit_and_denies_cross_target_requests():
    with pytest.raises(PoliticalAccessDenied):
        _scope([])
    with pytest.raises(PoliticalAccessDenied):
        _scope(["paes"], ["private"])
    assert _scope(["paes", "duarte"], ["duarte"]) == ["duarte"]


def test_dates_keep_unknown_and_respect_local_day():
    assert parse_date("invalid") is None
    assert parse_date("") is None
    assert parse_date("2026-06-01T23:59:00").utcoffset().total_seconds() == -10800
    with pytest.raises(ValueError):
        _date_window({"date_from": "2026-05-31", "date_to": "2026-06-01"})


def test_cursor_is_round_trippable_and_rejects_malformed_input():
    stamp = datetime(2026, 6, 2, tzinfo=timezone.utc)
    assert decode_cursor(encode_cursor(stamp, 32)) == (stamp, 32)
    for value in ["nonsense", "a" * 1000, encode_cursor(stamp, 0)]:
        with pytest.raises(ValueError):
            decode_cursor(value)


def test_body_only_matches_and_ambiguous_aliases_share_roster_rules():
    snapshots = [
        {"key": "eduardo_paes", "display_name": "Eduardo Paes", "keywords": ["Eduardo Paes"]},
        {"key": "renan_ferreirinha", "display_name": "Renan Ferreirinha", "keywords": ["Renan Ferreirinha"]},
    ]
    hits = match_targets(snapshots, "Acordo reúne deputados", "O texto cita Renan Ferreirinha e Eduardo Paes.")
    assert {item["target_key"] for item in hits} == {"eduardo_paes", "renan_ferreirinha"}
    assert match_targets(snapshots, "Eduardo Paesinho", "") == []


def test_content_addressing_is_deterministic_and_checks_integrity():
    class Store:
        enabled = True
        prefix = "test"
        objects = {}
        def upload_bytes(self, data, key, content_type):
            self.objects[key] = data
            return True
        def read_political_object(self, key):
            return self.objects[key]
    store = Store()
    service = PoliticalCorpusService(store=store)
    digest, key = service._store_text("Texto de notícia.")
    assert digest == hashlib.sha256("Texto de notícia.".encode()).hexdigest()
    assert service._store_text("Texto de notícia.") == (digest, key)
    assert len(store.objects) == 1
    assert service._read_text(key, digest) == "Texto de notícia."
    store.objects[key] = gzip.compress(b"corrupted")
    with pytest.raises(FetchProblem, match="integrity"):
        service._read_text(key, digest)


def test_worker_recovers_after_transient_claim_failure():
    stop = threading.Event()
    class Service:
        claims = 0
        def heartbeat(self, *args, **kwargs): pass
        def claim_task(self, kind, **kwargs):
            self.claims += 1
            if self.claims == 1:
                raise ConnectionError("temporary")
            stop.set()
            return None
    service = Service()
    worker_loop(service, "fetch", "test-worker", stop)
    assert service.claims == 2


def test_unconfigured_status_is_readable_but_no_implicit_target_access(monkeypatch):
    monkeypatch.delenv("POLITICAL_DATABASE_URL", raising=False)
    monkeypatch.delenv("RIO_CORPUS_DATABASE_URL", raising=False)
    service = PoliticalCorpusService()
    assert service.status(allowed_target_keys=["paes"])["configured"] is False
    with pytest.raises(PoliticalAccessDenied):
        service.status(allowed_target_keys=[])


@pytest.mark.parametrize("url,key,name", [
    ("https://g1.globo.com/rj/article", "g1", "G1"),
    ("https://WWW.G1.GLOBO.COM./rj/article", "g1", "G1"),
    ("https://extra.globo.com/article", "extra", "Extra"),
    ("https://g1.globo.com.unrelated.example/article", "publisher:g1.globo.com.unrelated.example", "g1.globo.com.unrelated.example"),
])
def test_publisher_registry_matches_hosts_exactly_and_preserves_discovery_metadata(url, key, name):
    candidate = {"source_key": "google_news", "source_name": "Google News", "metadata": {"query": "Eduardo Paes"}}
    attributed = _confirmed_publisher(candidate, url)
    assert attributed["source_key"] == key and attributed["source_name"] == name
    assert attributed["metadata"]["query"] == "Eduardo Paes"
    assert attributed["metadata"]["publisher_provenance"]["discovery_source_key"] == "google_news"
    assert candidate["source_key"] == "google_news" and candidate["metadata"] == {"query": "Eduardo Paes"}
