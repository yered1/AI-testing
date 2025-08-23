# File: AI-testing/orchestrator/llm_controller.py

- Size: 28417 bytes
- Kind: text
- SHA256: 6edffa05ca19a01700f9533b81bf633ad28f135805edc623142421d8d65d6756

## Python Imports

```
aiohttp, anthropic, argparse, asyncio, datetime, enum, json, logging, openai, os, pydantic, typing
```

## Head (first 60 lines)

```
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
```

## Tail (last 60 lines)

```
    
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
```

