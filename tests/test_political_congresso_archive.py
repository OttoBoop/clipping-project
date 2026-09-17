"""Public SSR pages preserved with provenance; mutations exercise failure paths."""
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from bs4 import BeautifulSoup
import pytest

from web_app import political_congresso_archive as archive
from web_app import political_expanded_discovery as expanded
from web_app.political_discovery import DiscoveryError

ROOT = Path(__file__).parent / 'fixtures/political_congresso_archive'


def fixture(product='noticia', page=2, start='2026-06-01', end='2026-09-17'):
    source = next(s for s in expanded.load_expanded_sources() if s['key'] == 'congresso_em_foco')
    task = next(t for t in expanded.build_expanded_tasks(source, start, end, [])
                if t['strategy'] == 'expanded_congresso_archive' and t['mechanism']['product'] == product)
    task['cursor'] = {'page': page}
    name = 'jun-newsletters.html.gz' if product == 'informativo' else f'{product}-{page}.html.gz'
    proof = next(r for r in json.loads((ROOT/'provenance.json').read_text()) if r['file'] == name)
    raw = gzip.decompress((ROOT/name).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == proof['sha256']
    return task, source, SimpleNamespace(content=raw, status_code=200, url=proof['url'], headers={})


def run(task, source, response):
    return expanded.discover_expanded(task, source, lambda *a, **k: response)


def mutate(response, change):
    soup = BeautifulSoup(response.content, 'html.parser')
    tag = soup.find('script', id='ng-state')
    state = json.loads(tag.text)
    change(state)
    tag.string = json.dumps(state).replace('</', '<\\/')
    response.content = str(soup).encode()


def rows(state, product='noticia'):
    code = archive.PRODUCTS[product]
    return next(v['Data']['widgetassets'] for k, v in state.items()
                if k.startswith('key_/Widget/Get_' + code + '_' + code + '_'))


def test_real_editorial_rows_are_not_filtered_by_names_or_sidebar():
    task, source, response = fixture()
    result = run(task, source, response)
    assert len(result['candidates']) == result['raw_count'] == 20
    assert all(c['metadata']['archive_widget'] == 'NOTICIAS_LISTA' for c in result['candidates'])
    assert result['next_cursor']['page'] == 3
    assert result['archive_response'] == response.content
    assert not result['publisher_archive']['headlineMatchingUsed']


def test_real_first_page_keeps_separate_featured_news_and_next_page_is_distinct():
    first = run(*fixture(page=1))
    second = run(*fixture(page=2))
    assert len(first['candidates']) == 21
    assert sum(c['metadata']['archive_featured'] for c in first['candidates']) == 1
    assert {c['url'] for c in first['candidates']}.isdisjoint(c['url'] for c in second['candidates'])


def test_actual_june_archive_keeps_june_first_and_requires_two_older_pages():
    task, source, response = fixture(page=120)
    result = run(task, source, response)
    assert any(c['published_at'].startswith('2026-06-01') for c in result['candidates'])
    assert result['outcome'] == 'continue'
    task['date_from'] = '2026-08-09'
    first = run(task, source, response)
    assert not first['candidates'] and first['outcome'] == 'continue'
    task['cursor'].update(older_pages=1)
    second = run(task, source, response)
    assert second['outcome'] == 'complete'
    assert second['publisher_archive']['stoppedBy'] == 'dated_boundary'


@pytest.mark.parametrize('product', ['artigo', 'coluna', 'informativo'])
def test_other_products_use_their_own_real_dated_widget(product):
    result = run(*fixture(product))
    assert len(result['candidates']) == (20 if product == 'informativo' else 10)
    assert all(c['metadata']['record_product'] == product for c in result['candidates'])
    assert result['outcome'] == ('complete' if product == 'informativo' else 'continue')


def test_unknown_dates_are_not_invented_and_prevent_older_boundary():
    task, source, response = fixture(page=120, start='2026-08-09', end='2026-08-09')
    mutate(response, lambda state: rows(state)[0]['asset'].update(pubdate=None))
    task['cursor']['older_pages'] = 1
    result = run(task, source, response)
    assert result['outcome'] == 'continue' and len(result['candidates']) == 1
    assert not result['candidates'][0]['published_at']
    assert result['publisher_archive']['unknownDatesThisPage'] == 1


def test_repetition_cap_disorder_and_wrong_ssr_context_are_visible():
    task, source, response = fixture()
    original = run(task, source, response)
    task['cursor']['fingerprints'] = [original['publisher_archive']['fingerprint']]
    assert 'repeated_page' in run(task, source, response)['gap_reason']
    task['cursor'] = {'page': 2}
    task['mechanism']['max_pages'] = 2
    assert 'page_cap' in run(task, source, response)['gap_reason']
    task['cursor']['page'] = 3
    with pytest.raises(DiscoveryError, match='context_missing'):
        run(task, source, response)
    task, source, response = fixture(page=120, start='2026-08-09')
    task['cursor'].update(older_pages=1)
    mutate(response, lambda state: rows(state).reverse())
    result = run(task, source, response)
    assert result['outcome'] == 'continue' and result['publisher_archive']['orderingUnverified']


def test_429_and_invalid_payload_do_not_complete_archive():
    task, source, response = fixture()
    response.status_code = 429
    response.headers['Retry-After'] = '21'
    with pytest.raises(DiscoveryError) as error:
        run(task, source, response)
    assert error.value.retryable and error.value.retry_after == 21
    response.status_code = 200
    response.content = b'<html>temporarily unavailable</html>'
    with pytest.raises(DiscoveryError, match='state_missing'):
        run(task, source, response)


def test_archive_parser_runs_without_optional_site_packages():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, '-S', '-c',
        'import gzip; from pathlib import Path; from web_app.political_congresso_archive import _state; '
        'assert len(_state(gzip.decompress(Path("tests/fixtures/political_congresso_archive/noticia-2.html.gz").read_bytes()))) > 2'],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_real_public_amp_keeps_editorial_body_and_its_own_day():
    from web_app.political_discovery import extract_article
    proof = next(r for r in json.loads((ROOT/'provenance.json').read_text()) if r['file'] == 'real-amp-120758.html.gz')
    raw = gzip.decompress((ROOT/proof['file']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == proof['sha256']
    article = extract_article(raw.decode(), proof['url'])
    assert article['published_at'] == '2026-07-25T03:00:00+00:00'
    assert article['publication_date_evidence']['precision'] == 'day'
    assert article['extraction_method'] == 'publisher_selector:#article-content'
    assert 'O Partido Liberal (PL) realiza neste sábado' in article['full_text']
    assert 'A reaproximação é vista como estratégica' in article['full_text']
    assert 'Publicidade' not in article['full_text']
    assert 'Cotada para vice de Flávio, Zanatta' not in article['full_text']
    absent = raw.decode().replace('class="publication-date"', 'class="missing-publication"')
    undated = extract_article(absent, proof['url'])
    assert not undated['published_at']
    assert undated['publication_date_evidence']['method'] == 'missing_original_post_date'
