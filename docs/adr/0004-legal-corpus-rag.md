# ADR 0004: Legal-Corpus RAG as a 4th Q&A Tool

Status: accepted (supersedes the "3 tools" wording of ADR 0003)

## Context

The sandboxed Q&A agent (ADR 0003) could only quote the notice, the stored
explanation, and a hardcoded glossary. Users also ask general how-to
questions ("How do I pay an e-challan?", "What does a recovery notice
mean?") that the notice text alone cannot answer. The fix must add
knowledge without touching escalation, the pipeline, or the 3-calls-per-
question safety budget.

## Decision

Add `search_corpus` as a 4th read-only tool, wired hexagonally:

```
application/ports.py LegalRetriever (port)
  -> infrastructure/retrieval.py (KeywordRetriever default/offline,
     GeminiEmbeddingRetriever when a Gemini key is set)
  -> infrastructure/corpus_tool.py make_search_corpus_tool(retriever, budget)
  -> infrastructure/qa_agent.py (registers it alongside the other 3)
```

- Corpus: 15–25 short plain-language markdown chunks in
  `backend/data/corpus/*.md` with frontmatter
  (`id, title, lang, source_url?, reviewed: false`). No section numbers,
  no unverified URLs or phone numbers; everything ships `reviewed: false`.
- Review gate: `reviewed:false` chunks are excluded unless
  `CORPUS_ALLOW_UNREVIEWED=true` (default false). Active vs gated counts
  are logged at load.
- The corpus tool shares the existing per-question call budget, so the
  "max 3 tool calls per question" invariant is unchanged (now 4 tools
  compete for the same 3 calls). Each call records its chunks into
  `budget["sources"]`.
- After the answer, qa_agent appends a deterministic `Sources:` list built
  ONLY from `budget["sources"]` (title + source_url when present), placed
  BEFORE the disclaimer. The model is never trusted to cite.
- System prompt: only claim what the tools returned; say so if the corpus
  has nothing relevant.

## Safety

- Agent still has no escalation tool — it cannot read or modify the flag
  (existing identity test keeps passing).
- Sources are deterministic code output, not model text — a model cannot
  invent citations.
- Gated-by-default corpus means unreviewed prose never reaches users until
  a maintainer flips the flag.
- `domain/` stays pure (CorpusChunk is a plain dataclass); `domain/` and
  `application/` never import LangChain.

## Consequences

- ADR 0003's "Three tools only" becomes "four read-only tools, still max
  3 calls/question". AGENTS.md updated accordingly.
- New env: `CORPUS_ALLOW_UNREVIEWED` (default false), `GEMINI_EMBED_MODEL`
  (default gemini-embedding-001). Embedding cache lives in
  `backend/.cache/` (gitignored).
- Real-agent path still activates only with `GEMINI_API_KEY` +
  `USE_FAKE_AI=false`; default remains keyword retrieval, zero spend.
