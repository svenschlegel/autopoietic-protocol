"""
Phase 1 multi-seed variance aggregation.

Loads all seed runs for treatments A (control) and C (sublinear+rebase)
from `results/phase1_<treatment>/seed<N>/run-*/results.json`, computes the
headline Phase 1 metrics for each, and reports mean ± std across seeds.

The point: lock the single-seed Phase 1 result against accusations of
cherry-picking. If treatment A's monopoly forms across all 3 seeds and
treatment C's reform validates across all 3 seeds with low variance,
the empirical claim is robust enough to ship in the V3.5 spec.

Run:
    python3 simulation/analysis/phase1_variance.py
    python3 simulation/analysis/phase1_variance.py --seeds 1 7 13
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean, median, pstdev

REPO_ROOT = Path(__file__).resolve().parents[2]
DOMAINS = ["SEMANTIC", "DETERMINISTIC", "SPATIAL", "TEMPORAL"]

# Reuse the per-treatment analysis from phase1_compare to keep one source of truth.
sys.path.insert(0, str(REPO_ROOT))
from simulation.analysis.phase1_compare import (  # noqa: E402
    analyze_treatment, latest_run_dir, load_run, fmt_ratio,
)

TREATMENTS = ("phase1_a_control", "phase1_c_sublinear_rebase")
TREATMENT_LABELS = {
    "phase1_a_control": "A: control (V3.4)",
    "phase1_c_sublinear_rebase": "C: sublinear+rebase",
}


def find_seed_runs(treatment: str, seeds: list[int]) -> list[tuple[int, Path]]:
    """For each requested seed, return (seed, latest run dir under that seed)."""
    base = REPO_ROOT / "results" / treatment
    out: list[tuple[int, Path]] = []
    for s in seeds:
        seed_parent = base / f"seed{s}"
        d = latest_run_dir(seed_parent)
        if d is not None:
            out.append((s, d))
    return out


def stats(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    return mean(values), pstdev(values)


def fmt_meanstd(m: float, s: float, fmt: str = ".3f") -> str:
    return f"{m:{fmt}} ± {s:{fmt}}"


def aggregate_treatment(name: str, seed_runs: list[tuple[int, Path]]) -> dict:
    """Run analyze_treatment on each seed run, then aggregate."""
    per_seed = []
    for seed, run_dir in seed_runs:
        blob = load_run(run_dir)
        if blob is None:
            continue
        analysis = analyze_treatment(name, run_dir, blob)
        analysis["seed"] = seed
        per_seed.append(analysis)
    return {"name": name, "label": TREATMENT_LABELS.get(name, name), "per_seed": per_seed}


def report(treatments: list[dict]) -> None:
    print()
    print("=" * 90)
    print("Phase 1 multi-seed variance — V3.5 mass-accrual reform")
    print("=" * 90)

    for t in treatments:
        ps = t["per_seed"]
        if not ps:
            print(f"\n--- {t['label']} --- NO SEEDS FOUND")
            continue

        seeds = [s["seed"] for s in ps]
        print(f"\n--- {t['label']} ---  ({len(ps)} seeds: {seeds})")

        # Per-seed line
        print(f"  {'seed':<6}{'quality':>10}{'throughput':>12}{'agg Gini':>12}{'#≥5':>7}")
        for s in ps:
            print(f"  {s['seed']:<6}{s['avg_quality']:>10.3f}{s['throughput']:>12.3f}"
                  f"{s['aggregate_gini']:>12.3f}{s['participation_ge5']:>7d}/10")

        # Aggregates
        q_m, q_s = stats([s["avg_quality"] for s in ps])
        t_m, t_s = stats([s["throughput"]  for s in ps])
        g_m, g_s = stats([s["aggregate_gini"] for s in ps])
        p_m, p_s = stats([float(s["participation_ge5"]) for s in ps])
        print(f"  {'mean':<6}{q_m:>10.3f}{t_m:>12.3f}{g_m:>12.3f}{p_m:>7.1f}/10")
        print(f"  {'std':<6}{q_s:>10.3f}{t_s:>12.3f}{g_s:>12.3f}{p_s:>7.2f}")

        # Per-domain naive top:median across seeds
        print(f"  per-domain top:median across seeds (naive — incl. dormant):")
        print(f"    {'domain':<14}{'min':>10}{'max':>10}{'mean':>12}")
        for d in DOMAINS:
            vals = [s["monopoly"][d]["top_to_median"] for s in ps]
            m, sd = stats(vals)
            print(f"    {d:<14}{fmt_ratio(min(vals)):>10}{fmt_ratio(max(vals)):>10}  {fmt_ratio(m):>10}")

        # Per-domain ACTIVE top:median across seeds
        print(f"  per-domain top:active-median across seeds (n_solves≥2):")
        print(f"    {'domain':<14}{'min':>10}{'max':>10}{'mean':>12}")
        for d in DOMAINS:
            vals = [s["monopoly"][d]["top_to_active_median"] for s in ps]
            m, sd = stats(vals)
            print(f"    {d:<14}{fmt_ratio(min(vals)):>10}{fmt_ratio(max(vals)):>10}  {fmt_ratio(m):>10}")

        # Rebase boundary stability (only meaningful for C)
        boundaries = [s["boundary"] for s in ps if s.get("boundary")]
        if boundaries:
            dips = [b["q_dip"] for b in boundaries]
            print(f"  rebase boundary quality Δ across seeds: min={min(dips):+.3f}  max={max(dips):+.3f}  mean={mean(dips):+.3f}")

    # Cross-treatment robustness summary
    print()
    print("=" * 90)
    print("Cross-treatment robustness summary")
    print("=" * 90)
    a = next((t for t in treatments if t["name"] == "phase1_a_control"), None)
    c = next((t for t in treatments if t["name"] == "phase1_c_sublinear_rebase"), None)
    if not a or not c or not a["per_seed"] or not c["per_seed"]:
        print("(both treatments need at least one seed each)")
        return

    a_q = [s["avg_quality"] for s in a["per_seed"]]
    c_q = [s["avg_quality"] for s in c["per_seed"]]
    a_g = [s["aggregate_gini"] for s in a["per_seed"]]
    c_g = [s["aggregate_gini"] for s in c["per_seed"]]
    a_p = [s["participation_ge5"] for s in a["per_seed"]]
    c_p = [s["participation_ge5"] for s in c["per_seed"]]

    a_q_m, a_q_s = stats(a_q); c_q_m, c_q_s = stats(c_q)
    a_g_m, a_g_s = stats(a_g); c_g_m, c_g_s = stats(c_g)
    a_p_m, a_p_s = stats([float(x) for x in a_p]); c_p_m, c_p_s = stats([float(x) for x in c_p])

    print()
    print(f"  {'metric':<24}{'A (control)':>22}{'C (reform)':>22}{'Δ (C - A)':>16}")
    print(f"  {'-'*82}")
    print(f"  {'avg quality':<24}{fmt_meanstd(a_q_m, a_q_s):>22}{fmt_meanstd(c_q_m, c_q_s):>22}{c_q_m - a_q_m:>+16.3f}")
    print(f"  {'aggregate Gini':<24}{fmt_meanstd(a_g_m, a_g_s):>22}{fmt_meanstd(c_g_m, c_g_s):>22}{c_g_m - a_g_m:>+16.3f}")
    print(f"  {'participation (#≥5)':<24}{fmt_meanstd(a_p_m, a_p_s, '.1f'):>22}{fmt_meanstd(c_p_m, c_p_s, '.1f'):>22}{c_p_m - a_p_m:>+16.1f}")

    # Worst-domain top:median (naive and active) across all seeds
    a_worst_naive = max(max(s["monopoly"][d]["top_to_median"] for d in DOMAINS) for s in a["per_seed"])
    c_worst_naive = max(max(s["monopoly"][d]["top_to_median"] for d in DOMAINS) for s in c["per_seed"])
    a_worst_active = max(max(s["monopoly"][d]["top_to_active_median"] for d in DOMAINS) for s in a["per_seed"])
    c_worst_active = max(max(s["monopoly"][d]["top_to_active_median"] for d in DOMAINS) for s in c["per_seed"])
    print()
    print(f"  worst-domain top:median (naive)   A: {fmt_ratio(a_worst_naive).strip():>8}   C: {fmt_ratio(c_worst_naive).strip():>8}")
    print(f"  worst-domain top:active-median    A: {fmt_ratio(a_worst_active).strip():>8}   C: {fmt_ratio(c_worst_active).strip():>8}")

    # Quality-cost-of-reform robustness
    q_cost_pct = (a_q_m - c_q_m) / a_q_m * 100 if a_q_m else 0
    print()
    print(f"  quality cost of reform: {q_cost_pct:.2f}% (spec guardrail: <10%)")
    print(f"  Gini compression:        {(1 - c_g_m / a_g_m) * 100:.1f}% reduction")
    print(f"  participation broadening: +{c_p_m - a_p_m:.1f} agents (mean across seeds)")
    print()

    # Robustness verdict
    q_overlap = abs(c_q_m - a_q_m) > 2 * (a_q_s + c_q_s)  # bands separated
    g_overlap = abs(c_g_m - a_g_m) > 2 * (a_g_s + c_g_s)
    print(f"  quality bands separated (>2σ apart)? {'YES' if q_overlap else 'NO — overlap'}")
    print(f"  Gini bands separated   (>2σ apart)? {'YES' if g_overlap else 'NO — overlap'}")
    print()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", type=int, default=[1, 7, 13],
                    help="Seeds to aggregate (default: 1 7 13)")
    args = ap.parse_args()

    treatments = []
    for name in TREATMENTS:
        seed_runs = find_seed_runs(name, args.seeds)
        treatments.append(aggregate_treatment(name, seed_runs))

    n_runs = sum(len(t["per_seed"]) for t in treatments)
    if n_runs == 0:
        print(f"No seed runs found under results/phase1_*/seed{{{','.join(map(str, args.seeds))}}}/.")
        print("Run the multiseed batch first.")
        return 1

    report(treatments)
    return 0


if __name__ == "__main__":
    sys.exit(main())
