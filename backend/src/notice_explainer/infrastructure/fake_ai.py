"""Fake AI adapters — deterministic stand-ins for Gemini/Bhashini (HLD §5).

Lets the vertical slice + frontend run with zero paid spend and no keys.
Real adapters later implement the same ports.
"""
from __future__ import annotations

from ..application.prompts import DISCLAIMER_TEXT, ESCALATION_NOTICE
from ..domain.models import (
    ClassificationResult,
    ExplanationResult,
    ExtractedFields,
    ExtractionResult,
)
from ..domain.types import DocumentType


class FakeTextExtractor:
    provider_name = "fake-vision"

    def extract(self, image: bytes) -> ExtractionResult:
        if not image:
            return ExtractionResult(text="", confidence=0.0, provider=self.provider_name)
        # Test hooks via raw bytes so integration tests can drive branches.
        if b"EMPTY" in image:
            return ExtractionResult(text="", confidence=0.10, provider=self.provider_name)
        if b"SUMMONS" in image:
            return ExtractionResult(
                text="COURT SUMMONS: you are summoned to appear. Warrant may issue if ignored.",
                confidence=0.97, provider=self.provider_name)
        if b"UNSUPPORTED-TEST" in image:
            return ExtractionResult(
                text="Marriage invitation in Hindi, no legal content.",
                confidence=0.96, provider=self.provider_name)
        if b"LOWCONF" in image:
            return ExtractionResult(text="blurry text", confidence=0.20, provider=self.provider_name)
        return ExtractionResult(
            text=("MUNICIPAL CORPORATION property tax demand notice. "
                  "Amount Rs 4500. Due 2026-11-15 under Section 12A. "
                  "Pay at ward office within 30 days."),
            confidence=0.95, provider=self.provider_name)


class FakeClassifier:
    model_version = "fake-0.1"

    def classify(self, text: str) -> ClassificationResult:
        low = text.lower()
        if "invitation" in low or "unsupported" in low:
            return ClassificationResult(document_type=DocumentType.UNSUPPORTED, confidence=0.92)
        if "blurry" in low or not text.strip():
            return ClassificationResult(document_type=DocumentType.UNSUPPORTED, confidence=0.30)
        if "summons" in low or "court" in low or "warrant" in low:
            return ClassificationResult(
                document_type=DocumentType.TRAFFIC_CHALLAN_SUMMONS, confidence=0.88)
        return ClassificationResult(document_type=DocumentType.PROPERTY_TAX_NOTICE, confidence=0.90)


class FakeFieldExtractor:
    model_version = "fake-0.1"

    def extract_fields(self, text: str, document_type: DocumentType) -> ExtractedFields:
        if document_type == DocumentType.TRAFFIC_CHALLAN_SUMMONS:
            return ExtractedFields(
                issuing_authority="District Court", deadline_date="2026-10-20",
                amount_owed=1500.0, cited_section="MV Act 177",
                required_action="Appear before the court on the given date.",
                field_confidence={"issuingAuthority": 0.9, "deadlineDate": 0.85,
                                  "amountOwed": 0.9, "citedSection": 0.8,
                                  "requiredAction": 0.75})
        return ExtractedFields(
            issuing_authority="Municipal Corporation", deadline_date="2026-11-15",
            amount_owed=4500.0, cited_section="Section 12A",
            required_action="Pay at the ward office within 30 days.",
            field_confidence={"issuingAuthority": 0.92, "deadlineDate": 0.88,
                              "amountOwed": 0.95, "citedSection": 0.82,
                              "requiredAction": 0.80})


class FakeExplanationGenerator:
    model_version = "fake-0.1"
    prompt_version = "p-v1"

    def generate(self, text: str, document_type: DocumentType, fields: ExtractedFields,
                 target_language: str, escalated: bool) -> ExplanationResult:
        disclaimer = DISCLAIMER_TEXT.get(target_language, DISCLAIMER_TEXT["en"])
        notice = ESCALATION_NOTICE.get(target_language, ESCALATION_NOTICE["en"])
        head = {
            "hi": f"यह {document_type.value} है।",
            "mr": f"हे {document_type.value} आहे.",
            "en": f"This is a {document_type.value}.",
        }.get(target_language, f"This is a {document_type.value}.")
        body = f"{head} "
        if fields.amount_owed is not None:
            body += f"Amount: {fields.amount_owed}. "
        if fields.deadline_date:
            body += f"Deadline: {fields.deadline_date}. "
        if fields.required_action:
            body += f"{fields.required_action} "
        if escalated:
            body += f"{notice} "
        body += disclaimer
        return ExplanationResult(explanation_text=body, disclaimer_included=True,
                                 escalation_notice_included=escalated)


class FakeVoiceService:
    def speech_to_text(self, audio: bytes, lang: str) -> str:
        return ""

    def text_to_speech(self, text: str, lang: str) -> bytes:
        return b""
