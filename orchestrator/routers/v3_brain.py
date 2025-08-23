# Destination: patches/v2.0.0/orchestrator/routers/v3_brain.py
# Rationale: Implement AI brain endpoints for automated test plan generation
# Provides /autoplan endpoint and provider management

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import os

# Import providers
from orchestrator.brain.providers.openai_chat import OpenAIProvider
from orchestrator.brain.providers.anthropic import AnthropicProvider
from orchestrator.brain.providers.heuristic import HeuristicProvider

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v3/brain",
    tags=["brain", "ai", "planning"]
)

# Request/Response models
class AutoPlanRequest(BaseModel):
    """Request model for auto-plan generation."""
    engagement_id: str
    engagement_data: Dict[str, Any]
    provider: Optional[str] = Field(default=None, description="Specific provider to use")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Provider-specific options")

class AutoPlanResponse(BaseModel):
    """Response model for auto-plan generation."""
    success: bool
    plan: Optional[Dict[str, Any]]
    provider_used: str
    generation_time: float
    message: Optional[str]
    error: Optional[str]

class ProviderInfo(BaseModel):
    """Information about an AI provider."""
    name: str
    available: bool
    model: Optional[str]
    capabilities: List[str]

# Provider management
class BrainManager:
    """Manages AI providers for plan generation."""
    
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "heuristic": HeuristicProvider()
        }
        self.default_provider = os.environ.get("DEFAULT_AI_PROVIDER", "heuristic")
    
    async def generate_plan(self, 
                           engagement_data: Dict[str, Any],
                           provider: Optional[str] = None,
                           context: Optional[Dict[str, Any]] = None) -> tuple[Dict[str, Any], str]:
        """Generate a plan using available providers."""
        
        # Determine which provider to use
        if provider and provider in self.providers:
            selected_provider = provider
        else:
            selected_provider = self._select_best_provider()
        
        # Get the provider instance
        provider_instance = self.providers[selected_provider]
        
        # Check if provider is available
        if not provider_instance.is_available():
            # Fallback to heuristic provider
            logger.warning(f"Provider {selected_provider} not available, falling back to heuristic")
            selected_provider = "heuristic"
            provider_instance = self.providers[selected_provider]
        
        # Generate the plan
        plan = await provider_instance.generate_plan(engagement_data, context)
        
        return plan, selected_provider
    
    def _select_best_provider(self) -> str:
        """Select the best available provider."""
        # Priority order
        priority = ["openai", "anthropic", "heuristic"]
        
        # Check default provider first
        if self.default_provider in self.providers:
            if self.providers[self.default_provider].is_available():
                return self.default_provider
        
        # Check providers in priority order
        for provider_name in priority:
            if provider_name in self.providers:
                if self.providers[provider_name].is_available():
                    return provider_name
        
        # Fallback to heuristic (always available)
        return "heuristic"
    
    def get_provider_info(self) -> List[ProviderInfo]:
        """Get information about all providers."""
        info = []
        for name, provider in self.providers.items():
            capabilities = []
            
            if name == "openai":
                capabilities = ["advanced_reasoning", "code_generation", "multi_phase_planning"]
                model = os.environ.get("OPENAI_MODEL", "gpt-4")
            elif name == "anthropic":
                capabilities = ["detailed_analysis", "security_focus", "comprehensive_planning"]
                model = os.environ.get("ANTHROPIC_MODEL", "claude-3")
            else:
                capabilities = ["basic_planning", "rule_based", "fast_generation"]
                model = "heuristic-v1"
            
            info.append(ProviderInfo(
                name=name,
                available=provider.is_available(),
                model=model if provider.is_available() else None,
                capabilities=capabilities
            ))
        
        return info

# Initialize brain manager
brain_manager = BrainManager()

# Endpoints
@router.post("/autoplan", response_model=AutoPlanResponse)
async def generate_auto_plan(request: AutoPlanRequest):
    """Generate an automated test plan using AI providers."""
    start_time = datetime.utcnow()
    
    try:
        # Generate the plan
        plan, provider_used = await brain_manager.generate_plan(
            engagement_data=request.engagement_data,
            provider=request.provider,
            context=request.context
        )
        
        # Calculate generation time
        generation_time = (datetime.utcnow() - start_time).total_seconds()
        
        return AutoPlanResponse(
            success=True,
            plan=plan,
            provider_used=provider_used,
            generation_time=generation_time,
            message=f"Plan generated successfully using {provider_used}"
        )
        
    except Exception as e:
        logger.error(f"Failed to generate auto plan: {str(e)}")
        generation_time = (datetime.utcnow() - start_time).total_seconds()
        
        return AutoPlanResponse(
            success=False,
            plan=None,
            provider_used="none",
            generation_time=generation_time,
            error=str(e)
        )

@router.get("/providers", response_model=List[ProviderInfo])
async def list_providers():
    """List available AI providers and their status."""
    return brain_manager.get_provider_info()

@router.get("/providers/{provider_name}")
async def get_provider_details(provider_name: str):
    """Get detailed information about a specific provider."""
    if provider_name not in brain_manager.providers:
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
    
    provider = brain_manager.providers[provider_name]
    
    # Build detailed response
    details = {
        "name": provider_name,
        "available": provider.is_available(),
        "configuration": {}
    }
    
    if provider_name == "openai":
        details["configuration"] = {
            "model": os.environ.get("OPENAI_MODEL", "gpt-4"),
            "max_tokens": os.environ.get("OPENAI_MAX_TOKENS", "2000"),
            "temperature": os.environ.get("OPENAI_TEMPERATURE", "0.7"),
            "api_key_set": bool(os.environ.get("OPENAI_API_KEY"))
        }
    elif provider_name == "anthropic":
        details["configuration"] = {
            "model": os.environ.get("ANTHROPIC_MODEL", "claude-3"),
            "max_tokens": os.environ.get("ANTHROPIC_MAX_TOKENS", "4000"),
            "api_key_set": bool(os.environ.get("ANTHROPIC_API_KEY"))
        }
    else:
        details["configuration"] = {
            "version": "1.0.0",
            "mode": "rule_based"
        }
    
    return details

@router.post("/validate-plan")
async def validate_plan(plan: Dict[str, Any]):
    """Validate a generated or manual plan."""
    errors = []
    warnings = []
    
    # Check required fields
    required_fields = ["name", "phases"]
    for field in required_fields:
        if field not in plan:
            errors.append(f"Missing required field: {field}")
    
    # Validate phases
    if "phases" in plan:
        if not isinstance(plan["phases"], list):
            errors.append("Phases must be a list")
        elif len(plan["phases"]) == 0:
            warnings.append("Plan has no phases")
        else:
            for i, phase in enumerate(plan["phases"]):
                if "name" not in phase:
                    errors.append(f"Phase {i} missing name")
                if "steps" not in phase or not phase["steps"]:
                    warnings.append(f"Phase {i} has no steps")
    
    # Check for high-risk operations
    if "phases" in plan:
        for phase in plan.get("phases", []):
            for step in phase.get("steps", []):
                if step.get("risk_level") == "high":
                    warnings.append(f"High-risk operation: {step.get('action', 'unknown')}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "recommendation": "Plan is valid" if len(errors) == 0 else "Plan needs correction"
    }

@router.get("/health")
async def brain_health():
    """Check health of the brain service and providers."""
    providers_status = {}
    
    for name, provider in brain_manager.providers.items():
        providers_status[name] = {
            "available": provider.is_available(),
            "healthy": True  # Could add more health checks
        }
    
    any_available = any(p["available"] for p in providers_status.values())
    
    return {
        "status": "healthy" if any_available else "degraded",
        "providers": providers_status,
        "default_provider": brain_manager.default_provider,
        "timestamp": datetime.utcnow().isoformat()
    }