#!/usr/bin/env python3
"""
LLM-Orchestrated Penetration Testing Controller
This module allows an LLM to control the entire penetration testing process
"""
import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class TestPhase(Enum):
    """Penetration test phases"""
    RECONNAISSANCE = "reconnaissance"
    ENUMERATION = "enumeration" 
    VULNERABILITY_ASSESSMENT = "vulnerability_assessment"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    LATERAL_MOVEMENT = "lateral_movement"
    PERSISTENCE = "persistence"
    EXFILTRATION = "exfiltration"
    REPORTING = "reporting"

class AgentCommand(BaseModel):
    """Command to be executed by a remote agent"""
    agent_id: str
    command_type: str  # shell, tool, script
    command: str
    args: List[str] = []
    params: Dict[str, Any] = {}
    timeout: int = 300
    requires_output: bool = True
    phase: TestPhase

class LLMDecision(BaseModel):
    """Decision made by the LLM"""
    reasoning: str
    next_commands: List[AgentCommand]
    phase_transition: Optional[str] = None
    findings_analysis: Optional[str] = None
    risk_assessment: Optional[str] = None

class PentestContext(BaseModel):
    """Current context of the penetration test"""
    engagement_id: str
    current_phase: TestPhase
    target_info: Dict[str, Any]
    discovered_services: List[Dict[str, Any]] = []
    identified_vulnerabilities: List[Dict[str, Any]] = []
    successful_exploits: List[Dict[str, Any]] = []
    credentials_found: List[Dict[str, Any]] = []
    lateral_movement_paths: List[Dict[str, Any]] = []
    command_history: List[Dict[str, Any]] = []
    agent_statuses: Dict[str, Any] = {}

class LLMOrchestrator:
    """
    Main orchestrator that interfaces between LLM and remote agents
    Manages the entire penetration testing workflow
    """
    
    def __init__(self, orchestrator_url: str, llm_provider: str = "openai"):
        self.orchestrator_url = orchestrator_url
        self.llm_provider = llm_provider
        self.context = None
        self.session = None
        self.active_agents = {}
        
        # LLM configuration
        self.llm_config = {
            "openai": {
                "api_key": os.environ.get("OPENAI_API_KEY"),
                "model": os.environ.get("OPENAI_MODEL", "gpt-4o"),
                "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
            },
            "anthropic": {
                "api_key": os.environ.get("ANTHROPIC_API_KEY"),
                "model": os.environ.get("ANTHROPIC_MODEL", "claude-3-opus-20240229")
            },
            "local": {
                "url": os.environ.get("LOCAL_LLM_URL", "http://localhost:11434"),
                "model": os.environ.get("LOCAL_LLM_MODEL", "mixtral")
            }
        }
    
    async def initialize(self, engagement_id: str, targets: List[str], scope: Dict[str, Any]):
        """Initialize a new penetration test"""
        self.session = aiohttp.ClientSession()
        
        self.context = PentestContext(
            engagement_id=engagement_id,
            current_phase=TestPhase.RECONNAISSANCE,
            target_info={
                "targets": targets,
                "scope": scope,
                "start_time": datetime.utcnow().isoformat()
            }
        )
        
        # Connect to available agents
        await self._discover_agents()
        
        logger.info(f"Initialized pentest for engagement {engagement_id}")
        return True
    
    async def _discover_agents(self):
        """Discover available agents from orchestrator"""
        async with self.session.get(f"{self.orchestrator_url}/v2/agents") as resp:
            agents = await resp.json()
            
        for agent in agents:
            if agent["status"] == "online":
                self.active_agents[agent["id"]] = {
                    "type": agent["agent_type"],
                    "capabilities": agent.get("capabilities", []),
                    "os": agent.get("os", "unknown"),
                    "last_heartbeat": agent.get("last_heartbeat")
                }
        
        logger.info(f"Discovered {len(self.active_agents)} active agents")
    
    async def execute_command_on_agent(self, command: AgentCommand) -> Dict[str, Any]:
        """Execute a command on a specific agent"""
        
        # Create job for agent
        job_data = {
            "agent_id": command.agent_id,
            "type": command.command_type,
            "command": command.command,
            "args": command.args,
            "params": command.params,
            "timeout": command.timeout
        }
        
        async with self.session.post(
            f"{self.orchestrator_url}/v2/jobs",
            json=job_data
        ) as resp:
            job = await resp.json()
        
        # Wait for completion if output required
        if command.requires_output:
            result = await self._wait_for_job_completion(job["id"], command.timeout)
        else:
            result = {"status": "submitted", "job_id": job["id"]}
        
        # Update context with command history
        self.context.command_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "phase": command.phase.value,
            "command": command.command,
            "agent": command.agent_id,
            "result": result
        })
        
        return result
    
    async def _wait_for_job_completion(self, job_id: str, timeout: int) -> Dict[str, Any]:
        """Wait for a job to complete and return results"""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            async with self.session.get(f"{self.orchestrator_url}/v2/jobs/{job_id}") as resp:
                job = await resp.json()
            
            if job["status"] in ["completed", "failed"]:
                return job
            
            await asyncio.sleep(2)
        
        return {"status": "timeout", "job_id": job_id}
    
    async def get_llm_decision(self, prompt: str, context: Dict[str, Any]) -> LLMDecision:
        """Get decision from LLM based on current context"""
        
        if self.llm_provider == "openai":
            return await self._get_openai_decision(prompt, context)
        elif self.llm_provider == "anthropic":
            return await self._get_anthropic_decision(prompt, context)
        elif self.llm_provider == "local":
            return await self._get_local_llm_decision(prompt, context)
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")
    
    async def _get_openai_decision(self, prompt: str, context: Dict[str, Any]) -> LLMDecision:
        """Get decision from OpenAI"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=self.llm_config["openai"]["api_key"],
            base_url=self.llm_config["openai"]["base_url"]
        )
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert penetration tester controlling a distributed testing system.
                You analyze results and decide next steps. Always follow legal and ethical guidelines.
                Provide decisions in JSON format with reasoning and specific commands for agents."""
            },
            {
                "role": "user",
                "content": f"{prompt}\n\nContext:\n{json.dumps(context, indent=2)}"
            }
        ]
        
        response = await client.chat.completions.create(
            model=self.llm_config["openai"]["model"],
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        decision_data = json.loads(response.choices[0].message.content)
        return LLMDecision(**decision_data)
    
    async def _get_anthropic_decision(self, prompt: str, context: Dict[str, Any]) -> LLMDecision:
        """Get decision from Anthropic Claude"""
        from anthropic import AsyncAnthropic
        
        client = AsyncAnthropic(api_key=self.llm_config["anthropic"]["api_key"])
        
        message = await client.messages.create(
            model=self.llm_config["anthropic"]["model"],
            max_tokens=2000,
            system="""You are an expert penetration tester controlling a distributed testing system.
            Analyze results and decide next steps following legal and ethical guidelines.
            Respond with JSON containing reasoning and specific agent commands.""",
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\nContext:\n{json.dumps(context, indent=2)}\n\nProvide response as JSON."
                }
            ]
        )
        
        decision_data = json.loads(message.content[0].text)
        return LLMDecision(**decision_data)
    
    async def _get_local_llm_decision(self, prompt: str, context: Dict[str, Any]) -> LLMDecision:
        """Get decision from local LLM (Ollama, etc.)"""
        url = f"{self.llm_config['local']['url']}/api/generate"
        
        data = {
            "model": self.llm_config["local"]["model"],
            "prompt": f"""You are a penetration tester. Analyze and decide next steps.
            
{prompt}

Context:
{json.dumps(context, indent=2)}

Respond with JSON containing: reasoning, next_commands (list of agent commands), 
phase_transition (if changing phase), findings_analysis, risk_assessment.""",
            "format": "json",
            "stream": False
        }
        
        async with self.session.post(url, json=data) as resp:
            result = await resp.json()
        
        decision_data = json.loads(result["response"])
        return LLMDecision(**decision_data)
    
    async def run_penetration_test(self) -> Dict[str, Any]:
        """Main loop - run the entire penetration test"""
        
        test_complete = False
        max_iterations = 1000  # Safety limit
        iteration = 0
        
        while not test_complete and iteration < max_iterations:
            iteration += 1
            
            # Build prompt for LLM based on current phase and context
            prompt = self._build_llm_prompt()
            
            # Get LLM decision
            context_dict = self.context.dict()
            context_dict["active_agents"] = self.active_agents
            
            try:
                decision = await self.get_llm_decision(prompt, context_dict)
            except Exception as e:
                logger.error(f"LLM decision error: {e}")
                await asyncio.sleep(5)
                continue
            
            logger.info(f"LLM Decision: {decision.reasoning[:200]}...")
            
            # Execute commands from LLM decision
            for command in decision.next_commands:
                try:
                    logger.info(f"Executing: {command.command} on {command.agent_id}")
                    result = await self.execute_command_on_agent(command)
                    
                    # Process result based on command type
                    await self._process_command_result(command, result)
                    
                except Exception as e:
                    logger.error(f"Command execution error: {e}")
            
            # Handle phase transition if suggested
            if decision.phase_transition:
                old_phase = self.context.current_phase
                self.context.current_phase = TestPhase(decision.phase_transition)
                logger.info(f"Phase transition: {old_phase.value} -> {self.context.current_phase.value}")
            
            # Store findings analysis
            if decision.findings_analysis:
                await self._store_findings_analysis(decision.findings_analysis)
            
            # Check if test is complete
            if self.context.current_phase == TestPhase.REPORTING:
                test_complete = True
            
            # Safety delay between iterations
            await asyncio.sleep(2)
        
        # Generate final report
        report = await self._generate_final_report()
        
        return report
    
    def _build_llm_prompt(self) -> str:
        """Build context-aware prompt for LLM"""
        
        phase_prompts = {
            TestPhase.RECONNAISSANCE: """
                We are in the reconnaissance phase. Analyze the targets and gather initial information.
                Suggest commands for: DNS enumeration, port scanning, service detection, subdomain discovery.
                Available tools: nmap, dnsx, httpx, subfinder, amass
            """,
            TestPhase.ENUMERATION: """
                We are in the enumeration phase. Deep dive into discovered services.
                Suggest commands for: service version detection, banner grabbing, directory enumeration.
                Available tools: nmap scripts, gobuster, ffuf, nikto
            """,
            TestPhase.VULNERABILITY_ASSESSMENT: """
                We are in vulnerability assessment. Identify security issues in discovered services.
                Suggest commands for: vulnerability scanning, configuration review, known CVE checks.
                Available tools: nuclei, nmap vuln scripts, custom scripts
            """,
            TestPhase.EXPLOITATION: """
                We are in exploitation phase. Attempt to exploit identified vulnerabilities safely.
                Only proceed with non-destructive exploits. Suggest careful exploitation attempts.
                Available tools: metasploit, custom exploits, manual techniques
            """,
            TestPhase.POST_EXPLOITATION: """
                We are in post-exploitation. Gather evidence and assess impact.
                Suggest commands for: privilege escalation checks, credential harvesting, system enumeration.
                Available tools: linpeas, winpeas, mimikatz (if authorized)
            """,
            TestPhase.LATERAL_MOVEMENT: """
                We are exploring lateral movement. Map the internal network and identify pivot points.
                Suggest commands for: network mapping, share enumeration, trust relationship discovery.
                Available tools: crackmapexec, bloodhound, internal port scans
            """
        }
        
        base_prompt = f"""
Current Phase: {self.context.current_phase.value}

{phase_prompts.get(self.context.current_phase, "Analyze current situation and suggest next steps.")}

Recent discoveries:
- Services found: {len(self.context.discovered_services)}
- Vulnerabilities identified: {len(self.context.identified_vulnerabilities)}
- Successful exploits: {len(self.context.successful_exploits)}
- Credentials found: {len(self.context.credentials_found)}

Analyze the current context and provide:
1. Your reasoning about the current situation
2. Specific commands to execute next (with agent assignments)
3. Whether we should transition to a different phase
4. Analysis of any critical findings
5. Current risk assessment

Be methodical, thorough, and always maintain operational security.
"""
        return base_prompt
    
    async def _process_command_result(self, command: AgentCommand, result: Dict[str, Any]):
        """Process and categorize command results"""
        
        if result.get("status") != "completed":
            return
        
        output = result.get("output", "")
        
        # Parse results based on command type and phase
        if command.phase == TestPhase.RECONNAISSANCE:
            # Parse port scan results
            if "nmap" in command.command:
                services = self._parse_nmap_output(output)
                self.context.discovered_services.extend(services)
            
            # Parse DNS results
            elif "dnsx" in command.command or "dns" in command.command:
                domains = self._parse_dns_output(output)
                self.context.target_info["discovered_domains"] = domains
        
        elif command.phase == TestPhase.VULNERABILITY_ASSESSMENT:
            # Parse vulnerability scan results
            if "nuclei" in command.command:
                vulns = self._parse_nuclei_output(output)
                self.context.identified_vulnerabilities.extend(vulns)
        
        elif command.phase == TestPhase.EXPLOITATION:
            # Track successful exploits
            if "session" in output.lower() or "shell" in output.lower():
                self.context.successful_exploits.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "target": command.params.get("target"),
                    "exploit": command.command,
                    "result": output[:500]
                })
        
        elif command.phase == TestPhase.POST_EXPLOITATION:
            # Parse credentials
            if "password" in output.lower() or "hash" in output.lower():
                creds = self._parse_credentials(output)
                self.context.credentials_found.extend(creds)
    
    def _parse_nmap_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse nmap output for services"""
        services = []
        # Simplified parsing - in production, use proper nmap XML output
        for line in output.split("\n"):
            if "/tcp" in line and "open" in line:
                parts = line.split()
                if len(parts) >= 3:
                    port = parts[0].split("/")[0]
                    state = parts[1]
                    service = parts[2] if len(parts) > 2 else "unknown"
                    services.append({
                        "port": port,
                        "state": state,
                        "service": service,
                        "protocol": "tcp"
                    })
        return services
    
    def _parse_dns_output(self, output: str) -> List[str]:
        """Parse DNS enumeration output"""
        domains = []
        for line in output.split("\n"):
            if "." in line and not line.startswith("#"):
                domain = line.strip().split()[0]
                if domain and domain not in domains:
                    domains.append(domain)
        return domains
    
    def _parse_nuclei_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse nuclei vulnerability scan output"""
        vulns = []
        # Parse nuclei JSON output
        try:
            for line in output.split("\n"):
                if line.strip().startswith("{"):
                    vuln = json.loads(line)
                    vulns.append({
                        "template": vuln.get("template-id"),
                        "severity": vuln.get("severity"),
                        "host": vuln.get("host"),
                        "matched": vuln.get("matched-at"),
                        "info": vuln.get("info", {})
                    })
        except:
            pass
        return vulns
    
    def _parse_credentials(self, output: str) -> List[Dict[str, Any]]:
        """Parse credentials from output"""
        creds = []
        # Simplified credential parsing
        lines = output.split("\n")
        for line in lines:
            if ":" in line and ("password" in line.lower() or "hash" in line.lower()):
                parts = line.split(":")
                if len(parts) >= 2:
                    creds.append({
                        "type": "hash" if "hash" in line.lower() else "password",
                        "username": parts[0].strip(),
                        "credential": parts[1].strip(),
                        "source": "post_exploitation"
                    })
        return creds
    
    async def _store_findings_analysis(self, analysis: str):
        """Store LLM's analysis of findings"""
        finding_data = {
            "engagement_id": self.context.engagement_id,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat(),
            "phase": self.context.current_phase.value
        }
        
        async with self.session.post(
            f"{self.orchestrator_url}/v2/findings/analysis",
            json=finding_data
        ) as resp:
            result = await resp.json()
        
        logger.info("Stored findings analysis")
    
    async def _generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive penetration test report"""
        
        report = {
            "engagement_id": self.context.engagement_id,
            "test_duration": self._calculate_test_duration(),
            "executive_summary": await self._generate_executive_summary(),
            "technical_findings": {
                "services_discovered": self.context.discovered_services,
                "vulnerabilities": self.context.identified_vulnerabilities,
                "successful_exploits": self.context.successful_exploits,
                "credentials_compromised": len(self.context.credentials_found),
                "lateral_movement_paths": self.context.lateral_movement_paths
            },
            "risk_assessment": await self._generate_risk_assessment(),
            "recommendations": await self._generate_recommendations(),
            "detailed_findings": await self._compile_detailed_findings(),
            "command_log": self.context.command_history
        }
        
        # Save report
        async with self.session.post(
            f"{self.orchestrator_url}/v2/reports",
            json=report
        ) as resp:
            result = await resp.json()
        
        logger.info(f"Generated final report: {result.get('report_id')}")
        
        return report
    
    def _calculate_test_duration(self) -> str:
        """Calculate total test duration"""
        if self.context.command_history:
            start = datetime.fromisoformat(self.context.target_info["start_time"])
            end = datetime.fromisoformat(self.context.command_history[-1]["timestamp"])
            duration = end - start
            return str(duration)
        return "Unknown"
    
    async def _generate_executive_summary(self) -> str:
        """Generate executive summary using LLM"""
        prompt = f"""
        Generate an executive summary for a penetration test with these results:
        - {len(self.context.discovered_services)} services discovered
        - {len(self.context.identified_vulnerabilities)} vulnerabilities found
        - {len(self.context.successful_exploits)} successful exploits
        - {len(self.context.credentials_found)} credentials compromised
        
        Focus on business impact and high-level risks.
        """
        
        decision = await self.get_llm_decision(prompt, {"summary_type": "executive"})
        return decision.reasoning
    
    async def _generate_risk_assessment(self) -> Dict[str, Any]:
        """Generate risk assessment"""
        critical_count = sum(1 for v in self.context.identified_vulnerabilities 
                           if v.get("severity") == "critical")
        high_count = sum(1 for v in self.context.identified_vulnerabilities 
                       if v.get("severity") == "high")
        
        risk_level = "CRITICAL" if critical_count > 0 or self.context.successful_exploits else \
                    "HIGH" if high_count > 2 else \
                    "MEDIUM" if high_count > 0 else "LOW"
        
        return {
            "overall_risk": risk_level,
            "critical_findings": critical_count,
            "high_findings": high_count,
            "exploitable_vulnerabilities": len(self.context.successful_exploits),
            "recommendations_priority": "IMMEDIATE" if risk_level == "CRITICAL" else "HIGH"
        }
    
    async def _generate_recommendations(self) -> List[str]:
        """Generate remediation recommendations"""
        recommendations = []
        
        # Basic recommendations based on findings
        if any(v.get("severity") == "critical" for v in self.context.identified_vulnerabilities):
            recommendations.append("IMMEDIATE: Patch all critical vulnerabilities identified")
        
        if self.context.credentials_found:
            recommendations.append("HIGH: Reset all compromised credentials and implement MFA")
        
        if len(self.context.discovered_services) > 20:
            recommendations.append("MEDIUM: Reduce attack surface by disabling unnecessary services")
        
        # Get LLM recommendations
        prompt = "Based on the test results, provide top 5 security recommendations"
        decision = await self.get_llm_decision(prompt, {"request": "recommendations"})
        
        if decision.findings_analysis:
            recommendations.extend(decision.findings_analysis.split("\n")[:5])
        
        return recommendations
    
    async def _compile_detailed_findings(self) -> List[Dict[str, Any]]:
        """Compile detailed findings for report"""
        findings = []
        
        # Convert vulnerabilities to detailed findings
        for vuln in self.context.identified_vulnerabilities:
            finding = {
                "title": vuln.get("template", "Unknown Vulnerability"),
                "severity": vuln.get("severity", "medium"),
                "description": f"Vulnerability found at {vuln.get('host')}",
                "evidence": vuln.get("matched"),
                "remediation": "Apply appropriate patches and configurations",
                "cvss_score": self._estimate_cvss(vuln.get("severity"))
            }
            findings.append(finding)
        
        # Add exploitation findings
        for exploit in self.context.successful_exploits:
            finding = {
                "title": f"Successful Exploitation - {exploit.get('exploit')}",
                "severity": "critical",
                "description": f"Successfully exploited target {exploit.get('target')}",
                "evidence": exploit.get("result"),
                "remediation": "Immediate patching required",
                "cvss_score": 9.0
            }
            findings.append(finding)
        
        return findings
    
    def _estimate_cvss(self, severity: str) -> float:
        """Estimate CVSS score from severity"""
        mapping = {
            "critical": 9.5,
            "high": 7.5,
            "medium": 5.0,
            "low": 3.0,
            "info": 0.0
        }
        return mapping.get(severity, 5.0)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()


# CLI Interface for running tests
async def main():
    """Main entry point for LLM-orchestrated penetration testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM-Orchestrated Penetration Testing")
    parser.add_argument("--orchestrator-url", default="http://localhost:8080")
    parser.add_argument("--llm-provider", choices=["openai", "anthropic", "local"], default="openai")
    parser.add_argument("--engagement-id", required=True)
    parser.add_argument("--targets", nargs="+", required=True)
    parser.add_argument("--scope", type=json.loads, default={})
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize orchestrator
    orchestrator = LLMOrchestrator(args.orchestrator_url, args.llm_provider)
    
    try:
        # Initialize test
        await orchestrator.initialize(args.engagement_id, args.targets, args.scope)
        
        # Run penetration test
        logger.info("Starting LLM-orchestrated penetration test...")
        report = await orchestrator.run_penetration_test()
        
        # Output report
        print("\n" + "="*60)
        print("PENETRATION TEST COMPLETE")
        print("="*60)
        print(json.dumps(report, indent=2))
        
    finally:
        await orchestrator.cleanup()

if __name__ == "__main__":
    asyncio.run(main())