# Background Job Processor - Memory Leak Demo

> **⚠️ WARNING**: This project intentionally contains memory leaks for demonstration purposes.

## Overview

A Python-based background job processor that processes data tasks. This project demonstrates common memory leak patterns that can occur in production systems.

## The Problem (KAN-2)

This application has a critical memory leak that causes:
- Memory usage increasing by ~50MB per hour
- Application crashes after 24-48 hours
- Performance degradation before crash
- OOM (Out of Memory) errors in production

## Architecture

```
┌─────────────────┐
│   Flask API     │  ← Submit jobs
└────────┬────────┘
         │
    ┌────▼─────┐
    │ Job Queue│
    └────┬─────┘
         │
    ┌────▼────────────┐
    │ Background      │  ← Memory leak here!
    │ Job Processor   │
    └─────────────────┘
         │
    ┌────▼─────┐
    │ Database │
    └──────────┘
```

## Known Issues (Memory Leaks)

1. **Database connections not properly closed** 🐛
2. **Event listeners accumulating without cleanup** 🐛
3. **Large objects held in memory cache** 🐛
4. **Circular references preventing garbage collection** 🐛

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

### Start the API Server
```bash
python app.py
```

### Start the Background Worker
```bash
python worker.py
```

### Monitor Memory Usage
```bash
python monitor_memory.py
```

## Reproducing the Memory Leak

1. Start the application and worker
2. Submit jobs via the API:
   ```bash
   curl -X POST http://localhost:5000/jobs \
     -H "Content-Type: application/json" \
     -d '{"type": "process_data", "data": "sample data"}'
   ```
3. Watch memory usage grow over time
4. Memory profiler will show the leaks

## Project Structure

```
memory-leak-demo/
├── app.py                  # Flask API for job submission
├── worker.py               # Background job processor (HAS LEAKS!)
├── jobs/
│   ├── background_processor.py  # Job handler (LEAK SOURCE)
│   └── job_queue.py        # Job queue management
├── database/
│   ├── connection_pool.py  # DB connection pool (LEAK SOURCE)
│   └── models.py           # Database models
├── utils/
│   └── event_emitter.py    # Event system (LEAK SOURCE)
├── monitor_memory.py       # Memory monitoring script
├── tests/
│   └── test_worker.py      # Tests (currently don't catch leaks)
└── requirements.txt        # Dependencies
```

## Memory Leak Details

### Leak 1: Unclosed Database Connections
**File**: `database/connection_pool.py`
- Connections created but never properly closed
- Pool grows indefinitely
- Each connection holds ~5-10MB

### Leak 2: Event Listener Accumulation
**File**: `utils/event_emitter.py`
- Event listeners registered but never removed
- Each job adds new listeners
- Callbacks hold references to job data

### Leak 3: In-Memory Cache
**File**: `jobs/background_processor.py`
- Results cached without size limits
- Old entries never evicted
- Cache grows unbounded

### Leak 4: Circular References
**File**: `jobs/background_processor.py`
- Job objects reference each other
- Prevents garbage collection
- Objects accumulate in memory

## Jira Ticket

This project demonstrates the bug described in:
**https://everythingdevops-37268243.atlassian.net/browse/KAN-2**

## Next Steps

Use Rovo Dev to:
1. Analyze the codebase
2. Identify memory leak sources
3. Implement fixes
4. Add tests to prevent regression
5. Update Jira ticket with solution

## License

MIT License - For demonstration purposes only
