"""
Background worker that processes jobs from the queue
⚠️ THIS FILE CONTAINS INTENTIONAL MEMORY LEAKS
"""

import time
import signal
import sys
from jobs.job_queue import JobQueue
from jobs.background_processor import BackgroundProcessor

# Global worker instance
worker = None

def signal_handler(sig, frame):
    """Handle graceful shutdown"""
    print('\n\n🛑 Shutting down worker...')
    if worker:
        worker.stop()
    sys.exit(0)

def main():
    global worker
    
    print("=" * 60)
    print("⚠️  WARNING: This worker has intentional memory leaks!")
    print("=" * 60)
    print("\n🚀 Starting background job worker...")
    print("📊 Monitor memory with: python monitor_memory.py")
    print("🛑 Press Ctrl+C to stop\n")
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create worker instance
    job_queue = JobQueue()
    worker = BackgroundProcessor(job_queue)
    
    # Start processing jobs
    worker.start()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == '__main__':
    main()
