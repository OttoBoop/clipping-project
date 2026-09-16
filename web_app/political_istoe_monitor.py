"""Minute production samples and temporary capacity protection for IstoÉ jobs."""
import json
import logging
import os
from pathlib import Path
import time

import requests

SCHEMA = """
CREATE TABLE IF NOT EXISTS political_istoe_samples (
 id BIGSERIAL PRIMARY KEY, job_id TEXT NOT NULL REFERENCES political_jobs(id) ON DELETE CASCADE,
 sampled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), payload JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS political_istoe_samples_job ON political_istoe_samples(job_id,id DESC);
"""


def resource_sample():
    root=Path('/sys/fs/cgroup')
    stats=dict(line.split() for line in (root/'memory.stat').read_text().splitlines())
    limit=int((root/'memory.max').read_text())
    working=max(0,int((root/'memory.current').read_text())-int(stats.get('inactive_file',0)))
    cpu=dict(line.split() for line in (root/'cpu.stat').read_text().splitlines())
    return {'memoryPercent':round(100*working/limit,2),'workingSetBytes':working,
            'memoryLimitBytes':limit,'cpuUsageUsec':int(cpu.get('usage_usec',0))}


def protection(samples):
    recent=samples[-3:]
    if len(recent)==3 and (all(s.get('memoryPercent',0)>70 for s in recent)
                          or all(s.get('webError',False) for s in recent)):
        return 'reduce'
    if len(samples)>=5 and all(s.get('memoryPercent',100)<60 and not s.get('webError',True) for s in samples[-5:]):
        return 'restore'
    return 'hold'


def reporting_loop(service,stop):
    log=logging.getLogger('political_istoe_monitor')
    original=os.environ.get('POLITICAL_FETCH_CONCURRENCY','4')
    original_heavy=os.environ.get('POLITICAL_HEAVY_PAUSED','')
    reduced=False
    while not stop.is_set():
        try:
            with service._connect() as conn:
                jobs=conn.execute("""SELECT id FROM political_jobs WHERE status IN ('queued','running')
                    AND metadata->'source_keys'='["istoe"]'::jsonb""").fetchall()
            if not jobs:
                if reduced:
                    os.environ['POLITICAL_FETCH_CONCURRENCY']=original
                    os.environ['POLITICAL_HEAVY_PAUSED']=original_heavy
                    reduced=False
            for job in jobs:
                sample={}
                try: sample.update(resource_sample())
                except (OSError,ValueError,ZeroDivisionError) as exc: sample['resourceError']=type(exc).__name__
                started=time.monotonic()
                try:
                    response=requests.get('https://clipping-project.onrender.com/healthz',timeout=8)
                    sample.update(webStatus=response.status_code,webError=response.status_code>=500)
                except requests.RequestException as exc: sample.update(webError=True,webErrorType=type(exc).__name__)
                sample['webHealthMs']=round(1000*(time.monotonic()-started),2)
                with service._connect() as conn:
                    previous=conn.execute("""SELECT payload FROM political_istoe_samples WHERE job_id=%s
                        AND sampled_at>NOW()-INTERVAL '6 minutes' ORDER BY id DESC LIMIT 4""",(job['id'],)).fetchall()
                    history=[r['payload'] for r in reversed(previous)]+[sample]
                    action=protection(history)
                    if action=='reduce':
                        os.environ['POLITICAL_FETCH_CONCURRENCY']=str(min(2,int(original)))
                        os.environ['POLITICAL_HEAVY_PAUSED']='1'
                        reduced=True
                    elif action=='restore' and reduced:
                        os.environ['POLITICAL_FETCH_CONCURRENCY']=original
                        os.environ['POLITICAL_HEAVY_PAUSED']=original_heavy
                        reduced=False
                    sample.update(capacityAction=action,fetchConcurrency=int(os.environ.get('POLITICAL_FETCH_CONCURRENCY',original)))
                    conn.execute('INSERT INTO political_istoe_samples(job_id,payload) VALUES(%s,%s::jsonb)',(job['id'],json.dumps(sample)))
                log.info('istoe_sample %s',json.dumps({'job':job['id'],**sample}))
        except Exception as exc:
            log.warning('istoe_monitor_sample_failed error_type=%s',type(exc).__name__)
        stop.wait(60)
