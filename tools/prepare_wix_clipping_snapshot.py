#!/usr/bin/env python3
"""Prepare a Wix-ready clipping snapshot: validate, archive, screenshot.

Original path: tools/prepare_wix_clipping_snapshot.py

Recovery notes:
- The old monolithic snapshot format is gone. The current production flow emits
  a light HTML shell plus external CSS/JS/JSON assets.
- This helper now wraps ``tools.export_mobile_snapshot`` and prepares a complete
  review/archive bundle for Wix and GitHub Pages style publishing.
- Screenshots are rendered through a temporary local HTTP server so the shell
  can fetch its sibling JSON assets correctly.
"""
from __future__ import annotations

import argparse
import functools
import json
import sys
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.export_mobile_snapshot as export_mobile_snapshot  # noqa: E402


DEFAULT_CURRENT_OUTPUT = (
    export_mobile_snapshot.REPORTS_DIR / "clipping_mobile_snapshot_wix_current.html"
)
DEFAULT_ARCHIVE_DIR = export_mobile_snapshot.REPORTS_DIR / "wix_archive"
DEFAULT_REVIEW_DIR = export_mobile_snapshot.REPORTS_DIR / "wix_review"


REQUIRED_MARKERS = [
    export_mobile_snapshot.WIX_SNAPSHOT_SENTINEL,
    "data-clipping-data-url",
    'id="storyStack"',
    'id="flatStack"',
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepara um bundle de clipping para validacao, arquivo e revisao visual."
    )
    parser.add_argument(
        "--db",
        default="",
        help="Caminho do banco SQLite a exportar. Default: data/clipping.db",
    )
    parser.add_argument("--date-from", default="", help="Data inicial em YYYY-MM-DD.")
    parser.add_argument("--date-to", default="", help="Data final em YYYY-MM-DD.")
    parser.add_argument(
        "--all-stories",
        action="store_true",
        help="Exporta todas as historias atuais do banco, ignorando a janela de datas.",
    )
    parser.add_argument(
        "--default-target",
        default=export_mobile_snapshot.DEFAULT_TARGET_KEY,
        help="Target inicial selecionado no filtro. Default: flavio_valle.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="HTML canonico a ser escrito. Default: o mesmo do export principal.",
    )
    parser.add_argument(
        "--merge-from",
        default="",
        help="Snapshot existente a mesclar antes de preparar o bundle.",
    )
    parser.add_argument(
        "--remap-incoming-ids-on-merge",
        action="store_true",
        help="Desloca IDs do banco atual para evitar colisao com o snapshot mesclado.",
    )
    parser.add_argument(
        "--current-output",
        default=str(DEFAULT_CURRENT_OUTPUT),
        help="Copia de trabalho do HTML shell para revisao atual.",
    )
    parser.add_argument(
        "--archive-dir",
        default=str(DEFAULT_ARCHIVE_DIR),
        help="Diretorio para snapshots archivados com timestamp.",
    )
    parser.add_argument(
        "--review-dir",
        default=str(DEFAULT_REVIEW_DIR),
        help="Diretorio para screenshots e metadata de revisao.",
    )
    parser.add_argument(
        "--skip-screenshots",
        action="store_true",
        help="Nao renderiza screenshots de revisao.",
    )
    args = parser.parse_args()
    if not args.all_stories and (not args.date_from or not args.date_to):
        parser.error("use --all-stories ou informe --date-from e --date-to")
    return args


def scope_token(args: argparse.Namespace) -> str:
    if args.all_stories:
        return "all_stories"
    return f"{args.date_from}_{args.date_to}"


def validate_snapshot_html(html_doc: str) -> dict[str, Any]:
    lowered = html_doc.lstrip().lower()
    checks = {
        "is_full_document": lowered.startswith("<!doctype html>"),
        "has_wix_sentinel": export_mobile_snapshot.WIX_SNAPSHOT_SENTINEL in html_doc,
        "has_data_url": 'data-clipping-data-url="' in html_doc,
        "has_story_stack": 'id="storyStack"' in html_doc,
        "has_flat_stack": 'id="flatStack"' in html_doc,
    }
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "missing_markers": [marker for marker in REQUIRED_MARKERS if marker not in html_doc],
    }


def json_ready(value: Any) -> Any:
    if isinstance(value, set):
        return sorted(json_ready(item) for item in value)
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    return value


def bundle_asset_paths_for_output(
    args: argparse.Namespace, output_path: Path
) -> dict[str, Path]:
    asset_dir = export_mobile_snapshot.bundle_asset_dir_for_output(args, output_path)
    return {
        "css": asset_dir / "clipping.css",
        "js": asset_dir / "clipping.js",
        "data": asset_dir / "clipping-data.json",
        "raw": asset_dir / "clipping-raw-texts.json",
    }


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


@contextmanager
def serve_directory(directory: Path) -> Iterator[str]:
    handler = functools.partial(_QuietHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def render_review_screenshots(html_path: Path, output_dir: Path) -> dict[str, str]:
    from playwright.sync_api import sync_playwright

    output_dir.mkdir(parents=True, exist_ok=True)
    desktop_path = output_dir / "desktop.png"
    mobile_path = output_dir / "mobile.png"

    with serve_directory(html_path.parent) as base_url:
        html_url = f"{base_url}/{quote(html_path.name)}"

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            desktop = browser.new_page(viewport={"width": 1440, "height": 2200})
            desktop.goto(html_url, wait_until="networkidle")
            desktop.wait_for_function(
                """() => {
                  const el = document.getElementById('loadingState');
                  return !el || el.hidden || el.classList.contains('app-error');
                }""",
                timeout=20000,
            )
            desktop.screenshot(path=str(desktop_path), full_page=True)
            desktop.close()

            mobile = browser.new_page(
                viewport={"width": 390, "height": 844},
                is_mobile=True,
                has_touch=True,
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                    "Mobile/15E148 Safari/604.1"
                ),
            )
            mobile.goto(html_url, wait_until="networkidle")
            mobile.wait_for_function(
                """() => {
                  const el = document.getElementById('loadingState');
                  return !el || el.hidden || el.classList.contains('app-error');
                }""",
                timeout=20000,
            )
            mobile.screenshot(path=str(mobile_path), full_page=True)
            mobile.close()

            browser.close()

    return {
        "desktop": str(desktop_path.resolve()),
        "mobile": str(mobile_path.resolve()),
    }


def write_bundle(
    *,
    args: argparse.Namespace,
    output_path: Path,
    artifact: dict[str, Any],
) -> dict[str, Path]:
    asset_paths = bundle_asset_paths_for_output(args, output_path)
    export_mobile_snapshot.write_bundle_assets(artifact, asset_paths)
    export_mobile_snapshot.write_shell_html(output_path, artifact["data_payload"], asset_paths)
    return asset_paths


def prepare_snapshot(args: argparse.Namespace) -> dict[str, Any]:
    prepared_at = datetime.now(timezone.utc)
    prepared_token = prepared_at.strftime("%Y%m%dT%H%M%SZ")

    canonical_output = export_mobile_snapshot.output_path_for_args(args).expanduser().resolve()
    current_output = Path(args.current_output).expanduser().resolve()
    archive_dir = Path(args.archive_dir).expanduser().resolve()
    review_root = Path(args.review_dir).expanduser().resolve()
    archive_html = archive_dir / f"clipping_mobile_snapshot_wix_{scope_token(args)}_{prepared_token}.html"

    artifact = export_mobile_snapshot.build_snapshot_artifact(args)
    html_doc = artifact["html_doc"]
    initial_stats = artifact["initial_stats"]

    validation = validate_snapshot_html(html_doc)
    if not validation["ok"]:
        raise RuntimeError(
            "Snapshot HTML invalido para o fluxo do Wix: "
            + ", ".join(validation["missing_markers"])
        )

    archive_dir.mkdir(parents=True, exist_ok=True)
    review_bundle_dir = review_root / f"{scope_token(args)}_{prepared_token}"
    review_bundle_dir.mkdir(parents=True, exist_ok=True)

    canonical_assets = write_bundle(args=args, output_path=canonical_output, artifact=artifact)
    current_assets = write_bundle(args=args, output_path=current_output, artifact=artifact)
    archive_assets = write_bundle(args=args, output_path=archive_html, artifact=artifact)

    screenshots: dict[str, str] = {}
    if not args.skip_screenshots:
        screenshots = render_review_screenshots(current_output, review_bundle_dir)

    metadata = {
        "prepared_at": prepared_token,
        "scope_token": scope_token(args),
        "initial_stats": json_ready(initial_stats),
        "validation": validation,
        "screenshots": screenshots,
        "canonical_output": str(canonical_output),
        "canonical_assets": {key: str(path) for key, path in canonical_assets.items()},
        "current_output": str(current_output),
        "current_assets": {key: str(path) for key, path in current_assets.items()},
        "archive_html": str(archive_html),
        "archive_assets": {key: str(path) for key, path in archive_assets.items()},
        "review_bundle_dir": str(review_bundle_dir),
    }
    metadata_path = review_bundle_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return metadata


def main() -> int:
    args = parse_args()
    try:
        metadata = prepare_snapshot(args)
    except (FileNotFoundError, RuntimeError, ImportError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    print(metadata["canonical_output"])
    print(metadata["current_output"])
    print(metadata["archive_html"])
    if metadata["screenshots"]:
        print(metadata["screenshots"]["desktop"])
        print(metadata["screenshots"]["mobile"])
    print(json.dumps(metadata["initial_stats"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
