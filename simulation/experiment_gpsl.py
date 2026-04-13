"""Phase 2 — GPSL Cipher Encoding & Operator-Level Continuous Distance.

Runs a 2×2 factorial experiment:
  Cell A: categorical D + linear accrual (V3.4 control)
  Cell B: continuous D + linear accrual
  Cell C: categorical D + sublinear accrual + rebase (Phase 1 validated)
  Cell D: continuous D + sublinear accrual + rebase (full V3.5+GPSL stack)

Each cell runs num_rounds rounds of GPSL-encoded Spatial payloads.
After each solve, the agent's operator fluency profile is updated.
The continuous-D router uses these profiles to compute distance.

Results saved to {output_dir}/gpsl_results.json.

See: docs/PHASE2_WORKPLAN.md
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from pathlib import Path

from node_client.core.types import FrictionType, VerificationTier
from simulation.agents.gpsl_scaffold import build_gpsl_system_prompt, GPSL_SYSTEM_SCAFFOLD
from simulation.agents.openrouter import OpenRouterClient
from simulation.agents.pool import AgentPool
from simulation.agents.sim_agent import SimAgent, DOMAIN_SYSTEM_PROMPTS
from simulation.config import SimulationConfig
from simulation.economy.mass_tracker import MassTracker
from simulation.payloads.gpsl_spatial_templates import GPSL_SPATIAL_TEMPLATES, GpslPayload
from simulation.payloads.templates import SimPayload
from simulation.routing.gravitational import GravitationalRouter
from simulation.routing.gravitational_gpsl import GravitationalGpslRouter
from simulation.verification.judge import JudgeLLM

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cell configuration
# ---------------------------------------------------------------------------

CELLS = {
    "A": {"label": "categorical D + linear accrual (V3.4)", "continuous_d": False, "sublinear": False},
    "B": {"label": "continuous D + linear accrual", "continuous_d": True, "sublinear": False},
    "C": {"label": "categorical D + sublinear (Phase 1)", "continuous_d": False, "sublinear": True},
    "D": {"label": "continuous D + sublinear (full stack)", "continuous_d": True, "sublinear": True},
}


class GpslExperimentRunner:
    """Runs the 2×2 factorial GPSL experiment."""

    def __init__(self, config: SimulationConfig, output_dir: Path):
        self.config = config
        self.output_dir = output_dir
        self.pool = AgentPool.from_config(config)
        self.client = OpenRouterClient(
            config.openrouter_api_key, config.openrouter_base_url,
        )
        self.judge = JudgeLLM(self.client, config.judge_model)

        # Routers
        self.cat_router = GravitationalRouter(
            alpha=config.alpha, beta=config.beta,
        )
        self.cont_router = GravitationalGpslRouter(
            alpha=config.alpha, beta=config.beta,
        )

        # Payload pool
        self.payloads = list(GPSL_SPATIAL_TEMPLATES)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _agent_solve(
        self, agent: SimAgent, prompt: str, use_gpsl_scaffold: bool = True,
    ) -> str:
        """Send a prompt to an agent and return the answer text."""
        if use_gpsl_scaffold:
            domain_prompt = DOMAIN_SYSTEM_PROMPTS.get(
                FrictionType.SPATIAL,
                "You are an AI agent solving a spatial reasoning task.",
            )
            system = build_gpsl_system_prompt(domain_prompt)
        else:
            system = DOMAIN_SYSTEM_PROMPTS.get(
                FrictionType.SPATIAL,
                "You are an AI agent solving a spatial reasoning task.",
            )

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        return await self.client.complete(
            model=agent.model,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )

    async def _score(self, prompt: str, rubric: str, answer: str) -> float:
        """Score an answer using the judge LLM."""
        judge_prompt = (
            f"You are evaluating an AI agent's answer to a spatial reasoning task.\n\n"
            f"TASK:\n{prompt}\n\n"
            f"AGENT'S ANSWER:\n{answer}\n\n"
            f"SCORING RUBRIC:\n{rubric}\n\n"
            f"Score the answer on a scale of 0.0 to 1.0 based on the rubric. "
            f"Return ONLY a decimal number between 0.0 and 1.0, nothing else."
        )
        messages = [
            {"role": "system", "content": "You are a strict, fair evaluator."},
            {"role": "user", "content": judge_prompt},
        ]
        raw = await self.client.complete(
            model=self.judge.model,
            messages=messages,
            temperature=0.0,
            max_tokens=10,
        )
        try:
            return float(raw.strip())
        except (ValueError, TypeError):
            logger.warning("Judge returned non-numeric: %s", raw[:50])
            return 0.0

    def _select_payload(self, rng: random.Random) -> GpslPayload:
        """Pick a random GPSL payload."""
        return rng.choice(self.payloads)

    # ------------------------------------------------------------------
    # Run one cell of the 2×2
    # ------------------------------------------------------------------

    async def _run_cell(
        self,
        cell_id: str,
        cell_cfg: dict,
        num_rounds: int,
        payloads_per_round: int,
        seed: int,
    ) -> dict:
        """Run a single cell of the factorial design."""
        label = cell_cfg["label"]
        use_continuous_d = cell_cfg["continuous_d"]
        use_sublinear = cell_cfg["sublinear"]

        print(f"\n{'='*60}", flush=True)
        print(f"Cell {cell_id}: {label}", flush=True)
        print(f"{'='*60}", flush=True)

        # Reset agents for this cell
        self.pool.reset_all(self.config.initial_mass)

        # Configure mass tracker for this cell
        from types import SimpleNamespace
        mass_cfg = SimpleNamespace(
            slash_rate=self.config.slash_rate,
            quarantine_threshold=self.config.quarantine_threshold,
            sigma_min=self.config.sigma_min,
            sigma_max=self.config.sigma_max,
            sublinear_accrual=use_sublinear,
            season_length=getattr(self.config, "season_length", 0) if use_sublinear else 0,
            season_rebase_c=getattr(self.config, "season_rebase_c", 100.0),
            decay_rate=0.0,
        )
        mass_tracker = MassTracker(mass_cfg)

        # Select router
        router = self.cont_router if use_continuous_d else self.cat_router

        rng = random.Random(seed)

        # Track results
        round_results = []
        routing_decisions = []
        total_quality = 0.0
        total_assigned = 0

        for round_num in range(num_rounds):
            round_qualities = []

            for _ in range(payloads_per_round):
                payload = self._select_payload(rng)

                # Route
                agent = router.select_agent(payload, self.pool.agents)
                if agent is None:
                    continue

                # Also compute what the OTHER router would have picked (for divergence)
                alt_router = self.cat_router if use_continuous_d else self.cont_router
                alt_agent = alt_router.select_agent(payload, self.pool.agents)
                diverged = (alt_agent is not None and alt_agent.agent_id != agent.agent_id)

                # Solve (use GPSL cipher for GPSL-encoded payloads)
                agent.current_load += 1
                try:
                    answer = await self._agent_solve(agent, payload.gpsl_cipher)
                    quality = await self._score(
                        payload.plain_prompt, payload.scoring_rubric, answer,
                    )
                except Exception as e:
                    logger.error("Solve/score failed: %s", e)
                    quality = 0.0
                    answer = ""
                finally:
                    agent.current_load = max(0, agent.current_load - 1)

                # Economy update
                if quality >= self.config.quality_threshold:
                    mass_tracker.accrue(
                        agent, payload.domain, payload.bounty,
                        1.0, payload.execution_window,
                    )
                    # Update operator fluency
                    agent.update_operator_fluency(
                        payload.operators_required, quality,
                    )
                else:
                    mass_tracker.slash(agent, payload.domain)

                round_qualities.append(quality)
                total_quality += quality
                total_assigned += 1

                routing_decisions.append({
                    "round": round_num,
                    "payload_id": payload.payload_id,
                    "operators": payload.operators_required,
                    "agent": agent.agent_id,
                    "alt_agent": alt_agent.agent_id if alt_agent else None,
                    "diverged": diverged,
                    "quality": round(quality, 4),
                })

            # Decay (if active)
            mass_tracker.tick_decay(self.pool.agents)

            # Season rebase
            season_length = mass_cfg.season_length
            if season_length > 0 and (round_num + 1) % season_length == 0:
                logger.info("Season rebase at round %d", round_num)
                mass_tracker.rebase_season(self.pool.agents)

            avg_q = sum(round_qualities) / len(round_qualities) if round_qualities else 0
            round_results.append({
                "round": round_num,
                "avg_quality": round(avg_q, 4),
                "payloads": len(round_qualities),
            })

            if (round_num + 1) % 10 == 0 or round_num == 0:
                print(
                    f"  Round {round_num+1}/{num_rounds} | "
                    f"avg_quality={avg_q:.3f}",
                    flush=True,
                )

        # Compute cell summary
        divergence_count = sum(1 for d in routing_decisions if d["diverged"])
        divergence_rate = divergence_count / len(routing_decisions) if routing_decisions else 0

        avg_quality = total_quality / total_assigned if total_assigned else 0

        # Operator fluency profiles
        fluency_profiles = {}
        for agent in self.pool.agents:
            if agent.operator_fluency:
                fluency_profiles[agent.agent_id] = {
                    op: {
                        "count": prof["count"],
                        "quality_sum": round(prof["quality_sum"], 4),
                    }
                    for op, prof in agent.operator_fluency.items()
                }

        # Mass snapshot
        mass_snapshot = mass_tracker.snapshot(self.pool.agents)

        # Per-agent solve counts
        agent_solves = {}
        for d in routing_decisions:
            aid = d["agent"]
            agent_solves[aid] = agent_solves.get(aid, 0) + 1

        print(
            f"  Final: quality={avg_quality:.3f} | "
            f"divergence={divergence_rate:.1%} ({divergence_count}/{len(routing_decisions)})",
            flush=True,
        )

        return {
            "cell": cell_id,
            "label": label,
            "continuous_d": use_continuous_d,
            "sublinear": use_sublinear,
            "num_rounds": num_rounds,
            "total_assignments": total_assigned,
            "avg_quality": round(avg_quality, 4),
            "divergence_rate": round(divergence_rate, 4),
            "divergence_count": divergence_count,
            "agent_solves": agent_solves,
            "fluency_profiles": fluency_profiles,
            "mass_snapshot": mass_snapshot,
            "rounds": round_results,
            "routing_decisions": routing_decisions,
        }

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def execute(self) -> dict:
        """Run all four cells of the 2×2 factorial."""
        num_rounds = self.config.num_rounds
        payloads_per_round = self.config.payloads_per_round
        seed = self.config.seed

        print(
            f"\nPhase 2 GPSL Experiment: 2×2 factorial",
            flush=True,
        )
        print(
            f"  {num_rounds} rounds × {payloads_per_round} payloads/round × 4 cells",
            flush=True,
        )
        print(
            f"  GPSL payloads: {len(self.payloads)}",
            flush=True,
        )
        print(
            f"  Agents: {[a.agent_id for a in self.pool.agents]}",
            flush=True,
        )

        results = {}
        for cell_id, cell_cfg in CELLS.items():
            cell_result = await self._run_cell(
                cell_id, cell_cfg, num_rounds, payloads_per_round, seed,
            )
            results[cell_id] = cell_result

        await self.client.close()

        # Save results
        self.output_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.output_dir / "gpsl_results.json"
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {out_path}", flush=True)

        # Summary
        print(f"\n{'='*60}")
        print("PHASE 2 SUMMARY")
        print(f"{'='*60}")
        print(f"  {'Cell':<6}{'Quality':>10}{'Divergence':>12}{'Label'}")
        print(f"  {'-'*60}")
        for cell_id, r in results.items():
            print(
                f"  {cell_id:<6}{r['avg_quality']:>10.3f}"
                f"{r['divergence_rate']:>11.1%}  {r['label']}"
            )

        return results
