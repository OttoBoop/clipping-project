import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.database import ClippingDB
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
    assert '<article class="article-card"' not in html_doc
    assert 'data-story-id="' not in html_doc
    assert "Carregando dados do clipping" in html_doc
    assert "Carregar mais noticias" in artifact["js_text"]
    assert "Carregando noticias" in artifact["js_text"]
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
    assert 'data-clipping-data-url="index_assets/clipping-data.json"' in html_doc
    assert 'data-clipping-raw-url="index_assets/clipping-raw-texts.json"' in html_doc


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
