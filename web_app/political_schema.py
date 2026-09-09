"""Isolated PostgreSQL schema for requested political clipping work."""

SCHEMA_VERSION = "political_corpus_v1"
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS political_jobs (
 id TEXT PRIMARY KEY, kind TEXT NOT NULL DEFAULT 'collect', status TEXT NOT NULL DEFAULT 'queued',
 target_keys TEXT[] NOT NULL, target_snapshots JSONB NOT NULL, date_from DATE NOT NULL, date_to DATE NOT NULL,
 requested_by TEXT NOT NULL, request_key TEXT UNIQUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 articles_inserted BIGINT NOT NULL DEFAULT 0, mentions_inserted BIGINT NOT NULL DEFAULT 0, fetch_attempted BIGINT NOT NULL DEFAULT 0,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), finished_at TIMESTAMPTZ, metadata JSONB NOT NULL DEFAULT '{}'
);
ALTER TABLE political_jobs ADD COLUMN IF NOT EXISTS articles_inserted BIGINT NOT NULL DEFAULT 0;
ALTER TABLE political_jobs ADD COLUMN IF NOT EXISTS mentions_inserted BIGINT NOT NULL DEFAULT 0;
ALTER TABLE political_jobs ADD COLUMN IF NOT EXISTS fetch_attempted BIGINT NOT NULL DEFAULT 0;
CREATE TABLE IF NOT EXISTS political_tasks (
 id BIGSERIAL PRIMARY KEY, job_id TEXT NOT NULL REFERENCES political_jobs(id) ON DELETE CASCADE,
 kind TEXT NOT NULL, source_key TEXT NOT NULL, dedupe_key TEXT NOT NULL, payload JSONB NOT NULL,
 cursor JSONB NOT NULL DEFAULT '{}', status TEXT NOT NULL DEFAULT 'queued', attempts INTEGER NOT NULL DEFAULT 0,
 max_attempts INTEGER NOT NULL DEFAULT 6, priority INTEGER NOT NULL DEFAULT 10,
 lease_owner TEXT, lease_token TEXT, leased_until TIMESTAMPTZ, next_attempt_at TIMESTAMPTZ,
 raw_count BIGINT NOT NULL DEFAULT 0, result JSONB NOT NULL DEFAULT '{}', error_type TEXT NOT NULL DEFAULT '',
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 UNIQUE(job_id,kind,dedupe_key)
);
CREATE INDEX IF NOT EXISTS political_tasks_claim ON political_tasks(kind,status,priority DESC,next_attempt_at,id);
CREATE INDEX IF NOT EXISTS political_tasks_job ON political_tasks(job_id,status);
CREATE TABLE IF NOT EXISTS political_source_leases (
 source_key TEXT PRIMARY KEY, task_id BIGINT, lease_token TEXT, leased_until TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS political_domain_limits (
 domain TEXT PRIMARY KEY, next_request_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS political_workers (
 id TEXT PRIMARY KEY, kind TEXT NOT NULL, heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 task_id BIGINT, error_type TEXT NOT NULL DEFAULT '', started_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS political_articles (
 id BIGSERIAL PRIMARY KEY, canonical_url TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
 source_key TEXT NOT NULL, source_name TEXT NOT NULL, published_at TIMESTAMPTZ,
 date_status TEXT NOT NULL DEFAULT 'unknown', discovered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 snippet TEXT NOT NULL DEFAULT '', summary TEXT NOT NULL DEFAULT '', body_status TEXT NOT NULL DEFAULT 'metadata_only',
 content_hash TEXT NOT NULL DEFAULT '', text_object_key TEXT NOT NULL DEFAULT '', body_chars INTEGER NOT NULL DEFAULT 0,
 html_hash TEXT NOT NULL DEFAULT '', html_object_key TEXT NOT NULL DEFAULT '',
 legacy_id BIGINT, metadata JSONB NOT NULL DEFAULT '{}', updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE political_articles ADD COLUMN IF NOT EXISTS html_hash TEXT NOT NULL DEFAULT '';
ALTER TABLE political_articles ADD COLUMN IF NOT EXISTS html_object_key TEXT NOT NULL DEFAULT '';
CREATE TABLE IF NOT EXISTS political_article_revisions (
 id BIGSERIAL PRIMARY KEY, article_id BIGINT NOT NULL REFERENCES political_articles(id) ON DELETE CASCADE,
 previous JSONB NOT NULL, reason TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS political_article_revisions_article ON political_article_revisions(article_id,id DESC);
CREATE INDEX IF NOT EXISTS political_articles_date ON political_articles(COALESCE(published_at,discovered_at) DESC,id DESC);
CREATE INDEX IF NOT EXISTS political_articles_source ON political_articles(source_key,id DESC);
CREATE TABLE IF NOT EXISTS political_url_aliases (
 url TEXT PRIMARY KEY, article_id BIGINT NOT NULL REFERENCES political_articles(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS political_mentions (
 article_id BIGINT NOT NULL REFERENCES political_articles(id) ON DELETE CASCADE,
 target_key TEXT NOT NULL, target_name TEXT NOT NULL, keyword_matched TEXT NOT NULL,
 legacy_id BIGINT, rule_version TEXT NOT NULL DEFAULT 'political_names_v1',
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY(article_id,target_key)
);
CREATE INDEX IF NOT EXISTS political_mentions_scope ON political_mentions(target_key,article_id DESC);
CREATE TABLE IF NOT EXISTS political_stories (
 id BIGSERIAL PRIMARY KEY, story_key TEXT NOT NULL UNIQUE, title TEXT NOT NULL, summary TEXT NOT NULL DEFAULT '',
 legacy_id BIGINT, metadata JSONB NOT NULL DEFAULT '{}', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS political_story_articles (
 article_id BIGINT NOT NULL REFERENCES political_articles(id) ON DELETE CASCADE,
 story_id BIGINT NOT NULL REFERENCES political_stories(id) ON DELETE CASCADE,
 PRIMARY KEY(article_id,story_id)
);
CREATE INDEX IF NOT EXISTS political_story_articles_story ON political_story_articles(story_id,article_id);
CREATE TABLE IF NOT EXISTS political_classifications (
 article_id BIGINT NOT NULL, target_key TEXT NOT NULL, payload JSONB NOT NULL,
 updated_by TEXT NOT NULL, updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), legacy_id BIGINT,
 PRIMARY KEY(article_id,target_key),
 FOREIGN KEY(article_id,target_key) REFERENCES political_mentions(article_id,target_key) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS political_classification_revisions (
 id BIGSERIAL PRIMARY KEY, article_id BIGINT NOT NULL, target_key TEXT NOT NULL,
 previous JSONB NOT NULL, updated_by TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 FOREIGN KEY(article_id,target_key) REFERENCES political_mentions(article_id,target_key) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS political_observations (
 id BIGSERIAL PRIMARY KEY, job_id TEXT NOT NULL REFERENCES political_jobs(id) ON DELETE CASCADE,
 source_task_id BIGINT NOT NULL REFERENCES political_tasks(id), observed_url TEXT NOT NULL,
 source_key TEXT NOT NULL, title TEXT NOT NULL DEFAULT '', snippet TEXT NOT NULL DEFAULT '',
 metadata JSONB NOT NULL DEFAULT '{}', article_id BIGINT REFERENCES political_articles(id),
 disposition TEXT NOT NULL DEFAULT 'pending', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 UNIQUE(job_id,observed_url)
);
CREATE INDEX IF NOT EXISTS political_observations_job ON political_observations(job_id,disposition);
CREATE TABLE IF NOT EXISTS political_import_progress (
 source_key TEXT PRIMARY KEY, last_article_id BIGINT NOT NULL DEFAULT 0, completed BOOLEAN NOT NULL DEFAULT FALSE,
 validation JSONB NOT NULL DEFAULT '{}', updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE political_import_progress ADD COLUMN IF NOT EXISTS validation JSONB NOT NULL DEFAULT '{}';
CREATE TABLE IF NOT EXISTS political_legacy_ids (
 source_key TEXT NOT NULL, entity_type TEXT NOT NULL, legacy_id BIGINT NOT NULL, new_id BIGINT NOT NULL,
 PRIMARY KEY(source_key,entity_type,legacy_id)
);
CREATE TABLE IF NOT EXISTS political_legacy_records (
 source_key TEXT NOT NULL, entity_type TEXT NOT NULL, legacy_id BIGINT NOT NULL,
 payload JSONB NOT NULL, PRIMARY KEY(source_key,entity_type,legacy_id)
);
CREATE TABLE IF NOT EXISTS political_legacy_story_articles (
 source_key TEXT NOT NULL, legacy_story_id BIGINT NOT NULL, legacy_article_id BIGINT NOT NULL,
 story_id BIGINT NOT NULL REFERENCES political_stories(id) ON DELETE CASCADE,
 article_id BIGINT NOT NULL REFERENCES political_articles(id) ON DELETE CASCADE,
 payload JSONB NOT NULL,
 PRIMARY KEY(source_key,legacy_story_id,legacy_article_id)
);
"""

SCHEMA_UPGRADES = ("""DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='political_story_articles'::regclass
            AND contype='p' AND array_length(conkey,1)=1) THEN
  ALTER TABLE political_story_articles DROP CONSTRAINT political_story_articles_pkey;
  ALTER TABLE political_story_articles ADD PRIMARY KEY(article_id,story_id);
 END IF;
END $$;""",)
