"""POST /api/v1/documents + GET /api/v1/documents/{jobId} (LLD §4.1/4.2)."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from ..application.use_cases.process_job import process_job
from ..application.use_cases.submit_document import ValidationError, submit_document
from . import deps
from .schemas import DocumentResult, SubmitResponse

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def _run(job_id: str) -> None:
    process_job(
        job_id, job_store=deps.job_store, image_store=deps.image_store,
        review_queue=deps.review_queue, audit=deps.audit,
        extractor=deps.extractor, classifier=deps.classifier,
        field_extractor=deps.field_extractor, explanation_gen=deps.explanation_gen,
        escalation_eval=deps.escalation_eval,
    )


@router.post("", status_code=202, response_model=SubmitResponse)
async def submit(
    background: BackgroundTasks,
    image: UploadFile = File(...),
    targetLanguage: str = Form(...),
    sessionId: str = Form("anon"),
) -> SubmitResponse:
    raw = await image.read()
    try:
        job = submit_document(
            raw, image.content_type or "", targetLanguage, sessionId,
            deps.job_store, deps.image_store, deps.audit)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code.value, "message": exc.message})
    background.add_task(_run, job.job_id)
    if deps.job_queue is not None:
        try:
            deps.job_queue.enqueue(job.job_id)
        except Exception:
            pass  # BackgroundTasks _run already scheduled inline
    return SubmitResponse(jobId=job.job_id, status="queued")


@router.get("/{job_id}", response_model=DocumentResult)
def get_result(job_id: str) -> DocumentResult:
    result = deps.job_store.get_result(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="unknown jobId")
    return DocumentResult(**result)
