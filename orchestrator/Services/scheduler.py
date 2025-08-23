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
                run.progress = progress
                db.commit()
                
                # Job will be picked up by agents via lease endpoint
                logger.info(f"Job {job.id} queued for execution")
            
            # Monitor completion in background
            asyncio.create_task(self._monitor_run_completion(run_id))
    
    async def _monitor_run_completion(self, run_id: str):
        """Monitor run for completion"""
        timeout = 3600  # 1 hour timeout
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            await asyncio.sleep(10)  # Check every 10 seconds
            
            with get_db() as db:
                run = db.query(Run).filter(Run.id == run_id).first()
                if not run:
                    return
                
                # Check if all jobs are complete
                jobs = db.query(Job).filter(Job.run_id == run_id).all()
                completed_jobs = [j for j in jobs if j.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]]
                
                if len(completed_jobs) == len(jobs):
                    # All jobs done
                    run.status = RunStatus.COMPLETED
                    run.completed_at = datetime.utcnow()
                    run.progress = 100
                    
                    # Calculate statistics
                    run.statistics = {
                        "total_jobs": len(jobs),
                        "completed": len([j for j in jobs if j.status == JobStatus.COMPLETED]),
                        "failed": len([j for j in jobs if j.status == JobStatus.FAILED]),
                        "cancelled": len([j for j in jobs if j.status == JobStatus.CANCELLED])
                    }
                    
                    db.commit()
                    logger.info(f"Run {run_id} completed")
                    
                    # Process findings from job results
                    await self._process_findings(run_id)
                    return
        
        # Timeout reached
        with get_db() as db:
            run = db.query(Run).filter(Run.id == run_id).first()
            if run and run.status == RunStatus.RUNNING:
                run.status = RunStatus.FAILED
                run.completed_at = datetime.utcnow()
                run.error_message = "Run timed out"
                db.commit()
                logger.error(f"Run {run_id} timed out")
    
    async def _process_findings(self, run_id: str):
        """Process job results into findings"""
        with get_db() as db:
            jobs = db.query(Job).filter(
                Job.run_id == run_id,
                Job.status == JobStatus.COMPLETED
            ).all()
            
            for job in jobs:
                if not job.result:
                    continue
                
                # Extract findings from job result
                # This would be customized based on agent output format
                findings_data = job.result.get("findings", [])
                
                for finding_data in findings_data:
                    finding = Finding(
                        run_id=run_id,
                        job_id=job.id,
                        title=finding_data.get("title", "Unknown Finding"),
                        description=finding_data.get("description"),
                        severity=self._map_severity(finding_data.get("severity", "info")),
                        vulnerability_type=finding_data.get("type"),
                        affected_component=finding_data.get("component"),
                        evidence=finding_data.get("evidence", {}),
                        remediation=finding_data.get("remediation"),
                        cvss_score=finding_data.get("cvss_score"),
                        cvss_vector=finding_data.get("cvss_vector"),
                        references=finding_data.get("references", [])
                    )
                    db.add(finding)
            
            db.commit()
            logger.info(f"Processed findings for run {run_id}")
    
    def _map_severity(self, severity_str: str) -> Severity:
        """Map string to severity enum"""
        severity_map = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
            "info": Severity.INFO,
            "informational": Severity.INFO
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