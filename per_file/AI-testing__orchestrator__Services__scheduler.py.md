# File: AI-testing/orchestrator/Services/scheduler.py

- Size: 8795 bytes
- Kind: text
- SHA256: 447d333fab9e8cee7c63b6cb7aba92018afeef098fd720594365eeb6408df784

## Python Imports

```
asyncio, datetime, logging, models, typing
```

## Head (first 60 lines)

```
"""Job scheduling and execution service"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from models import get_db, Run, RunStatus, Job, JobStatus, Finding, Severity

logger = logging.getLogger(__name__)

class Scheduler:
    """Job scheduler for test execution"""
    
    def __init__(self):
        self.running = False
        self.tasks = []
    
    async def start(self):
        """Start scheduler"""
        self.running = True
        logger.info("Scheduler started")
        
        # Start background tasks
        self.tasks.append(asyncio.create_task(self._job_monitor()))
        self.tasks.append(asyncio.create_task(self._timeout_monitor()))
    
    async def stop(self):
        """Stop scheduler"""
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("Scheduler stopped")
    
    async def execute_run(self, run_id: str):
        """Execute a test run"""
        logger.info(f"Executing run: {run_id}")
        
        with get_db() as db:
            run = db.query(Run).filter(Run.id == run_id).first()
            if not run:
                logger.error(f"Run not found: {run_id}")
                return
            
            # Update run status
            run.status = RunStatus.RUNNING
            run.started_at = datetime.utcnow()
            db.commit()
            
            # Process jobs
            jobs = db.query(Job).filter(Job.run_id == run_id).all()
            total_jobs = len(jobs)
            
            for idx, job in enumerate(jobs):
                # Update progress
                progress = int((idx / total_jobs) * 100)
```

## Tail (last 60 lines)

```
        }
        return severity_map.get(severity_str.lower(), Severity.INFO)
    
    async def _job_monitor(self):
        """Monitor jobs for issues"""
        while self.running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                with get_db() as db:
                    # Find stuck jobs
                    stuck_time = datetime.utcnow() - timedelta(minutes=30)
                    stuck_jobs = db.query(Job).filter(
                        Job.status == JobStatus.ASSIGNED,
                        Job.assigned_at < stuck_time
                    ).all()
                    
                    for job in stuck_jobs:
                        logger.warning(f"Job {job.id} appears stuck, resetting")
                        job.status = JobStatus.QUEUED
                        job.agent_id = None
                        job.assigned_at = None
                        job.attempts += 1
                        
                        if job.attempts >= job.max_attempts:
                            job.status = JobStatus.FAILED
                            job.error_message = "Max attempts reached"
                    
                    db.commit()
            
            except Exception as e:
                logger.error(f"Error in job monitor: {e}")
    
    async def _timeout_monitor(self):
        """Monitor for timed out runs"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                with get_db() as db:
                    # Find runs that have been running too long
                    timeout_time = datetime.utcnow() - timedelta(hours=2)
                    timed_out_runs = db.query(Run).filter(
                        Run.status == RunStatus.RUNNING,
                        Run.started_at < timeout_time
                    ).all()
                    
                    for run in timed_out_runs:
                        logger.warning(f"Run {run.id} timed out")
                        run.status = RunStatus.FAILED
                        run.completed_at = datetime.utcnow()
                        run.error_message = "Run exceeded maximum duration"
                    
                    db.commit()
            
            except Exception as e:
                logger.error(f"Error in timeout monitor: {e}")

# Global scheduler instance
scheduler = Scheduler()
```

