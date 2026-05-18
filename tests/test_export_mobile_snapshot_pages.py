import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.database import ClippingDB
from pipeline.matcher import Target
from tools import export_mobile_snapshot
from tools import prepare_wix_clipping_snapshot


def make_args(tmp_path, db_path, *, output_name="index.html", merge_from=""):
    return argparse.Namespace(
        db=str(db_path),
        date_from="",
        date_to="",
        all_stories=True,
        default_target="flavio_valle",
        output=str(tmp_path / output_name),
        merge_from=merge_from,
        remap_incoming_ids_on_merge=False,
    )


def make_prepare_args(tmp_path, db_path):
    return argparse.Namespace(
        db=str(db_path),
        date_from="",
        date_to="",
        all_stories=True,
        default_target="flavio_valle",
        output=str(tmp_path / "canonical.html"),
        merge_from="",
        remap_incoming_ids_on_merge=False,
        current_output=str(tmp_path / "current.html"),
        archive_dir=str(tmp_path / "archive"),
        review_dir=str(tmp_path / "review"),
        skip_screenshots=True,
    )


def seed_story_db(db_path: Path) -> None:
    long_text = "Texto bruto de teste. " * 80
    with ClippingDB(db_path) as db:
        article_id = db.insert_article(
            url="https://example.com/noticia-teste",
            title="Flavio Valle apresenta projeto de teste",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-04-06T12:30:00+00:00",
            snippet="Snippet do artigo de teste.",
            full_text=long_text,
        )
        assert article_id is not None
        db.insert_mention(article_id, "flavio_valle", "Flávio Valle", "Flavio Valle")
        story_id = db.create_story(
            title="Historia teste do bundle",
            summary="Resumo agrupado da historia de teste.",
            temperature=42.0,
            target_keys=["flavio_valle"],
        )
        db.attach_article_to_story(story_id, article_id)
        db.ensure_story_target(story_id, "flavio_valle")


def test_pages_artifact_uses_external_bundle(tmp_path):
    db_path = tmp_path / "clipping.db"
    seed_story_db(db_path)
    args = make_args(tmp_path, db_path)

    artifact = export_mobile_snapshot.build_snapshot_artifact(args)

    html_doc = artifact["html_doc"]
    assert 'data-clipping-data-url="' in html_doc
    assert 'data-clipping-raw-url="' in html_doc
    assert "Rodar atualização" in html_doc
    assert "Progresso compartilhado" in html_doc
    assert "?v=" in html_doc
    assert '<article class="article-card"' not in html_doc
    assert 'data-story-id="' not in html_doc
    assert "Carregando dados do clipping" in html_doc
    assert "Carregar mais notícias" in artifact["js_text"]
    assert "Carregando notícias" in artifact["js_text"]
    assert "hydrateRawDetails" in artifact["js_text"]
    assert "IntersectionObserver" not in artifact["js_text"]


def test_pages_bundle_writes_shell_and_assets(tmp_path):
    db_path = tmp_path / "clipping.db"
    seed_story_db(db_path)
    args = make_args(tmp_path, db_path)

    artifact = export_mobile_snapshot.build_snapshot_artifact(args)
    asset_paths = artifact["asset_paths"]
    export_mobile_snapshot.write_bundle_assets(artifact, asset_paths)
    export_mobile_snapshot.write_shell_html(Path(args.output), artifact["data_payload"], asset_paths)

    assert Path(args.output).exists()
    for key in ("css", "js", "data", "raw"):
        assert asset_paths[key].exists(), f"missing asset: {key}"

    data_payload = json.loads(asset_paths["data"].read_text(encoding="utf-8"))
    assert data_payload["meta"]["totalStories"] == 1
    assert data_payload["meta"]["totalArticles"] == 1
    assert len(data_payload["stories"]) == 1
    assert data_payload["stories"][0]["articles"][0]["rawTextKey"] == "article-1"

    html_doc = Path(args.output).read_text(encoding="utf-8")
    assert 'data-clipping-data-url="index_assets/clipping-data.json?v=' in html_doc
    assert 'data-clipping-raw-url="index_assets/clipping-raw-texts.json?v=' in html_doc
    assert 'href="index_assets/clipping.css?v=' in html_doc
    assert 'src="index_assets/clipping.js?v=' in html_doc


def test_export_bundle_uses_current_dashboard_javascript():
    dashboard_js = (PROJECT_ROOT / "assets" / "clipping.js").read_text(encoding="utf-8")

    assert export_mobile_snapshot.build_pages_javascript() == dashboard_js


def test_dashboard_javascript_preserves_original_target_keys_for_visible_articles():
    dashboard_js = (PROJECT_ROOT / "assets" / "clipping.js").read_text(encoding="utf-8")

    assert "var originalTargetKeys = articleTargetKeys(article, story);" in dashboard_js
    assert "var visibleTargetKeys = originalTargetKeys.slice();" in dashboard_js
    assert "targetKeys: visibleTargetKeys.length ? visibleTargetKeys : originalTargetKeys" in dashboard_js


def test_dashboard_javascript_recomputes_runtime_target_counts_from_payload():
    dashboard_js = (PROJECT_ROOT / "assets" / "clipping.js").read_text(encoding="utf-8")
    body = dashboard_js[
        dashboard_js.index("function mergeRuntimeTargetsIntoPayload") :
        dashboard_js.index("function activeTargetKeysFrom")
    ]

    assert "existing.storyCount = usage.storyCount;" in body
    assert "existing.articleCount = usage.articleCount;" in body
    assert "Math.max(Number(existing.storyCount" not in body
    assert "Math.max(Number(existing.articleCount" not in body


def test_dashboard_javascript_promotes_viewer_filters_when_scope_has_no_primary():
    dashboard_js = (PROJECT_ROOT / "assets" / "clipping.js").read_text(encoding="utf-8")
    body = dashboard_js[
        dashboard_js.index("function renderTargetButtons") :
        dashboard_js.index("function renderStats")
    ]

    assert "if (!primary.length && other.length && !viewerIsAdmin())" in body
    assert "primary = other.slice();" in body
    assert "other = [];" in body


def test_dashboard_javascript_normalizes_initial_payload_counts_before_render():
    dashboard_js = (PROJECT_ROOT / "assets" / "clipping.js").read_text(encoding="utf-8")
    load_body = dashboard_js[
        dashboard_js.index(".then(function (json) {") :
        dashboard_js.index("document.title = (payload.meta")
    ]

    assert "function normalizePayloadCounts()" in dashboard_js
    assert "payload.meta.totalArticles = totalArticles;" in dashboard_js
    assert "recomputeTargetCounts();" in dashboard_js[
        dashboard_js.index("function normalizePayloadCounts") :
        dashboard_js.index("function mergeLiveResultsIntoPayload")
    ]
    assert "normalizePayloadCounts();" in load_body


def test_dashboard_javascript_target_success_copy_mentions_base_atual():
    dashboard_js = (PROJECT_ROOT / "assets" / "clipping.js").read_text(encoding="utf-8")

    assert "Nome extra salvo. Ele já vale para a Base atual e para próximas rodadas." in dashboard_js
    assert "Nome restaurado. Ele já vale para a Base atual e para próximas rodadas." in dashboard_js
    assert "Nome extra salvo e disponível para a próxima rodada." not in dashboard_js


def test_dashboard_javascript_does_not_lock_target_management_during_updates():
    dashboard_js = (PROJECT_ROOT / "assets" / "clipping.js").read_text(encoding="utf-8")
    management_body = dashboard_js[
        dashboard_js.index("function managedTargetForm") :
        dashboard_js.index("function selectedRunTargetKeys")
    ]

    assert "targetActionsLocked" not in management_body
    assert "Aguarde a atualização terminar" not in management_body
    assert "aria-disabled" not in management_body


def test_static_export_marks_bundle_to_skip_api_polling(tmp_path):
    db_path = tmp_path / "clipping.db"
    seed_story_db(db_path)
    args = make_args(tmp_path, db_path)

    artifact = export_mobile_snapshot.build_snapshot_artifact(args)

    assert 'data-clipping-static="1"' in artifact["html_doc"]
    assert "apiAvailable" in artifact["js_text"]


def test_active_targets_without_stories_stay_available_as_filters(monkeypatch, tmp_path):
    db_path = tmp_path / "clipping.db"
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {
                    "key": "flavio_valle",
                    "label": "Flávio Valle",
                    "display_name": "Flávio Valle",
                    "primary": True,
                    "keywords": ["Flávio Valle"],
                },
                {
                    "key": "shakira",
                    "label": "shakira",
                    "display_name": "shakira",
                    "primary": False,
                    "keywords": ["shakira"],
                },
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(export_mobile_snapshot, "TARGETS_PATH", targets_path)
    seed_story_db(db_path)

    artifact = export_mobile_snapshot.build_snapshot_artifact(make_args(tmp_path, db_path))
    payload = artifact["data_payload"]

    assert [row["key"] for row in artifact["target_rows"]] == ["flavio_valle", "shakira"]
    assert [row["key"] for row in payload["targets"]] == ["flavio_valle", "shakira"]
    shakira_row = next(row for row in artifact["target_rows"] if row["key"] == "shakira")
    assert shakira_row["storyCount"] == 0
    assert shakira_row["articleCount"] == 0


def test_secondary_target_stories_are_exported_with_filter(monkeypatch, tmp_path):
    db_path = tmp_path / "clipping.db"
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {
                    "key": "flavio_valle",
                    "label": "Flávio Valle",
                    "display_name": "Flávio Valle",
                    "primary": True,
                    "keywords": ["Flávio Valle"],
                },
                {
                    "key": "shakira",
                    "label": "shakira",
                    "display_name": "shakira",
                    "primary": False,
                    "keywords": ["shakira"],
                },
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(export_mobile_snapshot, "TARGETS_PATH", targets_path)
    with ClippingDB(db_path) as db:
        article_id = db.insert_article(
            url="https://example.com/shakira-rio",
            title="Shakira anuncia show no Rio",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-05-01T12:00:00+00:00",
            snippet="Shakira anuncia show no Rio.",
            full_text="Shakira anuncia show no Rio. Texto completo da materia.",
        )
        assert article_id is not None
        db.insert_mention(article_id, "shakira", "shakira", "shakira")
        story_id = db.create_story(
            title="Shakira anuncia show no Rio",
            summary="Resumo sobre Shakira no Rio.",
            temperature=42.0,
            target_keys=["shakira"],
        )
        db.attach_article_to_story(story_id, article_id)
        db.ensure_story_target(story_id, "shakira")

    artifact = export_mobile_snapshot.build_snapshot_artifact(make_args(tmp_path, db_path))
    payload = artifact["data_payload"]
    shakira_stories = [story for story in payload["stories"] if story["targetKeys"] == ["shakira"]]

    assert "shakira" in [row["key"] for row in artifact["target_rows"]]
    assert "shakira" in [row["key"] for row in payload["targets"]]
    assert len(shakira_stories) == 1
    assert shakira_stories[0]["articles"][0]["targetKeys"] == ["shakira"]


def test_export_counts_articles_per_target_in_mixed_story(monkeypatch, tmp_path):
    db_path = tmp_path / "clipping.db"
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {
                    "key": "flavio_valle",
                    "label": "Flávio Valle",
                    "display_name": "Flávio Valle",
                    "primary": True,
                    "keywords": ["Flávio Valle"],
                },
                {
                    "key": "shakira",
                    "label": "shakira",
                    "display_name": "shakira",
                    "primary": False,
                    "keywords": ["shakira"],
                },
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(export_mobile_snapshot, "TARGETS_PATH", targets_path)
    with ClippingDB(db_path) as db:
        flavio_article = db.insert_article(
            url="https://example.com/flavio-agenda",
            title="Flávio Valle confirma agenda",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-05-01T12:00:00+00:00",
            snippet="Flávio Valle confirma agenda.",
            full_text="Flávio Valle confirma agenda.",
        )
        shakira_article = db.insert_article(
            url="https://example.com/shakira-show",
            title="Shakira anuncia show",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-05-01T13:00:00+00:00",
            snippet="Shakira anuncia show.",
            full_text="Shakira anuncia show.",
        )
        assert flavio_article is not None
        assert shakira_article is not None
        db.insert_mention(flavio_article, "flavio_valle", "Flávio Valle", "Flávio Valle")
        db.insert_mention(shakira_article, "shakira", "shakira", "shakira")
        story_id = db.create_story(
            title="Agenda e show no Rio",
            summary="Resumo misto.",
            temperature=42.0,
            target_keys=["flavio_valle", "shakira"],
        )
        db.attach_article_to_story(story_id, flavio_article)
        db.attach_article_to_story(story_id, shakira_article)
        db.ensure_story_target(story_id, "flavio_valle")
        db.ensure_story_target(story_id, "shakira")

    artifact = export_mobile_snapshot.build_snapshot_artifact(make_args(tmp_path, db_path))
    payload = artifact["data_payload"]
    by_target = {row["key"]: row for row in payload["targets"]}

    assert payload["stories"][0]["articleCount"] == 2
    assert by_target["flavio_valle"]["storyCount"] == 1
    assert by_target["flavio_valle"]["articleCount"] == 1
    assert by_target["shakira"]["storyCount"] == 1
    assert by_target["shakira"]["articleCount"] == 1
    assert payload["meta"]["initialArticleCount"] == 1
    assert export_mobile_snapshot.visibility_stats(payload["stories"], ["shakira"])["articleCount"] == 1


def test_export_filters_misleading_secondary_snippet_when_saved_text_disagrees(monkeypatch, tmp_path):
    db_path = tmp_path / "clipping.db"
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {
                    "key": "flavio_valle",
                    "label": "Flávio Valle",
                    "display_name": "Flávio Valle",
                    "primary": True,
                    "keywords": ["Flávio Valle"],
                },
                {
                    "key": "shakira",
                    "label": "shakira",
                    "display_name": "shakira",
                    "primary": False,
                    "keywords": ["shakira"],
                },
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(export_mobile_snapshot, "TARGETS_PATH", targets_path)
    with ClippingDB(db_path) as db:
        article_id = db.insert_article(
            url="https://example.com/projeto-transicao",
            title="Projeto busca orientar mulheres a lidarem com processos de transicao na vida",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-05-05T14:56:48+00:00",
            snippet="Trecho de busca enganoso cita Shakira em uma lista lateral.",
            full_text="Texto real da materia sobre empreendedorismo, carreira e inteligencia emocional.",
        )
        assert article_id is not None
        db.insert_mention(article_id, "shakira", "shakira", "shakira")
        story_id = db.create_story(
            title="Projeto busca orientar mulheres a lidarem com processos de transicao na vida",
            summary="Resumo real da materia.",
            temperature=42.0,
            target_keys=["shakira"],
        )
        db.attach_article_to_story(story_id, article_id)
        db.ensure_story_target(story_id, "shakira")

    artifact = export_mobile_snapshot.build_snapshot_artifact(make_args(tmp_path, db_path))
    payload = artifact["data_payload"]
    shakira_row = next(row for row in payload["targets"] if row["key"] == "shakira")

    assert shakira_row["storyCount"] == 0
    assert payload["stories"][0]["targetKeys"] == []
    assert payload["stories"][0]["articles"][0]["targetKeys"] == []


def test_export_filters_secondary_targets_from_merged_story_records():
    story_records = [
        {
            "storyIdInt": 127,
            "title": "Projeto busca orientar mulheres a lidarem com processos de transicao na vida",
            "targetKeys": ["shakira"],
            "articleCount": 1,
            "articles": [
                {
                    "articleId": 235,
                    "title": "Projeto busca orientar mulheres a lidarem com processos de transicao na vida",
                    "url": "https://example.com/projeto-transicao",
                    "targetKeys": ["shakira"],
                    "summaryPreview": "Trecho de busca antigo.",
                    "rawTextKey": "article-235",
                }
            ],
        }
    ]
    raw_texts = {
        "article-235": "Texto real da materia sobre empreendedorismo, carreira e inteligencia emocional."
    }
    secondary_targets = {
        "shakira": Target(key="shakira", label="shakira", display_name="shakira", keywords=["shakira"])
    }

    filtered = export_mobile_snapshot.filter_secondary_targets_from_story_records(
        story_records,
        secondary_targets,
        raw_texts,
    )

    assert filtered[0]["targetKeys"] == []
    assert filtered[0]["articles"][0]["targetKeys"] == []


def test_archived_targets_do_not_reappear_in_export_filters(monkeypatch, tmp_path):
    db_path = tmp_path / "clipping.db"
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            [
                {
                    "key": "flavio_valle",
                    "label": "Flávio Valle",
                    "display_name": "Flávio Valle",
                    "primary": True,
                    "keywords": ["Flávio Valle"],
                },
                {
                    "key": "ana_arquivada",
                    "label": "Ana Arquivada",
                    "display_name": "Ana Arquivada",
                    "primary": False,
                    "archived": True,
                    "keywords": ["Ana Arquivada"],
                },
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(export_mobile_snapshot, "TARGETS_PATH", targets_path)
    with ClippingDB(db_path) as db:
        archived_article = db.insert_article(
            url="https://example.com/arquivada",
            title="Materia apenas arquivada",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-04-06T12:00:00+00:00",
            snippet="Snippet arquivado.",
            full_text="Texto arquivado.",
        )
        assert archived_article is not None
        db.insert_mention(archived_article, "ana_arquivada", "Ana Arquivada", "Ana Arquivada")
        archived_story = db.create_story(
            title="Historia apenas arquivada",
            summary="Resumo arquivado.",
            temperature=4.0,
            target_keys=["ana_arquivada"],
        )
        db.attach_article_to_story(archived_story, archived_article)
        db.ensure_story_target(archived_story, "ana_arquivada")

        mixed_article = db.insert_article(
            url="https://example.com/mista",
            title="Flavio Valle e Ana Arquivada",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-04-06T13:00:00+00:00",
            snippet="Snippet misto.",
            full_text="Texto misto.",
        )
        assert mixed_article is not None
        db.insert_mention(mixed_article, "flavio_valle", "Flávio Valle", "Flávio Valle")
        db.insert_mention(mixed_article, "ana_arquivada", "Ana Arquivada", "Ana Arquivada")
        mixed_story = db.create_story(
            title="Historia mista",
            summary="Resumo misto.",
            temperature=8.0,
            target_keys=["flavio_valle", "ana_arquivada"],
        )
        db.attach_article_to_story(mixed_story, mixed_article)
        db.ensure_story_target(mixed_story, "flavio_valle")
        db.ensure_story_target(mixed_story, "ana_arquivada")
        archived_only_in_mixed = db.insert_article(
            url="https://example.com/mista-arquivada",
            title="Ana Arquivada sozinha dentro da historia mista",
            source_name="Fonte Teste",
            source_type="test",
            published_at="2026-04-06T14:00:00+00:00",
            snippet="Snippet arquivado dentro de historia mista.",
            full_text="Texto arquivado dentro de historia mista.",
        )
        assert archived_only_in_mixed is not None
        db.insert_mention(archived_only_in_mixed, "ana_arquivada", "Ana Arquivada", "Ana Arquivada")
        db.attach_article_to_story(mixed_story, archived_only_in_mixed)

    artifact = export_mobile_snapshot.build_snapshot_artifact(make_args(tmp_path, db_path))
    payload = artifact["data_payload"]

    assert [row["key"] for row in artifact["target_rows"]] == ["flavio_valle"]
    assert [row["key"] for row in payload["targets"]] == ["flavio_valle"]
    assert [story["title"] for story in payload["stories"]] == ["Historia mista"]
    assert payload["stories"][0]["targetKeys"] == ["flavio_valle"]
    assert payload["stories"][0]["articleCount"] == 1
    assert len(payload["stories"][0]["articles"]) == 1
    assert payload["stories"][0]["articles"][0]["targetKeys"] == ["flavio_valle"]


def test_parse_source_snapshot_reads_generated_bundle(tmp_path):
    db_path = tmp_path / "clipping.db"
    seed_story_db(db_path)
    args = make_args(tmp_path, db_path)

    artifact = export_mobile_snapshot.build_snapshot_artifact(args)
    export_mobile_snapshot.write_bundle_assets(artifact, artifact["asset_paths"])
    export_mobile_snapshot.write_shell_html(Path(args.output), artifact["data_payload"], artifact["asset_paths"])

    merge_meta, stories, raw_texts = export_mobile_snapshot.parse_source_snapshot(args.output)

    assert merge_meta["targets"]
    assert len(stories) == 1
    assert stories[0]["title"] == "Historia teste do bundle"
    assert stories[0]["articles"][0]["title"] == "Flavio Valle apresenta projeto de teste"
    assert raw_texts["article-1"].startswith("Texto bruto de teste.")


def test_parse_source_snapshot_reads_legacy_html(tmp_path):
    legacy_path = tmp_path / "legacy.html"
    legacy_payload = {
        "targets": [{"key": "flavio_valle", "label": "Flávio Valle", "storyCount": 1, "articleCount": 1}],
        "defaultTargets": ["flavio_valle"],
        "storyTargets": {"1": ["flavio_valle"]},
        "rawTexts": {},
    }
    legacy_html = f"""<!doctype html>
<html lang="pt-BR">
<body>
  <section id="storyStack">
    <details class="panel story-card" id="story-1" data-story-id="1" data-article-count="1" data-ai-count="0" data-raw-count="1" data-temperature="9" data-last-published="2026-01-01T10:00:00+00:00">
      <summary class="story-summary-row">
        <div class="story-heading"><div><h2>Legacy Story</h2></div></div>
        <div class="story-stats"><div><strong>1</strong><span>noticias</span></div><div><strong>9</strong><span>temperatura</span></div></div>
      </summary>
      <div class="story-meta"><span>Primeira publicacao: 01/01/2026 10:00 UTC</span><span>Ultima publicacao: 01/01/2026 10:00 UTC</span></div>
      <div class="story-blurb"><div class="summary-label">Resumo do agrupamento</div><p>Story summary</p></div>
      <div class="story-articles">
        <article class="article-card" id="article-10">
          <div class="article-top">
            <div>
              <h3><a href="https://example.com/legacy" target="_blank" rel="noreferrer">Legacy Article</a></h3>
              <p class="article-meta"><span>Legacy Source</span><span>01/01/2026 10:00 UTC</span><span>example.com</span></p>
            </div>
          </div>
          <div class="summary-box summary-raw">
            <div class="summary-label">Texto bruto</div>
            <div class="body-text">Preview legacy</div>
            <details class="raw-details">
              <summary>Ver texto bruto completo</summary>
              <div class="body-text full">Full legacy text</div>
            </details>
          </div>
        </article>
      </div>
    </details>
  </section>
  <script id="snapshot-payload" type="application/json">{json.dumps(legacy_payload, ensure_ascii=False)}</script>
</body>
</html>
"""
    legacy_path.write_text(legacy_html, encoding="utf-8")

    merge_meta, stories, raw_texts = export_mobile_snapshot.parse_source_snapshot(str(legacy_path))

    assert merge_meta["storyTargets"]["1"] == ["flavio_valle"]
    assert len(stories) == 1
    assert stories[0]["title"] == "Legacy Story"
    assert stories[0]["articles"][0]["title"] == "Legacy Article"
    assert stories[0]["articles"][0]["rawTextKey"] == "article-10"
    assert raw_texts["article-10"] == "Full legacy text"


def test_prepare_wix_snapshot_writes_bundle_variants(tmp_path):
    db_path = tmp_path / "clipping.db"
    seed_story_db(db_path)
    args = make_prepare_args(tmp_path, db_path)

    metadata = prepare_wix_clipping_snapshot.prepare_snapshot(args)

    canonical_output = Path(metadata["canonical_output"])
    current_output = Path(metadata["current_output"])
    archive_html = Path(metadata["archive_html"])
    metadata_path = Path(metadata["review_bundle_dir"]) / "metadata.json"

    assert canonical_output.exists()
    assert current_output.exists()
    assert archive_html.exists()
    assert metadata_path.exists()

    for bundle in ("canonical_assets", "current_assets", "archive_assets"):
        for path in metadata[bundle].values():
            assert Path(path).exists(), f"missing bundle asset: {path}"

    html_doc = canonical_output.read_text(encoding="utf-8")
    validation = prepare_wix_clipping_snapshot.validate_snapshot_html(html_doc)
    assert validation["ok"]
    assert metadata["screenshots"] == {}
