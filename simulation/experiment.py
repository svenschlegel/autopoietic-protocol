"""ExperimentRunner — the main simulation loop.

For each routing algorithm:
1. Reset all agents (fresh mass/state)
2. For each round: generate payloads → route → solve (async) → verify → update mass
3. Same seeded payload sequence per algorithm (fair comparison)
4. Cross-algorithm analysis at the end
"""

from __future__ import annotations

import asyncio
import logging
import random
from pathlib import Path

from node_client.core.types import FrictionType
from simulation.agents.openrouter import OpenRouterClient
from simulation.agents.pool import AgentPool
from simulation.agents.sim_agent import SimAgent
from simulation.config import SimulationConfig
from simulation.economy.mass_tracker import MassTracker
from simulation.metrics.analysis import (
    compare_algorithms,
    domain_dominance,
    gini_over_time,
    specialization_index,
)
from simulation.metrics.collector import (
    MetricsCollector,
    PayloadResult,
    RoundResult,
)
from simulation.payloads.generator import PayloadGenerator
from simulation.payloads.templates import SimPayload
from simulation.routing.base import RouterBase
from simulation.routing.elo import EloRouter
from simulation.routing.equal_mass import EqualMassRouter
from simulation.routing.gravitational import GravitationalRouter
from simulation.routing.random_router import RandomRouter
from simulation.routing.round_robin import RoundRobinRouter
from simulation.verification.judge import JudgeLLM
from simulation.verification.verifier import VerificationEngine

logger = logging.getLogger(__name__)


ROUTER_REGISTRY: dict[str, type] = {
    "gravitational": GravitationalRouter,
    "random": RandomRouter,
    "round_robin": RoundRobinRouter,
    "elo": EloRouter,
    "equal_mass": EqualMassRouter,
}


class ExperimentRunner:
    """Orchestrates the full simulation experiment."""

    def __init__(self, config: SimulationConfig, output_dir: Path):
        self.config = config
        self.output_dir = output_dir
        self.pool = AgentPool.from_config(config)
        self.client = OpenRouterClient(config.openrouter_api_key, config.openrouter_base_url)
        self.judge = JudgeLLM(self.client, config.judge_model)
        self.verifier = VerificationEngine(self.judge)
        self.mass_tracker = MassTracker(config)

    def _build_routers(self) -> list[RouterBase]:
        routers = []
        for name in self.config.routing_algorithms:
            cls = ROUTER_REGISTRY.get(name)
            if cls is None:
                logger.warning(f"Unknown router: {name}, skipping")
                continue
            if cls == GravitationalRouter or cls == EqualMassRouter:
                routers.append(cls(alpha=self.config.alpha, beta=self.config.beta))
            elif cls == RandomRouter:
                routers.append(cls(rng=random.Random(self.config.seed + 1000)))
            else:
                router = cls()
                routers.append(router)
        return routers

    async def execute(self) -> dict:
        """Run the full experiment. Returns summary + detailed results."""
        routers = self._build_routers()
        all_collectors: dict[str, MetricsCollector] = {}

        # Save generator state so each algorithm gets identical payloads
        base_rng = random.Random(self.config.seed)
        generator = PayloadGenerator(self.config, base_rng)
        initial_rng_state = generator.get_state()

        total_api_calls = (
            self.config.num_rounds
            * self.config.payloads_per_round
            * len(routers)
        )
        print(f"\nStarting experiment: {len(routers)} algorithms × "
              f"{self.config.num_rounds} rounds × {self.config.payloads_per_round} payloads/round", flush=True)
        print(f"Estimated API calls: ~{total_api_calls} solver + judge calls", flush=True)
        print(f"Agents: {[a.agent_id for a in self.pool.agents]}\n", flush=True)

        for router in routers:
            print(f"{'='*60}", flush=True)
            print(f"Running algorithm: {router.name}", flush=True)
            print(f"{'='*60}", flush=True)

            # Reset everything for fair comparison
            self.pool.reset_all(self.config.initial_mass)
            generator.set_state(initial_rng_state)

            if hasattr(router, "reset"):
                router.reset()

            collector = MetricsCollector(router.name)

            for round_num in range(self.config.num_rounds):
                payloads = generator.generate_batch(self.config.payloads_per_round)
                round_result = await self._run_round(round_num, router, payloads)
                collector.record_round(round_result)

                # Progress
                if (round_num + 1) % 10 == 0 or round_num == 0:
                    stats = collector.summary_stats()
                    print(
                        f"  Round {round_num + 1}/{self.config.num_rounds} | "
                        f"avg_quality={stats['avg_quality']:.3f} | "
                        f"throughput={stats['throughput']:.3f}",
                        flush=True,
                    )

            all_collectors[router.name] = collector
            summary = collector.summary_stats()
            print(f"  Final: quality={summary['avg_quality']:.3f}, "
                  f"throughput={summary['throughput']:.3f}, "
                  f"slashed={summary['total_slashed']}\n", flush=True)

        await self.client.close()

        # Cross-algorithm analysis
        comparison = compare_algorithms(all_collectors)

        # Build detailed output
        detailed = {
            "algorithms": [c.to_dict() for c in all_collectors.values()],
            "trajectories": {
                name: {
                    "gini": gini_over_time(coll),
                }
                for name, coll in all_collectors.items()
            },
        }

        # Final agent analysis (from last algorithm's state — for specialization)
        spec = specialization_index(self.pool.agents)
        dom = domain_dominance(self.pool.agents)

        print(f"\n{'='*60}")
        print("RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"Quality winner:     {comparison['comparison']['quality_winner']}")
        print(f"Throughput winner:   {comparison['comparison']['throughput_winner']}")
        print(f"Most equal (Gini):  {comparison['comparison']['most_equal']}")
        print(f"\nGini coefficients:  {comparison['gini_final']}")
        print()

        for name, summary in comparison["algorithms"].items():
            print(f"  {name:20s} | quality={summary['avg_quality']:.3f} | "
                  f"throughput={summary['throughput']:.3f} | "
                  f"slashed={summary['total_slashed']}")

        return {
            "summary": comparison,
            "detailed": detailed,
        }

    async def _run_round(
        self, round_num: int, router: RouterBase, payloads: list[SimPayload]
    ) -> RoundResult:
        """Execute one round: route → solve → verify → update mass."""
        payload_results: list[PayloadResult] = []

        # Route all payloads
        assignments: list[tuple[SimPayload, SimAgent | None]] = []
        for payload in payloads:
            agent = router.select_agent(payload, self.pool.agents)
            assignments.append((payload, agent))
            if agent:
                agent.current_load += 1

        # Solve concurrently
        async def solve_one(payload: SimPayload, agent: SimAgent) -> tuple[SimPayload, SimAgent, str, float, bool, str | None]:
            result = await agent.solve(payload, self.client)
            return payload, agent, result.answer, result.solve_time, result.success, result.error

        tasks = []
        for payload, agent in assignments:
            if agent is not None:
                tasks.append(solve_one(payload, agent))

        solve_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build a lookup for solved payloads
        solved_map: dict[str, tuple] = {}
        for result in solve_results:
            if isinstance(result, Exception):
                logger.error(f"Solve task exception: {result}")
                continue
            payload, agent, answer, solve_time, success, error = result
            solved_map[payload.payload_id] = (agent, answer, solve_time, success, error)

        # Verify and update economy
        for payload, assigned_agent in assignments:
            if assigned_agent is None:
                payload_results.append(PayloadResult(
                    payload_id=payload.payload_id,
                    domain=payload.domain.name,
                    difficulty=payload.difficulty,
                    bounty=payload.bounty,
                    assigned_agent=None,
                    agent_model=None,
                    quality_score=0.0,
                    solve_time=0.0,
                    mass_accrued=0.0,
                    was_slashed=False,
                    prompt=payload.prompt,
                    answer=None,
                    expected_answer=payload.expected_answer,
                    scoring_rubric=payload.scoring_rubric,
                ))
                continue

            solved = solved_map.get(payload.payload_id)
            if solved is None:
                # Exception during solve
                assigned_agent.current_load = max(0, assigned_agent.current_load - 1)
                slash = self.mass_tracker.slash(assigned_agent, payload.domain)
                payload_results.append(PayloadResult(
                    payload_id=payload.payload_id,
                    domain=payload.domain.name,
                    difficulty=payload.difficulty,
                    bounty=payload.bounty,
                    assigned_agent=assigned_agent.agent_id,
                    agent_model=assigned_agent.model,
                    quality_score=0.0,
                    solve_time=0.0,
                    mass_accrued=0.0,
                    was_slashed=True,
                    error="solve_exception",
                    prompt=payload.prompt,
                    answer=None,
                    expected_answer=payload.expected_answer,
                    scoring_rubric=payload.scoring_rubric,
                ))
                continue

            agent, answer, solve_time, success, error = solved
            agent.current_load = max(0, agent.current_load - 1)

            if not success:
                slash = self.mass_tracker.slash(agent, payload.domain)
                payload_results.append(PayloadResult(
                    payload_id=payload.payload_id,
                    domain=payload.domain.name,
                    difficulty=payload.difficulty,
                    bounty=payload.bounty,
                    assigned_agent=agent.agent_id,
                    agent_model=agent.model,
                    quality_score=0.0,
                    solve_time=solve_time,
                    mass_accrued=0.0,
                    was_slashed=True,
                    error=error,
                    prompt=payload.prompt,
                    answer=answer,  # "" on failure, but distinguishes from None
                    expected_answer=payload.expected_answer,
                    scoring_rubric=payload.scoring_rubric,
                ))
                continue

            # Score the answer
            quality = await self.verifier.score(payload, answer)

            # Economy update
            mass_accrued = 0.0
            was_slashed = False
            if quality >= self.config.quality_threshold:
                mass_accrued = self.mass_tracker.accrue(
                    agent, payload.domain, payload.bounty,
                    solve_time, payload.execution_window,
                )
            else:
                self.mass_tracker.slash(agent, payload.domain)
                was_slashed = True

            payload_results.append(PayloadResult(
                payload_id=payload.payload_id,
                domain=payload.domain.name,
                difficulty=payload.difficulty,
                bounty=payload.bounty,
                assigned_agent=agent.agent_id,
                agent_model=agent.model,
                quality_score=round(quality, 4),
                solve_time=round(solve_time, 3),
                mass_accrued=round(mass_accrued, 4),
                was_slashed=was_slashed,
                prompt=payload.prompt,
                answer=answer,
                expected_answer=payload.expected_answer,
                scoring_rubric=payload.scoring_rubric,
            ))

        # V3.5 reform stack — apply per-round decay before the snapshot so
        # the snapshot reflects the post-decay state of the round.
        # Default δ=0 makes this a no-op (V3.5 ships infrastructure only).
        self.mass_tracker.tick_decay(self.pool.agents)

        # Mass snapshot (post-accrual, post-decay, pre-rebase)
        snapshot = self.mass_tracker.snapshot(self.pool.agents)

        # Metabolic Season rebase fires AFTER the snapshot at season
        # boundaries. The snapshot for round N (the last round of a season)
        # records the pre-rebase peak; round N+1 starts with the rebased
        # routing mass. season_length=0 disables rebase entirely.
        season_length = getattr(self.config, "season_length", 0)
        if season_length > 0 and (round_num + 1) % season_length == 0:
            logger.info(
                f"  SEASON BOUNDARY: end of round {round_num}, "
                f"applying log-compression rebase to routing mass"
            )
            self.mass_tracker.rebase_season(self.pool.agents)

        return RoundResult(
            round_num=round_num,
            routing_algorithm=router.name,
            payloads=payload_results,
            mass_snapshot=snapshot,
        )
