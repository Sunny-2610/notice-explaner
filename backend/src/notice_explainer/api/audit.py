"""GET /api/v1/documents/{jobId}/audit — append-only trail (HLD §3.6)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from . import deps

router = APIRouter(prefix="/api/v1/documents", tags=["audit"])


@router.get("/{job_id}/audit")
def get_audit(job_id: str) -> dict:
    if deps.job_store.get_job(job_id) is None:
        raise HTTPException(status_code=404, detail="unknown jobId")
    entries = deps.audit.entries_for(job_id)
    out = []
    for e in entries:
        if isinstance(e, dict):
            out.append(e)
        else:
            out.append({"stage": e.stage_name, "input": e.input_ref,
                        "output": e.output_ref, "model": e.model_version,
                        "prompt": e.prompt_version})
    return {"jobId": job_id, "entries": out}
