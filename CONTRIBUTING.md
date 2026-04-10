# Contributing Guide

## This is a Demo Project

⚠️ **IMPORTANT**: This project intentionally contains memory leaks for demonstration purposes.

## The Challenge

Your task is to fix the memory leaks described in Jira ticket KAN-2:
https://everythingdevops-37268243.atlassian.net/browse/KAN-2

## Known Memory Leaks to Fix

### 1. Database Connection Pool (`database/connection_pool.py`)
- **Problem**: Connections created but never closed
- **Line**: `get_connection()` always creates new connections
- **Fix**: Implement proper connection reuse and cleanup

### 2. Event Listeners (`utils/event_emitter.py`)
- **Problem**: Listeners registered but never removed
- **Line**: `on()` method in EventEmitter
- **Fix**: Remove listeners after job completion

### 3. Results Cache (`jobs/background_processor.py`)
- **Problem**: Unbounded cache growth
- **Line**: `self.results_cache` dictionary
- **Fix**: Implement cache eviction policy (LRU, size limit, TTL)

### 4. Processed Jobs List (`jobs/background_processor.py`)
- **Problem**: All processed jobs kept in memory
- **Line**: `self.processed_jobs` list
- **Fix**: Clear or limit the list size

### 5. Circular References (`jobs/background_processor.py`)
- **Problem**: Jobs reference processor, preventing GC
- **Line**: `job['processor'] = self`
- **Fix**: Remove circular references or use weak references

## How to Verify Your Fix

1. **Run the memory monitor**:
   ```bash
   python monitor_memory.py
   ```

2. **Submit test jobs**:
   ```bash
   curl -X POST http://localhost:5000/jobs \
     -H "Content-Type: application/json" \
     -d '{"type": "process_data", "data": "test"}'
   ```

3. **Observe memory usage**:
   - Before fix: Memory grows continuously
   - After fix: Memory should remain stable

4. **Run tests**:
   ```bash
   pytest tests/
   ```

## Expected Outcome

After fixing all leaks:
- Memory usage should stabilize
- Connection pool should reuse connections
- Event listeners should be cleaned up
- Cache should have bounded size
- Tests should pass

## Demo Workflow

1. Run the buggy version and observe leaks
2. Use Rovo Dev to analyze the code
3. Implement fixes for each leak
4. Update KAN-2 ticket with findings
5. Verify fixes with memory monitor
6. Add tests to prevent regression

Good luck! 🚀
