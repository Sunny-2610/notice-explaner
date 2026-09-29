"""Twilio WhatsApp webhook (form-encoded). Disabled (404) unless configured.

Config: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM,
PUBLIC_BASE_URL, WHATSAPP_HASH_SALT. Signature validated by hand
(HMAC-SHA1 over PUBLIC_BASE_URL + path + sorted POST params).
"""
from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Request, Response

from ..application.use_cases.whatsapp_flow import (
    handle_message,
    hash_sender,
)
from ..infrastructure.twilio_whatsapp import verify_twilio_signature
from . import deps

router = APIRouter(prefix="/api/v1/channels/whatsapp", tags=["whatsapp"])


def _configured() -> bool:
    return all([
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN"),
        os.getenv("TWILIO_WHATSAPP_FROM"),
        os.getenv("PUBLIC_BASE_URL"),
        os.getenv("WHATSAPP_HASH_SALT"),
    ])


@router.post("/webhook")
async def webhook(request: Request) -> Response:
    if not _configured():
        raise HTTPException(status_code=404, detail="whatsapp channel disabled")
    form = await request.form()
    params = {k: str(v) for k, v in form.items()}
    base = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    url = base + request.url.path
    signature = request.headers.get("X-Twilio-Signature")
    if not verify_twilio_signature(
        os.getenv("TWILIO_AUTH_TOKEN", ""), url, params, signature
    ):
        raise HTTPException(status_code=403, detail="bad signature")

    sender = params.get("From", "")
    sender_hash = hash_sender(sender, os.getenv("WHATSAPP_HASH_SALT", ""))
    body = params.get("Body", "")
    media: tuple[bytes, str] | None = None
    try:
        num_media = int(params.get("NumMedia", "0"))
    except ValueError:
        num_media = 0
    if num_media > 0:
        content_type = params.get("MediaContentType0", "")
        media_url = params.get("MediaUrl0", "")
        if content_type.startswith("image/") and media_url:
            try:
                media = (deps.messaging_channel.download_media(media_url), content_type)
            except Exception:
                media = None

    try:
        aid_dir = deps.legal_aid_dir
        national = aid_dir.national()
    except Exception:
        national = []
    handle_message(
        sender_hash=sender_hash,
        to=sender,
        text=body,
        media=media,
        channel=deps.messaging_channel,
        job_store=deps.job_store,
        image_store=deps.image_store,
        review_queue=deps.review_queue,
        audit=deps.audit,
        extractor=deps.extractor,
        classifier=deps.classifier,
        field_extractor=deps.field_extractor,
        explanation_gen=deps.explanation_gen,
        escalation_eval=deps.escalation_eval,
        legal_aid=national,
    )
    return Response(status_code=204)
