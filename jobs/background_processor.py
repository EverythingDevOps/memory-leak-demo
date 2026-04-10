"""
Background job processor
⚠️ THIS FILE CONTAINS INTENTIONAL MEMORY LEAKS
"""

import time
import threading
from database.connection_pool import ConnectionPool
from utils.event_emitter import EventEmitter

class BackgroundProcessor:
    """
    Background job processor with memory leaks
    
    MEMORY LEAKS IN THIS FILE:
    1. Results cache never evicted (unbounded growth)
    2. Circular references between job objects
    3. Event listeners not cleaned up
    4. Database connections not properly closed
    """
    
    def __init__(self, job_queue):
        self.job_queue = job_queue
        self.running = False
        self.worker_thread = None
        
        # 🐛 MEMORY LEAK #1: Unbounded cache - never evicted!
        self.results_cache = {}  # This will grow forever
        
        # 🐛 MEMORY LEAK #2: Keeping references to all processed jobs
        self.processed_jobs = []  # Never cleared!
        
        # Database connection pool (has its own leaks)
        self.db_pool = ConnectionPool()
        
        # Event emitter (has leak in event listeners)
        self.event_emitter = EventEmitter()
        
        # Job counter
        self.jobs_processed = 0
        
    def start(self):
        """Start processing jobs"""
        if self.running:
            print("⚠️  Worker already running")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.worker_thread.start()
        print("✅ Worker started")
    
    def stop(self):
        """Stop processing jobs"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        print("✅ Worker stopped")
    
    def _process_loop(self):
        """Main processing loop"""
        while self.running:
            job = self.job_queue.get_next_job()
            
            if job:
                self._process_job(job)
            else:
                # No jobs available, sleep briefly
                time.sleep(0.1)
    
    def _process_job(self, job):
        """
        Process a single job
        ⚠️ THIS METHOD CONTAINS MULTIPLE MEMORY LEAKS
        """
        job_id = job['id']
        job_type = job['type']
        
        try:
            print(f"🔄 Processing job {job_id} (type: {job_type})")
            
            # 🐛 MEMORY LEAK #3: Register event listener but NEVER remove it!
            # Each job adds a new listener, they accumulate forever
            self.event_emitter.on('job_complete', lambda j: self._on_job_complete(j))
            
            # 🐛 MEMORY LEAK #4: Get database connection but DON'T close it!
            # Connection pool will keep growing
            db_conn = self.db_pool.get_connection()  # Never closed!
            
            # Simulate some work
            result = self._do_actual_work(job, db_conn)
            
            # 🐛 MEMORY LEAK #5: Store result in unbounded cache
            self.results_cache[job_id] = {
                'job': job,  # Holds entire job object
                'result': result,
                'timestamp': time.time(),
                'db_connection': db_conn  # Keeps connection alive!
            }
            
            # 🐛 MEMORY LEAK #6: Add job to processed list (never cleared)
            self.processed_jobs.append(job)
            
            # 🐛 MEMORY LEAK #7: Create circular reference
            job['processor'] = self  # Job holds reference to processor
            job['previous_job'] = self.processed_jobs[-2] if len(self.processed_jobs) > 1 else None
            
            # Update job status
            self.job_queue.update_job_status(job_id, 'completed', result=result)
            
            # Emit event (listeners will accumulate)
            self.event_emitter.emit('job_complete', job)
            
            self.jobs_processed += 1
            print(f"✅ Completed job {job_id} (Total processed: {self.jobs_processed})")
            print(f"   📊 Cache size: {len(self.results_cache)} | "
                  f"Processed list: {len(self.processed_jobs)} | "
                  f"Listeners: {self.event_emitter.listener_count('job_complete')}")
            
        except Exception as e:
            print(f"❌ Error processing job {job_id}: {e}")
            self.job_queue.update_job_status(job_id, 'failed', error=str(e))
    
    def _do_actual_work(self, job, db_conn):
        """Simulate actual work being done"""
        job_type = job['type']
        
        if job_type == 'process_data':
            # Simulate data processing
            time.sleep(0.5)
            
            # Create some data to process (adds to memory)
            data = job.get('data', {})
            
            # Simulate database query (connection already leaked)
            # In real code, we'd use db_conn here
            
            return {
                'status': 'success',
                'processed': True,
                'data_size': len(str(data))
            }
        
        elif job_type == 'generate_report':
            # Simulate report generation
            time.sleep(1.0)
            
            # Generate large report data (stays in cache)
            report = ['Line {}'.format(i) for i in range(10000)]
            
            return {
                'status': 'success',
                'report_lines': len(report),
                'report': report  # Large data kept in memory!
            }
        
        else:
            return {'status': 'success', 'message': 'Job processed'}
    
    def _on_job_complete(self, job):
        """
        Callback for job completion
        ⚠️ This callback is registered for EVERY job but never cleaned up!
        Each instance holds references to job data
        """
        # This callback accumulates in memory
        pass
