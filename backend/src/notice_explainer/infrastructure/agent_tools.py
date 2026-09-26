"""Bounded read-only tools for the follow-up Q&A agent (ADR 0003).

Three tools only: search_notice (BM25-style keyword search over the extracted
notice text), get_explanation (returns the already-generated explanation),
lookup_glossary (hardcoded legal-term dictionary).

The agent has NO tool that can read or change escalation state.
"""
from __future__ import annotations

import re

from langchain.tools import tool

GLOSSARY = {
    "summons": "A legal document ordering you to appear in court on a specific date.",
    "warrant": "A legal order authorizing arrest or search.",
    "recovery": "The process of recovering unpaid debts, often through asset seizure.",
    "court": "A government institution where legal disputes are resolved.",
    "ipc": "Indian Penal Code — the main criminal code of India.",
    "section": "A numbered provision within a legal act.",
    "suman": "समन — अदालत का आदेश जो आपको तय तारीख पर पेश होने के लिए कहता है।",
    "vaarant": "वारंट — गिरफ्तारी या तलाशी का कानूनी आदेश।",
}

# Deterministic off-topic markers — checked BEFORE any LLM call so
# out-of-scope questions are refused without spending inference.
OUT_OF_SCOPE_MARKERS = (
    "weather", "cricket", "football", "movie", "song", "recipe", "joke",
    "capital", "prime minister", "election", "stock", "cricket",
    "मौसम", "क्रिकेट", "फिल्म", "गाना", "रेसिपी", "मजाक",
    "हवामान", "क्रिकेट", "चित्रपट", "गाणे",
)

REFUSALS = {
    "hi": "मैं केवल इस नोटिस के बारे में सवालों का जवाब दे सकता हूँ।",
    "mr": "मी फक्त या नोटिसबद्दल प्रश्नांची उत्तरे देऊ शकतो.",
    "en": "I can only answer questions about this notice.",
}

DISCLAIMERS = {
    "hi": "⚠️ यह कानूनी सलाह नहीं है। गंभीर मामलों में वकील से संपर्क करें।",
    "mr": "⚠️ हा कायदेशीर सल्ला नाही. गंभीर प्रकरणांमध्ये वकिलाशी संपर्क साधा.",
    "en": "⚠️ This is not legal advice. Consult a lawyer for serious matters.",
}


def is_out_of_scope(question: str) -> bool:
    q = question.lower()
    return any(m in q for m in OUT_OF_SCOPE_MARKERS)


def _take_budget(budget: dict | None) -> bool:
    """Consume one tool call. Returns False when the 3-call budget is spent."""
    if budget is None:
        return True
    if budget["used"] >= budget["max"]:
        return False
    budget["used"] += 1
    return True


def make_search_notice_tool(notice_text: str, budget: dict | None = None):
    """BM25-style keyword search over the extracted notice text."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?।])\s+", notice_text) if s.strip()]

    @tool
    def search_notice(query: str) -> str:
        """Search the extracted notice text for passages relevant to the query.
        Use this when the user asks about specific details like amounts, dates, or authorities."""
        if not _take_budget(budget):
            return "Tool budget exhausted — answer from context gathered so far."
        if not sentences:
            return "No relevant passage found."
        q_words = set(re.findall(r"\w+", query.lower()))
        scored = []
        for s in sentences:
            s_words = set(re.findall(r"\w+", s.lower()))
            overlap = len(q_words & s_words)
            if overlap:
                scored.append((overlap, s))
        scored.sort(key=lambda t: t[0], reverse=True)
        if not scored:
            return "No relevant passage found."
        return "\n".join(s for _, s in scored[:3])

    return search_notice


def make_get_explanation_tool(explanation: str, budget: dict | None = None):
    """Returns the already-generated explanation."""

    @tool
    def get_explanation() -> str:
        """Get the plain-language explanation that was already generated for this notice.
        Use this when the user asks 'what does this mean?' or 'explain again'."""
        if not _take_budget(budget):
            return "Tool budget exhausted — answer from context gathered so far."
        return explanation

    return get_explanation


def make_glossary_tool(budget: dict | None = None):
    """Glossary lookup bound to the same call budget."""

    @tool
    def lookup_glossary_bound(term: str) -> str:
        """Look up a legal term in the glossary. Use this when the user asks about a specific
        legal term like 'summons', 'warrant', 'recovery', 'IPC', 'section'."""
        if not _take_budget(budget):
            return "Tool budget exhausted — answer from context gathered so far."
        return GLOSSARY.get(term.lower(), f"'{term}' glossary में नहीं मिला। / not found in glossary.")

    return lookup_glossary_bound


@tool
def lookup_glossary(term: str) -> str:
    """Look up a legal term in the glossary. Use this when the user asks about a specific
    legal term like 'summons', 'warrant', 'recovery', 'IPC', 'section'."""
    return GLOSSARY.get(term.lower(), f"'{term}' glossary में नहीं मिला। / not found in glossary.")
