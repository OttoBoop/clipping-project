"""Publisher-advertised public search; no login, snippets never become body text.

The current API ignores page size/page offsets. A response of 500 results is
therefore treated as capped, with durable date-window splitting down to a day.
"""
from datetime import date, datetime, time, timedelta
import hashlib
import json

ENDPOINT = 'https://front.congressoemfoco.com.br/Search/Query'
VERSION = 'congresso-public-search-1'
LIMIT = 500


def build_tasks(route, snapshots):
    queries = {}
    for row in snapshots:
        name = str(row.get('display_name') or row.get('label') or row.get('name') or '').strip()
        if not name:
            continue
        item = queries.setdefault(name.casefold(), {'query': name, 'target_ids': []})
        key = str(row.get('key') or row.get('id') or '')
        if key and key not in item['target_ids']:
            item['target_ids'].append(key)
    return [{**route, **item, 'url': route['mechanism']['url']} for item in queries.values()]


def discover(task, source, fetch):
    from . import political_expanded_discovery as expanded
    core = expanded._core()
    mechanism = task.get('mechanism') or {}
    if source.get('key') != 'congresso_em_foco' or mechanism.get('url') != ENDPOINT:
        raise core.DiscoveryError('congresso_search_invalid_endpoint', retryable=False)
    query = str(task.get('query') or '').strip()
    if not query or len(query) > 250:
        raise core.DiscoveryError('congresso_search_invalid_query', retryable=False)
    start, end = date.fromisoformat(task['date_from']), date.fromisoformat(task['date_to'])
    payload = {'query': query, 'searchcode': mechanism.get('searchcode', 'DEFNEW'),
               'usertoken': None, 'page': 1, 'pagesize': LIMIT,
               'datefrom': datetime.combine(start, time.min, core.SAO_PAULO).isoformat(),
               'dateto': datetime.combine(end, time.max, core.SAO_PAULO).isoformat()}
    response = core._get(fetch, ENDPOINT, method='POST', data=json.dumps(payload),
                         headers={'Content-Type': 'application/json'})
    if not expanded._allowed(getattr(response, 'url', '') or ENDPOINT, source):
        raise core.DiscoveryError('congresso_search_response_domain', retryable=False)
    try:
        document = json.loads(response.content)
    except (ValueError, TypeError) as exc:
        raise core.DiscoveryError('congresso_search_invalid_json', retryable=False) from exc
    data = document.get('Data') if isinstance(document, dict) else None
    if not isinstance(document, dict) or document.get('Code') != 0 or not isinstance(data, dict):
        raise core.DiscoveryError('congresso_search_invalid_result', retryable=False)
    if data.get('searcherroroccured') or data.get('resultprocessing'):
        raise core.DiscoveryError('congresso_search_processing_error')
    rows = data.get('results')
    # The publisher's verified empty response uses null, not an empty array.
    # Require the explicit zero counters; a malformed/missing result is a gap.
    if ('results' in data and rows is None and type(data.get('qty')) is int
            and data['qty'] == 0 and data.get('more') is False
            and data.get('page') == 0 and data.get('pageqty') == 0):
        rows = []
    if not isinstance(rows, list):
        raise core.DiscoveryError('congresso_search_invalid_result', retryable=False)
    qty = data.get('qty')
    pages = data.get('pageqty')
    if type(qty) is not int or qty < 0 or qty < len(rows) or len(rows) > LIMIT or type(pages) is not int or pages < 0:
        raise core.DiscoveryError('congresso_search_invalid_count', retryable=False)
    digest = hashlib.sha256(response.content).hexdigest()
    candidates, outside, invalid = [], 0, 0
    for row in rows:
        if not isinstance(row, dict) or type(row.get('articleKey')) is not int:
            invalid += 1
            continue
        url = row.get('URL', '')
        try:
            allowed = isinstance(url, str) and expanded._allowed(url, source, article=True)
        except ValueError:
            allowed = False
        if not allowed:
            invalid += 1
            continue
        published = core.parse_publication_date(row.get('date'))
        if not core.in_window(published, task['date_from'], task['date_to']):
            outside += 1
            continue
        candidates.append(expanded._candidate(source, url, str(row.get('title') or ''), published,
            str(row.get('summary') or ''), {'discovery_format': VERSION, 'public_search_query': query,
                'public_search_endpoint': ENDPOINT, 'public_search_record_id': row['articleKey'],
                'public_search_response_hash': digest, 'public_search_date_reported': row.get('date'),
                'public_search_highlight': core.html_to_text(str(row.get('highlight') or ''))[:1500]}))
    proof = {'version': VERSION, 'query': query, 'responseHash': digest, 'reportedResults': qty,
             'returnedResults': len(rows), 'outsideWindow': outside, 'invalidRows': invalid,
             'paginationUsed': False, 'bodyTextProvided': False}
    saturated = qty >= LIMIT or qty > len(rows) or data.get('more') or pages > 1
    if saturated and start < end:
        middle = start + timedelta(days=(end - start).days // 2)
        children = [{**task, 'date_from': first.isoformat(), 'date_to': last.isoformat(), 'cursor': {}}
                    for first, last in [(start, middle), (middle + timedelta(days=1), end)]]
        return expanded._result(candidates, raw_count=len(rows), outcome='split',
                                child_tasks=children, publisher_search=proof)
    reasons = []
    if saturated:
        reasons.append('congresso_search_single_day_limit')
    if outside:
        reasons.append('congresso_search_ignored_date_filter')
    if invalid:
        reasons.append('congresso_search_invalid_rows')
    return expanded._result(candidates, raw_count=len(rows), outcome='gap' if reasons else 'complete',
                            gap_reason=';'.join(reasons), publisher_search=proof)
