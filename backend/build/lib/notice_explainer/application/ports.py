"""Ports (interfaces) implemented by infrastructure adapters.

Domain and application code depend only on these Protocols — never on
concrete SDK clients. Keeps vision/reasoning and language/voice swappable.
"""
from __future__ import annotations

from typing import Protocol

from ..domain.models import (
    AuditEntry,
    ClassificationResult,
    CorpusChunk,
    EscalationResult,
    EscalationRule,
    ExplanationResult,
    ExtractedFields,
    ExtractionResult,
    Job,
    ReviewCase,
)
from ..domain.types import DocumentType, EscalationStage, JobStatus, ReviewReason


class TextExtractor(Protocol):
    provider_name: str

    def extract(self, image: bytes) -> ExtractionResult: ...


class DocumentClassifier(Protocol):
    model_version: str

    def classify(self, text: str) -> ClassificationResult: ...


class FieldExtractor(Protocol):
    model_version: str

    def extract_fields(
        self, text: str, document_type: DocumentType
    ) -> ExtractedFields: ...


class ExplanationGenerator(Protocol):
    model_version: str
    prompt_version: str

    def generate(
        self,
        text: str,
        document_type: DocumentType,
        fields: ExtractedFields,
        target_language: str,
        escalated: bool,
    ) -> ExplanationResult: ...


class VoiceService(Protocol):
    def speech_to_text(self, audio: bytes, lang: str) -> str: ...
    def text_to_speech(self, text: str, lang: str) -> bytes: ...


class EscalationRules(Protocol):
    """Versioned rule config with hot-reload (LLD §2.5.1)."""

    @property
    def version(self) -> int: ...
    def active_rules(self) -> list[EscalationRule]: ...


class JobStore(Protocol):
    """processing_jobs + result tables (LLD §3). Postgres later; memory now."""

    def create_job(self, job: Job) -> None: ...
    def get_job(self, job_id: str) -> Job | None: ...
    def set_status(
        self, job_id: str, status: JobStatus, error_code: str | None = None
    ) -> None: ...
    def save_extraction(self, job_id: str, result: ExtractionResult) -> None: ...
    def save_classification(
        self, job_id: str, result: ClassificationResult
    ) -> None: ...
    def save_fields(self, job_id: str, fields: ExtractedFields) -> None: ...
    def save_escalation(
        self, job_id: str, stage: EscalationStage, result: EscalationResult
    ) -> None: ...
    def save_explanation(
        self, job_id: str, target_language: str, result: ExplanationResult
    ) -> None: ...
    def get_result(self, job_id: str) -> dict | None: ...


class ImageStore(Protocol):
    """Transient raw-image storage. Images deleted at terminal states."""

    def put(self, job_id: str, image: bytes) -> None: ...
    def fetch(self, job_id: str) -> bytes | None: ...
    def delete(self, job_id: str) -> None: ...


class ReviewQueue(Protocol):
    def enqueue(self, job_id: str, reason: ReviewReason) -> None: ...
    def resolve(
        self,
        job_id: str,
        reviewer_id: str,
        decision: str,
        final_text: str | None = None,
    ) -> ReviewCase | None: ...
    def list_open(self) -> list[ReviewCase]: ...


class AuditLogger(Protocol):
    """Append-only. No update/delete interface is exposed (LLD §2.9)."""

    def log_stage(
        self,
        job_id: str,
        stage: str,
        input_ref: dict,
        output_ref: dict,
        model_version: str | None = None,
        prompt_version: str | None = None,
    ) -> None: ...
    def entries_for(self, job_id: str) -> list[AuditEntry]: ...


class EscalationEvaluator(Protocol):
    """Deterministic engine runner — records rules_version per evaluation."""

    def evaluate(
        self, text: str, stage: EscalationStage
    ) -> EscalationResult: ...


class LegalAidDirectory(Protocol):
    """Free legal-aid listings. No auth, no user data stored."""

    def national(self) -> list[dict]: ...
    def states(self) -> list[dict]: ...
    def lookup(
        self, state: str | None = None, district: str | None = None
    ) -> dict: ...


class LegalRetriever(Protocol):
    """Legal-corpus search behind the Q&A agent (ADR 0004)."""

    def search(self, query: str, top_k: int = 3) -> list[CorpusChunk]: ...


class MessagingChannel(Protocol):
    """Outbound messaging (WhatsApp via Twilio, or fake in tests)."""

    name: str

    def send_message(self, to: str, body: str) -> None: ...
    def download_media(self, url: str) -> bytes: ...
