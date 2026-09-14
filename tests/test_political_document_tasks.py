"""Real edition transport and durable pages in an explicitly disposable DB.

No generated article or document is included in collection counts. Preserved
publisher PDFs are optional external fixtures because their originals are large.
"""
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid

import pytest

from web_app.political_document_tasks import (
    DOCUMENT_SCHEMA_SQL, PoliticalDocumentMixin, date_overlaps,
    discover_edition_archive, document_url,
)
from web_app.political_documents import DocumentProblem
from web_app.political_corpus import PoliticalCorpusService, PoliticalNotFound, PoliticalAccessDenied

ROOT = Path(__file__).resolve().parents[2] / 'clipping-live-operations/2026-09-14-gap-closure/pdfs'
REAL_ROOT = Path(os.environ.get('POLITICAL_REAL_PDF_FIXTURES', str(ROOT)))
DATABASE_URL = os.environ.get('POLITICAL_DOCUMENT_TEST_DATABASE_URL', '')
PANORAMA_URL = 'https://panoramarj.com.br/wp-content/uploads/2026/07/Jornal-Panorama-Rio-de-Janeiro-27-de-Junho-de-2026.pdf'
MARE_URL = 'https://maredenoticias.com/wp-content/uploads/2026/07/PROPOSTA-MN-ED.169-V6-3.pdf'
REAL_HASHES = {'panorama-june.pdf': '609ad8a78bdd20a2716187b2956ddb61114146d792047f78d885b66f952d01be',
               'mare-169.pdf': 'b383c41371ee82f458ed2b633b547f409288026ceb6e14445aa8c615b2677b1f'}
TARGETS = [{'key': 'eduardo_cavaliere', 'display_name': 'Eduardo Cavaliere', 'keywords': ['Eduardo Cavaliere']},
           {'key': 'pedro_paulo', 'display_name': 'Pedro Paulo', 'keywords': ['Pedro Paulo']}]


def test_document_identity_and_uncertain_editorial_period():
    assert document_url(PANORAMA_URL + '#page=2') == document_url(PANORAMA_URL + '#page=3') == PANORAMA_URL
    assert date_overlaps({}, '2026-06-01', '2026-09-10') is None
    month = {'period_from': '2026-07-01', 'period_to': '2026-07-31'}
    assert date_overlaps(month, '2026-07-15', '2026-07-15') is True
    assert date_overlaps(month, '2026-08-09', '2026-08-09') is False
    with pytest.raises(DocumentProblem):
        document_url('https://credentials:private@example.com/edition.pdf')


@pytest.mark.skipif(not (REAL_ROOT / 'mare-169.html').exists(), reason='Preserved real publisher edition index required')
def test_real_edition_discovery_keeps_edition_dates_separate_from_upload_path():
    class Response:
        status_code, headers = 200, {}
        text = (REAL_ROOT / 'mare-169.html').read_text()
    task = {'url': 'https://maredenoticias.com/mare-de-noticias-169/',
        'strategy': 'expanded_edition_archive', 'date_from': '2026-06-01', 'date_to': '2026-09-10', 'cursor': {},
        'source_snapshot': {'key': 'mare', 'name': 'Maré', 'domains': ['maredenoticias.com']}}
    output = discover_edition_archive(task, task['source_snapshot'], lambda url: Response())
    assert output['candidates'][0]['url'] == MARE_URL
    assert output['candidates'][0]['document_type'] == 'edition_pdf'
    assert output['candidates'][0]['metadata']['date_status'] == 'unknown'
    assert output['child_tasks'][0]['source_snapshot'] == task['source_snapshot']
    assert output['child_tasks'][0]['url'].endswith('mare-de-noticias-168/')


@pytest.mark.skipif(not (REAL_ROOT / 'panorama-june.html').exists(), reason='Preserved real edition index required')
def test_real_archive_admission_tail_is_explicit_and_nearby_editions_come_first():
    class Response:
        status_code, headers = 200, {}
        text = (REAL_ROOT / 'panorama-june.html').read_text()
    task = {'url': 'https://panoramarj.com.br/jornais/', 'date_from': '2026-06-27',
        'date_to': '2026-06-29', 'cursor': {}, 'mechanism': {'max_entries': 2}}
    result = discover_edition_archive(task, {'key': 'panorama', 'name': 'Panorama', 'domains': ['panoramarj.com.br']}, lambda url: Response())
    assert result['outcome'] == 'gap' and result['gap_reason'] == 'pdf_edition_archive_entry_limit'
    assert result['next_cursor']['unprocessed_entries'] == 17
    assert result['candidates'][0]['url'] == PANORAMA_URL
    assert len(result['candidates']) == 2


@pytest.mark.skipif(not (REAL_ROOT / 'panorama-archive-root.html').exists(), reason='Preserved publisher archive root required')
def test_real_panorama_month_links_are_pruned_before_pdf_downloads():
    from urllib.parse import parse_qs, urlparse
    class Response:
        status_code, headers = 200, {}
        text = (REAL_ROOT / 'panorama-archive-root.html').read_text()
    source = {'key': 'panorama', 'name': 'Panorama', 'domains': ['panoramarj.com.br']}
    task = {'url': 'https://panoramarj.com.br/jornais/', 'date_from': '2026-08-09', 'date_to': '2026-08-09'}
    result = discover_edition_archive(task, source, lambda url: Response())
    months = [parse_qs(urlparse(c['url']).query)['mes'][0] for c in result['child_tasks']]
    assert months == ['8']
    boundary = discover_edition_archive({**task, 'date_from': '2026-06-01', 'date_to': '2026-09-10'}, source, lambda url: Response())
    months = [parse_qs(urlparse(c['url']).query)['mes'][0] for c in boundary['child_tasks']]
    assert months == ['5', '6', '7', '8', '9']


class Store:
    enabled, prefix = True, 'public-pdf-disposable-test'
    def __init__(self): self.objects = {}
    def upload_bytes(self, raw, key, content_type):
        self.objects[key] = raw
        return True
    def upload_path(self, path, key, content_type):
        self.objects[key] = Path(path).read_bytes()
        return True
    def read_political_object(self, key): return self.objects[key]


class FileResponse:
    status_code, headers = 200, {}
    def __init__(self, path, url): self.path, self.url, self.closed = path, url, False
    def iter_content(self, size):
        with self.path.open('rb') as handle:
            while chunk := handle.read(size):
                yield chunk
    def close(self): self.closed = True


@pytest.fixture
def service(tmp_path, monkeypatch):
    if not DATABASE_URL:
        pytest.skip('POLITICAL_DOCUMENT_TEST_DATABASE_URL must name a disposable PostgreSQL DB')
    if not all((REAL_ROOT / filename).exists() for filename in REAL_HASHES) or not shutil.which('pdftotext'):
        pytest.skip('Preserved real PDFs and Poppler required')
    for filename, expected in REAL_HASHES.items():
        assert hashlib.sha256((REAL_ROOT / filename).read_bytes()).hexdigest() == expected
    base = PoliticalCorpusService
    if not issubclass(base, PoliticalDocumentMixin):
        class DocumentService(PoliticalDocumentMixin, base): pass
        base = DocumentService
    service = base(store=Store(), database_url=DATABASE_URL)
    service.ensure_schema()
    with service._connect() as conn:
        for statement in DOCUMENT_SCHEMA_SQL.split(';'):
            if statement.strip(): conn.execute(statement)
        conn.execute('TRUNCATE political_jobs,political_documents,political_source_leases,political_domain_limits RESTART IDENTITY CASCADE')
    monkeypatch.setenv('POLITICAL_PDF_CACHE', str(tmp_path / 'pdf-cache'))
    yield service
    service.close()


def enqueue(service, *, url=PANORAMA_URL, first='2026-06-01', last='2026-09-10'):
    job = str(uuid.uuid4())
    with service._connect() as conn:
        conn.execute("""INSERT INTO political_jobs(id,kind,status,target_keys,target_snapshots,date_from,date_to,requested_by)
            VALUES (%s,'collect','queued',%s,%s::jsonb,%s,%s,'disposable-real-pdf-test')""",
            (job, [t['key'] for t in TARGETS], json.dumps(TARGETS), first, last))
        candidate = {'url': url, 'title': 'Edição pública preservada', 'source_key': 'panorama', 'source_name': 'Panorama', 'metadata': {}}
        first_task = service.enqueue_document_candidate(conn, job, candidate)
        assert not service.enqueue_document_candidate(conn, job, {**candidate, 'url': url + '#page=2'})
    filename = 'panorama-june.pdf' if url == PANORAMA_URL else 'mare-169.pdf'
    service.fetch = lambda requested, **kwargs: FileResponse(REAL_ROOT / filename, requested)
    return job, first_task


def step(service):
    task = service.claim_task('fetch', worker_id='disposable-document-worker')
    assert task is not None
    return service.process_document_task(task)


def drain(service, limit=25):
    for _ in range(limit):
        task = service.claim_task('fetch', worker_id='disposable-document-worker')
        if not task:
            return
        service.process_document_task(task)
    pytest.fail('Edition did not finish within its real page count')


def test_real_pdf_transactional_page_chain_storage_and_account_scope(service):
    job, _ = enqueue(service)
    output = step(service)
    assert output['documentPages'] == 6 and output['documentsNew'] == 1
    with service._connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM political_tasks WHERE status='queued'").fetchone()['n'] == 1
        assert conn.execute('SELECT COUNT(*) AS n FROM political_articles').fetchone()['n'] == 0
    drain(service)
    pages = service.document_pages(allowed_target_keys=['eduardo_cavaliere', 'pedro_paulo'], page_size=1)
    assert len(pages['items']) == 1 and not pages['hasMore']
    item = pages['items'][0]
    assert item['recordType'] == 'edition_page' and item['title'] == ''
    assert item['editorial_date']['period_to'] == '2026-06-29'
    assert item['editorial_date']['date_precision'] == 'range'
    text = service.document_page_text(item['id'], allowed_target_keys=['eduardo_cavaliere', 'pedro_paulo'])
    assert 'Eduardo Cavaliere' in text['text']
    assert text['documentSha256'] == REAL_HASHES['panorama-june.pdf']
    assert service.document_pages(allowed_target_keys=['other-client'])['items'] == []
    with pytest.raises(PoliticalNotFound):
        service.document_page_text(item['id'], allowed_target_keys=['other-client'])
    with pytest.raises(PoliticalAccessDenied):
        service.document_pages(allowed_target_keys=['other-client'], target_keys=['eduardo_cavaliere'])
    with service._connect() as conn:
        assert conn.execute('SELECT status FROM political_jobs WHERE id=%s', (job,)).fetchone()['status'] == 'succeeded'
        assert conn.execute('SELECT COUNT(*) AS n FROM political_articles').fetchone()['n'] == 0
    assert service.document_counts(allowed_target_keys=['eduardo_cavaliere', 'pedro_paulo'])['edition_pages'] == 1


def test_real_pdf_resume_after_commit_failure_and_object_cache_loss(service, monkeypatch):
    job, _ = enqueue(service)
    step(service)
    task = service.claim_task('fetch', worker_id='worker-that-dies')
    finish = service._finish
    def broken_commit(*args, **kwargs): raise RuntimeError('disposable commit interruption')
    monkeypatch.setattr(service, '_finish', broken_commit)
    with pytest.raises(RuntimeError, match='commit interruption'):
        service.process_document_task(task)
    with service._connect() as conn:
        assert conn.execute('SELECT COUNT(*) AS n FROM political_document_pages').fetchone()['n'] == 0
        conn.execute("UPDATE political_tasks SET leased_until=NOW()-INTERVAL '1 second' WHERE id=%s", (task['id'],))
    monkeypatch.setattr(service, '_finish', finish)
    shutil.rmtree(service._pdf_cache())
    drain(service)
    first = service.document_counts(allowed_target_keys=['eduardo_cavaliere', 'pedro_paulo'])
    enqueue(service)
    drain(service)
    second = service.document_counts(allowed_target_keys=['eduardo_cavaliere', 'pedro_paulo'])
    assert first == second
    with service._connect() as conn:
        assert conn.execute('SELECT COUNT(*) AS n FROM political_document_versions').fetchone()['n'] == 1
        assert conn.execute('SELECT COUNT(*) AS n FROM political_document_pages').fetchone()['n'] == 6
        assert conn.execute('SELECT COUNT(*) AS n FROM political_document_page_versions').fetchone()['n'] == 6
        assert conn.execute('SELECT COUNT(*) AS n FROM political_job_document_pages WHERE reused_text').fetchone()['n'] > 0


def test_real_monthly_cover_date_is_not_download_date_and_stops_outside_window(service):
    enqueue(service, url=MARE_URL, first='2026-08-09', last='2026-08-09')
    step(service)
    output = step(service)
    assert output['outsideWindow'] == 1
    with service._connect() as conn:
        version = conn.execute('SELECT * FROM political_document_versions').fetchone()
        assert version['editorial_date']['date_precision'] == 'month'
        assert version['editorial_date']['period_from'] == '2026-07-01'
        assert version['download_published_at'] == ''
        assert conn.execute('SELECT COUNT(*) AS n FROM political_tasks').fetchone()['n'] == 2
    assert service.document_pages(allowed_target_keys=['eduardo_cavaliere', 'pedro_paulo'])['items'] == []


def test_real_pdf_object_storage_failure_leaves_download_uncommitted(service, monkeypatch):
    _, _ = enqueue(service)
    monkeypatch.setattr(service.store, 'upload_path', lambda *args: False)
    with pytest.raises(DocumentProblem, match='pdf_storage_failed'):
        step(service)
    with service._connect() as conn:
        assert conn.execute('SELECT COUNT(*) AS n FROM political_document_versions').fetchone()['n'] == 0
        assert conn.execute('SELECT COUNT(*) AS n FROM political_document_pages').fetchone()['n'] == 0


def test_updated_original_keeps_authorized_previous_version_and_job_readback(service):
    first_job, _ = enqueue(service)
    drain(service)
    first = service.document_pages(allowed_target_keys=['eduardo_cavaliere'])['items'][0]
    # Controlled update of one document URL using the second preserved public
    # PDF's actual bytes. This is a persistence test, never a publisher claim.
    second_job, _ = enqueue(service)
    service.fetch = lambda requested, **kwargs: FileResponse(REAL_ROOT / 'mare-169.pdf', requested)
    drain(service)
    assert service.document_pages(allowed_target_keys=['eduardo_cavaliere'])['items'][0]['page_version_id'] == first['page_version_id']
    assert service.document_counts(allowed_target_keys=['eduardo_cavaliere', 'pedro_paulo'], job_id=first_job)['edition_pages'] == 1
    assert service.document_counts(allowed_target_keys=['eduardo_cavaliere', 'pedro_paulo'], job_id=second_job)['edition_pages'] == 0
    pinned = service.document_page_text(first['id'], allowed_target_keys=['eduardo_cavaliere'], page_version_id=first['page_version_id'])
    assert pinned['documentSha256'] == REAL_HASHES['panorama-june.pdf']
    with pytest.raises(PoliticalNotFound):
        service.document_page_text(first['id'], allowed_target_keys=['other-client'], page_version_id=first['page_version_id'])


def test_one_heavy_claim_keeps_three_html_slots_and_expired_page_resumes(service, monkeypatch):
    monkeypatch.setenv('POLITICAL_FETCH_CONCURRENCY', '4')
    job, _ = enqueue(service)
    step(service)  # One real edition's page is now pending.
    with service._connect() as conn:
        service.enqueue_document_candidate(conn, job, {'url': MARE_URL, 'source_key': 'mare', 'source_name': 'Maré'})
        for index in range(4):
            service._insert_task(conn, job, 'fetch', {'url': f'https://panoramarj.com.br/noticia-{index}/', 'source_key': 'panorama'})
    with ThreadPoolExecutor(max_workers=6) as pool:
        claimed = list(pool.map(lambda n: service.claim_task('fetch', worker_id=f'claim-{n}'), range(6)))
    claimed = [task for task in claimed if task]
    assert len(claimed) == 4
    heavy = [task for task in claimed if task['payload'].get('document_task')]
    assert len(heavy) == 1 and heavy[0]['payload']['document_task'] == 'page'
    assert len([task for task in claimed if not task['payload'].get('document_task')]) == 3
    with service._connect() as conn:
        conn.execute("UPDATE political_tasks SET leased_until=NOW()-INTERVAL '1 second' WHERE id=%s", (heavy[0]['id'],))
        # Source fairness may select the other publisher first; hold only its
        # queued work to check expired-page eligibility independently of order.
        conn.execute("UPDATE political_tasks SET next_attempt_at=NOW()+INTERVAL '1 hour' WHERE status='queued' AND id<>%s", (heavy[0]['id'],))
    resumed = service.claim_task('fetch', worker_id='replacement-page-worker')
    assert resumed['id'] == heavy[0]['id']
    assert resumed['lease_token'] != heavy[0]['lease_token']
