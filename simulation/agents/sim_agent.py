"""SimAgent — LLM-backed solver with per-domain Soulbound Mass."""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field

from node_client.core.types import FrictionType, VerificationTier
from simulation.agents.openrouter import OpenRouterClient

logger = logging.getLogger(__name__)

DOMAIN_SYSTEM_PROMPTS = {
    FrictionType.SEMANTIC: (
        "You are an AI agent solving a semantic analysis task. "
        "Be precise and thorough. Follow the instructions exactly."
    ),
    FrictionType.DETERMINISTIC: (
        "You are an AI agent solving a deterministic computation task. "
        "Return ONLY the exact answer with no explanation unless asked."
    ),
    FrictionType.SPATIAL: (
        "You are an AI agent solving a spatial reasoning task. "
        "Show your work step by step, then give the final answer clearly."
    ),
    FrictionType.TEMPORAL: (
        "You are an AI agent solving a temporal reasoning task. "
        "Think through the time relationships carefully. Show reasoning, then answer."
    ),
}


@dataclass
class SolveResult:
    answer: str
    solve_time: float  # seconds
    success: bool  # False if API error
    error: str | None = None


class SimAgent:
    """A simulation agent backed by an LLM via OpenRouter."""

    def __init__(
        self,
        agent_id: str,
        model: str,
        primary_domain: FrictionType,
        secondary_domains: list[FrictionType] | None = None,
        initial_mass: float = 1.0,
        max_load: int = 3,
    ):
        self.agent_id = agent_id
        self.model = model
        self.primary_domain = primary_domain
        self.secondary_domains = secondary_domains or []
        self.max_load = max_load

        # Per-domain Soulbound Mass — V3.5 Dual-Mass Architecture.
        # See docs/MASS_ACCRUAL_REFORM_v0.1.md §2.
        #   self.mass     == Routing Mass (M_route): cyclical, drives the
        #                    gravitational formula, subject to sublinear
        #                    accrual / seasonal rebase / decay in later steps.
        #   self.gov_mass == Governance Mass (M_gov): permanent, monotonic,
        #                    never decreases, used for voting / milestones /
        #                    social proof. Untouched by slash, decay, rebase.
        # In this intermediate refactor both quantities evolve identically;
        # the split is in name only and routing decisions must be unchanged.
        self.mass: dict[FrictionType, float] = {ft: initial_mass for ft in FrictionType}
        self.gov_mass: dict[FrictionType, float] = {ft: initial_mass for ft in FrictionType}
        self.current_load = 0
        self.consecutive_failures = 0
        self.is_quarantined = False

        # Tracking
        self.total_solved = 0
        self.total_failed = 0
        self.total_earned = 0.0
        self.solve_history: list[dict] = []

        # Phase 2 — per-operator GPSL fluency tracking.
        # Keys are operator strings (e.g., "→", "⥀", "⦸").
        # Values are {"count": int, "quality_sum": float}.
        # Updated after each solve based on which operators the payload
        # required and the quality score achieved. Used by the continuous-D
        # routing formula in simulation/routing/fluency.py.
        self.operator_fluency: dict[str, dict] = {}

    @property
    def aggregate_mass(self) -> float:
        """Sum of routing mass across domains. Backwards-compat alias."""
        return sum(self.mass.values())

    @property
    def aggregate_routing_mass(self) -> float:
        return sum(self.mass.values())

    @property
    def aggregate_governance_mass(self) -> float:
        return sum(self.gov_mass.values())

    def domain_mass(self, domain: FrictionType) -> float:
        """Routing mass in a domain. Backwards-compat alias for
        domain_routing_mass — all routers go through this."""
        return self.mass.get(domain, 0.0)

    def domain_routing_mass(self, domain: FrictionType) -> float:
        return self.mass.get(domain, 0.0)

    def domain_governance_mass(self, domain: FrictionType) -> float:
        return self.gov_mass.get(domain, 0.0)

    def update_operator_fluency(self, operators: list[str], quality: float) -> None:
        """Record operator-level fluency after a solve.

        Called after each successful payload solve with the list of GPSL
        operators the payload required and the quality score achieved.
        Builds the fluency profile used by the continuous-D router.
        """
        for op in operators:
            if op not in self.operator_fluency:
                self.operator_fluency[op] = {"count": 0, "quality_sum": 0.0}
            self.operator_fluency[op]["count"] += 1
            self.operator_fluency[op]["quality_sum"] += quality

    def topographic_distance(self, domain: FrictionType) -> float:
        """Distance from agent's specialization to the payload's domain."""
        if domain == self.primary_domain:
            return 0.0
        if domain in self.secondary_domains:
            return 0.5
        return 2.0

    def reset(self, initial_mass: float = 1.0):
        """Reset state for a new experiment run."""
        self.mass = {ft: initial_mass for ft in FrictionType}
        self.gov_mass = {ft: initial_mass for ft in FrictionType}
        self.operator_fluency = {}
        self.current_load = 0
        self.consecutive_failures = 0
        self.is_quarantined = False
        self.total_solved = 0
        self.total_failed = 0
        self.total_earned = 0.0
        self.solve_history = []

    async def solve(self, payload, client: OpenRouterClient) -> SolveResult:
        """Send the payload's task to the LLM and return the result."""
        system_prompt = DOMAIN_SYSTEM_PROMPTS.get(
            payload.domain, "You are an AI agent solving a task."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": payload.prompt},
        ]

        start = time.monotonic()
        try:
            answer = await client.complete(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
            )
            elapsed = time.monotonic() - start
            return SolveResult(answer=answer, solve_time=elapsed, success=True)
        except Exception as e:
            elapsed = time.monotonic() - start
            logger.error(f"Agent {self.agent_id} solve failed: {e}")
            return SolveResult(
                answer="", solve_time=elapsed, success=False, error=str(e)
            )

    def __repr__(self) -> str:
        return (
            f"SimAgent({self.agent_id}, model={self.model}, "
            f"primary={self.primary_domain.name}, mass={self.aggregate_mass:.2f})"
        )
