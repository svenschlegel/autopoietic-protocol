"""
Phase 0-A: Retrospective Continuous-Distance Routing Analysis.

Tests the Layer 3 hypothesis from docs/GPSL_INTEGRATION_PROPOSAL.md (v0.2):
would replacing categorical topographic distance D in {0.0, 0.5, 2.0}
with a continuous structural distance D in [0.0, 3.0] derived from
empirical track records change which agent wins a payload?

Method
------
- Load the existing gravitational run (results/run-2026-04-04T15-10-45)
- For each payload in each round, compute the gravitational priority
  under (a) the actual categorical D from agent subscriptions and
  (b) a continuous D derived from the agent's empirical track record
  in that domain so far.
- Hold load = 0 in both regimes to isolate the D effect.
- Compare argmax winners and characterize divergences.

Limits (be honest)
------------------
- Submission text is not stored, so this only tests Layer 3 (routing
  distance), not Layer 2 (verification noise reduction).
- Load is held at 0 in both regimes. The reconstructed categorical
  winners therefore will not always match the actual simulation winners
  (which used live load). The comparison is between two D regimes under
  identical simplifying conditions, not between this analysis and the
  ground-truth simulation.
- This is correlational. The counterfactual routing was not actually
  executed, so we cannot directly measure the quality outcome of
  alternative routing — only the strength of the would-have-been
  winner's prior track record in the relevant domain.
- Single seed (42), 200 payloads, 10 agents. Directional, not conclusive.

Run
---
    python3 simulation/analysis/phase0_continuous_distance.py
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

# --- Constants from configs/default.yaml + simulation/routing/gravitational.py ---
ALPHA = 0.8
BETA = 1.5
INITIAL_MASS = 1.0

# Subscriptions copied verbatim from configs/default.yaml
SUBSCRIPTIONS = {
    "haiku-1":        {"primary": "SEMANTIC",      "secondary": []},
    "haiku-2":        {"primary": "DETERMINISTIC", "secondary": []},
    "gemini-flash-1": {"primary": "DETERMINISTIC", "secondary": ["SPATIAL"]},
    "gemini-flash-2": {"primary": "SPATIAL",       "secondary": []},
    "llama-1":        {"primary": "SEMANTIC",      "secondary": ["TEMPORAL"]},
    "llama-2":        {"primary": "TEMPORAL",      "secondary": []},
    "gpt4o-mini-1":   {"primary": "DETERMINISTIC", "secondary": ["SEMANTIC"]},
    "gpt4o-mini-2":   {"primary": "SPATIAL",       "secondary": ["DETERMINISTIC"]},
    "mistral-1":      {"primary": "TEMPORAL",      "secondary": ["SEMANTIC"]},
    "qwen-1":         {"primary": "SEMANTIC",      "secondary": ["DETERMINISTIC"]},
}

DOMAINS = ["SEMANTIC", "DETERMINISTIC", "SPATIAL", "TEMPORAL"]

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_PATH = REPO_ROOT / "results" / "run-2026-04-04T15-10-45" / "results.json"


def categorical_distance(agent_id: str, domain: str) -> float:
    sub = SUBSCRIPTIONS[agent_id]
    if domain == sub["primary"]:
        return 0.0
    if domain in sub["secondary"]:
        return 0.5
    return 2.0


def fluency_to_distance(track_count: int, track_quality_sum: float) -> float:
    """Map empirical track record to a continuous distance in [0, 3].

    fluency        = avg_quality * log(1 + count) / log(11)
    fluency_capped = min(fluency, 1.0)        # 10 perfect solves saturates
    D              = 3.0 * (1 - fluency_capped)

    Examples:
        0 solves                  -> D = 3.0
        1 solve  at q=1.0         -> D = 2.13
        5 solves at q=1.0         -> D = 0.76
        10 solves at q=1.0        -> D = 0.0
        5 solves at q=0.5         -> D = 1.88
    """
    if track_count == 0:
        return 3.0
    avg_quality = track_quality_sum / track_count
    raw_fluency = avg_quality * math.log(1 + track_count) / math.log(11)
    fluency = min(raw_fluency, 1.0)
    return 3.0 * (1.0 - fluency)


def gravitational_priority(mass: float, distance: float, load: int = 0) -> float:
    """P_i = M^alpha / ((D + 1) * (L + 1)^beta)"""
    if mass <= 0:
        return 0.0
    return (mass ** ALPHA) / ((distance + 1) * ((load + 1) ** BETA))


def run_analysis(min_count_round: int = 0):
    """Run the analysis. Track records build from round 0 always; divergences
    are only counted starting at `min_count_round`. Set to 25 for the
    'charitable variant' that excludes the cold-start tie-breaking artifacts."""
    data = json.loads(RESULTS_PATH.read_text())
    grav = next(a for a in data["algorithms"] if a["algorithm"] == "gravitational")

    # Track record per (agent, domain): solve count + quality sum
    track = defaultdict(lambda: defaultdict(lambda: {"count": 0, "quality_sum": 0.0}))

    # The mass snapshot used for routing decisions in round R is the snapshot
    # at the END of round R-1 (which equals the START of round R).
    # For round 0, all agents start at INITIAL_MASS in every domain.
    prev_snapshot = {
        agent_id: {"per_domain": {d: INITIAL_MASS for d in DOMAINS}}
        for agent_id in SUBSCRIPTIONS
    }

    total_assignments = 0
    same_choice = 0
    divergences = 0

    domain_div_counts = defaultdict(int)
    domain_total_counts = defaultdict(int)

    cont_gains = defaultdict(int)   # agent -> times they won under cont but not cat
    cont_losses = defaultdict(int)  # agent -> times they lost under cont but won under cat

    div_records = []

    for round_obj in grav["rounds"]:
        round_num = round_obj["round_num"]

        count_this_round = round_num >= min_count_round

        for payload in round_obj["payloads"]:
            domain = payload["domain"]
            actual_winner = payload["assigned_agent"]
            quality = payload["quality_score"]
            if count_this_round:
                total_assignments += 1
                domain_total_counts[domain] += 1

            cat_priorities = {}
            cont_priorities = {}

            for agent_id in SUBSCRIPTIONS:
                m = prev_snapshot[agent_id]["per_domain"].get(domain, INITIAL_MASS)
                d_cat = categorical_distance(agent_id, domain)
                t = track[agent_id][domain]
                d_cont = fluency_to_distance(t["count"], t["quality_sum"])
                cat_priorities[agent_id] = gravitational_priority(m, d_cat)
                cont_priorities[agent_id] = gravitational_priority(m, d_cont)

            cat_winner = max(cat_priorities, key=cat_priorities.get)
            cont_winner = max(cont_priorities, key=cont_priorities.get)

            if cat_winner == cont_winner:
                if count_this_round:
                    same_choice += 1
            elif count_this_round:
                divergences += 1
                domain_div_counts[domain] += 1
                cont_gains[cont_winner] += 1
                cont_losses[cat_winner] += 1
                cat_t = track[cat_winner][domain]
                cont_t = track[cont_winner][domain]
                cat_avg_q = (cat_t["quality_sum"] / cat_t["count"]) if cat_t["count"] else None
                cont_avg_q = (cont_t["quality_sum"] / cont_t["count"]) if cont_t["count"] else None
                div_records.append({
                    "round": round_num,
                    "domain": domain,
                    "cat_winner": cat_winner,
                    "cat_winner_count_in_domain": cat_t["count"],
                    "cat_winner_avg_q": cat_avg_q,
                    "cont_winner": cont_winner,
                    "cont_winner_count_in_domain": cont_t["count"],
                    "cont_winner_avg_q": cont_avg_q,
                })

            # Update track record with the ACTUAL outcome
            track[actual_winner][domain]["count"] += 1
            track[actual_winner][domain]["quality_sum"] += quality

        # Snapshot for next round
        prev_snapshot = round_obj["mass_snapshot"]

    return {
        "total_assignments": total_assignments,
        "same_choice": same_choice,
        "divergences": divergences,
        "domain_div_counts": dict(domain_div_counts),
        "domain_total_counts": dict(domain_total_counts),
        "cont_gains": dict(cont_gains),
        "cont_losses": dict(cont_losses),
        "div_records": div_records,
    }


def fmt_q(q):
    return f"{q:.2f}" if q is not None else "—"


def report(r):
    print("=" * 72)
    print("Phase 0-A: Retrospective Continuous-Distance Routing Analysis")
    print("=" * 72)
    print()
    print(f"Source:    results/run-2026-04-04T15-10-45 (gravitational run only)")
    print(f"Constants: alpha={ALPHA}, beta={BETA}, load=0 (held constant)")
    print()

    print("--- Aggregate ---")
    n = r["total_assignments"]
    print(f"  Total payload assignments analyzed: {n}")
    print(f"  Same choice (cat == cont):          {r['same_choice']:>3}  ({r['same_choice']/n:.1%})")
    print(f"  Divergent choice:                   {r['divergences']:>3}  ({r['divergences']/n:.1%})")
    print()

    print("--- Divergences by Friction Type ---")
    for d in DOMAINS:
        total = r["domain_total_counts"].get(d, 0)
        div = r["domain_div_counts"].get(d, 0)
        rate = (div / total) if total else 0
        print(f"  {d:<14}  {div:>3} / {total:<3}   ({rate:.1%})")
    print()

    print("--- Track-Record Strength of Divergence Winners ---")
    cont_higher_q = 0
    cat_higher_q = 0
    tied_q = 0
    cont_no_history = 0
    cat_no_history = 0
    cont_more_solves = 0
    cat_more_solves = 0
    tied_solves = 0
    for d in r["div_records"]:
        cat_q = d["cat_winner_avg_q"]
        cont_q = d["cont_winner_avg_q"]
        if cat_q is None:
            cat_no_history += 1
        if cont_q is None:
            cont_no_history += 1
        if cat_q is not None and cont_q is not None:
            if cont_q > cat_q:
                cont_higher_q += 1
            elif cat_q > cont_q:
                cat_higher_q += 1
            else:
                tied_q += 1
        cn = d["cont_winner_count_in_domain"]
        cn2 = d["cat_winner_count_in_domain"]
        if cn > cn2:
            cont_more_solves += 1
        elif cn2 > cn:
            cat_more_solves += 1
        else:
            tied_solves += 1
    print(f"  cont winner had higher avg quality in domain: {cont_higher_q}")
    print(f"  cat  winner had higher avg quality in domain: {cat_higher_q}")
    print(f"  tied avg quality:                              {tied_q}")
    print(f"  cont winner had no domain history yet:        {cont_no_history}")
    print(f"  cat  winner had no domain history yet:        {cat_no_history}")
    print()
    print(f"  cont winner had more solves in domain:        {cont_more_solves}")
    print(f"  cat  winner had more solves in domain:        {cat_more_solves}")
    print(f"  tied solve count:                              {tied_solves}")
    print()

    print("--- Per-Agent Routing Share Delta Under Continuous D ---")
    print(f"  {'Agent':<18} {'Won (cont)':<12} {'Lost (cont)':<12} {'Net':>6}")
    all_agents = set(r["cont_gains"].keys()) | set(r["cont_losses"].keys())

    def net(a):
        return r["cont_gains"].get(a, 0) - r["cont_losses"].get(a, 0)

    for agent in sorted(all_agents, key=net, reverse=True):
        gain = r["cont_gains"].get(agent, 0)
        loss = r["cont_losses"].get(agent, 0)
        print(f"  {agent:<18} {gain:<12} {loss:<12} {net(agent):>+6}")
    print()

    print("--- Sample Divergences (first 10 of {} total) ---".format(len(r["div_records"])))
    for d in r["div_records"][:10]:
        print(
            f"  R{d['round']:>2} {d['domain']:<14} "
            f"cat-> {d['cat_winner']:<16} (n={d['cat_winner_count_in_domain']:<2}, q={fmt_q(d['cat_winner_avg_q'])})   "
            f"cont-> {d['cont_winner']:<16} (n={d['cont_winner_count_in_domain']:<2}, q={fmt_q(d['cont_winner_avg_q'])})"
        )
    print()

    print("--- Honest Limits ---")
    print("  - Load is held at 0 in both regimes (real sim uses live load).")
    print("  - This is correlational. Counterfactual routing was not executed.")
    print("  - Single seed (42). Directional, not conclusive.")
    print("  - Tests Layer 3 only. Layer 2 (verification) needs Phase 1 with text capture.")


if __name__ == "__main__":
    import sys
    if not RESULTS_PATH.exists():
        raise SystemExit(f"results.json not found at {RESULTS_PATH}")
    min_round = 0
    label = "FULL RUN (all 50 rounds)"
    if len(sys.argv) > 1 and sys.argv[1] == "--from-round":
        min_round = int(sys.argv[2])
        label = f"CHARITABLE VARIANT (rounds {min_round}-49 only, mature track records)"
    print(f"\n>>> {label}\n")
    r = run_analysis(min_count_round=min_round)
    report(r)
