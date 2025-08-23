"""Base agent implementation for AI-Testing platform"""

import time
import json
import logging
import requests
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all testing agents"""
    
    def __init__(
        self,
        orchestrator_url: str,
        token: str,
        agent_type: str,
        heartbeat_interval: int = 30,
        max_retries: int = 3
    ):
        self.orchestrator_url = orchestrator_url.rstrip('/')
        self.token = token
        self.agent_type = agent_type
        self.heartbeat_interval = heartbeat_interval
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
        self.running = False
        self.agent_id = None
    
    def register(self) -> bool:
        """Register agent with orchestrator"""
        try:
            response = self.session.post(
                f'{self.orchestrator_url}/v2/agents/register',
                json={'type': self.agent_type}
            )
            response.raise_for_status()
            data = response.json()
            self.agent_id = data['agent_id']
            logger.info(f"Agent registered: {self.agent_id}")
            return True
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return False
    
    def heartbeat(self) -> bool:
        """Send heartbeat to orchestrator"""
        try:
            response = self.session.post(
                f'{self.orchestrator_url}/v2/agents/{self.agent_id}/heartbeat'
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
            return False
    
    def lease_job(self) -> Optional[Dict[str, Any]]:
        """Lease a job from orchestrator"""
        try:
            response = self.session.post(
                f'{self.orchestrator_url}/v2/agents/lease2',
                json={'agent_type': self.agent_type}
            )
            if response.status_code == 204:
                return None  # No jobs available
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Job lease failed: {e}")
            return None
    
    def complete_job(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Mark job as complete"""
        try:
            response = self.session.post(
                f'{self.orchestrator_url}/v2/jobs/{job_id}/complete',
                json=result
            )
            response.raise_for_status()
            logger.info(f"Job {job_id} completed")
            return True
        except Exception as e:
            logger.error(f"Job completion failed: {e}")
            return False
    
    def upload_artifact(
        self,
        job_id: str,
        filename: str,
        content: bytes,
        content_type: str = 'application/octet-stream'
    ) -> bool:
        """Upload artifact for a job"""
        try:
            files = {'file': (filename, content, content_type)}
            response = self.session.post(
                f'{self.orchestrator_url}/v2/jobs/{job_id}/artifacts',
                files=files
            )
            response.raise_for_status()
            logger.info(f"Artifact {filename} uploaded for job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Artifact upload failed: {e}")
            return False
    
    @abstractmethod
    def process_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process a job - must be implemented by subclasses"""
        pass
    
    def run(self):
        """Main agent loop"""
        if not self.register():
            logger.error("Failed to register agent")
            return
        
        self.running = True
        last_heartbeat = time.time()
        
        while self.running:
            try:
                # Send heartbeat if needed
                if time.time() - last_heartbeat > self.heartbeat_interval:
                    self.heartbeat()
                    last_heartbeat = time.time()
                
                # Lease and process job
                job = self.lease_job()
                if job:
                    logger.info(f"Processing job: {job['id']}")
                    result = self.process_job(job)
                    self.complete_job(job['id'], result)
                else:
                    time.sleep(5)  # Wait before next lease attempt
                    
            except KeyboardInterrupt:
                logger.info("Shutting down agent")
                self.running = False
            except Exception as e:
                logger.error(f"Agent error: {e}")
                time.sleep(10)  # Wait before retry
    
    def stop(self):
        """Stop the agent"""
        self.running = False
