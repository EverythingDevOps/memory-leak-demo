"""
Memory monitoring script
Tracks memory usage of the worker process to demonstrate the leak
"""

import psutil
import time
import os
from datetime import datetime

def find_worker_process():
    """Find the worker.py process"""
    current_pid = os.getpid()
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and 'worker.py' in ' '.join(cmdline):
                if proc.info['pid'] != current_pid:
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return None

def format_bytes(bytes_value):
    """Format bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"

def monitor_memory():
    """Monitor memory usage of the worker process"""
    print("=" * 70)
    print("🔍 Memory Leak Monitor")
    print("=" * 70)
    print("\nSearching for worker.py process...")
    
    worker_proc = find_worker_process()
    
    if not worker_proc:
        print("❌ Worker process not found!")
        print("   Make sure 'python worker.py' is running in another terminal")
        return
    
    print(f"✅ Found worker process (PID: {worker_proc.pid})")
    print(f"\n{'Timestamp':<20} {'RSS Memory':<15} {'VMS Memory':<15} {'Change':<15}")
    print("-" * 70)
    
    initial_memory = None
    measurement_count = 0
    
    try:
        while True:
            try:
                # Get memory info
                mem_info = worker_proc.memory_info()
                rss = mem_info.rss  # Resident Set Size (actual physical memory)
                vms = mem_info.vms  # Virtual Memory Size
                
                if initial_memory is None:
                    initial_memory = rss
                    change = 0
                else:
                    change = rss - initial_memory
                
                # Format timestamp
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Format memory values
                rss_str = format_bytes(rss)
                vms_str = format_bytes(vms)
                change_str = f"+{format_bytes(change)}" if change >= 0 else format_bytes(change)
                
                # Print measurement
                print(f"{timestamp:<20} {rss_str:<15} {vms_str:<15} {change_str:<15}")
                
                measurement_count += 1
                
                # Print warning every 10 measurements if memory is growing
                if measurement_count % 10 == 0 and change > 10 * 1024 * 1024:  # 10MB
                    print(f"\n⚠️  WARNING: Memory has grown by {format_bytes(change)} since start!")
                    print(f"   This indicates a memory leak!\n")
                
                # Sleep before next measurement
                time.sleep(5)  # Monitor every 5 seconds
                
            except psutil.NoSuchProcess:
                print("\n❌ Worker process terminated")
                break
                
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped")
        
        if initial_memory:
            final_memory = worker_proc.memory_info().rss
            total_leak = final_memory - initial_memory
            print(f"\n📊 Summary:")
            print(f"   Initial memory: {format_bytes(initial_memory)}")
            print(f"   Final memory:   {format_bytes(final_memory)}")
            print(f"   Total growth:   {format_bytes(total_leak)}")
            print(f"   Measurements:   {measurement_count}")

if __name__ == '__main__':
    monitor_memory()
