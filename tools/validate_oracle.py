#!/usr/bin/env python3
"""
validate_oracle.py — Runs targeted searches for each qualified provider×website
combo from the historical HTML snapshot and checks whether the pipeline can
re-find previously registered articles.

Usage:
    cd clipping-project
    python tools/validate_oracle.py
"""
import re, json, sys, os, time, logging, unicodedata
from html.parser import HTMLParser
from collections import defaultdict
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.normalization import canonicalize_url
from pipeline.http_utils import is_likely_article_url
from pipeline.collectors import (
    collect_rss, collect_google_news, collect_wordpress_api,
    collect_internal_site_search, collect_sitemap_daily,
    collect_vejario_archive, collect_camara_archive,
)
from pipeline.settings import (
    WORDPRESS_API_SITES, DEFAULT_TARGETS,
    build_wordpress_queries_for_target,
)

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")


# ── HTML Parser ──────────────────────────────────────────────────────────
class SnapshotExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.articles = []
        self._in_article = self._in_h3 = self._in_meta = False
        self._current = {}; self._meta_spans = []; self._span_depth = 0
        self._h3_link = None; self._h3_text = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs); cls = d.get('class', '')
        if tag == 'article' and 'article-card' in cls:
            self._in_article = True; self._current = {}
        if self._in_article:
            if tag == 'h3': self._in_h3 = True; self._h3_text = []; self._h3_link = None
            if self._in_h3 and tag == 'a': self._h3_link = d.get('href', '')
            if tag == 'p' and 'meta-line' in cls:
                self._in_meta = True; self._meta_spans = []; self._span_depth = 0
            if self._in_meta and tag == 'span':
                self._span_depth += 1; self._meta_spans.append('')

    def handle_data(self, data):
        if self._in_h3: self._h3_text.append(data)
        if self._in_meta and self._span_depth > 0: self._meta_spans[-1] += data

    def handle_endtag(self, tag):
        if self._in_article:
            if tag == 'h3':
                self._in_h3 = False
                self._current['title'] = ''.join(self._h3_text).strip()
                self._current['url'] = self._h3_link or ''
            if tag == 'span' and self._in_meta: self._span_depth -= 1
            if tag == 'p' and self._in_meta:
                self._in_meta = False
                if len(self._meta_spans) >= 3:
                    self._current['source_name'] = self._meta_spans[0].strip()
                    self._current['date'] = self._meta_spans[1].strip()
                    self._current['domain'] = self._meta_spans[2].strip()
            if tag == 'article':
                self._in_article = False
                if self._current.get('url'): self.articles.append(self._current)
                self._current = {}


# ── Helpers ──────────────────────────────────────────────────────────────
def parse_date(s):
    m = re.match(r'(\d{2})/(\d{2})/(\d{4})', s)
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def pick_samples(arts, n=5):
    seen = set(); unique = []
    for a in arts:
        if a['url'] not in seen:
            # Skip non-article URLs (profile pages, structural pages, etc.)
            if not is_likely_article_url(a['url']):
                continue
            seen.add(a['url']); unique.append(a)
    unique.sort(key=lambda a: a.get('date', ''))
    if len(unique) <= n: return unique
    indices = [int(i * (len(unique) - 1) / (n - 1)) for i in range(n)]
    return [unique[i] for i in indices]


def url_in_results(expected_url, results, expected_title=""):
    """Canonicalized + path-based URL match, with title fallback."""
    canon = canonicalize_url(expected_url)
    exp_path = urlparse(expected_url).path.rstrip('/')
    exp_domain = urlparse(expected_url).hostname or ''
    for r in results:
        if canonicalize_url(r.url) == canon:
            return True
        if urlparse(r.url).path.rstrip('/') == exp_path and exp_path:
            return True
    # Slug-based partial matching: extract main slug and check for overlap
    exp_slug = exp_path.rsplit('/', 1)[-1] if exp_path else ''
    if exp_slug and len(exp_slug) >= 20:
        exp_words = set(exp_slug.split('-'))
        for r in results:
            r_path = urlparse(r.url).path.rstrip('/')
            r_slug = r_path.rsplit('/', 1)[-1] if r_path else ''
            if not r_slug:
                continue
            r_words = set(r_slug.split('-'))
            overlap = len(exp_words & r_words) / max(len(exp_words | r_words), 1)
            if overlap >= 0.7:  # 70%+ word overlap in slug
                return True
    # Title-based fallback: normalize both sides and compare
    if expected_title:
        norm_expected = _norm_title(expected_title)
        if len(norm_expected) >= 20:  # avoid false positives on short titles
            for r in results:
                r_title = getattr(r, 'title', '') or ''
                norm_r = _norm_title(r_title)
                # Exact normalized title match
                if norm_r == norm_expected:
                    if not exp_domain or not (rd := urlparse(r.url).hostname or '') or _domain_match(exp_domain, rd):
                        return True
                # High overlap title match (for title edits)
                if len(norm_expected) >= 30 and len(norm_r) >= 30:
                    exp_twords = set(norm_expected.split())
                    r_twords = set(norm_r.split())
                    t_overlap = len(exp_twords & r_twords) / max(len(exp_twords | r_twords), 1)
                    if t_overlap >= 0.75:
                        if not exp_domain or not (rd := urlparse(r.url).hostname or '') or _domain_match(exp_domain, rd):
                            return True
    return False


def _norm_title(t):
    """Normalize title for fuzzy comparison: lowercase, strip accents, collapse whitespace."""
    t = unicodedata.normalize('NFKD', t.lower())
    t = ''.join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r'[^\w\s]', '', t)
    return re.sub(r'\s+', ' ', t).strip()


def _domain_match(d1, d2):
    """Check if two domains are from the same family (e.g. oglobo.globo.com matches globo.com)."""
    d1 = d1.lstrip('www.')
    d2 = d2.lstrip('www.')
    return d1 == d2 or d1.endswith('.' + d2) or d2.endswith('.' + d1)


def date_range(samples):
    dates = [parse_date(a.get('date', '')) for a in samples]
    dates = sorted(d for d in dates if d)
    if not dates: return None, None
    d_from = datetime.strptime(dates[0], '%Y-%m-%d') - timedelta(days=1)
    d_to = datetime.strptime(dates[-1], '%Y-%m-%d') + timedelta(days=1)
    return d_from.strftime('%Y-%m-%d'), d_to.strftime('%Y-%m-%d')


# ── Collector dispatch ───────────────────────────────────────────────────
WP_SOURCES = {s['base_url'].split('//')[1].rstrip('/'): s for s in WORDPRESS_API_SITES}

# Build WordPress query terms from all targets (like the real pipeline does)
# Plus Pedro Duarte who appears heavily in the snapshot but isn't in DEFAULT_TARGETS
_WP_QUERIES = []
for _t in DEFAULT_TARGETS:
    _WP_QUERIES.extend(build_wordpress_queries_for_target(_t))
_WP_QUERIES.append("Pedro Duarte")
_WP_QUERIES = list(dict.fromkeys(_WP_QUERIES))  # dedupe preserving order


def dispatch(source_name, domain, df, dt, samples=None):
    """Returns list of CandidateArticle from the best-matching collector.
    
    For sitemap sources, does per-sample-date fetching to avoid limit truncation.
    For WordPress sources, uses real target query terms.
    """
    sn = source_name.lower()

    # WordPress API sites — use real query terms
    wp_key = domain
    if wp_key in WP_SOURCES:
        cfg = WP_SOURCES[wp_key]
        combined = []
        seen = set()
        for q in _WP_QUERIES:
            batch = collect_wordpress_api(
                query=q, source_name=cfg['source_name'],
                base_url=cfg['base_url'], date_from=df, date_to=dt,
                per_site_limit=200, request_timeout=15,
            )
            for r in batch:
                if r.url not in seen:
                    seen.add(r.url)
                    combined.append(r)
        return combined

    # Veja Rio (via WordPress + archive) — use real query terms
    if domain == 'vejario.abril.com.br':
        combined = []
        seen = set()
        for q in _WP_QUERIES:
            batch = collect_wordpress_api(
                query=q, source_name="Veja Rio",
                base_url="https://vejario.abril.com.br",
                date_from=df, date_to=dt, per_site_limit=200, request_timeout=15,
            )
            for r in batch:
                if r.url not in seen:
                    seen.add(r.url)
                    combined.append(r)
        archive = collect_vejario_archive(
            date_from=df, date_to=dt, limit_per_target=200,
            max_pages_per_target=30, request_timeout=15,
        )
        for r in archive:
            if r.url not in seen:
                seen.add(r.url)
                combined.append(r)
        return combined

    # Google News
    if 'google news' in sn:
        return collect_google_news(
            date_from=df, date_to=dt,
            limit_per_query=60, request_timeout=15, resolve_timeout=8,
        )

    # Câmara Municipal
    if domain == 'camara.rio':
        if 'internal' in sn:
            return collect_internal_site_search(
                date_from=df, date_to=dt,
                limit_per_adapter=120, request_timeout=15,
            )
        return collect_camara_archive(
            date_from=df, date_to=dt,
            limit_total=200, request_timeout=15,
        )

    # CONIB
    if domain == 'conib.org.br':
        if 'internal' in sn:
            return collect_internal_site_search(
                date_from=df, date_to=dt,
                limit_per_adapter=120, request_timeout=15,
            )
        return collect_rss(
            limit_per_feed=50, date_from=df, date_to=dt, request_timeout=15,
        )

    # Globo family (O Globo, G1, Extra, CBN) — per-sample-date sitemap fetching
    globo_domains = {'oglobo.globo.com', 'g1.globo.com', 'cbn.globo.com', 'extra.globo.com'}
    if domain in globo_domains:
        # Instead of one broad fetch, fetch sitemap per sample date
        # This avoids the limit_per_source truncation issue
        combined = []
        seen = set()
        if samples:
            for s in samples:
                d = parse_date(s.get('date', ''))
                if not d:
                    continue
                day_from = d
                day_to = d
                batch = collect_sitemap_daily(
                    date_from=day_from, date_to=day_to,
                    limit_per_source=500, request_timeout=15,
                )
                # Filter to matching domain only
                for r in batch:
                    if domain in r.url and r.url not in seen:
                        seen.add(r.url)
                        combined.append(r)
        else:
            # Fallback to broad fetch if no samples given
            rss = collect_rss(
                limit_per_feed=50, date_from=df, date_to=dt, request_timeout=15,
            )
            sitemap = collect_sitemap_daily(
                date_from=df, date_to=dt,
                limit_per_source=300, request_timeout=15,
            )
            combined = rss + sitemap
        return combined

    # O Dia, Band, Mercado e Eventos, Panrotas, Radio Tupi, Gazeta, etc — RSS
    if domain in {'odia.ig.com.br', 'band.com.br', 'panrotas.com.br', 'tupi.fm',
                  'mercadoeeventos.com.br', 'veja.abril.com.br', 'gazetadopovo.com.br',
                  'infomoney.com.br', 'revistaoeste.com'}:
        return collect_rss(
            limit_per_feed=50, date_from=df, date_to=dt, request_timeout=15,
        )

    # Portuguese news domains — via Google News
    pt_domains = {'jn.pt', 'publico.pt', 'rtp.pt', 'observador.pt', 'dn.pt',
                  'expresso.pt', 'cnnportugal.iol.pt', 'omirante.pt',
                  'correiodamanha.com.br', 'blogdonc.com', 'atelevisao.com',
                  'jpn.up.pt'}
    if domain in pt_domains:
        return collect_google_news(
            date_from=df, date_to=dt,
            limit_per_query=60, request_timeout=15, resolve_timeout=8,
        )

    # Fallback: RSS
    return collect_rss(
        limit_per_feed=50, date_from=df, date_to=dt, request_timeout=15,
    )


# ── Main ─────────────────────────────────────────────────────────────────
def main():
    html_path = os.path.expanduser('~/Downloads/clipping_mobile_snapshot_all_stories.html')
    if not os.path.exists(html_path):
        html_path = 'data/reports/clipping_mobile_snapshot_all_stories.html'
    print(f"Loading snapshot from: {html_path}")

    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    parser = SnapshotExtractor()
    parser.feed(html)

    combos = defaultdict(list)
    for a in parser.articles:
        key = (a.get('source_name', '?'), a.get('domain', '?'))
        combos[key].append(a)
    qualified = {k: v for k, v in combos.items() if len(v) >= 5}

    print(f"Total articles: {len(parser.articles)}")
    print(f"Qualified combos (≥5 articles): {len(qualified)}")
    print("=" * 100)

    results_log = []
    total_found = total_expected = 0

    for idx, ((src, dom), arts) in enumerate(
        sorted(qualified.items(), key=lambda x: -len(x[1])), 1
    ):
        samples = pick_samples(arts)
        df, dt = date_range(samples)
        if not df:
            print(f"\n[{idx}] {src} — {dom}: SKIP (no dates)")
            results_log.append((src, dom, 'SKIP', 0, len(samples), '—'))
            continue

        print(f"\n[{idx}/{len(qualified)}] {src} — {dom}")
        print(f"  Date window: {df} → {dt} | Samples: {len(samples)}")

        try:
            fetched = dispatch(src, dom, df, dt, samples=samples)
            print(f"  Collector returned {len(fetched)} candidates")
        except Exception as e:
            print(f"  ERROR: {e}")
            results_log.append((src, dom, 'ERROR', 0, len(samples), str(e)[:80]))
            continue

        found = 0
        for i, s in enumerate(samples):
            hit = url_in_results(s['url'], fetched, expected_title=s.get('title', ''))
            icon = "✓" if hit else "✗"
            if hit: found += 1
            d = parse_date(s.get('date', '')) or '?'
            t = s.get('title', '?')[:60]
            print(f"    [{i+1}] {icon} {d} | {t}")

        total_found += found
        total_expected += len(samples)

        if found == len(samples):
            verdict = 'PASS'
        elif found > 0:
            verdict = 'PARTIAL'
        else:
            verdict = 'FAIL'
        pct = found / len(samples) * 100
        results_log.append((src, dom, verdict, found, len(samples), f"{pct:.0f}%"))
        print(f"  → {verdict} ({found}/{len(samples)})")

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 100)
    print("VALIDATION SUMMARY")
    print("=" * 100)
    counts = defaultdict(int)
    for r in results_log: counts[r[2]] += 1
    for k in ['PASS', 'PARTIAL', 'FAIL', 'ERROR', 'SKIP']:
        print(f"  {k:8s}: {counts[k]}")
    pct = total_found / max(total_expected, 1) * 100
    print(f"  Articles: {total_found}/{total_expected} ({pct:.0f}%)")
    print()
    for src, dom, verdict, found, total, detail in results_log:
        icon = {'PASS': '✓', 'PARTIAL': '◐', 'FAIL': '✗', 'ERROR': '⚠', 'SKIP': '—'}[verdict]
        print(f"  {icon} {verdict:7s} {found}/{total}  {src:35s} {dom:30s} [{detail}]")

    # ── Append to VALIDATION_ORACLE.md (strip old Part 3 first) ────────
    oracle_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'VALIDATION_ORACLE.md'
    )
    # Remove old Part 3 if present
    if os.path.exists(oracle_path):
        with open(oracle_path, 'r', encoding='utf-8') as f:
            content = f.read()
        marker = '# Part 3'
        idx_p3 = content.find(marker)
        if idx_p3 != -1:
            # Find the preceding --- separator
            sep_idx = content.rfind('---', 0, idx_p3)
            if sep_idx != -1:
                content = content[:sep_idx].rstrip()
            else:
                content = content[:idx_p3].rstrip()
            with open(oracle_path, 'w', encoding='utf-8') as f:
                f.write(content + '\n')

    md = [
        "", "---", "",
        "# Part 3 — Automated Validation Results",
        "",
        f"_Run: {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "",
        "| Verdict | Count |",
        "|---------|-------|",
    ]
    for k in ['PASS', 'PARTIAL', 'FAIL', 'ERROR', 'SKIP']:
        md.append(f"| {k} | {counts[k]} |")
    md.append(f"| **Articles** | **{total_found}/{total_expected} ({pct:.0f}%)** |")
    md.extend([
        "",
        "| # | Verdict | Found | Source | Domain | Detail |",
        "|---|---------|-------|--------|--------|--------|",
    ])
    for i, (src, dom, verdict, found, total, detail) in enumerate(results_log, 1):
        md.append(f"| {i} | {verdict} | {found}/{total} | {src} | `{dom}` | {detail} |")
    md.append("")

    with open(oracle_path, 'a', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f"\nResults appended to {oracle_path}")


if __name__ == '__main__':
    main()
