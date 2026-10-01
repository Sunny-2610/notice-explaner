"""Voice I/O endpoints (LLD §2.7 + §4).

Voice NEVER fails the job: any failure/timeout -> E-302 style fallback
(voiceAvailable=false, text-only continues).
"""
from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from ..application.use_cases.answer_question import (
    AnswerQuestionError,
    answer_question,
)
from . import deps

router = APIRouter(prefix="/api/v1/documents", tags=["voice"])

MAX_SPEECH_CHARS = 1500


def _ask_error(exc: AnswerQuestionError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code.value, "message": exc.message},
    )


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
    except Exception as exc:
        deps.audit.log_stage(job_id, "voice_query", {"bytes": len(raw)},
                             {"error": str(exc)[:200], "code": "E-302"})
        return {"jobId": job_id, "transcription": "",
                "voiceAvailable": False, "code": "E-302"}
    if not text or not text.strip():
        deps.audit.log_stage(job_id, "voice_query", {"bytes": len(raw)},
                             {"transcription": "", "code": "E-302"})
        return {"jobId": job_id, "transcription": "",
                "voiceAvailable": False, "code": "E-302"}
    deps.audit.log_stage(job_id, "voice_query", {"bytes": len(raw)},
                         {"transcription": str(text)[:300]})
    return {"jobId": job_id, "transcription": text, "voiceAvailable": True}


@router.post("/{job_id}/voice-speech")
async def voice_speech(
    job_id: str,
    lang: str = Form("hi"),
    text: str | None = Form(None),
) -> Response:
    result = deps.job_store.get_result(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="unknown jobId")
    if text is not None and len(text) > MAX_SPEECH_CHARS:
        raise HTTPException(status_code=400, detail="text too long (max 1500 chars)")
    speak = text if text and text.strip() else (result.get("explanation") or "")
    if not speak:
        raise HTTPException(status_code=409, detail="no explanation yet")
    try:
        audio = deps.voice_service.text_to_speech(speak, lang)
    except Exception as exc:
        deps.audit.log_stage(job_id, "voice_speech", {}, {"error": str(exc)[:200]})
        audio = b""
    if not audio:
        return Response(status_code=204)  # text-only fallback (E-302)
    # Success is audited like every other stage (byte count only, never audio).
    deps.audit.log_stage(job_id, "voice_speech", {"chars": len(speak)},
                         {"bytes": len(audio)})
    return Response(content=audio, media_type="audio/mpeg")


@router.post("/{job_id}/voice-ask")
async def voice_ask(
    job_id: str,
    audio: UploadFile = File(...),
    lang: str = Form("hi"),
) -> dict:
    """Spoken follow-up: STT -> existing answer_question() use case.

    The 10-question limit, qa_ask audit trail and disclaimer all apply via
    the shared use case. STT failure/empty transcript returns E-302 and
    never calls the Q&A agent; voice failure never fails the job.
    """
    if deps.job_store.get_job(job_id) is None:
        raise HTTPException(status_code=404, detail="unknown jobId")
    raw = await audio.read()
    try:
        transcript = deps.voice_service.speech_to_text(raw, lang)
    except Exception as exc:
        deps.audit.log_stage(job_id, "voice_ask", {"bytes": len(raw)},
                             {"error": str(exc)[:200], "code": "E-302"})
        return {"jobId": job_id, "transcription": "", "answer": "",
                "disclaimerIncluded": False,
                "voiceAvailable": False, "code": "E-302"}
    if not transcript or not transcript.strip():
        deps.audit.log_stage(job_id, "voice_ask", {"bytes": len(raw)},
                             {"transcription": "", "code": "E-302"})
        return {"jobId": job_id, "transcription": "", "answer": "",
                "disclaimerIncluded": False,
                "voiceAvailable": False, "code": "E-302"}
    try:
        answer = answer_question(
            job_id, transcript.strip(),
            job_store=deps.job_store,
            qa_agent=deps.qa_agent,
            audit=deps.audit,
        )
    except AnswerQuestionError as exc:
        raise _ask_error(exc)
    deps.audit.log_stage(job_id, "voice_ask", {"bytes": len(raw)},
                         {"transcription": transcript.strip()[:300]})
    return {"jobId": job_id, "transcription": transcript.strip(),
            "answer": answer, "disclaimerIncluded": True,
            "voiceAvailable": True}
