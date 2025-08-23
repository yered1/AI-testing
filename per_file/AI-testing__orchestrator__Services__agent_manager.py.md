# File: AI-testing/orchestrator/Services/agent_manager.py

- Size: 2201 bytes
- Kind: text
- SHA256: bd5386ec13bfea1ad020a3a8b1e16ee12dc29a041324c3281e6675813bbff265

## Python Imports

```
datetime, logging, models, typing
```

## Head (first 60 lines)

```
"""Agent management service"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from models import get_db, Agent, AgentStatus, AgentType

logger = logging.getLogger(__name__)

class AgentManager:
    """Manage agent lifecycle and health"""
    
    def __init__(self):
        self.health_check_interval = 60  # seconds
        self.offline_threshold = 180  # seconds
    
    async def get_available_agents(self, agent_type: Optional[AgentType] = None) -> List[Agent]:
        """Get list of available agents"""
        with get_db() as db:
            query = db.query(Agent).filter(
                Agent.status == AgentStatus.ONLINE,
                Agent.is_active == True
            )
            
            if agent_type:
                query = query.filter(Agent.type == agent_type)
            
            return query.all()
    
    async def check_agent_health(self):
        """Check health of all agents"""
        with get_db() as db:
            threshold = datetime.utcnow() - timedelta(seconds=self.offline_threshold)
            
            # Mark offline agents
            offline_agents = db.query(Agent).filter(
                Agent.status == AgentStatus.ONLINE,
                Agent.last_heartbeat < threshold
            ).all()
            
            for agent in offline_agents:
                logger.warning(f"Agent {agent.name} marked offline")
                agent.status = AgentStatus.OFFLINE
            
            db.commit()
    
    async def assign_job_to_agent(self, job_id: str, agent_type: AgentType) -> Optional[str]:
        """Assign job to best available agent"""
        agents = await self.get_available_agents(agent_type)
        
        if not agents:
            logger.warning(f"No available agents of type {agent_type}")
            return None
        
        # Simple round-robin for now
        # Could implement more sophisticated load balancing
        agent = agents[0]
        
        with get_db() as db:
```

## Tail (last 60 lines)

```

from models import get_db, Agent, AgentStatus, AgentType

logger = logging.getLogger(__name__)

class AgentManager:
    """Manage agent lifecycle and health"""
    
    def __init__(self):
        self.health_check_interval = 60  # seconds
        self.offline_threshold = 180  # seconds
    
    async def get_available_agents(self, agent_type: Optional[AgentType] = None) -> List[Agent]:
        """Get list of available agents"""
        with get_db() as db:
            query = db.query(Agent).filter(
                Agent.status == AgentStatus.ONLINE,
                Agent.is_active == True
            )
            
            if agent_type:
                query = query.filter(Agent.type == agent_type)
            
            return query.all()
    
    async def check_agent_health(self):
        """Check health of all agents"""
        with get_db() as db:
            threshold = datetime.utcnow() - timedelta(seconds=self.offline_threshold)
            
            # Mark offline agents
            offline_agents = db.query(Agent).filter(
                Agent.status == AgentStatus.ONLINE,
                Agent.last_heartbeat < threshold
            ).all()
            
            for agent in offline_agents:
                logger.warning(f"Agent {agent.name} marked offline")
                agent.status = AgentStatus.OFFLINE
            
            db.commit()
    
    async def assign_job_to_agent(self, job_id: str, agent_type: AgentType) -> Optional[str]:
        """Assign job to best available agent"""
        agents = await self.get_available_agents(agent_type)
        
        if not agents:
            logger.warning(f"No available agents of type {agent_type}")
            return None
        
        # Simple round-robin for now
        # Could implement more sophisticated load balancing
        agent = agents[0]
        
        with get_db() as db:
            agent_db = db.query(Agent).filter(Agent.id == agent.id).first()
            agent_db.status = AgentStatus.BUSY
            db.commit()
        
        return agent.id
```

