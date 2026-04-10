"""Gravitational Routing — the protocol's core formula.

P_i = (M_i ^ α) / ((D_{i,p} + 1) × (L_i + 1) ^ β)
"""

from __future__ import annotations

from simulation.agents.sim_agent import SimAgent
from simulation.payloads.templates import SimPayload
from simulation.routing.base import RouterBase


class GravitationalRouter(RouterBase):
    """Routes payloads using the Gravitational Routing Formula."""

    def __init__(self, alpha: float = 0.8, beta: float = 1.5):
        self.alpha = alpha
        self.beta = beta

    @property
    def name(self) -> str:
        return "gravitational"

    def _priority(self, agent: SimAgent, payload: SimPayload) -> float:
        M = agent.domain_mass(payload.domain)
        D = agent.topographic_distance(payload.domain)
        L = agent.current_load
        if M <= 0:
            return 0.0
        return (M ** self.alpha) / ((D + 1) * (L + 1) ** self.beta)

    def select_agent(self, payload: SimPayload, agents: list[SimAgent]) -> SimAgent | None:
        available = self._available(agents)
        if not available:
            return None
        return max(available, key=lambda a: self._priority(a, payload))
