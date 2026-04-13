"""
Phase 2.5 — Composite payload cross-condition comparison.

Loads composite_results.json from a run directory and produces a
side-by-side report on the four experimental conditions:
  C1: single agent (generalist baseline)
  C2: independent specialists (concatenated, no fusion)
  C3: collaborative fusion via Seed
  C4: adversarial synthesis (critique + revision)

Key metrics: overall quality, per-domain quality, coherence,
completeness, and the revision delta (C4 - C3 draft score).

Run:
    python3 simulation/analysis/composite_compare.py
    python3 simulation/analysis/composite_compare.py --results path/to/composite_results.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean, pstdev

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS = REPO_ROOT / "results" / "composite_test"

CONDITIONS = ["C1_single", "C2_independent", "C3_fusion", "C4_adversarial", "C5_sequential", "C6_handoff", "C7_crosspollination"]
CONDITION_LABELS = {
    "C1_single": "C1: single",
    "C2_independent": "C2: indep",
    "C3_fusion": "C3: fusion",
    "C4_adversarial": "C4: advers",
    "C5_sequential": "C5: sequen",
    "C6_handoff": "C6: handoff",
    "C7_crosspollination": "C7: xpolln",
}


def load_results(path: Path) -> dict | None:
    if path.is_dir():
        # Find the most recent run dir, then composite_results.json
        candidates = sorted(p for p in path.iterdir() if p.is_dir() and p.name.startswith("run-"))
        if candidates:
            f = candidates[-1] / "composite_results.json"
            if f.exists():
                return json.loads(f.read_text())
        # Also check directly
        f = path / "composite_results.json"
        if f.exists():
            return json.loads(f.read_text())
    elif path.is_file():
        return json.loads(path.read_text())
    return None


def fmt(v: float | None) -> str:
    if v is None:
        return "  --"
    return f"{v:5.3f}"


def fmt_delta(v: float | None) -> str:
    if v is None:
        return "  --"
    return f"{v:+5.3f}"


def report(data: dict) -> None:
    payloads = data.get("payloads", [])
    if not payloads:
        print("No payloads found in results.")
        return

    print()
    print("=" * 90)
    print("Phase 2.5 — Multi-Agent Collaboration: Cross-Condition Comparison")
    print("=" * 90)
    print(f"  Payloads: {len(payloads)}")
    print()

    # Per-payload detail
    print("--- Per-payload scores ---")
    print(f"  {'payload':<20}", end="")
    for c in CONDITIONS:
        print(f"  {CONDITION_LABELS[c]:<16}", end="")
    print("  rev_delta")
    print("  " + "-" * 100)

    for p in payloads:
        pid = p.get("payload_id", "?")[:18]
        domains = "+".join(p.get("sub_domains", []))
        label = f"{pid} ({domains})"
        print(f"  {label:<20}", end="")
        for c in CONDITIONS:
            cond = p.get("conditions", {}).get(c, {})
            score = cond.get("score")
            print(f"  {fmt(score):<16}", end="")
        # Revision delta
        c4 = p.get("conditions", {}).get("C4_adversarial", {})
        delta = c4.get("revision_delta")
        print(f"  {fmt_delta(delta)}")

    # Aggregate stats
    print()
    print("--- Aggregate (mean ± std) ---")
    print(f"  {'condition':<20}{'mean':>8}{'std':>8}{'min':>8}{'max':>8}  wins")
    print("  " + "-" * 70)

    scores_by_cond: dict[str, list[float]] = {c: [] for c in CONDITIONS}
    for p in payloads:
        for c in CONDITIONS:
            s = p.get("conditions", {}).get(c, {}).get("score")
            if s is not None:
                scores_by_cond[c].append(s)

    for c in CONDITIONS:
        vals = scores_by_cond[c]
        if not vals:
            print(f"  {CONDITION_LABELS[c]:<20}  no data")
            continue
        m = mean(vals)
        s = pstdev(vals) if len(vals) > 1 else 0.0
        mn, mx = min(vals), max(vals)
        # Count wins: how many payloads this condition had the highest score
        wins = 0
        for p in payloads:
            best_score = -1
            best_cond = None
            for c2 in CONDITIONS:
                s2 = p.get("conditions", {}).get(c2, {}).get("score")
                if s2 is not None and s2 > best_score:
                    best_score = s2
                    best_cond = c2
            if best_cond == c:
                wins += 1
        print(f"  {CONDITION_LABELS[c]:<20}{m:>8.3f}{s:>8.3f}{mn:>8.3f}{mx:>8.3f}  {wins}/{len(payloads)}")

    # Revision delta analysis
    deltas = []
    for p in payloads:
        c4 = p.get("conditions", {}).get("C4_adversarial", {})
        d = c4.get("revision_delta")
        if d is not None:
            deltas.append(d)

    if deltas:
        print()
        print("--- Revision delta (C4 - C3 draft) ---")
        pos = sum(1 for d in deltas if d > 0.01)
        neg = sum(1 for d in deltas if d < -0.01)
        neutral = len(deltas) - pos - neg
        print(f"  mean: {mean(deltas):+.3f}  |  positive (helped): {pos}  |  negative (hurt): {neg}  |  neutral: {neutral}")
        if neg > pos:
            print("  ⚠ CRITIQUE DEGRADATION detected: adversarial loop hurt more than it helped")
        elif pos > neg:
            print("  ✓ Adversarial synthesis is constructive: critique loop improved results")
        else:
            print("  ≈ Adversarial synthesis is neutral: no clear directional effect")

    # Key comparisons
    print()
    print("--- Key comparisons ---")
    c1_scores = scores_by_cond["C1_single"]
    c2_scores = scores_by_cond["C2_independent"]
    c3_scores = scores_by_cond["C3_fusion"]
    c4_scores = scores_by_cond["C4_adversarial"]

    if c1_scores and c3_scores:
        c3_wins = sum(1 for a, b in zip(c1_scores, c3_scores) if b > a + 0.01)
        c1_wins = sum(1 for a, b in zip(c1_scores, c3_scores) if a > b + 0.01)
        delta_mean = mean(c3_scores) - mean(c1_scores)
        print(f"  C3 (fusion) vs C1 (single):  Δmean = {delta_mean:+.3f}  |  C3 wins {c3_wins}/{len(c1_scores)}, C1 wins {c1_wins}/{len(c1_scores)}")
        if c3_wins >= 7 and delta_mean >= 0.1:
            print("  ✓ COLLABORATION HYPOTHESIS CONFIRMED: fusion beats single-agent on ≥7/10 payloads by ≥0.1")
        elif c3_wins >= 7:
            print("  ~ Fusion wins on ≥7/10 but Δmean < 0.1 — directional but not conclusive")
        else:
            print(f"  ✗ Fusion wins on only {c3_wins}/10 — collaboration hypothesis not confirmed at this threshold")

    if c2_scores and c3_scores:
        c3_over_c2 = sum(1 for a, b in zip(c2_scores, c3_scores) if b > a + 0.01)
        delta_mean = mean(c3_scores) - mean(c2_scores)
        print(f"  C3 (fusion) vs C2 (independent):  Δmean = {delta_mean:+.3f}  |  C3 wins {c3_over_c2}/{len(c2_scores)}")
        if c3_over_c2 > len(c2_scores) // 2:
            print("  ✓ Fusion adds value beyond specialization alone")
        else:
            print("  ✗ Specialization alone may be sufficient — fusion doesn't clearly help")

    if c3_scores and c4_scores:
        c4_over_c3 = sum(1 for a, b in zip(c3_scores, c4_scores) if b > a + 0.01)
        delta_mean = mean(c4_scores) - mean(c3_scores)
        print(f"  C4 (adversarial) vs C3 (fusion):  Δmean = {delta_mean:+.3f}  |  C4 wins {c4_over_c3}/{len(c3_scores)}")
        if c4_over_c3 > len(c3_scores) // 2:
            print("  ✓ Adversarial synthesis adds value beyond basic fusion")
        else:
            print("  ✗ Adversarial synthesis does not clearly improve on fusion")

    c5_scores = scores_by_cond.get("C5_sequential", [])
    if c1_scores and c5_scores:
        c5_over_c1 = sum(1 for a, b in zip(c1_scores, c5_scores) if b > a + 0.01)
        delta_mean = mean(c5_scores) - mean(c1_scores)
        print(f"  C5 (sequential) vs C1 (single):  Δmean = {delta_mean:+.3f}  |  C5 wins {c5_over_c1}/{len(c1_scores)}")
        if c5_over_c1 >= 7 and delta_mean >= 0.1:
            print("  ✓ SEQUENTIAL PIPELINE CONFIRMED: context flow beats single-agent on ≥7/10 by ≥0.1")
        elif c5_over_c1 >= 7:
            print("  ~ Sequential wins ≥7/10 but Δmean < 0.1")
        else:
            print(f"  ✗ Sequential wins on only {c5_over_c1}/10")

    if c2_scores and c5_scores:
        c5_over_c2 = sum(1 for a, b in zip(c2_scores, c5_scores) if b > a + 0.01)
        delta_mean = mean(c5_scores) - mean(c2_scores)
        print(f"  C5 (sequential) vs C2 (independent):  Δmean = {delta_mean:+.3f}  |  C5 wins {c5_over_c2}/{len(c2_scores)}")
        if c5_over_c2 > len(c2_scores) // 2:
            print("  ✓ Context flow adds value beyond independent specialization")
        else:
            print("  ✗ Context flow does not clearly beat independent specialists")

    c6_scores = scores_by_cond.get("C6_handoff", [])
    if c2_scores and c6_scores:
        c6_over_c2 = sum(1 for a, b in zip(c2_scores, c6_scores) if b > a + 0.01)
        delta_mean = mean(c6_scores) - mean(c2_scores)
        print(f"  C6 (handoff) vs C2 (independent):  Δmean = {delta_mean:+.3f}  |  C6 wins {c6_over_c2}/{len(c2_scores)}")
        if c6_over_c2 > len(c2_scores) // 2:
            print("  ✓ Structured handoff beats independent specialization")
        else:
            print("  ✗ Structured handoff does not clearly beat independent specialists")

    c7_scores = scores_by_cond.get("C7_crosspollination", [])
    if c2_scores and c7_scores:
        c7_over_c2 = sum(1 for a, b in zip(c2_scores, c7_scores) if b > a + 0.01)
        delta_mean = mean(c7_scores) - mean(c2_scores)
        print(f"  C7 (cross-pollination) vs C2 (independent):  Δmean = {delta_mean:+.3f}  |  C7 wins {c7_over_c2}/{len(c2_scores)}")
        if c7_over_c2 > len(c2_scores) // 2:
            print("  ✓ Cross-pollination beats independent specialization")
        else:
            print("  ✗ Cross-pollination does not clearly beat independent specialists")

    # Best collaboration method overall
    collab_means = {}
    for c in ["C5_sequential", "C6_handoff", "C7_crosspollination"]:
        vals = scores_by_cond.get(c, [])
        if vals:
            collab_means[c] = mean(vals)
    if collab_means:
        best = max(collab_means, key=collab_means.get)
        print(f"\n  Best collaboration method: {CONDITION_LABELS.get(best, best)} (mean={collab_means[best]:.3f})")

    print()
    print("=" * 90)
    print("Spec pass/fail (MULTI_AGENT_COLLABORATION_SPEC.md §2.3)")
    print("=" * 90)
    if c1_scores and c3_scores:
        c3_wins = sum(1 for a, b in zip(c1_scores, c3_scores) if b > a + 0.01)
        delta = mean(c3_scores) - mean(c1_scores)
        passed = c3_wins >= 7 and delta >= 0.1
        print(f"  Must-have: C3 beats C1 on ≥7/10 payloads by ≥0.1")
        print(f"    C3 wins: {c3_wins}/10  |  Δmean: {delta:+.3f}  |  {'PASS' if passed else 'FAIL'}")
    print()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, default=DEFAULT_RESULTS,
                    help="Path to composite_results.json or directory containing it")
    args = ap.parse_args()

    data = load_results(args.results)
    if data is None:
        print(f"No composite_results.json found at {args.results}")
        print("Run the composite experiment first:")
        print("  PYTHONPATH=. python3 simulation/run_composite.py --config configs/composite_test.yaml")
        return 1

    report(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
