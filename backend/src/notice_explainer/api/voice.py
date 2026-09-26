"""Voice I/O endpoints (LLD §2.7 + §4).

Voice NEVER fails the job: any failure/timeout -> E-302 style fallback
(voiceAvailable=false, text-only continues).
"""
from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from . import deps

router = APIRouter(prefix="/api/v1/documents", tags=["voice"])


@router.post("/{job_id}/voice-query")
async def voice_query(
    job_id: str,
    audio: UploadFile = File(...),
    lang: str = Form("hi"),
) -> dict:
    if deps.job_store.get_job(job_id) is None:
        raise HTTPException(status_code=404, detail="unknown jobId")
    raw = await audio.read()
    try:
        text = deps.voice_service.speech_to_text(raw, lang)
        deps.audit.log_stage(job_id, "voice_query", {"bytes": len(raw)},
                             {"transcription": str(text)[:300]})
        return {"jobId": job_id, "transcription": text, "voiceAvailable": True}
    except Exception as exc:
        deps.audit.log_stage(job_id, "voice_query", {"bytes": len(raw)},
                             {"error": str(exc)[:200], "code": "E-302"})
        return {"jobId": job_id, "transcription": "",
                "voiceAvailable": False, "code": "E-302"}


@router.post("/{job_id}/voice-speech")
async def voice_speech(job_id: str, lang: str = Form("hi")) -> Response:
    result = deps.job_store.get_result(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="unknown jobId")
    text = result.get("explanation") or ""
    if not text:
        raise HTTPException(status_code=409, detail="no explanation yet")
    try:
        audio = deps.voice_service.text_to_speech(text, lang)
    except Exception as exc:
        deps.audit.log_stage(job_id, "voice_speech", {}, {"error": str(exc)[:200]})
        audio = b""
    if not audio:
        return Response(status_code=204)  # text-only fallback (E-302)
    return Response(content=audio, media_type="audio/mpeg")
