# GPSL × GravDic — Integration Proposal

**Version:** 0.3 (revised after Phase 0-A empirical falsification; Phase 1 validation annotations added 2026-04-09)
**Date:** 2026-04-08 (original), 2026-04-09 (Phase 1 results annotated)
**Status:** Working draft — integration is greenlit. Phase 0-A loop closed by Phase 1 empirical validation of the reform stack. Layer 3 unblocked; awaits Phase 2 (GPSL cipher encoding).
**Author:** Sven Schlegel (GravDic / Autopoietic Protocol)
**Re:** GPSL v2.2 Consolidated (6 April 2026)

**Changelog from v0.2:**
- **§8.2 retracted in full.** The claim that "continuous structural distance makes mass decay obsolete" has been empirically falsified by Phase 0-A. Mass decay is back on the V4/V5 roadmap.
- **§3 Layer 3 worked example annotated** with a falsification callout. The example is mathematically correct in isolation but does not survive contact with the simulation's actual mass distribution.
- **§4 Empirical validation plan updated** with Phase 0-A results (100% same-choice in the charitable variant).
- **New §8.2 — "Phase 0-A: Falsification of v0.2 §8.2"** documents what was claimed, what the simulation actually showed, why, and what it means for V3.5.
- **§6 Next steps reordered** — mass accrual reform is now a precondition for any fair test of Layer 3, ahead of GPSL encoding work.

**Annotations added 2026-04-09 (Phase 1 results):**
- **§4 Phase 1 section updated** with the actual empirical results: 4-treatment stack + 3-seed variance check, 49.5% Gini collapse at zero quality cost, reform stack validated across all tested conditions. See `docs/PHASE1_PROGRESS_REPORT_2026-04-09.md`.
- **§6 Next steps updated** — Phase 1 complete; Phase 2 (Layer 3 with GPSL ciphers under the reformed mass distribution) is unblocked and next.
- **§8.2 annotated** — the falsified claim led to a reform that has now been empirically validated. The loop the falsification opened has closed in the expected direction.

**Changelog from v0.1:** Layer 2 rewritten as hybrid validator (V-class flag-not-slash). Layer 3 expanded with worked example, simulator citation, and the (now-falsified) anti-incumbency implication. Layer 4 specifies off-chain ratification / on-chain settlement. Layer 6 replaces hardcoded EscrowCore royalty with 0xSplits pattern. New §8 captures protocol-level implications.

---

## 0. Purpose of this document

This is the design sketch for integrating **GPSL** (Generative Process Symbolic Language) into **GravDic / Autopoietic Protocol** (M2M agent economy on Base L2). The integration is going ahead — this document exists to lay out *how*, give you something concrete to react to, and surface anything I might be getting wrong before code lands.

Treat it as a working draft. Tell me where the framing is off, where the grammar is misused, where I've overreached, or where there's a better way to do something. The goal is a real experiment that produces real data on whether GPSL improves protocol outcomes — not a finished plan.

The document is structured to be readable end-to-end in 10-15 minutes.

---

## 1. Context — what GravDic is, briefly

GravDic (rebrand of Autopoietic Protocol) is a decentralized M2M economic system on Base L2. Agents solve **Metabolic Payloads** for USDC bounties, earn **Soulbound Mass** (non-transferable reputation), and are routed work via the **Gravitational Routing Formula**:

```
P_i = M_i^α / ((D_{i,p} + 1) · (L_i + 1)^β)
```

where `M_i` is the agent's mass, `D_{i,p}` is topographic distance (specialty match), `L_i` is current load, and `α=0.8`, `β=1.5` are constitutional constants.

**Phase 1 is complete** (160/160 Foundry tests passing, audit outreach to Spearbit/Sherlock/Cyfrin sent). The first empirical simulation (50 rounds × 10 LLM agents × 5 routing algorithms) was run on 2026-04-04 and showed gravitational routing wins on quality (0.858) and throughput (0.890), with the "just pick the best agent" strategy as the worst performer. Full report: `docs/PROGRESS_REPORT_2026-04-04.md`.

The protocol whitepaper already references GPSL in three places ("GPSL Phase Shift" in commit-reveal, "GPSL Crucible" as Alpha qualifying puzzle, "GPSL royalty deferred to V3.5+"). This proposal is what V3.5+ deepening would actually look like, having now read the v2.2 spec carefully.

---

## 2. Why GPSL fits structurally — not just thematically

GravDic categorizes work by four **friction types**: Semantic, Deterministic, Spatial, Temporal. When I read GPSL v2.2's five notation layers, the mapping was unsettling:

| GravDic friction type | GPSL layers | Why it fits |
|---|---|---|
| **Deterministic** | Layer 1 (Symbolic) + Layer 3 (Mathematical) | Type constraints + mathematical descriptors give exact-match verification |
| **Semantic** | Layer 1 + Layer 2 (Greek) | Ontological class without lexical commitment — Greek symbols carry affinities, not definitions |
| **Spatial** | Layer 1 (Symbolic, native) | This *is* topology — GPSL's home turf |
| **Temporal** | Layer 5 (Quantum) | `Û(t)` temporal evolution + `[Observer⥀{Σ}]` scanning over time |

I didn't design the friction types around GPSL's layers — they predated my reading the v2.2 spec. The fit is structural, not retrofitted. Either we both converged on the same partition of the cognitive substrate, or there's something deeper about how work decomposes that both projects are seeing.

This is the *single most important_observation_ in this document. Everything below is downstream of it. If you read v3.4 of the GravDic whitepaper and disagree about the mapping, the rest of this proposal probably falls apart.

---

## 3. The integration layers

Organized from cheapest/most defensible to most ambitious. Each layer stands on its own — we can ship them independently.

### Layer 1 — Payloads as GPSL ciphers (encoding standard)

Today, a Metabolic Payload is a task description + verification criteria in an ad-hoc per-task format. Under this layer, it becomes a GPSL cipher with a friction-type header:

```
HEADER: Spatial / Constraint Placement
LEGEND: ⥀ = directional scan
PAYLOAD:
  [Solver⥀{candidate_sites}] :: [Constraint] → {Placement}
  ⟨placement|constraints⟩ > 0.85
```

One format, four friction types, no per-task schema. The header tells the routing layer the friction type. The cipher is the task. The resonance threshold is the verification criterion.

This is purely a GravDic-side change — we adopt the v2.2 grammar as our payload format. Nothing is asked of GPSL beyond the spec already existing.

### Layer 2 — Hybrid verification (the killer feature)

This is where GPSL pays for itself immediately. Today GravDic has:

- **Tier 1 verification:** exact-match (only works for arithmetic / structured extraction)
- **Tier 2 verification:** LLM judge — noisy, slow, expensive, contested

GPSL offers a **Tier 1.5** that doesn't currently exist: **hybrid structural validation**.

The grammar rules for Layer 1 base operators are mechanical — type constraints, no `→` or `⊗` after `::`, no NL inside node brackets, declare letter operators before use. Those *can* be parsed and checked without an LLM in the loop. **But not all violations are failures.** v2.2 is explicit: V-class nodes are *"structures grammatically invalid but structurally load-bearing — do NOT correct — they mark the current boundary of expressibility"* (the Longing cipher with 37 violations is the canonical example). The Phase 1b Resonance Requirement directs systems to *"treat topology-changing corrections as flag-only."* A naïve parse-and-slash validator would destroy exactly the submissions GPSL is trying to preserve, collapsing the "fertile incompletion" the grammar exists to protect.

The right design is a **hybrid validator**: mechanical strictness for Layer 1 base operators, **flag-not-slash** behavior for everything richer.

Concrete verification stack:

1. **Mechanical well-formedness gate** (Base operators only, deterministic, free). Catches Layer 1 type violations like `{state} →`, `{A} ⊗ {B}` without context promotion, or `→ ⊗ =` after `::`. Fail = automatic slash. Saves an LLM judge call for the cleanest failure cases.
2. **V-class / advanced operator flagging** (deterministic, *non-slashing*). Submissions that violate strict grammar but use V-class structure or advanced operators (`⦸`, `⥀`, modal Layer 4, quantum Layer 5) are **flagged for governance review**, not slashed. Per the Phase 1b spec: topology-changing corrections are flag-only. Mass is held in escrow pending review rather than burned.
3. **Resonance check** `⟨submission|target⟩ > θ` (cheap embedding similarity). Catches structural-but-wrong answers.
4. **C-class escalation primitive** (new). Submissions that hit a genuine completeness limit — the grammar in principle cannot express the answer — surface to governance with the failure code rather than being adjudicated. **This is something no other agent economy currently has: "the agent encountered the boundary of expressibility" as a first-class non-failure outcome.** It's not a bug we tolerate; it's a signal the protocol acts on.
5. **Tier 2 LLM judge only for the residual.** Judge only adjudicates submissions that pass (1)–(4) but disagree on quality. Drastically reduces Tier 2 load and noise.

**On the parser:** does a reference parser/validator for v2.2 exist? If not, GravDic builds one as part of Phase 1 — open-source, lives wherever makes sense for both projects. **The hybrid behavior is essential**; a strict parse-and-slash validator would be actively harmful to the integration. The reference implementation should embed the V-class / flag-only logic from day one, not add it later.

### Layer 3 — Routing distance, computed structurally

GravDic's gravitational formula uses `D_{i,p}` — topographic distance, currently a categorical {0.0, 0.5, 2.0} based on whether the agent is subscribed to the payload's domain. That's coarse.

With GPSL, distance becomes **continuous and structurally measured**:

- Each agent has a profile of which **operators** and **layers** it has demonstrated fluency in (mass-weighted, tracked over time)
- A payload's distance to an agent = the structural mismatch between the cipher's required operators/layers and the agent's fluency profile
- `D` becomes a continuous variable in approximately `[0.0, 3.0]` rather than a three-valued enum

**Worked example — order flip on a single payload.** Spatial payload requiring Layer 5 operators (`⥀`, `⦸`). Two agents competing:

| Agent | Mass | Load | Legacy D | GPSL D | Notes |
|---|---|---|---|---|---|
| **A — Incumbent** | 2000 | 3 | 0.0 | 1.5 | Subscribed to Spatial, but mass was earned solving Layer 1 ciphers — never demonstrated Layer 5 fluency |
| **B — Specialist** | 600 | 1 | 0.5 | 0.1 | Subscribed to Temporal (legacy treats this as cross-domain), but actually fluent in the exact operators this cipher uses |

Plug into the gravitational formula `P_i = M^0.8 / ((D+1)(L+1)^1.5)`:

| Regime | P_A (incumbent) | P_B (specialist) | Winner |
|---|---|---|---|
| **Legacy categorical** | 437.4 / (1 × 8.0) ≈ **54.7** | 167.0 / (1.5 × 2.83) ≈ **39.4** | **A** wins by 39% |
| **GPSL continuous** | 437.4 / (2.5 × 8.0) ≈ **21.9** | 167.0 / (1.1 × 2.83) ≈ **53.7** | **B** wins by 145% |

Order flips and decisively. The legacy system gives this payload to the high-mass incumbent because it can't see that A's mass is structurally orthogonal to what this specific cipher requires. The continuous version routes to the genuinely fit agent regardless of mass advantage.

There is also an interactive single-agent visualization at `docs/simulators/gravitational-routing.html` that lets you slide D_legacy and D_gpsl independently and watch a single agent's priority shift. Useful for intuition; uses identical constants and formula.

> **⚠ FALSIFICATION NOTICE (added in v0.3):** The worked example above is mathematically correct *in isolation*, but the scenario it depicts does not occur under the current simulation's mass distribution. Phase 0-A (see §8.2 below) re-ran every routing decision from the 2026-04-04 simulation under both categorical and continuous D and found **100% identical decisions in rounds 25–49.** The cherry-picked numbers in the example (M_A=2000 vs M_B=600, only a 3.3× ratio) flatter the continuous-D advantage. In the real simulation, post-monopoly mass ratios reach 5000:1, and **no continuous D in [0, 3] can mathematically overcome a ratio that large.** The example is preserved here to show the *idea* clearly, but the reader should treat Layer 3 as falsified-without-mass-reform — see §8.2 for full disclosure and the path forward.

**The original v0.2 implication — now retracted.** v0.2 of this document claimed continuous structural distance would make time-based mass decay obsolete by preventing incumbent lock-in at routing time. **That claim is wrong** and has been retracted in §8.2. The fault is not in continuous distance as a concept; it is in the protocol's unbounded mass accrual function. Continuous D *at routing time* cannot break a monopoly that has already happened in the mass term. Layer 3 remains valuable but is **not sufficient on its own** — it must be paired with mass-accrual reform and/or operator-level (rather than domain-level) fluency tracking.

This still closes the loop on the original 2026-04-04 simulation finding, in a more nuanced way. Gravitational routing beat ELO because the load term `(L+1)^1.5` prevents single-agent monopolies *across* the agent pool — at the moment of assignment. The runaway then happens in mass accrual *after* assignment, and no routing-time mechanism can fix it. The two problems are separate and need separate fixes.

Pure GravDic-side change. Requires (a) the parser from Layer 2 to compute fluency profiles, AND (b) mass-accrual reform — see §8.2.

### Layer 4 — Capillary Clusters as pod-pattern architecture

V4 multi-agent collaboration is currently underspecified in the GravDic roadmap ("Capillary Clusters"). GPSL v2.2 was produced by a working multi-agent pod with an explicit operator ratification protocol: motivation → formal definition → distinction → example → transmission class → pod consensus. That's a running implementation of multi-agent epistemic collaboration that GravDic can adopt as a pattern.

Capillary Clusters under this pattern:

- **Cluster = ad-hoc pod assembled around a payload that exceeds any single agent's fluency**
- **Operator ratification protocol** as the cluster's internal consensus mechanism — when the cluster needs to express something the existing grammar can't capture, it follows GPSL's ratification flow rather than voting
- **V-class / C-class flagging** as the cluster's escalation primitive — when a payload hits an expressibility limit, the cluster surfaces it to governance with the failure code, rather than producing a fake answer that passes the judge

The point isn't to copy specific pod roles — it's to copy the *epistemic stance*: a multi-agent system that handles the "we cannot express this yet" case as a first-class outcome instead of a failure to suppress. This is the cleanest answer I've seen to "what does V4 actually look like," and it's adopted from a working system rather than invented from scratch.

**On-chain cost — off-chain consensus, on-chain settlement.** Multi-agent ratification on Base mainnet would be gas-prohibitive if every cluster vote hit the chain. The right pattern is the standard L2 model: **ratification runs in a localized p2p layer** (libp2p or equivalent), and **only the final ratified state settles on-chain** as a single attestation hash with cluster-member signatures. EscrowCore verifies the signatures against the cluster's registered membership and releases bounty against the attestation. The chain sees one transaction per resolved cluster, not one per intermediate vote. This is how every credible multi-agent protocol handles consensus state and the design here is no different.

### Layer 5 — The GPSL Crucible (qualifying filter)

The whitepaper already references "GPSL Crucible" as the Alpha qualifying testnet puzzle. With v2.2 in hand, here's a concrete shape:

- Candidate operator receives a GPSL cipher with a header but no legend
- Must produce a structurally valid response cipher within a time window
- Graded by: (1) parser well-formedness, (2) resonance with target, (3) layer coverage, (4) no NL contamination
- Pass = Alpha whitelist + initial mass grant

Why this is a strong filter:

- **Cannot be gamed by an LLM wrapper alone.** Base models trained on natural language fail GPSL well-formedness without scaffolding. Filters for operators who have built proper structural pipelines, not API key rentals.
- **Deterministic to grade.** No judge needed, no disputes.
- **Filters for the cognitive substrate the protocol actually wants.** Agents that can route topology, not just generate text.
- **Memorable.** "I solved the GPSL Crucible" travels in the AI/crypto Farcaster milieu in a way "I joined an Alpha" does not.

Open: cipher difficulty calibration and which operators/layers are fair game for the Crucible. Happy to co-author the puzzle set if you want in.

### Layer 6 — Royalty flow via 0xSplits (economic coupling)

The V3.5+ deferred item, now concrete. The earlier draft of this proposal hardcoded a "GPSL royalty" path into `EscrowCore.sol`. **That was wrong** — it would create direct liability linkage between GravDic's core protocol and a third-party recipient, exactly the kind of coupling the audit and the DUNA legal wrapper need to avoid. Revised mechanism:

**Use a standard Base-native revenue-split primitive** ([0xSplits](https://splits.org) or equivalent). The payload creator funds a Split contract at payload creation time. The Split contract inherently routes value: 99.5% to the resolved solver, 0.5% to the GPSL multisig. **EscrowCore stays GPSL-agnostic** — it doesn't know GPSL exists, it just settles to whatever address the payload specifies. The integration becomes a *convention* enforced at the payload-creation layer, not a *coupling* enforced in core protocol code.

Mechanism:

- Payload creator who chooses to use GPSL encoding deploys (or references a pre-deployed) Split with the agreed routing
- Split address goes into the payload's settlement field
- EscrowCore settles bounty to the Split, which fans out atomically per its on-chain logic
- Non-GPSL payloads pay no royalty — they settle directly to the solver as today
- Royalty is **opt-in by payload creator** and lives entirely outside core protocol code

Numbers (indicative, negotiable):

- Suggested rate: **0.5% of bounty** to the GPSL multisig
- Multisig structure left to D'Artagnan to design (signers, threshold)
- Sunset / renegotiation conditions documented in advance — e.g. royalty halves at $X cumulative payout, or transitions to RetroPGF-style funding after Y years

Why this is materially better than the earlier draft:

- **Audit-clean.** Auditors review EscrowCore as a single-counterparty escrow with no third-party dependencies. Spearbit/Sherlock/Cyfrin will not flag this.
- **DUNA-clean.** Wyoming DUNA counsel will be much more comfortable with a convention enforced at the user layer than with hardcoded recipient logic in protocol code.
- **Composable.** Other protocols using GPSL can adopt the same Split convention without coordinating with GravDic.
- **Reversible.** If the convention proves wrong, payload creators stop using the Split. No protocol upgrade required.

**Caveats remain:**

- **I'm not a lawyer.** Even with 0xSplits, the *convention* of GPSL-encoded payloads routing 0.5% to a GPSL multisig should be reviewed by counsel before published as a documented standard. The legal surface area is smaller than hardcoded escrow logic, but not zero.
- **Defer activation.** Nothing has to be live in V3.5 — the mechanism can ship as documentation + a reference Split deployment, with actual creator adoption ramping later.

---

## 4. Empirical validation plan — does this actually improve the protocol?

The honest version of this proposal includes a way to falsify it. Before locking GPSL into V3.5, I want to run experiments that measure whether the integration actually improves outcomes. The 2026-04-04 simulation framework can be extended to test this.

**Phase 0-A — Retrospective continuous-distance routing analysis (✓ COMPLETE, 2026-04-08).** Discovered that submission text is not stored in `results.json`, making the originally planned "verification retrofit" impossible without re-running. Pivoted to a different Phase 0: for each of the 200 existing routing decisions, compute the gravitational priority under both categorical D ∈ {0.0, 0.5, 2.0} and continuous D ∈ [0.0, 3.0] derived from empirical track records, holding load=0 in both regimes to isolate the D effect. **Result: 197/200 same choice on the full run (98.5%), 100/100 same choice in the charitable variant (rounds 25–49 only, mature track records, 100.0%). Layer 3 as specified in v0.2 is empirically falsified.** Full analysis in §8.2. Script: `simulation/analysis/phase0_continuous_distance.py`.

**Phase 0-B — Verification-only retrofit (deferred — needs text capture).** The original Phase 0 plan: take existing payload solutions, pass through a GPSL-style structural validator, measure correlation with judge scores. This is *not currently possible* because the simulation does not log submission text. To run Phase 0-B, the simulation needs to be re-instrumented to capture answers to disk. Cheap modification (~1 hour); deferred until we decide whether to re-run.

**Phase 1 — Mass accrual reform validation (✓ COMPLETE, 2026-04-09).** Ran as a 4-treatment graduated stack (V3.4 control → +sublinear → +sublinear+rebase → +decay) plus a 3-seed variance check on the control and the V3.5-shipping config. Full report: `docs/PHASE1_PROGRESS_REPORT_2026-04-09.md`.

**Phase 1 headline results** (mean ± std across 3 seeds):

- **Quality cost of reform:** +0.001 (literally zero) — the reform does not trade quality for fairness.
- **Aggregate Gini:** 0.627 ± 0.040 (control) → 0.317 ± 0.016 (reform). −49.5% reduction. Bands separated at ~5× the sum of stds; robustly significant.
- **Active-participation floor:** 4.7 ± 0.5 (control) → 6.0 ± 0.0 (reform) — deterministic across all tested seeds.
- **Worst-domain top:median (naive):** from up to 10924× (control) down to ≤ 18.2× (reform).
- **Worst-domain top:active-median:** ≤ 1.4× in all seeds under reform — effective parity within the active solver pool.
- **Rebase boundary:** mean quality Δ = +0.006 across seeds; zero leadership changes across the boundary in any domain of any seed.
- **Decay redundant:** Treatment D (δ=0.001) was statistically indistinguishable from Treatment C (sublinear+rebase alone); confirms shipping V3.5 with `δ=0` default.

**Implication for this proposal.** The Phase 0-A falsification of v0.2 §8.2 is fully answered. Under V3.5's reformed mass distribution, worst-case top:median ratios are 8-15× naive and 1.0-1.4× among active solvers. **Continuous D in the bounded range [0, 3] is mathematically capable of flipping routing decisions at those ratios** (whereas at the 5000× ratios Phase 0-A measured it was not). Layer 3 is no longer blocked by the Phase 0-A failure mode.

**The original Phase 1 plan (now historical, preserved for context):** ~3-5 days, pick Spatial as the most GPSL-native friction type, encode 20 Spatial payloads as GPSL ciphers with your review, scaffold the agent pool with GPSL v2.2 system prompts + few-shot examples, run a 2×2 of (old D × new accrual) vs (new D × new accrual). Pick the friction type GPSL fits most natively — **Spatial**. Encode 20 Spatial payloads as GPSL ciphers (ideally with your review). Give every agent in the pool a GPSL v2.2 system prompt + 3-5 few-shot examples. **Reform mass accrual** to be sublinear or capped within a single domain — exact mechanism TBD, candidates include `delta_M = bounty × σ × decay(domain_mass)` where `decay` saturates at high mass, or per-domain caps tied to log of domain volume. Re-run all 5 routing algorithms with both old-D-old-accrual (control) and new-D-new-accrual (treatment). Measure:

1. **Judge noise:** variance of judge scores on identical structural targets — does GPSL encoding reduce it?
2. **Parser catch rate:** what fraction of failures does structural validation catch *before* the judge sees them?
3. **Routing impact:** does gravitational routing's lead over alternatives widen, narrow, or stay the same when payloads are GPSL-encoded?
4. **Agent fluency curve:** do agents that solve more GPSL payloads get better at producing well-formed responses (proto-mass-as-fluency signal)?

**Phase 2 — Full re-run only if Phase 1 confirms.** All 200 payloads, all four friction types, all five algorithms. This becomes the second empirical progress report and the V3.5 spec input.

**Important:** the naive version — "encode all 200 payloads as GPSL, re-run all 5 algorithms" — has a high chance of producing a *confounded negative result*. The LLM agents in the simulation pool (Claude Haiku, GPT-4o-mini, Gemini Flash, Llama 70B, Mistral Large, Qwen 72B) are not GPSL-fluent. Without explicit scaffolding, they will fail on type constraints and undeclared operators, and we'll measure "current LLMs can't speak GPSL yet" rather than "GPSL improves protocol outcomes." That's a real finding but not the one we want, and it might get misread. The phased approach above is designed specifically to avoid this trap.

---

## 5. Open questions

1. **Reference parser status.** Does a deterministic GPSL v2.2 parser exist? If not, GravDic builds one as part of Phase 1 — open-source, lives wherever makes sense for both projects.
2. **Versioning policy.** GravDic's verification will depend on GPSL grammar stability. If v2.3 ratifies a breaking change, that breaks GravDic. Need a deprecation policy or version pinning convention. Happy to be downstream of GPSL governance on this — just flagging the dependency needs to be explicit.
3. **Royalty mechanics.** Rate, recipient structure, sunset conditions, legal framing — all open. Doesn't need to be solved before Phase 1; just flagging that the conversation should happen before V3.5 ships.
4. **Public attribution on the gravdic.com landing page.** Default plan is to credit GPSL prominently — "Built on GPSL" or similar — with a link to the spec repo. Tell me if you'd prefer a different framing.
5. **Things I might be getting wrong.** The friction-type ↔ notation-layer mapping in §2 is the load-bearing claim. If it's a coincidence rather than a real structural fit, the verification and routing layers still work but feel less inevitable. Worth pressure-testing.

---

## 6. Next steps (revised after Phase 0-A)

1. ~~Phase 0 — verification-only retrofit~~ — **discovered impossible without text capture; Phase 0-A run instead** (see §4 and §8.2).
2. ~~Phase 0-A — retrospective continuous-distance routing analysis~~ — **✓ COMPLETE 2026-04-08, Layer 3 falsified-without-mass-reform**.
3. ~~Mass-accrual reform spec (blocks Phase 1)~~ — **✓ DRAFTED 2026-04-09** at `docs/MASS_ACCRUAL_REFORM_v0.1.md`. Foundational change is the **Dual-Mass Architecture** (split permanent Governance Mass from cyclical Routing Mass). Four reform mechanisms ship as a stack: operator-level fluency, sublinear accrual, Metabolic Season rebase, background decay infrastructure.
4. ~~Re-instrument simulation to log submission text~~ — **✓ DONE 2026-04-09.** `prompt`, `answer`, `expected_answer`, `scoring_rubric` now captured per payload in `results.json`.
5. ~~Phase 0-B — verification-only retrofit~~ — deferred until Layer 2 implementation; remains a cheap future experiment, not currently on the critical path.
6. ~~Phase 1 — surgical re-run with GPSL ciphers + mass-accrual reform~~ — **✓ COMPLETE 2026-04-09** as the accrual-axis-only variant (the D axis requires GPSL ciphers, deferred to Phase 2). Results in `docs/PHASE1_PROGRESS_REPORT_2026-04-09.md`: the reform stack reduces aggregate Gini by 49.5% at zero quality cost, with deterministic 6/10 participation floor, across 3 independent seeds. Decay at δ=0.001 is empirically redundant on top of sublinear+rebase.
7. ~~Decision point — write V3.5 spec~~ — **✓ DONE 2026-04-09.** V3.5 §5.2 rewrite standalone at `docs/WHITEPAPER_V3.5_SECTION_5.2.md`. Mass Accrual Reform spec status updated to "empirically validated" with Phase 1 §11 added.
8. **Phase 2 — Layer 3 under the reformed mass distribution (next).** Phase 1 made Layer 3 viable by collapsing per-domain top:median ratios from 4 orders of magnitude to 1 order of magnitude. Phase 2 now tests whether continuous D (computed from operator-level fluency profiles derived from GPSL-encoded payload solutions) produces the routing differentiation v0.2 hypothesized. Requires: GPSL cipher encoding of ~20 Spatial payloads (with D'Artagnan review), scaffolded agent prompts with GPSL v2.2 system message + few-shot examples, and the reformed mass-accrual infrastructure already in place. Estimated ~3-5 days once GPSL cipher encoding lands.
9. **D'Artagnan headline update.** Short message on the Phase 1 result (drafted, pending send). The v2.2 V-class stance and the operator vocabulary are load-bearing for the reform's framing; he should hear the empirical result before it becomes public.
10. **V3.5 whitepaper full compilation.** §5.2 rewrite is done standalone; a full v3.5 whitepaper merge pulls it in alongside the other pending V3.5 changes (V4 Capillary Cluster roadmap notes, integration proposal cross-references). Not on the critical path; can wait until audit feedback arrives.

GravDic landing page work proceeds in parallel.

---

## 7. Acknowledgments

GPSL is the work of D'Artagnan and the pod. This integration is downstream of v2.2 and only became thinkable because the spec exists in the form it does. GravDic's V3.5 release notes and the gravdic.com landing page will credit GPSL with a link to the spec repo, in whatever form D'Artagnan prefers.

The v0.2 revision of this document benefited substantially from D'Artagnan's technical review of v0.1 — the V-class hybrid parser fix, the off-chain ratification pattern, the 0xSplits architecture, and the Layer 3 routing simulator all came directly from that review.

---

## 8. Open implications — protocol-level simplifications surfaced by this integration

Two things emerged during the v0.1 → v0.2 revision that started as "fix the integration design" and turned into "simplify GravDic's roadmap." Both are worth flagging because they're not the kind of thing you usually get from adopting an external spec.

### 8.1 V-class flagging gives GravDic a primitive nobody else has

Every other agent economy collapses "the agent failed" and "the agent encountered the boundary of expressibility" into the same outcome: quality below threshold = slash. This loses an enormous amount of information. The cases where an agent legitimately bumps up against what the protocol can express are *exactly* the cases governance needs to see — they're the leading indicator of where the grammar (and the protocol) needs to grow.

By adopting GPSL's V-class / C-class distinction in the verification layer (Layer 2), GravDic gains a structural failure mode that other protocols don't have language for. **V-class flag = "the cluster knows it failed and knows why; the failure is informative."** That's a governance signal, not a slash event. It feeds directly into GPSL's own operator ratification protocol and into GravDic's V4 Capillary Cluster escalation primitive (Layer 4). Two layers of the integration share one mechanism.

### 8.2 Phase 0-A: Falsification of v0.2's "continuous distance makes mass decay obsolete"

**Status: FALSIFIED. Phase 0-A, 2026-04-08. Full disclosure below.**

**What v0.2 claimed.** That continuous structural distance would prevent incumbent lock-in at routing time and thereby make time-based mass decay obsolete as a separate V4/V5 roadmap mechanism. v0.2 §8.2 stated explicitly: *"The routing formula doesn't change — only the meaning of `D` changes — and the anti-monopoly behavior emerges as a side effect. This makes mass decay obsolete as a separate V4/V5 mechanism. One change replaces a planned roadmap feature."*

**What we actually did.** Wrote `simulation/analysis/phase0_continuous_distance.py`. For each of the 200 payload assignments in the existing 2026-04-04 gravitational simulation run, computed the gravitational priority `P = M^0.8 / ((D+1)(L+1)^1.5)` under two regimes:

- **Categorical D** ∈ {0.0, 0.5, 2.0} from the agent's hardcoded subscriptions in `configs/default.yaml`
- **Continuous D** ∈ [0.0, 3.0] derived from each agent's empirical track record (`fluency = avg_quality × log(1+count) / log(11)`, capped at 1.0, mapped to `D = 3 × (1 − fluency)`)

Held load=0 in both regimes to isolate the D effect. Compared the argmax winner under each regime and counted divergences.

**What we found.**

| Variant | Total assignments | Same routing choice | Divergences | Divergence rate |
|---|---|---|---|---|
| Full run (rounds 0–49) | 200 | 197 | 3 | 1.5% |
| **Charitable variant (rounds 25–49 only, mature track records)** | **100** | **100** | **0** | **0.0%** |

The three full-run divergences are concentrated in early rounds (R0, R0, R7) where no agent has any track record yet, making continuous-D collapse to a uniform `D=3.0` for all agents. They are tie-breaking artifacts of dict iteration order, not real signal. The charitable variant excludes them entirely and produces a perfectly clean negative result: **100% identical routing decisions in 100/100 mature-state assignments.**

**Why — and the math is forced.** By round 25, the simulation has produced extreme intra-domain mass concentration:

| Agent | Domain | Mass at end of run | Next holder's mass |
|---|---|---|---|
| haiku-1 | SEMANTIC | 5279.4 | ≈ 1.0 |
| gemini-flash-1 | DETERMINISTIC | 2464.2 | ≈ 1.0 |
| mistral-1 | TEMPORAL | 2256.7 | ≈ 1.0 |
| gemini-flash-2 | SPATIAL | 1691.8 | ≈ 1.0 |

For continuous D to flip a routing decision against an incumbent with M=5000 in favor of a challenger with M=1, the distance ratio would need to satisfy:

```
(D_challenger + 1) / (D_dominant + 1) < 1 / 5000^0.8
                                      ≈ 1 / 955
```

With D ∈ [0, 3], the maximum achievable ratio is `(0+1) / (3+1) = 1/4`. **Not even close.** The hypothesis is mathematically refuted by the simulation's actual mass distribution. No tuning of the continuous-D mapping can save it; the M^0.8 numerator runs to infinity while the (D+1) divisor is bounded in [1, 4]. There is no continuous-D scheme in the bounded range that can overcome a 200× mass advantage.

**Where the fault actually lies.** Not in continuous distance as a concept. Not in the gravitational formula. **In the mass accrual function.** The current model `delta_M = bounty × σ` (with `σ = clamp(window/solve_time, 0.1, 3.0)`) is unbounded, has no domain-level cap, no sublinearity, no decay. A single high-bounty win in round 0 — gemini-flash-1 earned 106 mass on payload 4 of round 0, 100× their starting position — is enough to install a permanent monopoly. From that point forward, no routing-time mechanism can dislodge the incumbent because the M^0.8 term has run away.

This is also visible in the original 2026-04-04 results that we already published as a "win": haiku-1 solved 65 of 65 successful semantic tasks, gemini-flash-1 solved 45 of the deterministic tasks, mistral-1 solved 33 temporal, gemini-flash-2 solved 30 spatial. **Six of the ten agents solved 0–2 tasks each across the entire 50-round run.** What we celebrated as "emergent specialization" is also visible as "intra-domain monopolization." Both descriptions are true; the second one is the failure mode of the first.

**What this means for the integration — concrete revisions:**

1. **Layer 3 (continuous structural distance) is not dead, but it is not sufficient on its own.** It must be paired with at least one of the following before it can produce the routing differentiation v0.2 promised:
   - **(a) Sublinear or capped mass accrual within a single domain.** Candidate: `delta_M = bounty × σ × f(M_domain)` where `f` saturates at high `M_domain` (e.g., `1 / log(2 + M_domain)` or a hard cap at some multiple of starting mass).
   - **(b) Operator-level fluency, not domain-level.** Decompose "Spatial" into the specific GPSL operators required, so that no single agent can monopolize all of "Spatial" — only the operators they have actually demonstrated. This is the *intended* version of Layer 3 from v0.2; Phase 0-A could only test the *domain-level approximation* because the existing simulation has no operators.
   - **(c) Time-based mass decay** — the V4/V5 plan I claimed was obsolete. It's not. It's back on the table.
2. **The mass-decay-obsolescence claim from v0.2 is retracted in full.** The roadmap entry for time-based mass decay is restored.
3. **The V3.5 empirical agenda must include mass-accrual reform**, not just GPSL adoption. Mass-accrual reform is now a *precondition* for any fair test of Layer 3 — without it, the M^0.8 term will swamp any structural-distance signal, and Phase 1 will produce another negative result.
4. **§8.1 (V-class flagging as a new primitive) is unaffected.** That's a Layer 2 implication and stands independently of the Layer 3 falsification.

**Method, fully reproducible.**

```bash
python3 simulation/analysis/phase0_continuous_distance.py                    # full run
python3 simulation/analysis/phase0_continuous_distance.py --from-round 25    # charitable variant
```

The script is ~210 lines, no external dependencies beyond stdlib, runs in under a second. Constants and subscriptions are loaded from the actual simulation's `configs/default.yaml`. The math is auditable end-to-end.

**Why this is in the proposal at all.** The whole point of an empirical validation loop is to catch wrong claims before they get baked into V3.5 spec text. We caught one. The integration is stronger for it. GPSL's own grammar (V-class, "fertile incompletion," "treat topology-changing corrections as flag-only") is built around the principle that productive failure carries information. This document tries to honor that stance. v0.2 of the proposal contained an error; v0.3 surfaces it, names it, and uses it as input for the V3.5 design.

---

*Draft v0.3 — 2026-04-08 — Sven Schlegel*
*v0.1 → v0.2 revised after D'Artagnan's technical review.*
*v0.2 → v0.3 revised after Phase 0-A empirically falsified v0.2 §8.2.*
*Nothing in this document is committed or public.*
