"""RC's explicit monthly post cards can advertise valid short permalinks."""
import json
from types import SimpleNamespace

import pytest

from web_app import political_discovery as discovery

URL = 'https://rc24h.com.br/__trashed-3/'
TITLE = 'CRAS do Mossoró é revitalizado em São Pedro da Aldeia'


def card(url=URL, *, post_type='post', rel='bookmark'):
    return f'<div class="tdb_module_loop td_module_wrap td-cpt-{post_type}"><div class="td-module-meta-info"><h3 class="entry-title td-module-title"><a href="{url}" rel="{rel}">{TITLE}</a></h3></div></div>'


def parsed_row(raw):
    parser = discovery._RCArchiveCards()
    parser.feed(raw)
    return parser.rows[0]


def source():
    return next(row for row in discovery.load_sources() if row['key'] == 'rc24h')


def test_actual_short_permalink_requires_explicit_publisher_post_card_bookmark():
    row = parsed_row(card())
    assert not discovery._allowed_url(URL, source(), article=True)
    assert row['publisher_post_card'] and row['publisher_bookmark']
    assert discovery._rc24h_card_url_allowed(row, source())


@pytest.mark.parametrize('raw', [
    card(post_type='page'), card(rel='nofollow'), card('https://other.example/__trashed-3/'),
    card('https://rc24h.com.br/search/'), card('https://rc24h.com.br/author/'),
    card('https://rc24h.com.br/short.php'), card('https://rc24h.com.br/__trashed-3/?secret=1'),
])
def test_short_permalink_exception_rejects_unproven_cards_or_nonarticle_routes(raw):
    assert not discovery._rc24h_card_url_allowed(parsed_row(raw), source())


def test_monthly_discovery_emits_real_short_card_and_keeps_prior_unknown_gap():
    attrs = {'block_type': 'tdb_loop', 'date_query': {'year': 2026, 'month': 6, 'day': ''}, 'offset': '3', 'limit': '8'}
    html = '<script>var td_ajax_url="https://rc24h.com.br/wp-admin/admin-ajax.php";var tdBlockNonce="public-token";block_month.atts = \'' + json.dumps(attrs) + "';</script>"
    payload = {'td_block_id': 'month', 'td_data': card(), 'td_hide_next': True}
    def fetch(url, **kwargs):
        return SimpleNamespace(status_code=200, headers={}, text=json.dumps(payload) if kwargs.get('method') == 'POST' else html)
    task = {'source_key': 'rc24h', 'strategy': 'rc24h_archive', 'date_from': '2026-06-01',
            'date_to': '2026-06-30', 'month': '2026-06', 'cursor': {'page': 53, 'archive_offset': 3, 'archive_limit': 8}}
    result = discovery.discover(task, fetch)
    candidate, = result['candidates']
    assert result['outcome'] == 'complete' and result['raw_count'] == 1
    assert candidate['url'] == URL.rstrip('/')
    assert candidate['published_at'] == ''  # Publisher article must verify publication.
    assert candidate['metadata']['discovery_short_permalink']
    assert candidate['metadata']['publisher_post_card'] and candidate['metadata']['publisher_bookmark']
    inherited = discovery.discover({**task, 'cursor': {**task['cursor'], 'parse_gap': True}}, fetch)
    assert inherited['outcome'] == 'gap' and inherited['gap_reason'] == 'rc24h_archive_parse_gap'
