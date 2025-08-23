# File: AI-testing/agents/aws_agent/agent.py

- Size: 21922 bytes
- Kind: text
- SHA256: 1f926fc7ed3a24350ca7d6e60c9778c8352f3d05c354c86c87253bf57c2acc2b

## Python Imports

```
agent_sdk, boto3, datetime, json, logging, os, pathlib, shutil, subprocess, sys, tempfile, time, typing
```

## Head (first 60 lines)

```
#!/usr/bin/env python3
"""
AWS Cloud Security Agent
Performs cloud configuration audits using ScoutSuite and custom checks
"""
import os
import sys
import json
import time
import logging
import subprocess
import tempfile
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime
import boto3
from pathlib import Path

# Add orchestrator SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../orchestrator'))
from agent_sdk import AgentClient, AgentConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('aws_agent')

class AWSSecurityAgent:
    """AWS cloud security scanning agent"""
    
    def __init__(self):
        self.config = AgentConfig(
            name="aws_agent",
            agent_type="cloud_aws",
            capabilities=["cloud_audit", "aws_scan", "config_review"],
            version="1.0.0"
        )
        self.client = AgentClient(self.config)
        self.temp_dir = tempfile.mkdtemp(prefix="aws_agent_")
        
    def cleanup(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def parse_job_params(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Extract AWS credentials and scan parameters from job"""
        params = job.get('params', {})
        
        # Extract AWS credentials (should be encrypted/secured in production)
        aws_config = {
            'access_key': params.get('aws_access_key'),
            'secret_key': params.get('aws_secret_key'),
            'session_token': params.get('aws_session_token'),
            'region': params.get('aws_region', 'us-east-1'),
            'profile': params.get('aws_profile'),
            'role_arn': params.get('aws_role_arn')
        }
        
```

## Tail (last 60 lines)

```
                'status': 'completed',
                'findings_count': len(all_findings),
                'report': report
            }
            
        except Exception as e:
            logger.error(f"Job execution failed: {e}")
            self.client.post_event("error", f"Job failed: {str(e)[:500]}")
            return {
                'status': 'failed',
                'error': str(e)
            }
        finally:
            self.cleanup()
    
    def run(self):
        """Main agent loop"""
        logger.info("AWS Security Agent starting...")
        
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
        finally:
            self.cleanup()

if __name__ == "__main__":
    agent = AWSSecurityAgent()
    agent.run()
```

