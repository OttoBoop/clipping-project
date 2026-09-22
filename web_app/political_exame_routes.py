"""Reuse URLs independently advertised in Exame's dated article inventory.

The Academy and BTG Insights category sitemaps advertise broken /invest/<slug> links. Never
guess the missing section: require one other URL with the exact publisher
title, slug and publication timestamp, already discovered in this same job.
This routes discovery, not person matching or cross-job no-match reuse.
"""
from datetime import datetime
from urllib.parse import urlparse

ACADEMY = 'https://exame.com/categorias/invest/academy/sitemap.xml'
BROKEN_CATEGORY_SITEMAPS = {ACADEMY, 'https://exame.com/categorias/invest/btg-insights/sitemap.xml'}


def eligible(candidate):
    parsed = urlparse(candidate.get('url', ''))
    parts = parsed.path.strip('/').split('/')
    return (parsed.hostname == 'exame.com' and len(parts) == 2 and parts[0] == 'invest'
            and candidate.get('metadata', {}).get('sitemap_url') in BROKEN_CATEGORY_SITEMAPS
            and bool(candidate.get('title')) and bool(candidate.get('published_at')))


def find_alternative(candidate, tasks):
    if not eligible(candidate):
        return None
    original = urlparse(candidate['url'])
    matches = {}
    for task in tasks:
        other = task['payload']
        parsed = urlparse(other.get('url', ''))
        parts = parsed.path.strip('/').split('/')
        origin = urlparse(other.get('metadata', {}).get('sitemap_url', ''))
        if (parsed.hostname != 'exame.com' or len(parts) != 3 or parts[0] != 'invest'
                or parts[-1] != original.path.rstrip('/').rsplit('/', 1)[-1]
                or origin.hostname != 'exame.com' or not origin.path.startswith('/artigos/')
                or not origin.path.endswith('/sitemap.xml')
                or other.get('title') != candidate['title']):
            continue
        try:
            first = datetime.fromisoformat(candidate['published_at'])
            second = datetime.fromisoformat(other['published_at'])
            if not first.tzinfo or not second.tzinfo or first != second:
                continue
        except (KeyError, TypeError, ValueError):
            continue
        matches[other['url']] = {'url': other['url'], 'task_id': task['id'],
            'sitemap_url': other['metadata']['sitemap_url'],
            'publication': other['published_at'],
            'basis': 'same_job_publisher_daily_inventory_exact_title_slug_and_publication'}
    return next(iter(matches.values())) if len(matches) == 1 else None


def resolve(conn, job_id, candidates):
    titles = list({c['title'] for c in candidates if eligible(c)})
    if not titles:
        return {}
    tasks = conn.execute("""SELECT id,payload FROM political_tasks
        WHERE job_id=%s AND source_key='exame' AND kind='fetch'
          AND payload->>'title'=ANY(%s)
          AND payload->>'url' LIKE 'https://exame.com/invest/%%'""", (job_id, titles)).fetchall()
    return {c['url']: alternative for c in candidates
            if (alternative := find_alternative(c, tasks))}
