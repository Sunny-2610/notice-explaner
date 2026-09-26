# ADR 0003: Follow-Up Q&A via Sandboxed LangChain ReAct Agent

Status: accepted

## Context

After receiving a plain-language explanation, users ask follow-up questions
("What happens if I ignore this?", "Where do I pay?", "What does 'summons' mean?").
The core pipeline (`process_job.py`) is frozen and escalation is pure
deterministic logic — the Q&A feature must add interactivity without touching
either.

## Decision

Add `POST /api/v1/documents/{job_id}/ask`, wired hexagonally:

```
api/documents.py POST /{job_id}/ask
  → application/use_cases/answer_question.py (orchestration, no LangChain imports)
    → infrastructure/qa_agent.py (LangChain create_agent, v1.x API)
      → infrastructure/agent_tools.py (3 read-only tools)
```

- Tools: `search_notice` (keyword-overlap sentence search over extracted text),
  `get_explanation` (returns the stored explanation), `lookup_glossary`
  (hardcoded EN/HI/MR legal-term dictionary).
- Max 3 tool calls per question (shared call budget + `recursion_limit: 12`).
- Max 10 questions per job (counted from the `qa_ask` audit trail).
- Deterministic out-of-scope refusal runs BEFORE any LLM call.
- Disclaimer appended to EVERY answer; graceful fallback never fails the request.
- Tests use `FakeQAAgent` — zero API calls in CI.

## Alternatives considered

- **LangGraph multi-turn state:** rejected — one-shot Q&A needs no conversation
  memory; each question is independently answerable from notice + explanation.
- **Vector DB (Chroma/Pinecone):** rejected — single-document retrieval over a
  few sentences; keyword overlap is sufficient, free, and dependency-light.
- **Raw Gemini prompt without tools:** rejected — unbounded; tools constrain
  the agent to notice text, stored explanation, and glossary only.

## Safety

- `domain/escalation.py` and `process_job.py` untouched (verified by test +
  code review; escalation test asserts flag identity before/after Q&A).
- Agent has no escalation tool — it cannot read or modify the flag.
- System prompt forbids certainty about legal outcomes and forbids saying
  "you don't need a lawyer."
- Every `/ask` call logs a `qa_ask` audit stage keyed by `job_id`.

## Consequences

- Interactive UX via `FollowUpQA.tsx` (suggested-question chips + free input).
- New runtime deps: `langchain>=0.3`, `langchain-google-genai>=2.0`.
- Real-agent path activates only with `GEMINI_API_KEY` + `USE_FAKE_AI=false`;
  default remains fake (zero spend).
