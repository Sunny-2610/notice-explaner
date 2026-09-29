"""Gemini vision + reasoning adapters (HLD §5, LLD §7).

Only constructed when GEMINI_API_KEY is set and USE_FAKE_AI != true.
All calls: 8s timeout, 3x retry via application.retry. On quota/overload
(429/503) or retired-model 404, _generate automatically retries the
fallback model before raising, so transient free-tier spikes don't fail jobs.
Free-tier only; model defaults to gemini-3.5-flash-lite (cheap vision).
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
_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.1-flash-lite")


def _key() -> str:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    return key


def _post_model(model: str, parts: list[dict],
                timeout: int,
                generation_config: dict | None) -> str:
    url = f"{_API}/{model}:generateContent"
    body: dict = {"contents": [{"parts": parts}]}
    if generation_config is not None:
        body["generationConfig"] = generation_config
    r = httpx.post(url, json=body, headers={"x-goog-api-key": _key()}, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    candidates = data.get("candidates")
    if not candidates:
        raise RuntimeError(
            f"Gemini returned no candidates: {str(data)[:300]}"
        )
    finish = candidates[0].get("finishReason")
    if finish not in (None, "STOP"):
        raise RuntimeError(
            f"Gemini blocked (finishReason={finish}): {str(data)[:300]}"
        )
    try:
        return candidates[0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected Gemini response: {str(data)[:300]}") from exc


def _generate(
    parts: list[dict],
    timeout: int = VISION_REASONING_TIMEOUT_S,
    generation_config: dict | None = None,
) -> str:
    try:
        return _post_model(_MODEL, parts, timeout, generation_config)
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code if exc.response is not None else 0
        # Free-tier reality: primary 503 (high demand), 429 (quota), or 404
        # (retired alias) — one shot at the fallback model, then raise so
        # process_job maps it to E-301 as before.
        if code in (404, 429, 503) and _FALLBACK_MODEL and _FALLBACK_MODEL != _MODEL:
            return _post_model(_FALLBACK_MODEL, parts, timeout, generation_config)
        raise


_CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {
            "type": "string",
            "enum": [
                "property_tax_notice",
                "traffic_challan_summons",
                "bank_recovery_notice",
                "unsupported",
            ],
        },
        "confidence": {"type": "number"},
    },
    "required": ["label"],
}

_FIELDS_SCHEMA = {
    "type": "object",
    "properties": {
        "issuingAuthority": {"type": "string", "nullable": True},
        "deadlineDate": {"type": "string", "nullable": True},
        "amountOwed": {"type": "number", "nullable": True},
        "citedSection": {"type": "string", "nullable": True},
        "requiredAction": {"type": "string", "nullable": True},
    },
}

_JSON_CONFIG = {
    "temperature": 0,
    "responseMimeType": "application/json",
}

_LABEL_TO_TYPE = {
    "property_tax_notice": DocumentType.PROPERTY_TAX_NOTICE,
    "traffic_challan_summons": DocumentType.TRAFFIC_CHALLAN_SUMMONS,
    "bank_recovery_notice": DocumentType.BANK_RECOVERY_NOTICE,
    "unsupported": DocumentType.UNSUPPORTED,
}


def _parse_json_object(out: str) -> dict:
    """Strict parse first; tolerantly extract the first {...} as fallback."""
    try:
        d = json.loads(out)
        if isinstance(d, dict):
            return d
    except json.JSONDecodeError:
        pass
    start, end = out.index("{"), out.rindex("}") + 1
    d = json.loads(out[start:end])
    return d if isinstance(d, dict) else {}


class GeminiVisionExtractor:
    provider_name = f"gemini-{_MODEL}-vision"

    def extract(self, image: bytes) -> ExtractionResult:
        if not image:
            return ExtractionResult(text="", confidence=0.0, provider=self.provider_name)
        b64 = base64.b64encode(image).decode()
        mime = "image/png" if image.startswith(b"\x89PNG") else "image/jpeg"
        text = _generate([
            {"text": "Transcribe all visible text in this notice verbatim. Return text only."},
            {"inline_data": {"mime_type": mime, "data": b64}},
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
        out = _generate(
            [{"text": (
                "Classify this Indian notice as exactly one of: "
                "property_tax_notice, traffic_challan_summons, bank_recovery_notice, unsupported. "
                "Reply with JSON {\"label\": ..., \"confidence\": 0-1}.\n\n" + text[:4000])}],
            generation_config={**_JSON_CONFIG, "responseSchema": _CLASSIFY_SCHEMA},
        )
        try:
            d = _parse_json_object(out)
            label = str(d.get("label", "")).strip().lower()
            try:
                conf = float(d.get("confidence", 0.85))
            except (TypeError, ValueError):
                conf = 0.85
            conf = min(1.0, max(0.0, conf))
            if label in _LABEL_TO_TYPE:
                return ClassificationResult(_LABEL_TO_TYPE[label], conf)
            return ClassificationResult(DocumentType.UNSUPPORTED, 0.45)
        except (ValueError, json.JSONDecodeError, AttributeError):
            pass
        # Tolerant fallback: legacy free-text parse.
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
        out = _generate(
            [{"text": (
                "Extract JSON with keys issuingAuthority, deadlineDate (ISO-8601 or null), "
                "amountOwed (number or null), citedSection, requiredAction. JSON only.\n\n"
                + text[:4000])}],
            generation_config={**_JSON_CONFIG, "responseSchema": _FIELDS_SCHEMA},
        )
        try:
            d = _parse_json_object(out)
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
