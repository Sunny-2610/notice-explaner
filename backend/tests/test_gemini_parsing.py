"""Gemini parsing: structured JSON primary path, tolerant fallback (no network)."""
import json

import pytest

import notice_explainer.infrastructure.gemini as gemini_mod
from notice_explainer.domain.types import DocumentType


def _patch_generate(monkeypatch, text=None, capture=None, raw=None):
    def fake(parts, timeout=8, generation_config=None):
        if capture is not None:
            capture["parts"] = parts
            capture["generation_config"] = generation_config
        if raw is not None:
            return raw() if callable(raw) else raw
        return text

    monkeypatch.setattr(gemini_mod, "_generate", fake)


def test_classify_valid_json(monkeypatch):
    capture = {}
    _patch_generate(
        monkeypatch,
        text=json.dumps({"label": "bank_recovery_notice", "confidence": 0.91}),
        capture=capture,
    )
    r = gemini_mod.GeminiReasoner().classify("loan overdue notice")
    assert r.document_type == DocumentType.BANK_RECOVERY_NOTICE
    assert r.confidence == pytest.approx(0.91)
    cfg = capture["generation_config"]
    assert cfg["temperature"] == 0
    assert cfg["responseMimeType"] == "application/json"
    assert "responseSchema" in cfg


def test_extract_fields_valid_json(monkeypatch):
    capture = {}
    payload = {
        "issuingAuthority": "Municipal Corporation",
        "deadlineDate": "2026-11-15",
        "amountOwed": 4500,
        "citedSection": "Section 12A",
        "requiredAction": "Pay at the ward office.",
    }
    _patch_generate(monkeypatch, text=json.dumps(payload), capture=capture)
    f = gemini_mod.GeminiReasoner().extract_fields(
        "tax notice", DocumentType.PROPERTY_TAX_NOTICE
    )
    assert f.issuing_authority == "Municipal Corporation"
    assert f.deadline_date == "2026-11-15"
    assert f.amount_owed == 4500
    assert capture["generation_config"]["responseMimeType"] == "application/json"


def test_classify_malformed_json_falls_back(monkeypatch):
    _patch_generate(monkeypatch, raw="property_tax_notice 0.9 some free text")
    r = gemini_mod.GeminiReasoner().classify("tax due")
    assert r.document_type == DocumentType.PROPERTY_TAX_NOTICE
    assert r.confidence == pytest.approx(0.9)


def test_extract_fields_malformed_json_falls_back_empty(monkeypatch):
    _patch_generate(monkeypatch, raw="not json at all {{{")
    f = gemini_mod.GeminiReasoner().extract_fields(
        "blurry", DocumentType.PROPERTY_TAX_NOTICE
    )
    assert f.issuing_authority is None
    assert f.amount_owed is None


def test_classify_unknown_label_unsupported_low_confidence(monkeypatch):
    _patch_generate(
        monkeypatch,
        text=json.dumps({"label": "water_bill", "confidence": 0.99}),
    )
    r = gemini_mod.GeminiReasoner().classify("water bill")
    assert r.document_type == DocumentType.UNSUPPORTED
    assert r.confidence < 0.6


def test_extract_selects_png_mime(monkeypatch):
    capture = {}
    _patch_generate(
        monkeypatch,
        text="transcribed notice text that is long enough here",
        capture=capture,
    )
    ext = gemini_mod.GeminiVisionExtractor()
    ext.extract(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    inline = capture["parts"][1]["inline_data"]
    assert inline["mime_type"] == "image/png"


def test_extract_defaults_to_jpeg_mime(monkeypatch):
    capture = {}
    _patch_generate(
        monkeypatch,
        text="transcribed notice text that is long enough here",
        capture=capture,
    )
    gemini_mod.GeminiVisionExtractor().extract(b"\xff\xd8\xff" + b"\x00" * 64)
    assert capture["parts"][1]["inline_data"]["mime_type"] == "image/jpeg"
