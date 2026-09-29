"""4th Q&A tool: plain-language legal-corpus search (ADR 0004).

Shares the existing 3-call budget; every returned chunk is recorded into
budget["sources"] so qa_agent can append a deterministic Sources list
(title + source_url) that never trusts the model to cite.
"""
from __future__ import annotations

from langchain.tools import tool

from .agent_tools import _take_budget


def make_search_corpus_tool(retriever, budget: dict | None = None):
    """Corpus search bound to the shared per-question call budget."""

    @tool
    def search_corpus(query: str) -> str:
        """Search the plain-language legal guide corpus for how-to passages
        (paying challans, notice contents, asking for more time, legal aid).
        Use this when the user asks a general how-to question."""
        if not _take_budget(budget):
            return "Tool budget exhausted — answer from context gathered so far."
        try:
            chunks = retriever.search(query, top_k=3)
        except Exception:
            return "Corpus unavailable — answer from notice and explanation."
        if not chunks:
            return "No relevant corpus passage found."
        if budget is not None:
            sources = budget.setdefault("sources", [])
            for c in chunks:
                if all(s.get("title") != c.title for s in sources):
                    sources.append({"title": c.title, "source_url": c.source_url})
        return "\n\n".join(f"[{c.title}]\n{c.text}" for c in chunks)

    return search_corpus
