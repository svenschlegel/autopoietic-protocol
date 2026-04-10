"""MassTracker — per-agent, per-domain Soulbound Mass economy.

V3.5 Dual-Mass Architecture (see docs/MASS_ACCRUAL_REFORM_v0.1.md §2):
- Routing Mass (agent.mass): cyclical, drives the gravitational formula.
  Slashed on failure; will be subject to sublinear accrual / seasonal
  rebase / decay in later refactor steps.
- Governance Mass (agent.gov_mass): permanent, monotonically increasing.
  Never slashed, never decayed, never rebased. Used for voting / milestones
  / social proof.

Sublinear routing accrual (V3.5, MASS_ACCRUAL_REFORM_v0.1 §3.2):
  delta_route = bounty * sigma * (1 / log(2 + M_route_domain))
Governance mass continues to accrue the full linear delta. The two
quantities diverge over time: governance is the cumulative honest record;
routing is the saturated re-routable fuel.

At M_route≈0:    multiplier ≈ 1/log(2) ≈ 1.443  (slight boost for fresh agents)
At M_route=1:    multiplier ≈ 1/log(3) ≈ 0.910
At M_route=100:  multiplier ≈ 1/log(102) ≈ 0.216
At M_route=5000: multiplier ≈ 1/log(5002) ≈ 0.117

Implements:
- Accrual:  routing mass: delta_route = bounty * sigma * f(M_route_domain)
            governance mass: delta_gov = bounty * sigma  (linear, unchanged)
- Slashing: 5% of routing mass on failure. Governance mass untouched.
- Quarantine: after consecutive_failures >= threshold
"""

from __future__ import annotations

import logging
import math

from node_client.core.types import FrictionType
from simulation.agents.sim_agent import SimAgent
from simulation.config import SimulationConfig

logger = logging.getLogger(__name__)


class MassTracker:
    """Manages Soulbound Mass accrual, slashing, and quarantine."""

    def __init__(self, config: SimulationConfig):
        self.slash_rate = config.slash_rate
        self.quarantine_threshold = config.quarantine_threshold
        self.sigma_min = config.sigma_min
        self.sigma_max = config.sigma_max
        # V3.5 reform parameters (default to off if absent on the config).
        self.sublinear_accrual = getattr(config, "sublinear_accrual", True)
        self.season_length = getattr(config, "season_length", 0)
        self.season_rebase_c = getattr(config, "season_rebase_c", 100.0)
        self.decay_rate = getattr(config, "decay_rate", 0.0)

    def accrue(
        self,
        agent: SimAgent,
        domain: FrictionType,
        bounty: float,
        solve_time: float,
        execution_window: int,
    ) -> float:
        """
        Accrue mass after a successful solve.
        Returns the mass delta.
        """
        # Speed multiplier: faster = more mass
        if solve_time <= 0:
            sigma = self.sigma_max
        else:
            sigma = execution_window / solve_time
        sigma = max(self.sigma_min, min(self.sigma_max, sigma))

        # Linear delta — governance mass always uses this directly.
        linear_delta = bounty * sigma

        # Sublinear (log-saturation) damping for routing mass, gated by config
        # so the Phase 1 2×2 design can run V3.4-linear control cells.
        # See MASS_ACCRUAL_REFORM_v0.1.md §3.2. Domain-local: each agent
        # saturates per-domain so cross-domain growth is unrestricted.
        current_route = agent.mass.get(domain, 0.0)
        if self.sublinear_accrual:
            damping = 1.0 / math.log(2.0 + current_route)
            route_delta = linear_delta * damping
        else:
            damping = 1.0
            route_delta = linear_delta

        agent.mass[domain] = current_route + route_delta
        agent.gov_mass[domain] = agent.gov_mass.get(domain, 0.0) + linear_delta
        agent.consecutive_failures = 0
        agent.total_solved += 1
        agent.total_earned += bounty

        logger.debug(
            f"  +Mass: {agent.agent_id} domain={domain.name} "
            f"linear={linear_delta:.2f} damp={damping:.3f} (σ={sigma:.2f}) "
            f"route={agent.domain_routing_mass(domain):.2f} "
            f"gov={agent.domain_governance_mass(domain):.2f}"
        )
        # Return the routing-mass delta — that is the value that drives the
        # protocol-visible "mass earned" reporting downstream.
        return route_delta

    def slash(self, agent: SimAgent, domain: FrictionType) -> float:
        """
        Slash routing mass after a failed solve. Governance mass is untouched
        (it is permanent and monotonic by construction — see §2 of the
        Dual-Mass spec).
        Returns the amount slashed.
        """
        current = agent.mass.get(domain, 0.0)
        slash_amount = current * self.slash_rate
        agent.mass[domain] = current - slash_amount
        agent.consecutive_failures += 1
        agent.total_failed += 1

        logger.debug(
            f"  -Slash: {agent.agent_id} domain={domain.name} "
            f"slashed={slash_amount:.2f} failures={agent.consecutive_failures}"
        )

        self._check_quarantine(agent)
        return slash_amount

    def _check_quarantine(self, agent: SimAgent):
        """Quarantine agent if consecutive failures exceed threshold."""
        if agent.consecutive_failures >= self.quarantine_threshold and not agent.is_quarantined:
            agent.is_quarantined = True
            logger.info(
                f"  QUARANTINE: {agent.agent_id} after {agent.consecutive_failures} "
                f"consecutive failures"
            )

    def rebase_season(self, agents: list[SimAgent]) -> None:
        """Metabolic Season rebase (MASS_ACCRUAL_REFORM_v0.1.md §3.3).

        Log-compress routing mass while preserving order:
            M_route_new = log(1 + M_route_old) * C
        Governance mass is untouched (the dual-mass safety guarantee).

        The compression preserves the order of agents by routing mass while
        collapsing the meaningful range from many orders of magnitude to ~1,
        forcing the ecosystem to re-prove competence each season without
        destroying the historical record.
        """
        C = self.season_rebase_c
        for agent in agents:
            for domain in list(agent.mass.keys()):
                old = agent.mass[domain]
                agent.mass[domain] = math.log(1.0 + old) * C
            logger.info(
                f"  REBASE: {agent.agent_id} routing mass log-compressed × C={C} "
                f"(governance untouched)"
            )

    def tick_decay(self, agents: list[SimAgent]) -> None:
        """Per-round background decay (MASS_ACCRUAL_REFORM_v0.1.md §3.4).

            M_route *= (1 - δ)

        Touches routing mass only. Ships with δ=0 in V3.5 (infrastructure
        only) so default behavior is unchanged; governance can activate
        later via config if §3.1–§3.3 prove insufficient.
        """
        if self.decay_rate <= 0.0:
            return
        factor = 1.0 - self.decay_rate
        for agent in agents:
            for domain in list(agent.mass.keys()):
                agent.mass[domain] *= factor

    def snapshot(self, agents: list[SimAgent]) -> dict:
        """Return current mass state for all agents.

        Emits both routing mass and governance mass under the V3.5 dual-mass
        architecture. The legacy `per_domain` and `aggregate_mass` keys are
        preserved as aliases of the routing-mass quantities so that existing
        analysis scripts (notably simulation/analysis/phase0_continuous_distance.py)
        keep working against new results.json files.
        """
        return {
            agent.agent_id: {
                # Legacy keys (== routing mass; preserved for backwards compat).
                "aggregate_mass": agent.aggregate_routing_mass,
                "per_domain": {ft.name: agent.mass.get(ft, 0.0) for ft in FrictionType},
                # V3.5 explicit dual-mass keys.
                "aggregate_routing_mass": agent.aggregate_routing_mass,
                "aggregate_governance_mass": agent.aggregate_governance_mass,
                "per_domain_routing": {
                    ft.name: agent.mass.get(ft, 0.0) for ft in FrictionType
                },
                "per_domain_governance": {
                    ft.name: agent.gov_mass.get(ft, 0.0) for ft in FrictionType
                },
                "is_quarantined": agent.is_quarantined,
                "consecutive_failures": agent.consecutive_failures,
                "total_solved": agent.total_solved,
                "total_failed": agent.total_failed,
            }
            for agent in agents
        }
