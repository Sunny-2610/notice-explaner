"""Pipeline data shapes mirroring LLD §3 tables. Plain dataclasses, no I/O."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .types import DocumentType, EscalationStage, JobStatus, ReviewReason


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Job:
    job_id: str
    session_id: str
    target_language: str
    status: JobStatus = JobStatus.QUEUED
    error_code: str | None = None
    submitted_at: datetime = field(default_factory=utcnow)
    completed_at: datetime | None = None


@dataclass
class ExtractionResult:
    text: str
    confidence: float
    provider: str
    duration_ms: int = 0


@dataclass
class ClassificationResult:
    document_type: DocumentType
    confidence: float


@dataclass
class ExtractedFields:
    issuing_authority: str | None = None
    deadline_date: str | None = None  # ISO-8601
    amount_owed: float | None = None
    cited_section: str | None = None
    required_action: str | None = None
    field_confidence: dict[str, float] = field(default_factory=dict)


@dataclass
class EscalationRule:
    id: str
    pattern: str  # regex, matched against normalized text
    severity: str  # triage-only; never suppresses escalation
    description: str = ""


@dataclass
class EscalationResult:
    escalate: bool
    matched_rule_ids: list[str]
    stage: EscalationStage
    rules_version: int = 0


@dataclass
class ExplanationResult:
    explanation_text: str
    disclaimer_included: bool = True
    escalation_notice_included: bool = False


@dataclass
class ReviewCase:
    job_id: str
    routed_reason: ReviewReason
    reviewer_id: str | None = None
    decision: str | None = None  # approve | edit | reject


@dataclass
class AuditEntry:
    job_id: str
    stage_name: str
    input_ref: dict
    output_ref: dict
    model_version: str | None = None
    prompt_version: str | None = None
    created_at: datetime = field(default_factory=utcnow)
