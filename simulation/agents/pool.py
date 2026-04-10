"""AgentPool — creates and manages simulation agents from config."""

from __future__ import annotations

from node_client.core.types import FrictionType
from simulation.agents.sim_agent import SimAgent
from simulation.config import SimulationConfig

# Map string names to FrictionType enum
_DOMAIN_MAP = {
    "SEMANTIC": FrictionType.SEMANTIC,
    "DETERMINISTIC": FrictionType.DETERMINISTIC,
    "SPATIAL": FrictionType.SPATIAL,
    "TEMPORAL": FrictionType.TEMPORAL,
}


class AgentPool:
    """Creates and holds all simulation agents."""

    def __init__(self, agents: list[SimAgent]):
        self.agents = agents

    @classmethod
    def from_config(cls, config: SimulationConfig) -> "AgentPool":
        agents = []
        for ac in config.agent_configs:
            primary = _DOMAIN_MAP[ac.primary_domain]
            secondary = [_DOMAIN_MAP[d] for d in ac.secondary_domains]
            agent = SimAgent(
                agent_id=ac.name,
                model=ac.model,
                primary_domain=primary,
                secondary_domains=secondary,
                initial_mass=config.initial_mass,
                max_load=config.max_load,
            )
            agents.append(agent)
        return cls(agents)

    def reset_all(self, initial_mass: float = 1.0):
        """Reset all agents for a new algorithm run."""
        for agent in self.agents:
            agent.reset(initial_mass)

    def available_agents(self) -> list[SimAgent]:
        """Return agents that are not quarantined and not at max load."""
        return [
            a for a in self.agents
            if not a.is_quarantined and a.current_load < a.max_load
        ]

    def __len__(self) -> int:
        return len(self.agents)
