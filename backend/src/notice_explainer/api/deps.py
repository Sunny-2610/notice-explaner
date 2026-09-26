"""Shared singletons for the vertical slice.

Real Postgres/Redis/Gemini clients replace these in deps without
changing routers or use cases (hexagonal: api -> application -> domain).
"""
from __future__ import annotations

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

extractor = FakeTextExtractor()
classifier = FakeClassifier()
field_extractor = FakeFieldExtractor()
explanation_gen = FakeExplanationGenerator()
voice_service = FakeVoiceService()
escalation_eval = YamlEscalationEvaluator()
