"""Public publisher pagination; local assertions never enter collection totals."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from web_app.political_discovery import DiscoveryError, build_tasks, discover, load_sources

ACTION = '404f01c3d0caa10b02ca3723e7fc61b7cbf5d9c8aa'
SOURCE = next(r for r in load_sources() if r['key'] == 'metropoles')
ROWS = json.loads((Path(__file__).parent / 'fixtures/metropoles-public-list-real-20260910.json').read_text())['rows']


def task(**changes):
    return {'source_key': 'metropoles', 'strategy': 'metropoles_archive', 'section': 'brasil',
            'date_from': '2026-09-09', 'date_to': '2026-09-09', 'cursor': {'action_id': ACTION}, **changes}


def response(rows=None, status=200, text=None, headers=None):
    return SimpleNamespace(status_code=status, headers=headers or {},
        text=text if text is not None else '0:{"a":"$@1"}\n1:' + json.dumps({'data': rows if rows is not None else ROWS}))


def test_real_publisher_page_has_direct_urls_and_resumable_local_date_cursor():
    calls = []
    def fetch(url, **kwargs):
        calls.append((url, kwargs))
        return response()
    result = discover(task(), fetch)
    assert len(result['candidates']) == len(ROWS)
    assert all(c['url'].startswith('https://www.metropoles.com/brasil/') for c in result['candidates'])
    assert result['outcome'] == 'continue'
    assert result['next_cursor']['after'] == min(r['authority']['publishedAt'] for r in ROWS)
    assert json.loads(calls[0][1]['data']) == [{'startAfter': '2026-09-10 00:00:00', 'slug': 'brasil'}]
    discover(task(cursor=result['next_cursor']), fetch)
    assert json.loads(calls[1][1]['data'])[0]['startAfter'] == result['next_cursor']['after']
    assert all(call[1]['method'] == 'POST' for call in calls)


def test_action_identifier_is_checkpointed_before_first_archive_post():
    calls = []
    def fetch(url, **kwargs):
        calls.append((url, kwargs))
        return response(text=f'(0,n.createServerReference)("{ACTION}",n.callServer,void 0,n.findSourceMapURL,"getMoreArticlesAction")')
    result = discover(task(cursor={}), fetch)
    assert result['next_cursor']['action_id'] == ACTION
    assert not result['candidates'] and len(calls) == 1 and not calls[0][1].get('method')


def test_expired_bundle_hint_discovers_current_public_scripts_in_bounded_steps():
    asset = 'https://assets-v4.metroimg.com/_next/static/chunks/current.js'
    def fetch(url, **kwargs):
        if url == SOURCE['public_archive_action_bundle_hint']:
            return response(status=404)
        if url == 'https://www.metropoles.com/brasil':
            return response(text=f'<script src="{asset}"></script>')
        assert url == asset
        return response(text=f'createServerReference)("{ACTION}",x,y,z,"getMoreArticlesAction")')
    first = discover(task(cursor={}), fetch)
    assert first['next_cursor']['action_assets'] == [asset]
    second = discover(task(cursor=first['next_cursor']), fetch)
    assert second['next_cursor']['action_id'] == ACTION


def test_sao_paulo_end_day_boundaries_and_unknown_date_review():
    rows = [copy.deepcopy(ROWS[0]) for _ in range(5)]
    for row, stamp in zip(rows, ['2026-09-10 00:00:00', '2026-09-09 23:59:59',
                                '2026-09-09 00:00:00', '2026-09-08 23:59:59', '']):
        row['authority']['publishedAt'] = stamp
    result = discover(task(), lambda *a, **k: response(rows))
    assert [c['published_at'] for c in result['candidates']] == ['2026-09-10T02:59:59+00:00', '2026-09-09T03:00:00+00:00', '']
    assert result['candidates'][-1]['metadata']['needs_date_review']
    assert result['outcome'] == 'gap' and 'parse_gap' in result['gap_reason']


def test_missing_dates_and_stalled_pages_are_gaps_not_completed_searches():
    rows = copy.deepcopy(ROWS)
    for row in rows:
        row['authority']['publishedAt'] = ''
    assert discover(task(), lambda *a, **k: response(rows))['gap_reason'] == 'metropoles_archive_missing_dates'
    cursor = {'action_id': ACTION, 'after': min(r['authority']['publishedAt'] for r in ROWS)}
    assert discover(task(cursor=cursor), lambda *a, **k: response())['gap_reason'] == 'metropoles_archive_stalled_cursor'


def test_429_preserves_retry_after_and_empty_page_preserves_prior_parse_gap():
    with pytest.raises(DiscoveryError) as error:
        discover(task(), lambda *a, **k: response(status=429, headers={'Retry-After': '90'}))
    assert error.value.retryable and error.value.retry_after == 90
    assert discover(task(cursor={'action_id': ACTION, 'parse_gap': True}), lambda *a, **k: response([]))['outcome'] == 'gap'


def test_shared_discovery_does_not_multiply_public_archive_by_person():
    targets = [{'key': f'person_{i}', 'display_name': f'Person {i}'} for i in range(11)]
    tasks = build_tasks(targets, '2026-06-01', '2026-09-09', ['metropoles'])
    public = [t for t in tasks if t['strategy'] == 'metropoles_archive']
    assert len(public) == 1 and len(public[0]['target_ids']) == 11
    assert {t['target_ids'][0] for t in tasks if t['strategy'] == 'google_news'} == {t['key'] for t in targets}
