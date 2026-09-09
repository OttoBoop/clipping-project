from contextlib import contextmanager
import json

import pytest

from tools import political_static_export as export


TARGETS = [{"key": "eduardo_paes", "label": "Eduardo Paes", "primary": True}]
ROSTER = [{**row, "political_roster_version": "rio_2026_v1"} for row in TARGETS]


def row(article_id=1, story_id=1):
    return {"id": article_id, "story_id": story_id, "canonical_url": f"https://example.com/article/{article_id}",
            "title": "Eduardo Paes participa de reunião", "source_name": "Fonte pública", "source_key": "fixture",
            "published_at": "2026-06-01T12:00:00-03:00", "date_status": "page_verified",
            "body_status": "body_extracted", "snippet": "Trecho público da reportagem.", "summary": "",
            "target_keys": ["eduardo_paes"], "text_object_key": f"body/{article_id}", "content_hash": "fixture-hash",
            "classifications": [{"target_key": "eduardo_paes", "payload": {"target_sentiment": "neutral", "categories": ["Política"]}},
                                {"target_key": "private_target", "payload": {"categories": ["Privado"]}}]}


class NoTextService:
    def _read_text(self, *args):
        pytest.fail("metadata export must not download full text")


def test_target_selection_is_explicit_known_and_limited():
    assert export.scoped_targets(["eduardo_paes", "eduardo_paes"], ROSTER) == TARGETS
    with pytest.raises(ValueError):
        export.scoped_targets([], ROSTER)
    with pytest.raises(ValueError):
        export.scoped_targets(["private_target"], ROSTER)
    with pytest.raises(ValueError):
        export.scoped_targets(["shakira"], [*ROSTER, {"key": "shakira", "label": "Shakira"}])


def test_numeric_namespace_preserves_safe_ids_and_disjoint_story_kinds():
    assert export.namespaced_id(1) == -1
    assert export.namespaced_id(1, story=True) == -2
    assert export.namespaced_id(1, story=True, orphan=True) == -3
    assert abs(export.namespaced_id(export.MAX_SAFE_ID, story=True, orphan=True)) < 2**53
    with pytest.raises(ValueError):
        export.namespaced_id(export.MAX_SAFE_ID + 1)


def test_bundle_schema_preserves_scope_associations_classifications_and_unknown_dates():
    article = row()
    article["published_at"] = None
    article["target_keys"].append("private_target")
    payload = export.page_payload([article, row(2)], TARGETS, page_number=1, generated_at="fixture", text_keys={})
    story = payload["stories"][0]
    assert story["politicalStoryId"] == 1
    assert story["articleCount"] == 2
    assert story["targetKeys"] == ["eduardo_paes"]
    assert payload["targets"][0]["articleCount"] == 2
    public = story["articles"][0]
    assert public["publishedAt"] == ""
    assert "desconhecida" in public["publishedDisplay"]
    assert public["rawTextKey"] is None
    assert public["summaryLabel"] != "Texto completo"
    assert len(public["classifications"]) == 1
    assert public["classifications"][0]["article_id"] == public["articleId"]
    assert public["classifications"][0]["categories"] == ["Política"]
    assert "private_target" not in json.dumps(payload)


def test_defensive_scope_filter_rejects_outside_rows():
    article = row()
    article["target_keys"] = ["private_target"]
    with pytest.raises(ValueError, match="outside explicit"):
        export.article_record(article, ["eduardo_paes"])


def test_streams_individual_pages_and_preserves_story_identity_across_pages(monkeypatch, tmp_path):
    output = tmp_path / "new-snapshot"
    def batches(*args, **kwargs):
        yield [row(i) for i in range(1, 101)]
        assert (output / "assets/page-000001.json").exists()  # page persisted before next batch is requested
        yield [row(101), row(102, 2)]
    monkeypatch.setattr(export, "iter_batches", batches)
    manifest = export.export_snapshot(NoTextService(), output, TARGETS)
    assert manifest["article_count"] == 102
    assert manifest["page_count"] == 2
    assert manifest["story_count"] == 2
    assert manifest["text_count"] == 0
    assert manifest["uploaded"] is False
    first = json.loads((output / "assets/page-000001.json").read_text())
    second = json.loads((output / "assets/page-000002.json").read_text())
    assert first["stories"][0]["storyIdInt"] == second["stories"][0]["storyIdInt"]
    assert len(first["stories"][0]["articles"]) == 100
    shell = (output / "page-000001.html").read_text()
    assert 'data-clipping-static="1"' in shell
    assert 'data-clipping-api-url=""' in shell
    assert 'href="page-000002.html"' in shell
    assert "Filtros e busca se aplicam" in first["meta"]["scopeText"]


def test_existing_directory_and_assets_are_never_overwritten(tmp_path):
    (tmp_path / "sentinel.txt").write_text("existing")
    with pytest.raises(FileExistsError):
        export.export_snapshot(NoTextService(), tmp_path, TARGETS)
    assert (tmp_path / "sentinel.txt").read_text() == "existing"
    assert not (tmp_path / "assets").exists()


def test_multi_story_article_across_pages_reuses_body_and_counts_unique_articles(monkeypatch, tmp_path):
    first, repeated = row(1, 1), row(1, 2)
    first["first_story_association"] = True
    repeated["first_story_association"] = False
    monkeypatch.setattr(export, "iter_batches", lambda *a, **k: iter([[first], [repeated]]))
    reads = []
    class Service:
        def _read_text(self, *args):
            reads.append(args)
            return "Texto integral compartilhado entre histórias."
    output = tmp_path / "multi-story"
    manifest = export.export_snapshot(Service(), output, TARGETS, include_text=True)
    assert manifest["article_count"] == 1
    assert manifest["association_count"] == 2
    assert manifest["story_count"] == 2
    assert manifest["text_count"] == len(reads) == 1
    assert manifest["text_failures"] == 0
    for number in (1, 2):
        page = json.loads((output / f"assets/page-{number:06d}.json").read_text())
        assert page["stories"][0]["articles"][0]["rawTextKey"] == "political-article-1"


def test_optional_text_is_saved_separately_and_failures_remain_visible(monkeypatch, tmp_path):
    monkeypatch.setattr(export, "iter_batches", lambda *args, **kwargs: iter([[row(1), row(2)]]))
    class TextService:
        def _read_text(self, key, digest):
            if key == "body/2":
                raise OSError("do not reveal credentials or object URLs")
            return "Texto integral preservado."
    output = tmp_path / "with-text"
    manifest = export.export_snapshot(TextService(), output, TARGETS, include_text=True)
    assert manifest["status"] == "complete_with_text_gaps"
    assert manifest["text_count"] == manifest["text_failures"] == 1
    assert json.loads((output / "texts/political-article-1.json").read_text()) == "Texto integral preservado."
    payload = json.loads((output / "assets/page-000001.json").read_text())
    assert payload["stories"][0]["articles"][0]["rawTextKey"] == "political-article-1"
    assert payload["stories"][0]["articles"][1]["rawTextKey"] is None
    assert "credentials" not in (output / "text-failures.jsonl").read_text()
    javascript = (output / "assets/clipping.js").read_text()
    assert "function ensureRawTexts(rawKey)" in javascript
    assert "rawUrl.replace('{key}', encodeURIComponent(rawKey))" in javascript


def test_failed_export_has_explicit_status(monkeypatch, tmp_path):
    def failed(*args, **kwargs):
        raise ConnectionError("unavailable")
        yield
    monkeypatch.setattr(export, "iter_batches", failed)
    with pytest.raises(ConnectionError):
        export.export_snapshot(NoTextService(), tmp_path / "failed", TARGETS)
    assert json.loads((tmp_path / "failed/manifest.json").read_text())["status"] == "failed"


def test_database_cursor_is_read_only_batched_and_classifications_are_scoped():
    statements, fetched = [], []
    class Cursor:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, sql, params): statements.append((sql, params))
        def fetchmany(self, size):
            fetched.append(size)
            return [row()] if len(fetched) == 1 else []
    class Connection:
        def execute(self, sql, params=None):
            statements.append((sql, params))
            return self
        def fetchall(self): return []
        def cursor(self, **kwargs):
            assert kwargs["name"] == "political_static_export"
            return Cursor()
    class Service:
        def _article_filters(self, allowed, **filters):
            assert allowed == ["eduardo_paes"]
            return "a.id > %s", [0]
        @contextmanager
        def _connect(self): yield Connection()
    batches = list(export.iter_batches(Service(), ["eduardo_paes"]))
    assert len(batches) == 1
    assert fetched == [100, 100]
    assert "READ ONLY" in statements[0][0]
    assert "political_classifications" in statements[-1][0]
    assert statements[-1][1] == ([1], ["eduardo_paes"])
    assert not any(sql.lstrip().startswith(("INSERT", "UPDATE", "CREATE", "DELETE")) for sql, _ in statements)
