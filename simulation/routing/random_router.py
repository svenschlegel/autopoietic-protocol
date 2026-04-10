"""Random routing — uniform random assignment."""

from __future__ import annotations

import random as _random

from simulation.agents.sim_agent import SimAgent
from simulation.payloads.templates import SimPayload
from simulation.routing.base import RouterBase


class RandomRouter(RouterBase):

    def __init__(self, rng: _random.Random | None = None):
        self.rng = rng or _random.Random()

    @property
    def name(self) -> str:
        return "random"

    def select_agent(self, payload: SimPayload, agents: list[SimAgent]) -> SimAgent | None:
        available = self._available(agents)
        if not available:
            return None
        return self.rng.choice(available)
