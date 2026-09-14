"""Public newspaper editions: bounded PDF transport and page-at-a-time text.

This module does not create articles, alter the database, or discover from
third-party mirrors. The caller owns the domain limiter, durable task lease,
document identity, and transaction that acknowledges each yielded page.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import calendar
import hashlib
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from urllib.parse import unquote, urljoin, urlparse, urlunparse

VERSION = "public_pdf_pages_v1"
MAX_PDF_BYTES = 32 * 1024 * 1024
MAX_PDF_SECONDS = 90
MAX_PDF_PAGES = 500
MAX_PAGE_TEXT_BYTES = 2 * 1024 * 1024
SUBPROCESS_MEMORY_BYTES = 256 * 1024 * 1024
SUBPROCESS_FILE_BYTES = 32 * 1024 * 1024
MONTHS = {name: index for index, name in enumerate(
    ("janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto",
     "setembro", "outubro", "novembro", "dezembro"), 1)}
_MONTH_RE = "(?:" + "|".join(MONTHS) + ")"


class DocumentProblem(ValueError):
    def __init__(self, reason: str, *, retryable: bool = False):
        super().__init__(reason)
        self.retryable = retryable


@dataclass(frozen=True)
class DocumentFile:
    path: str
    sha256: str
    bytes: int
    url: str = ""


@dataclass(frozen=True)
class PageResult:
    document_sha256: str
    page_number: int
    page_count: int
    text: str
    method: str
    state: str
    error_type: str = ""
    version: str = VERSION

    def to_dict(self):
        return asdict(self)


def _plain(value: str) -> str:
    value = unicodedata.normalize("NFKD", unquote(str(value or ""))).casefold()
    return "".join(char for char in value if not unicodedata.combining(char))


def edition_date(text: str, *, filename: str = "", allow_month: bool = True) -> dict:
    """Read an editorial label, never PDF creation time or /uploads/YYYY/MM/.

    Month-only editions retain an interval and an unknown publication day.
    The caller may supply the cover's masthead text, not the entire newspaper.
    """
    result = {"edition_date": "", "edition_month": "", "date_status": "unknown",
              "date_precision": "unknown", "period_from": "", "period_to": "",
              "date_evidence": ""}
    for raw, basis in ((text, "publisher_edition_label"),
                       (Path(urlparse(filename).path).name, "publisher_edition_filename")):
        normalized = re.sub(r"[-_]+", " ", _plain(raw))
        span = re.search(r"\b(\d{1,2})\s+a\s+(?:[a-z]+\s+){0,4}(\d{1,2})\s+(?:de\s+)?(" + _MONTH_RE + r")\s+(?:de\s+)?(20\d{2})\b", normalized)
        if span:
            try:
                first = date(int(span[4]), MONTHS[span[3]], int(span[1]))
                last = date(int(span[4]), MONTHS[span[3]], int(span[2]))
                if last < first:
                    raise ValueError()
            except ValueError:
                continue
            return {**result, "edition_date": first.isoformat(), "date_status": basis,
                    "date_precision": "range", "period_from": first.isoformat(), "period_to": last.isoformat(),
                    "date_evidence": str(raw)[:500]}
        match = re.search(r"\b(\d{1,2})\s+(?:de\s+)?(" + _MONTH_RE + r")\s+(?:de\s+)?(20\d{2})\b", normalized)
        if match:
            try:
                stamp = date(int(match[3]), MONTHS[match[2]], int(match[1])).isoformat()
            except ValueError:
                continue
            return {**result, "edition_date": stamp, "date_status": basis,
                    "date_precision": "day", "period_from": stamp, "period_to": stamp,
                    "date_evidence": str(raw)[:500]}
    if allow_month:
        # A numeric upload path is deliberately not inspected for month evidence.
        normalized = re.sub(r"[-_]+", " ", _plain(text))
        match = re.search(r"\b(" + _MONTH_RE + r")\s+(?:de\s+)?(20\d{2})\b", normalized)
        if match:
            year, month = int(match[2]), MONTHS[match[1]]
            return {**result, "edition_month": f"{year:04d}-{month:02d}",
                    "date_status": "edition_month_only", "date_precision": "month",
                    "period_from": date(year, month, 1).isoformat(),
                    "period_to": date(year, month, calendar.monthrange(year, month)[1]).isoformat(),
                    "date_evidence": str(text)[:500]}
    return result


class _EditionLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.current = [], None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            self.current = {"href": attrs.get("href") or "", "parts": [],
                            "label": attrs.get("title") or ""}
        elif tag == "img" and self.current is not None:
            self.current["parts"].append(attrs.get("alt") or "")

    def handle_data(self, data):
        if self.current is not None:
            self.current["parts"].append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.links.append(self.current)
            self.current = None


def parse_edition_links(raw_html: str, page_url: str, source_key: str,
                        *, allowed_hosts=None) -> list[dict]:
    """Publisher-local PDFs and the two verified edition-index URL families.

    This returns candidates only. Matching and date-window checks remain with
    the caller. A page's web publication date is not its printed edition date.
    """
    parser = _EditionLinks()
    parser.feed(raw_html or "")
    normalized_host = lambda value: (value or "").casefold().removeprefix("www.")
    hosts = {normalized_host(host) for host in (allowed_hosts or [urlparse(page_url).hostname])}
    candidates = {}
    for link in parser.links:
        parsed = urlparse(urljoin(page_url, link["href"]))
        if parsed.scheme not in {"https", "http"} or normalized_host(parsed.hostname) not in hosts or parsed.username or parsed.password:
            continue
        path = unquote(parsed.path)
        pdf = path.casefold().endswith(".pdf")
        edition = bool(re.search(r"/(?:mare-de-noticias-\d+|edicoes-link)/?$", path))
        if not pdf and not edition:
            continue
        # Fragments are navigation within an edition, never document identity.
        url = urlunparse(parsed._replace(fragment=""))
        if edition and parsed.path.rstrip("/") == urlparse(page_url).path.rstrip("/") and not parsed.path.endswith("edicoes-link/"):
            continue
        if url == urlunparse(urlparse(page_url)._replace(fragment="")):
            continue
        title = " ".join(" ".join(link["parts"]).split()) or link["label"] or Path(path).stem
        candidates.setdefault(url, {"url": url, "title": title, "source_key": source_key,
            "product_kind": "pdf_edition" if pdf else "edition_index",
            "discovery_url": page_url, **edition_date(title, filename=url if pdf else "")})
    return list(candidates.values())


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def document_file(path, *, url="", expected_sha256="") -> DocumentFile:
    path = Path(path)
    size = path.stat().st_size
    if not 0 < size <= MAX_PDF_BYTES:
        raise DocumentProblem("pdf_byte_limit")
    with path.open("rb") as stream:
        if b"%PDF-" not in stream.read(1024):
            raise DocumentProblem("pdf_signature_missing")
    digest = _hash_file(path)
    if expected_sha256 and digest != expected_sha256:
        raise DocumentProblem("pdf_hash_mismatch")
    return DocumentFile(str(path), digest, size, url)


def download_pdf(response, directory, *, expected_sha256="") -> DocumentFile:
    """Consume a streaming response from the caller's authorized, limited GET.

    Closes the response on every exit. No access credentials or second request
    are introduced here. A corrupt/missing object may be redownloaded by caller.
    """
    temporary = None
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    try:
        status = int(response.status_code)
        if status >= 400:
            raise DocumentProblem(f"http_{status}", retryable=status in {408, 425, 429} or status >= 500)
        length = response.headers.get("Content-Length", "")
        if str(length).isdigit() and int(length) > MAX_PDF_BYTES:
            raise DocumentProblem("pdf_byte_limit")
        digest, size, prefix = hashlib.sha256(), 0, bytearray()
        started = time.monotonic()
        with tempfile.NamedTemporaryFile(dir=directory, suffix=".part", delete=False) as stream:
            temporary = Path(stream.name)
            for chunk in response.iter_content(65536):
                if not chunk:
                    continue
                size += len(chunk)
                if size > MAX_PDF_BYTES:
                    raise DocumentProblem("pdf_byte_limit")
                if time.monotonic() - started > MAX_PDF_SECONDS:
                    raise DocumentProblem("pdf_download_timeout", retryable=True)
                if len(prefix) < 1024:
                    prefix.extend(chunk[:1024 - len(prefix)])
                digest.update(chunk)
                stream.write(chunk)
            stream.flush()
            os.fsync(stream.fileno())
        if b"%PDF-" not in prefix:
            raise DocumentProblem("pdf_signature_missing")
        checksum = digest.hexdigest()
        if expected_sha256 and checksum != expected_sha256:
            raise DocumentProblem("pdf_hash_mismatch")
        target = directory / (checksum + ".pdf")
        os.replace(temporary, target)
        temporary = None
        return DocumentFile(str(target), checksum, size, str(getattr(response, "url", "")))
    finally:
        response.close()
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def store_pdf(document: DocumentFile, store) -> dict:
    """Save original bytes by hash. An interrupted DB commit can safely retry.

    ArtifactStore's existing upload_bytes interface requires one bounded read;
    prefer upload_file when supplied by a future streaming store implementation.
    """
    verified = document_file(document.path, expected_sha256=document.sha256)
    key = f"{store.prefix}/political/documents/{verified.sha256[:2]}/{verified.sha256}.pdf"
    try:
        if not store.enabled:
            raise DocumentProblem("pdf_storage_unavailable", retryable=True)
        if hasattr(store, "upload_path"):
            saved = store.upload_path(Path(verified.path), key, "application/pdf")
        elif hasattr(store, "upload_file"):
            saved = store.upload_file(Path(verified.path), key)
        else:
            saved = store.upload_bytes(Path(verified.path).read_bytes(), key, "application/pdf")
        if not saved:
            raise DocumentProblem("pdf_storage_failed", retryable=True)
    except DocumentProblem:
        raise
    except Exception as exc:
        raise DocumentProblem("pdf_storage_failed", retryable=True) from exc
    return {"key": key, "sha256": verified.sha256, "bytes": verified.bytes,
            "content_type": "application/pdf", "version": VERSION}


def _environment():
    environment = dict(os.environ)
    environment.update({"OMP_THREAD_LIMIT": "1", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
    installation = os.environ.get("POLITICAL_OCR_ROOT")
    default = Path(__file__).resolve().parents[1] / ".render-tools/political-ocr"
    if not installation and default.is_dir():
        installation = str(default)
    if installation:
        root = Path(installation)
        environment["PATH"] = str(root / "usr/bin") + os.pathsep + environment.get("PATH", "")
        libraries = [str(path) for path in (root / "usr/lib").glob("*-linux-gnu")]
        environment["LD_LIBRARY_PATH"] = os.pathsep.join(libraries + [environment.get("LD_LIBRARY_PATH", "")])
        environment["TESSDATA_PREFIX"] = str(root / "usr/share/tesseract-ocr/5/tessdata")
    return environment


# Setting resource limits in a tiny exec wrapper avoids preexec_fn, which is
# unsafe in the multithreaded worker. Each child has its own process group.
_LIMITED_EXEC = """import os,resource,sys
memory,files,cpu=map(int,sys.argv[1:4])
resource.setrlimit(resource.RLIMIT_AS,(memory,memory))
resource.setrlimit(resource.RLIMIT_FSIZE,(files,files))
resource.setrlimit(resource.RLIMIT_CPU,(cpu,cpu+1))
os.execvpe(sys.argv[4],sys.argv[4:],os.environ)
"""


def _run(command: list[str], directory: Path, *, timeout: int) -> str:
    environment = _environment()
    binary = shutil.which(command[0], path=environment.get("PATH"))
    if not binary:
        raise DocumentProblem("pdf_tool_unavailable:" + command[0])
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        proc = subprocess.Popen([sys.executable, "-c", _LIMITED_EXEC,
            str(SUBPROCESS_MEMORY_BYTES), str(SUBPROCESS_FILE_BYTES), str(timeout), binary, *command[1:]],
            cwd=directory, env=environment, stdin=subprocess.DEVNULL, stdout=output,
            stderr=errors, start_new_session=True)
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            raise DocumentProblem("pdf_tool_timeout:" + command[0], retryable=True) from exc
        if proc.returncode:
            raise DocumentProblem("pdf_tool_failed:" + command[0])
        output.seek(0)
        raw = output.read(MAX_PAGE_TEXT_BYTES + 1)
        if len(raw) > MAX_PAGE_TEXT_BYTES:
            raise DocumentProblem("pdf_output_limit")
        return raw.decode("utf-8", errors="replace")


def inspect_pdf(document: DocumentFile) -> dict:
    with tempfile.TemporaryDirectory(prefix="political-pdf-info-") as working:
        raw = _run(["pdfinfo", str(Path(document.path).resolve())], Path(working), timeout=15)
    match = re.search(r"^Pages:\s+(\d+)\s*$", raw, re.M)
    if not match:
        raise DocumentProblem("pdf_page_count_unknown")
    count = int(match[1])
    if not 0 < count <= MAX_PDF_PAGES:
        raise DocumentProblem("pdf_page_limit")
    # PDF CreationDate and ModDate are intentionally not publication evidence.
    return {"page_count": count, "sha256": document.sha256, "bytes": document.bytes,
            "encrypted": bool(re.search(r"^Encrypted:\s+yes\b", raw, re.M)), "version": VERSION}


def _read_page_text(path):
    path = Path(path)
    if not path.exists():
        return ""
    if path.stat().st_size > MAX_PAGE_TEXT_BYTES:
        raise DocumentProblem("pdf_page_text_limit")
    text = path.read_text(encoding="utf-8", errors="replace").replace("\x00", "")
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def usable_page_text(text: str) -> bool:
    letters = sum(char.isalpha() for char in text)
    return letters >= 40 and len(re.findall(r"[^\W\d_]{2,}", text, re.UNICODE)) >= 10


def extract_pdf_pages(path, *, start_page=1, max_pages=4, expected_sha256="",
                      allow_ocr=True, checkpoint=None):
    """Yield bounded pages. A callback must commit before returning successfully.

    The callback receives PageResult; it may raise to stop before the next page.
    A resumed caller supplies its last *committed* page plus one. Pages remain
    document pages, never fabricated articles or fragment-based article URLs.
    """
    document = document_file(path, expected_sha256=expected_sha256)
    info = inspect_pdf(document)
    if type(start_page) is not int or not 1 <= start_page <= info["page_count"] + 1:
        raise DocumentProblem("pdf_page_cursor_invalid")
    if type(max_pages) is not int or not 1 <= max_pages <= 20:
        raise DocumentProblem("pdf_page_batch_invalid")
    absolute = str(Path(path).resolve())
    for number in range(start_page, min(info["page_count"] + 1, start_page + max_pages)):
        text, method, error = "", "poppler", ""
        with tempfile.TemporaryDirectory(prefix="political-pdf-page-") as working:
            folder = Path(working)
            try:
                _run(["pdftotext", "-f", str(number), "-l", str(number), "-layout", "-enc", "UTF-8",
                      absolute, str(folder / "native.txt")], folder, timeout=20)
                text = _read_page_text(folder / "native.txt")
            except DocumentProblem as exc:
                error = str(exc)
            if not usable_page_text(text) and allow_ocr:
                try:
                    _run(["pdftoppm", "-f", str(number), "-l", str(number), "-singlefile", "-scale-to", "2000",
                          "-gray", "-png", absolute, str(folder / "page")], folder, timeout=30)
                    _run(["tesseract", str(folder / "page.png"), str(folder / "ocr"), "-l", "por", "--psm", "3"],
                         folder, timeout=60)
                    ocr = _read_page_text(folder / "ocr.txt")
                    if usable_page_text(ocr) or len(ocr) > len(text):
                        text, method = ocr, "tesseract_por"
                    error = "" if usable_page_text(text) else "pdf_editorial_text_unavailable"
                except DocumentProblem as exc:
                    error = str(exc)
            state = "text_available" if usable_page_text(text) else "partial_text" if text else "gap"
            if state != "text_available" and not error:
                error = "pdf_editorial_text_unavailable"
            result = PageResult(document.sha256, number, info["page_count"], text, method, state, error)
        if checkpoint is not None:
            checkpoint(result)
        yield result
