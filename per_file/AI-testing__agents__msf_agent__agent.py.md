# File: AI-testing/agents/msf_agent/agent.py

- Size: 20382 bytes
- Kind: text
- SHA256: 774cd4ecb13b5395f2d23f08d27b962b611aea6056faba0ac4a0277d8e04c48d

## Python Imports

```
agent_sdk, datetime, json, logging, os, pathlib, pymetasploit3, requests, sys, tempfile, time, typing
```

## Head (first 60 lines)

```
#!/usr/bin/env python3
"""
Metasploit Framework Agent
Performs automated exploitation and post-exploitation using MSF
"""
import os
import sys
import json
import time
import logging
import tempfile
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests
from pymetasploit3.msfrpc import MsfRpcClient
from pathlib import Path

# Add orchestrator SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../orchestrator'))
from agent_sdk import AgentClient, AgentConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('msf_agent')

class MetasploitAgent:
    """Metasploit Framework exploitation agent"""
    
    def __init__(self):
        self.config = AgentConfig(
            name="msf_agent",
            agent_type="exploitation",
            capabilities=["exploit", "post_exploit", "privilege_escalation"],
            version="1.0.0"
        )
        self.client = AgentClient(self.config)
        self.msf_client = None
        self.temp_dir = tempfile.mkdtemp(prefix="msf_agent_")
        
        # MSF RPC configuration
        self.msf_host = os.environ.get('MSF_HOST', 'localhost')
        self.msf_port = int(os.environ.get('MSF_PORT', 55553))
        self.msf_user = os.environ.get('MSF_USER', 'msf')
        self.msf_pass = os.environ.get('MSF_PASS', 'msf')
        
        # Safety controls
        self.allow_exploitation = os.environ.get('ALLOW_EXPLOITATION', '0') == '1'
        self.safe_mode = os.environ.get('SAFE_MODE', '1') == '1'
        
    def connect_msf(self) -> bool:
        """Connect to Metasploit RPC"""
        try:
            self.msf_client = MsfRpcClient(
                self.msf_pass,
                server=self.msf_host,
                port=self.msf_port,
                username=self.msf_user,
                ssl=False
```

## Tail (last 60 lines)

```
            self.client.post_event("success", f"Exploitation job completed")
            
            return {
                'status': 'completed',
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Job execution failed: {e}")
            self.client.post_event("error", f"Job failed: {str(e)[:500]}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def run(self):
        """Main agent loop"""
        logger.info("Metasploit Agent starting...")
        logger.info(f"Exploitation enabled: {self.allow_exploitation}")
        logger.info(f"Safe mode: {self.safe_mode}")
        
        # Register with orchestrator
        if not self.client.register():
            logger.error("Failed to register with orchestrator")
            return
        
        logger.info("Successfully registered with orchestrator")
        
        try:
            while True:
                # Heartbeat
                if not self.client.heartbeat():
                    logger.warning("Heartbeat failed, re-registering...")
                    if not self.client.register():
                        time.sleep(30)
                        continue
                
                # Try to lease a job
                job = self.client.lease_job()
                if job:
                    logger.info(f"Leased job: {job['id']}")
                    
                    # Execute the job
                    result = self.execute_job(job)
                    
                    # Mark job complete
                    self.client.complete_job(job['id'], result)
                    logger.info(f"Completed job: {job['id']}")
                else:
                    # No jobs available, wait
                    time.sleep(10)
                    
        except KeyboardInterrupt:
            logger.info("Agent shutting down...")
        except Exception as e:
            logger.error(f"Agent error: {e}")

if __name__ == "__main__":
    agent = MetasploitAgent()
    agent.run()
```

