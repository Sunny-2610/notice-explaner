"""Submit-document use case (LLD §2.1 + §5).

Validates ingestion (10MB, jpeg/png, hi/mr/en) then creates job + stores image.
Raises ValidationError with ErrorCode for API -> HTTP 400 mapping.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from ...domain.models import Job
from ...domain.types import (
    ALLOWED_CONTENT_TYPES,
    MAX_IMAGE_BYTES,
    SUPPORTED_LANGUAGES,
    ErrorCode,
    JobStatus,
)


@dataclass
class ValidationError(Exception):
    code: ErrorCode
    message: str


def submit_document(
    image: bytes,
    content_type: str,
    target_language: str,
    session_id: str,
    job_store,
    image_store,
    audit,
) -> Job:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError(ErrorCode.INVALID_FILE, "Use a JPEG/PNG image under 10MB.")
    if len(image) > MAX_IMAGE_BYTES:
        raise ValidationError(ErrorCode.INVALID_FILE, "Image must be 10MB or smaller.")
    if not image:
        raise ValidationError(ErrorCode.INVALID_FILE, "Empty image upload.")
    if target_language not in SUPPORTED_LANGUAGES:
        raise ValidationError(
            ErrorCode.UNSUPPORTED_LANGUAGE,
            f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}.",
        )
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    job = Job(job_id=job_id, session_id=session_id or "anon", target_language=target_language)
    job_store.create_job(job)
    image_store.put(job_id, image)
    job_store.set_status(job_id, JobStatus.QUEUED)
    audit.log_stage(job_id, "ingestion", {"sessionId": job.session_id}, {"status": "queued"})
    return job
