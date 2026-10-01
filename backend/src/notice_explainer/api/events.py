"""SSE job progress (stage updates only — never explanation tokens).

Polls the job store (never hooks process_job), so this works with the Redis
worker and Postgres stores while process_job stays frozen.

Streaming protocol (provisional-first delivery):
  status events  -> every stage change, client refetches the full payload.
  result events  -> the full DocumentResult. Sent ONCE for final states
    (completed/failed, or awaiting_review WITHOUT an explanation), but
    TWICE for provisional states (awaiting_review WITH an E-401
    explanation): first the AI answer now, later the verified answer after
    the reviewer resolves. The frontend keeps the stream open on provisional
    results and swaps the banner on the second frame.
"""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from . import deps
from .documents import enrich_with_deadline

router = APIRouter(prefix="/api/v1/documents", tags=["documents-events"])

# Provisional-first delivery: awaiting_review WITH an explanation (E-401) is
# NOT final — emit the provisional result but keep the stream open so the
# later reviewer resolve (awaiting_review -> completed) emits a second,
# verified result. awaiting_review WITHOUT explanation (E-150/E-201) and
# failed/completed are final.
FINAL = {"completed", "failed"}
# Backwards-compat alias (old clients treated awaiting_review as terminal).
TERMINAL = FINAL | {"awaiting_review"}
POLL_S = 0.3
MAX_POLLS = 400  # 120 s hard cap


def _is_provisional(result: dict) -> bool:
    if result.get("provisional") is True:
        return True
    # Fallback for stores that predate the provisional flag.
    return bool(
        result.get("status") == "awaiting_review"
        and result.get("explanation")
        and result.get("errorCode") == "E-401"
    )


async def _stream(job_id: str):
    last: str | None = None
    last_text: str | None = None
    sent_provisional = False
    for _ in range(MAX_POLLS):
        result = deps.job_store.get_result(job_id)
        if result is None:
            return
        status = result.get("status")
        text = result.get("explanation")
        if status != last or text != last_text:
            last = status
            last_text = text
            yield f"event: status\ndata: {json.dumps({'status': status})}\n\n"
            if status in FINAL:
                payload = enrich_with_deadline(result)
                yield f"event: result\ndata: {json.dumps(payload, default=str)}\n\n"
                return
            if status == "awaiting_review":
                if _is_provisional(result):
                    # Provisional answer now, verified answer later.
                    payload = enrich_with_deadline(result)
                    yield f"event: result\ndata: {json.dumps(payload, default=str)}\n\n"
                    sent_provisional = True
                    # Fall through — keep polling for reviewer resolve.
                else:
                    # E-150/E-201: nothing truthful to show yet.
                    payload = enrich_with_deadline(result)
                    yield f"event: result\ndata: {json.dumps(payload, default=str)}\n\n"
                    return
        # Reviewer resolved while stream open: provisional -> completed.
        # Status-change branch above already handles it; this is a no-op guard.
        _ = sent_provisional
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
