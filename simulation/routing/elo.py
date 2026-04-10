"""ELO / pure-skill routing — pick the highest-mass agent for the domain.

No load or distance factor. Tests whether "just pick the best" works better
than gravitational routing's load-balancing and distance components.
"""

from __future__ import annotations

from simulation.agents.sim_agent import SimAgent
from simulation.payloads.templates import SimPayload
from simulation.routing.base import RouterBase


class EloRouter(RouterBase):

    @property
    def name(self) -> str:
        return "elo"

    def select_agent(self, payload: SimPayload, agents: list[SimAgent]) -> SimAgent | None:
        available = self._available(agents)
        if not available:
            return None
        return max(available, key=lambda a: a.domain_mass(payload.domain))
