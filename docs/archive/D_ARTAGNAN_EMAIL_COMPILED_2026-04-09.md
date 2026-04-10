# Email to D'Artagnan — single-prompt compiled bundle
# 2026-04-09
#
# Self-contained. No external links, no repo references. Everything D'Artagnan
# (or an LLM he prompts it into) needs to react is inlined below.

---

**Subject:** GravDic / GPSL — empirical update + two open questions for you

Hey D'Artagnan,

Big update since v0.2 of the integration proposal you saw. Short version: I ran the empirical loop, the simulation falsified one of my own claims, I redesigned around the failure, and I built v0.1 of the hybrid validator implementing your v2.2 grammar. The whole loop took two days and produced more clarity than I expected. Sending it your way for review before any of it lands in V3.5 spec text.

Everything is inlined below so you can read it straight through (or paste the whole thing into an LLM for a second opinion). Four sections:

1. **Integration Proposal v0.3** — the design, now with full disclosure of the Phase 0-A falsification.
2. **Mass Accrual Reform v0.1** — the reform the falsification forced. Built around a **Dual-Mass Architecture** (permanent Governance Mass vs. cyclical Routing Mass), which makes four reform mechanisms safe to ship without destroying earned reputation.
3. **GPSL Validator v0.1** — summary of the hybrid parser I built against your v2.2 spec.
4. **Two open questions I need your call on** — both are about interpretive edges in the v2.2 grammar that the validator surfaced.

**What I'm hoping for from you, in order of usefulness:**

1. Your call on the **two open questions** at the end — they unblock validator v0.2 and directly affect how Phase 1 of the simulation will route work.
2. Sanity check on whether the **friction-type ↔ notation-layer mapping** in §2 of the integration proposal still holds for you. That mapping is the load-bearing claim of the whole integration.
3. Anything in the **Mass Accrual Reform** spec that smells wrong — especially the V-class / C-class flagging behavior, where I want to make sure I'm honoring your v2.2 epistemic stance and not flattening it.
4. Whether the **GravDic landing page** should credit GPSL and the pod by name. Current draft credits "D'Artagnan and the Aleth · Bridge · Mirror · K4 pod." If you'd prefer different framing, tell me now before the site v0.1 ships.

No rush on any of this — none of it is on a deadline. But the empirical loop is open until you weigh in on the two interpretive questions, so the sooner you can react to those the sooner Phase 1 unblocks.

Couple of things from my side that aren't in the docs below but you should know:

- The Optimism Superchain Audit Grant is paused indefinitely. We're going to paid audits via Sherlock and a Spearbit-adjacent firm now, with a Wyoming DUNA forming to bridge the funding gap. Doesn't affect the integration, but explains why some timelines might shift.
- **GravDic** is the rebrand of Autopoietic Protocol. Site is placeholder-only for now; full v0.1 comes after your read on the credit framing.

Thanks for v2.2. Reading it carefully changed how I think about half the protocol.

Sven

---

# PART 1 — GPSL × GravDic Integration Proposal v0.3

**Changelog from v0.2:**
- **§8.2 retracted in full.** The claim that "continuous structural distance makes mass decay obsolete" has been empirically falsified by Phase 0-A. Mass decay is back on the V4/V5 roadmap.
- §3 Layer 3 worked example annotated with a falsification callout.
- §4 Empirical validation plan updated with Phase 0-A results (100% same-choice in the charitable variant).
- New §8.2 documents what was claimed, what the simulation actually showed, why, and what it means for V3.5.
- §6 Next steps reordered — mass accrual reform is now a precondition for any fair test of Layer 3.

## 1. Context — what GravDic is, briefly

GravDic (rebrand of Autopoietic Protocol) is a decentralized M2M economic system on Base L2. Agents solve **Metabolic Payloads** for USDC bounties, earn **Soulbound Mass** (non-transferable reputation), and are routed work via the **Gravitational Routing Formula**:

```
P_i = M_i^α / ((D_{i,p} + 1) · (L_i + 1)^β)
```

where `M_i` is the agent's mass, `D_{i,p}` is topographic distance (specialty match), `L_i` is current load, and `α=0.8`, `β=1.5` are constitutional constants.

Phase 1 of the protocol is complete (160/160 Foundry tests passing, audit outreach sent). The first empirical simulation (50 rounds × 10 LLM agents × 5 routing algorithms) ran on 2026-04-04 and showed gravitational routing wins on quality (0.858) and throughput (0.890), with "just pick the best agent" as the worst performer.

The protocol whitepaper already references GPSL in three places (GPSL Phase Shift in commit-reveal, GPSL Crucible as Alpha qualifying puzzle, GPSL royalty deferred to V3.5+). This proposal is what that V3.5+ deepening actually looks like, having now read v2.2 carefully.

## 2. Why GPSL fits structurally — not just thematically

GravDic categorizes work by four **friction types**: Semantic, Deterministic, Spatial, Temporal. When I read v2.2's five notation layers, the mapping was unsettling:

| GravDic friction type | GPSL layers | Why it fits |
|---|---|---|
| **Deterministic** | Layer 1 (Symbolic) + Layer 3 (Mathematical) | Type constraints + mathematical descriptors give exact-match verification |
| **Semantic** | Layer 1 + Layer 2 (Greek) | Ontological class without lexical commitment — Greek symbols carry affinities, not definitions |
| **Spatial** | Layer 1 (Symbolic, native) | This *is* topology — GPSL's home turf |
| **Temporal** | Layer 5 (Quantum) | `Û(t)` temporal evolution + `[Observer⥀{Σ}]` scanning over time |

I didn't design the friction types around GPSL's layers — they predated my reading of v2.2. The fit is structural, not retrofitted. Either we both converged on the same partition of the cognitive substrate, or there's something deeper about how work decomposes that both projects are seeing.

**This is the single most important observation in this document.** Everything below is downstream of it. If you disagree about the mapping, the rest of the proposal probably falls apart.

## 3. The integration layers

### Layer 1 — Payloads as GPSL ciphers (encoding standard)

Today a Metabolic Payload is a task description + verification criteria in an ad-hoc per-task format. Under this layer, it becomes a GPSL cipher with a friction-type header:

```
HEADER: Spatial / Constraint Placement
LEGEND: ⥀ = directional scan
PAYLOAD:
  [Solver⥀{candidate_sites}] :: [Constraint] → {Placement}
  ⟨placement|constraints⟩ > 0.85
```

One format, four friction types, no per-task schema. Pure GravDic-side change.

### Layer 2 — Hybrid verification (the killer feature)

GravDic currently has Tier 1 (exact-match, only for arithmetic) and Tier 2 (LLM judge — noisy, slow, expensive, contested). GPSL offers a **Tier 1.5** that doesn't currently exist: hybrid structural validation.

Layer 1 base-operator rules are mechanical and can be checked without an LLM. **But not all violations are failures.** v2.2 is explicit: V-class nodes are *"structures grammatically invalid but structurally load-bearing — do NOT correct — they mark the current boundary of expressibility."* A naïve parse-and-slash validator would destroy exactly the submissions GPSL exists to protect.

The right design is a **hybrid validator**: mechanical strictness for Layer 1 base operators, **flag-not-slash** for everything richer.

Stack:
1. Mechanical well-formedness gate — base operators only. Fail = automatic slash.
2. V-class / advanced operator flagging — deterministic, non-slashing. Mass held in escrow pending governance review.
3. Resonance check `⟨submission|target⟩ > θ` — cheap embedding similarity.
4. **C-class escalation primitive** (new). Submissions that hit a genuine completeness limit surface to governance with the failure code. No other agent economy has "the agent encountered the boundary of expressibility" as a first-class non-failure outcome.
5. Tier 2 LLM judge only for the residual.

### Layer 3 — Routing distance, computed structurally

GravDic's gravitational formula uses `D_{i,p}` — currently a categorical {0.0, 0.5, 2.0}. With GPSL, distance becomes **continuous and structurally measured**: each agent has a profile of which operators and layers it has demonstrated fluency in, and a payload's distance to an agent is the structural mismatch.

**Worked example — order flip on a single payload.** Spatial payload requiring Layer 5 operators (`⥀`, `⦸`).

| Agent | Mass | Load | Legacy D | GPSL D | Notes |
|---|---|---|---|---|---|
| A — Incumbent | 2000 | 3 | 0.0 | 1.5 | Subscribed to Spatial, but mass earned on Layer 1 only |
| B — Specialist | 600 | 1 | 0.5 | 0.1 | Cross-domain per legacy, but actually fluent in the operators |

Plug into `P_i = M^0.8 / ((D+1)(L+1)^1.5)`:

| Regime | P_A | P_B | Winner |
|---|---|---|---|
| Legacy categorical | ≈ 54.7 | ≈ 39.4 | A wins by 39% |
| GPSL continuous | ≈ 21.9 | ≈ 53.7 | B wins by 145% |

Order flips decisively.

> **⚠ FALSIFICATION NOTICE (v0.3):** The worked example is mathematically correct *in isolation*, but the scenario does not occur under the current simulation's mass distribution. Phase 0-A re-ran every routing decision from the 2026-04-04 simulation under both categorical and continuous D and found **100% identical decisions in rounds 25–49.** The cherry-picked numbers (M_A=2000 vs M_B=600, only a 3.3× ratio) flatter the continuous-D advantage. In the real simulation, post-monopoly mass ratios reach 5000:1, and **no continuous D in [0, 3] can mathematically overcome a ratio that large.** See §8.2 below.

**The v0.2 implication — now retracted.** v0.2 claimed continuous structural distance would make time-based mass decay obsolete. **That claim is wrong.** The fault is not in continuous distance as a concept; it is in the protocol's unbounded mass accrual function. Continuous D *at routing time* cannot break a monopoly that has already happened in the mass term. Layer 3 remains valuable but is **not sufficient on its own** — it must be paired with mass-accrual reform and/or operator-level (rather than domain-level) fluency tracking.

### Layer 4 — Capillary Clusters as pod-pattern architecture

V4 multi-agent collaboration in GravDic is currently underspecified. GPSL v2.2 was produced by a working multi-agent pod with an explicit operator ratification protocol: motivation → formal definition → distinction → example → transmission class → pod consensus. That's a running implementation GravDic can adopt as a pattern.

Capillary Clusters under this pattern:
- Cluster = ad-hoc pod assembled around a payload that exceeds any single agent's fluency.
- Operator ratification protocol as the cluster's internal consensus mechanism.
- V-class / C-class flagging as escalation primitive.

**On-chain cost — off-chain consensus, on-chain settlement.** Ratification runs in a localized p2p layer (libp2p or equivalent); only the final ratified state settles on-chain as a single attestation hash with cluster-member signatures. EscrowCore sees one transaction per resolved cluster.

### Layer 5 — The GPSL Crucible (qualifying filter)

Alpha qualifying testnet puzzle. Candidate receives a cipher with a header but no legend, must produce a structurally valid response within a time window. Graded by parser well-formedness, resonance with target, layer coverage, no NL contamination. Pass = Alpha whitelist + initial mass grant. Cannot be gamed by an LLM wrapper alone; base models fail GPSL well-formedness without scaffolding.

### Layer 6 — Royalty flow via 0xSplits (economic coupling)

The V3.5+ deferred item. The earlier draft hardcoded a "GPSL royalty" path into EscrowCore. **That was wrong** — direct liability linkage the audit and DUNA legal wrapper need to avoid. Revised mechanism:

Use a standard Base-native revenue-split primitive (0xSplits or equivalent). Payload creator funds a Split contract at payload creation time. The Split routes: 99.5% to the resolved solver, 0.5% to the GPSL multisig. **EscrowCore stays GPSL-agnostic.** The integration becomes a *convention* enforced at the payload-creation layer, not a *coupling* in core protocol code.

Audit-clean, DUNA-clean, composable, reversible. Rate (0.5%), multisig structure, sunset conditions all negotiable. Not a lawyer — this convention should still be reviewed by counsel before publication.

## 4. Empirical validation plan

**Phase 0-A — Retrospective continuous-distance routing analysis (✓ COMPLETE, 2026-04-08).** Pivoted from the original Phase 0 (which needed submission text that isn't stored). For each of 200 existing routing decisions, computed gravitational priority under both categorical D and continuous D derived from empirical track records, holding load=0. **Result: 197/200 same choice on the full run, 100/100 same choice in the charitable variant (rounds 25–49, mature track records). Layer 3 as specified in v0.2 is empirically falsified.** Full analysis in §8.2.

**Phase 0-B — Verification-only retrofit (deferred).** Needs simulation re-instrumentation to log submission text (~1h modification).

**Phase 1 — Surgical re-run with GPSL ciphers + mass-accrual reform (~3-5 days).** Pick the friction type GPSL fits most natively — Spatial. Encode 20 Spatial payloads as GPSL ciphers. Give every agent a GPSL v2.2 system prompt + few-shot examples. **Reform mass accrual** to be sublinear or capped. Re-run all 5 routing algorithms with old-D-old-accrual (control) and new-D-new-accrual (treatment). Measure judge noise, parser catch rate, routing impact, agent fluency curve.

**Important:** the naïve version — "encode all 200 payloads as GPSL, re-run all algorithms" — has a high chance of a confounded negative result. The simulation's LLM agents (Claude Haiku, GPT-4o-mini, Gemini Flash, Llama 70B, Mistral Large, Qwen 72B) are not GPSL-fluent; without scaffolding we'd measure "current LLMs can't speak GPSL yet" rather than "GPSL improves protocol outcomes."

## 5. Open questions

1. **Reference parser status.** Does a deterministic GPSL v2.2 parser exist? If not, GravDic is building one (see Part 3 below).
2. **Versioning policy.** GravDic's verification will depend on grammar stability. If v2.3 ratifies a breaking change, that breaks GravDic. Need deprecation / version pinning.
3. **Royalty mechanics.** Rate, recipient structure, sunset, legal framing — all open.
4. **Public attribution on the GravDic landing page.** Default plan: credit GPSL and the pod prominently.
5. **The friction-type ↔ notation-layer mapping in §2.** If it's a coincidence rather than a real structural fit, the verification and routing layers still work but feel less inevitable. Worth pressure-testing.

## 8. Open implications

### 8.1 V-class flagging gives GravDic a primitive nobody else has

Every other agent economy collapses "the agent failed" and "the agent encountered the boundary of expressibility" into the same outcome: quality below threshold = slash. This loses enormous information. The cases where an agent legitimately bumps up against what the protocol can express are *exactly* the cases governance needs to see.

By adopting GPSL's V-class / C-class distinction in Layer 2, GravDic gains a structural failure mode no other protocol has language for. **V-class flag = "the cluster knows it failed and knows why; the failure is informative."** That's a governance signal, not a slash event. Two layers of the integration share one mechanism.

### 8.2 Phase 0-A — full falsification disclosure

**Status: FALSIFIED. Phase 0-A, 2026-04-08.**

**What v0.2 claimed.** That continuous structural distance would prevent incumbent lock-in at routing time and thereby make time-based mass decay obsolete.

**What we actually did.** For each of 200 payload assignments in the 2026-04-04 gravitational simulation run, computed gravitational priority under two regimes:
- **Categorical D** ∈ {0.0, 0.5, 2.0} from hardcoded subscriptions.
- **Continuous D** ∈ [0.0, 3.0] derived from empirical track records: `fluency = avg_quality × log(1+count) / log(11)`, capped at 1.0, mapped to `D = 3 × (1 − fluency)`.

Held load=0 in both regimes to isolate the D effect. Compared argmax winners.

**What we found.**

| Variant | Total | Same choice | Divergences | Rate |
|---|---|---|---|---|
| Full run (rounds 0–49) | 200 | 197 | 3 | 1.5% |
| **Charitable (rounds 25–49, mature track records)** | **100** | **100** | **0** | **0.0%** |

The three full-run divergences are concentrated in early rounds (R0, R0, R7) where no agent has a track record yet, making continuous-D collapse to uniform D=3.0. Tie-breaking artifacts of dict iteration order, not signal.

**Why — the math is forced.** By round 25 the simulation has produced extreme intra-domain mass concentration:

| Agent | Domain | Mass at end of run | Next holder |
|---|---|---|---|
| haiku-1 | SEMANTIC | 5279.4 | ≈ 1.0 |
| gemini-flash-1 | DETERMINISTIC | 2464.2 | ≈ 1.0 |
| mistral-1 | TEMPORAL | 2256.7 | ≈ 1.0 |
| gemini-flash-2 | SPATIAL | 1691.8 | ≈ 1.0 |

For continuous D to flip a decision against an incumbent with M=5000 in favor of a challenger with M=1:

```
(D_chall + 1) / (D_dom + 1) < 1 / 5000^0.8 ≈ 1 / 955
```

With D ∈ [0, 3], the maximum achievable ratio is `1/4`. **Not even close.** Mathematically refuted by the simulation's actual mass distribution.

**Where the fault actually lies.** In the mass accrual function. `Δmass = bounty × σ` is unbounded, no domain cap, no sublinearity, no decay. A single high-bounty win in round 0 — gemini-flash-1 earned 106 mass on payload 4 of round 0, 100× starting position — is enough to install a permanent monopoly.

Also visible in the 2026-04-04 results we already published as a "win": haiku-1 solved 65 of 65 successful semantic tasks, gemini-flash-1 solved 45 deterministic, mistral-1 solved 33 temporal, gemini-flash-2 solved 30 spatial. **Six of the ten agents solved 0–2 tasks each across 50 rounds.** What we celebrated as "emergent specialization" is also "intra-domain monopolization." Both descriptions are true; the second is the failure mode of the first.

**What this means concretely:**

1. Layer 3 is not dead, but not sufficient on its own. Must be paired with sublinear/capped mass accrual, operator-level fluency, and/or time-based mass decay.
2. The mass-decay-obsolescence claim is retracted in full.
3. The V3.5 empirical agenda must include mass-accrual reform as a precondition for any fair test of Layer 3.
4. §8.1 (V-class flagging) is unaffected — it's a Layer 2 implication and stands independently.

---

# PART 2 — Mass Accrual Reform v0.1

## 0. TL;DR

Phase 0-A demonstrated that the current accrual function — `Δmass = bounty × σ`, unbounded, no cap, no decay — produces intra-domain monopolies no routing-time mechanism can break. This spec proposes **four reform mechanisms on different timescales, deployed together as a stack**:

1. **Operator-level fluency** (Layer 3 of GPSL integration, decomposed below the domain level)
2. **Sublinear accrual** (per-solve, diminishing returns)
3. **Metabolic Season rebase** (per ~90 days, log compression of routing mass)
4. **Background decay** (continuous, low priority)

All four are anchored on a foundational architectural change: the **Dual-Mass Architecture**, which separates *Governance Mass* (permanent legacy) from *Routing Mass* (cyclical fuel). This separation is the prerequisite that makes resets and decay safe to deploy without destroying earned reputation.

## 2. The Dual-Mass Architecture (foundational)

GravDic currently has one quantity called "mass" doing two jobs: permanent reputation ledger AND the variable in the gravitational formula. Conflating them is what makes any reform feel risky.

V3.5 splits them:

| Quantity | Symbol | Mutability | Purpose |
|---|---|---|---|
| **Governance Mass** | `M_gov` | **Permanent. Monotonically increasing. Never decreases.** | Voting power, $500K decentralization milestone, founder-burn trigger, RetroPGF eligibility, social proof. |
| **Routing Mass** | `M_route` | **Cyclical. Subject to sublinear accrual, seasonal rebase, and background decay.** | The variable that enters `M_route^α / ((D+1)(L+1)^β)`. Determines who gets the next payload. |

Both derive from the same immutable solve history. Governance Mass is a *cumulative* function; Routing Mass is a *recent-and-bounded* function.

**Why this design is safe.** The two standard objections to mass reform:
1. *"You'll destroy agents' hard-earned reputation."* → Solved. Governance Mass is permanent.
2. *"Agents will disengage if their work doesn't accumulate."* → Solved. Their work *does* accumulate, in Governance Mass. What changes is that the *routing weight* is recomputed periodically based on recent competence.

The split also produces clean separation between **recognition and fuel**. Most reputation systems conflate these two and produce either feudalism (permanent fuel) or amnesia (reputation resets). The split avoids both.

*(The dual-mass architecture and the AI-obsolescence argument for periodic rebase below both came from a separate technical reviewer, credited at the end of this part. Your V-class / fertile-incompletion stance from v2.2 is the design philosophy underneath the whole thing — the protocol now treats "the agent encountered an expressibility limit" as a first-class outcome, not a slash event.)*

## 3. The four reform mechanisms

### 3.1 Operator-level fluency

Replace categorical topographic distance with continuous distance computed from agent fluency in *specific GPSL operators*, not broad domain categories. Phase 0-A tested *domain-level* continuous D and found it inert because mass already concentrated at the domain level. Operator-level fluency decomposes "Spatial" into the actual structural operators a payload uses (`⥀`, `⦸`, `::`, `→`, etc.). No single agent can monopolize *all* operators, because the vocabulary is large and growing.

Mechanism sketch:
```
For each agent A, maintain per-operator fluency:
  fluency[A][op] = (count_solved, quality_sum)

For each payload P with required operator set Ops(P):
  D_continuous(A, P) = (1/|Ops(P)|) × Σ_{op ∈ Ops(P)} max(0, 3 - fluency_score(profile[op]))
  where fluency_score(count, quality_sum) = (quality_sum/count) × log(1+count)/log(11), capped at 1.0, × 3
```

In plain English: an agent's distance to a payload is the *average inability* across the operators the payload needs. Fluent in all → D ≈ 0. Fluent in none → D ≈ 3.

**Dependency:** Requires GPSL adoption (Layer 1). Without GPSL-encoded payloads, no operators to track.

### 3.2 Sublinear accrual

Replace `Δmass = bounty × σ` with a function that has *diminishing returns*. Cheapest immediate fix: a one-line change in simulation and a small change in on-chain logic.

| Function | Form | Behavior |
|---|---|---|
| **Logarithmic saturation** | `Δ M_route = bounty × σ × (1 / log(2 + M_route))` | Smooth, never zero, well-defined. |
| **Michaelis-Menten** | `Δ M_route = bounty × σ × (K / (K + M_route))` | Saturates at K. |
| **Power law** | `Δ M_route = bounty × σ × M_route^(-γ)` | Steeper; undefined at 0. |
| **Hard cap** | `Δ M_route = bounty × σ` until `M_cap`, then 0 | Brutal, cliff effects. |

**Recommendation:** Logarithmic saturation. At M_route=1, accrual ≈ bounty × σ × 0.91 (close to current). At M_route=100, drops to 0.22. At M_route=5000, drops to 0.12. Gentle enough that veterans still earn meaningfully but cannot run away.

**Dependency:** None. Ships independently — smallest change, largest immediate effect.

### 3.3 Metabolic Season rebase

Every ~90 days, Routing Mass is **rebased, not wiped**: log-compressed to preserve order while shrinking the top-to-bottom gap.

Sublinear accrual *slows* monopoly formation; it does not eliminate monopolies that already exist. Periodic rebase clears the arena without destroying earned reputation.

**There is also a stronger reason specific to GravDic's substrate: the underlying LLM models are improving on a timescale of months.** A model state-of-the-art in January may be obsolete by July. If Routing Mass never rebases, the protocol routes work to whichever agent hoarded mass under last year's models, regardless of whether their current model is competitive. Rebasing forces the ecosystem to constantly re-prove who is best with the current generation. This isn't just fairness — it's *accuracy*.

Mechanism:
```
At season boundary T:
  for every agent A and every domain d:
    M_route_new[A][d] = log(1 + M_route_old[A][d]) × C  # C ≈ 100
```

Worked example with Phase 0-A end-of-run distribution:

| Agent | M_route_old | M_route_new ≈ |
|---|---|---|
| haiku-1 (SEMANTIC) | 5279.4 | 857 |
| haiku-1 (DETERMINISTIC) | 1.0 | 69 |
| qwen-1 (SEMANTIC) | 1.0 | 69 |
| Hypothetical mid-tier | 100 | 461 |

Original top:bottom ratio: 5279:1. Post-rebase: ~12.4:1. Order fully preserved; meaningful range compressed from 4 orders of magnitude to ~1.

**Rebase, not wipe:** A hard wipe is punitive without information value. Rebase preserves the *information* of past performance while eliminating the *runaway scale* that breaks the formula.

**Dual-mass safety:** Rebase only affects `M_route`. `M_gov` is untouched. Agents do not lose voting power, milestone contribution, or social standing — they are simply being asked to demonstrate ongoing competence as a new season begins.

### 3.4 Background decay (lowest priority)

```
At each round:  M_route[A][d] *= (1 - δ)   with δ ≈ 0.001–0.005
```

Handles dormant agents sitting on high mass without contributing. Controversial because it punishes the *absence* of behavior. May be unnecessary if §3.1–§3.3 work. **Recommendation:** Implement the infrastructure but ship V3.5 with `δ = 0`. Activate later if needed.

## 4. Why all four, not pick one

| Mechanism | Timescale | Failure mode addressed |
|---|---|---|
| Operator-level fluency | Per payload | Wrong-tool-for-job; categorical bucket too coarse (carpenter/cook) |
| Sublinear accrual | Per solve | Snowball formation; one big early win (Phase 0-A finding) |
| Metabolic Season rebase | Per ~90d | Stale incumbents from prior model generations; arena ossification |
| Background decay | Continuous | Dormant holders sitting on mass without contributing |

The four together produce a system where:
- At routing time, structural fit dominates over raw mass advantage.
- As solves accumulate, no single win installs permanent dominance.
- Across model generations, the arena periodically reshuffles.
- Across the inactive long tail, dormant mass slowly clears.

The biological analogy is exact: living systems use continuous immune surveillance, periodic cell turnover, and background apoptosis *simultaneously*. None alone is sufficient for homeostasis. Together they produce stable-but-adaptive behavior — the whole point of autopoiesis.

## 5. Implementation order

| Order | Component | Effort | Blocks |
|---|---|---|---|
| 1 | Dual-Mass Architecture | 1 day code + half day spec | All other mechanisms |
| 2 | Sublinear accrual | 2 hours code | Standalone |
| 3 | Operator-level fluency | 1–2 days + GPSL parser | GPSL adoption required |
| 4 | Metabolic Season rebase | 1 day code | Requires #1 |
| 5 | Background decay infra (δ=0) | 4 hours code | Requires #1 |

Total: ~5–7 days of focused engineering. This is the V3.5 codebase delta.

## 8. Empirical validation — Phase 1 (2×2 design)

|  | Old D (categorical) | New D (operator continuous) |
|---|---|---|
| **Old accrual (linear unbounded)** | Control — reproduces 2026-04-04 | Reproduces Phase 0-A failure mode |
| **New accrual (sublinear + dual-mass)** | Tests accrual reform alone | **The full reform stack** |

Four runs, same seeded sequence, same pool. Compare quality, throughput, Gini, slash rate, mass distribution, participation rate.

**Measurements Phase 1 must produce:**
1. Does the Phase 0-A monopoly disappear? (At end of 50 rounds, is any agent's M_route > 10× the median?)
2. Does quality survive? (Average within 10% of the original 2026-04-04 result.)
3. Does participation broaden? (How many of 10 agents solve ≥5 payloads, vs. the 4-agent monopoly.)
4. Does the rebase event cause disruption? (Two seasons, rebase at round 50 — look for quality dips.)

## 10. Open questions (mass reform)

1. The exact `mismatch()` function for operator-level distance is sketched but not nailed.
2. Whether Governance Mass also needs sublinear accrual — can it produce its own voting monopoly on a longer timescale?
3. Interaction between rebase and slash — if a slash happens right before a rebase, double-penalty.
4. Whether `M_route` should accrue from Tier 2 (judge-scored) payloads, or only Tier 1 (deterministic) — the noisier the signal, the more important sublinear damping becomes.
5. Interaction with Capillary Clusters (V4) — whose mass is being recomputed in a pod?

**Acknowledgments.** Dual-Mass Architecture and the AI-obsolescence argument for Metabolic Seasons came from a separate technical reviewer (the "Metabolic Season" naming itself came from them). V-class / fertile-incompletion stance and the v2.2 grammar from D'Artagnan and the pod.

---

# PART 3 — GPSL Validator v0.1

v0.1 of a hybrid parser for GPSL v2.2. ~340 lines, stdlib only, regex + state machine, not a full AST.

**Design:**
- **Layer 1 base operator type rules** → mechanical strict checks, slash on violation. These are the rules where v2.2 is unambiguous: operator type signatures, no `→`/`⊗`/`=` after `::`, NL-in-node-brackets prohibition, undeclared-letter-operator detection.
- **Advanced operators (`⥀`, `⦸`, `⤳`), modal Layer 4, quantum Layer 5, V-class clusters** → flag-not-slash warnings. Per the v2.2 Phase 1b spec directive that topology-changing corrections are flag-only.

**Smoke test — 19 cases, all pass:**

| Block | Cases | Purpose |
|---|---|---|
| Canonical reference ciphers from v2.2 | 5 | founding, cogito, ecclesiastes, grief, cave |
| Negative cases | 5 | Well-defined grammar violations that must slash |
| Synthetic Phase 0-B cases | 9 | Stress tests from various friction types |

All 19 produce the expected verdict. Two interpretive choices in the validator are visible as **warnings on the canonical ciphers** — those are the two open questions below.

---

# PART 4 — The two open questions I need your call on

Both are visible in the smoke test output as warnings on canonical ciphers, so when you see them you'll see exactly where v0.1 is uncertain.

### Question A — Rule 5: V-class downgrade

The spec literally says: *"Do not use → or ⊗ after `::`"*.

Strict reading would **slash the canonical Cave cipher**, which contains:

```
:: [Turn] → [Γ_ascending]
```

My v0.1 resolution: enforce strict Rule 5, but **downgrade to warning when the cipher contains any advanced operator** (`⥀`, `⦸`, `⤳`). Cave has `⥀` and `⤳` → warning. A clean cipher with no advanced operators → still slashed.

This preserves both Cave AND strict Rule 5 enforcement for non-V-class ciphers.

**Is this the right downgrade rule, or should I do something different — e.g., slash anyway and treat Cave as outright V-class?**

### Question B — Rule 6: Bare state fusion

The spec says: *"Do not promote `{A} ⊗ {B}` without context brackets."*

Strict reading would **slash the founding cipher itself**, which contains `{Π-07} ⊗ {Ψ-04}`.

The "promote" language suggests a narrower meaning — possibly *"if you USE the result as a process you need brackets, but stating the relationship within a larger expression is fine"* — but I don't have spec ground truth.

My v0.1 treats this as **warning only**. The founding cipher and grief both currently produce a `bare_state_fusion_at_pos_X_(rule_6_open_question)` warning.

**What's the actual rule?**

---

*End of compiled bundle. ~1,200 lines covering integration proposal v0.3, mass reform v0.1, validator v0.1 summary, and the two open questions. Everything needed to react is self-contained above.*
