"""Field grounding verifier (pure, stdlib only).

Never show a field value with high confidence unless it actually appears in
the extracted notice text. Values are never modified — only the
field_confidence map is rebuilt.
"""
from __future__ import annotations

import re
from datetime import date

from .models import ExtractedFields

_DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def normalize_digits(text: str) -> str:
    """Map Devanagari digits ०-९ to 0-9."""
    return text.translate(_DEVA_DIGITS)


_NUM_TOKEN_RE = re.compile(r"\d+(?:\.\d+)?")


def amount_grounded(amount: float, text: str) -> bool:
    """True if the amount appears among numeric tokens in the text."""
    norm = normalize_digits(text)
    # Strip grouping commas (incl. Indian 1,00,000) and currency markers.
    no_commas = norm.replace(",", "")
    cleaned = no_commas.replace("₹", " ")
    cleaned = re.sub(r"(?i)\brs\.?\b|\binr\b", " ", cleaned)
    for tok in _NUM_TOKEN_RE.findall(cleaned):
        try:
            if abs(float(tok) - float(amount)) <= 0.005:
                return True
        except ValueError:
            continue
    return False


_EN_MONTHS = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sept": 9, "sep": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

_HI_MONTHS = {
    "जनवरी": 1,
    "फरवरी": 2, "फ़रवरी": 2, "फरवरी": 2,
    "मार्च": 3,
    "अप्रैल": 4, "अप्रेल": 4,
    "मई": 5,
    "जून": 6,
    "जुलाई": 7, "जुलई": 7,
    "अगस्त": 8, "आगस्ट": 8,
    "सितंबर": 9, "सितम्बर": 9,
    "अक्टूबर": 10, "अक्तूबर": 10,
    "नवंबर": 11, "नवम्बर": 11,
    "दिसंबर": 12, "दिसम्बर": 12,
}

_MR_MONTHS = {
    "जानेवारी": 1,
    "फेब्रुवारी": 2,
    "मार्च": 3,
    "एप्रिल": 4,
    "मे": 5,
    "जून": 6,
    "जुलै": 7,
    "ऑगस्ट": 8, "आगस्ट": 8,
    "सप्टेंबर": 9, "सप्टेबर": 9,
    "ऑक्टोबर": 10, "ऑक्टोबर": 10,
    "नोव्हेंबर": 11, "नोव्हेबर": 11,
    "डिसेंबर": 12,
}

_MONTH_LOOKUP: dict[str, int] = {}
for _table in (_EN_MONTHS, _HI_MONTHS, _MR_MONTHS):
    for _k, _v in _table.items():
        _MONTH_LOOKUP[_k.lower()] = _v

_ISO_RE = re.compile(r"(\d{4})\s*[-/.\u2013\u2014]\s*(\d{1,2})\s*[-/.\u2013\u2014]\s*(\d{1,2})")
_DMY_RE = re.compile(r"\b(\d{1,2})\s*[-/.\u2013\u2014]\s*(\d{1,2})\s*[-/.\u2013\u2014]\s*(\d{2,4})")
_TEXTUAL_RE = re.compile(
    r"(\d{1,2})\s+([A-Za-z\u0900-\u097F]+?)\s+(\d{2,4})",
)


def _parse_iso(iso: str) -> date | None:
    try:
        parts = iso.strip().split("-")
        if len(parts) != 3:
            return None
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, AttributeError):
        return None


def date_grounded(iso: str, text: str) -> bool:
    """True if the ISO date appears in the text in a supported format."""
    target = _parse_iso(iso)
    if target is None:
        return False
    norm = normalize_digits(text)
    candidates: list[date] = []

    for m in _ISO_RE.finditer(norm):
        try:
            candidates.append(date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
        except ValueError:
            continue
    for m in _DMY_RE.finditer(norm):
        try:
            dd, mm = int(m.group(1)), int(m.group(2))
            yy_raw = m.group(3)
            yy = int(yy_raw)
            if len(yy_raw) == 2:
                yy = 2000 + yy if yy < 70 else 1900 + yy
            candidates.append(date(yy, mm, dd))
        except ValueError:
            continue
    for m in _TEXTUAL_RE.finditer(norm):
        try:
            dd = int(m.group(1))
            name = m.group(2).strip().strip(",.;:").lower()
            mm = _MONTH_LOOKUP.get(name)
            if mm is None:
                continue
            yy_raw = m.group(3)
            yy = int(yy_raw)
            if len(yy_raw) == 2:
                yy = 2000 + yy if yy < 70 else 1900 + yy
            candidates.append(date(yy, mm, dd))
        except ValueError:
            continue
    return target in candidates


_SPLIT_RE = re.compile(r'[\s,.;:!?()\[\]{}"\'\-—–/\\|।॥]+', re.UNICODE)


def _tokenize(s: str) -> list[str]:
    return [t for t in _SPLIT_RE.split(s.lower()) if t]


def text_overlap(value: str, text: str) -> float:
    """Token overlap ratio: |value-tokens found in text| / |value-tokens|."""
    vtoks = _tokenize(value)
    if not vtoks:
        return 0.0
    text_set = set(_tokenize(text))
    hits = sum(1 for t in vtoks if t in text_set)
    return hits / len(vtoks)


def _score_text(value: str, text: str) -> float:
    if value.lower() in text.lower():
        return 0.95
    if text_overlap(value, text) >= 0.6:
        return 0.75
    return 0.30


def ground_fields(fields: ExtractedFields, text: str) -> ExtractedFields:
    """Return a NEW ExtractedFields with field_confidence rebuilt."""
    conf: dict[str, float] = {}
    if fields.issuing_authority is not None:
        conf["issuingAuthority"] = _score_text(fields.issuing_authority, text)
    if fields.deadline_date is not None:
        conf["deadlineDate"] = (
            0.95 if date_grounded(fields.deadline_date, text) else 0.30
        )
    if fields.amount_owed is not None:
        conf["amountOwed"] = (
            0.95 if amount_grounded(fields.amount_owed, text) else 0.30
        )
    if fields.cited_section is not None:
        conf["citedSection"] = _score_text(fields.cited_section, text)
    if fields.required_action is not None:
        conf["requiredAction"] = _score_text(fields.required_action, text)
    return ExtractedFields(
        issuing_authority=fields.issuing_authority,
        deadline_date=fields.deadline_date,
        amount_owed=fields.amount_owed,
        cited_section=fields.cited_section,
        required_action=fields.required_action,
        field_confidence=conf,
    )
