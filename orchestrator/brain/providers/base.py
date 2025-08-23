from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseProvider(ABC):
    name = "base"

    @abstractmethod
    def plan(self, scope: Dict[str, Any], engagement_type: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Return {selected_tests: [ids], params: {test_id: {}}, explanation: str} """
        ...

    def enrich(self, scope: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        """Optionally add params based on scope; default is passthrough"""
        return plan
