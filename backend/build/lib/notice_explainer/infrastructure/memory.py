"""In-memory adapters for vertical slice (LLD §3).

Postgres/Redis replace these later without touching domain/application —
they implement the same ports. Thread-safe enough for demo via a lock.
"""
from __future__ import annotations

import threading
from collections import defaultdict

from ..domain.models import (
    AuditEntry,
    ClassificationResult,
    EscalationResult,
    ExplanationResult,
    ExtractedFields,
    ExtractionResult,
    Job,
    ReviewCase,
)
from ..domain.types import EscalationStage, JobStatus, ReviewReason


class MemoryJobStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.jobs: dict[str, Job] = {}
        self.extractions: dict[str, ExtractionResult] = {}
        self.classifications: dict[str, ClassificationResult] = {}
        self.fields: dict[str, ExtractedFields] = {}
        self.escalations: dict[str, dict[str, EscalationResult]] = defaultdict(dict)
        self.explanations: dict[str, ExplanationResult] = {}
        self.explanation_lang: dict[str, str] = {}

    def create_job(self, job: Job) -> None:
        with self._lock:
            self.jobs[job.job_id] = job

    def get_job(self, job_id: str) -> Job | None:
        return self.jobs.get(job_id)

    def set_status(self, job_id: str, status: JobStatus, error_code: str | None = None) -> None:
        with self._lock:
            job = self.jobs.get(job_id)
            if job:
                job.status = status
                job.error_code = error_code

    def save_extraction(self, job_id: str, result: ExtractionResult) -> None:
        self.extractions[job_id] = result

    def save_classification(self, job_id: str, result: ClassificationResult) -> None:
        self.classifications[job_id] = result

    def save_fields(self, job_id: str, fields: ExtractedFields) -> None:
        self.fields[job_id] = fields

    def save_escalation(self, job_id: str, stage: EscalationStage, result: EscalationResult) -> None:
        self.escalations[job_id][stage.value] = result

    def save_explanation(self, job_id: str, target_language: str, result: ExplanationResult) -> None:
        self.explanations[job_id] = result
        self.explanation_lang[job_id] = target_language

    def get_extraction(self, job_id: str) -> ExtractionResult | None:
        return self.extractions.get(job_id)

    def update_explanation_text(self, job_id: str, text: str) -> bool:
        existing = self.explanations.get(job_id)
        if existing is None:
            return False
        existing.explanation_text = text
        return True

    def get_result(self, job_id: str) -> dict | None:
        job = self.jobs.get(job_id)
        if not job:
            return None
        cls = self.classifications.get(job_id)
        expl = self.explanations.get(job_id)
        pre = self.escalations.get(job_id, {}).get("pre_explanation")
        post = self.escalations.get(job_id, {}).get("post_explanation")
        flagged = bool((pre and pre.escalate) or (post and post.escalate))
        matched = list(dict.fromkeys(
            (pre.matched_rule_ids if pre else []) + (post.matched_rule_ids if post else [])))
        f = self.fields.get(job_id)
        return {
            "jobId": job_id,
            "status": job.status.value,
            "errorCode": job.error_code,
            "targetLanguage": job.target_language,
            "documentType": cls.document_type.value if cls else None,
            "classificationConfidence": cls.confidence if cls else None,
            "fields": {
                "issuingAuthority": f.issuing_authority if f else None,
                "deadlineDate": f.deadline_date if f else None,
                "amountOwed": f.amount_owed if f else None,
                "citedSection": f.cited_section if f else None,
                "requiredAction": f.required_action if f else None,
                "fieldConfidence": f.field_confidence if f else {},
            },
            "explanation": expl.explanation_text if expl else None,
            "disclaimerIncluded": expl.disclaimer_included if expl else False,
            "escalation": {"flagged": flagged, "matchedRuleIds": matched},
            "voiceAvailable": True,
        }


class MemoryImageStore:
    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}

    def put(self, job_id: str, image: bytes) -> None:
        self._data[job_id] = image

    def fetch(self, job_id: str) -> bytes | None:
        return self._data.get(job_id)

    def delete(self, job_id: str) -> None:
        self._data.pop(job_id, None)


class MemoryReviewQueue:
    def __init__(self) -> None:
        self._cases: dict[str, ReviewCase] = {}

    def enqueue(self, job_id: str, reason: ReviewReason) -> None:
        self._cases.setdefault(job_id, ReviewCase(job_id=job_id, routed_reason=reason))

    def resolve(self, job_id: str, reviewer_id: str, decision: str,
                final_text: str | None = None) -> ReviewCase | None:
        case = self._cases.get(job_id)
        if not case:
            return None
        case.reviewer_id = reviewer_id
        case.decision = decision
        return case

    def list_open(self) -> list[ReviewCase]:
        return [c for c in self._cases.values() if not c.decision]


class MemoryAuditLogger:
    def __init__(self) -> None:
        self._entries: dict[str, list[AuditEntry]] = defaultdict(list)

    def log_stage(self, job_id: str, stage: str, input_ref: dict, output_ref: dict,
                  model_version: str | None = None, prompt_version: str | None = None) -> None:
        self._entries[job_id].append(AuditEntry(
            job_id=job_id, stage_name=stage, input_ref=dict(input_ref or {}),
            output_ref=dict(output_ref or {}), model_version=model_version,
            prompt_version=prompt_version))

    def entries_for(self, job_id: str) -> list[AuditEntry]:
        return list(self._entries.get(job_id, []))
