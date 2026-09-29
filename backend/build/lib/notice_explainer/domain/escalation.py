"""Deterministic escalation engine (LLD §2.5).

Pure logic: stdlib only, no model calls, no I/O. Evaluated TWICE per job —
once on raw extracted text, once on the generated explanation. Any match
sets escalate=True; severity is reviewer-triage metadata only.
"""
from __future__ import annotations

import re
import string

from .models import EscalationResult, EscalationRule
from .types import EscalationStage


def normalize(text: str) -> str:
    """Lowercase + strip punctuation, per LLD §2.5 pseudocode."""
    lowered = text.lower()
    return lowered.translate(str.maketrans("", "", string.punctuation))


def evaluate(
    text: str,
    stage: EscalationStage,
    rules: list[EscalationRule],
    rules_version: int = 0,
) -> EscalationResult:
    normalized = normalize(text)
    matched: list[str] = []
    for rule in rules:
        if re.search(rule.pattern, normalized):
            matched.append(rule.id)
    return EscalationResult(
        escalate=len(matched) > 0,
        matched_rule_ids=matched,
        stage=stage,
        rules_version=rules_version,
    )
