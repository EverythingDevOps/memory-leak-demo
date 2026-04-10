"""
Flask API for submitting background jobs
"""

from flask import Flask, request, jsonify
from jobs.job_queue import JobQueue
import threading
import time

app = Flask(__name__)
job_queue = JobQueue()

@app.route('/')
def home():
    return jsonify({
        "service": "Background Job Processor",
        "status": "running",
        "warning": "⚠️ This application has memory leaks!",
        "endpoints": {
            "POST /jobs": "Submit a new job",
            "GET /jobs/<job_id>": "Get job status",
            "GET /stats": "Get queue statistics"
        }
    })

@app.route('/jobs', methods=['POST'])
def submit_job():
    """Submit a new background job"""
    data = request.get_json()
    
    if not data or 'type' not in data:
        return jsonify({'error': 'Job type is required'}), 400
    
    job_id = job_queue.submit_job(
        job_type=data['type'],
        job_data=data.get('data', {}),
        priority=data.get('priority', 'normal')
    )
    
    return jsonify({
        'job_id': job_id,
        'status': 'queued',
        'message': f'Job {job_id} submitted successfully'
    }), 201

@app.route('/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get status of a specific job"""
    status = job_queue.get_job_status(job_id)
    
    if not status:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(status)

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get queue statistics"""
    return jsonify(job_queue.get_stats())

if __name__ == '__main__':
    print("=" * 50)
    print("⚠️  WARNING: This application has memory leaks!")
    print("=" * 50)
    print("\nStarting Flask API on http://localhost:5000")
    print("Run 'python worker.py' in another terminal to process jobs")
    print("Run 'python monitor_memory.py' to monitor memory usage\n")
    
    app.run(debug=True, port=5000, use_reloader=False)
