"""Operator-level fluency distance computation.

Computes continuous topographic distance D ∈ [0, 3] from the structural
mismatch between an agent's operator fluency profile and a payload's
required operators. Replaces categorical D ∈ {0.0, 0.5, 2.0} for GPSL-
encoded payloads.

See: MASS_ACCRUAL_REFORM_v0.1.md §3.1
     PHASE2_WORKPLAN.md §1.3
     GPSL_INTEGRATION_PROPOSAL.md §3 Layer 3
"""

from __future__ import annotations

import math


def fluency_score(count: int, quality_sum: float) -> float:
    """Compute a single fluency score in [0, 1] from solve count + quality.

    fluency = avg_quality × log(1 + count) / log(11)

    At 0 solves:  0.0
    At 1 solve q=1.0:  0.289
    At 5 solves q=1.0: 0.749
    At 10 solves q=1.0: 1.0 (saturates)
    At 5 solves q=0.5:  0.374
    """
    if count == 0:
        return 0.0
    avg_quality = quality_sum / count
    raw = avg_quality * math.log(1 + count) / math.log(11)
    return min(raw, 1.0)


def continuous_distance(
    agent_fluency: dict[str, dict],
    required_operators: list[str],
) -> float:
    """Compute D ∈ [0, 3] from operator-level fluency mismatch.

    D = (1 / |required_ops|) × Σ max(0, 3 - fluency_score(op) × 3)

    An agent fluent in every required operator has D ≈ 0.
    An agent fluent in none has D ≈ 3.
    An agent fluent in half has D ≈ 1.5.

    Args:
        agent_fluency: dict mapping operator strings to
            {"count": int, "quality_sum": float}
        required_operators: list of operator strings the payload uses

    Returns:
        Distance in [0.0, 3.0]
    """
    if not required_operators:
        return 0.0

    total_gap = 0.0
    for op in required_operators:
        profile = agent_fluency.get(op, {"count": 0, "quality_sum": 0.0})
        f = fluency_score(profile["count"], profile["quality_sum"])
        total_gap += max(0.0, 3.0 - f * 3.0)

    return total_gap / len(required_operators)
