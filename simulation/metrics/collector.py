"""MetricsCollector — records per-round, per-payload results."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict


@dataclass
class PayloadResult:
    payload_id: str
    domain: str  # FrictionType name
    difficulty: float
    bounty: float
    assigned_agent: str | None
    agent_model: str | None
    quality_score: float
    solve_time: float
    mass_accrued: float
    was_slashed: bool
    error: str | None = None
    # --- Submission/verification data (added 2026-04-09 for Phase 0-B and operator-level fluency tracking) ---
    # All four are optional and may be None for unassigned/exception payloads.
    # See docs/MASS_ACCRUAL_REFORM_v0.1.md and docs/GPSL_INTEGRATION_PROPOSAL.md v0.3.
    prompt: str | None = None              # The task prompt sent to the agent
    answer: str | None = None              # The agent's submitted answer text
    expected_answer: str | None = None     # Tier 1 ground truth (exact match target)
    scoring_rubric: str | None = None      # Tier 2 grading rubric (LLM judge prompt)


@dataclass
class RoundResult:
    round_num: int
    routing_algorithm: str
    payloads: list[PayloadResult] = field(default_factory=list)
    mass_snapshot: dict = field(default_factory=dict)


class MetricsCollector:
    """Accumulates round-by-round results for one algorithm run."""

    def __init__(self, algorithm_name: str):
        self.algorithm_name = algorithm_name
        self.rounds: list[RoundResult] = []

    def record_round(self, result: RoundResult):
        self.rounds.append(result)

    def to_dict(self) -> dict:
        """Serialize all data for JSON export."""
        return {
            "algorithm": self.algorithm_name,
            "total_rounds": len(self.rounds),
            "rounds": [
                {
                    "round_num": r.round_num,
                    "payloads": [asdict(p) for p in r.payloads],
                    "mass_snapshot": r.mass_snapshot,
                }
                for r in self.rounds
            ],
        }

    def all_payload_results(self) -> list[PayloadResult]:
        """Flatten all payload results across rounds."""
        results = []
        for r in self.rounds:
            results.extend(r.payloads)
        return results

    def summary_stats(self) -> dict:
        """Compute aggregate statistics."""
        all_results = self.all_payload_results()
        if not all_results:
            return {"algorithm": self.algorithm_name, "total_payloads": 0}

        assigned = [r for r in all_results if r.assigned_agent is not None]
        solved = [r for r in assigned if r.quality_score >= 0.5]

        # Per-domain quality
        domain_scores: dict[str, list[float]] = {}
        for r in assigned:
            domain_scores.setdefault(r.domain, []).append(r.quality_score)

        avg_quality_by_domain = {
            d: sum(scores) / len(scores) for d, scores in domain_scores.items()
        }

        # Solve times
        solve_times = [r.solve_time for r in assigned if r.solve_time > 0]

        return {
            "algorithm": self.algorithm_name,
            "total_payloads": len(all_results),
            "assigned": len(assigned),
            "unassigned": len(all_results) - len(assigned),
            "avg_quality": (
                sum(r.quality_score for r in assigned) / len(assigned)
                if assigned else 0.0
            ),
            "avg_quality_by_domain": avg_quality_by_domain,
            "throughput": len(solved) / len(all_results) if all_results else 0.0,
            "median_solve_time": (
                sorted(solve_times)[len(solve_times) // 2] if solve_times else 0.0
            ),
            "total_slashed": sum(1 for r in all_results if r.was_slashed),
            "final_mass_snapshot": (
                self.rounds[-1].mass_snapshot if self.rounds else {}
            ),
        }
