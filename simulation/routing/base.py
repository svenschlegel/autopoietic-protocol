"""RouterBase — abstract base class for routing algorithms."""

from __future__ import annotations

from abc import ABC, abstractmethod
from simulation.agents.sim_agent import SimAgent
from simulation.payloads.templates import SimPayload


class RouterBase(ABC):
    """Select which agent should handle a given payload."""

    @abstractmethod
    def select_agent(self, payload: SimPayload, agents: list[SimAgent]) -> SimAgent | None:
        """Return the best agent for this payload, or None if all unavailable."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this routing algorithm."""

    def _available(self, agents: list[SimAgent]) -> list[SimAgent]:
        """Filter to non-quarantined, non-full agents."""
        return [
            a for a in agents
            if not a.is_quarantined and a.current_load < a.max_load
        ]
