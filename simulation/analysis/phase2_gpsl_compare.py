"""
Phase 2 — GPSL experiment cross-cell comparison.

Loads gpsl_results.json and produces a side-by-side report on the
2×2 factorial: {categorical D, continuous D} × {linear, sublinear}.

Key metrics:
- Routing divergence: how often does continuous-D pick a different agent?
- Quality: does continuous-D produce better solutions?
- Operator fluency: do agents develop differentiated profiles?
- Monopoly: does any agent dominate all operators within Spatial?

Run:
    python3 simulation/analysis/phase2_gpsl_compare.py
    python3 simulation/analysis/phase2_gpsl_compare.py --results path/to/gpsl_results.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS = REPO_ROOT / "results" / "phase2_gpsl"


def load_results(path: Path) -> dict | None:
    if path.is_dir():
        candidates = sorted(p for p in path.iterdir() if p.is_dir() and p.name.startswith("run-"))
        if candidates:
            f = candidates[-1] / "gpsl_results.json"
            if f.exists():
                return json.loads(f.read_text())
        f = path / "gpsl_results.json"
        if f.exists():
            return json.loads(f.read_text())
    elif path.is_file():
        return json.loads(path.read_text())
    return None


def report(data: dict) -> None:
    print()
    print("=" * 80)
    print("Phase 2 — GPSL Cipher Encoding: 2×2 Factorial Comparison")
    print("=" * 80)

    # Cell summary
    print()
    print(f"  {'Cell':<6}{'Quality':>10}{'Divergence':>12}{'Assigns':>10}  Label")
    print(f"  {'-'*72}")
    for cell_id in ["A", "B", "C", "D"]:
        r = data.get(cell_id, {})
        print(
            f"  {cell_id:<6}"
            f"{r.get('avg_quality', 0):>10.3f}"
            f"{r.get('divergence_rate', 0):>11.1%}"
            f"{r.get('total_assignments', 0):>10d}"
            f"  {r.get('label', '?')}"
        )

    # Key comparisons
    print()
    print("--- Key comparisons ---")

    a = data.get("A", {})
    b = data.get("B", {})
    c = data.get("C", {})
    d = data.get("D", {})

    # Phase 0-A reproduction: B vs A
    if a and b:
        div_b = b.get("divergence_rate", 0)
        q_delta = b.get("avg_quality", 0) - a.get("avg_quality", 0)
        print(f"  B vs A (continuous D under OLD accrual):")
        print(f"    divergence: {div_b:.1%}  quality Δ: {q_delta:+.3f}")
        if div_b < 0.05:
            print(f"    → Reproduces Phase 0-A: continuous D alone is inert under linear accrual")
        else:
            print(f"    → Continuous D produces {div_b:.0%} different routing decisions even under linear accrual")

    # The main test: D vs C
    if c and d:
        div_d = d.get("divergence_rate", 0)
        q_delta = d.get("avg_quality", 0) - c.get("avg_quality", 0)
        print(f"  D vs C (continuous D under REFORMED accrual):")
        print(f"    divergence: {div_d:.1%}  quality Δ: {q_delta:+.3f}")
        if div_d >= 0.10 and q_delta >= 0:
            print(f"    ✓ LAYER 3 VALIDATED: continuous D produces ≥10% routing divergence with no quality loss")
        elif div_d >= 0.10:
            print(f"    ~ Continuous D diverges ({div_d:.0%}) but quality dropped ({q_delta:+.3f})")
        else:
            print(f"    ✗ Continuous D produces <10% divergence — operator-level routing not yet meaningful")

    # Reform effect: C vs A
    if a and c:
        q_delta = c.get("avg_quality", 0) - a.get("avg_quality", 0)
        print(f"  C vs A (reform effect, categorical D):")
        print(f"    quality Δ: {q_delta:+.3f}")

    # Full stack vs control: D vs A
    if a and d:
        q_delta = d.get("avg_quality", 0) - a.get("avg_quality", 0)
        div_d = d.get("divergence_rate", 0)
        print(f"  D vs A (full stack vs V3.4 control):")
        print(f"    quality Δ: {q_delta:+.3f}  divergence: {div_d:.1%}")

    # Agent solve distribution per cell
    print()
    print("--- Agent solve distribution ---")
    for cell_id in ["A", "B", "C", "D"]:
        r = data.get(cell_id, {})
        solves = r.get("agent_solves", {})
        if solves:
            total = sum(solves.values())
            top_agent = max(solves, key=solves.get)
            top_share = solves[top_agent] / total if total else 0
            active = sum(1 for v in solves.values() if v >= 5)
            print(
                f"  Cell {cell_id}: top={top_agent} ({top_share:.0%} of work) | "
                f"active (≥5 solves): {active}/{len(solves)}"
            )

    # Operator fluency profiles (Cell D only — the interesting one)
    d_fluency = data.get("D", {}).get("fluency_profiles", {})
    if d_fluency:
        print()
        print("--- Operator fluency profiles (Cell D: full stack) ---")

        # Collect all operators seen
        all_ops = set()
        for agent_id, profile in d_fluency.items():
            all_ops.update(profile.keys())
        all_ops = sorted(all_ops)

        if all_ops:
            # Header
            header = f"  {'Agent':<18}"
            for op in all_ops[:10]:  # limit columns
                header += f"{op:>6}"
            print(header)
            print(f"  {'-'*len(header)}")

            for agent_id, profile in sorted(d_fluency.items()):
                row = f"  {agent_id:<18}"
                for op in all_ops[:10]:
                    count = profile.get(op, {}).get("count", 0)
                    row += f"{count:>6}"
                print(row)

            # Check differentiation
            agent_op_sets = {}
            for agent_id, profile in d_fluency.items():
                top_ops = sorted(profile.keys(), key=lambda o: profile[o]["count"], reverse=True)[:3]
                agent_op_sets[agent_id] = set(top_ops)

            # How many unique top-3 operator sets?
            unique_profiles = len(set(frozenset(s) for s in agent_op_sets.values()))
            print(f"\n  Unique top-3 operator profiles: {unique_profiles}/{len(d_fluency)}")
            if unique_profiles > len(d_fluency) // 2:
                print(f"  ✓ Agents developed differentiated operator-level specializations")
            else:
                print(f"  ✗ Agents converged on similar operator profiles — no differentiation")

    # Divergence by operator complexity
    d_decisions = data.get("D", {}).get("routing_decisions", [])
    if d_decisions:
        print()
        print("--- Divergence by operator complexity (Cell D) ---")
        base_divs = [d for d in d_decisions if len(d.get("operators", [])) <= 5]
        adv_divs = [d for d in d_decisions if len(d.get("operators", [])) > 5]

        if base_divs:
            base_rate = sum(1 for d in base_divs if d["diverged"]) / len(base_divs)
            base_q = mean([d["quality"] for d in base_divs]) if base_divs else 0
            print(f"  Base operators (≤5 ops): divergence={base_rate:.1%} quality={base_q:.3f} (n={len(base_divs)})")
        if adv_divs:
            adv_rate = sum(1 for d in adv_divs if d["diverged"]) / len(adv_divs)
            adv_q = mean([d["quality"] for d in adv_divs]) if adv_divs else 0
            print(f"  Advanced (>5 ops):       divergence={adv_rate:.1%} quality={adv_q:.3f} (n={len(adv_divs)})")

    # Pass/fail
    print()
    print("=" * 80)
    print("Phase 2 spec pass/fail (PHASE2_WORKPLAN.md §2.4)")
    print("=" * 80)
    if c and d:
        div_d = d.get("divergence_rate", 0)
        q_c = c.get("avg_quality", 0)
        q_d = d.get("avg_quality", 0)
        div_pass = div_d >= 0.10
        q_pass = q_d >= q_c
        print(f"  Must-have #1: Cell D divergence ≥10%: {div_d:.1%} {'PASS' if div_pass else 'FAIL'}")
        print(f"  Must-have #2: Cell D quality ≥ Cell C: {q_d:.3f} vs {q_c:.3f} {'PASS' if q_pass else 'FAIL'}")
        if div_pass and q_pass:
            print(f"\n  ✓ LAYER 3 VALIDATED — operator-level continuous D produces meaningful routing")
            print(f"    differentiation under the reformed mass distribution with no quality loss.")
        elif div_pass:
            print(f"\n  ~ Divergence confirmed but quality dropped. Continuous D routes differently")
            print(f"    but not necessarily better. Investigate operator-quality correlation.")
        else:
            print(f"\n  ✗ Continuous D does not yet produce ≥10% routing divergence.")
            print(f"    Consider: more rounds, more payloads, different mismatch function shape.")
    print()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    args = ap.parse_args()

    data = load_results(args.results)
    if data is None:
        print(f"No gpsl_results.json found at {args.results}")
        return 1

    report(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
