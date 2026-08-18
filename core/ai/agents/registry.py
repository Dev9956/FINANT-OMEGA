"""FININT OMEGA — Workflow Agent Framework: agent registry."""

from __future__ import annotations

from typing import Any

from core.ai.agents.base import AgentConfig, AgentRole, BaseAgent


class AgentNotFoundError(Exception):
    """Raised when an agent is not found in the registry."""


class AgentRegistry:
    """Registry for managing agent instances and configurations."""

    def __init__(self) -> None:
        self._agents: dict[str, type[BaseAgent]] = {}
        self._configs: dict[str, AgentConfig] = {}
        self._instances: dict[str, BaseAgent] = {}

    def register(
        self,
        agent_id: str,
        agent_class: type[BaseAgent],
        config: AgentConfig | None = None,
    ) -> None:
        """Register an agent class with an optional config."""
        if not issubclass(agent_class, BaseAgent):
            raise TypeError(f"{agent_class.__name__} must be a subclass of BaseAgent")

        self._agents[agent_id] = agent_class

        if config is None:
            # Create a default instance to get the role
            temp = agent_class()
            config = AgentConfig(role=temp.role)

        self._configs[agent_id] = config

    def get(self, agent_id: str) -> BaseAgent:
        """Get or create an agent instance by ID."""
        if agent_id not in self._agents:
            raise AgentNotFoundError(f"Agent '{agent_id}' not registered")

        # Return cached instance or create new
        if agent_id not in self._instances:
            config = self._configs.get(agent_id)
            self._instances[agent_id] = self._agents[agent_id](config)

        return self._instances[agent_id]

    def list_agents(self) -> list[AgentConfig]:
        """List all registered agent configurations."""
        return list(self._configs.values())

    def list_agent_ids(self) -> list[str]:
        """List all registered agent IDs."""
        return list(self._agents.keys())

    def create_agent(self, role: AgentRole) -> BaseAgent:
        """Create an agent for a given role."""
        for agent_id, config in self._configs.items():
            if config.role == role:
                return self.get(agent_id)
        raise AgentNotFoundError(f"No agent registered for role {role.value}")

    def unregister(self, agent_id: str) -> None:
        """Remove an agent from the registry."""
        self._agents.pop(agent_id, None)
        self._configs.pop(agent_id, None)
        self._instances.pop(agent_id, None)

    def has_agent(self, agent_id: str) -> bool:
        """Check if an agent is registered."""
        return agent_id in self._agents
