# Multi-Agent Collaboration — Phase 2.5 Experiment Spec

**Date:** 2026-04-12
**Status:** Design spec for next engineering session. Tests the core hypothesis that multi-agent collaboration produces better results than single-agent routing on complex tasks.
**Depends on:** V3.5 simulation framework (done), OpenRouter API key (need fresh one)
**Whitepaper reference:** §7 (Capillary Clusters), §7.2 (Lifecycle), §7.5 (Adversarial Synthesis)

---

## 0. Why this matters now

GravDic's value proposition is not just "better matching" — it's that independent AI agents can self-organize into temporary teams, communicate structured information, fuse their outputs, and produce results no single agent could. If agents can't collaborate effectively, GravDic is a routing engine. If they can, it's an organism.

The whitepaper describes the full Capillary Cluster architecture (six phases, Gravitational Dictatorship, Adversarial Synthesis, GPSL-encoded communication, collaborative memory). That's the V4 target. This experiment tests the core hypothesis underneath all of it: **does routing sub-tasks to specialized models and fusing their outputs produce better results than giving the whole task to one generalist?**

If yes: build the full Cluster architecture with confidence.
If no: the protocol's collaboration layer needs fundamental rethinking before V4.

---

## 1. The experiment

### 1.1 Composite payloads

Create 10 tasks that genuinely require two or more friction types to solve well. These are tasks where a single-specialist agent would get part of the answer right and part wrong, because no one model excels at both the semantic reasoning AND the deterministic extraction AND the spatial/temporal reasoning the task requires.

**Example composite payloads:**

**Task A — Semantic + Deterministic:**
> "Read this legal contract clause: [clause text]. (1) Identify the three key obligations and assess whether any are ambiguous (semantic analysis). (2) Extract the exact dollar amounts, dates, and party names into a structured JSON object (deterministic extraction). Return both the analysis and the JSON."

**Task B — Semantic + Spatial:**
> "A city is planning three new schools. Here are the demographic data for 8 neighborhoods: [data]. (1) Analyze which neighborhoods have the greatest educational need based on population density, income, and existing school proximity (semantic reasoning). (2) Propose optimal coordinates for the three schools to minimize average travel distance for students (spatial optimization). Show both the reasoning and the placement."

**Task C — Deterministic + Temporal:**
> "Here is a server log with 50 entries: [log data]. (1) Parse each entry and extract timestamp, severity, and error code into a structured table (deterministic extraction). (2) Identify the causal chain: which errors triggered which subsequent errors, and predict what will fail next if the pattern continues (temporal reasoning)."

**Task D — Semantic + Deterministic + Spatial (triple composite):**
> "A real estate investment firm is evaluating 5 properties: [property descriptions with financials]. (1) Analyze the qualitative risks and opportunities for each property (semantic). (2) Extract and compute the cap rate, cash-on-cash return, and debt service coverage ratio for each (deterministic). (3) Map the properties geographically and assess portfolio concentration risk (spatial). Produce a single investment recommendation with supporting analysis."

### 1.2 Three experimental conditions

For each composite payload, run three conditions:

**Condition 1 — Single agent (control).**
Route the entire composite payload to the single highest-priority agent via the gravitational formula (standard V3.5 routing). The agent gets the whole task and produces one answer.

**Condition 2 — Independent specialists (no communication).**
Decompose the payload into sub-tasks by friction type. Route each sub-task to the best-fit specialist via the gravitational formula. Each specialist solves independently. Their outputs are concatenated (not fused) and submitted as the composite answer. This tests whether specialization alone helps, even without communication.

**Condition 3 — Collaborative specialists (the Cluster).**
Same decomposition and routing as Condition 2, but after specialists solve independently, their outputs are fed to the highest-mass agent (the Seed) with explicit fusion instructions. The Seed sees all specialist outputs + the original composite task and produces a single fused answer. This tests whether structured fusion adds value on top of specialization.

**Condition 4 (stretch goal) — Adversarial Synthesis.**
Same as Condition 3, but after the Seed produces a draft fusion, each specialist reviews the draft and submits a critique: "here's what's wrong with how you used my output." The Seed then revises. This tests the full adversarial dialectic from the whitepaper §7.5.

### 1.3 What we measure

For each composite payload × each condition, the LLM judge scores the complete answer on:

1. **Overall quality** (0-1): Does the answer correctly address all parts of the composite task?
2. **Per-domain quality** (0-1 per friction type): How well did the answer handle each sub-domain? A single agent might nail the semantic part but botch the extraction.
3. **Coherence** (0-1): Is the final answer a unified, coherent response? Or does it feel like stapled-together parts? (Relevant for Conditions 2-4.)
4. **Completeness** (0-1): Did the answer address every sub-task, or did it skip/shortcut some?

The key comparison: does Condition 3 (collaborative fusion) beat Condition 1 (single agent) on overall quality? By how much? Does Condition 4 (adversarial synthesis) beat Condition 3? Does Condition 2 (independent, no fusion) beat Condition 1?

---

## 2. Engineering plan

### 2.1 New code (estimated ~3 days total)

**Day 1 — Composite payloads + decomposition:**

`simulation/payloads/composite_templates.py` (new, ~200 lines)
- 10 composite payload templates, each tagged with 2-3 friction types
- `CompositePayload` dataclass extending `SimPayload` with `sub_domains: list[FrictionType]` and `sub_prompts: dict[FrictionType, str]` (the decomposed sub-task per domain)
- Each template includes: the full composite prompt, the per-domain decomposed prompts, and a composite scoring rubric for the judge
- The decomposition is authored by hand (not automated) — we control what each specialist sees

`simulation/payloads/generator.py` (modify)
- Add `generate_composite_batch(count)` method that samples from composite templates

**Day 2 — Multi-agent solve pipeline:**

`simulation/experiment_composite.py` (new, ~300 lines)
- `CompositeExperimentRunner` that implements all four conditions:

```python
async def run_condition_1_single(payload, agents):
    """Route entire composite to best single agent."""
    agent = router.select_agent(payload, agents)  # existing formula
    result = await agent.solve(payload, client)
    return result

async def run_condition_2_independent(payload, agents):
    """Route sub-tasks to specialists, concatenate outputs."""
    outputs = {}
    for domain, sub_prompt in payload.sub_prompts.items():
        sub_payload = make_sub_payload(payload, domain, sub_prompt)
        agent = router.select_agent(sub_payload, agents)
        result = await agent.solve(sub_payload, client)
        outputs[domain.name] = result.answer
    # Concatenate without fusion
    return concatenate(outputs)

async def run_condition_3_fusion(payload, agents):
    """Route sub-tasks to specialists, then fuse via Seed."""
    outputs = await run_condition_2_independent(payload, agents)
    seed = select_seed(agents)  # highest routing mass
    fusion_prompt = build_fusion_prompt(payload, outputs)
    fused = await seed.solve(fusion_prompt, client)
    return fused

async def run_condition_4_adversarial(payload, agents):
    """Condition 3 + critique round + revision."""
    draft = await run_condition_3_fusion(payload, agents)
    critiques = {}
    for domain, agent in specialist_assignments.items():
        critique_prompt = build_critique_prompt(draft, domain, agent_output)
        critique = await agent.solve(critique_prompt, client)
        critiques[domain.name] = critique.answer
    # Seed revises based on critiques
    revision_prompt = build_revision_prompt(draft, critiques)
    final = await seed.solve(revision_prompt, client)
    return final
```

**Key design decision — the fusion prompt.** This is the most important prompt in the system. It must:
- Present the original composite task
- Present each specialist's output, labeled by domain
- Instruct the Seed to produce a unified answer that integrates all specialist outputs
- NOT instruct the Seed to simply concatenate — it must reason about how the outputs relate

Draft fusion prompt template:
```
You are the Fusion Agent for a multi-specialist team. Your team has produced the following specialist outputs for a composite task.

ORIGINAL TASK:
{composite_prompt}

SPECIALIST OUTPUTS:
[SEMANTIC SPECIALIST]: {semantic_output}
[DETERMINISTIC SPECIALIST]: {deterministic_output}
[SPATIAL SPECIALIST]: {spatial_output}

Your job: produce a single, coherent answer that integrates all specialist outputs. Do not simply concatenate them. Reason about how they relate — does the semantic analysis inform the spatial placement? Does the deterministic extraction support or contradict the semantic conclusions? Produce one unified answer that is better than any individual specialist's output.
```

Draft critique prompt template:
```
You are the {domain} specialist who produced the following output:

YOUR OUTPUT:
{specialist_output}

The Fusion Agent produced this draft answer using your output and other specialists' outputs:

DRAFT FUSION:
{fusion_draft}

Review how the Fusion Agent used your {domain} output. Identify any errors, misinterpretations, or missed connections. If the draft is correct, say "No critique." If you find a problem, describe it specifically and propose a fix.
```

**Day 3 — Scoring + comparison:**

`simulation/analysis/composite_compare.py` (new, ~150 lines)
- Load results from all four conditions
- Per-payload comparison: C1 vs C2 vs C3 vs C4 on all four metrics
- Aggregate: does collaboration beat single-agent? By how much? Does adversarial synthesis add further value?
- Statistical summary across the 10 composite payloads

Config: `configs/composite_test.yaml` (new)
- Same agent pool as Phase 1
- 10 composite payloads, 4 conditions each = 40 "runs" but actually ~80-120 LLM calls (each condition involves 1-4 agent calls per payload)
- Estimated cost: ~$10-15

### 2.2 What this doesn't build (deferred to V4)

- **Self-assembly.** In this experiment, we manually decompose payloads and assign specialists. In the full Cluster architecture, agents would self-select based on the gravitational formula applied per-slot. Deferred because self-assembly requires Gossipsub signaling infrastructure.
- **GPSL communication.** Specialists communicate via natural language prompts in this experiment, not GPSL ciphers. Deferred to Phase 2 proper (GPSL cipher encoding).
- **On-chain settlement.** No smart contract interaction. This is a pure simulation experiment. The escrow and payout logic for Composite Payloads is a V4 contract extension.
- **Collaborative memory.** No Plasticity Matrix update. The experiment doesn't track whether successful collaborations produce faster re-formation.
- **The annealing window.** The critique round in Condition 4 is not time-bounded. In the full architecture, the 20% annealing window would enforce a deadline.

### 2.3 Success criteria

**Must-have (for the collaboration hypothesis to hold):**
- Condition 3 (fusion) beats Condition 1 (single agent) on overall quality for ≥ 7 of 10 composite payloads
- The improvement is ≥ 0.1 on the 0-1 quality scale (not just noise)

**Strong signal:**
- Condition 3 beats Condition 2 (independent specialists without fusion) — proving that fusion adds value beyond specialization alone
- Condition 4 (adversarial) beats Condition 3 — proving the critique loop improves the output

**Failure modes to watch for:**
- Fusion produces *worse* results than single-agent because the Seed introduces errors when trying to integrate specialist outputs ("fusion confusion")
- The critique round in Condition 4 produces defensive revisions that make the answer worse ("critique degradation")
- Independent specialists (Condition 2) already beat single-agent, making fusion unnecessary ("specialization is sufficient")

---

## 3. What this proves for the protocol

If the experiment succeeds:

1. **Capillary Clusters are worth building.** The V4 investment (composite payloads, cluster formation, GPSL communication, on-chain settlement) is justified by empirical evidence that multi-agent fusion produces superior results.

2. **Gravitational Dictatorship works.** The highest-mass agent acting as Fusion Agent produces coherent, integrated outputs — the "data dictator with no financial power" model from the whitepaper.

3. **Adversarial Synthesis adds value.** The critique-revision loop produces measurably better outputs than unchallenged fusion — justifying the annealing window and Red Team incentive design.

4. **The protocol can handle Flinn-style medical reasoning.** If independent AI models with different strengths can collaborate via structured fusion to solve complex multi-domain problems, GravDic can serve as the infrastructure for any domain where task complexity exceeds single-model capability — including medical AI, legal analysis, financial compliance, and scientific research.

If the experiment fails:

1. **Redesign the communication layer** before building V4 contracts. If natural-language fusion doesn't work, GPSL-encoded structured communication becomes even more critical (not less) — agents need a formal protocol to integrate outputs, not just context windows.

2. **Consider simpler collaboration models.** Maybe the right architecture isn't "specialists fuse via a Seed" but "the best agent solves with specialist outputs as context" (a RAG-like approach rather than a team approach). The experiment's Condition 2 vs Condition 3 comparison will reveal this.

3. **Phase 2 (GPSL) becomes even more urgent.** If the bottleneck is communication quality, then the notation layer — structured, formal, topology-preserving — is the fix, and it needs to come before the collaboration layer, not after.

---

## 4. Relationship to the Flinn parallel

What Flinn does centrally (pick which models handle which sub-tasks, orchestrate the pipeline, fuse results), GravDic would do via physics:

| Aspect | Flinn (centralized) | GravDic (physics-based) |
|---|---|---|
| **Model selection** | Engineers design which model handles which task type | Gravitational formula routes by M, D, L |
| **Decomposition** | Engineered pipeline splits tasks | Composite payload emits per-domain signals |
| **Communication** | Shared context / API calls between models | GPSL ciphers encoding relational topology |
| **Fusion** | Engineered aggregation layer | Highest-mass Seed integrates via Gravitational Dictatorship |
| **Quality control** | Internal testing / human review | Adversarial Synthesis — team members challenge the Seed |
| **Incentives** | Salary / corporate structure | USDC bounties, mass accrual, payout-share capture |

The key advantage of the physics-based approach: it's **permissionless and self-improving**. Anyone can add a new model to the GravDic network. If that model is better at a specific task type, it earns mass and naturally gets routed more of that work. No engineer needs to update a pipeline. The system adapts because the physics reward competence.

---

## 5. Implementation order for next session

1. Write 10 composite payload templates (~2 hours)
2. Build `CompositePayload` dataclass + decomposition logic (~1 hour)
3. Build `CompositeExperimentRunner` with all 4 conditions (~3 hours)
4. Write the fusion, critique, and revision prompt templates (~1 hour)
5. Write `composite_compare.py` analysis script (~1 hour)
6. Create fresh OpenRouter API key
7. Run the experiment (~30 minutes, ~$10-15)
8. Analyze results and write up findings

**Total: ~1 day of focused engineering + ~30 minutes of simulation runtime.**

---

*Design spec — 2026-04-12*
*This experiment is Phase 2.5: between the accrual reform (Phase 1, done) and the GPSL cipher encoding (Phase 2, next). It tests the collaboration hypothesis that underlies the entire V4 Capillary Cluster architecture.*
