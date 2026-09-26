"""Unit: deterministic escalation — any match escalates, severity never suppresses."""
from notice_explainer.domain.escalation import evaluate
from notice_explainer.domain.models import EscalationRule
from notice_explainer.domain.types import EscalationStage

RULES = [
    EscalationRule(id="R-001", pattern=r"\bsummons\b", severity="high"),
    EscalationRule(id="R-002", pattern=r"\barrest\b|\bwarrant\b", severity="high"),
    EscalationRule(id="R-004", pattern=r"\bcourt\b", severity="medium"),
]


def test_no_match_no_escalation():
    r = evaluate("property tax due soon", EscalationStage.PRE_EXPLANATION, RULES, 3)
    assert r.escalate is False and r.matched_rule_ids == [] and r.rules_version == 3


def test_medium_severity_still_escalates():
    r = evaluate("please visit the court office", EscalationStage.POST_EXPLANATION, RULES, 3)
    assert r.escalate is True and r.matched_rule_ids == ["R-004"]


def test_normalize_strips_punctuation_case():
    r = evaluate("SUMMONS, issued!", EscalationStage.PRE_EXPLANATION, RULES, 3)
    assert r.escalate is True and "R-001" in r.matched_rule_ids
