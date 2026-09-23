"""Elizeu Pires' public dated API: preserve responses and reconcile page totals.

Reuse the shared WordPress body batches and domain transport. No name query or
Google fallback is involved; matching happens on each article's editorial body.
"""
from __future__ import annotations

import hashlib
import json

VERSION = 'elizeu-public-api-1'


def discover(task, source, fetch, wordpress):
    captured = []

    def observed(url):
        response = fetch(url)
        captured.append((url, response))
        return response

    result = wordpress(task, source, observed)
    url, response = captured[-1]
    raw = response.content
    rows = json.loads(response.text)
    cursor = task.get('cursor') or {}
    page = int(cursor.get('page', 1))
    size = min(50, max(1, int(task['mechanism'].get('page_size', 50))))
    total_raw = response.headers.get('X-WP-Total') or response.headers.get('x-wp-total')
    total = int(total_raw) if total_raw and str(total_raw).isdigit() else None
    seen = int(cursor.get('inventory_rows', 0)) + (len(rows) if isinstance(rows, list) else 0)
    gap = ''
    if total is None:
        gap = 'elizeu_inventory_total_unverified'
    elif cursor.get('inventory_total') is not None and cursor['inventory_total'] != total:
        gap = 'elizeu_inventory_changed_during_pagination'
    elif isinstance(rows, list):
        expected = min(size, max(0, total - (page - 1) * size))
        if len(rows) != expected:
            gap = 'elizeu_inventory_page_count_mismatch'
        elif not result.get('next_cursor') and seen != total:
            gap = 'elizeu_inventory_total_mismatch'
        ids = [row.get('id') for row in rows if isinstance(row, dict)]
        if len(ids) != len(rows) or len(set(ids)) != len(ids):
            gap = 'elizeu_inventory_duplicate_or_invalid_ids'
        previous = set(cursor.get('inventory_ids', []))
        if previous.intersection(ids):
            gap = 'elizeu_inventory_overlapping_pages'
        if result.get('next_cursor'):
            result['next_cursor'].update(inventory_ids=list(previous.union(ids)),
                inventory_rows=seen, inventory_total=total)
    else:
        gap = 'elizeu_inventory_unexpected_response'
    # Keep the original, more specific protocol diagnosis when one exists.
    if gap and result['outcome'] != 'gap':
        result.update(outcome='gap', gap_reason=gap, next_cursor=None)
    result['archive_response'] = raw
    result['publisher_archive'] = {
        'version': VERSION, 'url': url, 'responseHash': hashlib.sha256(raw).hexdigest(),
        'page': page, 'rawRows': len(rows) if isinstance(rows, list) else 0,
        'rowsTraversed': seen, 'announcedTotal': total,
        'dateFrom': task['date_from'], 'dateTo': task['date_to'],
        'dateFilterZone': 'America/Sao_Paulo', 'articleDateField': 'date_gmt',
        'gapReason': result.get('gap_reason', ''),
    }
    return result
