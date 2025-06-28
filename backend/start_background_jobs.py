#!/usr/bin/env python3
"""
Start Background Jobs System

This script starts the complete background job system including:
- Celery workers for different queues
- Celery beat scheduler for periodic tasks
- Health monitoring
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def print_step(step, description):
    """Print a formatted step"""
    print(f"\n📋 Step {step}: {description}")
    print("-" * 40)

def check_redis():
    """Check if Redis is available"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("💡 Please install and start Redis server")
        return False

def start_celery_worker(queue_name, concurrency=2):
    """Start a Celery worker for a specific queue"""
    print(f"🔧 Starting Celery worker for queue: {queue_name}")
    
    cmd = [
        sys.executable, "-m", "celery", 
        "-A", "app.core.celery_app", 
        "worker",
        "--loglevel=info",
        f"--concurrency={concurrency}",
        f"--queues={queue_name}",
        f"--hostname=worker-{queue_name}@%h"
    ]
    
    try:
        process = subprocess.Popen(cmd, cwd=Path(__file__).parent)
        print(f"✅ Worker for {queue_name} started (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ Failed to start worker for {queue_name}: {e}")
        return None

def start_celery_beat():
    """Start Celery beat scheduler"""
    print("⏰ Starting Celery beat scheduler...")
    
    cmd = [
        sys.executable, "-m", "celery",
        "-A", "app.core.celery_app",
        "beat",
        "--loglevel=info"
    ]
    
    try:
        process = subprocess.Popen(cmd, cwd=Path(__file__).parent)
        print(f"✅ Celery beat started (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ Failed to start Celery beat: {e}")
        return None

def test_scraping_task():
    """Test the scraping task"""
    print("🧪 Testing scraping task...")
    
    try:
        from app.tasks.scraping_tasks import scrape_single_source
        
        # Test with a small number of vehicles
        result = scrape_single_source.delay('gruppoautouno', max_vehicles=5)
        print(f"✅ Scraping task queued: {result.id}")
        
        # Wait a bit and check status
        time.sleep(2)
        if result.ready():
            print(f"📊 Task result: {result.result}")
        else:
            print("⏳ Task is running in background...")
            
        return True
        
    except Exception as e:
        print(f"❌ Scraping task test failed: {e}")
        return False

def main():
    """Main function"""
    print_header("Auto Scouter Background Jobs System")
    
    # Check if we're in the right directory
    if not Path("app").exists():
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    print_step(1, "Checking Dependencies")
    
    # Check Redis
    if not check_redis():
        print("\n💡 To install Redis on Windows:")
        print("   1. Download Redis from: https://github.com/microsoftarchive/redis/releases")
        print("   2. Or use Docker: docker run -d -p 6379:6379 redis:alpine")
        print("   3. Or use WSL: sudo apt install redis-server")
        sys.exit(1)
    
    print_step(2, "Starting Background Workers")
    
    workers = []
    queues = [
        ("scraping", 1),      # 1 worker for scraping (CPU intensive)
        ("alert_matching", 2), # 2 workers for alert matching
        ("notifications", 2),  # 2 workers for notifications
        ("maintenance", 1),    # 1 worker for maintenance tasks
        ("default", 1)         # 1 worker for default queue
    ]
    
    for queue_name, concurrency in queues:
        worker = start_celery_worker(queue_name, concurrency)
        if worker:
            workers.append(worker)
    
    print_step(3, "Starting Scheduler")
    
    # Start beat scheduler
    beat_process = start_celery_beat()
    if beat_process:
        workers.append(beat_process)
    
    print_step(4, "Testing System")
    
    # Wait a moment for workers to start
    time.sleep(3)
    
    # Test scraping task
    test_scraping_task()
    
    print_step(5, "System Status")
    
    print(f"✅ Started {len(workers)} background processes")
    print("📊 Scheduled tasks:")
    print("   - Vehicle scraping: Every 5 minutes")
    print("   - Alert matching: Every 5 minutes") 
    print("   - Notification processing: Every minute")
    print("   - Data cleanup: Every hour")
    print("   - Listing cleanup: Daily")
    print("   - Daily digest: Daily at 8 AM")
    
    print("\n🎉 Background job system is running!")
    print("💡 Press Ctrl+C to stop all processes")
    
    try:
        # Keep the script running
        while True:
            time.sleep(10)
            
            # Check if processes are still running
            running_count = sum(1 for p in workers if p.poll() is None)
            if running_count == 0:
                print("❌ All workers have stopped")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping background jobs...")
        
        # Terminate all processes
        for process in workers:
            if process.poll() is None:
                process.terminate()
                
        # Wait for processes to stop
        for process in workers:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                
        print("✅ All background jobs stopped")

if __name__ == "__main__":
    main()
