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
        
        # Scan configuration
        scan_config = {
            'services': params.get('services', ['iam', 'ec2', 's3', 'rds', 'cloudtrail']),
            'use_scoutsuite': params.get('use_scoutsuite', True),
            'custom_checks': params.get('custom_checks', True),
            'max_workers': params.get('max_workers', 10)
        }
        
        return {'aws': aws_config, 'scan': scan_config}
    
    def setup_aws_session(self, aws_config: Dict[str, Any]) -> boto3.Session:
        """Create AWS session with provided credentials"""
        if aws_config.get('profile'):
            return boto3.Session(profile_name=aws_config['profile'])
        elif aws_config.get('role_arn'):
            # Assume role
            sts = boto3.client('sts')
            response = sts.assume_role(
                RoleArn=aws_config['role_arn'],
                RoleSessionName='aws_agent_scan'
            )
            creds = response['Credentials']
            return boto3.Session(
                aws_access_key_id=creds['AccessKeyId'],
                aws_secret_access_key=creds['SecretAccessKey'],
                aws_session_token=creds['SessionToken'],
                region_name=aws_config['region']
            )
        else:
            return boto3.Session(
                aws_access_key_id=aws_config['access_key'],
                aws_secret_access_key=aws_config['secret_key'],
                aws_session_token=aws_config.get('session_token'),
                region_name=aws_config['region']
            )
    
    def run_scoutsuite(self, aws_config: Dict[str, Any], services: List[str]) -> Optional[Dict]:
        """Run ScoutSuite audit"""
        try:
            self.client.post_event("info", "Starting ScoutSuite cloud audit")
            
            # Prepare ScoutSuite command
            cmd = [
                'scout', 'aws',
                '--no-browser',
                '--report-dir', self.temp_dir,
                '--report-name', 'scout_report'
            ]
            
            # Add credentials
            if aws_config.get('profile'):
                cmd.extend(['--profile', aws_config['profile']])
            else:
                # Set environment variables for credentials
                env = os.environ.copy()
                if aws_config.get('access_key'):
                    env['AWS_ACCESS_KEY_ID'] = aws_config['access_key']
                    env['AWS_SECRET_ACCESS_KEY'] = aws_config['secret_key']
                    if aws_config.get('session_token'):
                        env['AWS_SESSION_TOKEN'] = aws_config['session_token']
            
            # Add services to scan
            if services:
                cmd.extend(['--services', ','.join(services)])
            
            # Run ScoutSuite
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env if not aws_config.get('profile') else None,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"ScoutSuite failed: {result.stderr}")
                self.client.post_event("error", f"ScoutSuite failed: {result.stderr[:500]}")
                return None
            
            # Parse results
            report_file = Path(self.temp_dir) / 'scout_report' / 'scoutsuite_results.json'
            if report_file.exists():
                with open(report_file, 'r') as f:
                    return json.load(f)
            
            return None
            
        except subprocess.TimeoutExpired:
            self.client.post_event("error", "ScoutSuite scan timed out")
            return None
        except Exception as e:
            logger.error(f"ScoutSuite error: {e}")
            self.client.post_event("error", f"ScoutSuite error: {str(e)[:500]}")
            return None
    
    def run_custom_checks(self, session: boto3.Session) -> List[Dict]:
        """Run custom AWS security checks"""
        findings = []
        
        try:
            # Check S3 bucket policies
            self.client.post_event("info", "Checking S3 bucket configurations")
            s3 = session.client('s3')
            
            try:
                buckets = s3.list_buckets()
                for bucket in buckets.get('Buckets', []):
                    bucket_name = bucket['Name']
                    
                    # Check public access
                    try:
                        acl = s3.get_bucket_acl(Bucket=bucket_name)
                        for grant in acl.get('Grants', []):
                            grantee = grant.get('Grantee', {})
                            if grantee.get('Type') == 'Group' and \
                               'AllUsers' in grantee.get('URI', ''):
                                findings.append({
                                    'title': f'S3 Bucket {bucket_name} has public read access',
                                    'severity': 'high',
                                    'category': 'Cloud Misconfiguration',
                                    'service': 'S3',
                                    'resource': bucket_name,
                                    'description': 'S3 bucket allows public read access which may expose sensitive data'
                                })
                    except:
                        pass
                    
                    # Check encryption
                    try:
                        encryption = s3.get_bucket_encryption(Bucket=bucket_name)
                    except:
                        findings.append({
                            'title': f'S3 Bucket {bucket_name} lacks encryption',
                            'severity': 'medium',
                            'category': 'Cloud Misconfiguration',
                            'service': 'S3',
                            'resource': bucket_name,
                            'description': 'S3 bucket does not have default encryption enabled'
                        })
            except Exception as e:
                logger.error(f"S3 check error: {e}")
            
            # Check IAM password policy
            self.client.post_event("info", "Checking IAM configurations")
            iam = session.client('iam')
            
            try:
                policy = iam.get_account_password_policy()
                policy_data = policy['PasswordPolicy']
                
                if not policy_data.get('RequireUppercaseCharacters'):
                    findings.append({
                        'title': 'Weak IAM password policy - no uppercase required',
                        'severity': 'low',
                        'category': 'Cloud Misconfiguration',
                        'service': 'IAM',
                        'description': 'IAM password policy does not require uppercase characters'
                    })
                
                if policy_data.get('MinimumPasswordLength', 0) < 14:
                    findings.append({
                        'title': 'Weak IAM password policy - short minimum length',
                        'severity': 'medium',
                        'category': 'Cloud Misconfiguration',
                        'service': 'IAM',
                        'description': f"IAM password policy allows passwords shorter than 14 characters (current: {policy_data.get('MinimumPasswordLength', 'not set')})"
                    })
            except iam.exceptions.NoSuchEntityException:
                findings.append({
                    'title': 'No IAM password policy configured',
                    'severity': 'high',
                    'category': 'Cloud Misconfiguration',
                    'service': 'IAM',
                    'description': 'No password policy is configured for IAM users'
                })
            except Exception as e:
                logger.error(f"IAM check error: {e}")
            
            # Check EC2 security groups
            self.client.post_event("info", "Checking EC2 security groups")
            ec2 = session.client('ec2')
            
            try:
                sgs = ec2.describe_security_groups()
                for sg in sgs.get('SecurityGroups', []):
                    for rule in sg.get('IpPermissions', []):
                        for ip_range in rule.get('IpRanges', []):
                            if ip_range.get('CidrIp') == '0.0.0.0/0':
                                port_info = ""
                                if rule.get('FromPort'):
                                    port_info = f" on port {rule['FromPort']}"
                                    if rule['FromPort'] != rule.get('ToPort'):
                                        port_info = f" on ports {rule['FromPort']}-{rule['ToPort']}"
                                
                                severity = 'medium'
                                if rule.get('FromPort') in [22, 3389, 445, 135, 139]:
                                    severity = 'critical'
                                elif rule.get('FromPort') in [80, 443, 8080, 8443]:
                                    severity = 'low'
                                
                                findings.append({
                                    'title': f"Security group {sg['GroupId']} allows unrestricted inbound access{port_info}",
                                    'severity': severity,
                                    'category': 'Cloud Misconfiguration',
                                    'service': 'EC2',
                                    'resource': sg['GroupId'],
                                    'description': f"Security group {sg['GroupName']} allows inbound traffic from any IP address{port_info}"
                                })
            except Exception as e:
                logger.error(f"EC2 check error: {e}")
            
            # Check CloudTrail
            self.client.post_event("info", "Checking CloudTrail configuration")
            cloudtrail = session.client('cloudtrail')
            
            try:
                trails = cloudtrail.describe_trails()
                if not trails.get('trailList'):
                    findings.append({
                        'title': 'No CloudTrail configured',
                        'severity': 'high',
                        'category': 'Cloud Misconfiguration',
                        'service': 'CloudTrail',
                        'description': 'No CloudTrail is configured to log API calls'
                    })
                else:
                    for trail in trails['trailList']:
                        status = cloudtrail.get_trail_status(Name=trail['TrailARN'])
                        if not status.get('IsLogging'):
                            findings.append({
                                'title': f"CloudTrail {trail['Name']} is not logging",
                                'severity': 'high',
                                'category': 'Cloud Misconfiguration',
                                'service': 'CloudTrail',
                                'resource': trail['Name'],
                                'description': 'CloudTrail exists but is not actively logging events'
                            })
            except Exception as e:
                logger.error(f"CloudTrail check error: {e}")
            
        except Exception as e:
            logger.error(f"Custom checks error: {e}")
            self.client.post_event("error", f"Custom checks failed: {str(e)[:500]}")
        
        return findings
    
    def process_scoutsuite_findings(self, scout_data: Dict) -> List[Dict]:
        """Convert ScoutSuite findings to our format"""
        findings = []
        
        # Process each service
        for service_name, service_data in scout_data.get('services', {}).items():
            if not isinstance(service_data, dict):
                continue
            
            # Process findings in service
            for finding_type, finding_data in service_data.get('findings', {}).items():
                if not isinstance(finding_data, dict):
                    continue
                
                # Map ScoutSuite severity
                scout_level = finding_data.get('level', 'warning')
                severity_map = {
                    'danger': 'critical',
                    'warning': 'high',
                    'caution': 'medium',
                    'info': 'low'
                }
                severity = severity_map.get(scout_level, 'medium')
                
                # Get affected resources
                items = finding_data.get('items', [])
                if items:
                    for item in items[:10]:  # Limit to first 10 to avoid huge reports
                        findings.append({
                            'title': finding_data.get('description', finding_type),
                            'severity': severity,
                            'category': 'Cloud Misconfiguration',
                            'service': service_name.upper(),
                            'resource': item,
                            'description': finding_data.get('rationale', ''),
                            'remediation': finding_data.get('remediation', '')
                        })
                elif finding_data.get('flagged'):
                    findings.append({
                        'title': finding_data.get('description', finding_type),
                        'severity': severity,
                        'category': 'Cloud Misconfiguration',
                        'service': service_name.upper(),
                        'description': finding_data.get('rationale', ''),
                        'remediation': finding_data.get('remediation', '')
                    })
        
        return findings
    
    def execute_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AWS cloud security scan"""
        try:
            self.client.post_event("info", f"Starting AWS cloud security scan for job {job['id']}")
            
            # Parse parameters
            config = self.parse_job_params(job)
            aws_config = config['aws']
            scan_config = config['scan']
            
            # Setup AWS session
            session = self.setup_aws_session(aws_config)
            
            # Verify credentials
            try:
                sts = session.client('sts')
                identity = sts.get_caller_identity()
                self.client.post_event("info", f"Authenticated as: {identity['Arn']}")
            except Exception as e:
                self.client.post_event("error", f"AWS authentication failed: {str(e)}")
                return {
                    'status': 'failed',
                    'error': 'AWS authentication failed',
                    'findings': []
                }
            
            all_findings = []
            
            # Run ScoutSuite if enabled
            if scan_config.get('use_scoutsuite'):
                scout_data = self.run_scoutsuite(aws_config, scan_config['services'])
                if scout_data:
                    scout_findings = self.process_scoutsuite_findings(scout_data)
                    all_findings.extend(scout_findings)
                    
                    # Save full ScoutSuite report as artifact
                    report_path = Path(self.temp_dir) / 'scoutsuite_full.json'
                    with open(report_path, 'w') as f:
                        json.dump(scout_data, f, indent=2)
                    
                    self.client.upload_artifact(
                        job['id'],
                        str(report_path),
                        'scoutsuite_report.json',
                        'application/json'
                    )
            
            # Run custom checks if enabled
            if scan_config.get('custom_checks'):
                custom_findings = self.run_custom_checks(session)
                all_findings.extend(custom_findings)
            
            # Create findings report
            report = {
                'scan_type': 'aws_cloud_audit',
                'account_id': identity.get('Account'),
                'scan_time': datetime.utcnow().isoformat(),
                'services_scanned': scan_config['services'],
                'total_findings': len(all_findings),
                'findings_by_severity': {},
                'findings': all_findings
            }
            
            # Count by severity
            for finding in all_findings:
                sev = finding['severity']
                report['findings_by_severity'][sev] = report['findings_by_severity'].get(sev, 0) + 1
            
            # Save report as artifact
            report_path = Path(self.temp_dir) / 'aws_audit_report.json'
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.client.upload_artifact(
                job['id'],
                str(report_path),
                'aws_audit_report.json',
                'application/json'
            )
            
            # Post findings to orchestrator
            for finding in all_findings:
                self.client.post_finding(
                    job['id'],
                    title=finding['title'],
                    severity=finding['severity'],
                    category=finding['category'],
                    description=finding['description'],
                    evidence={
                        'service': finding.get('service'),
                        'resource': finding.get('resource')
                    },
                    remediation=finding.get('remediation')
                )
            
            self.client.post_event("success", f"AWS scan completed: {len(all_findings)} findings")
            
            return {
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