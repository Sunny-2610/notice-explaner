"""LLD §4 response shapes (camelCase on the wire, snake_case in domain).

DocumentResult is THE contract the frontend renders. provisional/verified/
reviewReason drive the provisional-first UX: an escalated job returns its AI
answer immediately (provisional=true, review pending) and flips to
verified=true once a reviewer approves. Memory and Postgres stores must
return byte-identical keys (see their get_result docstrings).
"""
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


class DeadlineInfo(BaseModel):
    daysRemaining: int | None = None
    overdue: bool = False
    checklist: list[str] = []


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
    deadline: DeadlineInfo | None = None
    # Provisional-first delivery (instant answer + async expert review).
    # provisional=True means AI answer is shown but expert check is pending
    # (awaiting_review + E-401 with explanation saved). verified=True means
    # a human reviewer approved/edited and status flipped to completed.
    provisional: bool = False
    verified: bool = False
    reviewReason: str | None = None


class ReviewItem(BaseModel):
    jobId: str
    routedReason: str
    reviewerId: str | None = None
    decision: str | None = None


class AskRequest(BaseModel):
    question: str
    targetLanguage: str | None = None


class AskResponse(BaseModel):
    jobId: str
    question: str
    answer: str
    disclaimerIncluded: bool = True
