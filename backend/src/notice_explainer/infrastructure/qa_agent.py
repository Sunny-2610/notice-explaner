"""LangChain ReAct Q&A agent (ADR 0003, ADR 0004).

Sandboxed: 4 read-only tools, max 3 tool calls per question (call budget +
recursion_limit), deterministic out-of-scope refusal BEFORE any LLM call,
deterministic Sources list built only from retrieved chunks (never trusted
from the model), disclaimer appended to EVERY response, graceful fallback
that never fails the request. The agent has no escalation access whatsoever.
"""
from __future__ import annotations

import logging
import os

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)

from .agent_tools import (
    DISCLAIMERS,
    REFUSALS,
    is_out_of_scope,
    make_get_explanation_tool,
    make_glossary_tool,
    make_search_notice_tool,
)
from .corpus_tool import make_search_corpus_tool

SYSTEM_PROMPT = """
You are a helpful assistant for Yojana Mitra, an Indian government notice explainer.

You answer questions about a SPECIFIC notice the user has already uploaded.

RULES:
1. Only answer questions about this notice. If asked anything else, say:
   "मैं केवल इस नोटिस के बारे में सवालों का जवाब दे सकता हूँ। / I can only answer questions about this notice."
2. Never claim certainty about legal outcomes.
3. Never say "you don't need a lawyer."
4. Use the tools provided. Only claim what the notice, explanation,
   glossary, or corpus tools returned. If the corpus has nothing relevant,
   say so plainly instead of inventing an answer.
5. Respond in the user's target language (Hindi or Marathi).
6. End EVERY response with the disclaimer for the target language.

DISCLAIMERS:
- hi: "⚠️ यह कानूनी सलाह नहीं है। गंभीर मामलों में वकील से संपर्क करें।"
- mr: "⚠️ हा कायदेशीर सल्ला नाही. गंभीर प्रकरणांमध्ये वकिलाशी संपर्क साधा."
- en: "⚠️ This is not legal advice. Consult a lawyer for serious matters."
"""

FALLBACK = {
    "hi": "अभी जवाब नहीं दे सकता। कृपया बाद में प्रयास करें।",
    "mr": "आत्ता उत्तर देऊ शकत नाही. कृपया नंतर प्रयत्न करा.",
    "en": "I cannot answer right now. Please try again later.",
}

MAX_TOOL_CALLS = 3


class QAAgent:
    def __init__(self, retriever=None):
        self._llm = None
        self._retriever = retriever

    def _get_retriever(self):
        if self._retriever is None:
            from .retrieval import build_default_retriever

            self._retriever = build_default_retriever()
        return self._retriever

    def _get_llm(self):
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
                temperature=0.2,
                google_api_key=os.getenv("GEMINI_API_KEY"),
            )
        return self._llm

    def answer(self, notice_text, explanation, target_language, question) -> str:
        disclaimer = DISCLAIMERS.get(target_language, DISCLAIMERS["en"])

        # Deterministic refusal before any inference.
        if is_out_of_scope(question):
            return f"{REFUSALS.get(target_language, REFUSALS['en'])}\n\n{disclaimer}"

        try:
            budget: dict = {"used": 0, "max": MAX_TOOL_CALLS, "sources": []}
            tools = [
                make_search_notice_tool(notice_text, budget),
                make_get_explanation_tool(explanation, budget),
                make_glossary_tool(budget),
                make_search_corpus_tool(self._get_retriever(), budget),
            ]
            agent = create_agent(
                model=self._get_llm(),
                tools=tools,
                system_prompt=SYSTEM_PROMPT,
            )
            result = agent.invoke(
                {"messages": [("user", f"[{target_language}] {question}")]},
                config={"recursion_limit": 12},
            )
            answer = result["messages"][-1].content
            if not isinstance(answer, str):
                answer = str(answer)

            # Deterministic Sources list from retrieved chunks only — never
            # trust the model to cite. Placed BEFORE the disclaimer.
            sources = budget.get("sources", [])
            if sources:
                lines = ["Sources:"]
                for s in sources:
                    if s.get("source_url"):
                        lines.append(f"- {s['title']} ({s['source_url']})")
                    else:
                        lines.append(f"- {s['title']}")
                answer = answer.rstrip() + "\n\n" + "\n".join(lines)
            if disclaimer not in answer:
                answer = answer.rstrip() + f"\n\n{disclaimer}"
            return answer
        except Exception as exc:
            # Fallback: never fail the request (E-302 spirit). Log the error
            # type only — never the user question text.
            logger.warning("qa_agent failed: %s", type(exc).__name__)
            fb = FALLBACK.get(target_language, FALLBACK["en"])
            return f"{fb}\n\n{disclaimer}"
