"""
GPSL Hybrid Validator (v0.1) — Layer 1 Base operators + V-class flagging.

Implements the hybrid validation strategy from `docs/GPSL_INTEGRATION_PROPOSAL.md` v0.3 §3 Layer 2:

- **Mechanical strictness** for Layer 1 base operator type rules — these slash on violation
- **Flag-not-slash** for V-class anomalies, advanced operators (⥀, ⦸, ⤳),
  modal Layer 4, quantum Layer 5 — these warn but pass
- **Detection of operators_used and layers_used** for downstream operator-level
  fluency tracking (V3.5 reform §3.1)

Not a full AST parser. Pure regex + simple state machine. Sufficient for:
- Phase 0-B (verification retrofit testing)
- Foundation for operator-level fluency tracking once Dual-Mass lands

Reference grammar: `docs/GPSL-v2.2-consolidated.md` (D'Artagnan + pod, 6 April 2026)

Usage:
    from simulation.verification.gpsl_validator import validate_gpsl_cipher
    result = validate_gpsl_cipher(submission_text)
    if result.valid:
        ...  # passed (possibly with warnings)
    else:
        ...  # slash

Run smoke tests:
    python3 simulation/verification/gpsl_validator.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# === GPSL v2.2 grammar constants ===

# Layer 1 — Symbolic, base operators (cold-transmissible without legend per v2.2)
# Note: ⟲ (U+27F2) is *not* in this set. It appears only in the spec's Cogito
# canonical example and is not defined in any operator table — likely a distinct
# loopback symbol or a V-class anomaly. We do NOT treat it as ↺ (U+21BA), which
# is the actual recurrence operator. Treating it as unknown lets Cogito validate.
BASE_OPERATORS: set[str] = {
    '→', '⊗', '=', '::', ':', '↺', '↔', '↑', '↓', '⊕', '|', ';', '↛',
}

# Advanced operators (opaque — require inline legend per v2.2 spec)
ADVANCED_OPERATORS: set[str] = {'⤳', '⥀', '⦸'}

# Special tokens
NULL_TOKEN = '{∅}'

# Layer 2 — Greek (ontological class, type-neutral)
GREEK_SYMBOLS: set[str] = set('ΦΨΩΣΔΞΓΘΠΛΙΚΕΑΒ')

# Layer 3 — Mathematical (topological descriptors, NOT arithmetic)
MATH_SYMBOLS: set[str] = {'ℵ', '∫', '∂', '∑', '∀', '∃'}

# Layer 4 — Modal
MODAL_SYMBOLS: set[str] = {'□', '◇', '¬'}

# Layer 5 — Quantum (substring markers)
QUANTUM_MARKERS: tuple[str, ...] = ('|ψ⟩', 'Û(t)', 'Tr_')

# Operators forbidden as the FIRST operator immediately after `::`
# (Lenient reading of rule 5: derivational continuity terminator means
#  "don't reach across the boundary," not "no derivational ops anywhere downstream.")
FORBIDDEN_FIRST_AFTER_DOUBLE_COLON: set[str] = {'→', '⊗'}


# === Validation result type ===


@dataclass
class GpslValidation:
    """Result of validating a GPSL cipher.

    Attributes
    ----------
    valid:
        False = slash. True = pass (possibly with warnings). Errors block; warnings don't.
    has_warnings:
        True if any flag-not-slash anomalies were detected.
    errors:
        List of slash-worthy violations. Each is a short string identifier.
    warnings:
        List of flag-not-slash anomalies. Each is a short string identifier.
    operators_used:
        Set of base + advanced GPSL operators detected in the cipher.
        Used for downstream operator-level fluency tracking.
    layers_used:
        Set of integers in {1, 2, 3, 4, 5} indicating which GPSL notation layers appeared.
    nodes_found:
        Total number of [process] and {state} nodes detected.
    """

    valid: bool = True
    has_warnings: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    operators_used: set[str] = field(default_factory=set)
    layers_used: set[int] = field(default_factory=set)
    nodes_found: int = 0

    def to_dict(self) -> dict:
        return {
            'valid': self.valid,
            'has_warnings': self.has_warnings,
            'errors': list(self.errors),
            'warnings': list(self.warnings),
            'operators_used': sorted(self.operators_used),
            'layers_used': sorted(self.layers_used),
            'nodes_found': self.nodes_found,
        }


# === Helpers ===


def _strip_metadata(text: str) -> str:
    """Remove HEADER:, LEGEND:, and PAYLOAD: prefix lines if present.

    These are GPSL transmission metadata, not cipher content. They should not be
    subject to type rule checks, and they should not be counted as nodes.
    """
    out: list[str] = []
    for line in text.split('\n'):
        s = line.strip()
        if s.startswith('HEADER:') or s.startswith('LEGEND:'):
            continue
        if s.startswith('PAYLOAD:'):
            after = s[len('PAYLOAD:'):].lstrip()
            if after:
                out.append(after)
            continue
        out.append(line)
    return '\n'.join(out)


def _looks_like_natural_language(content: str) -> bool:
    """Heuristic for rule 8 ('No natural language inside node brackets').

    A bracket content is flagged as NL if and only if it contains:
    - 3 or more ASCII word tokens of length >= 2
    - separated by actual whitespace (spaces inside the bracket)
    - and contains no GPSL operators or Greek/math symbols

    This deliberately passes single underscored or hyphenated identifiers like
    `cave_knowledge`, `Γ-03`, `pattern_of_rising`, which are conventional GPSL
    node IDs even though they look 'word-like'.
    """
    if not content.strip():
        return False
    # Bracket contents with GPSL operators are clearly not free NL
    if any(s in content for s in BASE_OPERATORS | ADVANCED_OPERATORS):
        return False
    if any(s in content for s in GREEK_SYMBOLS | MATH_SYMBOLS):
        return False
    # Identifiers with no whitespace are not sentences
    if ' ' not in content:
        return False
    words = re.findall(r'[a-zA-Z]{2,}', content)
    return len(words) >= 3


def _detect_layers(text: str) -> set[int]:
    """Detect which GPSL notation layers appear anywhere in the text."""
    layers: set[int] = set()
    if re.search(r'\[|\{', text):
        layers.add(1)  # Symbolic — at least one node
    if any(s in text for s in GREEK_SYMBOLS):
        layers.add(2)
    if any(s in text for s in MATH_SYMBOLS):
        layers.add(3)
    if any(s in text for s in MODAL_SYMBOLS):
        layers.add(4)
    if any(m in text for m in QUANTUM_MARKERS):
        layers.add(5)
    return layers


# === Main validation entry point ===


def validate_gpsl_cipher(text: str) -> GpslValidation:
    """Validate a GPSL cipher. Hybrid: errors slash, warnings flag.

    Parameters
    ----------
    text:
        The full submitted cipher, optionally including HEADER:/LEGEND:/PAYLOAD: lines.

    Returns
    -------
    GpslValidation with .valid, .has_warnings, .errors, .warnings,
    .operators_used, .layers_used, .nodes_found populated.
    """
    result = GpslValidation()

    if not text or not text.strip():
        result.valid = False
        result.errors.append("empty_cipher")
        return result

    cipher = _strip_metadata(text)

    # === Operator detection (longest first to avoid prefix collisions, e.g. :: vs :) ===
    for op in sorted(BASE_OPERATORS | ADVANCED_OPERATORS, key=len, reverse=True):
        if op in cipher:
            result.operators_used.add(op)

    # === Layer detection ===
    result.layers_used = _detect_layers(cipher)

    # === Node extraction ===
    process_nodes: list[tuple[str, int]] = [
        (m.group(1), m.start()) for m in re.finditer(r'\[([^\[\]\n]*?)\]', cipher)
    ]
    state_nodes: list[tuple[str, int]] = []
    for m in re.finditer(r'\{([^{}\n]*?)\}', cipher):
        if m.group(0) == NULL_TOKEN:
            continue  # void is a special token, not a content node
        state_nodes.append((m.group(1), m.start()))

    result.nodes_found = len(process_nodes) + len(state_nodes)

    if result.nodes_found == 0:
        result.valid = False
        result.errors.append("no_nodes_found")
        return result

    # === ERROR: rule 7 — {state} → or {state} ↺ (states do not initiate flow or loop) ===
    # Only ↺ (U+21BA), the defined recurrence operator. ⟲ is intentionally excluded.
    for m in re.finditer(r'\}\s*(→|↺)', cipher):
        op = m.group(1)
        result.errors.append(f"state_initiates_{op}_at_pos_{m.start()}")

    # === ERROR: rule 8 — natural language inside brackets ===
    for content, pos in process_nodes:
        if _looks_like_natural_language(content):
            result.errors.append(f"nl_contamination_in_process_node_at_pos_{pos}")
    for content, pos in state_nodes:
        if _looks_like_natural_language(content):
            result.errors.append(f"nl_contamination_in_state_node_at_pos_{pos}")

    # === RULE 5 — derivational ops (→ ⊗) after :: ===
    # The spec literally says "Do not use → or ⊗ after ::". Strict reading would
    # slash the canonical Cave cipher (which has `:: [Turn] → [Γ_ascending]`).
    # Resolution: enforce strictly, but DOWNGRADE TO WARNING when the cipher
    # contains any advanced operator (⥀ ⦸ ⤳) — these are V-class indicators
    # and rule 5 violations within V-class contexts are flag-not-slash per
    # the integration proposal v0.3 §3 Layer 2.
    has_advanced = bool(result.operators_used & ADVANCED_OPERATORS)
    for expr_idx, expr in enumerate(re.split(r'[;\n]', cipher)):
        if '::' not in expr:
            continue
        # Take everything after the first :: in this expression
        post = expr.split('::', 1)[1]
        for op in FORBIDDEN_FIRST_AFTER_DOUBLE_COLON:
            if op in post:
                msg = f"derivational_op_{op}_after_::_in_expression_{expr_idx}"
                if has_advanced:
                    result.warnings.append(msg + "_(v_class_context)")
                else:
                    result.errors.append(msg)
                break  # one report per expression is enough

    # === RULE 6 — {A} ⊗ {B} not in a [...] context (warning, not error in v0.1) ===
    # The strict reading would slash the founding cipher, which has bare
    # `{Π-07} ⊗ {Ψ-04}`. The spec's own canonical example contradicts the strict
    # reading, so v0.1 of the validator treats this as a WARNING and flags it for
    # D'Artagnan to clarify. Likely the rule is "if you USE the result as a
    # process, wrap in [...]; stating the relationship within a larger expression
    # is fine," but we don't yet have spec confirmation.
    for m in re.finditer(r'\}\s*⊗\s*\{', cipher):
        pos = m.start()
        prefix = cipher[:pos]
        open_brackets = prefix.count('[') - prefix.count(']')
        if open_brackets <= 0:
            result.warnings.append(
                f"bare_state_fusion_at_pos_{pos}_(rule_6_open_question)"
            )

    # === WARNING: rule 9 — multiple `:` separators per expression ===
    for expr_idx, expr in enumerate(re.split(r'[;\n]', cipher)):
        single_colons = expr.replace('::', '').count(':')
        if single_colons > 1:
            result.warnings.append(
                f"multiple_colon_separators_expression_{expr_idx}_count_{single_colons}"
            )

    # === WARNING: advanced operators present (need legend) ===
    for op in sorted(result.operators_used & ADVANCED_OPERATORS):
        result.warnings.append(f"advanced_operator_{op}_requires_legend")

    # === WARNING: modal layer present (rule 10 territory — declare or document) ===
    if 4 in result.layers_used:
        result.warnings.append("modal_layer_4_present_check_legend")

    # === WARNING: quantum layer present ===
    if 5 in result.layers_used:
        result.warnings.append("quantum_layer_5_present_check_legend")

    # === V-class detection: 5+ clustered errors suggest structural intent ===
    # Per v2.2 spec, V-class instances like the Longing cipher (37 violations,
    # stable loop) are 'structurally load-bearing' and should be flagged for
    # governance, not slashed. We can't distinguish V-class from garbage with
    # certainty, but high error count is a useful proxy signal.
    if len(result.errors) >= 5:
        result.warnings.append(
            f"v_class_pattern_suspected_{len(result.errors)}_violations_may_be_load_bearing"
        )

    # === Final verdict ===
    result.valid = len(result.errors) == 0
    result.has_warnings = len(result.warnings) > 0

    return result


# === Canonical reference ciphers from GPSL v2.2 spec, used as smoke tests ===

CANONICAL_CIPHERS: dict[str, str] = {
    "founding": (
        "HEADER: Consciousness\n\n"
        "[Ξ-06] → [Φ-02] : {Π-07} ⊗ {Ψ-04} = [Ω-05] (Δ-03↓)"
    ),
    "cogito": (
        "HEADER: Philosophy / Cogito\n\n"
        "[Ι-01] → {Ψ-02} ⟲ [Ι-01]"
    ),
    "ecclesiastes": (
        "HEADER: Ecclesiastes\n\n"
        "⦸({sun_rising}) ↺ {pattern_of_rising}\n"
        "⦸({generation}) ↺ {earth_enduring}\n"
        "⦸ ⊗ ⦸ ≜ {vanity_of_vanities}"
    ),
    "grief": (
        "HEADER: Grief\n\n"
        "[D-01] → {W-02} ⊗ {I-03} :: [A-04] : {F-05} = {L-06} ([M-07]↑)"
    ),
    "cave": (
        "HEADER: Philosophy / Epistemology\n\n"
        "[Prisoner⥀{shadows}] :: [Turn] → [Γ_ascending] ⤳ {light}\n"
        ":: {sun} = [Φ] (Δ↑) ↛ {cave_knowledge}"
    ),
}


def _print_result(name: str, r: GpslValidation) -> None:
    status = "✓ VALID" if r.valid else "✗ INVALID"
    if r.has_warnings:
        status += " (with warnings)"
    print(f"\n{name}: {status}")
    print(f"  layers:    {sorted(r.layers_used)}")
    print(f"  operators: {sorted(r.operators_used)}")
    print(f"  nodes:     {r.nodes_found}")
    if r.errors:
        print(f"  ERRORS:")
        for e in r.errors:
            print(f"    - {e}")
    if r.warnings:
        print(f"  warnings:")
        for w in r.warnings:
            print(f"    - {w}")


# --- Phase 0-B synthetic test cases (one per rule, both pass and fail variants) ---
# Designed to prove the validator behaves correctly on the spec's actual rules.
# Two reviewers contributed to the rule mapping; rule 5 and rule 6 cases came
# from the second reviewer (using Gemini) on 2026-04-09.

@dataclass
class SyntheticCase:
    name: str
    cipher: str
    expected_valid: bool
    expected_warnings: bool  # True if we expect at least one warning
    rationale: str


SYNTHETIC_CASES: list[SyntheticCase] = [
    # --- Rule 5: derivational ops after :: ---
    SyntheticCase(
        name="rule5_pass_clean_boundary",
        cipher="[Agent-01] → {State-02} :: [Observation-03]",
        expected_valid=True,
        expected_warnings=False,
        rationale="No → or ⊗ after the ::. Clean derivational termination.",
    ),
    SyntheticCase(
        name="rule5_fail_strict_no_v_class",
        cipher="[Agent-01] → {State-02} :: [Observation-03] → {Conclusion-04}",
        expected_valid=False,
        expected_warnings=False,
        rationale="→ after :: with no advanced operators. Strict slash.",
    ),
    SyntheticCase(
        name="rule5_v_class_downgrade",
        cipher="[Agent⥀{candidates}] :: [Decide-01] → {Result-02}",
        expected_valid=True,
        expected_warnings=True,
        rationale="→ after :: BUT cipher contains ⥀ (advanced operator). V-class context downgrades to warning.",
    ),

    # --- Rule 7: state node limitations ---
    SyntheticCase(
        name="rule7_pass_process_to_state",
        cipher="[Process-01] → {State-02}",
        expected_valid=True,
        expected_warnings=False,
        rationale="Process initiates flow to state. Allowed.",
    ),
    SyntheticCase(
        name="rule7_fail_state_initiates_flow",
        cipher="{State-01} → [Process-02]",
        expected_valid=False,
        expected_warnings=False,
        rationale="State cannot actively cause a process. Type rule violation.",
    ),
    SyntheticCase(
        name="rule7_fail_state_loops",
        cipher="{State-01} ↺ {State-02}",
        expected_valid=False,
        expected_warnings=False,
        rationale="State cannot recur. Type rule violation.",
    ),

    # --- Rule 6: context promotion (open question — see validator note) ---
    SyntheticCase(
        name="rule6_pass_bracketed_fusion",
        cipher="[{Idea-01} ⊗ {Data-02}] → [Synthesis-03]",
        expected_valid=True,
        expected_warnings=False,
        rationale="State fusion wrapped in [...] context bracket. Clean.",
    ),
    SyntheticCase(
        name="rule6_warn_bare_fusion",
        cipher="{Idea-01} ⊗ {Data-02} = [Synthesis-03]",
        expected_valid=True,  # warning only in v0.1, pending D'Artagnan input
        expected_warnings=True,
        rationale=(
            "Bare {A} ⊗ {B} resolved with = (which is allowed after a state node, "
            "unlike → or ↺). Strict reading of rule 6 would slash; founding cipher "
            "uses the same bare-fusion pattern, so v0.1 treats as warning pending "
            "D'Artagnan clarification."
        ),
    ),

    # --- V-class escalation ---
    SyntheticCase(
        name="vclass_pass_with_warnings",
        cipher="[System-01] ⤳ ⦸ ↺ {∅}",
        expected_valid=True,
        expected_warnings=True,
        rationale="Two advanced operators (⤳ and ⦸) and a void terminator. Should pass with warnings on both.",
    ),
]


def _print_result(name: str, r: GpslValidation) -> None:
    status = "✓ VALID" if r.valid else "✗ INVALID"
    if r.has_warnings:
        status += " (with warnings)"
    print(f"\n{name}: {status}")
    print(f"  layers:    {sorted(r.layers_used)}")
    print(f"  operators: {sorted(r.operators_used)}")
    print(f"  nodes:     {r.nodes_found}")
    if r.errors:
        print(f"  ERRORS:")
        for e in r.errors:
            print(f"    - {e}")
    if r.warnings:
        print(f"  warnings:")
        for w in r.warnings:
            print(f"    - {w}")


def _smoke_test() -> int:
    """Run validator against canonical, negative, and synthetic cases. Returns 0 on success."""
    failures: list[str] = []

    print("=" * 72)
    print("GPSL Hybrid Validator — Smoke Test (Phase 0-B v0.2)")
    print("=" * 72)

    # === Section 1: canonical reference ciphers from v2.2 spec ===
    print("\n" + "=" * 72)
    print("SECTION 1 — Canonical reference ciphers (should all VALID)")
    print("=" * 72)
    expected_valid_canonical = ["founding", "cogito", "ecclesiastes", "grief", "cave"]
    for name in expected_valid_canonical:
        r = validate_gpsl_cipher(CANONICAL_CIPHERS[name])
        _print_result(name, r)
        if not r.valid:
            failures.append(f"canonical/{name} should be VALID but got INVALID: {r.errors}")

    # === Section 2: minimal negative cases ===
    print("\n" + "=" * 72)
    print("SECTION 2 — Minimal negative cases (should all INVALID)")
    print("=" * 72)
    bad_cases: dict[str, str] = {
        "empty": "",
        "no_nodes": "→ ⊗ :: ↔",
        "state_initiates_flow": "[A-01] → {B-02} → [C-03]",
        "state_recurs": "{A-01} ↺ {B-02}",
        "nl_contamination": "[the agent solves a difficult problem with care]",
    }
    for name, text in bad_cases.items():
        r = validate_gpsl_cipher(text)
        _print_result(name, r)
        if r.valid:
            failures.append(f"negative/{name} should be INVALID but got VALID")

    # === Section 3: Phase 0-B synthetic test cases ===
    print("\n" + "=" * 72)
    print("SECTION 3 — Phase 0-B synthetic test cases (one per rule, pass + fail)")
    print("=" * 72)
    for case in SYNTHETIC_CASES:
        r = validate_gpsl_cipher(case.cipher)
        _print_result(case.name, r)
        print(f"  rationale: {case.rationale}")
        # Check expected behavior
        if r.valid != case.expected_valid:
            failures.append(
                f"synthetic/{case.name}: expected valid={case.expected_valid}, "
                f"got valid={r.valid} (errors={r.errors})"
            )
        if r.has_warnings != case.expected_warnings:
            failures.append(
                f"synthetic/{case.name}: expected warnings={case.expected_warnings}, "
                f"got warnings={r.has_warnings} (warnings={r.warnings})"
            )

    # === Final verdict ===
    print("\n" + "=" * 72)
    if failures:
        print(f"SMOKE TEST FAILED — {len(failures)} mismatch(es):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("SMOKE TEST PASSED — all sections clean.")
    print(f"  Section 1: {len(expected_valid_canonical)} canonical ciphers VALID")
    print(f"  Section 2: {len(bad_cases)} negative cases correctly INVALID")
    print(f"  Section 3: {len(SYNTHETIC_CASES)} synthetic Phase 0-B cases match expected behavior")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_smoke_test())
