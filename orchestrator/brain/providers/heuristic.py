# Destination: patches/v2.0.0/orchestrator/brain/providers/heuristic.py
# Rationale: Rule-based fallback provider that always works without external dependencies
# Generates reasonable test plans based on engagement type and scope

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class HeuristicProvider:
    """Heuristic/rule-based provider for generating test plans."""
    
    def __init__(self):
        self.enabled = True  # Always enabled
        self.templates = self._load_templates()
    
    def is_available(self) -> bool:
        """Check if provider is available (always true for heuristic)."""
        return True
    
    async def generate_plan(self, 
                           engagement_data: Dict[str, Any],
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a test plan based on rules and templates."""
        
        # Determine engagement type
        engagement_type = engagement_data.get("engagement_type", "general")
        scope = engagement_data.get("scope", {})
        
        # Select appropriate template
        if engagement_type in self.templates:
            base_plan = self.templates[engagement_type].copy()
        else:
            base_plan = self.templates["general"].copy()
        
        # Customize plan based on scope
        plan = self._customize_plan(base_plan, engagement_data, scope)
        
        # Add metadata
        plan["created_at"] = datetime.utcnow().isoformat()
        plan["provider"] = "heuristic"
        plan["metadata"] = {
            "generator": "heuristic_provider",
            "version": "1.0.0",
            "engagement_id": engagement_data.get("id"),
            "created_by": "rule_based_engine"
        }
        
        return plan
    
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load plan templates for different engagement types."""
        return {
            "web_application": self._get_web_app_template(),
            "network": self._get_network_template(),
            "mobile": self._get_mobile_template(),
            "cloud": self._get_cloud_template(),
            "api": self._get_api_template(),
            "general": self._get_general_template()
        }
    
    def _customize_plan(self, base_plan: Dict[str, Any], 
                       engagement_data: Dict[str, Any],
                       scope: Dict[str, Any]) -> Dict[str, Any]:
        """Customize the plan based on engagement specifics."""
        
        # Update plan name and description
        base_plan["name"] = f"Test Plan - {engagement_data.get('name', 'Security Assessment')}"
        base_plan["description"] = engagement_data.get('description', base_plan.get('description', ''))
        
        # Adjust targets in steps
        targets = scope.get('targets', [])
        if targets:
            for phase in base_plan.get("phases", []):
                for step in phase.get("steps", []):
                    if step.get("target") == "TARGET_PLACEHOLDER":
                        step["target"] = targets[0] if isinstance(targets[0], str) else json.dumps(targets[0])
        
        # Add excluded items as constraints
        excluded = scope.get('excluded', [])
        if excluded:
            base_plan["constraints"] = {
                "excluded_targets": excluded,
                "excluded_tests": scope.get('excluded_tests', [])
            }
        
        # Determine risk level based on scope
        if scope.get('production', False):
            base_plan["risk_level"] = "high"
            base_plan["approval_required"] = True
        else:
            base_plan["risk_level"] = "medium"
            base_plan["approval_required"] = False
        
        # Extract dependencies
        base_plan["dependencies"] = self._extract_dependencies(base_plan)
        
        return base_plan
    
    def _extract_dependencies(self, plan: Dict[str, Any]) -> List[str]:
        """Extract tool dependencies from plan."""
        tools = set()
        for phase in plan.get("phases", []):
            for step in phase.get("steps", []):
                if "tool" in step:
                    tools.add(step["tool"])
        return sorted(list(tools))
    
    def _get_web_app_template(self) -> Dict[str, Any]:
        """Template for web application testing."""
        return {
            "name": "Web Application Security Test",
            "description": "Comprehensive web application security assessment",
            "risk_level": "medium",
            "estimated_duration": "16 hours",
            "phases": [
                {
                    "name": "Reconnaissance",
                    "order": 1,
                    "description": "Information gathering and enumeration",
                    "steps": [
                        {
                            "order": 1,
                            "action": "Subdomain enumeration",
                            "tool": "subfinder",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"recursive": True, "sources": "all"},
                            "expected_outcome": "List of subdomains",
                            "risk_level": "low"
                        },
                        {
                            "order": 2,
                            "action": "Technology stack identification",
                            "tool": "wappalyzer",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {},
                            "expected_outcome": "Technology stack details",
                            "risk_level": "low"
                        },
                        {
                            "order": 3,
                            "action": "Directory and file enumeration",
                            "tool": "gobuster",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"wordlist": "common.txt", "extensions": "php,asp,aspx,jsp"},
                            "expected_outcome": "Hidden directories and files",
                            "risk_level": "low"
                        }
                    ]
                },
                {
                    "name": "Vulnerability Scanning",
                    "order": 2,
                    "description": "Automated vulnerability detection",
                    "steps": [
                        {
                            "order": 1,
                            "action": "Web vulnerability scan",
                            "tool": "nikto",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"tuning": "123456789", "format": "json"},
                            "expected_outcome": "Common web vulnerabilities",
                            "risk_level": "medium"
                        },
                        {
                            "order": 2,
                            "action": "SSL/TLS configuration scan",
                            "tool": "testssl",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"severity": "all"},
                            "expected_outcome": "SSL/TLS vulnerabilities",
                            "risk_level": "low"
                        },
                        {
                            "order": 3,
                            "action": "OWASP Top 10 scan",
                            "tool": "zap",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"mode": "standard", "ajax": True},
                            "expected_outcome": "OWASP vulnerabilities",
                            "risk_level": "medium"
                        }
                    ]
                },
                {
                    "name": "Manual Testing",
                    "order": 3,
                    "description": "Manual security testing and validation",
                    "steps": [
                        {
                            "order": 1,
                            "action": "Authentication testing",
                            "tool": "burp",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"test_types": ["bypass", "bruteforce", "session"]},
                            "expected_outcome": "Authentication vulnerabilities",
                            "risk_level": "medium"
                        },
                        {
                            "order": 2,
                            "action": "SQL injection testing",
                            "tool": "sqlmap",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"level": 2, "risk": 1, "batch": True},
                            "expected_outcome": "SQL injection points",
                            "risk_level": "high"
                        },
                        {
                            "order": 3,
                            "action": "XSS testing",
                            "tool": "xsstrike",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"fuzzer": True, "crawl": True},
                            "expected_outcome": "XSS vulnerabilities",
                            "risk_level": "medium"
                        }
                    ]
                }
            ],
            "approval_required": False
        }
    
    def _get_network_template(self) -> Dict[str, Any]:
        """Template for network penetration testing."""
        return {
            "name": "Network Penetration Test",
            "description": "Network infrastructure security assessment",
            "risk_level": "medium",
            "estimated_duration": "24 hours",
            "phases": [
                {
                    "name": "Network Discovery",
                    "order": 1,
                    "description": "Network mapping and host discovery",
                    "steps": [
                        {
                            "order": 1,
                            "action": "Host discovery",
                            "tool": "nmap",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"scan_type": "ping", "timing": "T3"},
                            "expected_outcome": "Live hosts",
                            "risk_level": "low"
                        },
                        {
                            "order": 2,
                            "action": "Port scanning",
                            "tool": "nmap",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"ports": "1-65535", "scan_type": "SYN", "timing": "T4"},
                            "expected_outcome": "Open ports and services",
                            "risk_level": "low"
                        },
                        {
                            "order": 3,
                            "action": "Service enumeration",
                            "tool": "nmap",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"scripts": "default,vuln", "version_detection": True},
                            "expected_outcome": "Service versions and vulnerabilities",
                            "risk_level": "low"
                        }
                    ]
                },
                {
                    "name": "Vulnerability Assessment",
                    "order": 2,
                    "description": "Identify network vulnerabilities",
                    "steps": [
                        {
                            "order": 1,
                            "action": "Vulnerability scan",
                            "tool": "openvas",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"config": "full_and_deep"},
                            "expected_outcome": "Network vulnerabilities",
                            "risk_level": "medium"
                        },
                        {
                            "order": 2,
                            "action": "SMB enumeration",
                            "tool": "enum4linux",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"all": True},
                            "expected_outcome": "SMB configuration issues",
                            "risk_level": "low"
                        }
                    ]
                },
                {
                    "name": "Exploitation",
                    "order": 3,
                    "description": "Controlled exploitation attempts",
                    "steps": [
                        {
                            "order": 1,
                            "action": "Exploit known vulnerabilities",
                            "tool": "metasploit",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"mode": "check_only"},
                            "expected_outcome": "Exploitable vulnerabilities",
                            "risk_level": "high"
                        }
                    ]
                }
            ],
            "approval_required": True
        }
    
    def _get_mobile_template(self) -> Dict[str, Any]:
        """Template for mobile application testing."""
        return {
            "name": "Mobile Application Security Test",
            "description": "Mobile app security assessment",
            "risk_level": "low",
            "estimated_duration": "12 hours",
            "phases": [
                {
                    "name": "Static Analysis",
                    "order": 1,
                    "description": "Static code and binary analysis",
                    "steps": [
                        {
                            "order": 1,
                            "action": "APK/IPA analysis",
                            "tool": "mobsf",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"scan_type": "static"},
                            "expected_outcome": "Static vulnerabilities",
                            "risk_level": "low"
                        }
                    ]
                },
                {
                    "name": "Dynamic Analysis",
                    "order": 2,
                    "description": "Runtime security testing",
                    "steps": [
                        {
                            "order": 1,
                            "action": "Dynamic testing",
                            "tool": "mobsf",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"scan_type": "dynamic"},
                            "expected_outcome": "Runtime vulnerabilities",
                            "risk_level": "medium"
                        }
                    ]
                }
            ],
            "approval_required": False
        }
    
    def _get_cloud_template(self) -> Dict[str, Any]:
        """Template for cloud infrastructure testing."""
        return {
            "name": "Cloud Security Assessment",
            "description": "Cloud infrastructure and configuration review",
            "risk_level": "medium",
            "estimated_duration": "20 hours",
            "phases": [
                {
                    "name": "Cloud Configuration Review",
                    "order": 1,
                    "description": "Review cloud service configurations",
                    "steps": [
                        {
                            "order": 1,
                            "action": "AWS configuration scan",
                            "tool": "prowler",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"checks": "all", "region": "all"},
                            "expected_outcome": "Configuration issues",
                            "risk_level": "low"
                        },
                        {
                            "order": 2,
                            "action": "S3 bucket analysis",
                            "tool": "s3scanner",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"enumerate": True},
                            "expected_outcome": "S3 misconfigurations",
                            "risk_level": "medium"
                        }
                    ]
                }
            ],
            "approval_required": True
        }
    
    def _get_api_template(self) -> Dict[str, Any]:
        """Template for API testing."""
        return {
            "name": "API Security Test",
            "description": "REST/GraphQL API security assessment",
            "risk_level": "medium",
            "estimated_duration": "8 hours",
            "phases": [
                {
                    "name": "API Discovery",
                    "order": 1,
                    "description": "API endpoint discovery and documentation",
                    "steps": [
                        {
                            "order": 1,
                            "action": "API endpoint discovery",
                            "tool": "postman",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"method": "automated"},
                            "expected_outcome": "API endpoints",
                            "risk_level": "low"
                        }
                    ]
                },
                {
                    "name": "API Testing",
                    "order": 2,
                    "description": "API security testing",
                    "steps": [
                        {
                            "order": 1,
                            "action": "API fuzzing",
                            "tool": "ffuf",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"wordlist": "api_endpoints.txt"},
                            "expected_outcome": "API vulnerabilities",
                            "risk_level": "medium"
                        }
                    ]
                }
            ],
            "approval_required": False
        }
    
    def _get_general_template(self) -> Dict[str, Any]:
        """Generic template for general assessments."""
        return {
            "name": "Security Assessment",
            "description": "General security assessment",
            "risk_level": "low",
            "estimated_duration": "8 hours",
            "phases": [
                {
                    "name": "Information Gathering",
                    "order": 1,
                    "description": "Initial reconnaissance",
                    "steps": [
                        {
                            "order": 1,
                            "action": "Basic scanning",
                            "tool": "nmap",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {"scan_type": "quick"},
                            "expected_outcome": "Basic information",
                            "risk_level": "low"
                        }
                    ]
                },
                {
                    "name": "Assessment",
                    "order": 2,
                    "description": "Security assessment",
                    "steps": [
                        {
                            "order": 1,
                            "action": "Vulnerability scan",
                            "tool": "generic_scanner",
                            "target": "TARGET_PLACEHOLDER",
                            "parameters": {},
                            "expected_outcome": "Security findings",
                            "risk_level": "medium"
                        }
                    ]
                }
            ],
            "approval_required": False
        }