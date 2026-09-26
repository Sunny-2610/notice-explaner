# Yojana Mitra — Notice Explainer

AI-assisted govt/legal notice explainer (PS-06 AI for Bharat). Photo upload → plain-language explanation in Hindi/Marathi + escalation flag. Repo is docs-only so far — no code, no toolchain; `docs/*.docx` (BRS, SRS, HLD, LLD v1.0 draft) are the source of truth.

## Safety invariants (from BRS/SRS/HLD/LLD — do not weaken)

- Escalation is pure deterministic logic, never LLM-only. `evaluate()` runs TWICE per job: on raw extracted text (pre-explanation) and on generated explanation (post-explanation). Any rule match → `escalate=true` (severity is triage-only). Default to escalation when uncertain — zero false negatives is the success metric.
- Every explanation ends with the not-legal-advice disclaimer (`disclaimerIncluded` always true); escalated outputs also recommend seeing a lawyer.
- System never files, responds to, pays, or resolves a notice; never claims certainty about legal outcomes.
- Every stage logs keyed by `job_id` to an append-only audit store (inputs/outputs, model+prompt versions, rule-config version, decisions).

## Pipeline order (HLD §4 / LLD §7)

upload + language select → gateway (auth, rate-limit, validate) → job queue (`jobId`) → extract → classify → field extract → escalation pre-check → generate explanation → escalation post-check → review queue if escalated/low-confidence → deliver. Stages are independently retryable; never reprocess prior successful stages.

## Verified thresholds and limits (LLD — these override any other numbers)

- Extraction confidence < 0.55 (or 3 retries with backoff base 500ms exhausted) → `awaiting_review`, reason `low_extraction_confidence`.
- Classification `unsupported` or confidence < 0.6 → short-circuit `not yet supported` (E-201), skip field extraction.
- Ingestion validation: image ≤ 10 MB, `image/jpeg`|`image/png` only, `targetLanguage` in supported list, else HTTP 400.
- Voice (ASR/TTS) failure or timeout > 8s → continue text-only with `voiceAvailable=false`; never fail the job.
- NFRs: < 15 s end-to-end (single page); free-tier only, zero paid API spend.

## Domain facts agents get wrong

- Supported types (closed enum): `property_tax_notice`, `traffic_challan_summons`, `bank_recovery_notice`, `unsupported`. Fields: issuingAuthority, deadlineDate (ISO-8601), amountOwed, citedSection, requiredAction + per-field confidence map.
- Launch languages: Hindi + Marathi only; new languages extend translation/voice config without touching reasoning or escalation.
- Escalation rules live in versioned `escalation_rules.yaml` (hot-reloadable, deployed without app redeploy); seed patterns: summons, arrest/warrant, recovery/auction/seizure, court.
- Privacy: raw images deleted immediately after processing (consent required to retain); audit keeps structured fields + document hash only.
- Intended layout is hexagonal: `domain/` (pure, no external deps) / `application/` (use cases + ports) / `infrastructure/` (Gemini-vision, Bhashini, Postgres, Redis adapters) / `api/`. Domain never imports infrastructure; infra implements ports. Stack is undecided where docs say "or": FastAPI vs Express, Redis vs managed queue, Postgres vs doc store — match whatever gets scaffolded first; keep provider abstraction so vision/reasoning and language/voice stay swappable.
