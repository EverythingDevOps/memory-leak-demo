"""
Tests for background worker

⚠️ NOTE: These tests currently DON'T catch the memory leaks!
This is part of the demo - tests need to be improved to detect leaks.
"""

import pytest
import time
from jobs.job_queue import JobQueue
from jobs.background_processor import BackgroundProcessor

@pytest.fixture
def job_queue():
    """Create a job queue for testing"""
    return JobQueue()

@pytest.fixture
def processor(job_queue):
    """Create a background processor for testing"""
    return BackgroundProcessor(job_queue)

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
    
    # Start processor
    processor.start()
    
    # Wait for job to be processed
    time.sleep(2)
    
    # Stop processor
    processor.stop()
    
    # Check job status
    job = job_queue.get_job_status(job_id)
    assert job['status'] == 'completed'
    assert job['result'] is not None

def test_queue_stats(job_queue):
    """Test queue statistics"""
    # Submit some jobs
    job_queue.submit_job('job1', {})
    job_queue.submit_job('job2', {})
    job_queue.submit_job('job3', {})
    
    stats = job_queue.get_stats()
    assert stats['total_jobs'] == 3
    assert stats['pending'] == 3

# 🐛 MISSING TEST: Memory leak detection!
# This test SHOULD exist but doesn't:
#
# def test_no_memory_leak():
#     """Test that processing jobs doesn't cause memory leak"""
#     # This test is missing!
#     # Should process many jobs and verify memory doesn't grow
#     pass

# 🐛 MISSING TEST: Connection pool cleanup!
# def test_database_connections_cleaned_up():
#     """Test that database connections are properly closed"""
#     # This test is missing!
#     pass

# 🐛 MISSING TEST: Event listener cleanup!
# def test_event_listeners_removed():
#     """Test that event listeners are removed after job completion"""
#     # This test is missing!
#     pass
