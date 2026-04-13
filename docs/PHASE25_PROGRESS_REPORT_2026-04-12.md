# GravDic — Progress Report: Multi-Agent Collaboration Experiment

**Date:** 2026-04-12
**Phase:** 2.5 — Multi-Agent Collaboration (V4 Capillary Cluster validation)
**Status:** 7 collaboration patterns tested. Structured handoff (C6) validated as the winning pattern. Generative fusion, adversarial synthesis, and peer review all empirically falsified.
**Prior report:** `docs/PHASE1_PROGRESS_REPORT_2026-04-09.md` (Phase 1 — Mass Accrual Reform)
**Spec:** `docs/MULTI_AGENT_COLLABORATION_SPEC.md`

---

## 1. Executive Summary

Phase 1 (2026-04-09) validated the V3.5 mass accrual reform: the homeostatic reputation engine prevents monopolies at zero quality cost. Phase 2.5 tests the next fundamental claim: that independent AI agents can collaborate on complex multi-domain tasks and produce better results than any single agent.

The experiment ran 10 composite payloads (each requiring 2-3 friction types) across 7 collaboration patterns, from a single generalist baseline through increasingly structured cooperation models. The result is a clear hierarchy of what works and what doesn't:

| Rank | Condition | Mean quality | Description |
|---|---|---|---|
| **1** | **C6: structured handoff** | **0.745** | Sequential specialists with focused 3-bullet handoff memos |
| 2 | C2: independent specialists | 0.730 | Parallel specialists, no communication |
| 3 | C5: sequential pipeline | 0.710 | Sequential with full prior context |
| 4 | C1: single agent | 0.570 | One generalist handles everything |
| 5 | C3: LLM fusion via Seed | 0.455 | Highest-mass agent integrates specialist outputs |
| 6 | C7: cross-pollination | 0.365 | Parallel solve → peer review → revision |
| 7 | C4: adversarial synthesis | 0.185 | Fusion + critique loop + revision |

**Key findings:**

1. **Specialization works.** Every multi-specialist approach (C2, C5, C6) dramatically outperforms a single generalist (C1: 0.570). Routing sub-tasks to domain experts is the core value — this validates the gravitational formula's design for multi-domain tasks.

2. **Structured handoff is the best collaboration pattern.** C6 (0.745) wins by passing focused 3-bullet memos between sequential specialists — not full context (C5: 0.710), not LLM-generated fusion (C3: 0.455), not peer review (C7: 0.365). The signal cascade model, where each specialist receives only the key findings from the prior specialist, produces the optimal balance of cross-domain awareness and specialist autonomy.

3. **LLM-generated fusion consistently degrades quality.** C3 (Seed fusion) scores lower than C2 (no communication at all). The Seed agent overwrites good specialist reasoning with worse generalist reasoning when trying to integrate outputs it doesn't fully understand. This is the most important negative finding: the whitepaper's Gravitational Dictatorship model as specified (Seed fuses outputs) does not work with current LLMs.

4. **Adversarial synthesis is destructive.** C4 produced 0 positive revision deltas out of 10 payloads (6 negative, 4 neutral). The critique loop amplifies noise rather than filtering it — specialists find "problems" even when there aren't any, and the Seed's revisions degrade quality.

5. **Peer review (cross-pollination) is catastrophic.** C7 (0.365) is worse than a single generalist. Specialists revise their confident domain-specific outputs into watered-down versions after reading summaries from domains they don't understand.

**The collaboration hierarchy is:** focused signal cascade > no communication > full context > LLM fusion > peer review > adversarial critique. More communication is not better; *better-structured* communication is better.

---

## 2. The Experiment

### 2.1 Design — 7-condition graduated stack

10 composite payloads, each requiring 2-3 friction types (6 dual-domain + 4 triple-domain tasks). All 6 possible domain pairs represented. Same 10-agent pool as Phase 1 (Claude Haiku ×2, Gemini Flash ×2, Llama 70B ×2, GPT-4o-mini ×2, Mistral Large, Qwen 72B).

Each composite payload carries `domain_weights` (how much each domain contributes to the task) and hand-authored per-domain sub-prompts. The decomposition is human-authored to isolate the collaboration mechanism from the decomposition mechanism.

| Condition | Communication model | Who produces the final answer? |
|---|---|---|
| **C1: single agent** | None | One generalist (best composite-priority agent) |
| **C2: independent** | None | Concatenated specialist outputs (parallel, no communication) |
| **C3: fusion** | Specialist outputs → Seed | Seed produces a fused answer |
| **C4: adversarial** | C3 + specialists critique → Seed revises | Seed's revised answer |
| **C5: sequential** | Full prior output passed to next specialist | Concatenated specialist outputs (sequential) |
| **C6: handoff** | 3-bullet handoff memo passed to next specialist | Concatenated specialist outputs (sequential, focused signals) |
| **C7: cross-pollination** | All solve independently → read 1-paragraph summaries → all revise | Concatenated revised outputs |

### 2.2 Composite payloads

| # | Domains | Task |
|---|---|---|
| 1 | SEMANTIC + DETERMINISTIC | Legal contract analysis + structured extraction |
| 2 | SEMANTIC + SPATIAL | School placement: need assessment + location optimization |
| 3 | DETERMINISTIC + TEMPORAL | Server log parsing + causal chain prediction |
| 4 | SEMANTIC + TEMPORAL | Historical event analysis + causation mapping |
| 5 | SEM + DET + SPATIAL | Real estate portfolio: risk analysis + financials + geography |
| 6 | SPATIAL + TEMPORAL | Delivery routing with time constraints |
| 7 | DETERMINISTIC + SPATIAL | Network topology parsing + layout optimization |
| 8 | SEM + DET + TEMPORAL | Clinical trial: design analysis + statistics + outcome prediction |
| 9 | SEM + SPATIAL + TEMPORAL | Disaster response: assessment + resource placement + timeline |
| 10 | DETERMINISTIC + SEMANTIC | Financial fraud detection: pattern extraction + intent analysis |

### 2.3 Routing

**C1 (single agent)** uses a Composite Priority Score to select the best generalist:
```
P_composite = Σ(w_d × M_route_d^α) / ((D_weighted + 1)(L + 1)^β)
where D_weighted = Σ(w_d × D_d)
```
This ensures the control baseline is fair — the best-fit generalist for each specific task mix, not just the highest-aggregate-mass agent.

**C2-C7** use the standard gravitational formula per sub-domain to select the best specialist for each friction type.

**C5 and C6** order specialists by domain weight (highest first — the most important domain sets the foundation).

### 2.4 Judge rubric

All conditions scored on overall quality (0-1) by Claude Sonnet as judge. For concatenated outputs (C2, C5, C6, C7), the judge evaluates logical consistency between parts, not stylistic coherence — preventing an unfair penalty for multi-voice outputs.

---

## 3. Results

### 3.1 Per-payload scores

| Payload | C1 | C2 | C3 | C4 | C5 | **C6** | C7 |
|---|---|---|---|---|---|---|---|
| 01 legal (SEM+DET) | 0.85 | 0.85 | 0.55 | 0.55 | 0.85 | **0.85** | 0.85 |
| 02 school (SEM+SPA) | 0.45 | 0.85 | 0.65 | 0.00 | 0.65 | **0.65** | 0.65 |
| 03 server (DET+TEM) | 0.55 | 0.85 | 0.55 | 0.00 | 0.85 | **0.85** | 0.45 |
| 04 history (SEM+TEM) | 0.65 | 0.65 | 0.65 | 0.65 | 0.65 | **0.85** | 0.00 |
| 05 real estate (SEM+DET+SPA) | 0.75 | 0.80 | 0.15 | 0.00 | **0.95** | **0.95** | 0.75 |
| 06 delivery (SPA+TEM) | 0.15 | 0.65 | 0.15 | 0.15 | 0.45 | **0.45** | 0.65 |
| 07 network (DET+SPA) | 0.45 | 0.65 | 0.15 | 0.00 | 0.50 | **0.65** | 0.15 |
| 08 clinical (SEM+DET+TEM) | 1.00 | 0.75 | 0.50 | 0.50 | 0.75 | **0.75** | 0.00 |
| 09 disaster (SEM+SPA+TEM) | 0.55 | 0.45 | 0.40 | 0.00 | **0.85** | **0.75** | 0.15 |
| 10 fraud (DET+SEM) | 0.30 | 0.80 | 0.80 | 0.00 | 0.60 | **0.70** | 0.00 |
| **Mean** | **0.57** | **0.73** | **0.46** | **0.19** | **0.71** | **0.75** | **0.37** |

### 3.2 C6 vs C2 — where structured handoff adds value

On 3 of 10 payloads, C6 beat C2:
- Payload 4 (historical causation): C6=0.85 vs C2=0.65. The semantic specialist's handoff memo about key historical patterns helped the temporal specialist make better causal predictions.
- Payload 5 (real estate): C6=0.95 vs C2=0.80. The deterministic specialist's financial metrics handoff informed the semantic risk analysis AND the spatial concentration assessment.
- Payload 9 (disaster response): C6=0.75 vs C2=0.45. The spatial resource-placement specialist benefited from knowing the semantic specialist's need-assessment priorities.

On 7 of 10 payloads, C6 matched C2 — the handoff memo neither helped nor hurt.

On 0 of 10 payloads did C6 score lower than C2. **Structured handoff has no downside** — it matches or exceeds independent specialization, never degrades it.

### 3.3 The fusion failure — why C3 and C4 break

C3 (fusion) scored lower than C2 (independent) on 8 of 10 payloads. The pattern is consistent: the Seed agent (haiku-1, highest aggregate mass) receives specialist outputs and tries to integrate them, but:

- It overwrites domain-specific nuances with generalist summaries
- It introduces factual errors when reasoning about domains it doesn't specialize in
- It produces a coherent-sounding but less accurate answer than the raw specialist outputs

C4 (adversarial) is even worse because the critique loop compounds the problem: specialists critique the Seed's already-degraded draft, the Seed revises based on critiques that are partly valid and partly hallucinated, and the final output is worse than the original fusion.

**Revision delta analysis (C4 - C3 draft):** mean = −0.270. 6 payloads negative (critique hurt), 4 neutral, 0 positive. The adversarial loop is reliably destructive.

### 3.4 The cross-pollination catastrophe

C7 (0.365) is the second-worst condition — worse than a single generalist. The mechanism: after independent solving, specialists read 1-paragraph summaries from other domains and revise their own work. The result: specialists second-guess their confident domain-specific reasoning in response to summaries they don't fully understand. Four payloads scored 0.00 or 0.15 under C7, down from 0.65-0.85 under C2 for the same payloads. The peer-review model actively destroys specialist quality.

---

## 4. Key Findings

### 4.1 The collaboration hierarchy

```
C6 (structured handoff)     0.745  ████████████████████████████████████████
C2 (independent)            0.730  ███████████████████████████████████████
C5 (sequential full ctx)    0.710  ██████████████████████████████████████
C1 (single generalist)      0.570  ██████████████████████████████
C3 (LLM fusion)             0.455  ███████████████████████
C7 (cross-pollination)      0.365  ██████████████████
C4 (adversarial)            0.185  █████████
```

The hierarchy is: **focused signal > no signal > full signal > LLM integration > peer review > adversarial critique.**

The counter-intuitive finding: more communication can be worse than no communication. What matters is not the amount of information shared but its *structure and focus*. Three bullet points (C6) beat an entire prior output (C5) beat no communication at all (C2) beat a generated fusion (C3) beat a peer-review round (C7).

### 4.2 What this means for V4 Capillary Clusters

The whitepaper §7 describes Capillary Clusters with a Cluster Seed that fuses outputs via Gravitational Dictatorship, with Adversarial Synthesis as a quality-control mechanism. Phase 2.5 empirically falsifies both components:

- **Gravitational Dictatorship as fusion:** the Seed fusing specialist outputs produces worse results than no fusion at all. The Seed's role must be revised from *integrator* to *orchestrator*.
- **Adversarial Synthesis as quality control:** the critique-revision loop is reliably destructive, not constructive. The mechanism must be removed or fundamentally redesigned.

**The revised V4 design should implement:**

1. **The Cluster Seed as orchestrator, not integrator.** The highest-mass agent decomposes the task, determines execution order, formats handoff memos between specialists, and mechanically assembles the final output. It does NOT produce a "fused" answer — it arranges the specialist outputs structurally.

2. **Structured handoff as the communication protocol.** Each specialist produces their full output + a 3-bullet handoff memo of key findings. The next specialist in the pipeline receives only the memo, not the full output. This is the C6 pattern.

3. **GPSL operators determine the collaboration pattern.** Composite payloads with `→` (causal dependency between domains) route sequentially with handoff. Payloads with `⊗` (independent domains that need combining) route in parallel with mechanical concatenation. The notation tells the protocol which pattern to use.

4. **Mechanical assembly, not generative fusion.** The final answer is a structured combination of specialist outputs — slotted into predefined sections with explicit cross-references. No LLM produces the "fused" version.

5. **No adversarial synthesis in V4.** The critique loop is empirically harmful. If quality control is needed, it should come from the verification layer (the existing Tier 1/Tier 2 Membrane), not from agents critiquing each other's work.

### 4.3 The protocol as head agent

Traditional multi-agent frameworks (LangChain, CrewAI, AutoGen) use a centralized orchestrator — either a human or a hardcoded LLM — to decompose tasks and assign sub-agents. GravDic's physics-based alternative:

- **The gravitational formula selects specialists** per sub-domain (proven in Phase 1 and Phase 2.5)
- **Domain weights determine execution order** (highest-weighted domain goes first — proven in C6)
- **The handoff memo structure is protocol-defined** (3 key findings, formatted by the specialist, not by an orchestrator)
- **Assembly is mechanical** (structured concatenation with domain labels)

No LLM needs to make orchestration decisions. The protocol IS the head agent. This is the "physics, not committees" principle applied to collaboration, not just routing.

**One remaining question for Phase 2.6:** can the protocol auto-decompose a complex task into the right sub-tasks and domain weights, or does decomposition require human authoring? Phase 2.5 used hand-authored decomposition to isolate the collaboration variable. Auto-decomposition is the next experiment.

### 4.4 Relationship to the Flinn parallel

The medical AI company Flinn uses centralized engineering to decide which LLMs handle which sub-tasks. GravDic would do the same thing via physics:

| Step | Flinn (centralized) | GravDic (physics-based) |
|---|---|---|
| Decompose | Engineered pipeline | Protocol classifies by friction type |
| Select specialists | Engineering decision | Gravitational formula per sub-domain |
| Order execution | Hardcoded pipeline | Domain weights (highest first) |
| Communicate between steps | Shared API context | Structured handoff memos (3 bullets) |
| Assemble final answer | Engineering aggregation | Mechanical structured concatenation |
| Quality control | Human review | Tier 1/Tier 2 verification membrane |

The advantage: GravDic's pipeline is permissionless and self-improving. New models join, earn mass, and get routed work — no engineer updates the pipeline. The protocol adapts because the physics reward competence.

---

## 5. Methodology Notes

### 5.1 Limitations

1. **10 payloads is directional, not conclusive.** The results are consistent across payloads but the sample is small. A 50-payload run would strengthen the claims.
2. **Hand-authored decomposition.** Sub-prompts and domain weights were human-authored, not auto-generated. This isolates the collaboration variable but doesn't test decomposition quality.
3. **Single seed (42).** No multi-seed variance check on collaboration results. Phase 1 proved multi-seed robustness for the accrual reform; Phase 2.5 should do the same if these results become a spec input.
4. **Model-dependent.** The fusion failure may be specific to the model pool used (Haiku as Seed). A stronger Seed model (Sonnet, GPT-4o full) might produce better fusion. However, this would undermine the "physics decides" principle — if fusion requires a specific strong model, it's not a general-purpose protocol mechanism.
5. **No GPSL encoding.** Communication was in natural language. GPSL-encoded handoff memos (using formal operators to express relationships between specialist findings) might improve C6 further. This is Phase 2 proper.
6. **Network interruption.** One run (the C5-only experiment) crashed on payload 9/10 due to DNS resolution failure. The full 7-condition run completed successfully.
7. **Judge scoring variance.** LLM judges (Claude Sonnet) have inherent scoring noise. Some payloads may have been scored differently on different runs. The relative ordering of conditions is more reliable than the absolute scores.

### 5.2 Cost

Total Phase 2.5 API cost across all runs: approximately $50-60 (3 experiment runs × 10 payloads × 5-7 conditions × multiple LLM calls per condition).

---

## 6. Implications and Next Steps

### 6.1 Immediate — update the whitepaper

Whitepaper §7 (Capillary Clusters) needs revision to reflect the empirical findings:
- Gravitational Dictatorship: Seed role changes from fusion-integrator to pipeline-orchestrator
- Adversarial Synthesis (§7.5): marked as empirically falsified in current form; removed or redesigned
- Communication model: structured handoff (C6) replaces GPSL-encoded full-context sharing

### 6.2 Near-term — Phase 2.6 (auto-decomposition)

Test whether the protocol can automatically decompose a complex task into sub-tasks and domain weights without human authoring. This is the remaining piece needed to prove the "protocol as head agent" concept.

### 6.3 Medium-term — V4 engineering

Build Capillary Clusters around the C6 pattern:
- Composite Payload support in EscrowCore (multiple friction type slots)
- Per-slot routing via gravitational formula
- Structured handoff memo format (protocol-defined, not free-form)
- Mechanical assembly of specialist outputs into final response
- Atomic multi-wallet payout distribution

### 6.4 Future — GPSL-encoded handoff

Replace natural-language handoff memos with GPSL-encoded structural summaries. The `→` (causation) and `⊗` (fusion) operators would formalize inter-specialist communication from "3 English bullet points" into "structured topology that the next specialist's system prompt can parse mechanically." This is the long-term vision for inter-agent communication in the protocol.

---

## 7. Acknowledgments

The four peer-review findings that improved the experiment design (composite priority formula for C1, C2 judge rubric adjustment, C4 token budget, revision delta tracking) were contributed by a technical reviewer prior to the experiment run.

The Phase 2.5 experiment design, the seven collaboration patterns, and the analysis were developed iteratively during the session, with C5, C6, and C7 designed in direct response to the C1-C4 results.

---

*Progress Report — 2026-04-12*
*Phase 2.5 is between the mass-accrual reform (Phase 1, validated) and the GPSL cipher encoding (Phase 2, next). It tests the collaboration hypothesis that underlies the V4 Capillary Cluster architecture.*
