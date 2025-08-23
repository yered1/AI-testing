# File: AI-testing/orchestrator/brain/providers/anthropic.py

- Size: 18222 bytes
- Kind: text
- SHA256: fde88ad13f032bf28ce35dfd4ffa70225663a7ab0a2382cbd5995590aa883662

## Python Imports

```
anthropic, base, json, logging, os, re, typing
```

## Head (first 60 lines)

```
"""
Anthropic Claude provider for AI Brain planning
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from .base import BaseBrainProvider, PlanResult

logger = logging.getLogger(__name__)

class AnthropicBrainProvider(BaseBrainProvider):
    """Anthropic Claude-based brain provider"""
    
    def __init__(self):
        super().__init__()
        self.name = "anthropic"
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.model = os.environ.get('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20240620')
        self.client = None
        
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
    
    def is_available(self) -> bool:
        """Check if provider is configured and available"""
        return self.client is not None
    
    def generate_plan(
        self,
        engagement: Dict[str, Any],
        catalog: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> PlanResult:
        """Generate test plan using Claude"""
        
        if not self.is_available():
            return PlanResult(
                success=False,
                error="Anthropic provider not configured"
            )
        
        try:
            # Build the prompt
            prompt = self._build_planning_prompt(engagement, catalog, context)
            
            # Call Anthropic API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                system="""You are an expert penetration testing planner with deep knowledge of security testing methodologies. 
                Generate comprehensive, risk-aware test plans that follow industry best practices.
                Always structure your response as valid JSON.""",
                messages=[
                    {
                        "role": "user",
                        "content": prompt + "\n\nRespond only with valid JSON, no other text."
                    }
```

## Tail (last 60 lines)

```
        }
    ],
    "reasoning": "explanation of plan logic"
}

PLANNING GUIDELINES:
1. Start with reconnaissance (discovery, enumeration)
2. Progress to vulnerability identification
3. Include targeted deep-dive tests based on discovered services
4. Mark ALL active/intrusive tests as approval_required=true
5. Ensure logical flow and dependencies
6. Prioritize based on likelihood of findings
7. Include both automated and manual test types where relevant"""
        
        if context:
            prompt += f"\n\nADDITIONAL CONTEXT:\n{json.dumps(context, indent=2)}"
        
        return prompt
    
    def _filter_relevant_tests(
        self,
        engagement_type: str,
        catalog: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Filter catalog tests relevant to engagement type"""
        
        relevant = {}
        tests = catalog.get('tests', {})
        
        # Enhanced mapping with more categories
        type_mapping = {
            'web': ['web', 'api', 'authentication', 'injection', 'xss', 'csrf'],
            'network': ['network', 'infrastructure', 'service', 'port', 'vulnerability'],
            'mobile': ['mobile', 'api', 'binary', 'reverse_engineering'],
            'cloud': ['cloud', 'infrastructure', 'configuration', 'iam', 's3'],
            'code': ['code', 'static_analysis', 'dependency', 'secrets'],
            'internal': ['network', 'infrastructure', 'privilege_escalation', 'lateral_movement', 'active_directory', 'credential'],
            'external': ['web', 'network', 'discovery', 'osint', 'reconnaissance'],
            'wireless': ['wireless', 'wifi', 'bluetooth', 'radio'],
            'physical': ['physical', 'badge', 'lock', 'social_engineering'],
            'red_team': ['exploitation', 'post_exploitation', 'persistence', 'c2', 'evasion']
        }
        
        relevant_categories = type_mapping.get(engagement_type, [])
        
        for test_id, test_info in tests.items():
            category = test_info.get('category', '').lower()
            tags = test_info.get('tags', [])
            
            # Check category match
            if any(cat in category for cat in relevant_categories):
                relevant[test_id] = test_info
            # Check tag match
            elif any(tag in tags for tag in relevant_categories):
                relevant[test_id] = test_info
            # Check engagement type in tags
            elif engagement_type in tags:
                relevant[test_id] = test_info
        
        return relevant
```

