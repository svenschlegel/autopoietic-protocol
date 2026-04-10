"""Cross-algorithm analysis — Gini, specialization, comparison."""

from __future__ import annotations

from node_client.core.types import FrictionType
from simulation.agents.sim_agent import SimAgent
from simulation.metrics.collector import MetricsCollector


def gini_coefficient(values: list[float]) -> float:
    """Compute Gini coefficient. 0 = perfect equality, 1 = total inequality."""
    if not values or all(v == 0 for v in values):
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    numerator = sum((2 * i - n + 1) * v for i, v in enumerate(sorted_vals))
    denominator = n * sum(sorted_vals)
    if denominator == 0:
        return 0.0
    return numerator / denominator


def specialization_index(agents: list[SimAgent]) -> dict[str, float]:
    """Per agent: max domain mass / total mass. Higher = more specialized."""
    result = {}
    for agent in agents:
        total = agent.aggregate_mass
        if total <= 0:
            result[agent.agent_id] = 0.0
            continue
        max_domain = max(agent.mass.values())
        result[agent.agent_id] = max_domain / total
    return result


def domain_dominance(agents: list[SimAgent]) -> dict[str, dict]:
    """Per domain: top agent's mass share and HHI concentration."""
    result = {}
    for ft in FrictionType:
        masses = [(a.agent_id, a.domain_mass(ft)) for a in agents]
        total = sum(m for _, m in masses)
        if total <= 0:
            result[ft.name] = {"top_agent": None, "top_share": 0.0, "hhi": 0.0}
            continue

        masses.sort(key=lambda x: x[1], reverse=True)
        top_agent, top_mass = masses[0]
        shares = [(m / total) for _, m in masses]
        hhi = sum(s ** 2 for s in shares)

        result[ft.name] = {
            "top_agent": top_agent,
            "top_share": round(top_mass / total, 4),
            "hhi": round(hhi, 4),
        }
    return result


def gini_over_time(collector: MetricsCollector) -> list[dict]:
    """Gini coefficient at each round from mass snapshots."""
    trajectory = []
    for r in collector.rounds:
        masses = [
            info["aggregate_mass"]
            for info in r.mass_snapshot.values()
        ]
        trajectory.append({
            "round": r.round_num,
            "gini": round(gini_coefficient(masses), 4),
        })
    return trajectory


def quality_over_time(collector: MetricsCollector) -> list[dict]:
    """Average quality at each round."""
    trajectory = []
    for r in collector.rounds:
        scores = [p.quality_score for p in r.payloads if p.assigned_agent]
        avg = sum(scores) / len(scores) if scores else 0.0
        trajectory.append({
            "round": r.round_num,
            "avg_quality": round(avg, 4),
        })
    return trajectory


def compare_algorithms(results: dict[str, MetricsCollector]) -> dict:
    """Cross-algorithm comparison table."""
    summaries = {name: coll.summary_stats() for name, coll in results.items()}

    # Find winners
    quality_winner = max(summaries, key=lambda k: summaries[k].get("avg_quality", 0))
    throughput_winner = max(summaries, key=lambda k: summaries[k].get("throughput", 0))

    # Gini from final snapshots
    gini_scores = {}
    for name, summary in summaries.items():
        snap = summary.get("final_mass_snapshot", {})
        masses = [info["aggregate_mass"] for info in snap.values()] if snap else []
        gini_scores[name] = gini_coefficient(masses)

    most_equal = min(gini_scores, key=gini_scores.get) if gini_scores else None

    return {
        "algorithms": summaries,
        "gini_final": {k: round(v, 4) for k, v in gini_scores.items()},
        "comparison": {
            "quality_winner": quality_winner,
            "throughput_winner": throughput_winner,
            "most_equal": most_equal,
        },
    }
