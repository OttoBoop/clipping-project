"""Offline telemetry checks: no HTTP, database or storage requests."""
import json
import logging
import threading

import pytest

from web_app import political_metrics as metrics
from tools.political_worker import worker_loop


def test_operations_count_status_errors_and_never_log_sensitive_payloads(caplog):
    collector = metrics.Collector(allowed_sources={'g1'})
    caplog.set_level(logging.INFO, logger='political_metrics')
    with metrics.task_metrics({'id': 7, 'kind': 'fetch', 'source_key': 'g1',
                               'url': 'https://secret.invalid/?token=never-log-this', 'password': 'private'}, metrics=collector) as task:
        metrics.record_timing('http', .5, status_code=429)
        metrics.record_timing('throttle_wait', 2)
        metrics.record_timing('extraction', .1)
        with pytest.raises(RuntimeError):
            with metrics.timed_operation('object_upload'):
                raise RuntimeError('Bearer never-log-this')
        task.outcome = 'retryable'
    rows = collector.drain(30)
    http = next(row for row in rows if row['operation'] == 'http')
    assert http['httpStatus'] == 429 and http['outcome'] == 'error'
    assert http['count'] == 1 and http['durationMs'] == 500
    assert http['perSecond'] == pytest.approx(1 / 30, abs=.0001)
    assert next(row for row in rows if row['operation'] == 'object_upload')['outcome'] == 'error'
    events = [json.loads(record.message) for record in caplog.records if record.name == 'political_metrics']
    assert len(events) == 1
    assert events[0]['event'] == 'political_task_duration'
    assert events[0]['taskId'] == 7 and events[0]['outcome'] == 'retryable'
    assert events[0]['operations']['http']['count'] == 1
    assert 'never-log-this' not in caplog.text and 'private' not in caplog.text
    assert collector.drain(30) == []


def test_parallel_workers_keep_source_context_separate():
    collector = metrics.Collector(allowed_sources={'g1', 'tupi'})
    barrier = threading.Barrier(2)
    def worker(source):
        with metrics.task_metrics({'id': 1, 'kind': 'fetch', 'source_key': source}, metrics=collector) as task:
            barrier.wait(timeout=3)
            metrics.record_timing('http', .2, status_code=200)
            metrics.record_timing('http', .4, status_code=200)
            task.outcome = 'saved'
    threads = [threading.Thread(target=worker, args=(source,)) for source in ('g1', 'tupi')]
    for thread in threads: thread.start()
    for thread in threads: thread.join(timeout=5)
    assert not any(thread.is_alive() for thread in threads)
    rows = collector.drain(10)
    http = [row for row in rows if row['operation'] == 'http']
    assert {row['source'] for row in http} == {'g1', 'tupi'}
    assert all(row['count'] == 2 and row['durationMs'] == 600 for row in http)
    assert sum(row['count'] for row in rows if row['operation'] == 'task') == 2


def test_cardinality_is_bounded_and_unknown_labels_are_not_exposed():
    collector = metrics.Collector(allowed_sources={'g1'}, max_series=4)
    for code in range(100, 200):
        collector.observe('fetch', 'g1', 'http', 1, 'ok', code)
    collector.observe('https://secret.invalid', 'Bearer secret-value', 'sensitive-operation', 1, 'secret-error', 999)
    rows = collector.drain(30)
    assert len(rows) <= 4
    assert sum(row['count'] for row in rows) == 101
    serialized = json.dumps(rows)
    assert 'secret' not in serialized and 'sensitive-operation' not in serialized


def test_task_exception_restores_thread_context_and_counts_failure():
    collector = metrics.Collector(allowed_sources={'g1'})
    with pytest.raises(ValueError):
        with metrics.task_metrics({'id': 2, 'kind': 'discovery', 'source_key': 'g1'}, metrics=collector):
            raise ValueError('not included in logs')
    metrics.record_timing('http', 1, status_code=200)
    rows = collector.drain(1)
    assert len(rows) == 1 and rows[0]['operation'] == 'task' and rows[0]['outcome'] == 'error'


def test_worker_emits_real_result_duration_and_metrics_report_flushes(monkeypatch, caplog):
    collector = metrics.Collector(allowed_sources={'g1'})
    monkeypatch.setattr(metrics, 'collector', collector)
    caplog.set_level(logging.INFO, logger='political_metrics')
    class Service:
        def heartbeat(self, *a, **k): pass
        def claim_task(self, *a, **k): return {'id': 9, 'kind': 'fetch', 'source_key': 'g1'}
        def process_task(self, task):
            with metrics.timed_operation('http') as request:
                request.status_code = 200
            return {'status': 'saved'}
    worker_loop(Service(), 'fetch', 'test', threading.Event(), once=True)
    metrics.report_interval(30)
    events = [json.loads(record.message) for record in caplog.records if record.name == 'political_metrics']
    assert any(event['event'] == 'political_task_duration' and event['outcome'] == 'saved' for event in events)
    rows = [event for event in events if event['event'] == 'political_worker_metrics']
    assert {row['operation'] for row in rows} == {'task', 'http'}
    assert all(row['source'] == 'g1' and row['count'] == 1 for row in rows)
