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
                "-config", "api.disablekey=true"
            ]
            
            self.zap_daemon = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for ZAP to start
            time.sleep(10)
            
            # Verify ZAP is running
            for _ in range(30):
                try:
                    response = requests.get("http://127.0.0.1:8090/JSON/core/view/version/")
                    if response.status_code == 200:
                        logger.info("ZAP daemon started successfully")
                        return True
                except:
                    pass
                time.sleep(2)
            
            logger.error("ZAP daemon failed to start")
            return False
            
        except Exception as e:
            logger.error(f"Error starting ZAP: {e}")
            return False
    
    def stop_zap_daemon(self):
        """Stop ZAP daemon"""
        if self.zap_daemon:
            logger.info("Stopping ZAP daemon...")
            self.zap_daemon.terminate()
            self.zap_daemon.wait()
    
    def register(self):
        """Register agent with orchestrator"""
        try:
            data = {
                "name": self.agent_name,
                "type": self.agent_type,
                "version": "2.0.0",
                "capabilities": [
                    "web_discovery",
                    "web_vulnerabilities",
                    "api_fuzzing"
                ]
            }
            
            response = self.session.post(
                f"{self.orchestrator_url}/api/v2/agents/register",
                json=data
            )
            
            if response.status_code == 200:
                logger.info("Agent registered successfully")
                return True
            else:
                logger.error(f"Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    def heartbeat(self):
        """Send heartbeat to orchestrator"""
        try:
            response = self.session.post(
                f"{self.orchestrator_url}/api/v2/agents/heartbeat"
            )
            return response.status_code == 200
        except:
            return False
    
    def lease_job(self) -> Optional[Dict[str, Any]]:
        """Lease a job from orchestrator"""
        try:
            response = self.session.post(
                f"{self.orchestrator_url}/api/v2/agents/lease",
                json={"agent_type": self.agent_type}
            )
            
            if response.status_code == 200:
                job = response.json()
                if job:
                    logger.info(f"Leased job: {job['id']}")
                    return job
            
            return None
            
        except Exception as e:
            logger.error(f"Lease error: {e}")
            return None
    
    def execute_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a ZAP scanning job"""
        logger.info(f"Executing job {job['id']}: {job['test_id']}")
        
        test_id = job['test_id']
        parameters = job.get('parameters', {})
        
        try:
            if test_id == "web_discovery":
                return self.execute_discovery(parameters)
            elif test_id == "web_vulnerabilities":
                return self.execute_vulnerability_scan(parameters)
            elif test_id == "api_fuzzing":
                return self.execute_api_fuzzing(parameters)
            else:
                logger.warning(f"Unknown test type: {test_id}")
                return {
                    "status": "failed",
                    "error_message": f"Unknown test type: {test_id}"
                }
                
        except Exception as e:
            logger.error(f"Job execution error: {e}")
            return {
                "status": "failed",
                "error_message": str(e)
            }
    
    def execute_discovery(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute web discovery scan"""
        target = parameters.get("target", "http://localhost")
        logger.info(f"Starting discovery scan on {target}")
        
        try:
            # Spider the target
            spider_response = requests.get(
                f"http://127.0.0.1:8090/JSON/spider/action/scan/",
                params={"url": target, "maxChildren": "10", "recurse": "true"}
            )
            
            if spider_response.status_code != 200:
                raise Exception("Spider scan failed")
            
            spider_id = spider_response.json()["scan"]
            
            # Wait for spider to complete
            while True:
                status_response = requests.get(
                    f"http://127.0.0.1:8090/JSON/spider/view/status/",
                    params={"scanId": spider_id}
                )
                
                status = int(status_response.json()["status"])
                if status >= 100:
                    break
                
                logger.info(f"Spider progress: {status}%")
                time.sleep(5)
            
            # Get discovered URLs
            urls_response = requests.get(
                f"http://127.0.0.1:8090/JSON/spider/view/results/",
                params={"scanId": spider_id}
            )
            
            urls = urls_response.json()["results"]
            
            # Run passive scan
            pscan_response = requests.get(
                f"http://127.0.0.1:8090/JSON/pscan/action/enableAllScanners/"
            )
            
            # Wait for passive scan
            time.sleep(10)
            
            # Get alerts
            alerts_response = requests.get(
                f"http://127.0.0.1:8090/JSON/core/view/alerts/",
                params={"baseurl": target}
            )
            
            alerts = alerts_response.json()["alerts"]
            
            # Process findings
            findings = []
            for alert in alerts:
                findings.append({
                    "title": alert.get("name", "Unknown"),
                    "description": alert.get("description", ""),
                    "severity": self._map_zap_severity(alert.get("risk", "Informational")),
                    "type": alert.get("wascid", ""),
                    "component": alert.get("url", ""),
                    "evidence": {
                        "method": alert.get("method"),
                        "param": alert.get("param"),
                        "attack": alert.get("attack"),
                        "evidence": alert.get("evidence")
                    },
                    "remediation": alert.get("solution", ""),
                    "references": [alert.get("reference", "")]
                })
            
            return {
                "status": "completed",
                "result": {
                    "urls_discovered": len(urls),
                    "findings": findings
                }
            }
            
        except Exception as e:
            logger.error(f"Discovery scan error: {e}")
            return {
                "status": "failed",
                "error_message": str(e)
            }
    
    def execute_vulnerability_scan(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute vulnerability scan"""
        target = parameters.get("target", "http://localhost")
        logger.info(f"Starting vulnerability scan on {target}")
        
        if not self.allow_active_scan:
            logger.warning("Active scanning disabled - running passive scan only")
            return self.execute_discovery(parameters)
        
        try:
            # First run discovery
            discovery_result = self.execute_discovery(parameters)
            
            # Then run active scan
            ascan_response = requests.get(
                f"http://127.0.0.1:8090/JSON/ascan/action/scan/",
                params={
                    "url": target,
                    "recurse": "true",
                    "inScopeOnly": "false",
                    "scanPolicyName": "",
                    "method": "",
                    "postData": ""
                }
            )
            
            if ascan_response.status_code != 200:
                raise Exception("Active scan failed")
            
            scan_id = ascan_response.json()["scan"]
            
            # Wait for scan to complete
            while True:
                status_response = requests.get(
                    f"http://127.0.0.1:8090/JSON/ascan/view/status/",
                    params={"scanId": scan_id}
                )
                
                status = int(status_response.json()["status"])
                if status >= 100:
                    break
                
                logger.info(f"Active scan progress: {status}%")
                time.sleep(10)
            
            # Get all alerts
            alerts_response = requests.get(
                f"http://127.0.0.1:8090/JSON/core/view/alerts/",
                params={"baseurl": target}
            )
            
            alerts = alerts_response.json()["alerts"]
            
            # Process findings
            findings = []
            for alert in alerts:
                findings.append({
                    "title": alert.get("name", "Unknown"),
                    "description": alert.get("description", ""),
                    "severity": self._map_zap_severity(alert.get("risk", "Informational")),
                    "type": alert.get("wascid", ""),
                    "component": alert.get("url", ""),
                    "evidence": {
                        "method": alert.get("method"),
                        "param": alert.get("param"),
                        "attack": alert.get("attack"),
                        "evidence": alert.get("evidence")
                    },
                    "remediation": alert.get("solution", ""),
                    "references": [alert.get("reference", "")]
                })
            
            return {
                "status": "completed",
                "result": {
                    "findings": findings
                }
            }
            
        except Exception as e:
            logger.error(f"Vulnerability scan error: {e}")
            return {
                "status": "failed",
                "error_message": str(e)
            }
    
    def execute_api_fuzzing(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute API fuzzing"""
        # Similar implementation to vulnerability scan but with API-specific tests
        return self.execute_vulnerability_scan(parameters)
    
    def _map_zap_severity(self, risk: str) -> str:
        """Map ZAP risk levels to our severity levels"""
        mapping = {
            "High": "high",
            "Medium": "medium",
            "Low": "low",
            "Informational": "info"
        }
        return mapping.get(risk, "info")
    
    def complete_job(self, job_id: str, result: Dict[str, Any]):
        """Report job completion to orchestrator"""
        try:
            response = self.session.post(
                f"{self.orchestrator_url}/api/v2/jobs/{job_id}/complete",
                json=result
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



