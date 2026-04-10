"""PayloadGenerator — creates batches of simulation payloads."""

from __future__ import annotations

import random
import uuid

from node_client.core.types import FrictionType
from simulation.config import SimulationConfig
from simulation.payloads.templates import (
    DOMAIN_GENERATORS,
    DOMAIN_TIERS,
    SimPayload,
)

# Map string names to FrictionType
_DOMAIN_MAP = {
    "SEMANTIC": FrictionType.SEMANTIC,
    "DETERMINISTIC": FrictionType.DETERMINISTIC,
    "SPATIAL": FrictionType.SPATIAL,
    "TEMPORAL": FrictionType.TEMPORAL,
}


class PayloadGenerator:
    """Generates simulation payloads with seeded randomness."""

    def __init__(self, config: SimulationConfig, rng: random.Random):
        self.config = config
        self.rng = rng

        # Build weighted domain list for sampling
        self._domains: list[FrictionType] = []
        self._weights: list[float] = []
        for name, weight in config.domain_weights.items():
            self._domains.append(_DOMAIN_MAP[name])
            self._weights.append(weight)

    def generate_batch(self, count: int) -> list[SimPayload]:
        """Generate a batch of payloads with domain distribution matching config weights."""
        return [self._generate_one() for _ in range(count)]

    def _generate_one(self) -> SimPayload:
        # Sample domain
        domain = self.rng.choices(self._domains, weights=self._weights, k=1)[0]

        # Sample difficulty and bounty
        diff_lo, diff_hi = self.config.difficulty_range
        difficulty = self.rng.uniform(diff_lo, diff_hi)

        bounty_lo, bounty_hi = self.config.bounty_range
        bounty = round(self.rng.uniform(bounty_lo, bounty_hi), 2)

        # Generate task content
        generator = DOMAIN_GENERATORS[domain]
        prompt, expected_answer, scoring_rubric = generator(self.rng, difficulty)

        tier = DOMAIN_TIERS[domain]

        return SimPayload(
            payload_id=uuid.uuid4().hex[:12],
            domain=domain,
            tier=tier,
            prompt=prompt,
            expected_answer=expected_answer,
            scoring_rubric=scoring_rubric,
            difficulty=difficulty,
            bounty=bounty,
            execution_window=self.config.execution_window,
        )

    def get_state(self) -> tuple:
        """Return RNG state for reproducibility."""
        return self.rng.getstate()

    def set_state(self, state: tuple):
        """Restore RNG state for reproducibility."""
        self.rng.setstate(state)
