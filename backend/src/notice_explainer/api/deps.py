"""Shared singletons for the vertical slice.

Hexagonal: api -> application -> domain. Infrastructure selected by env:
  USE_FAKE_AI=true (default) -> Fake* adapters, zero keys, zero spend.
  USE_FAKE_AI=false + GEMINI_API_KEY set -> Gemini vision/reasoning.
  BHASHINI_API_KEY set -> Bhashini voice, else FakeVoiceService.
Tests force fake by leaving USE_FAKE_AI unset.
"""
from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException

from ..infrastructure.escalation import YamlEscalationEvaluator
from ..infrastructure.grounding import GroundedFieldExtractor
from ..infrastructure.legal_aid import JsonLegalAidDirectory
from ..infrastructure.twilio_whatsapp import FakeMessagingChannel
from ..infrastructure.fake_ai import (
    FakeClassifier,
    FakeExplanationGenerator,
    FakeFieldExtractor,
    FakeTextExtractor,
    FakeVoiceService,
)
from ..infrastructure.memory import (
    MemoryAuditLogger,
    MemoryImageStore,
    MemoryJobStore,
    MemoryReviewQueue,
)

review_queue = MemoryReviewQueue()

# Optional Postgres job/image stores (compose sets DATABASE_URL); memory otherwise.
# Mirrors the audit try/except pattern: tests keep working with no DATABASE_URL set.
if os.getenv("DATABASE_URL"):
    try:
        from ..infrastructure.postgres import PostgresImageStore, PostgresJobStore

        job_store = PostgresJobStore()  # type: ignore[assignment]
        image_store = PostgresImageStore()  # type: ignore[assignment]
    except Exception as exc:
        print(f"CRITICAL: Failed to connect to Postgres! DATABASE_URL is set but connection failed: {exc}")
        raise RuntimeError(f"Database connection failed: {exc}")
else:
    print("deps: DATABASE_URL unset — using memory job/image stores")
    job_store = MemoryJobStore()
    image_store = MemoryImageStore()

# Optional Postgres audit (compose sets DATABASE_URL); memory otherwise.
if os.getenv("DATABASE_URL"):
    try:
        from ..infrastructure.postgres import PostgresAuditLogger

        audit = PostgresAuditLogger()  # type: ignore[assignment]
    except Exception as exc:
        print(f"CRITICAL: Failed to connect to Postgres for audit log! {exc}")
        raise RuntimeError(f"Audit database connection failed: {exc}")
else:
    print("deps: DATABASE_URL unset — using memory audit")
    audit = MemoryAuditLogger()

# Optional Redis job queue; None -> FastAPI BackgroundTasks inline run.
try:
    if os.getenv("REDIS_URL"):
        from ..infrastructure.redis_queue import RedisJobQueue

        job_queue: RedisJobQueue | None = RedisJobQueue()
    else:
        job_queue = None
except Exception as exc:
    print(f"deps: inline job run fallback ({exc})")
    job_queue = None

USE_FAKE = os.getenv("USE_FAKE_AI", "true").lower() in ("1", "true", "yes")
AI_MODE = "fake"

if USE_FAKE or not os.getenv("GEMINI_API_KEY"):
    extractor = FakeTextExtractor()
    classifier = FakeClassifier()
    field_extractor = FakeFieldExtractor()
    explanation_gen = FakeExplanationGenerator()
else:
    from ..infrastructure.gemini import GeminiReasoner, GeminiVisionExtractor

    import httpx as _httpx

    def _is_quota_error(exc: BaseException) -> bool:
        if isinstance(exc, _httpx.HTTPStatusError) and exc.response is not None:
            return exc.response.status_code in (429, 503)
        msg = str(exc).lower()
        return ("429" in msg or "503" in msg or "quota" in msg
                or "high demand" in msg or "rate limit" in msg)

    class _ResilientExtractor:
        provider_name = "gemini-with-fake-fallback"

        def __init__(self, primary, fallback):
            self._p, self._f = primary, fallback

        def extract(self, image: bytes):
            try:
                return self._p.extract(image)
            except Exception as exc:
                if _is_quota_error(exc):
                    print(f"deps: gemini quota/overload, fake vision fallback ({type(exc).__name__})")
                    return self._f.extract(image)
                raise

    class _ResilientReasoner:
        model_version = "gemini-with-fake-fallback"
        prompt_version = "p-v1"

        def __init__(self, primary, c_fallback, f_fallback, g_fallback):
            self._p = primary
            self._cf, self._ff, self._gf = c_fallback, f_fallback, g_fallback

        def classify(self, text: str):
            try:
                return self._p.classify(text)
            except Exception as exc:
                if _is_quota_error(exc):
                    print(f"deps: gemini quota/overload, fake classify fallback ({type(exc).__name__})")
                    return self._cf.classify(text)
                raise

        def extract_fields(self, text: str, document_type):
            try:
                return self._p.extract_fields(text, document_type)
            except Exception as exc:
                if _is_quota_error(exc):
                    print(f"deps: gemini quota/overload, fake fields fallback ({type(exc).__name__})")
                    return self._ff.extract_fields(text, document_type)
                raise

        def generate(self, text: str, document_type, fields, target_language: str, escalated: bool):
            try:
                return self._p.generate(text, document_type, fields, target_language, escalated)
            except Exception as exc:
                if _is_quota_error(exc):
                    print(f"deps: gemini quota/overload, fake explanation fallback ({type(exc).__name__})")
                    return self._gf.generate(text, document_type, fields, target_language, escalated)
                raise

    _reasoner = GeminiReasoner()
    _fake_c, _fake_f, _fake_g = FakeClassifier(), FakeFieldExtractor(), FakeExplanationGenerator()
    extractor = _ResilientExtractor(GeminiVisionExtractor(), FakeTextExtractor())  # type: ignore[assignment]
    _resilient = _ResilientReasoner(_reasoner, _fake_c, _fake_f, _fake_g)
    classifier = _resilient  # type: ignore[assignment]
    field_extractor = _resilient  # type: ignore[assignment]
    explanation_gen = _resilient  # type: ignore[assignment]
    AI_MODE = "gemini"

# Grounding wrapper (pure re-score, no process_job.py change) for both modes.
field_extractor = GroundedFieldExtractor(field_extractor)  # type: ignore[assignment]

if os.getenv("BHASHINI_API_KEY") and not USE_FAKE:
    from ..infrastructure.bhashini import BhashiniVoiceService

    voice_service = BhashiniVoiceService()  # type: ignore[assignment]
    AI_MODE += "+bhashini"
else:
    voice_service = FakeVoiceService()
escalation_eval = YamlEscalationEvaluator()

# Free legal-aid directory (seed data only; states populated by maintainer).
try:
    legal_aid_dir = JsonLegalAidDirectory()
except Exception as exc:
    print(f"deps: legal-aid directory unavailable ({exc})")
    legal_aid_dir = None  # type: ignore[assignment]

# WhatsApp channel: Twilio only when fully configured, else fake recorder.
# Raw numbers are never logged or stored outside the ephemeral in-memory
# sender registry (see application/use_cases/whatsapp_flow.py).
try:
    if all([
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN"),
        os.getenv("TWILIO_WHATSAPP_FROM"),
        os.getenv("PUBLIC_BASE_URL"),
        os.getenv("WHATSAPP_HASH_SALT"),
    ]):
        from ..infrastructure.twilio_whatsapp import TwilioWhatsAppChannel

        messaging_channel = TwilioWhatsAppChannel()  # type: ignore[assignment]
    else:
        raise RuntimeError("WhatsApp env unset — fake channel")
except Exception as exc:
    print(f"deps: fake messaging channel fallback ({exc})")
    messaging_channel = FakeMessagingChannel()

def require_reviewer_key(
    x_reviewer_key: str | None = Header(default=None, alias="X-Reviewer-Key"),
) -> None:
    """Simple API-key guard for reviewer endpoints (stopgap until real login).

    Reads ``X-Reviewer-Key`` and compares (constant-time) to REVIEWER_API_KEY.
    When REVIEWER_API_KEY is unset, auth is disabled for local dev (main.py
    prints a REVIEWER AUTH DISABLED warning at startup).
    """
    expected = os.getenv("REVIEWER_API_KEY", "")
    if not expected:
        return
    if not x_reviewer_key or not hmac.compare_digest(x_reviewer_key, expected):
        raise HTTPException(status_code=401, detail="missing or invalid reviewer key")


# Q&A agent — lazy shape, only used when POST /{job_id}/ask is called.
# Fake (deterministic, no API) unless a real Gemini key is configured.
if USE_FAKE or not os.getenv("GEMINI_API_KEY"):
    from ..infrastructure.fake_ai import FakeQAAgent

    qa_agent = FakeQAAgent()
else:
    from ..infrastructure.qa_agent import QAAgent

    qa_agent = QAAgent()
