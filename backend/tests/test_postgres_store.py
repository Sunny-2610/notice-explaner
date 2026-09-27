"""Postgres-backed stores (Task 2). Skipped without DATABASE_URL so CI stays green."""
import os

import pytest

DATABASE_URL = os.getenv("DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL, reason="DATABASE_URL not set — Postgres tests skipped")

try:
    from notice_explainer.domain.models import (
        ClassificationResult,
        EscalationResult,
        ExplanationResult,
        ExtractedFields,
        ExtractionResult,
        Job,
    )
    from notice_explainer.domain.types import (
        DocumentType,
        EscalationStage,
        JobStatus,
    )
    from notice_explainer.infrastructure.postgres import (
        PostgresImageStore,
        PostgresJobStore,
    )
except Exception:  # psycopg missing -> skip at collection via fixture below
    PostgresJobStore = None  # type: ignore[assignment]


def _needs_psycopg():
    try:
        import psycopg  # noqa: F401
    except Exception:
        pytest.skip("psycopg not installed")


def test_job_round_trip_matches_memory_shape():
    _needs_psycopg()
    from notice_explainer.infrastructure.memory import MemoryJobStore

    store = PostgresJobStore()
    mem = MemoryJobStore()

    job = Job(job_id="pg-job-1", session_id="s1", target_language="hi")
    store.create_job(job)
    mem.create_job(Job(job_id="pg-job-1", session_id="s1", target_language="hi"))

    extraction = ExtractionResult(text="property tax notice", confidence=0.9,
                                  provider="test", duration_ms=5)
    classification = ClassificationResult(document_type=DocumentType.PROPERTY_TAX_NOTICE,
                                          confidence=0.9)
    fields = ExtractedFields(issuing_authority="Nagar Nigam", deadline_date="2026-11-15",
                             amount_owed=4500.0, cited_section="Sec 12",
                             required_action="Pay by deadline",
                             field_confidence={"amountOwed": 0.9})
    pre = EscalationResult(escalate=False, matched_rule_ids=[],
                           stage=EscalationStage.PRE_EXPLANATION, rules_version=1)
    explanation = ExplanationResult(explanation_text="plain text",
                                    disclaimer_included=True,
                                    escalation_notice_included=False)
    post = EscalationResult(escalate=False, matched_rule_ids=[],
                            stage=EscalationStage.POST_EXPLANATION, rules_version=1)

    for target in (store, mem):
        target.save_extraction("pg-job-1", extraction)
        target.save_classification("pg-job-1", classification)
        target.save_fields("pg-job-1", fields)
        target.save_escalation("pg-job-1", EscalationStage.PRE_EXPLANATION, pre)
        target.save_explanation("pg-job-1", "hi", explanation)
        target.save_escalation("pg-job-1", EscalationStage.POST_EXPLANATION, post)
        target.set_status("pg-job-1", JobStatus.COMPLETED)

    got = store.get_result("pg-job-1")
    expected = mem.get_result("pg-job-1")
    assert got == expected
    assert got["jobId"] == "pg-job-1"
    assert got["status"] == "completed"
    assert got["fields"]["amountOwed"] == 4500.0

    # Compat shims used by application/api layers.
    assert store.get_extraction("pg-job-1").text == "property tax notice"
    assert "pg-job-1" in store.explanations
    assert store.update_explanation_text("pg-job-1", "edited") is True
    assert store.get_result("pg-job-1")["explanation"] == "edited"


def test_image_put_fetch_delete():
    _needs_psycopg()
    images = PostgresImageStore()
    images.put("pg-img-1", b"raw-bytes")
    assert images.fetch("pg-img-1") == b"raw-bytes"
    images.delete("pg-img-1")
    assert images.fetch("pg-img-1") is None
