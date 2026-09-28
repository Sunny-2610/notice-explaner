"""WhatsApp intake flow (ports only — no infrastructure imports).

Raw phone numbers are NEVER stored in jobs, logs, or audit entries: senders
are keyed by sha256(number + salt)[:16]. The only exception is the ephemeral
in-memory sender_registry (job_id -> number, single process), which exists
solely so the review-resolve hook can deliver the approved explanation and
is never written to any log or store.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path

from ...domain.checklist import checklist_for
from ...domain.types import ALLOWED_CONTENT_TYPES, MAX_IMAGE_BYTES, JobStatus
from ..prompts import DISCLAIMER_TEXT
from .process_job import process_job
from .submit_document import ValidationError, submit_document

MAX_MESSAGE_CHARS = 1500
RATE_LIMIT = 10
RATE_WINDOW_S = 3600
WAIT_S = 60

# Ephemeral, single-process state (documented limitation: prefs/rate limits
# do not survive restarts or scale past one worker).
lang_prefs: dict[str, str] = {}
greeted: set[str] = set()
rate_hits: dict[str, list[float]] = {}
sender_registry: dict[str, dict] = {}

_STRINGS_PATH = Path(__file__).resolve().parents[4] / "data" / "whatsapp_strings.json"
_strings_cache: dict | None = None


def load_strings() -> dict:
    global _strings_cache
    if _strings_cache is None:
        _strings_cache = json.loads(_STRINGS_PATH.read_text(encoding="utf-8"))
    return _strings_cache


def t(lang: str) -> dict:
    strings = load_strings()
    return strings.get(lang, strings["hi"])


def hash_sender(number: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}{number}".encode("utf-8")).hexdigest()[:16]


def _inr(amount: float) -> str:
    n = int(round(float(amount)))
    s = str(abs(n))
    last3 = s[-3:]
    rest = s[:-3]
    groups = []
    while rest:
        groups.append(rest[-2:])
        rest = rest[:-2]
    head = ",".join(reversed(groups)) + ("," if groups else "")
    return ("-₹" if n < 0 else "₹") + head + last3


def _dmy(iso: str | None) -> str | None:
    if not iso:
        return None
    try:
        y, m, d = iso.split("-")
        return f"{int(d):02d}/{int(m):02d}/{y}"
    except (ValueError, AttributeError):
        return None


def _legal_aid_line(lang: str, entries: list[dict]) -> str:
    bits = [f"{e.get('name', '')} {e.get('phone', '')}".strip() for e in entries]
    bits = [b for b in bits if b]
    if not bits:
        return ""
    return t(lang)["legal_aid"].format(entries=", ".join(bits))


def format_reply(result: dict, lang: str, legal_aid: list[dict]) -> list[str]:
    """Deterministic WhatsApp reply bodies (each <= 1500 chars)."""
    s = t(lang)
    fields = result.get("fields") or {}
    escalated = bool((result.get("escalation") or {}).get("flagged"))
    status = result.get("status", "")
    disclaimer = DISCLAIMER_TEXT.get(lang, DISCLAIMER_TEXT["en"])

    if escalated and status != "completed":
        # Escalated jobs stay awaiting_review: verdict + human-review note +
        # legal aid NOW, never the unreviewed explanation.
        lines = [s["verdict_serious"], s["under_review"]]
        aid = _legal_aid_line(lang, legal_aid)
        if aid:
            lines.append(aid)
        lines.append(disclaimer)
        return split_message("\n".join(lines))

    lines = [s["verdict_serious"] if escalated else s["verdict_ok"]]
    facts: list[str] = []
    if fields.get("issuingAuthority"):
        facts.append(f"{s['authority_label']}: {fields['issuingAuthority']}")
    if fields.get("amountOwed") is not None:
        facts.append(f"{s['amount_label']}: {_inr(fields['amountOwed'])}")
    if fields.get("deadlineDate"):
        facts.append(f"{s['deadline_label']}: {_dmy(fields['deadlineDate'])}")
    if fields.get("requiredAction"):
        facts.append(f"{s['action_label']}: {fields['requiredAction']}")
    if facts:
        lines.extend(facts)
    if result.get("explanation"):
        lines.append(result["explanation"])
    else:
        lines.append(disclaimer)
    checklist = checklist_for(result.get("documentType") or "", lang)
    if checklist:
        lines.append(s["checklist_title"] + " " + " ".join(f"- {item}" for item in checklist))
    if escalated:
        aid = _legal_aid_line(lang, legal_aid)
        if aid:
            lines.append(aid)
    return split_message("\n".join(lines))


def split_message(text: str, limit: int = MAX_MESSAGE_CHARS) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    current: list[str] = []
    size = 0
    for line in text.split("\n"):
        extra = len(line) + (1 if current else 0)
        if current and size + extra > limit:
            parts.append("\n".join(current))
            current, size = [], 0
            extra = len(line)
        current.append(line)
        size += extra
    if current:
        parts.append("\n".join(current))
    return [p for p in parts if p]


def _rate_limited(sender_hash: str) -> bool:
    now = time.time()
    hits = [h for h in rate_hits.get(sender_hash, []) if now - h < RATE_WINDOW_S]
    rate_hits[sender_hash] = hits
    return len(hits) >= RATE_LIMIT


def _record_hit(sender_hash: str) -> None:
    rate_hits.setdefault(sender_hash, []).append(time.time())


def _wait_terminal(job_store, job_id: str, timeout: float) -> dict | None:
    end = time.time() + timeout
    while time.time() < end:
        result = job_store.get_result(job_id)
        if result and result.get("status") in ("completed", "awaiting_review", "failed"):
            return result
        time.sleep(0.5)
    return None


def handle_message(
    *,
    sender_hash: str,
    to: str,
    text: str,
    media: tuple[bytes, str] | None,
    lang_store: dict | None = None,
    channel,
    job_store,
    image_store,
    review_queue,
    audit,
    extractor,
    classifier,
    field_extractor,
    explanation_gen,
    escalation_eval,
    legal_aid: list[dict] | None = None,
) -> None:
    """Route one incoming WhatsApp message. Never logs the raw number."""
    prefs = lang_store if lang_store is not None else lang_prefs
    aid = legal_aid or []
    body = (text or "").strip()

    if body in ("1", "2"):
        prefs[sender_hash] = "hi" if body == "1" else "mr"
        channel.send_message(to, t(prefs[sender_hash])["lang_set"])
        return
    if sender_hash not in prefs and sender_hash not in greeted:
        greeted.add(sender_hash)
        channel.send_message(to, f"{t('hi')['menu']}")
        return

    lang = prefs.get(sender_hash, "hi")
    if media is None:
        channel.send_message(to, t(lang)["send_photo"])
        return

    image, content_type = media
    if content_type not in ALLOWED_CONTENT_TYPES or len(image) > MAX_IMAGE_BYTES or not image:
        channel.send_message(to, t(lang)["bad_file"])
        return
    if _rate_limited(sender_hash):
        channel.send_message(to, t(lang)["rate_limited"])
        return

    try:
        job = submit_document(
            image, content_type, lang, f"wa:{sender_hash}",
            job_store, image_store, audit)
    except ValidationError as exc:
        channel.send_message(to, t(lang)["bad_file"])
        # Audit key carries only the sender hash, never the raw number.
        audit.log_stage(f"wa-validation-{sender_hash}", "whatsapp_validation",
                        {}, {"code": exc.code.value})
        return
    _record_hit(sender_hash)
    sender_registry[job.job_id] = {"to": to, "lang": lang}

    thread = threading.Thread(
        target=process_job,
        kwargs=dict(
            job_id=job.job_id, job_store=job_store, image_store=image_store,
            review_queue=review_queue, audit=audit, extractor=extractor,
            classifier=classifier, field_extractor=field_extractor,
            explanation_gen=explanation_gen, escalation_eval=escalation_eval),
        daemon=True)
    thread.start()
    result = _wait_terminal(job_store, job.job_id, WAIT_S)
    if result is None:
        channel.send_message(to, t(lang)["still_processing"])
        _watch_later(job.job_id, channel, job_store, aid)
        return
    for part in format_reply(result, lang, aid):
        channel.send_message(to, part)
    if result.get("status") == "completed":
        sender_registry.pop(job.job_id, None)


def _watch_later(job_id: str, channel, job_store, aid: list[dict]) -> None:
    """Deliver the reply when a slow job finishes (best effort, daemon)."""

    def _run() -> None:
        result = _wait_terminal(job_store, job_id, 9 * 60)
        if result is None:
            sender_registry.pop(job_id, None)
            return
        info = sender_registry.get(job_id, {})
        for part in format_reply(result, info.get("lang", "hi"), aid):
            try:
                channel.send_message(info.get("to", ""), part)
            except Exception:
                break
        if result.get("status") == "completed":
            sender_registry.pop(job_id, None)

    threading.Thread(target=_run, daemon=True).start()
