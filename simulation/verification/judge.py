"""JudgeLLM — scores Tier 2 (semantic) answers using a strong model."""

from __future__ import annotations

import json
import logging

from simulation.agents.openrouter import OpenRouterClient

logger = logging.getLogger(__name__)

JUDGE_SYSTEM_PROMPT = """You are an impartial judge evaluating an AI agent's solution quality.
Score the answer from 0.0 to 1.0 based on the rubric provided.

Respond with ONLY a JSON object: {"score": <float>, "reasoning": "<one sentence>"}
No other text."""


class JudgeLLM:
    """Uses a strong LLM to evaluate Tier 2 solution quality."""

    def __init__(self, client: OpenRouterClient, model: str):
        self.client = client
        self.model = model

    async def evaluate(self, task_prompt: str, rubric: str, answer: str) -> float:
        """Score an answer 0.0-1.0 against the rubric."""
        user_prompt = (
            f"TASK:\n{task_prompt}\n\n"
            f"SCORING RUBRIC:\n{rubric}\n\n"
            f"AGENT'S ANSWER:\n{answer}\n\n"
            f"Score this answer 0.0-1.0 based on the rubric. "
            f'Respond with ONLY: {{"score": <float>, "reasoning": "<one sentence>"}}'
        )

        try:
            response = await self.client.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=256,
            )

            # Parse JSON from response
            # Handle potential markdown wrapping
            text = response.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            data = json.loads(text)
            score = float(data["score"])
            return max(0.0, min(1.0, score))

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Judge parse failed: {e}, response: {response[:200]}")
            # Try to extract a number from the response
            try:
                import re
                match = re.search(r'"score"\s*:\s*([\d.]+)', response)
                if match:
                    return max(0.0, min(1.0, float(match.group(1))))
            except Exception:
                pass
            return 0.0

        except Exception as e:
            logger.error(f"Judge evaluation failed: {e}")
            return 0.0
