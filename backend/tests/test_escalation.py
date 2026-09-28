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


def _real_evaluator():
    from notice_explainer.infrastructure.escalation import YamlEscalationEvaluator

    return YamlEscalationEvaluator()


def test_yaml_v4_hindi_summons_escalates():
    ev = _real_evaluator()
    assert ev.version == 4
    r = ev.evaluate(
        "न्यायालय समन: आपको निर्धारित तारीख पर उपस्थित होना है।",
        EscalationStage.PRE_EXPLANATION,
    )
    assert r.escalate is True
    assert r.rules_version == 4


def test_yaml_v4_hindi_recovery_auction_escalates():
    ev = _real_evaluator()
    r = ev.evaluate(
        "बकाया वसूली हेतु कुर्की और नीलामी की कार्रवाई की जाएगी।",
        EscalationStage.PRE_EXPLANATION,
    )
    assert r.escalate is True
    assert r.rules_version == 4


def test_yaml_v4_marathi_warrant_escalates():
    ev = _real_evaluator()
    r = ev.evaluate(
        "न्यायालयाने तुमच्याविरुद्ध वॉरंट जारी केले आहे.",
        EscalationStage.PRE_EXPLANATION,
    )
    assert r.escalate is True
    assert r.rules_version == 4


def test_yaml_v4_marathi_seizure_escalates():
    ev = _real_evaluator()
    r = ev.evaluate(
        "थकबाकी वसुलीसाठी मालमत्तेची जप्ती करण्यात येईल.",
        EscalationStage.PRE_EXPLANATION,
    )
    assert r.escalate is True
    assert r.rules_version == 4


def test_yaml_v4_fake_property_tax_does_not_escalate():
    ev = _real_evaluator()
    r = ev.evaluate(
        "MUNICIPAL CORPORATION property tax demand notice. "
        "Amount Rs 4500. Due 2026-11-15 under Section 12A. "
        "Pay at ward office within 30 days.",
        EscalationStage.PRE_EXPLANATION,
    )
    assert r.escalate is False and r.matched_rule_ids == []
    assert r.rules_version == 4
