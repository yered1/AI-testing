# Destination: patches/v2.0.0/orchestrator/brain/providers/openai_chat.py
# Rationale: Implement OpenAI provider for automated test planning
# Uses environment variables for configuration and safety

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class PlanStep:
    """Represents a single step in the test plan."""
    order: int
    action: str
    tool: str
    target: str
    parameters: Dict[str, Any]
    expected_outcome: str
    risk_level: str = "low"


class OpenAIProvider:
    """OpenAI provider for generating test plans."""
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4")
        self.enabled = bool(self.api_key)
        self.max_tokens = int(os.environ.get("OPENAI_MAX_TOKENS", "2000"))
        self.temperature = float(os.environ.get("OPENAI_TEMPERATURE", "0.7"))
        
        if not self.enabled:
            logger.warning("OpenAI provider disabled - no API key found")
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        return self.enabled
    
    async def generate_plan(self, 
                           engagement_data: Dict[str, Any],
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a test plan based on engagement data."""
        if not self.enabled:
            raise RuntimeError("OpenAI provider is not configured")
        
        try:
            import openai
            from openai import AsyncOpenAI
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")
        
        client = AsyncOpenAI(api_key=self.api_key)
        
        # Build the prompt
        prompt = self._build_prompt(engagement_data, context)
        
        try:
            # Call OpenAI API
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            plan_json = json.loads(response.choices[0].message.content)
            
            # Validate and enhance the plan
            plan = self._validate_plan(plan_json, engagement_data)
            
            return plan
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise RuntimeError(f"Failed to generate plan: {str(e)}")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for plan generation."""
        return """You are an expert security testing orchestrator. Generate comprehensive test plans 
        for security assessments. Your plans should be:
        1. Methodical and risk-aware (start with reconnaissance, escalate carefully)
        2. Tool-specific (use appropriate tools for each task)
        3. Measurable (clear success criteria)
        4. Safe (respect scope boundaries, avoid destructive actions)
        
        Output valid JSON with this structure:
        {
            "name": "Plan name",
            "description": "Plan description",
            "risk_level": "low|medium|high",
            "estimated_duration": "duration in hours",
            "phases": [
                {
                    "name": "Phase name",
                    "order": 1,
                    "steps": [
                        {
                            "order": 1,
                            "action": "What to do",
                            "tool": "Tool to use",
                            "target": "Target system/URL",
                            "parameters": {"key": "value"},
                            "expected_outcome": "What we expect",
                            "risk_level": "low|medium|high"
                        }
                    ]
                }
            ],
            "dependencies": ["required tools/agents"],
            "approval_required": true/false
        }"""
    
    def _build_prompt(self, engagement_data: Dict[str, Any], context: Dict[str, Any] = None) -> str:
        """Build the prompt for plan generation."""
        scope = engagement_data.get("scope", {})
        
        prompt = f"""Generate a security test plan for the following engagement:
        
        Engagement: {engagement_data.get('name', 'Security Assessment')}
        Description: {engagement_data.get('description', 'N/A')}
        
        Scope:
        - Targets: {json.dumps(scope.get('targets', []), indent=2)}
        - Included: {json.dumps(scope.get('included', []), indent=2)}
        - Excluded: {json.dumps(scope.get('excluded', []), indent=2)}
        - Constraints: {json.dumps(scope.get('constraints', {}), indent=2)}
        """
        
        if context:
            prompt += f"\n\nAdditional Context:\n{json.dumps(context, indent=2)}"
        
        prompt += "\n\nGenerate a comprehensive test plan following security best practices."
        
        return prompt
    
    def _validate_plan(self, plan_json: Dict[str, Any], engagement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the generated plan."""
        # Ensure required fields
        plan_json.setdefault("name", f"Auto-generated plan for {engagement_data.get('name', 'engagement')}")
        plan_json.setdefault("created_at", datetime.utcnow().isoformat())
        plan_json.setdefault("provider", "openai")
        plan_json.setdefault("model", self.model)
        
        # Validate phases
        if "phases" not in plan_json:
            plan_json["phases"] = [self._get_default_phase()]
        
        # Ensure phase ordering
        for i, phase in enumerate(plan_json["phases"]):
            phase.setdefault("order", i + 1)
            
            # Ensure step ordering
            for j, step in enumerate(phase.get("steps", [])):
                step.setdefault("order", j + 1)
                step.setdefault("risk_level", "low")
        
        # Add metadata
        plan_json["metadata"] = {
            "generator": "openai_provider",
            "version": "1.0.0",
            "engagement_id": engagement_data.get("id"),
            "created_by": "ai_brain"
        }
        
        return plan_json
    
    def _get_default_phase(self) -> Dict[str, Any]:
        """Get a default phase if none provided."""
        return {
            "name": "Reconnaissance",
            "order": 1,
            "steps": [
                {
                    "order": 1,
                    "action": "Perform port scan",
                    "tool": "nmap",
                    "target": "target_host",
                    "parameters": {
                        "ports": "1-65535",
                        "scan_type": "SYN"
                    },
                    "expected_outcome": "List of open ports and services",
                    "risk_level": "low"
                }
            ]
        }