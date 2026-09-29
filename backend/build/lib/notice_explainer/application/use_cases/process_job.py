"""End-to-end job runner (LLD §5 pseudocode).

Stages are independently retryable: never reprocess a prior successful stage
on retry — each save_* is idempotent by job_id. Fake/real AI injected via ports.
"""
from __future__ import annotations

from ...domain.types import (
    CLASSIFICATION_CONFIDENCE_THRESHOLD,
    EXTRACTION_CONFIDENCE_THRESHOLD,
    DocumentType,
    ErrorCode,
    EscalationStage,
    JobStatus,
    ReviewReason,
)
from ..retry import run_with_retries


def process_job(
    job_id: str,
    *,
    job_store,
    image_store,
    review_queue,
    audit,
    extractor,
    classifier,
    field_extractor,
    explanation_gen,
    escalation_eval,
    voice_available: bool = True,
) -> None:
    job = job_store.get_job(job_id)
    if job is None:
        return
    image = image_store.fetch(job_id)

    # 1. Extraction (retryable, LLD §2.2)
    job_store.set_status(job_id, JobStatus.EXTRACTING)
    try:
        extraction = run_with_retries(lambda: extractor.extract(image or b""))
    except Exception as exc:  # E-301 retries exhausted
        job_store.set_status(job_id, JobStatus.FAILED, ErrorCode.AI_TIMEOUT.value)
        audit.log_stage(job_id, "extraction", {}, {"error": str(exc)[:300]})
        image_store.delete(job_id)
        return
    job_store.save_extraction(job_id, extraction)
    audit.log_stage(job_id, "extraction", {"bytes": len(image or b"")},
                    {"confidence": extraction.confidence, "provider": extraction.provider})
    if extraction.confidence < EXTRACTION_CONFIDENCE_THRESHOLD:
        job_store.set_status(job_id, JobStatus.AWAITING_REVIEW, ErrorCode.LOW_EXTRACTION.value)
        review_queue.enqueue(job_id, ReviewReason.LOW_EXTRACTION_CONFIDENCE)
        audit.log_stage(job_id, "review_route", {}, {"reason": "low_extraction_confidence"})
        return

    # 2. Classification (LLD §2.3) — short-circuit unsupported E-201
    job_store.set_status(job_id, JobStatus.CLASSIFYING)
    try:
        classification = run_with_retries(lambda: classifier.classify(extraction.text))
    except Exception as exc:
        job_store.set_status(job_id, JobStatus.FAILED, ErrorCode.AI_TIMEOUT.value)
        audit.log_stage(job_id, "classification", {}, {"error": str(exc)[:300]})
        image_store.delete(job_id)
        return
    job_store.save_classification(job_id, classification)
    audit.log_stage(job_id, "classification", {},
                    {"documentType": classification.document_type.value,
                     "confidence": classification.confidence})
    if (classification.document_type == DocumentType.UNSUPPORTED
            or classification.confidence < CLASSIFICATION_CONFIDENCE_THRESHOLD):
        job_store.set_status(job_id, JobStatus.AWAITING_REVIEW, ErrorCode.UNSUPPORTED_DOCUMENT.value)
        review_queue.enqueue(job_id, ReviewReason.UNSUPPORTED_DOCUMENT_TYPE)
        image_store.delete(job_id)
        return

    # 3. Field extraction (LLD §2.4)
    job_store.set_status(job_id, JobStatus.EXTRACTING_FIELDS)
    try:
        fields = run_with_retries(
            lambda: field_extractor.extract_fields(extraction.text, classification.document_type)
        )
    except Exception as exc:
        job_store.set_status(job_id, JobStatus.FAILED, ErrorCode.AI_TIMEOUT.value)
        audit.log_stage(job_id, "field_extraction", {}, {"error": str(exc)[:300]})
        image_store.delete(job_id)
        return
    job_store.save_fields(job_id, fields)
    audit.log_stage(job_id, "field_extraction", {}, {"fields": str(fields)[:500]})

    # 4. Escalation pre-check (deterministic, never LLM-only)
    job_store.set_status(job_id, JobStatus.CHECKING_ESCALATION)
    pre = escalation_eval.evaluate(extraction.text, EscalationStage.PRE_EXPLANATION)
    job_store.save_escalation(job_id, EscalationStage.PRE_EXPLANATION, pre)
    audit.log_stage(job_id, "escalation_pre", {},
                    {"escalate": pre.escalate, "rules": pre.matched_rule_ids,
                     "version": pre.rules_version})

    # 5. Explanation (LLD §2.6 — disclaimer always true)
    job_store.set_status(job_id, JobStatus.GENERATING_EXPLANATION)
    try:
        explanation = run_with_retries(
            lambda: explanation_gen.generate(
                extraction.text, classification.document_type, fields,
                job.target_language, pre.escalate)
        )
    except Exception as exc:
        job_store.set_status(job_id, JobStatus.FAILED, ErrorCode.AI_TIMEOUT.value)
        audit.log_stage(job_id, "explanation", {}, {"error": str(exc)[:300]})
        image_store.delete(job_id)
        return
    job_store.save_explanation(job_id, job.target_language, explanation)
    audit.log_stage(job_id, "explanation", {"escalated": pre.escalate},
                    {"disclaimer": explanation.disclaimer_included,
                     "voiceAvailable": voice_available})

    # 6. Escalation post-check on generated text
    post = escalation_eval.evaluate(explanation.explanation_text, EscalationStage.POST_EXPLANATION)
    job_store.save_escalation(job_id, EscalationStage.POST_EXPLANATION, post)
    audit.log_stage(job_id, "escalation_post", {},
                    {"escalate": post.escalate, "rules": post.matched_rule_ids,
                     "version": post.rules_version})

    if pre.escalate or post.escalate:
        job_store.set_status(job_id, JobStatus.AWAITING_REVIEW, ErrorCode.ESCALATION_SET.value)
        review_queue.enqueue(job_id, ReviewReason.ESCALATION_FLAG_SET)
        return  # keep image for reviewer context

    job_store.set_status(job_id, JobStatus.COMPLETED)
    image_store.delete(job_id)
