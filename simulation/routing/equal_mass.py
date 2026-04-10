"""Equal-mass gravitational routing — same formula but M_i = 1.0 for all.

Tests whether the load-balancing and distance components alone are valuable,
removing the rich-get-richer dynamic.
"""

from __future__ import annotations

from simulation.agents.sim_agent import SimAgent
from simulation.payloads.templates import SimPayload
from simulation.routing.base import RouterBase


class EqualMassRouter(RouterBase):

    def __init__(self, alpha: float = 0.8, beta: float = 1.5):
        self.alpha = alpha
        self.beta = beta

    @property
    def name(self) -> str:
        return "equal_mass"

    def _priority(self, agent: SimAgent, payload: SimPayload) -> float:
        M = 1.0  # Override: all agents treated as equal mass
        D = agent.topographic_distance(payload.domain)
        L = agent.current_load
        return (M ** self.alpha) / ((D + 1) * (L + 1) ** self.beta)

    def select_agent(self, payload: SimPayload, agents: list[SimAgent]) -> SimAgent | None:
        available = self._available(agents)
        if not available:
            return None
        return max(available, key=lambda a: self._priority(a, payload))
