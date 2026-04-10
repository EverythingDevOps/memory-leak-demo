"""
Tests for background worker — including regression tests for memory leaks.
"""

import gc
import time
import pytest
from jobs.job_queue import JobQueue, _COMPLETED_JOBS_MAX
from jobs.background_processor import BackgroundProcessor, _CACHE_MAX_SIZE


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def job_queue():
    """Create a job queue for testing"""
    return JobQueue()


@pytest.fixture
def processor(job_queue):
    """Create and yield a BackgroundProcessor; ensure it is stopped after the test."""
    proc = BackgroundProcessor(job_queue)
    yield proc
    # Guarantee cleanup even if the test fails mid-way
    if proc.running:
        proc.stop()


# ---------------------------------------------------------------------------
# Original functional tests (unchanged behaviour)
# ---------------------------------------------------------------------------

def test_job_queue_submit(job_queue):
    """Test submitting a job to the queue"""
    job_id = job_queue.submit_job(
        job_type='process_data',
        job_data={'test': 'data'}
    )

    assert job_id is not None

    job = job_queue.get_job_status(job_id)
    assert job is not None
    assert job['status'] == 'pending'
    assert job['type'] == 'process_data'


def test_job_queue_get_next(job_queue):
    """Test getting next job from queue"""
    job_id = job_queue.submit_job('test_job', {})

    next_job = job_queue.get_next_job()
    assert next_job is not None
    assert next_job['id'] == job_id
    assert next_job['status'] == 'processing'


def test_processor_processes_job(job_queue, processor):
    """Test that processor can process a job"""
    job_id = job_queue.submit_job('process_data', {'test': 'data'})

    processor.start()
    time.sleep(2)
    processor.stop()

    job = job_queue.get_job_status(job_id)
    assert job['status'] == 'completed'
    assert job['result'] is not None


def test_queue_stats(job_queue):
    """Test queue statistics"""
    job_queue.submit_job('job1', {})
    job_queue.submit_job('job2', {})
    job_queue.submit_job('job3', {})

    stats = job_queue.get_stats()
    assert stats['total_jobs'] == 3
    assert stats['pending'] == 3


# ---------------------------------------------------------------------------
# Regression tests — memory leak prevention
# ---------------------------------------------------------------------------

def test_results_cache_bounded(job_queue, processor):
    """
    Regression: results cache must not grow beyond _CACHE_MAX_SIZE.

    Processes (_CACHE_MAX_SIZE + 20) jobs and verifies the cache size never
    exceeds the configured limit.
    """
    processor.start()

    total = _CACHE_MAX_SIZE + 20
    for _ in range(total):
        job_queue.submit_job('process_data', {'x': 'y'})

    # Allow time for all jobs to be processed
    deadline = time.time() + 60
    while job_queue.get_stats()['pending'] > 0 and time.time() < deadline:
        time.sleep(0.2)

    processor.stop()

    assert len(processor.results_cache) <= _CACHE_MAX_SIZE, (
        f"Cache grew to {len(processor.results_cache)}, expected <= {_CACHE_MAX_SIZE}"
    )


def test_event_listeners_not_accumulated(job_queue, processor):
    """
    Regression: event listeners must not accumulate across jobs.

    After processing N jobs the listener count for 'job_complete' must still
    be 0 (one-shot listeners are removed after firing).
    """
    processor.start()

    for _ in range(10):
        job_queue.submit_job('process_data', {})

    deadline = time.time() + 30
    while job_queue.get_stats()['pending'] > 0 and time.time() < deadline:
        time.sleep(0.2)

    processor.stop()

    listener_count = processor.event_emitter.listener_count('job_complete')
    assert listener_count == 0, (
        f"Expected 0 listeners after processing, found {listener_count}"
    )


def test_database_connections_released(job_queue, processor):
    """
    Regression: database connections must be returned to the pool after each job.

    After all jobs finish, the number of active (in-use) connections must be 0.
    """
    processor.start()

    for _ in range(5):
        job_queue.submit_job('process_data', {})

    deadline = time.time() + 30
    while job_queue.get_stats()['pending'] > 0 and time.time() < deadline:
        time.sleep(0.2)

    processor.stop()

    stats = processor.db_pool.get_stats()
    assert stats['active_connections'] == 0, (
        f"Expected 0 active connections after stop, found {stats['active_connections']}"
    )


def test_database_connections_closed_on_stop(job_queue, processor):
    """
    Regression: stop() must close all database connections and free buffers.
    """
    processor.start()
    job_queue.submit_job('process_data', {})

    deadline = time.time() + 10
    while job_queue.get_stats()['pending'] > 0 and time.time() < deadline:
        time.sleep(0.1)

    processor.stop()

    for conn in processor.db_pool.connections:
        assert conn.is_closed, f"Connection {conn.id} was not closed after stop()"
        assert conn.buffer is None, f"Connection {conn.id} buffer was not freed after stop()"


def test_no_circular_references(job_queue, processor):
    """
    Regression: jobs must not hold references to the processor or to each other,
    so that the garbage collector can reclaim them immediately after processing.
    """
    processor.start()

    job_id = job_queue.submit_job('process_data', {'value': 'test'})

    deadline = time.time() + 10
    while True:
        status = job_queue.get_job_status(job_id)
        if status and status['status'] == 'completed':
            break
        if time.time() > deadline:
            pytest.fail("Job did not complete in time")
        time.sleep(0.1)

    processor.stop()

    # The job dict stored in the queue must not reference the processor
    completed_job = job_queue.get_job_status(job_id)
    if completed_job is not None:
        assert 'processor' not in completed_job, (
            "Job dict must not hold a reference to the processor (circular ref)"
        )
        assert 'previous_job' not in completed_job, (
            "Job dict must not hold a reference to another job (circular ref)"
        )


def test_job_queue_evicts_old_completed_jobs(job_queue):
    """
    Regression: the job queue must evict old completed/failed jobs to prevent
    the jobs dict from growing without bound.
    """
    overflow = 20
    total = _COMPLETED_JOBS_MAX + overflow

    for i in range(total):
        job_id = job_queue.submit_job('test_job', {})
        job_queue.get_next_job()  # move to 'processing'
        job_queue.update_job_status(job_id, 'completed')

    assert len(job_queue.jobs) <= _COMPLETED_JOBS_MAX, (
        f"JobQueue grew to {len(job_queue.jobs)} entries, expected <= {_COMPLETED_JOBS_MAX}"
    )


def test_stop_clears_results_cache(job_queue, processor):
    """
    Regression: stop() must clear the results cache so cached objects are freed.
    """
    processor.start()
    job_queue.submit_job('process_data', {})

    deadline = time.time() + 10
    while job_queue.get_stats()['pending'] > 0 and time.time() < deadline:
        time.sleep(0.1)

    processor.stop()

    assert len(processor.results_cache) == 0, (
        "Results cache should be empty after stop()"
    )
