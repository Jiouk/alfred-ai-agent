"""
IntegrationRegistry - Plugin-style integrations
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseIntegration(ABC):
    """Base class for all integrations"""
    
    name: str
    setup_flow: str
    
    @abstractmethod
    async def execute(self, action: str, params: Dict) -> Any:
        """Execute integration action"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if integration is working"""
        pass


class IntegrationRegistry:
    """Registry of all available integrations"""
    
    _integrations: Dict[str, BaseIntegration] = {}
    
    @classmethod
    def register(cls, name: str, integration: BaseIntegration):
        """Register an integration"""
        cls._integrations[name] = integration
    
    @classmethod
    def get(cls, name: str) -> Optional[BaseIntegration]:
        """Get integration by name"""
        return cls._integrations.get(name)
    
    @classmethod
    def list_integrations(cls) -> list:
        """List all registered integrations"""
        return list(cls._integrations.keys())
