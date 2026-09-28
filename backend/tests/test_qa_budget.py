"""Q&A tool-budget proof with a fake LLM/agent (no langchain import).

Stubs the langchain modules in sys.modules before importing qa_agent, so
this test also proves fake mode never needs the real LangChain package.
"""
import sys
import types

from notice_explainer.infrastructure.agent_tools import DISCLAIMERS

_BUDGET_MSG = "Tool budget exhausted — answer from context gathered so far."


class _DummyRetriever:
    """Corpus stub: one chunk per query so the Sources path is exercised."""

    def search(self, query: str, top_k: int = 3):
        from notice_explainer.domain.models import CorpusChunk

        return [CorpusChunk(id="t1", title="Test Chunk", lang="en", text="body")]


def _install_langchain_stubs(monkeypatch):
    def tool_deco(fn=None, **kwargs):
        if callable(fn):
            return fn

        def wrap(f):
            return f

        return wrap

    lc = types.ModuleType("langchain")
    tools_mod = types.ModuleType("langchain.tools")
    tools_mod.tool = tool_deco
    agents_mod = types.ModuleType("langchain.agents")

    def _placeholder_create_agent(*args, **kwargs):
        raise RuntimeError("create_agent stub not configured")

    agents_mod.create_agent = _placeholder_create_agent
    genai_mod = types.ModuleType("langchain_google_genai")
    genai_mod.ChatGoogleGenerativeAI = type("ChatGoogleGenerativeAI", (), {})
    monkeypatch.setitem(sys.modules, "langchain", lc)
    monkeypatch.setitem(sys.modules, "langchain.tools", tools_mod)
    monkeypatch.setitem(sys.modules, "langchain.agents", agents_mod)
    monkeypatch.setitem(sys.modules, "langchain_google_genai", genai_mod)
    return agents_mod


def _fresh_qa_agent(monkeypatch):
    """Import qa_agent against the stubs (restoring real modules after)."""
    stashed = {}
    for name in (
        "notice_explainer.infrastructure.agent_tools",
        "notice_explainer.infrastructure.qa_agent",
    ):
        if name in sys.modules:
            stashed[name] = sys.modules.pop(name)
    agents_mod = _install_langchain_stubs(monkeypatch)
    try:
        import notice_explainer.infrastructure.qa_agent as qa_mod

        importlib_reload = __import__("importlib").reload
        importlib_reload(qa_mod)
        return qa_mod, agents_mod
    finally:
        sys.modules.pop("notice_explainer.infrastructure.qa_agent", None)
        sys.modules.pop("notice_explainer.infrastructure.agent_tools", None)
        sys.modules.update(stashed)


def test_three_tool_call_budget_stops_further_use(monkeypatch):
    qa_mod, agents_mod = _fresh_qa_agent(monkeypatch)
    seen_tools: list = []
    results: list[str] = []

    class _Msg:
        content = "final answer without disclaimer"

    class _FakeAgent:
        def invoke(self, *args, **kwargs):
            search = next(
                t for t in seen_tools if getattr(t, "__name__", "") == "search_notice"
            )
            for i in range(5):
                if hasattr(search, "invoke"):
                    results.append(search.invoke(f"question {i}"))
                else:
                    results.append(search(f"question {i}"))
            return {"messages": [_Msg()]}

    def _capture(kwargs):
        seen_tools.extend(kwargs.get("tools", []))
        return None

    def _factory(**kwargs):
        _capture(kwargs)
        return _FakeAgent()

    monkeypatch.setattr(qa_mod, "create_agent", _factory)
    agent = qa_mod.QAAgent(retriever=_DummyRetriever())
    monkeypatch.setattr(agent, "_get_llm", lambda: object())
    answer = agent.answer(
        notice_text="Amount Rs 4500. Due 2026-11-15.",
        explanation="Property tax notice.",
        target_language="hi",
        question="रकम कितनी है?",
    )
    assert len(seen_tools) == 4
    assert len(results) == 5
    assert all(isinstance(r, str) for r in results)
    # First 3 calls served; calls 4-5 refused by the shared budget.
    assert results[3] == _BUDGET_MSG
    assert results[4] == _BUDGET_MSG
    # Disclaimer always appended, even when the model omits it.
    assert answer.rstrip().endswith(DISCLAIMERS["hi"])
    # Deterministic Sources list is absent here (fake agent never called
    # the corpus tool) — covered in test_corpus.py.


def test_agent_exception_still_returns_disclaimer(monkeypatch, caplog):
    qa_mod, agents_mod = _fresh_qa_agent(monkeypatch)

    def _boom(**kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(qa_mod, "create_agent", _boom)
    agent = qa_mod.QAAgent()
    monkeypatch.setattr(agent, "_get_llm", lambda: object())
    with caplog.at_level("WARNING"):
        answer = agent.answer(
            notice_text="text",
            explanation="expl",
            target_language="mr",
            question="काय आहे?",
        )
    assert answer.rstrip().endswith(DISCLAIMERS["mr"])
    assert any("qa_agent failed" in r.message for r in caplog.records)
