# Destination: patches/v2.0.0/orchestrator/brain/providers/anthropic.py
# Rationale: Implement Anthropic Claude provider for automated test planning
# Provides alternative LLM option with different capabilities

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AnthropicProvider:
    """Anthropic Claude provider for generating test plans."""
    
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.model = os.environ.get("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        self.enabled = bool(self.api_key)
        self.max_tokens = int(os.environ.get("ANTHROPIC_MAX_TOKENS", "4000"))
        
        if not self.enabled:
            logger.warning("Anthropic provider disabled - no API key found")
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        return self.enabled
    
    async def generate_plan(self, 
                           engagement_data: Dict[str, Any],
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a test plan based on engagement data."""
        if not self.enabled:
            raise RuntimeError("Anthropic provider is not configured")
        
        try:
            import anthropic
        except ImportError:
            raise RuntimeError("anthropic package not installed. Run: pip install anthropic")
        
        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
        # Build the prompt
        prompt = self._build_prompt(engagement_data, context)
        
        try:
            # Call Anthropic API
            response = await client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self._get_system_prompt(),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract JSON from response
            content = response.content[0].text
            
            # Try to extract JSON if wrapped in markdown
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            # Parse the response
            plan_json = json.loads(content)
            
            # Validate and enhance the plan
            plan = self._validate_plan(plan_json, engagement_data)
            
            return plan
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Anthropic response as JSON: {str(e)}")
            # Return a fallback plan
            return self._get_fallback_plan(engagement_data)
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise RuntimeError(f"Failed to generate plan: {str(e)}")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for plan generation."""
        return """You are an expert security testing orchestrator specializing in comprehensive security assessments.
        
        Your role is to generate detailed, methodical test plans that:
        1. Follow security testing best practices and methodologies (OWASP, NIST, etc.)
        2. Progress from low-risk reconnaissance to higher-risk testing
        3. Respect scope boundaries and avoid destructive actions
        4. Use appropriate tools for each testing phase
        5. Include clear success criteria and risk assessments
        
        Always output valid JSON following the specified structure. Be thorough but practical.
        Consider both automated and manual testing approaches where appropriate."""
    
    def _build_prompt(self, engagement_data: Dict[str, Any], context: Dict[str, Any] = None) -> str:
        """Build the prompt for plan generation."""
        scope = engagement_data.get("scope", {})
        
        prompt = f"""Create a comprehensive security test plan for this engagement.

ENGAGEMENT DETAILS:
- Name: {engagement_data.get('name', 'Security Assessment')}
- Description: {engagement_data.get('description', 'Comprehensive security testing')}
- Type: {engagement_data.get('engagement_type', 'penetration_test')}

SCOPE:
- Target Systems: {json.dumps(scope.get('targets', []), indent=2)}
- In Scope: {json.dumps(scope.get('included', ['All standard security tests']), indent=2)}
- Out of Scope: {json.dumps(scope.get('excluded', ['Production data modification']), indent=2)}
- Constraints: {json.dumps(scope.get('constraints', {'testing_window': 'business_hours'}), indent=2)}

REQUIREMENTS:
1. Start with reconnaissance and information gathering
2. Progress through vulnerability identification
3. Include exploitation attempts (within scope)
4. Document all findings thoroughly
5. Generate comprehensive reports

OUTPUT FORMAT:
Generate a JSON test plan with this exact structure:
{{
    "name": "Descriptive plan name",
    "description": "Detailed plan description",
    "risk_level": "low|medium|high",
    "estimated_duration": "X hours",
    "phases": [
        {{
            "name": "Phase name",
            "order": 1,
            "description": "Phase description",
            "steps": [
                {{
                    "order": 1,
                    "action": "Specific action to perform",
                    "tool": "Tool/agent to use",
                    "target": "Target system or component",
                    "parameters": {{"param": "value"}},
                    "expected_outcome": "What we expect to find/achieve",
                    "risk_level": "low|medium|high",
                    "manual_review": false
                }}
            ]
        }}
    ],
    "dependencies": ["List of required tools/agents"],
    "approval_required": true,
    "notification_settings": {{
        "on_start": true,
        "on_completion": true,
        "on_critical_finding": true
    }}
}}"""
        
        if context:
            prompt += f"\n\nADDITIONAL CONTEXT:\n{json.dumps(context, indent=2)}"
        
        prompt += "\n\nGenerate the complete JSON test plan now:"
        
        return prompt
    
    def _validate_plan(self, plan_json: Dict[str, Any], engagement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the generated plan."""
        # Ensure required fields
        plan_json.setdefault("name", f"Security Test Plan - {engagement_data.get('name', 'Assessment')}")
        plan_json.setdefault("created_at", datetime.utcnow().isoformat())
        plan_json.setdefault("provider", "anthropic")
        plan_json.setdefault("model", self.model)
        plan_json.setdefault("approval_required", True)
        
        # Validate and enhance phases
        if "phases" not in plan_json or not plan_json["phases"]:
            plan_json["phases"] = self._get_default_phases()
        
        # Ensure proper ordering and structure
        for i, phase in enumerate(plan_json["phases"]):
            phase.setdefault("order", i + 1)
            phase.setdefault("description", f"Phase {i + 1} of security testing")
            
            # Validate steps
            if "steps" not in phase or not phase["steps"]:
                phase["steps"] = [self._get_default_step(phase["name"])]
            
            for j, step in enumerate(phase["steps"]):
                step.setdefault("order", j + 1)
                step.setdefault("risk_level", "low")
                step.setdefault("manual_review", False)
                step.setdefault("parameters", {})
        
        # Add metadata
        plan_json["metadata"] = {
            "generator": "anthropic_provider",
            "version": "1.0.0",
            "engagement_id": engagement_data.get("id"),
            "created_by": "ai_brain",
            "model_used": self.model
        }
        
        # Ensure dependencies list
        if "dependencies" not in plan_json:
            plan_json["dependencies"] = self._extract_dependencies(plan_json)
        
        return plan_json
    
    def _get_default_phases(self) -> List[Dict[str, Any]]:
        """Get default testing phases."""
        return [
            {
                "name": "Reconnaissance",
                "order": 1,
                "description": "Information gathering and target enumeration",
                "steps": [
                    {
                        "order": 1,
                        "action": "Perform DNS enumeration",
                        "tool": "dnsenum",
                        "target": "target_domain",
                        "parameters": {"recursive": True},
                        "expected_outcome": "Subdomain list and DNS records",
                        "risk_level": "low"
                    },
                    {
                        "order": 2,
                        "action": "Port scanning",
                        "tool": "nmap",
                        "target": "target_network",
                        "parameters": {"scan_type": "SYN", "ports": "common"},
                        "expected_outcome": "Open ports and service identification",
                        "risk_level": "low"
                    }
                ]
            },
            {
                "name": "Vulnerability Assessment",
                "order": 2,
                "description": "Identify potential security vulnerabilities",
                "steps": [
                    {
                        "order": 1,
                        "action": "Web vulnerability scanning",
                        "tool": "nikto",
                        "target": "web_applications",
                        "parameters": {"thorough": True},
                        "expected_outcome": "List of web vulnerabilities",
                        "risk_level": "medium"
                    }
                ]
            }
        ]
    
    def _get_default_step(self, phase_name: str) -> Dict[str, Any]:
        """Get a default step for a phase."""
        return {
            "order": 1,
            "action": f"Perform {phase_name.lower()} analysis",
            "tool": "manual_review",
            "target": "specified_scope",
            "parameters": {},
            "expected_outcome": "Initial findings",
            "risk_level": "low",
            "manual_review": True
        }
    
    def _extract_dependencies(self, plan: Dict[str, Any]) -> List[str]:
        """Extract tool dependencies from the plan."""
        tools = set()
        for phase in plan.get("phases", []):
            for step in phase.get("steps", []):
                if "tool" in step:
                    tools.add(step["tool"])
        return sorted(list(tools))
    
    def _get_fallback_plan(self, engagement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a fallback plan if generation fails."""
        return {
            "name": f"Fallback Plan - {engagement_data.get('name', 'Assessment')}",
            "description": "Basic security assessment plan (fallback)",
            "risk_level": "low",
            "estimated_duration": "8 hours",
            "phases": self._get_default_phases(),
            "dependencies": ["nmap", "nikto", "dnsenum"],
            "approval_required": True,
            "created_at": datetime.utcnow().isoformat(),
            "provider": "anthropic",
            "model": self.model,
            "metadata": {
                "generator": "anthropic_provider",
                "version": "1.0.0",
                "is_fallback": True
            }
        }