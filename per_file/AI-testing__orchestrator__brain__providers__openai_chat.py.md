# File: AI-testing/orchestrator/brain/providers/openai_chat.py

- Size: 11734 bytes
- Kind: text
- SHA256: 50d74f3f155e05bd26799ef2dbafafac2229007a308570396e86fa338b213690

## Python Imports

```
base, json, logging, openai, os, typing
```

## Head (first 60 lines)

```
"""
OpenAI ChatGPT provider for AI Brain planning
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from .base import BaseBrainProvider, PlanResult

logger = logging.getLogger(__name__)

class OpenAIBrainProvider(BaseBrainProvider):
    """OpenAI GPT-based brain provider"""
    
    def __init__(self):
        super().__init__()
        self.name = "openai"
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
        self.base_url = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.client = None
        
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
    
    def is_available(self) -> bool:
        """Check if provider is configured and available"""
        return self.client is not None
    
    def generate_plan(
        self,
        engagement: Dict[str, Any],
        catalog: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> PlanResult:
        """Generate test plan using OpenAI"""
        
        if not self.is_available():
            return PlanResult(
                success=False,
                error="OpenAI provider not configured"
            )
        
        try:
            # Build the prompt
            prompt = self._build_planning_prompt(engagement, catalog, context)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert penetration testing planner. 
                        Generate comprehensive test plans based on engagement parameters.
                        Always return valid JSON with a 'tests' array containing test IDs from the catalog.
```

## Tail (last 60 lines)

```
        
        prompt += """
Generate a comprehensive test plan as JSON with this structure:
{
    "tests": [
        {
            "id": "test_id_from_catalog",
            "params": {"any": "needed parameters"},
            "approval_required": true/false,
            "priority": "critical/high/medium/low"
        }
    ],
    "reasoning": "explanation of the plan"
}

Consider:
1. Start with reconnaissance and discovery
2. Progress to vulnerability identification
3. Include exploitation only if appropriate
4. Mark intrusive tests as requiring approval
5. Ensure logical test progression
"""
        
        if context:
            prompt += f"\nAdditional context: {json.dumps(context, indent=2)}"
        
        return prompt
    
    def _filter_relevant_tests(
        self,
        engagement_type: str,
        catalog: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Filter catalog tests relevant to engagement type"""
        
        relevant = {}
        tests = catalog.get('tests', {})
        
        # Map engagement types to test categories
        type_mapping = {
            'web': ['web', 'api', 'authentication'],
            'network': ['network', 'infrastructure', 'service'],
            'mobile': ['mobile', 'api'],
            'cloud': ['cloud', 'infrastructure'],
            'code': ['code', 'static_analysis'],
            'internal': ['network', 'infrastructure', 'privilege_escalation', 'lateral_movement'],
            'external': ['web', 'network', 'discovery']
        }
        
        relevant_categories = type_mapping.get(engagement_type, [])
        
        for test_id, test_info in tests.items():
            category = test_info.get('category', '').lower()
            if any(cat in category for cat in relevant_categories):
                relevant[test_id] = test_info
            # Also include if engagement type in test tags
            elif engagement_type in test_info.get('tags', []):
                relevant[test_id] = test_info
        
        return relevant
```

