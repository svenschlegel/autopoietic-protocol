# Mass Accrual Reform — V3.5 Design Spec

**Version:** 0.1 (first draft)
**Date:** 2026-04-09
**Status:** **Empirically validated by Phase 1 (2026-04-09).** Reform stack reduces aggregate Gini by 49.5% with zero quality cost across 3 independent seeds; active-participation floor raised to 6/10 agents (deterministic across seeds); decay empirically redundant on top of sublinear+rebase. See `docs/PHASE1_PROGRESS_REPORT_2026-04-09.md` and §11 below for details.
**Author:** Sven Schlegel
**Re:** Phase 0-A finding (`docs/GPSL_INTEGRATION_PROPOSAL.md` v0.3 §8.2). The reform this spec describes was the precondition for Phase 1, which has now validated it.

---

## 0. TL;DR

Phase 0-A empirically demonstrated that the current GravDic mass accrual function — `Δmass = bounty × σ`, unbounded, no domain cap, no decay — produces extreme intra-domain monopolies that no routing-time mechanism can break. By round 25 of the 2026-04-04 simulation, four agents had each accumulated 1500–5300 mass in their respective domains while six other agents remained at ~1.0. Continuous structural distance, the v0.2 fix, was mathematically incapable of overcoming a 200× mass ratio.

This spec proposes **four reform mechanisms operating on different timescales**, deployed together as a stack rather than chosen between:

1. **Operator-level fluency** (Layer 3 of GPSL integration, decomposed below the domain level)
2. **Sublinear accrual** (per-solve, diminishing returns)
3. **Metabolic Season rebase** (per ~90 days, log compression of routing mass)
4. **Background decay** (continuous, low priority)

All four are anchored on a foundational architectural change: **the Dual-Mass Architecture** (§2), which separates *Governance Mass* (permanent legacy) from *Routing Mass* (cyclical fuel). This separation is the prerequisite that makes resets and decay safe to deploy without destroying earned reputation.

Combined, the four mechanisms address: *the wrong-tool-for-the-job problem* (operator fluency), *the snowball problem* (sublinear accrual), *the stale-incumbent problem from prior LLM generations* (Season rebase), and *the dormant-holder problem* (background decay).

The spec is intentionally complete enough to draft Phase 1 of the empirical loop and intentionally honest about which constants are guesses pending data.

---

## 1. Context — what Phase 0-A actually showed

The 2026-04-04 simulation produced these end-of-run mass distributions in the gravitational routing condition:

| Agent | Primary Domain | Final Domain Mass | Next Holder's Mass |
|---|---|---|---|
| haiku-1 | SEMANTIC | 5279.4 | ≈ 1.0 |
| gemini-flash-1 | DETERMINISTIC | 2464.2 | ≈ 1.0 |
| mistral-1 | TEMPORAL | 2256.7 | ≈ 1.0 |
| gemini-flash-2 | SPATIAL | 1691.8 | ≈ 1.0 |

Six of the ten agents in the pool solved 0–2 tasks across the entire 50-round run. What we celebrated in `docs/PROGRESS_REPORT_2026-04-04.md` as "emergent specialization" is also accurately describable as **intra-domain monopolization**.

Phase 0-A (`simulation/analysis/phase0_continuous_distance.py`, executed 2026-04-08) re-routed every payload from the same simulation under both categorical D ∈ {0.0, 0.5, 2.0} and a continuous D ∈ [0.0, 3.0] derived from agents' empirical track records, holding load=0 in both regimes. Result:

- Full run (rounds 0–49): **197/200 same routing decision (98.5%)**
- Charitable variant (rounds 25–49 only, mature track records): **100/100 same routing decision (100.0%)**

The math is forced. For continuous D in [0, 3] to flip a routing decision against an incumbent with M=5000 in favor of a challenger with M=1, the distance ratio would need to satisfy `(D_chall + 1) / (D_dom + 1) < 1/955`. The maximum achievable ratio with bounded D is `1/4`. **Continuous distance cannot overcome a 200× mass advantage.**

Therefore the fault lies not in the routing formula but in the mass accrual function. Hence this spec.

---

## 2. The Dual-Mass Architecture (foundational change)

**This is the single most important architectural decision in V3.5.** All four reform mechanisms below depend on it.

### 2.1 The split

GravDic currently has one quantity called "mass" that does two jobs:

1. It is the agent's permanent reputation ledger (the social and governance signal)
2. It is the variable that plugs into the gravitational routing formula `M^α` (the work-fuel)

These are different functions. Conflating them is what makes mass-accrual reform feel risky: any decay, reset, or compression mechanism appears to "destroy reputation."

V3.5 splits them into two distinct quantities:

| Quantity | Symbol | Mutability | Purpose |
|---|---|---|---|
| **Governance Mass** | `M_gov` | **Permanent. Monotonically increasing. Never decreases.** | Voting power, $500K decentralization milestone, founder-burn trigger, RetroPGF eligibility, social proof, "this agent has done good work over time." |
| **Routing Mass** | `M_route` | **Cyclical. Subject to sublinear accrual, seasonal rebase, and background decay.** | The variable that enters the gravitational priority formula `M_route^α / ((D+1)(L+1)^β)`. Determines who gets the next payload. |

Both are derived from the same underlying solve history (the immutable record of which agent solved which payload at what quality). Governance Mass is a *cumulative* function of that history; Routing Mass is a *recent-and-bounded* function of it.

### 2.2 Why this design is safe

The two key objections to any mass-reform mechanism:

1. *"You'll destroy agents' hard-earned reputation."* — **Solved.** Governance Mass is permanent. The receipts are forever. The blockchain history of every solve is forever. Nothing about your standing in the protocol's social and governance layer is touched.
2. *"Agents will disengage if their work doesn't accumulate."* — **Solved.** Their work *does* accumulate, in Governance Mass. What changes is that *the routing weight* — which determines current work flow — is recomputed periodically based on recent and ongoing competence. This is actually how meritocracy is supposed to work.

The dual-mass split also unlocks something the original whitepaper couldn't do: **clean separation between recognition and fuel**. Governance Mass is for "who has standing in the DUNA"; Routing Mass is for "who should solve the next payload." Most existing reputation systems conflate these two and produce either feudalism (when fuel is permanent) or amnesia (when reputation resets). The split avoids both.

### 2.3 What changes in the codebase

- `simulation/economy/mass_tracker.py` — split the per-agent mass dict into two parallel dicts
- `simulation/agents/sim_agent.py` — `domain_mass()` becomes `domain_routing_mass()`; add `domain_governance_mass()`
- `simulation/routing/gravitational.py` — uses `domain_routing_mass()` (line 25)
- `contracts/src/SoulboundMass.sol` — needs corresponding refactor for V3.5 deployment; both quantities tracked on-chain

### 2.4 What changes in the whitepaper

`docs/whitepaper-v3.4.md` §4 (Soulbound Mass) needs to be rewritten end-to-end to define both quantities, the relationship between them, and the rules governing each. This is the largest single delta from V3.4 to V3.5.

---

## 3. The four reform mechanisms

Organized from highest priority to lowest, by how much each contributes to solving the Phase 0-A failure mode.

### 3.1 Operator-level fluency (Layer 3 of GPSL integration, properly)

**What it is:** Replace categorical topographic distance `D ∈ {0.0, 0.5, 2.0}` with a continuous distance computed from agent fluency in *specific GPSL operators*, not in broad domain categories.

**Why this is the highest-priority mechanism.** Phase 0-A tested *domain-level* continuous D and found it inert because mass already concentrated at the domain level. Operator-level fluency decomposes "Spatial" into the actual structural operators a payload uses (`⥀`, `⦸`, `::`, `→`, etc.). No single agent can monopolize *all* the operators in a domain, because the operator vocabulary is large and growing (GPSL v2.2 adds `⥀`, `⦸`, `↛`; v2.3+ will add more). The monopoly decomposes naturally as the operator space expands.

This is also what the carpenter/cook intuition demands: routing should match by *the specific operations the work requires*, not by the categorical label hung on the worker. A "kitchen carpentry" task needs food-safety operators that a generic carpenter doesn't have, even though both belong in "carpentry." Routing should flow to the agent fluent in the operators the task actually uses.

**Mechanism:**

```
For each agent A, maintain a per-operator fluency profile:
  fluency[A][op] = (count_solved, quality_sum)
  for every GPSL operator op the agent has demonstrated

For each payload P with required operator set Ops(P):
  D_continuous(A, P) = mismatch(fluency[A], Ops(P))
```

The exact `mismatch()` function is open. Candidate (TBD, validate in Phase 1):

```
mismatch(profile, required_ops) =
    (1 / |required_ops|) * sum over op in required_ops of:
        max(0, 3 - fluency_score(profile[op]))
    where fluency_score(count, quality_sum) = (quality_sum / count) * log(1 + count) / log(11)
                                            (capped at 1.0, then × 3 to map to [0, 3])
```

In plain English: an agent's distance to a payload is the *average inability* across the operators the payload needs, where "ability" is fluency-score (combines quality and count). An agent fluent in every operator the payload requires has D ≈ 0. An agent fluent in *none* of them has D ≈ 3.

**Dependency:** Requires GPSL adoption (Layer 1 of the integration proposal — payloads as GPSL ciphers). Without GPSL-encoded payloads, there are no operators to track fluency in.

**Status:** Designed in v0.3 of the integration proposal but not implemented. Cannot be tested in Phase 1 without GPSL ciphers in the simulation, which is a Phase 1 prerequisite.

### 3.2 Sublinear accrual

**What it is:** Replace the current `Δmass = bounty × σ` (unbounded, linear) with a function that has *diminishing returns* — the more `M_route` an agent already has in a domain, the less each new win adds.

**Why second priority:** This is the cheapest immediate fix. It's a one-line change in the simulation and a small change in the on-chain mass-accrual logic. It directly attacks the snowball: a single high-bounty win in round 0 can no longer 100× an agent's mass.

**Candidate functions** (to be selected in Phase 1):

| Function | Form | Behavior |
|---|---|---|
| **Logarithmic saturation** | `Δ M_route = bounty × σ × (1 / log(2 + M_route))` | Smooth, never zero, well-defined for all M_route ≥ 0. Each additional unit of mass adds slightly less than the previous. |
| **Michaelis-Menten** | `Δ M_route = bounty × σ × (K / (K + M_route))` | Saturates at K (a tunable constant). At M_route = K, accrual is half its max rate. |
| **Power law decay** | `Δ M_route = bounty × σ × M_route^(-γ)` for γ ∈ (0, 1) | Steeper than log, cleaner math, but undefined at M_route = 0 (needs an offset). |
| **Hard cap with smoothing** | `Δ M_route = bounty × σ` until M_route reaches `M_cap`, then 0 | Brutal, easy to reason about. Risk of cliff effects. |

**Recommendation:** Logarithmic saturation. It's smooth, well-behaved at all scales, and the constant is implicit (no `K` to tune). The formula has the right shape: at M_route=1 (new agent), accrual is `bounty × σ / log(3) ≈ bounty × σ × 0.91` (close to current behavior). At M_route=100, accrual drops to `bounty × σ × 0.22`. At M_route=5000, accrual drops to `bounty × σ × 0.12`. The slope is gentle enough that veterans still earn meaningfully but cannot run away.

**Dependency:** None. Can ship independently of any other reform. **This is the first mechanism that should land in code** because it's the smallest change with the largest immediate effect.

### 3.3 Metabolic Season rebase (the periodic reset)

**What it is:** Every N ≈ 90 days (a "Metabolic Season"), Routing Mass is **rebased**, not wiped. Specifically: log-compressed to preserve order while shrinking the gap between top and bottom.

**Why this is needed even with sublinear accrual.** Sublinear accrual *slows* monopoly formation; it does not eliminate monopolies that already exist. After a few months, even sublinear-grown leaders accumulate a meaningful gap. Periodic rebase clears the arena without destroying earned reputation.

There is also a stronger reason specific to GravDic's substrate: **the underlying LLM models are improving on a timescale of months.** A model that is state-of-the-art in January may be obsolete by July. If Routing Mass never rebases, the protocol routes work to whichever agent hoarded mass under last year's models, regardless of whether their current model is competitive. **Rebasing forces the ecosystem to constantly re-prove who is best with the current generation of models.** This isn't just a fairness mechanism — it's an *accuracy* mechanism. Without it, GravDic decays into "routing work to the best agent of yesterday's model generation."

**Mechanism — rebase, not wipe:**

```
At season boundary T:
  for every agent A and every domain d:
    M_route_new[A][d] = log(1 + M_route_old[A][d]) × C
  where C = scaling_factor (e.g., 100)
```

Worked example with the actual Phase 0-A end-of-run distribution:

| Agent | M_route_old | log(1 + M_route_old) × 100 = M_route_new |
|---|---|---|
| haiku-1 (SEMANTIC) | 5279.4 | log(5280.4) × 100 ≈ 857 |
| haiku-1 (DETERMINISTIC) | 1.0 | log(2) × 100 ≈ 69 |
| qwen-1 (SEMANTIC) | 1.0 | log(2) × 100 ≈ 69 |
| Hypothetical mid-tier | 100 | log(101) × 100 ≈ 461 |

Original ratio top:bottom: **5279:1**. Post-rebase ratio top:bottom: **857:69 ≈ 12.4:1**. The order is fully preserved (haiku-1 is still on top). The *meaningful range* is compressed from 4 orders of magnitude to ~1.

**Why rebase, not wipe:** A hard wipe (`M_route → 1.0` for all) is punitive without information value. An agent that genuinely was the best in season N starts season N+1 with no advantage — that's overcorrection. Rebase preserves the *information* of past performance (the order, the ratios in compressed form) while eliminating the *runaway scale* that breaks the routing formula.

**Dual-mass safety:** Critically, the rebase only affects `M_route`. Governance Mass (`M_gov`) is untouched. Agents do not lose voting power, milestone-trigger contribution, or social standing. They are simply being asked to demonstrate ongoing competence as a new season begins.

**Cycle length:** 90 days is a starting hypothesis. The right value depends on (a) how fast monopolies form under sublinear accrual, (b) how often new LLM model generations actually arrive, (c) how much disruption agents tolerate. Should be a configurable governance parameter, not a constitutional constant. 60–180 days is the plausible range.

**Dependency:** Requires §2 (Dual-Mass Architecture). Cannot ship without it; rebasing the only-mass-quantity would be the destructive wipe everyone is afraid of.

### 3.4 Background decay (lowest priority)

**What it is:** Continuous slow erosion of `M_route` for agents that aren't actively earning new mass.

```
At each round (or each block):
  M_route[A][d] *= (1 - δ)
  where δ is small, e.g., 0.001-0.005 per round
```

**Why this exists:** For dormant agents that have sat on a high mass position without contributing recently. Sublinear accrual prevents new mass from running away; rebase periodically clears the slate; decay handles the in-between case where someone has accumulated mass and then stopped contributing.

**Why it's lowest priority:** Decay is the most controversial of the four mechanisms because it punishes *the absence of behavior* rather than reacting to *behavior*. It is also the most likely to be unnecessary if §3.1, §3.2, and §3.3 work as intended — sublinear accrual + rebase together may already produce the desired turnover, with decay as redundant overhead. Defer decay to a later spec revision or to a governance-tunable parameter that is initially set to zero.

**Recommendation for V3.5:** Implement the *infrastructure* for decay (the parameter, the per-round application logic) but ship V3.5 with `δ = 0`. Activate it later if §3.1–§3.3 prove insufficient.

---

## 4. Why all four mechanisms, not pick one

Each mechanism operates on a different timescale and addresses a different failure mode. They are complementary, not competing.

| Mechanism | Timescale | Failure mode it addresses |
|---|---|---|
| Operator-level fluency | Per payload | Wrong-tool-for-the-job; categorical bucket too coarse (the carpenter/cook problem) |
| Sublinear accrual | Per solve | Snowball formation; one early big win locking in dominance (the Phase 0-A finding) |
| Metabolic Season rebase | Per ~90 days | Stale incumbents from prior LLM model generations; arena ossification |
| Background decay | Continuous | Dormant holders sitting on mass without contributing |

A protocol that ships only sublinear accrual will slow monopoly formation but not eliminate it; the snowball still grows, just slower. A protocol that ships only seasonal rebase will reset old monopolies but allow new ones to form rapidly within each season. A protocol that ships only operator-level fluency without accrual reform will produce *finer-grained* monopolies (one agent per operator instead of one per domain) — better than the current state, but still not adequate.

The four together produce a system where:

- **At payload routing time**, structural fit dominates over raw mass advantage (operator fluency)
- **As successful solves accumulate**, no single win can install permanent dominance (sublinear accrual)
- **Across model generations**, the arena periodically reshuffles to reflect the current capability frontier (Metabolic Seasons)
- **Across the inactive long tail**, dormant mass slowly clears so it doesn't distort routing (background decay)

The biological analogy is exact: living systems use **continuous immune surveillance, periodic cell turnover, and background apoptosis** simultaneously. None of these alone is sufficient to maintain homeostasis. Together they produce the stable-but-adaptive behavior that is the entire point of autopoiesis.

---

## 5. Implementation order for V3.5

Ship in this order. Each step is independently testable in the simulation framework before moving to the next.

| Order | Component | Estimated effort | Blocks |
|---|---|---|---|
| 1 | Dual-Mass Architecture (§2) | 1 day code + half day spec | All other mechanisms |
| 2 | Sublinear accrual (§3.2) | 2 hours code | Standalone but most effective when combined with #1 |
| 3 | Operator-level fluency (§3.1) | 1-2 days code + GPSL parser dependency | Requires GPSL adoption (Layer 1 of integration proposal) |
| 4 | Metabolic Season rebase (§3.3) | 1 day code | Requires #1 |
| 5 | Background decay infrastructure (§3.4) | 4 hours code, ship with δ=0 | Requires #1 |

**Total: ~5–7 days of focused engineering work** assuming the GPSL parser dependency in #3 is satisfied (or stubbed for the simulation). This becomes the V3.5 codebase delta.

---

## 6. Open parameters — what we don't yet know

Phase 1 of the empirical loop will inform these. They are explicitly *not* constitutional constants — they should be governance-tunable in V3.5 with sensible defaults.

| Parameter | Symbol | Tentative default | What Phase 1 should test |
|---|---|---|---|
| Sublinear accrual function | (function) | Logarithmic saturation `1 / log(2 + M_route)` | Whether log saturation, Michaelis-Menten, or power law produces the most balanced ecosystem |
| Season length | `T_season` | 90 days | Whether 30/60/90/180 days produces healthier dynamics |
| Rebase scaling factor | `C` | 100 | Whether higher or lower compression preserves the right amount of advantage |
| Operator fluency cap | (in `fluency_score()`) | 10 perfect solves saturates | Whether 5/10/20 is the right saturation point |
| Background decay rate | `δ` | 0.0 (off in V3.5) | Whether activating decay adds value when §3.1–§3.3 are also active |

---

## 7. What this means for the V3.5 whitepaper

The V3.4 whitepaper has §4 *"Soulbound Mass"* which describes a single mass quantity. V3.5 needs:

1. **§4 rewritten end-to-end** to introduce Governance Mass and Routing Mass as distinct quantities, the dual-derivation from solve history, and the rules governing each.
2. **§4.1 (new)** *"Sublinear Accrual"* — the function and its derivation, with the snowball-prevention argument from Phase 0-A as motivation.
3. **§4.2 (new)** *"Operator-Level Fluency"* — how the gravitational formula's `D` is computed from operator track records under GPSL adoption. Cross-references the GPSL integration proposal.
4. **§4.3 (new)** *"Metabolic Seasons"* — the rebase mechanism, the dual-mass safety argument, the AI obsolescence justification.
5. **§4.4 (new)** *"Background Decay (Reserved)"* — the infrastructure exists, currently inactive, governance can activate later.
6. **§7 Roadmap** updated — V4 Capillary Clusters can now reference the dual-mass architecture (clusters use Routing Mass for assembly, Governance Mass for cluster-level voting if/when that exists).
7. **§9 Empirical Validation** — point to Phase 0-A as the precedent for the design choices in §4.

The reform spec also affects:

- **Tokenomics §6** — VRGDA design doesn't change, but the relationship between $AUTO and Soulbound Mass needs clarification. Specifically: $AUTO governance staking interacts with Governance Mass, not Routing Mass.
- **Decentralization milestone §6.4** — the $500K CPI-adjusted milestone is triggered by Governance Mass distribution, not Routing Mass (which fluctuates).
- **Founder burn §6.5** — same. Triggered by Governance Mass milestone, not Routing Mass.

---

## 8. Empirical validation plan — Phase 1

Phase 0-A was a retrospective analysis on existing data. Phase 1 will be a forward-looking simulation re-run with the reform mechanisms active. The comparison structure:

### 8.1 The 2×2 design

|  | Old D (categorical) | New D (operator-level continuous) |
|---|---|---|
| **Old accrual (linear unbounded)** | Control — reproduces 2026-04-04 | Reproduces Phase 0-A failure mode |
| **New accrual (sublinear + dual-mass)** | Tests accrual reform alone | **The full reform stack** |

Four runs, same seeded payload sequence, same agent pool. Compare quality, throughput, Gini, slash rate, mass distribution, agent participation rate, monopoly index.

### 8.2 What Phase 1 must measure

1. **Does the Phase 0-A monopoly disappear under the full reform?** Specifically: at the end of 50 rounds, is any single agent's M_route greater than 10× the median?
2. **Does quality survive the reform?** Specifically: is the average quality under the full-reform run within 10% of the original 2026-04-04 result? (We do not want to break what was working.)
3. **Does participation broaden?** Specifically: how many of the 10 agents solve at least 5 payloads, vs. the 4-agent monopoly in the original run?
4. **Does the rebase event cause any catastrophic disruption?** Run two full simulated seasons (100 rounds total, with rebase at round 50). Look for quality dips or routing chaos around the boundary.

### 8.3 What Phase 1 will not test

- **Longer-term LLM obsolescence dynamics.** This requires running across multiple actual model generations, which is impractical in a 50-round simulation. The AI obsolescence argument for Metabolic Seasons (§3.3) is theoretical and will be validated only by mainnet deployment over months.
- **Real-world adversarial behavior.** Agents in the simulation are not strategic; they don't game the rebase boundary or coordinate to exploit accrual rules. Adversarial testing is a separate Phase (Phase A from the integration proposal's V4 roadmap).

---

## 9. Acknowledgments

This spec exists because two technical reviewers independently challenged the v0.2 GPSL integration proposal in ways that produced the design above:

- **D'Artagnan and the GPSL pod** for the v2.2 spec, the V-class / fertile incompletion stance, and the technical review of the v0.1 integration proposal that produced v0.2.
- **A second technical reviewer** for two contributions that became load-bearing in this spec: **(a) the dual-mass architecture** (Governance Mass vs Routing Mass) which makes resets safe, and **(b) the AI model obsolescence argument** for Metabolic Seasons, which is the strongest justification I have seen for periodic reset in any agent-economy context. The "Metabolic Season" naming itself also came from this reviewer.

The empirical falsification that motivated the spec (Phase 0-A) is documented in `docs/GPSL_INTEGRATION_PROPOSAL.md` v0.3 §8.2. The script that produced the falsification is at `simulation/analysis/phase0_continuous_distance.py`.

---

## 11. Empirical validation — Phase 1 results (added 2026-04-09)

Phase 1 ran as a 4-treatment graduated stack (control → +sublinear → +sublinear+rebase → +decay) plus a 3-seed variance check on treatments A and C. All four treatments shared the same seeded payload sequence, agent pool, and routing algorithm (gravitational). Total API cost: ~$40 across 10 simulations. Full report: `docs/PHASE1_PROGRESS_REPORT_2026-04-09.md`.

### Headline results (mean ± std across 3 seeds: 1, 7, 13)

| Metric | V3.4 control (A) | V3.5 reform (C) | Δ |
|---|---|---|---|
| Average quality | 0.820 ± 0.037 | 0.820 ± 0.026 | **+0.001 (zero cost)** |
| Aggregate Gini | 0.627 ± 0.040 | **0.317 ± 0.016** | **−49.5%** |
| Active participation (≥5 solves) | 4.7 ± 0.5 | **6.0 ± 0.0** | **+1.3** |
| Worst-domain top:median (naive) | up to 10924× | ≤ 18.2× | ~600× collapse |
| Worst-domain top:active-median | up to 1.9× | **≤ 1.4×** | within-domain parity |
| Rebase boundary quality Δ (mean) | — | +0.006 | no catastrophic dip |

### Mechanism-by-mechanism verdict

**§2 Dual-Mass Architecture.** Validated. The split is behaviorally inert in linear mode (routing mass byte-identical to V3.4 in direct unit test), and it is the foundational piece that makes all the reform mechanisms safe. The two-objection test from §2.2 held in the experiment: governance mass stayed monotonic across all accrue/slash/rebase/decay transitions; no agent's voting-relevant history was touched.

**§3.2 Sublinear accrual.** Validated as necessary-but-insufficient. On its own (Treatment B), it compresses per-domain monopolies by ~5-7× and drops Gini from 0.685 to 0.627. Top earners are still at hundreds of times the median. This is the snowball-prevention layer; it slows monopoly formation but does not eliminate existing monopolies. Quality cost isolated at this layer: −0.6%.

**§3.3 Metabolic Season rebase.** Validated as load-bearing. Adding rebase on top of sublinear (Treatment C) is the transition that collapses the regime. Per-domain ratios drop from hundreds to 8-15×; Gini drops from 0.627 to 0.317 (a further 49%); participation jumps from 5 to 6 active agents. The rebase boundary itself is benign: mean quality Δ across the boundary is +0.006 across seeds, and zero leadership changes across the boundary in any domain of any seed. Bidirectional range compression (agents below the fixed point near M≈600 are lifted; agents above are compressed) is the intended behavior and produces the observed effect.

**§3.4 Background decay (δ=0.001).** **Empirically redundant on top of §3.2+§3.3.** Treatment D activated δ=0.001 decay and produced statistically indistinguishable results from Treatment C on every headline metric (Gini 0.256 vs 0.257; participation identical; quality within seed noise). This confirms §3.4's own recommendation that V3.5 should ship with decay infrastructure in place but `δ=0` default. Governance retains the dial to activate decay later under different operating conditions, without a protocol upgrade.

**§3.1 Operator-level fluency.** Not tested. Requires GPSL ciphers in the payload corpus (GPSL adoption prerequisite). Phase 1 made §3.1 *viable* by collapsing the mass ratios from 4 orders of magnitude to 1 order of magnitude — at 15:1 ratios, bounded continuous D can mathematically flip routing decisions, whereas at 5000:1 ratios it cannot. §3.1 remains scheduled for Phase 2.

### Robustness of the Gini-collapse claim

Mean separation of Gini bands: `|0.627 − 0.317| = 0.310`. Sum of stds: `0.040 + 0.016 = 0.056`. Separation is ~5× the sum of stds, giving strong evidence the effect is not a single-seed artifact. Participation variance under reform is exactly zero across seeds — every C-seed produced 6/10 active agents.

### What this closes

Phase 0-A (2026-04-08) opened a falsification loop against v0.2 §8.2 of the integration proposal. Phase 1 closes it: the reform that grew out of the falsification is now empirically validated. The claim "the dual-mass architecture reduces aggregate Gini by 49.5% with zero quality cost across 3 independent seeds" is defensible under audit scrutiny.

The GPSL integration proposal's Layer 3 (operator-level continuous distance) is unblocked. Phase 2 can now test whether continuous D under the reformed mass distribution produces the routing differentiation v0.2 originally hypothesized — at 15:1 ratios, it is mathematically possible for the first time.

---

## 10. Open questions

1. **The exact `mismatch()` function for operator-level distance** is sketched in §3.1 but not nailed. Phase 1 will need a concrete implementation; the spec proposes a candidate but does not commit to it.
2. **Whether Governance Mass also needs sublinear accrual.** If `M_gov` is monotonic and unbounded, can it produce its own monopoly in voting power even if `M_route` is well-behaved? Probably yes, on a longer timescale. Worth a follow-up spec.
3. **The interaction between Routing Mass rebase and the slash mechanism.** Currently slashes reduce mass by 5% of domain mass. If a slash happens right before a rebase, the slashed agent gets double-penalized. Needs explicit handling.
4. **Whether `M_route` should accrue at all from Tier 2 (judge-scored) payloads, or only Tier 1 (deterministic)** — the noisier the accrual signal, the more important sublinear damping becomes. Worth analyzing.
5. **Backward compatibility for Phase 1 simulation.** If the reform ships in V3.5 contracts but the simulation framework still runs with old accrual for the control condition, we need clean conditional logic. Easy but worth flagging.
6. **The interaction with Capillary Clusters (V4).** When agents form temporary pods, whose mass is being recomputed? The cluster's? Each member's? This is a V4 concern but the dual-mass split affects it.

---

*Draft v0.1 — 2026-04-09 — Sven Schlegel*
*Informed by Phase 0-A empirical falsification and two independent technical reviews.*
*Nothing in this document is committed or public.*
