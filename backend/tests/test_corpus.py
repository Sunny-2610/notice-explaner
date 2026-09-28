"""Legal-corpus RAG: review gate, ranking, deterministic sources, budget."""
import sys

from notice_explainer.domain.models import CorpusChunk
from notice_explainer.infrastructure import qa_agent as qa_mod
from notice_explainer.infrastructure.agent_tools import DISCLAIMERS
from notice_explainer.infrastructure.retrieval import KeywordRetriever, load_corpus


def test_review_gate_excludes_unreviewed_by_default(monkeypatch):
    monkeypatch.delenv("CORPUS_ALLOW_UNREVIEWED", raising=False)
    active, gated = load_corpus()
    assert len(active) == 0
    assert len(gated) == 18


def test_review_gate_flag_includes_unreviewed(monkeypatch):
    monkeypatch.setenv("CORPUS_ALLOW_UNREVIEWED", "true")
    active, gated = load_corpus()
    assert len(active) == 18
    assert gated == []


def test_keyword_ranking_hindi_query(monkeypatch):
    monkeypatch.setenv("CORPUS_ALLOW_UNREVIEWED", "true")
    retriever = KeywordRetriever()
    top = retriever.search("ई-चालान का भुगतान कैसे करें?", top_k=3)
    assert top, "expected corpus hits for a Hindi how-to query"
    assert top[0].id == "echallan-pay-hi"


def test_keyword_ranking_english_query(monkeypatch):
    monkeypatch.setenv("CORPUS_ALLOW_UNREVIEWED", "true")
    retriever = KeywordRetriever()
    top = retriever.search("where can I get free legal aid helpline?", top_k=3)
    assert top and top[0].id == "free-legal-aid-en"


def _chunks():
    return [
        CorpusChunk(id="c1", title="Pay Guide", lang="en",
                    text="Pay at the counter named on the notice.",
                    source_url="https://nalsa.gov.in"),
        CorpusChunk(id="c2", title="Keep Papers", lang="en", text="Keep receipts."),
    ]


def test_sources_appended_only_from_retrieved_chunks(monkeypatch):
    """Fake agent calls the corpus tool; Sources list is deterministic."""
    retriever = KeywordRetriever(chunks=_chunks())
    seen: list = []

    class _Msg:
        content = "pay at the counter"

    class _FakeAgent:
        def invoke(self, *args, **kwargs):
            corpus = next(
                t for t in seen
                if getattr(t, "name", getattr(t, "__name__", "")) == "search_corpus"
            )
            if hasattr(corpus, "invoke"):
                corpus.invoke("how to pay and keep papers?")
            else:
                corpus("how to pay and keep papers?")
            return {"messages": [_Msg()]}

    def _factory(**kwargs):
        seen.extend(kwargs.get("tools", []))
        return _FakeAgent()

    monkeypatch.setattr(qa_mod, "create_agent", _factory)
    agent = qa_mod.QAAgent(retriever=retriever)
    monkeypatch.setattr(agent, "_get_llm", lambda: object())
    answer = agent.answer(
        notice_text="challan paper",
        explanation="challan explanation",
        target_language="en",
        question="How do I pay this?",
    )
    assert len(seen) == 4
    assert "- Pay Guide (https://nalsa.gov.in)" in answer
    assert "- Keep Papers" in answer
    # Sources come before the final disclaimer, never after it.
    assert answer.index("Sources:") < answer.rindex(DISCLAIMERS["en"])
    assert answer.rstrip().endswith(DISCLAIMERS["en"])


def test_corpus_tool_shares_call_budget():
    from notice_explainer.infrastructure.corpus_tool import make_search_corpus_tool

    retriever = KeywordRetriever(chunks=_chunks())
    budget: dict = {"used": 3, "max": 3, "sources": []}
    tool = make_search_corpus_tool(retriever, budget)
    out = tool.invoke("how to pay?") if hasattr(tool, "invoke") else tool("how to pay?")
    assert out.startswith("Tool budget exhausted")
    assert budget["sources"] == []


def test_empty_corpus_says_so_plainly():
    retriever = KeywordRetriever(chunks=[])
    assert retriever.search("anything", top_k=3) == []


def test_no_escalation_access_in_qa_agent():
    """The agent has no escalation tool, import, or evaluator reference."""
    src = sys.modules["notice_explainer.infrastructure.qa_agent"].__file__
    assert src is not None
    text = open(src, encoding="utf-8").read()
    assert "import escalation" not in text
    assert "escalation_eval" not in text
    assert "EscalationEvaluator" not in text
    assert "make_escalation" not in text.lower()
