"""
Job queue management
✅ FIXED: Completed/failed jobs are evicted after exceeding a retention limit
          to prevent the jobs dict growing without bound.
"""

import uuid
from datetime import datetime
from threading import Lock

# Maximum number of completed/failed jobs to retain in memory
_COMPLETED_JOBS_MAX = 500

class JobQueue:
    """
    Simple in-memory job queue.

    ✅ FIX: When the number of finished (completed/failed) jobs exceeds
    _COMPLETED_JOBS_MAX, the oldest finished jobs are evicted from the
    in-memory store so the dict does not grow without bound.
    """

    def __init__(self):
        self.jobs = {}
        self.pending_jobs = []
        self._finished_job_ids = []   # ordered list of finished job IDs for eviction
        self.lock = Lock()
    
    def submit_job(self, job_type, job_data, priority='normal'):
        """Submit a new job to the queue"""
        job_id = str(uuid.uuid4())
        
        job = {
            'id': job_id,
            'type': job_type,
            'data': job_data,
            'priority': priority,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'result': None,
            'error': None
        }
        
        with self.lock:
            self.jobs[job_id] = job
            self.pending_jobs.append(job_id)
        
        return job_id
    
    def get_next_job(self):
        """Get the next pending job"""
        with self.lock:
            if not self.pending_jobs:
                return None
            
            job_id = self.pending_jobs.pop(0)
            job = self.jobs.get(job_id)
            
            if job:
                job['status'] = 'processing'
                job['updated_at'] = datetime.now().isoformat()
            
            return job
    
    def update_job_status(self, job_id, status, result=None, error=None):
        """Update job status, evicting old finished jobs when the retention limit is exceeded."""
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]['status'] = status
                self.jobs[job_id]['updated_at'] = datetime.now().isoformat()

                if result is not None:
                    self.jobs[job_id]['result'] = result

                if error is not None:
                    self.jobs[job_id]['error'] = error

                # ✅ FIX: Track finished jobs and evict oldest when over the limit
                if status in ('completed', 'failed'):
                    self._finished_job_ids.append(job_id)
                    while len(self._finished_job_ids) > _COMPLETED_JOBS_MAX:
                        oldest_id = self._finished_job_ids.pop(0)
                        self.jobs.pop(oldest_id, None)
    
    def get_job_status(self, job_id):
        """Get status of a specific job"""
        with self.lock:
            return self.jobs.get(job_id)
    
    def get_stats(self):
        """Get queue statistics"""
        with self.lock:
            total = len(self.jobs)
            pending = len(self.pending_jobs)
            processing = sum(1 for j in self.jobs.values() if j['status'] == 'processing')
            completed = sum(1 for j in self.jobs.values() if j['status'] == 'completed')
            failed = sum(1 for j in self.jobs.values() if j['status'] == 'failed')
            
            return {
                'total_jobs': total,
                'pending': pending,
                'processing': processing,
                'completed': completed,
                'failed': failed
            }
