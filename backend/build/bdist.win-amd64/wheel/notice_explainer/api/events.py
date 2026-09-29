"""SSE job progress (stage updates only — never explanation tokens).

Polls the job store (never hooks process_job), so this works with the Redis
worker and Postgres stores while process_job stays frozen.
"""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from . import deps
from .documents import enrich_with_deadline

router = APIRouter(prefix="/api/v1/documents", tags=["documents-events"])

TERMINAL = {"completed", "awaiting_review", "failed"}
POLL_S = 0.3
MAX_POLLS = 400  # 120 s hard cap


async def _stream(job_id: str):
    last: str | None = None
    for _ in range(MAX_POLLS):
        result = deps.job_store.get_result(job_id)
        if result is None:
            return
        status = result.get("status")
        if status != last:
            last = status
            yield f"event: status\ndata: {json.dumps({'status': status})}\n\n"
            if status in TERMINAL:
                payload = enrich_with_deadline(result)
                yield f"event: result\ndata: {json.dumps(payload, default=str)}\n\n"
                return
        await asyncio.sleep(POLL_S)
    yield "event: timeout\ndata: {}\n\n"


@router.get("/{job_id}/events")
async def job_events(job_id: str) -> StreamingResponse:
    if deps.job_store.get_job(job_id) is None:
        raise HTTPException(status_code=404, detail="unknown jobId")
    return StreamingResponse(
        _stream(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
