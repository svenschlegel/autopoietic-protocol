"""Gravitational Routing with operator-level continuous distance.

Extends GravitationalRouter to use continuous D from operator fluency
profiles when the payload has operators_required metadata. Falls back
to categorical D for standard payloads.

P_i = M_route^α / ((D + 1)(L + 1)^β)

where D is:
  - continuous_distance(agent_fluency, payload.operators_required) if GPSL
  - categorical topographic_distance(agent, domain) otherwise

See: PHASE2_WORKPLAN.md §3.5
"""

from __future__ import annotations

from simulation.agents.sim_agent import SimAgent
from simulation.payloads.templates import SimPayload
from simulation.routing.base import RouterBase
from simulation.routing.fluency import continuous_distance


class GravitationalGpslRouter(RouterBase):
    """Gravitational router with GPSL operator-level distance."""

    def __init__(self, alpha: float = 0.8, beta: float = 1.5):
        self.alpha = alpha
        self.beta = beta

    @property
    def name(self) -> str:
        return "gravitational_gpsl"

    def _priority(self, agent: SimAgent, payload: SimPayload) -> float:
        M = agent.domain_routing_mass(payload.domain)
        L = agent.current_load

        if M <= 0:
            return 0.0

        # Use continuous D if the payload has operator metadata
        operators_required: list[str] | None = getattr(
            payload, "operators_required", None
        )
        if operators_required:
            D = continuous_distance(agent.operator_fluency, operators_required)
        else:
            D = agent.topographic_distance(payload.domain)

        return (M ** self.alpha) / ((D + 1) * (L + 1) ** self.beta)

    def select_agent(
        self, payload: SimPayload, agents: list[SimAgent]
    ) -> SimAgent | None:
        available = self._available(agents)
        if not available:
            return None
        return max(available, key=lambda a: self._priority(a, payload))
