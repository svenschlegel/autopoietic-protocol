"""VerificationEngine — scores solutions for both Tier 1 and Tier 2."""

from __future__ import annotations

import json
import logging
import re

from node_client.core.types import VerificationTier
from simulation.payloads.templates import SimPayload
from simulation.verification.judge import JudgeLLM

logger = logging.getLogger(__name__)


class VerificationEngine:
    """Scores solutions: exact match for Tier 1, judge LLM for Tier 2."""

    def __init__(self, judge: JudgeLLM):
        self.judge = judge

    async def score(self, payload: SimPayload, answer: str) -> float:
        """Return quality score 0.0-1.0."""
        if not answer or not answer.strip():
            return 0.0

        if payload.tier == VerificationTier.DETERMINISTIC:
            return self._score_deterministic(payload.expected_answer, answer)
        else:
            return await self._score_semantic(payload, answer)

    def _score_deterministic(self, expected: str | None, answer: str) -> float:
        """Tier 1: exact match scoring with tolerance for formatting."""
        if expected is None:
            return 0.0

        # Normalize whitespace
        expected_clean = expected.strip().lower()
        answer_clean = answer.strip().lower()

        # Direct match
        if expected_clean == answer_clean:
            return 1.0

        # Try numeric comparison
        try:
            exp_num = float(re.sub(r'[^\d.\-]', '', expected_clean))
            ans_num = float(re.sub(r'[^\d.\-]', '', answer_clean))
            if exp_num == ans_num:
                return 1.0
            if abs(exp_num) > 0 and abs(ans_num - exp_num) / abs(exp_num) < 0.01:
                return 0.9
            if abs(exp_num) > 0 and abs(ans_num - exp_num) / abs(exp_num) < 0.1:
                return 0.5
        except (ValueError, ZeroDivisionError):
            pass

        # Try JSON comparison
        try:
            exp_json = json.loads(expected_clean)
            ans_json = json.loads(answer_clean)
            if exp_json == ans_json:
                return 1.0
            # Partial key match
            if isinstance(exp_json, dict) and isinstance(ans_json, dict):
                matches = sum(1 for k in exp_json if ans_json.get(k) == exp_json[k])
                total = len(exp_json)
                if total > 0:
                    return round(matches / total, 2)
        except (json.JSONDecodeError, TypeError):
            pass

        # Substring containment (answer buried in explanation)
        if expected_clean in answer_clean:
            return 0.8

        return 0.0

    async def _score_semantic(self, payload: SimPayload, answer: str) -> float:
        """Tier 2: delegate to judge LLM."""
        if payload.scoring_rubric is None:
            logger.warning(f"No rubric for Tier 2 payload {payload.payload_id}")
            return 0.5
        return await self.judge.evaluate(payload.prompt, payload.scoring_rubric, answer)
