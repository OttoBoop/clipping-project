"""Provenance and bounded reuse of Exame's advertised public WordPress API."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

METHOD = 'exame_public_wordpress_api'


def publication(row, response_hash, endpoint):
    evidence = {'method': METHOD, 'publisher_post_id': row.get('id'),
                'response_sha256': response_hash, 'api_url': endpoint,
                'date_local': row.get('date'), 'date_gmt': row.get('date_gmt')}
    try:
        local = datetime.fromisoformat(row['date']).replace(tzinfo=ZoneInfo('America/Sao_Paulo'))
        gmt = datetime.fromisoformat(row['date_gmt']).replace(tzinfo=timezone.utc)
        if local != gmt:
            raise ValueError('publisher clock disagreement')
    except (KeyError, ValueError, TypeError):
        return '', {**evidence, 'method': 'exame_api_date_unverified'}
    return gmt.isoformat(), evidence


def cache_candidate(candidate):
    metadata = candidate.get('metadata') or {}
    if (candidate.get('source_key') != 'exame' or not candidate.get('body_batch_ref')
            or (metadata.get('publication_date_evidence') or {}).get('method') != METHOD):
        return None
    return {k: candidate[k] for k in ('url', 'source_key', 'published_at', 'body_batch_ref')} | {
        'metadata': {k: metadata[k] for k in ('wordpress_id', 'publication_date_evidence')}}


def reuse_candidate(original, cached):
    cached = cache_candidate(cached)
    if not cached or cached['url'] != original.get('url') or original.get('source_key') != 'exame':
        return original
    return {**original, 'body_batch_ref': cached['body_batch_ref'],
            'published_at': cached['published_at'],
            'metadata': {**(original.get('metadata') or {}), **cached['metadata'],
                         'public_api_body_reused': True}}
