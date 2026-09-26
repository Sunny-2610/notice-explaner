"""Explanation prompt template + disclaimer copy (LLD §2.6.1).

Disclaimer wording is scaffold placeholder copy — MUST pass legal review
before any pilot beyond demo scope (SRS §8.2).
"""
from __future__ import annotations

SYSTEM_PROMPT_TEMPLATE = """You explain government/legal notices in plain,
everyday {target_language}. You are not a lawyer
and must never claim certainty about legal outcomes.
Always end with: '{disclaimer_text}'"""

DISCLAIMER_TEXT = {
    "en": "This is not legal advice. If this matter looks serious, please consult a lawyer.",
    "hi": "यह कानूनी सलाह नहीं है। यदि मामला गंभीर लगे तो कृपया किसी वकील से सलाह लें।",
    "mr": "हा कायदेशीर सल्ला नाही. प्रकरण गंभीर वाटल्यास कृपया वकिलाचा सल्ला घ्या.",
}

ESCALATION_NOTICE = {
    "en": "This notice looks serious. Please see a lawyer soon.",
    "hi": "यह नोटिस गंभीर लग रहा है। कृपया जल्द किसी वकील से मिलें।",
    "mr": "ही नोटीस गंभीर वाटते. कृपया लवकरच वकिलाला भेटा.",
}


def render_system_prompt(target_language: str) -> tuple[str, str]:
    disclaimer = DISCLAIMER_TEXT.get(target_language, DISCLAIMER_TEXT["en"])
    return (
        SYSTEM_PROMPT_TEMPLATE.format(
            target_language=target_language, disclaimer_text=disclaimer
        ),
        disclaimer,
    )
