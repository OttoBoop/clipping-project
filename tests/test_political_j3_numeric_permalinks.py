"""Verified J3 API IDs/date paths retain stories the generic slug filter misses."""
import json
from types import SimpleNamespace

import pytest

from web_app import political_discovery as discovery


def api_post(**changes):
    return {
        'id': 494660,
        'link': 'https://j3news.com/2026/06/07/494660/',
        'date': '2026-06-07T02:08:00',
        'date_gmt': '2026-06-07T05:08:00',
        'title': {'rendered': 'Endurance Brasil desembarca em Interlagos para 2ª e 3ª etapas'},
        'excerpt': {'rendered': ''},
        'content': {'rendered': '<img src="/editorial.jpg">', 'protected': False},
        **changes,
    }


def run_page(posts, source_key='j3news'):
    task = {'source_key': source_key, 'strategy': 'wordpress', 'date_from': '2026-06-01',
            'date_to': '2026-06-07', 'cursor': {'page': 1}}
    response = SimpleNamespace(status_code=200, text=json.dumps(posts), headers={'X-WP-TotalPages': '1'})
    return discovery.discover(task, lambda _: response)


def test_actual_numeric_j3_post_is_discovered_without_claiming_image_as_full_text():
    post = api_post()
    source = next(row for row in discovery.load_sources() if row['key'] == 'j3news')
    assert not discovery._allowed_url(post['link'], source, article=True)
    result = run_page([post])
    assert result['raw_count'] == 1 and result['outcome'] == 'complete'
    candidate, = result['candidates']
    assert candidate['url'] == post['link'].rstrip('/')
    assert candidate['published_at'] == '2026-06-07T05:08:00+00:00'
    assert candidate['metadata']['wordpress_numeric_permalink_verified'] is True
    assert candidate['metadata']['wordpress_id'] == 494660
    assert 'full_text' not in candidate
    assert result['body_batch']['records'][0]['content_html'] == '<img src="/editorial.jpg">'


@pytest.mark.parametrize('changes', [
    {'id': 494661},
    {'id': '494660'},
    {'link': 'https://other.example/2026/06/07/494660/'},
    {'link': 'https://j3news.com/2026/06/08/494660/'},
    {'link': 'https://j3news.com/2026/06/07/494660/?other=1'},
    {'date': '', 'date_gmt': ''},
    {'date': '', 'date_gmt': 'not-a-date'},
])
def test_numeric_exception_requires_matching_publisher_api_identity_and_date(changes):
    assert run_page([api_post(**changes)])['candidates'] == []


def test_numeric_permalink_agreement_uses_sao_paulo_publication_day():
    result = run_page([api_post(date='2026-06-07T23:30:00', date_gmt='2026-06-08T02:30:00')])
    assert len(result['candidates']) == 1
    assert result['candidates'][0]['published_at'] == '2026-06-08T02:30:00+00:00'


def test_j3_exception_does_not_change_other_publishers_or_generic_url_filter():
    post = api_post(link='https://temporealrj.com/2026/06/07/494660/')
    assert run_page([post], 'tempo_real_rj')['candidates'] == []
