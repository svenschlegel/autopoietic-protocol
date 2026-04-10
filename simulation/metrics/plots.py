"""Visualization — generates PNG plots from simulation results."""

from __future__ import annotations

from pathlib import Path

from simulation.metrics.analysis import gini_over_time, quality_over_time
from simulation.metrics.collector import MetricsCollector


def generate_all_plots(detailed_results: dict, output_dir: Path | str):
    """Generate all visualization plots."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    algo_collectors = _rebuild_collectors(detailed_results)

    _plot_quality_comparison(algo_collectors, output_dir)
    _plot_gini_over_time(algo_collectors, output_dir)
    _plot_quality_over_time(algo_collectors, output_dir)
    _plot_mass_distribution(detailed_results, output_dir)


def _rebuild_collectors(detailed: dict) -> dict[str, MetricsCollector]:
    """Rebuild MetricsCollector objects from serialized results for analysis."""
    from simulation.metrics.collector import MetricsCollector, RoundResult, PayloadResult

    collectors = {}
    for algo_data in detailed.get("algorithms", []):
        name = algo_data["algorithm"]
        coll = MetricsCollector(name)
        for r in algo_data.get("rounds", []):
            rr = RoundResult(
                round_num=r["round_num"],
                routing_algorithm=name,
                payloads=[PayloadResult(**p) for p in r["payloads"]],
                mass_snapshot=r.get("mass_snapshot", {}),
            )
            coll.record_round(rr)
        collectors[name] = coll
    return collectors


def _plot_quality_comparison(collectors: dict[str, MetricsCollector], output_dir: Path):
    """Bar chart: average quality per algorithm, grouped by domain."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Overall quality
    ax = axes[0]
    names = list(collectors.keys())
    qualities = [c.summary_stats()["avg_quality"] for c in collectors.values()]
    colors = plt.cm.Set2([i / len(names) for i in range(len(names))])
    ax.bar(names, qualities, color=colors)
    ax.set_ylabel("Average Quality Score")
    ax.set_title("Overall Quality by Algorithm")
    ax.set_ylim(0, 1)
    for i, v in enumerate(qualities):
        ax.text(i, v + 0.02, f"{v:.3f}", ha="center", fontsize=9)

    # Throughput
    ax = axes[1]
    throughputs = [c.summary_stats()["throughput"] for c in collectors.values()]
    ax.bar(names, throughputs, color=colors)
    ax.set_ylabel("Throughput (solved/total)")
    ax.set_title("Throughput by Algorithm")
    ax.set_ylim(0, 1)
    for i, v in enumerate(throughputs):
        ax.text(i, v + 0.02, f"{v:.3f}", ha="center", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_dir / "quality_comparison.png", dpi=150)
    plt.close()


def _plot_gini_over_time(collectors: dict[str, MetricsCollector], output_dir: Path):
    """Line chart: Gini coefficient per algorithm over rounds."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 5))

    for name, coll in collectors.items():
        trajectory = gini_over_time(coll)
        rounds = [t["round"] for t in trajectory]
        ginis = [t["gini"] for t in trajectory]
        ax.plot(rounds, ginis, label=name, linewidth=1.5)

    ax.set_xlabel("Round")
    ax.set_ylabel("Gini Coefficient")
    ax.set_title("Mass Concentration Over Time")
    ax.legend()
    ax.set_ylim(0, 1)
    plt.tight_layout()
    plt.savefig(output_dir / "gini_over_time.png", dpi=150)
    plt.close()


def _plot_quality_over_time(collectors: dict[str, MetricsCollector], output_dir: Path):
    """Line chart: average quality per round."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 5))

    for name, coll in collectors.items():
        trajectory = quality_over_time(coll)
        rounds = [t["round"] for t in trajectory]
        quals = [t["avg_quality"] for t in trajectory]
        ax.plot(rounds, quals, label=name, linewidth=1.5)

    ax.set_xlabel("Round")
    ax.set_ylabel("Average Quality")
    ax.set_title("Solution Quality Over Time")
    ax.legend()
    ax.set_ylim(0, 1)
    plt.tight_layout()
    plt.savefig(output_dir / "quality_over_time.png", dpi=150)
    plt.close()


def _plot_mass_distribution(detailed: dict, output_dir: Path):
    """Heatmap: final mass per agent per domain for each algorithm."""
    import matplotlib.pyplot as plt
    import numpy as np

    algo_list = detailed.get("algorithms", [])
    if not algo_list:
        return

    n_algos = len(algo_list)
    fig, axes = plt.subplots(1, n_algos, figsize=(5 * n_algos, 6))
    if n_algos == 1:
        axes = [axes]

    domains = ["SEMANTIC", "DETERMINISTIC", "SPATIAL", "TEMPORAL"]

    for idx, algo_data in enumerate(algo_list):
        ax = axes[idx]
        name = algo_data["algorithm"]
        rounds = algo_data.get("rounds", [])
        if not rounds:
            continue

        snapshot = rounds[-1].get("mass_snapshot", {})
        agents = sorted(snapshot.keys())

        matrix = []
        for agent in agents:
            info = snapshot[agent]
            row = [info["per_domain"].get(d, 0.0) for d in domains]
            matrix.append(row)

        matrix = np.array(matrix) if matrix else np.zeros((1, 4))

        im = ax.imshow(matrix, aspect="auto", cmap="YlOrRd")
        ax.set_xticks(range(len(domains)))
        ax.set_xticklabels(domains, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(agents)))
        ax.set_yticklabels(agents, fontsize=8)
        ax.set_title(name, fontsize=10)

        # Add text annotations
        for i in range(len(agents)):
            for j in range(len(domains)):
                val = matrix[i, j]
                ax.text(j, i, f"{val:.1f}", ha="center", va="center", fontsize=7)

    fig.suptitle("Final Mass Distribution (Agent x Domain)", fontsize=12)
    plt.tight_layout()
    plt.savefig(output_dir / "mass_distribution.png", dpi=150)
    plt.close()
