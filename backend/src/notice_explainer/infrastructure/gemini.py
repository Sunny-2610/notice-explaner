"""Gemini vision + reasoning adapters (HLD §5, LLD §7).

Only constructed when GEMINI_API_KEY is set and USE_FAKE_AI != true.
All calls: 8s timeout, 3x retry via application.retry, failures raise
so process_job maps them to E-301 (job failed, client retries later).
Free-tier only; model defaults to gemini-2.0-flash (cheap vision).
"""
from __future__ import annotations

import base64
import json
import os

import httpx

from ..domain.models import (
    ClassificationResult,
    ExplanationResult,
    ExtractedFields,
    ExtractionResult,
)
from ..domain.types import DocumentType, VISION_REASONING_TIMEOUT_S
from ..application.prompts import DISCLAIMER_TEXT, ESCALATION_NOTICE

_API = "https://generativelanguage.googleapis.com/v1beta/models"
_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def _key() -> str:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    return key


def _generate(parts: list[dict], timeout: int = VISION_REASONING_TIMEOUT_S) -> str:
    url = f"{_API}/{_MODEL}:generateContent?key={_key()}"
    r = httpx.post(url, json={"contents": [{"parts": parts}]}, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected Gemini response: {str(data)[:300]}") from exc


class GeminiVisionExtractor:
    provider_name = f"gemini-{_MODEL}-vision"

    def extract(self, image: bytes) -> ExtractionResult:
        if not image:
            return ExtractionResult(text="", confidence=0.0, provider=self.provider_name)
        b64 = base64.b64encode(image).decode()
        text = _generate([
            {"text": "Transcribe all visible text in this notice verbatim. Return text only."},
            {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
        ])
        # Vision models rarely return calibrated confidence; 0.85 keeps us
        # above the 0.55 review threshold only when text is non-trivial.
        conf = 0.85 if len(text.strip()) > 20 else 0.40
        return ExtractionResult(text=text, confidence=conf, provider=self.provider_name)


class GeminiReasoner:
    """Classifier + field extractor + explanation generator in one client."""

    model_version = f"gemini-{_MODEL}"
    prompt_version = "p-v1"

    def classify(self, text: str) -> ClassificationResult:
        out = _generate([{"text": (
            "Classify this Indian notice as exactly one of: "
            "property_tax_notice, traffic_challan_summons, bank_recovery_notice, unsupported. "
            "Reply '<label> <confidence 0-1>'.\n\n" + text[:4000])}])
        low = out.lower()
        conf = 0.85
        for tok in low.replace(",", " ").split():
            try:
                v = float(tok)
                if 0.0 <= v <= 1.0:
                    conf = v
            except ValueError:
                pass
        if "property_tax" in low:
            return ClassificationResult(DocumentType.PROPERTY_TAX_NOTICE, conf)
        if "challan" in low or "summons" in low:
            return ClassificationResult(DocumentType.TRAFFIC_CHALLAN_SUMMONS, conf)
        if "recovery" in low or "bank" in low:
            return ClassificationResult(DocumentType.BANK_RECOVERY_NOTICE, conf)
        return ClassificationResult(DocumentType.UNSUPPORTED, conf if "unsupported" in low else 0.45)

    def extract_fields(self, text: str, document_type: DocumentType) -> ExtractedFields:
        out = _generate([{"text": (
            "Extract JSON with keys issuingAuthority, deadlineDate (ISO-8601 or null), "
            "amountOwed (number or null), citedSection, requiredAction. JSON only.\n\n"
            + text[:4000])}])
        try:
            start, end = out.index("{"), out.rindex("}") + 1
            d = json.loads(out[start:end])
        except (ValueError, json.JSONDecodeError):
            d = {}
        return ExtractedFields(
            issuing_authority=d.get("issuingAuthority"),
            deadline_date=d.get("deadlineDate"),
            amount_owed=d.get("amountOwed"),
            cited_section=d.get("citedSection"),
            required_action=d.get("requiredAction"),
            field_confidence={"llm": 0.8},
        )

    def generate(self, text: str, document_type: DocumentType, fields: ExtractedFields,
                 target_language: str, escalated: bool) -> ExplanationResult:
        disclaimer = DISCLAIMER_TEXT.get(target_language, DISCLAIMER_TEXT["en"])
        notice = ESCALATION_NOTICE.get(target_language, ESCALATION_NOTICE["en"])
        out = _generate([{"text": (
            f"Explain this {document_type.value} in plain everyday {target_language} "
            f"(not a lawyer; never claim certainty). Cover: 1) what it is "
            f"2) deadline/action 3) what happens if ignored. "
            + (f"4) {notice} " if escalated else "")
            + f"End with exactly: '{disclaimer}'\n\nFields: {fields}\n\nOriginal:\n{text[:4000]}")}])
        if disclaimer not in out:
            out = out.rstrip() + f"\n{disclaimer}"
        return ExplanationResult(explanation_text=out, disclaimer_included=True,
                                 escalation_notice_included=escalated)
