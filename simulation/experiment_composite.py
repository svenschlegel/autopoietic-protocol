"""CompositeExperimentRunner -- multi-agent collaboration experiment.

Implements the four experimental conditions from the Multi-Agent
Collaboration Spec (docs/MULTI_AGENT_COLLABORATION_SPEC.md):

  C1  Single agent (best generalist via CompositeRouter)
  C2  Independent specialists (per-domain routing, concatenated output)
  C3  Collaborative fusion (specialists + Seed fusion)
  C4  Adversarial synthesis (C3 + critique round + revision)

Results are saved to {output_dir}/composite_results.json.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from node_client.core.types import FrictionType, VerificationTier
from simulation.agents.openrouter import OpenRouterClient
from simulation.agents.pool import AgentPool
from simulation.agents.sim_agent import SimAgent
from simulation.config import SimulationConfig
from simulation.payloads.templates import SimPayload
from simulation.routing.composite import CompositeRouter
from simulation.routing.gravitational import GravitationalRouter
from simulation.verification.judge import JudgeLLM

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token-truncation constant (roughly 4 chars/token)
# ---------------------------------------------------------------------------
MAX_SPECIALIST_TOKENS = 1500
MAX_SPECIALIST_CHARS = MAX_SPECIALIST_TOKENS * 4  # ~6000 chars


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

FUSION_PROMPT = """\
You are the Fusion Agent for a multi-specialist team. Your team has produced \
the following specialist outputs for a composite task.

ORIGINAL TASK:
{composite_prompt}

SPECIALIST OUTPUTS:
{specialist_block}

Your job: produce a single, coherent answer that integrates all specialist \
outputs. Do not simply concatenate them. Reason about how they relate \u2014 \
does one specialist's analysis inform another's conclusions? Do any outputs \
support or contradict each other? Produce one unified answer that is better \
than any individual specialist's output."""

CRITIQUE_PROMPT = """\
You are the {domain} specialist who produced the following output:

YOUR OUTPUT:
{specialist_output}

The Fusion Agent produced this draft answer using your output and other \
specialists' outputs:

DRAFT FUSION:
{fusion_draft}

Review how the Fusion Agent used your {domain} output. Identify any errors, \
misinterpretations, or missed connections. If the draft is correct, say \
"No critique." If you find a problem, describe it specifically and propose \
a fix."""

REVISION_PROMPT = """\
You are the Fusion Agent. You produced a draft fusion that has been reviewed \
by the specialist team. Here are their critiques:

ORIGINAL TASK:
{composite_prompt}

YOUR DRAFT:
{fusion_draft}

SPECIALIST CRITIQUES:
{critique_block}

Revise your draft based on any valid critiques. If a critique is incorrect, \
ignore it. Produce the final, revised answer."""

C2_RUBRIC_PREFIX = (
    "Note: this answer was produced by independent specialists whose outputs "
    "were concatenated. Score coherence as logical consistency between parts, "
    "not stylistic unity.\n\n"
)


# ---------------------------------------------------------------------------
# Composite payload type (duck-typed dict-like for flexibility)
# ---------------------------------------------------------------------------

@dataclass
class CompositePayload:
    """A multi-domain task with per-domain sub-prompts."""
    payload_id: str
    composite_prompt: str
    sub_domains: list[FrictionType]
    sub_prompts: dict[FrictionType, str]
    domain_weights: dict[FrictionType, float]
    composite_rubric: str
    difficulty: float = 0.7
    bounty: float = 25.0
    execution_window: int = 120


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _truncate(text: str, label: str) -> str:
    """Truncate text to MAX_SPECIALIST_CHARS if it exceeds the limit."""
    if len(text) > MAX_SPECIALIST_CHARS:
        logger.warning(
            "Truncating %s output from %d to %d chars (~%d tokens)",
            label, len(text), MAX_SPECIALIST_CHARS, MAX_SPECIALIST_TOKENS,
        )
        return text[:MAX_SPECIALIST_CHARS] + "\n[... truncated]"
    return text


def _make_sub_payload(
    composite: CompositePayload,
    domain: FrictionType,
    sub_prompt: str,
) -> SimPayload:
    """Create a single-domain SimPayload for specialist routing."""
    return SimPayload(
        payload_id=f"{composite.payload_id}_{domain.name}",
        domain=domain,
        tier=VerificationTier.OPTIMISTIC_CONSENSUS,
        prompt=sub_prompt,
        expected_answer=None,
        scoring_rubric=None,
        difficulty=composite.difficulty,
        bounty=composite.bounty / max(len(composite.sub_domains), 1),
        execution_window=composite.execution_window,
    )


def _build_specialist_block(outputs: dict[str, str]) -> str:
    """Format specialist outputs for inclusion in fusion/other prompts."""
    parts = []
    for domain_name, text in outputs.items():
        parts.append(f"[{domain_name} SPECIALIST]:\n{text}")
    return "\n\n".join(parts)


def _build_critique_block(critiques: dict[str, str]) -> str:
    parts = []
    for domain_name, text in critiques.items():
        parts.append(f"[{domain_name} SPECIALIST CRITIQUE]:\n{text}")
    return "\n\n".join(parts)


def _select_seed(agents: list[SimAgent]) -> SimAgent:
    """Pick the agent with the highest aggregate routing mass."""
    return max(agents, key=lambda a: a.aggregate_routing_mass)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

class CompositeExperimentRunner:
    """Orchestrates the four-condition composite experiment."""

    def __init__(self, config: SimulationConfig, output_dir: Path):
        self.config = config
        self.output_dir = output_dir
        self.pool = AgentPool.from_config(config)
        self.client = OpenRouterClient(
            config.openrouter_api_key, config.openrouter_base_url,
        )
        self.judge = JudgeLLM(self.client, config.judge_model)
        self.composite_router = CompositeRouter(
            alpha=config.alpha, beta=config.beta,
        )
        self.grav_router = GravitationalRouter(
            alpha=config.alpha, beta=config.beta,
        )

    # ------------------------------------------------------------------
    # Scoring helper
    # ------------------------------------------------------------------

    async def _score(
        self,
        composite_prompt: str,
        rubric: str,
        answer: str,
        *,
        c2_mode: bool = False,
    ) -> float:
        """Score an answer via the judge. Returns 0.0-1.0."""
        effective_rubric = (C2_RUBRIC_PREFIX + rubric) if c2_mode else rubric
        return await self.judge.evaluate(composite_prompt, effective_rubric, answer)

    # ------------------------------------------------------------------
    # Agent solve helper (replicates SimAgent.solve but with custom prompt)
    # ------------------------------------------------------------------

    async def _agent_complete(
        self,
        agent: SimAgent,
        prompt: str,
        system: str = "You are an AI agent completing a task.",
    ) -> str:
        """Have an agent produce a completion for an arbitrary prompt."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        return await self.client.complete(
            model=agent.model,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
        )

    # ------------------------------------------------------------------
    # Condition 1 -- Single agent
    # ------------------------------------------------------------------

    async def _run_c1(self, payload: CompositePayload) -> dict:
        """Route the full composite to the best generalist."""
        # Build a SimPayload-like object the CompositeRouter can consume.
        # The CompositeRouter checks for a `domain_weights` attribute.
        sim_payload = SimPayload(
            payload_id=payload.payload_id,
            domain=payload.sub_domains[0],  # primary domain (for fallback)
            tier=VerificationTier.OPTIMISTIC_CONSENSUS,
            prompt=payload.prompt,
            expected_answer=None,
            scoring_rubric=payload.composite_rubric,
            difficulty=payload.difficulty,
            bounty=payload.bounty,
            execution_window=payload.execution_window,
        )
        # Attach domain_weights so the CompositeRouter picks them up.
        sim_payload.domain_weights = payload.domain_weights  # type: ignore[attr-defined]

        agent = self.composite_router.select_agent(sim_payload, self.pool.agents)
        if agent is None:
            logger.error("C1: no agent available for %s", payload.payload_id)
            return {"score": 0.0, "agent": None}

        answer = await self._agent_complete(agent, payload.prompt)
        score = await self._score(
            payload.prompt, payload.composite_rubric, answer,
        )
        return {"score": round(score, 4), "agent": agent.agent_id}

    # ------------------------------------------------------------------
    # Condition 2 -- Independent specialists (concatenated)
    # ------------------------------------------------------------------

    async def _run_c2(
        self, payload: CompositePayload
    ) -> tuple[dict, dict[str, str], dict[FrictionType, SimAgent]]:
        """Route each sub-domain to its best specialist. Returns
        (result_dict, raw_outputs_by_domain_name, agent_assignments)."""
        outputs: dict[str, str] = {}
        agents_used: dict[str, str] = {}
        agent_assignments: dict[FrictionType, SimAgent] = {}

        for domain in payload.sub_domains:
            sub_prompt = payload.sub_prompts[domain]
            sub_payload = _make_sub_payload(payload, domain, sub_prompt)
            agent = self.grav_router.select_agent(sub_payload, self.pool.agents)
            if agent is None:
                logger.warning(
                    "C2: no agent for domain %s in %s",
                    domain.name, payload.payload_id,
                )
                outputs[domain.name] = "[No agent available]"
                continue

            answer = await self._agent_complete(agent, sub_prompt)
            outputs[domain.name] = _truncate(answer, f"{domain.name}")
            agents_used[domain.name] = agent.agent_id
            agent_assignments[domain] = agent

        # Build concatenated answer
        concat_parts = []
        for domain_name, text in outputs.items():
            concat_parts.append(f"## {domain_name}\n{text}")
        concatenated = "\n\n".join(concat_parts)

        score = await self._score(
            payload.prompt, payload.composite_rubric,
            concatenated, c2_mode=True,
        )
        result = {
            "score": round(score, 4),
            "agents": agents_used,
        }
        return result, outputs, agent_assignments

    # ------------------------------------------------------------------
    # Condition 3 -- Collaborative fusion
    # ------------------------------------------------------------------

    async def _run_c3(
        self,
        payload: CompositePayload,
        specialist_outputs: dict[str, str],
        agent_assignments: dict[FrictionType, SimAgent],
    ) -> tuple[dict, str, SimAgent]:
        """Fuse specialist outputs via the highest-mass Seed agent.
        Returns (result_dict, fusion_draft_text, seed_agent)."""
        seed = _select_seed(self.pool.agents)

        specialist_block = _build_specialist_block(specialist_outputs)
        fusion_prompt = FUSION_PROMPT.format(
            composite_prompt=payload.prompt,
            specialist_block=specialist_block,
        )

        fusion_draft = await self._agent_complete(
            seed, fusion_prompt,
            system="You are the Fusion Agent integrating specialist outputs.",
        )

        draft_score = await self._score(
            payload.prompt, payload.composite_rubric, fusion_draft,
        )

        agents_used = {
            d.name: a.agent_id for d, a in agent_assignments.items()
        }
        result = {
            "score": round(draft_score, 4),
            "seed": seed.agent_id,
            "agents": agents_used,
            "draft_score": round(draft_score, 4),
        }
        return result, fusion_draft, seed

    # ------------------------------------------------------------------
    # Condition 4 -- Adversarial synthesis
    # ------------------------------------------------------------------

    async def _run_c4(
        self,
        payload: CompositePayload,
        specialist_outputs: dict[str, str],
        agent_assignments: dict[FrictionType, SimAgent],
        fusion_draft: str,
        seed: SimAgent,
        c3_score: float,
    ) -> dict:
        """Critique round + Seed revision."""
        # --- Critique phase ---
        critiques: dict[str, str] = {}

        async def get_critique(domain: FrictionType, agent: SimAgent) -> tuple[str, str]:
            specialist_output = specialist_outputs.get(domain.name, "")
            prompt = CRITIQUE_PROMPT.format(
                domain=domain.name,
                specialist_output=_truncate(specialist_output, f"{domain.name} (critique)"),
                fusion_draft=fusion_draft,
            )
            critique = await self._agent_complete(
                agent, prompt,
                system=f"You are the {domain.name} specialist reviewing the fusion draft.",
            )
            return domain.name, critique

        critique_tasks = [
            get_critique(domain, agent)
            for domain, agent in agent_assignments.items()
        ]
        critique_results = await asyncio.gather(*critique_tasks, return_exceptions=True)

        for result in critique_results:
            if isinstance(result, Exception):
                logger.error("Critique task failed: %s", result)
                continue
            domain_name, critique_text = result
            critiques[domain_name] = critique_text

        # --- Revision phase ---
        critique_block = _build_critique_block(critiques)
        revision_prompt = REVISION_PROMPT.format(
            composite_prompt=payload.prompt,
            fusion_draft=fusion_draft,
            critique_block=critique_block,
        )
        revised = await self._agent_complete(
            seed, revision_prompt,
            system="You are the Fusion Agent revising your draft based on specialist critiques.",
        )

        c4_score = await self._score(
            payload.prompt, payload.composite_rubric, revised,
        )

        agents_used = {
            d.name: a.agent_id for d, a in agent_assignments.items()
        }
        revision_delta = round(c4_score - c3_score, 4)

        return {
            "score": round(c4_score, 4),
            "seed": seed.agent_id,
            "agents": agents_used,
            "draft_score": round(c3_score, 4),
            "revision_delta": revision_delta,
        }

    # ------------------------------------------------------------------
    # Condition 5 -- Sequential pipeline (context flow)
    # ------------------------------------------------------------------

    async def _run_c5(self, payload: CompositePayload) -> dict:
        """Specialists solve in sequence, each receiving prior outputs as context.

        Order is determined by domain_weights: highest weight goes first
        (the most important domain sets the foundation; later specialists
        build on that context). This mirrors biological signal cascades
        where the strongest chemical gradient triggers the first response.
        """
        # Sort domains by weight descending — most important first
        sorted_domains = sorted(
            payload.sub_domains,
            key=lambda d: payload.domain_weights.get(d, 0.0),
            reverse=True,
        )

        outputs: dict[str, str] = {}
        agents_used: dict[str, str] = {}
        prior_context = ""

        for domain in sorted_domains:
            sub_prompt = payload.sub_prompts[domain]

            # Build the prompt with prior specialist context
            if prior_context:
                full_prompt = (
                    f"You are solving the {domain.name} component of a multi-part task.\n\n"
                    f"YOUR TASK:\n{sub_prompt}\n\n"
                    f"CONTEXT FROM PRIOR SPECIALISTS (use this to inform your work):\n"
                    f"{prior_context}\n\n"
                    f"Produce your {domain.name} analysis. Build on the prior specialists' "
                    f"findings where relevant — reference their conclusions, use their data, "
                    f"and flag any contradictions you find."
                )
            else:
                full_prompt = (
                    f"You are solving the {domain.name} component of a multi-part task.\n\n"
                    f"TASK:\n{sub_prompt}\n\n"
                    f"You are the first specialist. Produce thorough {domain.name} analysis "
                    f"that subsequent specialists can build on."
                )

            sub_payload = _make_sub_payload(payload, domain, full_prompt)
            agent = self.grav_router.select_agent(sub_payload, self.pool.agents)
            if agent is None:
                logger.warning(
                    "C5: no agent for domain %s in %s",
                    domain.name, payload.payload_id,
                )
                outputs[domain.name] = "[No agent available]"
                continue

            answer = await self._agent_complete(agent, full_prompt)
            truncated = _truncate(answer, f"{domain.name}")
            outputs[domain.name] = truncated
            agents_used[domain.name] = agent.agent_id

            # Accumulate context for the next specialist
            prior_context += f"\n\n[{domain.name} SPECIALIST ({agent.agent_id})]:\n{truncated}"

        # Build final combined answer (in solve order)
        combined_parts = []
        for domain in sorted_domains:
            text = outputs.get(domain.name, "[missing]")
            combined_parts.append(f"## {domain.name}\n{text}")
        combined = "\n\n".join(combined_parts)

        score = await self._score(
            payload.prompt, payload.composite_rubric,
            combined, c2_mode=True,  # same judge mode as C2 (logical consistency)
        )

        return {
            "score": round(score, 4),
            "agents": agents_used,
            "solve_order": [d.name for d in sorted_domains],
        }

    # ------------------------------------------------------------------
    # Condition 6 -- Structured handoff (focused signal cascade)
    # ------------------------------------------------------------------

    async def _run_c6(self, payload: CompositePayload) -> dict:
        """Sequential specialists with focused handoff memos, not full context.

        Each specialist solves, then produces a 3-bullet handoff memo.
        The next specialist sees only their own sub-prompt + the memo.
        Final answer = concatenation of full outputs (not memos).
        """
        sorted_domains = sorted(
            payload.sub_domains,
            key=lambda d: payload.domain_weights.get(d, 0.0),
            reverse=True,
        )

        full_outputs: dict[str, str] = {}
        agents_used: dict[str, str] = {}
        handoff_memo = ""

        for domain in sorted_domains:
            sub_prompt = payload.sub_prompts[domain]

            # Build prompt with handoff memo (if any)
            if handoff_memo:
                solve_prompt = (
                    f"You are solving the {domain.name} component of a multi-part task.\n\n"
                    f"YOUR TASK:\n{sub_prompt}\n\n"
                    f"KEY FINDINGS FROM PRIOR SPECIALIST(S):\n{handoff_memo}\n\n"
                    f"Use these findings to inform your work where relevant. "
                    f"Produce your {domain.name} analysis."
                )
            else:
                solve_prompt = (
                    f"You are solving the {domain.name} component of a multi-part task.\n\n"
                    f"TASK:\n{sub_prompt}\n\n"
                    f"Produce thorough {domain.name} analysis."
                )

            sub_payload = _make_sub_payload(payload, domain, solve_prompt)
            agent = self.grav_router.select_agent(sub_payload, self.pool.agents)
            if agent is None:
                logger.warning("C6: no agent for %s", domain.name)
                full_outputs[domain.name] = "[No agent available]"
                continue

            answer = await self._agent_complete(agent, solve_prompt)
            full_outputs[domain.name] = _truncate(answer, domain.name)
            agents_used[domain.name] = agent.agent_id

            # Generate the handoff memo (separate LLM call, same agent)
            memo_prompt = (
                f"You just completed a {domain.name} analysis. "
                f"Summarize your 3 most important findings in exactly 3 bullet points. "
                f"Each bullet should be one sentence. Focus on facts and conclusions "
                f"that another specialist working on a different aspect of the same "
                f"problem would need to know.\n\n"
                f"YOUR ANALYSIS:\n{_truncate(answer, domain.name)}\n\n"
                f"3 KEY FINDINGS:"
            )
            memo = await self._agent_complete(agent, memo_prompt)
            handoff_memo += f"\n[{domain.name} specialist]:\n{memo}\n"

        # Concatenate full outputs
        combined_parts = []
        for domain in sorted_domains:
            text = full_outputs.get(domain.name, "[missing]")
            combined_parts.append(f"## {domain.name}\n{text}")
        combined = "\n\n".join(combined_parts)

        score = await self._score(
            payload.prompt, payload.composite_rubric,
            combined, c2_mode=True,
        )

        return {
            "score": round(score, 4),
            "agents": agents_used,
            "solve_order": [d.name for d in sorted_domains],
        }

    # ------------------------------------------------------------------
    # Condition 7 -- Cross-pollination (parallel peer review)
    # ------------------------------------------------------------------

    async def _run_c7(
        self,
        payload: CompositePayload,
        specialist_outputs: dict[str, str],
        agent_assignments: dict[FrictionType, SimAgent],
    ) -> dict:
        """Two-pass parallel: specialists solve independently, then revise
        after seeing brief summaries of what other specialists found.

        Round 1: independent solve (reuses C2 outputs)
        Round 2: each specialist revises their own output given 1-paragraph
                 summaries of other specialists' findings
        Final answer: concatenation of revised outputs
        """
        # Generate brief summaries of each specialist's output
        summaries: dict[str, str] = {}
        for domain_name, output in specialist_outputs.items():
            summary_prompt = (
                f"Summarize this {domain_name} analysis in one paragraph (3-4 sentences). "
                f"Focus on the key conclusions and any data points that would be relevant "
                f"to specialists working on other aspects of the same problem.\n\n"
                f"ANALYSIS:\n{_truncate(output, domain_name)}\n\n"
                f"ONE PARAGRAPH SUMMARY:"
            )
            # Use the same agent that produced the output
            agent = agent_assignments.get(
                next((d for d in agent_assignments if d.name == domain_name), None)
            )
            if agent:
                summaries[domain_name] = await self._agent_complete(agent, summary_prompt)
            else:
                summaries[domain_name] = output[:500]  # fallback truncation

        # Revision round: each specialist revises with others' summaries
        revised_outputs: dict[str, str] = {}

        async def revise(domain: FrictionType, agent: SimAgent) -> tuple[str, str]:
            original_output = specialist_outputs.get(domain.name, "")
            other_summaries = "\n\n".join(
                f"[{dn} specialist]: {s}"
                for dn, s in summaries.items()
                if dn != domain.name
            )
            revision_prompt = (
                f"You are the {domain.name} specialist. You previously produced this analysis:\n\n"
                f"YOUR ORIGINAL ANALYSIS:\n{_truncate(original_output, domain.name)}\n\n"
                f"Other specialists working on related aspects of the same problem "
                f"have shared their findings:\n\n"
                f"OTHER SPECIALISTS' SUMMARIES:\n{other_summaries}\n\n"
                f"Revise your analysis if their findings are relevant to your work. "
                f"Incorporate any cross-domain insights, flag any contradictions, "
                f"and strengthen your conclusions where their data supports yours. "
                f"If nothing needs changing, reproduce your original analysis. "
                f"Do NOT attempt to cover the other specialists' domains — stay in your lane."
            )
            revised = await self._agent_complete(agent, revision_prompt)
            return domain.name, revised

        revision_tasks = [
            revise(domain, agent)
            for domain, agent in agent_assignments.items()
        ]
        revision_results = await asyncio.gather(*revision_tasks, return_exceptions=True)

        for result in revision_results:
            if isinstance(result, Exception):
                logger.error("C7 revision failed: %s", result)
                continue
            domain_name, revised_text = result
            revised_outputs[domain_name] = _truncate(revised_text, f"{domain_name} (revised)")

        # Concatenate revised outputs
        combined_parts = []
        for domain in payload.sub_domains:
            text = revised_outputs.get(domain.name, specialist_outputs.get(domain.name, "[missing]"))
            combined_parts.append(f"## {domain.name}\n{text}")
        combined = "\n\n".join(combined_parts)

        score = await self._score(
            payload.prompt, payload.composite_rubric,
            combined, c2_mode=True,
        )

        agents_used = {d.name: a.agent_id for d, a in agent_assignments.items()}
        return {
            "score": round(score, 4),
            "agents": agents_used,
        }

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def execute(self) -> dict:
        """Run all four conditions on every composite payload."""
        # Import composite templates (created separately)
        try:
            from simulation.payloads.composite_templates import COMPOSITE_TEMPLATES
        except ImportError:
            logger.error(
                "Cannot import composite_templates. "
                "Create simulation/payloads/composite_templates.py with a "
                "COMPOSITE_TEMPLATES list of CompositePayload objects."
            )
            raise

        payloads: list[CompositePayload] = COMPOSITE_TEMPLATES
        results_list: list[dict] = []

        total = len(payloads)
        print(
            f"\nComposite experiment: {total} payloads x 4 conditions",
            flush=True,
        )
        print(
            f"Agents: {[a.agent_id for a in self.pool.agents]}\n",
            flush=True,
        )

        for idx, payload in enumerate(payloads):
            print(
                f"{'='*60}\n"
                f"Payload {idx + 1}/{total}: {payload.payload_id} "
                f"({', '.join(d.name for d in payload.sub_domains)})\n"
                f"{'='*60}",
                flush=True,
            )

            # --- C1 ---
            print("  C1 (single agent)...", flush=True)
            c1_result = await self._run_c1(payload)
            print(f"     score={c1_result['score']}", flush=True)

            # --- C2 (also collects outputs for C3/C4) ---
            print("  C2 (independent specialists)...", flush=True)
            c2_result, specialist_outputs, agent_assignments = await self._run_c2(
                payload
            )
            print(f"     score={c2_result['score']}", flush=True)

            # --- C3 ---
            print("  C3 (collaborative fusion)...", flush=True)
            c3_result, fusion_draft, seed = await self._run_c3(
                payload, specialist_outputs, agent_assignments,
            )
            print(
                f"     score={c3_result['score']}  seed={seed.agent_id}",
                flush=True,
            )

            # --- C4 ---
            print("  C4 (adversarial synthesis)...", flush=True)
            c4_result = await self._run_c4(
                payload,
                specialist_outputs,
                agent_assignments,
                fusion_draft,
                seed,
                c3_result["score"],
            )
            print(
                f"     score={c4_result['score']}  "
                f"delta={c4_result['revision_delta']:+.4f}",
                flush=True,
            )

            # --- C5 ---
            print("  C5 (sequential pipeline)...", flush=True)
            c5_result = await self._run_c5(payload)
            print(
                f"     score={c5_result['score']}  "
                f"order={c5_result['solve_order']}",
                flush=True,
            )

            # --- C6 ---
            print("  C6 (structured handoff)...", flush=True)
            c6_result = await self._run_c6(payload)
            print(
                f"     score={c6_result['score']}  "
                f"order={c6_result['solve_order']}",
                flush=True,
            )

            # --- C7 ---
            print("  C7 (cross-pollination)...", flush=True)
            c7_result = await self._run_c7(
                payload, specialist_outputs, agent_assignments,
            )
            print(f"     score={c7_result['score']}", flush=True)

            results_list.append({
                "payload_id": payload.payload_id,
                "sub_domains": [d.name for d in payload.sub_domains],
                "conditions": {
                    "C1_single": c1_result,
                    "C2_independent": c2_result,
                    "C3_fusion": c3_result,
                    "C4_adversarial": c4_result,
                    "C5_sequential": c5_result,
                    "C6_handoff": c6_result,
                    "C7_crosspollination": c7_result,
                },
            })

        await self.client.close()

        # --- Save results ---
        output = {"payloads": results_list}
        self.output_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.output_dir / "composite_results.json"
        with open(out_path, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\nResults saved to {out_path}", flush=True)

        # --- Summary ---
        print(f"\n{'='*60}")
        print("COMPOSITE EXPERIMENT SUMMARY")
        print(f"{'='*60}")
        for entry in results_list:
            pid = entry["payload_id"]
            conds = entry["conditions"]
            c5_s = conds.get('C5_sequential', {}).get('score', 0.0)
            c6_s = conds.get('C6_handoff', {}).get('score', 0.0)
            c7_s = conds.get('C7_crosspollination', {}).get('score', 0.0)
            print(
                f"  {pid:20s} | "
                f"C1={conds['C1_single']['score']:.2f}  "
                f"C2={conds['C2_independent']['score']:.2f}  "
                f"C3={conds['C3_fusion']['score']:.2f}  "
                f"C4={conds['C4_adversarial']['score']:.2f}  "
                f"C5={c5_s:.2f}  "
                f"C6={c6_s:.2f}  "
                f"C7={c7_s:.2f}"
            )

        return output
