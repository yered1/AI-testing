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
                ]
            )
            
            # Extract JSON from response
            response_text = message.content[0].text
            
            # Parse JSON response
            try:
                # Try to extract JSON if wrapped in markdown
                if '```json' in response_text:
                    json_start = response_text.find('```json') + 7
                    json_end = response_text.find('```', json_start)
                    response_text = response_text[json_start:json_end]
                elif '```' in response_text:
                    json_start = response_text.find('```') + 3
                    json_end = response_text.find('```', json_start)
                    response_text = response_text[json_start:json_end]
                
                plan_data = json.loads(response_text.strip())
            except json.JSONDecodeError:
                # Try to extract JSON object pattern
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    plan_data = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse JSON from response")
            
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
            
            # Get reasoning
            reasoning = plan_data.get('reasoning', 'Plan generated based on engagement parameters and security best practices')
            
            return PlanResult(
                success=True,
                tests=tests,
                risk_tier=risk_tier,
                reasoning=reasoning,
                metadata={
                    'provider': 'anthropic',
                    'model': self.model,
                    'total_tests': len(tests)
                }
            )
            
        except Exception as e:
            logger.error(f"Anthropic planning failed: {e}")
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
            return {'error': 'Anthropic provider not configured'}
        
        try:
            # Build findings summary
            findings_summary = self._summarize_findings(findings)
            
            prompt = f"""Analyze these penetration test findings and provide a comprehensive security assessment.

Findings Summary:
{json.dumps(findings_summary, indent=2)}

Total Findings: {len(findings)}
Critical: {findings_summary.get('critical_count', 0)}
High: {findings_summary.get('high_count', 0)}
Medium: {findings_summary.get('medium_count', 0)}

Please provide:
1. Executive Summary (2-3 paragraphs suitable for C-level executives)
2. Technical Risk Assessment with business impact analysis
3. Prioritized Remediation Roadmap with quick wins and long-term improvements
4. Attack Chain Analysis showing how findings could be combined
5. Security Posture Rating (Critical/High/Medium/Low) with justification"""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.5,
                system="You are a senior security consultant preparing an executive security assessment report. Be thorough but concise, focusing on business impact and actionable recommendations.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            analysis = message.content[0].text
            
            # Parse structured sections
            sections = self._parse_analysis_sections(analysis)
            
            return {
                'success': True,
                'analysis': analysis,
                'sections': sections,
                'provider': 'anthropic',
                'model': self.model
            }
            
        except Exception as e:
            logger.error(f"Anthropic enrichment failed: {e}")
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
            
            # Focus on high-value findings for context
            critical_findings = [f for f in current_findings if f.get('severity') in ['critical', 'high']][:5]
            
            prompt = f"""Based on the current penetration test findings, suggest the next most valuable tests to run.

Key Findings:
{json.dumps(findings_summary, indent=2)}

Critical/High Findings Details:
{json.dumps([{'title': f.get('title'), 'category': f.get('category')} for f in critical_findings], indent=2)}

Completed Tests: {', '.join(completed_tests[:10])}

Available Tests (sample): {', '.join(available_tests[:30])}

Provide your response as JSON with this structure:
{{
    "suggestions": [
        {{
            "test_id": "exact_test_id_from_available_list",
            "reasoning": "why this test is valuable given current findings",
            "priority": "critical/high/medium/low",
            "expected_value": "what we might discover"
        }}
    ]
}}

Focus on:
1. Tests that could chain with existing findings for privilege escalation
2. Tests that explore identified attack surfaces deeper
3. Tests that verify the exploitability of found vulnerabilities
4. Lateral movement opportunities if internal access is indicated

Return only valid JSON."""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.7,
                system="You are a penetration testing expert planning the next phase of testing based on current findings. Focus on high-impact, logical next steps.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = message.content[0].text
            
            # Parse JSON response
            try:
                if '```json' in response_text:
                    json_start = response_text.find('```json') + 7
                    json_end = response_text.find('```', json_start)
                    response_text = response_text[json_start:json_end]
                
                result = json.loads(response_text.strip())
            except:
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    return []
            
            suggestions = []
            for suggestion in result.get('suggestions', []):
                if isinstance(suggestion, dict):
                    test_id = suggestion.get('test_id')
                    if test_id and test_id in available_tests:
                        suggestions.append({
                            'test_id': test_id,
                            'reasoning': suggestion.get('reasoning', ''),
                            'priority': suggestion.get('priority', 'medium'),
                            'expected_value': suggestion.get('expected_value', '')
                        })
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Anthropic suggestions failed: {e}")
            return []
    
    def analyze_attack_chains(
        self,
        findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze potential attack chains from findings"""
        
        if not self.is_available():
            return []
        
        try:
            # Prepare findings for analysis
            findings_data = [
                {
                    'title': f.get('title'),
                    'severity': f.get('severity'),
                    'category': f.get('category'),
                    'affected_hosts': f.get('affected_hosts', []),
                    'affected_urls': f.get('affected_urls', [])
                }
                for f in findings[:20]  # Limit to prevent token overflow
            ]
            
            prompt = f"""Analyze these security findings and identify potential attack chains.

Findings:
{json.dumps(findings_data, indent=2)}

Identify attack chains where multiple findings can be combined to achieve higher impact.
Focus on realistic scenarios that could lead to:
- Full system compromise
- Data exfiltration
- Privilege escalation
- Lateral movement

Provide response as JSON:
{{
    "attack_chains": [
        {{
            "name": "descriptive name",
            "risk_level": "critical/high/medium",
            "findings_used": ["finding titles used in chain"],
            "description": "how the attack would work",
            "impact": "business impact if successful",
            "likelihood": "high/medium/low",
            "mitigation_priority": "which finding to fix first"
        }}
    ]
}}"""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.6,
                system="You are a security expert analyzing attack chains. Focus on realistic, high-impact scenarios.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = message.content[0].text
            
            # Parse response
            try:
                if '```json' in response_text:
                    json_start = response_text.find('```json') + 7
                    json_end = response_text.find('```', json_start)
                    response_text = response_text[json_start:json_end]
                
                result = json.loads(response_text.strip())
                return result.get('attack_chains', [])
            except:
                return []
                
        except Exception as e:
            logger.error(f"Attack chain analysis failed: {e}")
            return []
    
    def _build_planning_prompt(
        self,
        engagement: Dict[str, Any],
        catalog: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build the planning prompt for Claude"""
        
        engagement_type = engagement.get('type', 'external')
        scope = engagement.get('scope', {})
        targets = scope.get('targets', [])
        
        # Get relevant tests
        relevant_tests = self._filter_relevant_tests(engagement_type, catalog)
        
        prompt = f"""Create a comprehensive penetration testing plan.

ENGAGEMENT DETAILS:
Type: {engagement_type}
Targets: {json.dumps(targets, indent=2)}

AVAILABLE TESTS:
"""
        
        # Group tests by category
        tests_by_category = {}
        for test_id, test_info in relevant_tests.items():
            category = test_info.get('category', 'Other')
            if category not in tests_by_category:
                tests_by_category[category] = []
            tests_by_category[category].append(f"{test_id}: {test_info.get('description', test_id)}")
        
        for category, tests in tests_by_category.items():
            prompt += f"\n{category}:\n"
            for test in tests[:10]:  # Limit per category to manage tokens
                prompt += f"  - {test}\n"
        
        prompt += """
REQUIREMENTS:
Generate a JSON test plan with this exact structure:
{
    "tests": [
        {
            "id": "exact_test_id_from_catalog",
            "params": {},
            "approval_required": boolean,
            "priority": "critical|high|medium|low"
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