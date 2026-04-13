"""Composite Routing — weighted multi-domain priority scoring.

For composite (multi-domain) payloads:

    P_composite = Sigma(w_d * M_route_d^alpha) / ((D_weighted + 1) * (L + 1)^beta)
    where D_weighted = Sigma(w_d * D_d)

Falls back to standard gravitational routing for single-domain payloads
(i.e. those without a domain_weights attribute).
"""

from __future__ import annotations

from node_client.core.types import FrictionType
from simulation.agents.sim_agent import SimAgent
from simulation.payloads.templates import SimPayload
from simulation.routing.base import RouterBase


class CompositeRouter(RouterBase):
    """Routes payloads using a weighted composite priority score across domains."""

    def __init__(self, alpha: float = 0.8, beta: float = 1.5):
        self.alpha = alpha
        self.beta = beta

    @property
    def name(self) -> str:
        return "composite"

    # ------------------------------------------------------------------
    # Single-domain fallback (standard gravitational formula)
    # ------------------------------------------------------------------

    def _gravitational_priority(self, agent: SimAgent, payload: SimPayload) -> float:
        M = agent.domain_mass(payload.domain)
        D = agent.topographic_distance(payload.domain)
        L = agent.current_load
        if M <= 0:
            return 0.0
        return (M ** self.alpha) / ((D + 1) * (L + 1) ** self.beta)

    # ------------------------------------------------------------------
    # Multi-domain composite score
    # ------------------------------------------------------------------

    def _composite_priority(
        self,
        agent: SimAgent,
        payload: SimPayload,
        domain_weights: dict[FrictionType, float],
    ) -> float:
        weighted_mass = 0.0
        weighted_distance = 0.0

        for domain, w in domain_weights.items():
            M = agent.domain_mass(domain)
            if M <= 0:
                # Zero mass in any weighted domain contributes nothing
                # (but other domains can still contribute).
                pass
            else:
                weighted_mass += w * (M ** self.alpha)
            weighted_distance += w * agent.topographic_distance(domain)

        if weighted_mass <= 0:
            return 0.0

        L = agent.current_load
        return weighted_mass / ((weighted_distance + 1) * (L + 1) ** self.beta)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_agent(self, payload: SimPayload, agents: list[SimAgent]) -> SimAgent | None:
        available = self._available(agents)
        if not available:
            return None

        domain_weights: dict[FrictionType, float] | None = getattr(
            payload, "domain_weights", None
        )

        if domain_weights:
            key = lambda a: self._composite_priority(a, payload, domain_weights)
        else:
            key = lambda a: self._gravitational_priority(a, payload)

        return max(available, key=key)
