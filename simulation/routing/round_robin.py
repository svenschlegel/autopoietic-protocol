"""Round-robin routing — fixed cycle through agents."""

from __future__ import annotations

from simulation.agents.sim_agent import SimAgent
from simulation.payloads.templates import SimPayload
from simulation.routing.base import RouterBase


class RoundRobinRouter(RouterBase):

    def __init__(self):
        self._index = 0

    @property
    def name(self) -> str:
        return "round_robin"

    def reset(self):
        self._index = 0

    def select_agent(self, payload: SimPayload, agents: list[SimAgent]) -> SimAgent | None:
        available = self._available(agents)
        if not available:
            return None

        # Cycle through all agents, skipping unavailable ones
        n = len(agents)
        for _ in range(n):
            candidate = agents[self._index % n]
            self._index += 1
            if not candidate.is_quarantined and candidate.current_load < candidate.max_load:
                return candidate
        return None
