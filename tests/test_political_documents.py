"""PDF boundaries and resume behavior; live PDF probes are separate artifacts."""
import hashlib
from pathlib import Path
import shutil

import pytest

from web_app import political_documents as documents


def test_edition_date_is_not_the_upload_month_or_web_publication():
    url = "https://panoramarj.com.br/wp-content/uploads/2026/07/Jornal-Panorama-Rio-de-Janeiro-27-de-Junho-de-2026.pdf"
    parsed = documents.edition_date("Pré-visualização do PDF", filename=url)
    assert parsed["edition_date"] == "2026-06-27"
    assert parsed["date_status"] == "publisher_edition_filename"
    unknown = documents.edition_date("Maré de Notícias #169", filename="https://maredenoticias.com/wp-content/uploads/2026/07/PROPOSTA-MN-ED.169-V6-3.pdf")
    assert unknown["edition_date"] == unknown["edition_month"] == ""
    assert unknown["date_status"] == "unknown"


def test_month_and_weekend_range_remain_explicit():
    month = documents.edition_date("JULHO - 2026")
    assert month["edition_date"] == "" and month["date_precision"] == "month"
    assert (month["period_from"], month["period_to"]) == ("2026-07-01", "2026-07-31")
    weekend = documents.edition_date("RIO DE JANEIRO, SÁBADO 27 A SEGUNDA-FEIRA 29 DE JUNHO DE 2026")
    assert weekend["edition_date"] == "2026-06-27"
    assert (weekend["period_from"], weekend["period_to"]) == ("2026-06-27", "2026-06-29")
    assert documents.edition_date("31 de fevereiro de 2026", allow_month=False)["date_status"] == "unknown"


def test_publisher_pdf_links_deduplicate_fragments_without_accepting_external_mirrors():
    html = '''<a href="/edicao.pdf#page=2">27 de junho de 2026</a>
    <a href="/edicao.pdf#page=3">duplicado</a><a href="https://elsewhere.test/edicao.pdf">externo</a>
    <a href="/mare-de-noticias-169/?amp=1">mobile</a><a href="/mare-de-noticias-168/">Maré 168</a>
    <a href="/noticia/">notícia diária</a>'''
    rows = documents.parse_edition_links(html, "https://maredenoticias.com/mare-de-noticias-169/", "mare")
    assert [row["url"] for row in rows] == ["https://maredenoticias.com/edicao.pdf", "https://maredenoticias.com/mare-de-noticias-168/"]
    assert rows[0]["edition_date"] == "2026-06-27"


class Response:
    status_code = 200
    headers = {}
    url = "https://publisher.test/edition.pdf"
    closed = False

    def __init__(self, chunks):
        self.chunks = chunks

    def iter_content(self, size):
        yield from self.chunks

    def close(self):
        self.closed = True


def test_streamed_download_has_hash_and_cleans_failed_partial_files(tmp_path, monkeypatch):
    raw = b"%PDF-1.4\npublic document transport bytes"
    response = Response([raw[:4], raw[4:]])
    downloaded = documents.download_pdf(response, tmp_path)
    assert response.closed and downloaded.sha256 == hashlib.sha256(raw).hexdigest()
    assert Path(downloaded.path).read_bytes() == raw
    before = set(tmp_path.iterdir())
    for chunks, reason in [([b"<html>Access denied</html>"], "pdf_signature_missing"),
                           ([raw], "pdf_hash_mismatch")]:
        with pytest.raises(documents.DocumentProblem, match=reason):
            documents.download_pdf(Response(chunks), tmp_path, expected_sha256="0" * 64)
        assert set(tmp_path.iterdir()) == before
    monkeypatch.setattr(documents, "MAX_PDF_BYTES", 12)
    with pytest.raises(documents.DocumentProblem, match="pdf_byte_limit"):
        documents.download_pdf(Response([raw]), tmp_path)
    assert set(tmp_path.iterdir()) == before


def test_storage_failure_never_claims_a_saved_object(tmp_path):
    path = tmp_path / "edition.pdf"
    path.write_bytes(b"%PDF-1.4\ntransport only")
    class Store:
        enabled, prefix = True, "archive"
        def upload_path(self, *args):
            return False
    with pytest.raises(documents.DocumentProblem, match="pdf_storage_failed") as exc:
        documents.store_pdf(documents.document_file(path), Store())
    assert exc.value.retryable


def test_page_checkpoint_interrupts_before_next_page_and_resume_reuses_hash(tmp_path, monkeypatch):
    path = tmp_path / "edition.pdf"
    path.write_bytes(b"%PDF-1.4\ntransport only")
    monkeypatch.setattr(documents, "inspect_pdf", lambda _: {"page_count": 3})
    visited = []
    def run(command, directory, **kwargs):
        assert command[0] == "pdftotext"
        page = int(command[command.index("-f") + 1])
        visited.append(page)
        Path(command[-1]).write_text("Um texto editorial de página preservada com palavras suficientes para verificação e leitura. " * 3)
        return ""
    monkeypatch.setattr(documents, "_run", run)
    committed = []
    def commit(page):
        if page.page_number == 2:
            raise RuntimeError("database unavailable")
        committed.append(page.page_number)
    with pytest.raises(RuntimeError, match="database unavailable"):
        list(documents.extract_pdf_pages(path, max_pages=3, checkpoint=commit))
    assert committed == [1] and visited == [1, 2]
    resumed = list(documents.extract_pdf_pages(path, start_page=2, max_pages=2))
    assert [page.page_number for page in resumed] == [2, 3]
    assert all(page.document_sha256 == hashlib.sha256(path.read_bytes()).hexdigest() for page in resumed)


def test_ocr_failure_keeps_available_native_fragment_and_explicit_gap(tmp_path, monkeypatch):
    path = tmp_path / "edition.pdf"
    path.write_bytes(b"%PDF-1.4\ntransport only")
    monkeypatch.setattr(documents, "inspect_pdf", lambda _: {"page_count": 1})
    def run(command, directory, **kwargs):
        if command[0] == "pdftotext":
            Path(command[-1]).write_text("Título preservado")
            return ""
        raise documents.DocumentProblem("pdf_tool_unavailable:tesseract")
    monkeypatch.setattr(documents, "_run", run)
    page = next(documents.extract_pdf_pages(path))
    assert page.text == "Título preservado" and page.state == "partial_text"
    assert page.error_type == "pdf_tool_unavailable:tesseract"


def test_missing_binary_is_reported_without_spawning(tmp_path):
    with pytest.raises(documents.DocumentProblem, match="pdf_tool_unavailable"):
        documents._run(["clipping-no-such-pdf-tool"], tmp_path, timeout=1)


@pytest.mark.skipif(not shutil.which("pdftotext"), reason="Poppler required")
def test_subprocess_deadline_kills_child_without_unbounded_wait(tmp_path):
    import sys
    import time
    start = time.monotonic()
    with pytest.raises(documents.DocumentProblem, match="pdf_tool_timeout"):
        documents._run([sys.executable, "-c", "import time;time.sleep(10)"], tmp_path, timeout=1)
    assert time.monotonic() - start < 4
