# Phase 2 — GPSL Cipher Encoding & Operator-Level Continuous Distance

**Date:** 2026-04-13
**Status:** Workplan. Ready to build when next engineering session starts.
**Depends on:** V3.5 simulation framework (done), Phase 1 reform stack (done, validated), Phase 2.5 collaboration findings (done), fresh OpenRouter API key
**Whitepaper reference:** §3 Layer 3 of GPSL Integration Proposal, §5.2 Operator-level fluency (MASS_ACCRUAL_REFORM_v0.1 §3.1)

---

## 0. What this proves and why it matters now

Phase 1 collapsed intra-domain mass monopolies from 5000:1 to 15:1. At 15:1 ratios, continuous structural distance CAN mathematically flip routing decisions — but only if the distance is computed from something more granular than categorical domain labels. Phase 2 tests whether **operator-level fluency** (tracking which GPSL operators each agent has demonstrated competence with) produces meaningful routing differentiation that categorical D cannot.

This is the Layer 3 test that Phase 0-A proved was impossible under V3.4 mass distribution and that Phase 1 made viable.

---

## 1. The three deliverables

### 1.1 GPSL cipher-encoded payloads

Translate 20 Spatial-domain payloads into GPSL v2.2 cipher format. Each payload becomes a cipher with:
- A friction-type header
- An operator legend
- The task expressed in GPSL notation
- A resonance threshold for verification

**Why Spatial first:** it's GPSL's native terrain. The notation was designed for topological reasoning. If GPSL encoding improves routing quality anywhere, it's here. If it doesn't work for Spatial, it won't work for the others.

**What the ciphers look like (from the integration proposal §3 Layer 1):**
```
HEADER: Spatial / Constraint Placement
LEGEND: ⥀ = directional scan
PAYLOAD:
  [Solver⥀{candidate_sites}] :: [Constraint] → {Placement}
  ⟨placement|constraints⟩ > 0.85
```

Each cipher must use a mix of operators so agents build differentiated fluency profiles. Some ciphers should use only base operators (→, ⊗, ::). Others should use advanced operators (⥀, ⦸, ⤳). This creates the operator diversity that makes the continuous-D computation meaningful.

### 1.2 Scaffolded agent system prompts

Every LLM in the simulation pool gets a GPSL v2.2 system prompt that:
- Defines the base operators and their type signatures
- Provides 3-5 few-shot examples of well-formed GPSL responses
- Explains the flag-not-slash behavior for V-class structures
- Instructs the agent to output solutions in GPSL notation

**The scaffolding is critical.** Phase 1 of the integration proposal explicitly warned: without scaffolding, the LLM agents will fail on type constraints and undeclared operators, and we'll measure "current LLMs can't speak GPSL yet" rather than "GPSL improves protocol outcomes." The scaffolding ensures we test the right hypothesis.

### 1.3 Operator-level continuous distance

Replace the categorical D ∈ {0.0, 0.5, 2.0} with a continuous D computed from each agent's empirical fluency in the specific GPSL operators a payload requires:

```
For each agent A, maintain per-operator fluency:
  fluency[A][op] = (count_solved, quality_sum)

For each payload P with required operator set Ops(P):
  D_continuous(A, P) = (1/|Ops(P)|) × Σ_{op ∈ Ops(P)} max(0, 3 - fluency_score(profile[op]))
  where fluency_score(count, quality_sum) = (quality_sum/count) × log(1+count)/log(11)
                                            capped at 1.0, then × 3 to map to [0, 3]
```

An agent fluent in every operator the payload requires has D ≈ 0. An agent fluent in none has D ≈ 3. The key improvement over domain-level D: no single agent can monopolize all operators in a domain, because the operator vocabulary is large and growing.

---

## 2. The experiment

### 2.1 Design — 2×2 factorial

Same structure as the original Phase 1 spec (MASS_ACCRUAL_REFORM_v0.1 §8.1), now executable because Phase 1 collapsed the mass ratios:

|  | Categorical D | Continuous D (operator-level) |
|---|---|---|
| **V3.4 accrual (linear)** | Cell A: control baseline | Cell B: continuous D under old mass regime |
| **V3.5 accrual (sublinear + rebase)** | Cell C: what Phase 1 tested | **Cell D: the full V3.5+GPSL stack** |

Cell D is the target: sublinear accrual + seasonal rebase + operator-level continuous distance. This is the complete V3.5 routing system as specified.

### 2.2 Setup

- 20 GPSL-encoded Spatial payloads
- 10 agents with GPSL scaffolding (same pool as Phase 1)
- 50 rounds (enough for operator fluency profiles to develop)
- Gravitational routing only
- Seed 42 initially, multi-seed if results warrant

### 2.3 What we measure

1. **Routing differentiation:** How often does the continuous-D winner differ from the categorical-D winner? (This is what Phase 0-A measured at 0% under old mass distribution — the whole reason for the reform.)
2. **Quality improvement:** Does the continuous-D winner produce higher-quality solutions? (The routing formula should send work to agents who are actually fluent in the required operators, not just subscribed to the right domain.)
3. **Fluency development:** Do agents develop differentiated operator-level profiles over 50 rounds? (Some agents should become fluent in ⥀, others in ⦸, etc.)
4. **Monopoly prevention:** Under continuous D + reformed accrual, does any single agent still dominate an entire domain? Or do different operators within a domain get routed to different specialists?

### 2.4 Success criteria

**Must-have:**
- Cell D (full stack) produces ≥10% routing divergence from Cell C (categorical D) — meaning continuous D actually matters now that mass ratios are 15:1 instead of 5000:1
- Quality in Cell D is ≥ quality in Cell C (continuous D doesn't hurt)

**Strong signal:**
- Agents develop measurably different operator-level fluency profiles (not all agents fluent in the same operators)
- Cell D produces higher quality than Cell C on payloads requiring advanced operators (⥀, ⦸, ⤳)

**Would validate the full GPSL integration hypothesis:**
- Cell B (continuous D + old accrual) shows negligible divergence (reproducing Phase 0-A under GPSL encoding — confirming that the reform is the prerequisite, not GPSL alone)
- Cell D shows significant divergence AND quality improvement (confirming that reform + GPSL together produce the routing differentiation neither can achieve alone)

---

## 3. Engineering plan

### Day 1 — GPSL cipher payloads + agent scaffolding (~4 hours)

**3.1 Create `simulation/payloads/gpsl_spatial_templates.py`** (~300 lines)

20 Spatial payloads in GPSL cipher format. Each includes:
- `gpsl_cipher: str` — the full cipher (header, legend, payload notation, resonance threshold)
- `operators_required: list[str]` — which GPSL operators this cipher uses
- `plain_prompt: str` — the same task in natural language (for comparison and for agents that can't parse GPSL)
- `expected_answer: str | None` — for Tier 1 tasks
- `scoring_rubric: str | None` — for Tier 2 tasks

Operator distribution across the 20 payloads:
- 6 payloads using only base operators (→, ⊗, ::, =)
- 6 payloads using base + one advanced operator (⥀ or ⦸ or ⤳)
- 4 payloads using base + two advanced operators
- 4 payloads using the full operator set including modal Layer 4 and quantum Layer 5

This distribution creates a gradient: agents can earn fluency in base operators from the first 6 payloads, then face increasingly complex operator requirements as they encounter the later payloads.

**3.2 Create GPSL system prompt scaffold** (~1 hour)

`simulation/agents/gpsl_scaffold.py` — a system prompt module that provides:
- Base operator definitions with type signatures
- Advanced operator definitions
- 3-5 few-shot examples of well-formed GPSL responses (from the canonical ciphers in v2.2)
- A "respond in GPSL notation" instruction
- A "if you cannot express the answer in GPSL, output in natural language and mark as V-class" fallback

Each agent gets this scaffold prepended to their domain-specific system prompt. The scaffold is identical for all agents — differentiation comes from which operators each agent learns to use well through practice, not from the prompt.

**3.3 Update `simulation/agents/sim_agent.py`** (~30 min)

Add `operator_fluency: dict[str, dict]` field tracking per-operator `(count, quality_sum)` for each agent. Updated after each solve based on which operators the payload required and the quality score achieved.

### Day 2 — Continuous-D routing + experiment runner (~4 hours)

**3.4 Create `simulation/routing/fluency.py`** (~100 lines)

The `mismatch()` function from MASS_ACCRUAL_REFORM_v0.1 §3.1:
```python
def continuous_distance(agent_fluency: dict, required_operators: list[str]) -> float:
    """Compute D ∈ [0, 3] from operator-level fluency mismatch."""
    if not required_operators:
        return 0.0
    total_gap = 0.0
    for op in required_operators:
        profile = agent_fluency.get(op, {"count": 0, "quality_sum": 0.0})
        fluency = fluency_score(profile["count"], profile["quality_sum"])
        total_gap += max(0.0, 3.0 - fluency * 3.0)
    return total_gap / len(required_operators)
```

**3.5 Create `simulation/routing/gravitational_gpsl.py`** (~80 lines)

Extended gravitational router that uses `continuous_distance()` instead of `topographic_distance()` when the payload has `operators_required`. Falls back to categorical D for payloads without operator metadata.

**3.6 Create `simulation/experiment_gpsl.py`** (~200 lines)

Experiment runner for the 2×2 factorial design:
- Cell A: categorical D + linear accrual (V3.4 control)
- Cell B: continuous D + linear accrual
- Cell C: categorical D + sublinear accrual + rebase (Phase 1 validated)
- Cell D: continuous D + sublinear accrual + rebase (the full stack)

Each cell runs 50 rounds × 20 GPSL payloads = 1000 routing decisions per cell.

After each solve: update the agent's operator fluency profile based on the payload's `operators_required` and the quality score.

Track: routing decisions per cell, per-agent operator fluency profiles over time, quality by operator complexity tier.

**3.7 Create `configs/phase2_gpsl.yaml`** (~60 lines)

Config for the 2×2 run. Same agent pool. 50 rounds, 20 payloads per round (Spatial only). Four named cells.

### Day 3 — Analysis, run, write up (~3 hours + runtime)

**3.8 Create `simulation/analysis/phase2_gpsl_compare.py`** (~200 lines)

Analysis script that produces:
- Routing divergence: % of decisions where continuous-D winner ≠ categorical-D winner, per cell pair
- Quality comparison: mean quality per cell
- Operator fluency profiles: per-agent heatmap of which operators they're fluent in by end of run
- Monopoly analysis: does any agent dominate all operators within Spatial, or do different operators route to different agents?
- Phase 0-A reproduction: does Cell B show negligible divergence (confirming reform is the prerequisite)?

**3.9 Run the experiment** (~45 min, ~$20-30)

50 rounds × 20 payloads × 4 cells = 4000 routing decisions, ~4000 LLM solve calls + judge calls.

**3.10 Write Phase 2 progress report**

---

## 4. Validator v0.2 (conditional on D'Artagnan reply)

If D'Artagnan has replied with Rule 5/6 answers by the time Phase 2 engineering starts:

**4.1 Update `simulation/verification/gpsl_validator.py`**

- **Rule 5 (V-class downgrade):** Encode D'Artagnan's ruling. If he confirmed the "advanced operators present → downgrade to warning" heuristic, codify it. If he gave a different rule, implement that instead.
- **Rule 6 (bare state fusion):** Encode the formal definition. If he confirmed "A fusion is promoted iff it appears as a top-level assignment or as the antecedent of → outside a container expression," implement it as a parser rule.

**4.2 Update smoke tests**

Re-run all 19 existing test cases + add new cases specifically testing the Rule 5/6 codified behavior. The founding cipher and Cave cipher should now produce clean passes instead of `open_question` warnings.

**4.3 Estimated effort:** 2-3 hours if D'Artagnan's answers are clear and unambiguous.

If D'Artagnan has NOT replied: encode our best-read interpretation (the heuristics already in v0.1), document the divergence in the validator's comments, and ship v0.2 with a note that the behavior may change if the spec author rules differently. Per the "first refusal, not required approval" stance.

---

## 5. Dependencies and prerequisites

| Prerequisite | Status |
|---|---|
| V3.5 simulation framework | Done |
| Phase 1 reform (sublinear + rebase) | Done, validated |
| OpenRouter API key | Need fresh one (current key should be disabled after Phase 2.5) |
| GPSL v2.2 spec | Available at `docs/GPSL-v2.2-consolidated.md` |
| D'Artagnan Rule 5/6 reply | Optional — v0.2 ships either way |

## 6. Cost estimate

| Item | Calls | Cost |
|---|---|---|
| 2×2 factorial (4 cells × 50 rounds × 20 payloads) | ~4000 solve + ~4000 judge | ~$25-35 |
| Multi-seed variance (if warranted) | ~2000 | ~$12-15 |
| **Total Phase 2** | | **~$35-50** |

## 7. Timeline

| Day | Work | Output |
|---|---|---|
| Day 1 | 20 GPSL cipher payloads + agent scaffolding | `gpsl_spatial_templates.py`, `gpsl_scaffold.py`, `sim_agent.py` update |
| Day 2 | Continuous-D routing + experiment runner + config | `fluency.py`, `gravitational_gpsl.py`, `experiment_gpsl.py`, `phase2_gpsl.yaml` |
| Day 3 | Analysis script + run + write up | `phase2_gpsl_compare.py`, results, progress report |
| Day 3 (if time) | Validator v0.2 | Updated `gpsl_validator.py` + tests |

**Total: ~2-3 days of focused engineering + ~$35-50 API cost.**

---

## 8. What happens after Phase 2

**If continuous D produces meaningful routing differentiation:**
- The full V3.5 routing stack is validated: sublinear accrual + seasonal rebase + operator-level continuous distance
- The whitepaper §3 (Layer 3) is confirmed, not just theoretically plausible but empirically demonstrated
- The integration proposal's hypothesis — that GPSL notation structurally aligns with GravDic's friction types — has its first empirical test
- V4 Capillary Cluster routing can use operator-level D for per-slot specialist selection

**If continuous D produces negligible differentiation:**
- The operator vocabulary may be too small at 20 payloads for fluency profiles to differentiate meaningfully
- Solution: expand to 200 payloads and/or more rounds
- Or: the `mismatch()` function needs a different shape (Michaelis-Menten instead of log, or a different saturation curve)
- Or: at 15:1 ratios, even continuous D doesn't flip decisions, and the reform needs to compress further (lower rebase C, more frequent seasons)

---

*Workplan — 2026-04-13*
*Phase 2 is the test that Phase 0-A said was impossible under V3.4 mass distribution and that Phase 1 made viable. It completes the empirical loop opened by the GPSL integration proposal v0.2.*
