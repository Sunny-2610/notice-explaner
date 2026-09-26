"""LLD §4 response shapes (camelCase on the wire, snake_case in domain)."""
from __future__ import annotations

from pydantic import BaseModel


class SubmitResponse(BaseModel):
    jobId: str
    status: str


class EscalationPayload(BaseModel):
    flagged: bool
    matchedRuleIds: list[str] = []


class FieldsPayload(BaseModel):
    issuingAuthority: str | None = None
    deadlineDate: str | None = None
    amountOwed: float | None = None
    citedSection: str | None = None
    requiredAction: str | None = None
    fieldConfidence: dict[str, float] = {}


class DocumentResult(BaseModel):
    jobId: str
    status: str
    errorCode: str | None = None
    targetLanguage: str | None = None
    documentType: str | None = None
    classificationConfidence: float | None = None
    fields: FieldsPayload = FieldsPayload()
    explanation: str | None = None
    disclaimerIncluded: bool = False
    escalation: EscalationPayload = EscalationPayload(flagged=False)
    voiceAvailable: bool = True


class ReviewItem(BaseModel):
    jobId: str
    routedReason: str
    reviewerId: str | None = None
    decision: str | None = None
