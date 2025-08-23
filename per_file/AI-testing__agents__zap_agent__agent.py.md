# File: AI-testing/agents/zap_agent/agent.py

- Size: 15336 bytes
- Kind: text
- SHA256: c92cc5ba4ba019635e15b781ccf1d42fcbe8e5ad593e525f9ba3d43bee0e2f7f

## Python Imports

```
datetime, hashlib, json, logging, os, requests, subprocess, sys, time, typing
```

## Head (first 60 lines)

```
# agents/zap_agent/agent.py
"""ZAP Security Testing Agent"""

import os
import sys
import time
import json
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import subprocess
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ZAPAgent")

class ZAPAgent:
    """OWASP ZAP testing agent"""
    
    def __init__(self):
        self.orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8080")
        self.agent_token = os.getenv("AGENT_TOKEN")
        self.agent_type = "zap"
        self.agent_name = os.getenv("AGENT_NAME", "zap-agent")
        self.allow_active_scan = os.getenv("ALLOW_ACTIVE_SCAN", "0") == "1"
        
        if not self.agent_token:
            logger.error("AGENT_TOKEN environment variable not set")
            sys.exit(1)
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.agent_token}",
            "Content-Type": "application/json"
        })
        
        self.running = True
        self.zap_daemon = None
        
        logger.info(f"ZAP Agent initialized - Orchestrator: {self.orchestrator_url}")
        logger.info(f"Active scanning: {'ENABLED' if self.allow_active_scan else 'DISABLED'}")
    
    def start_zap_daemon(self):
        """Start ZAP daemon process"""
        try:
            logger.info("Starting ZAP daemon...")
            
            # Start ZAP in daemon mode
            cmd = [
                "zap.sh",
                "-daemon",
                "-host", "127.0.0.1",
                "-port", "8090",
                "-config", "api.addrs.addr.name=.*",
                "-config", "api.addrs.addr.regex=true",
```

## Tail (last 60 lines)

```
            )
            
            if response.status_code == 200:
                logger.info(f"Job {job_id} completed successfully")
            else:
                logger.error(f"Failed to complete job: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Complete job error: {e}")
    
    def run(self):
        """Main agent loop"""
        logger.info("Starting ZAP Agent...")
        
        # Start ZAP daemon
        if not self.start_zap_daemon():
            logger.error("Failed to start ZAP daemon")
            return
        
        # Register with orchestrator
        if not self.register():
            logger.error("Failed to register agent")
            return
        
        last_heartbeat = time.time()
        
        try:
            while self.running:
                try:
                    # Send heartbeat
                    if time.time() - last_heartbeat > 30:
                        self.heartbeat()
                        last_heartbeat = time.time()
                    
                    # Lease job
                    job = self.lease_job()
                    
                    if job:
                        # Execute job
                        result = self.execute_job(job)
                        
                        # Report completion
                        self.complete_job(job['id'], result)
                    else:
                        # No job available, wait
                        time.sleep(5)
                    
                except KeyboardInterrupt:
                    logger.info("Shutdown requested")
                    break
                except Exception as e:
                    logger.error(f"Agent loop error: {e}")
                    time.sleep(10)
        
        finally:
            self.stop_zap_daemon()
            logger.info("ZAP Agent stopped")



```

