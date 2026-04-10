"""
Phase 1 cross-treatment comparison.

Loads the most recent run directory under each of:
    results/phase1_a_control/
    results/phase1_b_sublinear/
    results/phase1_c_sublinear_rebase/
    results/phase1_d_full_stack/

…and produces a side-by-side report on the metrics that matter for the
mass accrual reform: monopoly formation, participation, quality, and the
behavior of the rebase boundary at round 49→50 for treatments C and D.

Per docs/MASS_ACCRUAL_REFORM_v0.1.md §8.2, the four questions Phase 1
must answer:

  1. Does the Phase 0-A monopoly disappear under the reform?
     Specifically: at the end of 100 rounds, is any single agent's
     M_route greater than 10× the median?
  2. Does quality survive the reform?
     Specifically: avg quality within 10% of the original 2026-04-04 result.
  3. Does participation broaden?
     Specifically: how many of 10 agents solve at least 5 payloads?
  4. Does the rebase event cause catastrophic disruption?
     Look for quality dips around the boundary.

Run:
    python3 simulation/analysis/phase1_compare.py
    python3 simulation/analysis/phase1_compare.py --runs <dir1> <dir2> ...

Stdlib only. Reads results.json files in the existing schema (with the
new V3.5 dual-mass keys; falls back to legacy `per_domain` if needed).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean, median

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PARENTS = [
    REPO_ROOT / "results" / "phase1_a_control",
    REPO_ROOT / "results" / "phase1_b_sublinear",
    REPO_ROOT / "results" / "phase1_c_sublinear_rebase",
    REPO_ROOT / "results" / "phase1_d_full_stack",
]
DOMAINS = ["SEMANTIC", "DETERMINISTIC", "SPATIAL", "TEMPORAL"]

# === Treatment metadata ===
# (label, expected behavior, season_length used) — used for the report header.
TREATMENTS = {
    "phase1_a_control":          ("A: control (V3.4)",       "monopoly expected",                    None),
    "phase1_b_sublinear":        ("B: sublinear",            "monopoly slowed but persists",         None),
    "phase1_c_sublinear_rebase": ("C: sublinear+rebase",     "V3.5 ship config; 1 mid-run rebase",   50),
    "phase1_d_full_stack":       ("D: full stack +decay",    "exploratory; tiny δ=0.001 active",     50),
}


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def latest_run_dir(parent: Path) -> Path | None:
    """Return the most recent run-* subdirectory inside `parent`."""
    if not parent.is_dir():
        return None
    candidates = sorted(p for p in parent.iterdir() if p.is_dir() and p.name.startswith("run-"))
    return candidates[-1] if candidates else None


def load_run(run_dir: Path) -> dict | None:
    """Load results.json from a run directory."""
    f = run_dir / "results.json"
    if not f.exists():
        return None
    return json.loads(f.read_text())


def get_routing_per_domain(snapshot_entry: dict) -> dict[str, float]:
    """Extract per-domain routing mass from a snapshot entry, supporting both
    the V3.5 explicit key and the legacy alias."""
    return snapshot_entry.get("per_domain_routing") or snapshot_entry.get("per_domain") or {}


def get_governance_per_domain(snapshot_entry: dict) -> dict[str, float]:
    """Extract per-domain governance mass; returns empty dict if not present
    (pre-V3.5 results.json)."""
    return snapshot_entry.get("per_domain_governance") or {}


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def gini(values: list[float]) -> float:
    if not values or all(v == 0 for v in values):
        return 0.0
    s = sorted(values)
    n = len(s)
    num = sum((2 * i - n + 1) * v for i, v in enumerate(s))
    den = n * sum(s)
    return num / den if den > 0 else 0.0


def top_to_median_ratio(values: list[float]) -> float:
    """How many times larger is the top value than the median?
    A value of 1.0 means perfect equality at the top; ≥10 means runaway."""
    if not values:
        return 0.0
    m = median(values)
    if m <= 0:
        return float("inf")
    return max(values) / m


def participation_count(payload_results: list[dict], threshold: int = 5) -> int:
    """How many distinct agents solved (quality >= 0.5) at least `threshold` payloads."""
    counts: dict[str, int] = {}
    for p in payload_results:
        if p.get("assigned_agent") and p.get("quality_score", 0) >= 0.5:
            counts[p["assigned_agent"]] = counts.get(p["assigned_agent"], 0) + 1
    return sum(1 for c in counts.values() if c >= threshold)


def solves_per_agent_domain(payload_results: list[dict], min_quality: float = 0.5) -> dict[str, dict[str, int]]:
    """Count successful solves for each (agent, domain) pair."""
    out: dict[str, dict[str, int]] = {}
    for p in payload_results:
        aid = p.get("assigned_agent")
        if not aid or p.get("quality_score", 0) < min_quality:
            continue
        out.setdefault(aid, {}).setdefault(p["domain"], 0)
        out[aid][p["domain"]] += 1
    return out


def quality_window(payloads: list[dict], lo: int, hi: int) -> float:
    """Average quality of assigned-and-not-failed payloads in rounds [lo, hi)."""
    pool = [p["quality_score"] for p in payloads
            if p.get("assigned_agent") and p.get("round_num_internal", -1) in range(lo, hi)
            and p.get("quality_score", 0) >= 0]
    return mean(pool) if pool else 0.0


# ---------------------------------------------------------------------------
# Per-treatment analysis
# ---------------------------------------------------------------------------

def analyze_treatment(name: str, run_dir: Path, results_blob: dict) -> dict:
    """Compute all the Phase 1 metrics for one treatment."""
    label, expectation, season_length = TREATMENTS.get(name, (name, "?", None))

    # Phase 1 configs run gravitational only — but tolerate multi-router runs.
    grav = next((a for a in results_blob["algorithms"] if a["algorithm"] == "gravitational"), None)
    if grav is None:
        return {"name": name, "label": label, "error": "no gravitational algorithm in results"}

    rounds = grav["rounds"]
    n_rounds = len(rounds)

    # Flatten payloads, tagging each with its round
    flat_payloads: list[dict] = []
    for r in rounds:
        for p in r["payloads"]:
            p2 = dict(p)
            p2["round_num_internal"] = r["round_num"]
            flat_payloads.append(p2)

    # Final routing-mass distribution from the last round's snapshot
    final_snap = rounds[-1]["mass_snapshot"]
    per_domain_routing: dict[str, list[float]] = {d: [] for d in DOMAINS}
    per_domain_gov: dict[str, list[float]] = {d: [] for d in DOMAINS}
    final_routing_mass: dict[str, dict[str, float]] = {}
    final_gov_mass: dict[str, dict[str, float]] = {}

    for agent_id, entry in final_snap.items():
        rdom = get_routing_per_domain(entry)
        gdom = get_governance_per_domain(entry)
        final_routing_mass[agent_id] = rdom
        final_gov_mass[agent_id] = gdom
        for d in DOMAINS:
            per_domain_routing[d].append(float(rdom.get(d, 0.0)))
            if gdom:
                per_domain_gov[d].append(float(gdom.get(d, 0.0)))

    # Per-domain monopoly metrics, with both naive and active-only views.
    # "Active in domain d" = solved ≥ 2 payloads in d at quality ≥ 0.5.
    # The active-only view strips out agents whose post-rebase routing mass
    # is dominated by the rebase floor rather than by earned signal — that's
    # the population the routing formula actually competes within.
    solves_by_ad = solves_per_agent_domain(flat_payloads)
    ACTIVE_THRESHOLD = 2
    monopoly = {}
    for d in DOMAINS:
        vals = per_domain_routing[d]
        active_agents = {aid for aid, dmap in solves_by_ad.items()
                         if dmap.get(d, 0) >= ACTIVE_THRESHOLD}
        active_vals = [final_routing_mass[aid].get(d, 0.0) for aid in active_agents
                       if aid in final_routing_mass]
        monopoly[d] = {
            "max": max(vals) if vals else 0.0,
            "median": median(vals) if vals else 0.0,
            "top_to_median": top_to_median_ratio(vals),
            "n_active": len(active_vals),
            "active_median": median(active_vals) if active_vals else 0.0,
            "top_to_active_median": top_to_median_ratio(active_vals) if active_vals else float("inf"),
            "active_gini": gini(active_vals),
            "gini": gini(vals),
            "top_agent": max(final_routing_mass.items(),
                             key=lambda kv: kv[1].get(d, 0.0))[0] if final_routing_mass else None,
        }

    # Aggregate-routing-mass Gini across all agents (sum across domains)
    agent_aggregates = [sum(rmap.values()) for rmap in final_routing_mass.values()]
    aggregate_gini = gini(agent_aggregates)

    # Quality and throughput
    qualities = [p["quality_score"] for p in flat_payloads
                 if p.get("assigned_agent") and p.get("quality_score", 0) >= 0]
    avg_quality = mean(qualities) if qualities else 0.0
    solved = sum(1 for p in flat_payloads if p.get("quality_score", 0) >= 0.5)
    throughput = solved / len(flat_payloads) if flat_payloads else 0.0

    # Participation
    participation = participation_count(flat_payloads, threshold=5)

    # Rebase boundary effect — only meaningful if a season fired
    boundary = None
    if season_length and n_rounds > season_length:
        # Last 10 rounds before rebase vs first 10 rounds after.
        pre_lo = max(0, season_length - 10)
        pre_hi = season_length
        post_lo = season_length
        post_hi = min(n_rounds, season_length + 10)
        q_pre = quality_window(flat_payloads, pre_lo, pre_hi)
        q_post = quality_window(flat_payloads, post_lo, post_hi)
        # Did the top mass agent change before vs after the rebase?
        snap_pre = rounds[season_length - 1]["mass_snapshot"]
        snap_post = rounds[season_length]["mass_snapshot"] if n_rounds > season_length else snap_pre
        def top_agent_per_domain(snap):
            out = {}
            for d in DOMAINS:
                best, best_v = None, -1.0
                for aid, e in snap.items():
                    v = float(get_routing_per_domain(e).get(d, 0.0))
                    if v > best_v:
                        best, best_v = aid, v
                out[d] = best
            return out
        top_pre = top_agent_per_domain(snap_pre)
        top_post = top_agent_per_domain(snap_post)
        boundary = {
            "pre_window": (pre_lo, pre_hi),
            "post_window": (post_lo, post_hi),
            "q_pre": q_pre,
            "q_post": q_post,
            "q_dip": q_pre - q_post,
            "top_per_domain_pre": top_pre,
            "top_per_domain_post": top_post,
            "leadership_changed": {d: top_pre[d] != top_post[d] for d in DOMAINS},
        }

    return {
        "name": name,
        "label": label,
        "expectation": expectation,
        "season_length": season_length,
        "n_rounds": n_rounds,
        "n_payloads": len(flat_payloads),
        "monopoly": monopoly,
        "aggregate_gini": aggregate_gini,
        "avg_quality": avg_quality,
        "throughput": throughput,
        "participation_ge5": participation,
        "boundary": boundary,
        "run_dir": str(run_dir.relative_to(REPO_ROOT)) if run_dir.is_relative_to(REPO_ROOT) else str(run_dir),
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def fmt_ratio(r: float) -> str:
    if r == float("inf"):
        return "  ∞"
    if r >= 100:
        return f"{r:>5.0f}×"
    return f"{r:>5.1f}×"


def report(treatments: list[dict]) -> None:
    print()
    print("=" * 88)
    print("Phase 1 cross-treatment comparison — V3.5 mass-accrual reform")
    print("=" * 88)

    for t in treatments:
        if "error" in t:
            print(f"\n{t['label']:<28} ERROR: {t['error']}")
            continue
        print(f"\n--- {t['label']} ---")
        print(f"  expectation:   {t['expectation']}")
        print(f"  source:        {t['run_dir']}")
        print(f"  rounds:        {t['n_rounds']}  (payloads: {t['n_payloads']})")
        print(f"  avg quality:   {t['avg_quality']:.3f}")
        print(f"  throughput:    {t['throughput']:.3f}")
        print(f"  participation: {t['participation_ge5']:>2} of 10 agents solved ≥5 payloads")
        print(f"  agg Gini:      {t['aggregate_gini']:.3f}  (1.0 = total inequality)")
        print(f"  per-domain monopoly:")
        print(f"    {'domain':<14}{'top':>10}{'med':>9}{'top:med':>10}"
              f"{'#act':>5}{'act-med':>10}{'top:act':>10}  top agent")
        for d in DOMAINS:
            m = t["monopoly"][d]
            print(f"    {d:<14}{m['max']:>10.1f}{m['median']:>9.1f}"
                  f"  {fmt_ratio(m['top_to_median'])}"
                  f"{m['n_active']:>5d}{m['active_median']:>10.1f}"
                  f"  {fmt_ratio(m['top_to_active_median'])}  {m['top_agent']}")
        if t["boundary"]:
            b = t["boundary"]
            arrow = "↓" if b["q_dip"] > 0.01 else ("↑" if b["q_dip"] < -0.01 else "≈")
            print(f"  rebase boundary at round {t['season_length']}:")
            print(f"    quality pre  (R{b['pre_window'][0]}-{b['pre_window'][1]-1}):  {b['q_pre']:.3f}")
            print(f"    quality post (R{b['post_window'][0]}-{b['post_window'][1]-1}):  {b['q_post']:.3f}  {arrow} (Δ {b['q_dip']:+.3f})")
            changes = sum(1 for v in b["leadership_changed"].values() if v)
            print(f"    leadership changes across boundary: {changes}/4 domains")
            for d in DOMAINS:
                if b["leadership_changed"][d]:
                    print(f"      {d}: {b['top_per_domain_pre'][d]} → {b['top_per_domain_post'][d]}")

    # === Cross-treatment summary table ===
    print()
    print("=" * 88)
    print("Side-by-side summary")
    print("=" * 88)
    if not any("error" not in t for t in treatments):
        print("(no usable treatments to compare)")
        return
    headers = ["metric"] + [t["label"][:18] for t in treatments if "error" not in t]
    rows: list[list[str]] = []
    valid = [t for t in treatments if "error" not in t]
    rows.append(["avg quality"]    + [f"{t['avg_quality']:.3f}" for t in valid])
    rows.append(["throughput"]     + [f"{t['throughput']:.3f}"  for t in valid])
    rows.append(["participation"]  + [f"{t['participation_ge5']}/10" for t in valid])
    rows.append(["agg Gini"]       + [f"{t['aggregate_gini']:.3f}" for t in valid])
    for d in DOMAINS:
        rows.append([f"top:med {d[:6]}"] + [fmt_ratio(t['monopoly'][d]['top_to_median']).strip() for t in valid])
    # column widths
    widths = [max(len(r[i]) for r in [headers] + rows) + 2 for i in range(len(headers))]
    def fmt_row(r): return "".join(c.ljust(widths[i]) for i, c in enumerate(r))
    print(fmt_row(headers))
    print("-" * sum(widths))
    for r in rows:
        print(fmt_row(r))

    # === Pass/fail readout against the four spec questions ===
    print()
    print("=" * 88)
    print("Phase 1 spec questions (MASS_ACCRUAL_REFORM_v0.1.md §8.2)")
    print("=" * 88)
    control = next((t for t in valid if t["name"] == "phase1_a_control"), None)
    reform  = next((t for t in valid if t["name"] == "phase1_c_sublinear_rebase"), None)

    if control:
        worst_dom_ratio = max(control["monopoly"][d]["top_to_median"] for d in DOMAINS)
        print(f"  Q1 (control): does the monopoly form? "
              f"top:median in worst domain = {fmt_ratio(worst_dom_ratio).strip()} "
              f"({'YES — monopoly reproduced' if worst_dom_ratio >= 10 else 'NO — anomaly, investigate'})")
    if reform:
        worst_naive  = max(reform["monopoly"][d]["top_to_median"]        for d in DOMAINS)
        worst_active = max(reform["monopoly"][d]["top_to_active_median"] for d in DOMAINS)
        # Naive metric is misleading post-rebase: medians are dominated by
        # rebase-floor values from never-active agents. The active-median
        # metric measures the population the routing formula actually
        # competes within. Both reported.
        print(f"  Q1 (reform):  is any agent's M_route > 10× median?")
        print(f"      naive top:median  (incl. dormant): "
              f"{fmt_ratio(worst_naive).strip()} "
              f"({'PASS' if worst_naive < 10 else 'FAIL — but see active'})")
        print(f"      top:ACTIVE-median (n_solves≥2):    "
              f"{fmt_ratio(worst_active).strip()} "
              f"({'PASS — monopoly broken' if worst_active < 10 else 'FAIL — still monopolizing'})")
    if control and reform:
        q_delta = abs(reform["avg_quality"] - control["avg_quality"]) / control["avg_quality"] if control["avg_quality"] else 0
        print(f"  Q2: quality preserved within 10% of control? "
              f"|Δquality|/control = {q_delta*100:.1f}% "
              f"({'PASS' if q_delta < 0.10 else 'FAIL'})")
        part_delta = reform["participation_ge5"] - control["participation_ge5"]
        print(f"  Q3: participation broadened? "
              f"control = {control['participation_ge5']}/10, reform = {reform['participation_ge5']}/10 "
              f"(Δ = {part_delta:+d}; {'PASS' if part_delta > 0 else 'NO IMPROVEMENT'})")
    if reform and reform["boundary"]:
        b = reform["boundary"]
        catastrophic = b["q_dip"] > 0.10
        print(f"  Q4: rebase boundary catastrophic? "
              f"Δquality across R49→R50 = {b['q_dip']:+.3f} "
              f"({'FAIL — catastrophic dip' if catastrophic else 'PASS — boundary stable'})")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+",
                    help="Run directories to compare (default: most recent in results/phase1_*)")
    args = ap.parse_args()

    if args.runs:
        run_dirs = [(Path(p).name.replace("run-", "").rsplit("/", 1)[0], Path(p)) for p in args.runs]
        # Try to map provided dirs back to phase1_* parent name; fall back to dirname
        mapped: list[tuple[str, Path]] = []
        for raw in args.runs:
            p = Path(raw).resolve()
            parent_name = p.parent.name if p.parent.name.startswith("phase1_") else p.name
            mapped.append((parent_name, p))
        items = mapped
    else:
        items = []
        for parent in DEFAULT_PARENTS:
            d = latest_run_dir(parent)
            if d is not None:
                items.append((parent.name, d))
        if not items:
            print("No phase1 runs found under results/phase1_*. Run a treatment first:")
            print("  python3 simulation/run.py --config configs/phase1_a_control.yaml")
            return 1

    treatments = []
    for name, d in items:
        blob = load_run(d)
        if blob is None:
            treatments.append({"name": name, "label": TREATMENTS.get(name, (name, "?", None))[0],
                               "error": f"no results.json in {d}"})
            continue
        treatments.append(analyze_treatment(name, d, blob))

    report(treatments)
    return 0


if __name__ == "__main__":
    sys.exit(main())
