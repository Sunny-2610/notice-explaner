"""POST /api/v1/documents + GET /api/v1/documents/{jobId} (LLD §4.1/4.2)."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Response, UploadFile

from ..application.use_cases.process_job import process_job
from ..application.use_cases.answer_question import answer_question, AnswerQuestionError
from ..application.use_cases.submit_document import ValidationError, submit_document
from ..application.prompts import DISCLAIMER_TEXT
from ..domain.checklist import checklist_for
from ..domain.deadline import days_remaining, today_ist
from . import deps
from .schemas import AskRequest, AskResponse, DocumentResult, SubmitResponse

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
    if deps.job_queue is not None:
        try:
            deps.job_queue.enqueue(job.job_id)
        except Exception:
            # Redis enqueue failed — fall back to inline run.
            background.add_task(_run, job.job_id)
    else:
        # No Redis configured (demo/dev path) — run inline.
        background.add_task(_run, job.job_id)
    return SubmitResponse(jobId=job.job_id, status="queued")


@router.get("/{job_id}", response_model=DocumentResult)
def get_result(job_id: str) -> DocumentResult:
    result = deps.job_store.get_result(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="unknown jobId")
    return DocumentResult(**enrich_with_deadline(result))


def enrich_with_deadline(result: dict) -> dict:
    """Attach the presentation-layer deadline/checklist without touching stores."""
    try:
        fields = result.get("fields") or {}
        iso = fields.get("deadlineDate")
        lang = result.get("targetLanguage") or "hi"
        if iso:
            days = days_remaining(iso, today_ist())
            result["deadline"] = {
                "daysRemaining": days,
                "overdue": bool(days is not None and days < 0),
                "checklist": checklist_for(
                    result.get("documentType") or "", lang
                ),
            }
        else:
            result["deadline"] = None
    except Exception:
        result["deadline"] = None
    return result


@router.post("/{job_id}/ask", response_model=AskResponse)
def ask(job_id: str, body: AskRequest) -> AskResponse:
    """Follow-up Q&A about a processed notice (ADR 0003).

    Sandboxed agent: read-only tools, disclaimer always appended.
    Escalation state is never read or modified here.
    """
    try:
        answer = answer_question(
            job_id, body.question,
            job_store=deps.job_store,
            qa_agent=deps.qa_agent,
            audit=deps.audit,
        )
    except AnswerQuestionError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code.value, "message": exc.message})
    return AskResponse(jobId=job_id, question=body.question, answer=answer)


_ICS_SUMMARY = {
    "en": "Notice deadline",
    "hi": "नोटिस की अंतिम तारीख",
    "mr": "नोटीसची अंतिम तारीख",
}

_ICS_AUTH_LABEL = {"en": "Authority", "hi": "कार्यालय", "mr": "कार्यालय"}
_ICS_ACTION_LABEL = {"en": "Action", "hi": "कार्रवाई", "mr": "कारवाई"}


def _ics_escape(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
    )


def _ics_fold(line: str) -> str:
    """Fold a content line at 75 octets (RFC 5545 §3.1), CRLF + space."""
    raw_len = len(line.encode("utf-8"))
    if raw_len <= 75:
        return line
    chunks: list[bytes] = []
    cur = b""
    limit = 75
    for ch in line:
        b = ch.encode("utf-8")
        if len(cur) + len(b) > limit and cur:
            chunks.append(cur)
            cur = b""
            limit = 74  # continuation line reserves 1 octet for the space
        else:
            cur += b
    if cur:
        chunks.append(cur)
    out = chunks[0].decode("utf-8")
    for c in chunks[1:]:
        out += "\r\n " + c.decode("utf-8")
    return out


def _parse_iso_date(iso: str) -> date | None:
    try:
        y, m, d = iso.strip().split("-")
        return date(int(y), int(m), int(d))
    except (ValueError, AttributeError):
        return None


@router.get("/{job_id}/reminder.ics")
def reminder_ics(job_id: str) -> Response:
    """All-day VEVENT on the notice deadline with 7/3/1-day 9AM alarms."""
    result = deps.job_store.get_result(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="unknown jobId")
    fields = result.get("fields") or {}
    iso = fields.get("deadlineDate")
    target = _parse_iso_date(iso) if iso else None
    if target is None:
        raise HTTPException(status_code=404, detail="no deadline")
    days = days_remaining(iso, today_ist())
    if days is None or days < 0:
        raise HTTPException(status_code=404, detail="no upcoming deadline")
    lang = result.get("targetLanguage") or "hi"
    if lang not in ("en", "hi", "mr"):
        lang = "hi"
    summary = _ICS_SUMMARY[lang]
    disclaimer = DISCLAIMER_TEXT.get(lang, DISCLAIMER_TEXT["en"])
    authority = fields.get("issuingAuthority") or ""
    action = fields.get("requiredAction") or ""
    desc_parts = []
    if authority:
        desc_parts.append(f"{_ICS_AUTH_LABEL[lang]}: {authority}")
    if action:
        desc_parts.append(f"{_ICS_ACTION_LABEL[lang]}: {action}")
    desc_parts.append(disclaimer)
    description = "\n".join(desc_parts)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dtstart = target.strftime("%Y%m%d")
    dtend = (target + timedelta(days=1)).strftime("%Y%m%d")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Yojana Mitra//Notice Deadline//EN",
        "BEGIN:VEVENT",
        f"UID:{job_id}@yojana-mitra",
        f"DTSTAMP:{stamp}",
        f"DTSTART;VALUE=DATE:{dtstart}",
        f"DTEND;VALUE=DATE:{dtend}",
        f"SUMMARY:{_ics_escape(summary)}",
        f"DESCRIPTION:{_ics_escape(description)}",
    ]
    for trigger in ("-P6DT15H", "-P2DT15H", "-PT15H"):
        lines += [
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"TRIGGER:{trigger}",
            f"DESCRIPTION:{_ics_escape(summary)}",
            "END:VALARM",
        ]
    lines += ["END:VEVENT", "END:VCALENDAR"]
    body = "\r\n".join(_ics_fold(line) for line in lines) + "\r\n"
    return Response(
        content=body,
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="notice-deadline.ics"'},
    )
