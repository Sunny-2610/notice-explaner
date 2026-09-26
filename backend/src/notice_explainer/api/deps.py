"""Shared singletons for the vertical slice.

Hexagonal: api -> application -> domain. Infrastructure selected by env:
  USE_FAKE_AI=true (default) -> Fake* adapters, zero keys, zero spend.
  USE_FAKE_AI=false + GEMINI_API_KEY set -> Gemini vision/reasoning.
  BHASHINI_API_KEY set -> Bhashini voice, else FakeVoiceService.
Tests force fake by leaving USE_FAKE_AI unset.
"""
from __future__ import annotations

import os

from ..infrastructure.escalation import YamlEscalationEvaluator
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

job_store = MemoryJobStore()
image_store = MemoryImageStore()
review_queue = MemoryReviewQueue()
audit = MemoryAuditLogger()

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

if os.getenv("BHASHINI_API_KEY") and not USE_FAKE:
    from ..infrastructure.bhashini import BhashiniVoiceService

    voice_service = BhashiniVoiceService()  # type: ignore[assignment]
    AI_MODE += "+bhashini"
else:
    voice_service = FakeVoiceService()
escalation_eval = YamlEscalationEvaluator()
