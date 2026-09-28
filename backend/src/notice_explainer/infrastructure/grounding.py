"""Grounding wrapper: re-scores field confidence against extracted text.

Composed in api/deps.py around the real/fake extractor. process_job.py is
untouched — this implements the same FieldExtractor port.
"""
from __future__ import annotations

from ..application.ports import FieldExtractor
from ..domain.grounding import ground_fields
from ..domain.models import ExtractedFields
from ..domain.types import DocumentType


class GroundedFieldExtractor(FieldExtractor):
    def __init__(self, inner: FieldExtractor) -> None:
        self._inner = inner

    @property
    def model_version(self) -> str:
        inner_v = getattr(self._inner, "model_version", "unknown")
        return f"{inner_v}+grounded"

    def extract_fields(
        self, text: str, document_type: DocumentType
    ) -> ExtractedFields:
        fields = self._inner.extract_fields(text, document_type)
        return ground_fields(fields, text)
