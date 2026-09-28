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
try:
    if os.getenv("DATABASE_URL"):
        from ..infrastructure.postgres import PostgresImageStore, PostgresJobStore

        job_store = PostgresJobStore()  # type: ignore[assignment]
        image_store = PostgresImageStore()  # type: ignore[assignment]
    else:
        raise RuntimeError("DATABASE_URL unset — memory job/image stores")
except Exception as exc:
    print(f"deps: memory job/image store fallback ({exc})")
    job_store = MemoryJobStore()
    image_store = MemoryImageStore()

# Optional Postgres audit (compose sets DATABASE_URL); memory otherwise.
try:
    if os.getenv("DATABASE_URL"):
        from ..infrastructure.postgres import PostgresAuditLogger

        audit = PostgresAuditLogger()  # type: ignore[assignment]
    else:
        raise RuntimeError("DATABASE_URL unset — memory audit")
except Exception as exc:
    print(f"deps: memory audit fallback ({exc})")
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

    _reasoner = GeminiReasoner()
    extractor = GeminiVisionExtractor()  # type: ignore[assignment]
    classifier = _reasoner  # type: ignore[assignment]
    field_extractor = _reasoner  # type: ignore[assignment]
    explanation_gen = _reasoner  # type: ignore[assignment]
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
