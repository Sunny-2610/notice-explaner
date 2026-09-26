"""LangChain ReAct Q&A agent (ADR 0003).

Sandboxed: 3 read-only tools, max 3 tool calls per question (call budget +
recursion_limit), deterministic out-of-scope refusal BEFORE any LLM call,
disclaimer appended to EVERY response, graceful fallback that never fails
the request. The agent has no escalation access whatsoever.
"""
from __future__ import annotations

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from .agent_tools import (
    DISCLAIMERS,
    REFUSALS,
    is_out_of_scope,
    make_get_explanation_tool,
    make_glossary_tool,
    make_search_notice_tool,
)

SYSTEM_PROMPT = """
You are a helpful assistant for Yojana Mitra, an Indian government notice explainer.

You answer questions about a SPECIFIC notice the user has already uploaded.

RULES:
1. Only answer questions about this notice. If asked anything else, say:
   "मैं केवल इस नोटिस के बारे में सवालों का जवाब दे सकता हूँ। / I can only answer questions about this notice."
2. Never claim certainty about legal outcomes.
3. Never say "you don't need a lawyer."
4. Use the tools provided. If you don't know, say so.
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
    def __init__(self):
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.2,
            )
        return self._llm

    def answer(self, notice_text, explanation, target_language, question) -> str:
        disclaimer = DISCLAIMERS.get(target_language, DISCLAIMERS["en"])

        # Deterministic refusal before any inference.
        if is_out_of_scope(question):
            return f"{REFUSALS.get(target_language, REFUSALS['en'])}\n\n{disclaimer}"

        try:
            budget = {"used": 0, "max": MAX_TOOL_CALLS}
            tools = [
                make_search_notice_tool(notice_text, budget),
                make_get_explanation_tool(explanation, budget),
                make_glossary_tool(budget),
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

            if disclaimer not in answer:
                answer = answer.rstrip() + f"\n\n{disclaimer}"
            return answer
        except Exception:
            # Fallback: never fail the request (E-302 spirit).
            fb = FALLBACK.get(target_language, FALLBACK["en"])
            return f"{fb}\n\n{disclaimer}"
