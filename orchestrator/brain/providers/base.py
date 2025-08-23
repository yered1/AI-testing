from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    def plan(self, scope: Dict[str, Any], engagement_type: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def enrich(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"data": data, "explanation": f"{self.name} enrich: no-op"}

    def learn(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": True, "explanation": f"{self.name} learn: no-op"}
