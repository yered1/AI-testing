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
                        Include 'approval_required' boolean for intrusive tests.
                        Be thorough but avoid redundancy."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result_text = response.choices[0].message.content
            plan_data = json.loads(result_text)
            
            # Validate and structure the plan
            tests = []
            for test_entry in plan_data.get('tests', []):
                if isinstance(test_entry, str):
                    test_id = test_entry
                    params = {}
                    approval = False
                elif isinstance(test_entry, dict):
                    test_id = test_entry.get('id')
                    params = test_entry.get('params', {})
                    approval = test_entry.get('approval_required', False)
                else:
                    continue
                
                # Verify test exists in catalog
                if self._test_exists_in_catalog(test_id, catalog):
                    tests.append({
                        'test_id': test_id,
                        'params': params,
                        'approval_required': approval,
                        'priority': test_entry.get('priority', 'medium') if isinstance(test_entry, dict) else 'medium'
                    })
            
            # Calculate risk tier
            risk_tier = self._calculate_risk_tier(tests, catalog)
            
            # Get reasoning if provided
            reasoning = plan_data.get('reasoning', 'Plan generated based on engagement parameters and best practices')
            
            return PlanResult(
                success=True,
                tests=tests,
                risk_tier=risk_tier,
                reasoning=reasoning,
                metadata={
                    'provider': 'openai',
                    'model': self.model,
                    'total_tests': len(tests)
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI planning failed: {e}")
            return PlanResult(
                success=False,
                error=str(e)
            )
    
    def enrich_findings(
        self,
        findings: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Enrich findings with AI analysis"""
        
        if not self.is_available():
            return {'error': 'OpenAI provider not configured'}
        
        try:
            # Build findings summary
            findings_summary = self._summarize_findings(findings)
            
            prompt = f"""Analyze these penetration test findings and provide:
1. Executive summary (2-3 paragraphs)
2. Risk assessment and business impact
3. Prioritized remediation roadmap
4. Key attack vectors identified

Findings summary:
{json.dumps(findings_summary, indent=2)}

Context:
- Total findings: {len(findings)}
- Critical: {findings_summary.get('critical_count', 0)}
- High: {findings_summary.get('high_count', 0)}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior security analyst preparing an executive report."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=1500
            )
            
            analysis = response.choices[0].message.content
            
            # Try to extract structured sections
            sections = self._parse_analysis_sections(analysis)
            
            return {
                'success': True,
                'analysis': analysis,
                'sections': sections,
                'provider': 'openai',
                'model': self.model
            }
            
        except Exception as e:
            logger.error(f"OpenAI enrichment failed: {e}")
            return {'error': str(e)}
    
    def suggest_next_steps(
        self,
        current_findings: List[Dict[str, Any]],
        completed_tests: List[str],
        catalog: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest next tests based on current findings"""
        
        if not self.is_available():
            return []
        
        try:
            # Build context
            findings_summary = self._summarize_findings(current_findings)
            available_tests = self._get_available_tests(completed_tests, catalog)
            
            prompt = f"""Based on these findings, suggest the next most valuable tests to run.

Current findings:
{json.dumps(findings_summary, indent=2)}

Completed tests: {', '.join(completed_tests)}

Available tests: {', '.join(available_tests[:20])}

Return a JSON object with a 'suggestions' array containing test IDs and reasoning."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a penetration testing expert suggesting follow-up tests."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            suggestions = []
            
            for suggestion in result.get('suggestions', []):
                if isinstance(suggestion, dict):
                    test_id = suggestion.get('test_id')
                    if test_id and test_id in available_tests:
                        suggestions.append({
                            'test_id': test_id,
                            'reasoning': suggestion.get('reasoning', ''),
                            'priority': suggestion.get('priority', 'medium')
                        })
            
            return suggestions[:5]  # Limit to top 5 suggestions
            
        except Exception as e:
            logger.error(f"OpenAI suggestions failed: {e}")
            return []
    
    def _build_planning_prompt(
        self,
        engagement: Dict[str, Any],
        catalog: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build the planning prompt for OpenAI"""
        
        # Extract key information
        engagement_type = engagement.get('type', 'external')
        scope = engagement.get('scope', {})
        targets = scope.get('targets', [])
        
        # Get relevant tests from catalog
        relevant_tests = self._filter_relevant_tests(engagement_type, catalog)
        
        prompt = f"""Create a penetration testing plan for this engagement:

Engagement Type: {engagement_type}
Targets: {json.dumps(targets, indent=2)}

Available Tests (ID -> Description):
"""
        
        for test_id, test_info in relevant_tests.items():
            prompt += f"- {test_id}: {test_info.get('description', test_id)}\n"
        
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