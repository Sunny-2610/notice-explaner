"""Review queue endpoints (LLD §2.8 + §4). Reviewer/admin auth comes later."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..domain.types import JobStatus
from . import deps
from .schemas import ReviewItem

router = APIRouter(prefix="/api/v1/review", tags=["review"])


class ResolveBody(BaseModel):
    reviewerId: str = "reviewer-1"
    decision: str = "approve"  # approve | edit | reject
    finalText: str | None = None


@router.get("/queue", response_model=list[ReviewItem])
def list_queue() -> list[ReviewItem]:
    return [ReviewItem(jobId=c.job_id, routedReason=c.routed_reason.value,
                       reviewerId=c.reviewer_id, decision=c.decision)
            for c in deps.review_queue.list_open()]


@router.post("/{job_id}/resolve", response_model=ReviewItem)
def resolve(job_id: str, body: ResolveBody) -> ReviewItem:
    if body.decision not in ("approve", "edit", "reject"):
        raise HTTPException(status_code=400, detail="decision must be approve|edit|reject")
    case = deps.review_queue.resolve(job_id, body.reviewerId, body.decision, body.finalText)
    if case is None:
        raise HTTPException(status_code=404, detail="unknown review case")
    if body.decision in ("approve", "edit"):
        deps.job_store.set_status(job_id, JobStatus.COMPLETED)
        if body.finalText and job_id in deps.job_store.explanations:
            deps.job_store.explanations[job_id].explanation_text = body.finalText
    else:
        deps.job_store.set_status(job_id, JobStatus.FAILED, "E-401")
    deps.image_store.delete(job_id)
    return ReviewItem(jobId=case.job_id, routedReason=case.routed_reason.value,
                      reviewerId=case.reviewer_id, decision=case.decision)
