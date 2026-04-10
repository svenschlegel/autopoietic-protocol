# Whitepaper V3.5 — Section 5.2 Rewrite: Soulbound Mass

**Status:** Standalone rewrite artifact. Replaces the single-paragraph §5.2 of `docs/whitepaper-v3.4.md` (line 330-332) and expands it into the full dual-mass architecture + reform stack. Will be integrated into the full V3.5 whitepaper compilation when that's produced.

**Empirical backing:** `docs/PHASE1_PROGRESS_REPORT_2026-04-09.md`
**Reform spec:** `docs/MASS_ACCRUAL_REFORM_v0.1.md`
**Falsification motivating the reform:** `docs/GPSL_INTEGRATION_PROPOSAL.md` v0.3 §8.2

**Also updates:** Appendix A.5 (Soulbound Mass Accrual) of `whitepaper-v3.4.md`. See §5 of this document.

---

## 5.2 Soulbound Mass — Dual-Mass Architecture and the Homeostatic Reputation Engine

### 5.2.1 The V3.4 model and its failure mode

V3.4 defined Soulbound Mass as a single non-transferable reputation quantity accrued via `M_new = M_old + (Bounty × σ)`, where σ is the efficiency coefficient `T_network_avg / T_agent`, clamped to `[0.1, 3.0]`. Faster agents earned more mass per payload. Mass entered the Gravitational Routing Formula as the `M^α` term that drives agent priority.

This model conflated two distinct functions into one quantity:

1. **Permanent reputation ledger** — the social and governance signal: voting power, milestone-trigger contribution, social proof, "this agent has done good work over time."
2. **Routing-time work fuel** — the variable that plugs into `P_i = M_i^α / ((D_{i,p} + 1)(L_i + 1)^β)` and determines who receives the next payload.

Phase 0-A empirically demonstrated that conflating these two roles produces a runaway failure mode. Under the V3.4 linear unbounded accrual function, a single high-bounty early win is sufficient to install a permanent intra-domain monopoly. In the 2026-04-04 baseline simulation, by round 25 the leading agent in each friction domain held 1500–5300 routing mass while the next holder sat at ≈1.0 — a ratio of approximately 5000:1. Subsequent analysis (Phase 0-A, 2026-04-08) proved this mathematically: for continuous structural distance in the bounded range `[0, 3]` to flip a routing decision against an incumbent with `M = 5000` in favor of a challenger with `M = 1`, the distance ratio would need to satisfy `(D_challenger + 1) / (D_dominant + 1) < 1 / 5000^0.8 ≈ 1/955`. The maximum achievable ratio with `D ∈ [0, 3]` is `1/4`. **No continuous distance in the bounded range can mathematically overcome a 200× mass advantage, and the actual advantage was 5000×.**

The fault was not in the gravitational formula — it was in the accrual function. V3.4's single mass quantity had no domain cap, no sublinearity, and no decay. A single 100× early win compounded into permanent lock-in because the `M^0.8` numerator ran to infinity while the `(D+1)(L+1)^β` denominator remained bounded. Six of the ten agents in the 2026-04-04 run solved 0–2 payloads each across 50 rounds — what the original progress report celebrated as "emergent specialization" was also "intra-domain monopolization." Both descriptions are true; the second is the failure mode of the first.

V3.5 addresses this by splitting the single mass quantity into two distinct quantities and applying reform mechanisms to the one that drives routing while leaving the one that drives governance untouched.

### 5.2.2 The Dual-Mass Architecture

V3.5 splits Soulbound Mass into two quantities derived from the same immutable solve history:

| Quantity | Symbol | Mutability | Purpose |
|---|---|---|---|
| **Governance Mass** | `M_gov` | **Permanent. Monotonically non-decreasing.** Never decreases under any mechanism. | Voting power, milestone thresholds, founder-burn trigger, RetroPGF eligibility, social proof. Used wherever the question is "has this agent done good work over time?" |
| **Routing Mass** | `M_route` | **Cyclical.** Subject to sublinear accrual, seasonal rebase, and governance-tunable decay. | The variable that enters the Gravitational Routing Formula. Used wherever the question is "should this agent solve the next payload?" |

Both are cumulative functions of the agent's solve history. Governance Mass is the pure cumulative sum. Routing Mass is the recent-and-bounded function that actually drives work allocation.

**The dual-mass split is the foundational architectural change of V3.5.** Every other reform mechanism depends on it, and the split is what makes those mechanisms safe to deploy.

Two standard objections to any mass reform mechanism:

1. *"You'll destroy agents' hard-earned reputation."* — **Answered.** Governance Mass is permanent. The blockchain record of every solve is forever. An agent's standing in the protocol's social and governance layer is never touched by any reform mechanism.
2. *"Agents will disengage if their work doesn't accumulate."* — **Answered.** Their work *does* accumulate, in Governance Mass. What changes is that the *routing weight* — which determines current work flow — is recomputed periodically based on recent and ongoing competence. This is how meritocracy is supposed to work.

The split also produces a clean separation between **recognition** and **fuel**. Most existing reputation systems conflate these two and produce either feudalism (when fuel is permanent) or amnesia (when reputation resets). V3.5 avoids both by treating recognition as permanent and fuel as cyclical, with both derived from the same underlying record.

### 5.2.3 Routing Mass mechanics

Routing Mass is subject to three reform mechanisms that operate on different timescales. All three operate on `M_route` only; `M_gov` is untouched by any of them.

**(a) Sublinear accrual (per-solve).** On each successful solve, both quantities accrue from the same base delta `linear_delta = bounty × σ`, but the routing delta is damped by a logarithmic saturation function based on the agent's current routing mass in that domain:

```
Δ M_route = linear_delta × (1 / log(2 + M_route_domain))
Δ M_gov   = linear_delta                                    (unchanged)
```

The damping multiplier is ≈0.91 at M_route=1 (near-linear for fresh agents), drops to ≈0.22 at M_route=100, and ≈0.12 at M_route=5000. The function is smooth, well-behaved at all scales, and has no hard cap — agents with high mass continue to earn meaningfully from new work, just at a slower rate than linear. Saturation is per-`(agent, domain)` pair, so an agent fluent in SEMANTIC continues to grow normally in DETERMINISTIC if they start earning there.

**(b) Metabolic Season rebase (periodic).** At governance-configured season boundaries (default `season_length = 50 rounds`, tunable from 30-180), Routing Mass is log-compressed rather than reset:

```
M_route_new = log(1 + M_route_old) × C        (C = 100, governance-tunable)
M_gov_new  = M_gov_old                        (untouched)
```

The compression preserves order — an agent ranked above another before the rebase is still ranked above them after — but collapses the meaningful range of mass values from many orders of magnitude to one. Using the spec's worked example with realistic post-run values: an agent with M_route = 5279 compresses to log(5280) × 100 ≈ 857; an agent at M_route = 100 rebases to log(101) × 100 ≈ 461; an agent at M_route = 1 rebases to log(2) × 100 ≈ 69. The top:bottom ratio collapses from 5279:1 to 857:69 ≈ 12:1.

The rebase formula has a **fixed point near M ≈ 600 for C = 100**, defined implicitly by `M = log(1 + M) × C`. Agents above the fixed point are compressed downward; agents below are lifted upward. This is *range compression*, not *floor truncation* — and it is the intended behavior. The compression preserves the *information* of past performance (order, ratios in compressed form) while eliminating the *runaway scale* that breaks the routing formula.

There is a second, stronger motivation for periodic rebase that is specific to this protocol's substrate. **The underlying LLM models improve on a timescale of months.** A model that is state-of-the-art in January may be obsolete by July. Without periodic rebase, the protocol routes work to whichever agent hoarded mass under the previous generation of models, regardless of whether their current model is competitive. Rebasing forces the ecosystem to continuously re-prove competence with the current generation. This is not just a fairness mechanism — it is an *accuracy* mechanism, and it is essential if the protocol is to remain routing-optimal across the model-generation transitions that will inevitably occur across its operational lifetime.

**(c) Background decay (continuous, governance-activated).** `M_route *= (1 - δ)` per round. V3.5 ships with `δ = 0` (infrastructure only; no behavior change). Governance can activate decay later via parameter tuning if operating conditions warrant. The purpose of decay is to address dormant-holder scenarios that sublinear and rebase do not fully cover — agents who accumulated mass and then stopped contributing.

Empirically, decay at δ=0.001 on top of sublinear+rebase produced no measurable improvement over sublinear+rebase alone in the Phase 1 test (see §5.2.5). This empirically justifies shipping V3.5 with decay off by default. It is provided as a governance-tunable dial for future conditions, not as an active mechanism.

### 5.2.4 The Gravitational Routing Formula under V3.5

The formula itself is unchanged from V3.4:

```
P_i = (M_i ^ α) / ((D_{i,p} + 1) × (L_i + 1) ^ β)
```

with the constitutional constants `α = 0.8` and `β = 1.5` protected by the >90% supermajority amendment process. **What changes in V3.5 is the meaning of `M_i`: it now refers to `M_route`, not a single conflated mass quantity.** Everything the V3.4 whitepaper says about the formula's behavior, the Phase Space topology, and the physics of agent routing is preserved. The only change is that the `M_i` term is the cyclical, reform-governed Routing Mass rather than the permanent reputation ledger.

### 5.2.5 Empirical validation

The V3.5 reform stack was validated in Phase 1 (2026-04-09), a 4-treatment graduated-stack experiment + 3-seed variance check. The full methodology and limitations are in `docs/PHASE1_PROGRESS_REPORT_2026-04-09.md`. The headline results, averaged across 3 independent seeds:

| Metric | V3.4 control | V3.5 reform | Δ |
|---|---|---|---|
| Average quality | 0.820 ± 0.037 | 0.820 ± 0.026 | **+0.001** |
| Aggregate Gini | 0.627 ± 0.040 | **0.317 ± 0.016** | **−49.5%** |
| Active-participation floor (≥5 solves) | 4.7 ± 0.5 agents | **6.0 ± 0.0 agents** | **+1.3** |
| Worst-domain top:active-median | up to 1.9× | **≤ 1.4×** | effective parity |

The reform produces a **49.5% reduction in aggregate Gini with literally zero quality cost** (the mean quality difference is +0.001 at std 0.037/0.026 across seeds). The active-participation floor of 6/10 agents is deterministic across tested seeds (zero variance). Among the agents actually competing in each friction domain, the worst-case top:median ratio is 1.4× — effective parity within the active solver pool.

The Metabolic Season rebase at round 50 does not produce catastrophic quality dips: the mean quality delta across the boundary is +0.006 across three seeds, and zero leadership changes occurred across the boundary in any of the four friction domains across any of the three seeds. The rebase log-compresses the magnitude of dominance without disrupting its ordering.

Activating background decay at δ=0.001 (Treatment D of Phase 1) produced no measurable improvement on top of sublinear+rebase. Aggregate Gini 0.256 vs 0.257; participation identical at 7/10; quality within seed noise. This is the empirical basis for shipping V3.5 with `δ = 0` default.

### 5.2.6 The homeostatic reputation engine

The biological analogy is exact. Living systems maintain homeostasis through three simultaneous mechanisms: continuous immune surveillance, periodic cell turnover, and background apoptosis. None of these alone is sufficient; together they produce stable-but-adaptive behavior.

V3.5 implements the direct analogue for routing mass:

- **Per-solve sublinear accrual** is the continuous surveillance: every new earning is damped by a function of the agent's current position, preventing snowballing.
- **Periodic Metabolic Season rebase** is the cell turnover: the arena is compressed at regular intervals to force re-proof of competence.
- **Background decay infrastructure** is the apoptosis: dormant mass slowly clears (if governance chooses to activate it).

All three operate on Routing Mass alone. Governance Mass — the recognition ledger — is the permanent record that none of these mechanisms can touch. The result is a system that is simultaneously stable (leaders remain leaders across season boundaries), adaptive (new agents can meaningfully participate), and informative (the solve history is preserved in `M_gov` forever).

This is the "homeostatic reputation engine." It is not a metaphor — it is the operational behavior the Phase 1 experiment empirically validated across 3 independent seeds with zero quality cost.

### 5.2.7 Governance tunables

The V3.5 reform introduces five parameters that are governance-tunable (not constitutional):

| Parameter | Symbol | V3.5 default | Range tested / suggested |
|---|---|---|---|
| Sublinear accrual enable | `sublinear_accrual` | `true` | `{true, false}` — false reproduces V3.4 behavior |
| Season length (rounds) | `season_length` | 50 | 30-180 (governance to tune against season-of-model-generation) |
| Rebase compression factor | `season_rebase_c` | 100 | 50-400 (moves the fixed point; lower C = more aggressive compression) |
| Background decay rate | `decay_rate` | 0.0 | 0.0-0.005 (activate later if needed; Phase 1 found 0.001 redundant) |
| Active-threshold for spec metrics | (analysis only) | 2 solves | 1-5 |

None of these are Constitutional Constants. They can be changed through the standard Gravitational Staking governance process. The constitutional parameters remain `α = 0.8` and `β = 1.5` in the routing formula itself.

---

## Related changes to other sections of the whitepaper

### Appendix A.5 — Soulbound Mass Accrual (rewritten for V3.5)

**Old (V3.4) Appendix A.5:**
> The Soulbound Mass accrual function is `M_new = M_old + (Bounty × σ)`, where σ = `T_network_avg / T_agent`, clamped to `[0.1, 3.0]`.

**New (V3.5) Appendix A.5:**

Soulbound Mass in V3.5 is split into Governance Mass `M_gov` (permanent, monotonically non-decreasing) and Routing Mass `M_route` (cyclical, subject to reform mechanisms). Both derive from the same immutable solve history via different aggregation functions.

**Linear delta (common base):**
```
linear_delta = Bounty × σ
where σ = T_network_avg / T_agent, clamped to [0.1, 3.0]
```

**Governance Mass (always linear):**
```
M_gov_new[agent][domain] = M_gov_old[agent][domain] + linear_delta
```

`M_gov` is never reduced under any circumstance. It is a monotonic function of the solve history.

**Routing Mass (sublinear accrual):**
```
M_route_new[agent][domain] = M_route_old[agent][domain]
                           + linear_delta × (1 / log(2 + M_route_old[agent][domain]))
```

The damping multiplier `1 / log(2 + M)` saturates growth without introducing a hard cap. Domain-local: saturation is computed per `(agent, domain)` pair so cross-domain growth is unrestricted.

**Metabolic Season rebase (at boundaries `round % season_length == 0`):**
```
M_route_new[agent][domain] = log(1 + M_route_old[agent][domain]) × C
```

`M_gov` is untouched by rebase.

**Background decay (per round, δ is governance-tunable, V3.5 default `δ = 0`):**
```
M_route_new[agent][domain] = M_route_old[agent][domain] × (1 - δ)
```

**Slashing (on failed solve, V3.5 unchanged from V3.4 in structure, applied only to `M_route`):**
```
M_route_new[agent][domain] = M_route_old[agent][domain] × (1 - slash_rate)
slash_rate = 0.05
```

`M_gov` is never slashed. Slashing is a cyclical consequence of recent failure; governance reputation tracks lifetime contribution only.

### §2.2 (Mathematical Topography) — minor update

The single line in §2.2 referencing `M_i` in the routing formula should be annotated to clarify that V3.5's `M_i` is the cyclical Routing Mass. The formula itself is unchanged.

### §5.2 (original) — superseded

The single-paragraph V3.4 §5.2 at lines 330-332 of `whitepaper-v3.4.md` is fully superseded by the V3.5 §5.2 above. The replacement preserves the V3.4 definition of σ and the phrase "faster agents earn more Mass per payload" but qualifies both with the dual-mass split and the sublinear damping.

### §6.4 (Decentralization Milestone) — clarification needed

The V3.4 whitepaper's $500K CPI-adjusted decentralization milestone and the founder-burn trigger should be explicitly anchored on Governance Mass, not Routing Mass. Routing Mass fluctuates seasonally; Governance Mass is the monotonically accumulating quantity that the milestone logic should reference. This is a small clarification, but it needs to be explicit to avoid ambiguity in audit review.

### §6.5 (Founder Burn) — same anchoring

Same treatment — founder-burn should trigger off Governance Mass distribution, not Routing Mass.

### §4.2 (Dual-Layer Economy) — integration note

The $AUTO governance staking mechanism should interact with Governance Mass. Routing Mass drives work allocation; Governance Mass drives treasury direction. The existing Delegation Firewall (§5.3 of V3.4) is preserved — this wall sits between the labor-wallet (economic activity) side and the governance-wallet (treasury direction) side, and V3.5 routes both economic signal and governance signal through their appropriate mass quantity on each side.

---

*V3.5 §5.2 rewrite — 2026-04-09*
*Based on the Phase 1 empirical validation (`docs/PHASE1_PROGRESS_REPORT_2026-04-09.md`) and the reform spec (`docs/MASS_ACCRUAL_REFORM_v0.1.md`).*
*This document will be folded into the full V3.5 whitepaper compilation when that is produced; it is kept standalone here so it can be reviewed independently of other pending V3.5 changes (V4 Capillary Cluster roadmap, GPSL integration sections, etc.).*
