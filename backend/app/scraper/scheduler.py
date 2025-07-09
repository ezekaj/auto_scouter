"""
Scraper Scheduler Module
Handles scheduling and management of scraping jobs
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)

class ScraperScheduler:
    """Manages scraping job scheduling and execution"""
    
    def __init__(self):
        self.jobs = {}
        self.running = False
        self.last_run = None
        
    def get_job_status(self) -> Dict[str, Any]:
        """Get current status of scheduled jobs"""
        return {
            "running": self.running,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "active_jobs": len(self.jobs),
            "jobs": list(self.jobs.keys())
        }
    
    def trigger_manual_scrape(self) -> str:
        """Trigger a manual scraping job"""
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "id": job_id,
            "type": "manual",
            "status": "queued",
            "created_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None
        }
        
        logger.info(f"Manual scraping job {job_id} queued")
        return job_id
    
    def start_job(self, job_id: str):
        """Mark a job as started"""
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "running"
            self.jobs[job_id]["started_at"] = datetime.utcnow()
            self.running = True
            
    def complete_job(self, job_id: str, success: bool = True):
        """Mark a job as completed"""
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "completed" if success else "failed"
            self.jobs[job_id]["completed_at"] = datetime.utcnow()
            self.last_run = datetime.utcnow()
            self.running = False
            
    def cleanup_old_jobs(self, hours: int = 24):
        """Remove old completed jobs"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        to_remove = []
        
        for job_id, job in self.jobs.items():
            if (job.get("completed_at") and 
                job["completed_at"] < cutoff):
                to_remove.append(job_id)
                
        for job_id in to_remove:
            del self.jobs[job_id]
            
        logger.info(f"Cleaned up {len(to_remove)} old jobs")

# Global scheduler instance
scraper_scheduler = ScraperScheduler()
