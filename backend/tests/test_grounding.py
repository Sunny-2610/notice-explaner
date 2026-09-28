"""Grounding verifier: confidence reflects presence in extracted text."""
from notice_explainer.domain.grounding import (
    amount_grounded,
    date_grounded,
    ground_fields,
    normalize_digits,
    text_overlap,
)
from notice_explainer.domain.models import ExtractedFields
from notice_explainer.domain.types import DocumentType


def test_normalize_digits_devanagari():
    assert normalize_digits("४५००") == "4500"
    assert normalize_digits("Rs ४,५००") == "Rs 4,500"


def test_amount_grounded_indian_grouping():
    assert amount_grounded(100000.0, "Amount Rs 1,00,000 due soon.") is True
    assert amount_grounded(4500.0, "Amount Rs 4500. Due 2026-11-15.") is True


def test_amount_grounded_devanagari_numerals():
    assert amount_grounded(4500.0, "रक्कम ₹४५०० भरा.") is True


def test_amount_hallucinated_gets_low():
    assert amount_grounded(1500.0, "COURT SUMMONS: appear. No amount stated.") is False
    f = ExtractedFields(amount_owed=1500.0)
    g = ground_fields(f, "COURT SUMMONS: appear. No amount stated.")
    assert g.field_confidence["amountOwed"] == 0.30


def test_date_iso_format():
    assert date_grounded("2026-11-15", "Due 2026-11-15.") is True


def test_date_slash_dash_dot_formats():
    assert date_grounded("2026-11-15", "Due 15/11/2026.") is True
    assert date_grounded("2026-11-15", "Due 15-11-2026.") is True
    assert date_grounded("2026-11-15", "Due 15.11.2026.") is True
    assert date_grounded("2026-11-15", "Due 15/11/26.") is True


def test_date_english_month_name():
    assert date_grounded("2026-11-15", "Due 15 November 2026.") is True


def test_date_hindi_month_name():
    assert date_grounded("2026-11-15", "अंतिम तिथि 15 नवंबर 2026.") is True


def test_date_marathi_month_name():
    assert date_grounded("2026-11-15", "अंतिम तारीख 15 नोव्हेंबर 2026.") is True


def test_date_hallucinated_gets_low():
    assert date_grounded("2026-10-20", "COURT SUMMONS: appear soon.") is False
    f = ExtractedFields(deadline_date="2026-10-20")
    g = ground_fields(f, "COURT SUMMONS: appear soon.")
    assert g.field_confidence["deadlineDate"] == 0.30


def test_partial_authority_match_gets_mid():
    # "Municipal Corporation Ward Office" vs text missing "Ward" -> overlap >= 0.6
    f = ExtractedFields(issuing_authority="Municipal Corporation Ward Office")
    g = ground_fields(
        f, "MUNICIPAL CORPORATION office issued this. Pay within 30 days."
    )
    # tokens: municipal, corporation, ward, office -> 3/4 = 0.75 overlap -> 0.75
    assert g.field_confidence["issuingAuthority"] == 0.75


def test_exact_authority_match_gets_high():
    f = ExtractedFields(issuing_authority="Municipal Corporation")
    g = ground_fields(f, "MUNICIPAL CORPORATION property tax demand notice.")
    assert g.field_confidence["issuingAuthority"] == 0.95


def test_values_never_modified_and_nulls_omitted():
    f = ExtractedFields(
        issuing_authority="Municipal Corporation",
        deadline_date="2026-11-15",
        amount_owed=4500.0,
        cited_section=None,
        required_action="Pay at the ward office.",
    )
    text = "MUNICIPAL CORPORATION property tax demand notice. Amount Rs 4500."
    g = ground_fields(f, text)
    assert g.issuing_authority == "Municipal Corporation"
    assert g.deadline_date == "2026-11-15"
    assert g.amount_owed == 4500.0
    assert g.cited_section is None
    assert "citedSection" not in g.field_confidence
    assert set(g.field_confidence) == {
        "issuingAuthority", "deadlineDate", "amountOwed", "requiredAction",
    }
    assert f is not g


def test_text_overlap_devanagari_matras_stay_attached():
    # Full overlap -> 1.0
    assert text_overlap("न्यायालय समन", "न्यायालय समन जारी.") == 1.0
    # Partial -> ratio
    assert text_overlap("जिल्हा न्यायालय कार्यालय", "न्यायालय कार्यालय") == 2 / 3


def test_wrapper_with_fake_extractor_end_to_end():
    from notice_explainer.infrastructure.fake_ai import FakeFieldExtractor
    from notice_explainer.infrastructure.grounding import GroundedFieldExtractor

    wrapped = GroundedFieldExtractor(FakeFieldExtractor())
    assert wrapped.model_version == "fake-0.1+grounded"
    # Summons fixture invents amount/date not present in the raw text ->
    # legitimately low confidence after grounding.
    summons_text = "COURT SUMMONS: you are summoned to appear. Warrant may issue if ignored."
    out = wrapped.extract_fields(summons_text, DocumentType.TRAFFIC_CHALLAN_SUMMONS)
    assert out.amount_owed == 1500.0
    assert out.deadline_date == "2026-10-20"
    assert out.field_confidence["amountOwed"] == 0.30
    assert out.field_confidence["deadlineDate"] == 0.30
    # Property-tax fixture stays grounded high.
    tax_text = ("MUNICIPAL CORPORATION property tax demand notice. "
                "Amount Rs 4500. Due 2026-11-15 under Section 12A. "
                "Pay at ward office within 30 days.")
    out2 = wrapped.extract_fields(tax_text, DocumentType.PROPERTY_TAX_NOTICE)
    assert out2.field_confidence["amountOwed"] == 0.95
    assert out2.field_confidence["deadlineDate"] == 0.95
