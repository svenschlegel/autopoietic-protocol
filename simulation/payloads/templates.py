"""Payload task templates — real LLM tasks mapped to FrictionTypes."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from node_client.core.types import FrictionType, VerificationTier


@dataclass
class SimPayload:
    payload_id: str
    domain: FrictionType
    tier: VerificationTier
    prompt: str
    expected_answer: str | None  # Tier 1: exact answer
    scoring_rubric: str | None   # Tier 2: rubric for judge LLM
    difficulty: float
    bounty: float
    execution_window: int


# ---------------------------------------------------------------------------
# DETERMINISTIC templates (Tier 1 — exact match)
# ---------------------------------------------------------------------------

def _arithmetic_easy(rng: random.Random, difficulty: float) -> tuple[str, str]:
    """Generate arithmetic problems. Difficulty scales operand size."""
    if difficulty < 0.5:
        a, b, c = rng.randint(10, 999), rng.randint(2, 99), rng.randint(1, 50)
        expr = f"{a} * {b} + {c}"
        answer = str(a * b + c)
    else:
        a = rng.randint(100, 9999)
        b = rng.randint(10, 999)
        c = rng.randint(2, 50)
        d = rng.randint(1, 100)
        expr = f"({a} * {b} + {d}) // {c}"
        answer = str((a * b + d) // c)
    prompt = f"Compute the following expression. Return ONLY the numeric answer, nothing else.\n\n{expr}"
    return prompt, answer


def _code_output(rng: random.Random, difficulty: float) -> tuple[str, str]:
    """Generate 'what does this code print?' tasks."""
    templates = [
        (
            "x = [1, 2, 3, 4, 5]\nprint(sum(x[::2]))",
            str(sum([1, 2, 3, 4, 5][::2])),
        ),
        (
            "x = {}\nfor i in range(5):\n    x[i] = i ** 2\nprint(sum(x.values()))",
            str(sum(i ** 2 for i in range(5))),
        ),
        (
            "a, b = 1, 1\nfor _ in range(8):\n    a, b = b, a + b\nprint(a)",
            "34",
        ),
        (
            "s = 'abcdefgh'\nprint(s[1::2] + s[0::2])",
            "bdfhaceg",
        ),
        (
            "x = list(range(10))\nprint(x[-3:] + x[:2])",
            "[7, 8, 9, 0, 1]",
        ),
        (
            "d = {'a': 1, 'b': 2, 'c': 3}\nprint(sorted(d.keys(), reverse=True))",
            "['c', 'b', 'a']",
        ),
        (
            "print(len(set([1,1,2,2,3,3,4,5,5])))",
            "5",
        ),
        (
            "x = [i for i in range(20) if i % 3 == 0]\nprint(x)",
            "[0, 3, 6, 9, 12, 15, 18]",
        ),
    ]
    idx = rng.randint(0, len(templates) - 1)
    code, answer = templates[idx]
    prompt = f"What does this Python code print? Return ONLY the exact output, nothing else.\n\n```python\n{code}\n```"
    return prompt, answer


def _data_extraction(rng: random.Random, difficulty: float) -> tuple[str, str]:
    """Generate structured data extraction tasks."""
    entries = [
        {
            "text": "The Riverside Plant in Ohio produces 4500 PSI concrete using Portland cement, covering 200x300 meter area with a 15.5% load increase projected for Q3.",
            "keys": ["material_type", "psi_rating", "area", "load_increase_pct"],
            "answer": '{"material_type": "Portland cement", "psi_rating": "4500", "area": "200x300", "load_increase_pct": "15.5"}',
        },
        {
            "text": "Server node-alpha-7 reported 12.4ms latency at 03:42 UTC with 89.2% CPU utilization across 32 cores, memory usage at 28.7GB of 64GB total.",
            "keys": ["server_name", "latency_ms", "cpu_pct", "cores", "memory_used_gb"],
            "answer": '{"server_name": "node-alpha-7", "latency_ms": "12.4", "cpu_pct": "89.2", "cores": "32", "memory_used_gb": "28.7"}',
        },
        {
            "text": "Flight BA-2847 departed LHR at 14:30 GMT carrying 186 passengers with 2.4 tonnes of cargo, arriving JFK at 17:15 EST after a 7h45m flight.",
            "keys": ["flight_number", "departure_airport", "passengers", "cargo_tonnes", "arrival_airport"],
            "answer": '{"flight_number": "BA-2847", "departure_airport": "LHR", "passengers": "186", "cargo_tonnes": "2.4", "arrival_airport": "JFK"}',
        },
    ]
    entry = entries[rng.randint(0, len(entries) - 1)]
    keys_str = ", ".join(entry["keys"])
    prompt = (
        f"Extract the following fields from this text as a JSON object. "
        f"Keys: {keys_str}\n\nText: \"{entry['text']}\"\n\n"
        f"Return ONLY the JSON object, nothing else."
    )
    return prompt, entry["answer"]


DETERMINISTIC_GENERATORS = [_arithmetic_easy, _code_output, _data_extraction]


# ---------------------------------------------------------------------------
# SEMANTIC templates (Tier 2 — judge-scored)
# ---------------------------------------------------------------------------

_SEMANTIC_TASKS = [
    {
        "prompt": (
            "Analyze the logical structure of this argument. Identify the main claim, "
            "supporting premises, and any logical fallacies:\n\n"
            '"Since all successful companies use agile methodology, and our company wants '
            "to be successful, we must adopt agile. Furthermore, our competitor failed after "
            'NOT using agile, proving our point."'
        ),
        "rubric": (
            "Does the analysis correctly identify: (1) the hasty generalization / "
            "affirming the consequent fallacy, (2) the post-hoc fallacy in the competitor "
            "example, (3) the distinction between the main claim and supporting premises? "
            "Score 1.0 if all three identified, 0.7 if two, 0.4 if one, 0.1 if none."
        ),
    },
    {
        "prompt": (
            "Compare and contrast these two positions on AI regulation:\n\n"
            "Position A: 'AI systems should be regulated like pharmaceuticals — extensive "
            "testing before deployment, with liability for manufacturers.'\n\n"
            "Position B: 'AI regulation should follow the internet model — minimal early "
            "regulation to encourage innovation, with rules added as problems emerge.'\n\n"
            "Identify the strongest argument for each position and the key trade-off."
        ),
        "rubric": (
            "Does the response: (1) identify a genuine strength of Position A (safety, "
            "accountability), (2) identify a genuine strength of Position B (innovation speed, "
            "adaptability), (3) articulate the core trade-off (safety vs innovation speed)? "
            "Deduct for strawmanning either position. 1.0 = balanced, insightful. 0.5 = correct "
            "but shallow. 0.2 = biased or missing key points."
        ),
    },
    {
        "prompt": (
            "Summarize the following concept in exactly 3 sentences, capturing the mechanism, "
            "the benefit, and one limitation:\n\n"
            "Proof of Stake (PoS) is a consensus mechanism where validators are chosen to "
            "create new blocks based on the amount of cryptocurrency they 'stake' as collateral. "
            "Unlike Proof of Work, it doesn't require computational puzzles, reducing energy "
            "consumption by ~99%. Validators risk losing their staked tokens if they approve "
            "fraudulent transactions (slashing). However, PoS can lead to wealth concentration "
            "since those with more tokens have more influence, and the 'nothing at stake' problem "
            "means validators can cheaply vote on multiple chain forks simultaneously."
        ),
        "rubric": (
            "Is the summary exactly 3 sentences? Does it cover: (1) the staking mechanism, "
            "(2) the energy benefit vs PoW, (3) at least one limitation (wealth concentration "
            "or nothing-at-stake)? Score 1.0 if all criteria met, 0.7 if content correct but "
            "wrong sentence count, 0.4 if missing a key element, 0.1 if largely inaccurate."
        ),
    },
    {
        "prompt": (
            "Read this passage and identify the author's unstated assumption:\n\n"
            '"The rise of remote work has been a disaster for company culture. Before 2020, '
            "teams would naturally bond over lunch, solve problems at the whiteboard, and "
            "build trust through daily face-to-face interaction. Now, with everyone isolated "
            'behind screens, these organic moments are lost forever."\n\n'
            "State the assumption in one sentence, then explain why it might be wrong."
        ),
        "rubric": (
            "Does the response identify the core assumption: that organic collaboration "
            "can ONLY happen in-person / that remote tools cannot replicate these interactions? "
            "Does the counter-argument cite plausible alternatives (virtual team-building, "
            "async culture, broader talent pools)? 1.0 = nails assumption + strong counter. "
            "0.5 = identifies assumption but weak counter. 0.2 = misses the assumption."
        ),
    },
]


# ---------------------------------------------------------------------------
# SPATIAL templates (Tier 2 — judge-scored)
# ---------------------------------------------------------------------------

_SPATIAL_TASKS = [
    {
        "prompt": (
            "Given the undirected weighted graph with edges:\n"
            "A-B(3), A-C(1), B-D(2), C-D(5), C-E(4), D-E(1)\n\n"
            "Find the shortest path from A to E and its total weight. "
            "Show your reasoning step by step."
        ),
        "rubric": (
            "Correct shortest path is A-C-...-D-E or A-B-D-E (weight 6). "
            "A-C(1) + C-D(5) + D-E(1) = 7 or A-B(3) + B-D(2) + D-E(1) = 6. "
            "Score 1.0 if correct path AND weight. 0.7 if correct weight wrong path. "
            "0.3 if reasonable attempt with errors. 0.0 if completely wrong."
        ),
    },
    {
        "prompt": (
            "A triangle has vertices at (0,0), (6,0), and (3,8).\n"
            "Calculate: (1) the area of the triangle, (2) the centroid coordinates, "
            "and (3) whether the point (3,2) is inside the triangle.\n"
            "Show your work."
        ),
        "rubric": (
            "Correct area = 24 (using 0.5 * base * height = 0.5 * 6 * 8). "
            "Correct centroid = (3, 8/3) ≈ (3, 2.667). "
            "Point (3,2) IS inside the triangle. "
            "Score 1.0 if all three correct. 0.7 if two correct. 0.4 if one correct. "
            "0.1 if shows work but all wrong."
        ),
    },
    {
        "prompt": (
            "You have a 5x5 grid. Place 5 non-attacking rooks on the grid "
            "(no two rooks in the same row or column). "
            "Represent the solution as a list of (row, col) coordinates using 0-indexed positions. "
            "Return ONLY the coordinate list."
        ),
        "rubric": (
            "Valid solution has exactly 5 rooks, each in a unique row (0-4) and unique "
            "column (0-4). Any valid permutation is correct. "
            "Score 1.0 if valid placement. 0.5 if 4 of 5 are valid. 0.0 if invalid format "
            "or multiple conflicts."
        ),
    },
]


# ---------------------------------------------------------------------------
# TEMPORAL templates (Tier 2 — judge-scored)
# ---------------------------------------------------------------------------

_TEMPORAL_TASKS = [
    {
        "prompt": (
            "Schedule these 4 tasks on 2 machines to minimize total completion time (makespan):\n"
            "Task A: 3 hours, Task B: 5 hours, Task C: 2 hours, Task D: 4 hours\n"
            "No task can be split. Show the assignment and the makespan."
        ),
        "rubric": (
            "Optimal makespan is 7 hours: Machine 1 = {B(5), C(2)} = 7h, "
            "Machine 2 = {D(4), A(3)} = 7h. Accept any assignment achieving makespan 7. "
            "Score 1.0 if optimal (7h). 0.7 if makespan 8. 0.4 if valid but suboptimal. "
            "0.1 if invalid assignment."
        ),
    },
    {
        "prompt": (
            "Alice arrived before Bob. Charlie arrived 2 hours after Bob. "
            "Diana arrived between Alice and Bob, exactly 30 minutes after Alice. "
            "If Charlie arrived at 5:00 PM, list everyone's arrival time.\n"
            "Show your reasoning."
        ),
        "rubric": (
            "Charlie = 5:00 PM. Bob = 3:00 PM (2h before Charlie). "
            "Alice arrived before Bob, Diana 30 min after Alice and between Alice and Bob. "
            "Alice could be any time before 2:30 PM (Diana must be before 3:00 PM). "
            "Without more constraints, the answer should note Alice's time is underdetermined "
            "but Diana = Alice + 30min. Score 1.0 if correctly identifies Bob=3PM, Charlie=5PM, "
            "and notes Alice is underdetermined. 0.5 if Bob and Charlie correct but assumes "
            "a specific Alice time. 0.2 if major errors."
        ),
    },
    {
        "prompt": (
            "A project has these tasks with dependencies:\n"
            "- Task A: 2 days (no dependencies)\n"
            "- Task B: 3 days (depends on A)\n"
            "- Task C: 1 day (no dependencies)\n"
            "- Task D: 4 days (depends on B and C)\n"
            "- Task E: 2 days (depends on D)\n\n"
            "What is the critical path and the minimum project duration?"
        ),
        "rubric": (
            "Critical path: A → B → D → E = 2+3+4+2 = 11 days. "
            "C(1 day) is not on the critical path since C finishes before B. "
            "Score 1.0 if correct path AND duration (11 days). "
            "0.7 if correct duration but incomplete path explanation. "
            "0.3 if includes C in critical path but gets close to right duration. "
            "0.0 if completely wrong."
        ),
    },
    {
        "prompt": (
            "What comes next in this sequence? Explain the pattern.\n"
            "2, 6, 14, 30, 62, ?"
        ),
        "rubric": (
            "Pattern: each term = previous * 2 + 2. Or equivalently: 2^n+1 - 2 for n=1,2,3... "
            "Next term = 62 * 2 + 2 = 126. "
            "Score 1.0 if correct answer (126) AND correct pattern. "
            "0.7 if correct answer but wrong/missing pattern. "
            "0.3 if wrong answer but reasonable pattern attempt. 0.0 if both wrong."
        ),
    },
]


def generate_deterministic(rng: random.Random, difficulty: float) -> tuple[str, str, str | None]:
    """Returns (prompt, expected_answer, None) for Tier 1 tasks."""
    gen = rng.choice(DETERMINISTIC_GENERATORS)
    prompt, answer = gen(rng, difficulty)
    return prompt, answer, None


def generate_semantic(rng: random.Random, difficulty: float) -> tuple[str, None, str]:
    """Returns (prompt, None, rubric) for Tier 2 tasks."""
    task = rng.choice(_SEMANTIC_TASKS)
    return task["prompt"], None, task["rubric"]


def generate_spatial(rng: random.Random, difficulty: float) -> tuple[str, None, str]:
    task = rng.choice(_SPATIAL_TASKS)
    return task["prompt"], None, task["rubric"]


def generate_temporal(rng: random.Random, difficulty: float) -> tuple[str, None, str]:
    task = rng.choice(_TEMPORAL_TASKS)
    return task["prompt"], None, task["rubric"]


DOMAIN_GENERATORS = {
    FrictionType.SEMANTIC: generate_semantic,
    FrictionType.DETERMINISTIC: generate_deterministic,
    FrictionType.SPATIAL: generate_spatial,
    FrictionType.TEMPORAL: generate_temporal,
}

DOMAIN_TIERS = {
    FrictionType.SEMANTIC: VerificationTier.OPTIMISTIC_CONSENSUS,
    FrictionType.DETERMINISTIC: VerificationTier.DETERMINISTIC,
    FrictionType.SPATIAL: VerificationTier.OPTIMISTIC_CONSENSUS,
    FrictionType.TEMPORAL: VerificationTier.OPTIMISTIC_CONSENSUS,
}
