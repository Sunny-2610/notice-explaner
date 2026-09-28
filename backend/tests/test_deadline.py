"""Deadline math, checklist safety, .ics structure."""
from datetime import date

from notice_explainer.domain.checklist import checklist_for
from notice_explainer.domain.deadline import days_remaining

BANNED = [
    "no need", "don't need a lawyer", "dont need a lawyer", "guarantee",
    "वकील की जरूरत नहीं", "वकील नहीं चाहिए", "गारंटी",
    "वकिलाची गरज नाही", "वकील नको", "हमी",
]


def test_days_remaining_math():
    assert days_remaining("2026-11-15", date(2026, 11, 10)) == 5
    assert days_remaining("2026-11-15", date(2026, 11, 15)) == 0
    assert days_remaining("2026-11-15", date(2026, 11, 20)) == -5


def test_days_remaining_unparseable_none():
    assert days_remaining("not-a-date", date(2026, 11, 10)) is None
    assert days_remaining("", date(2026, 11, 10)) is None
    assert days_remaining(None, date(2026, 11, 10)) is None  # type: ignore[arg-type]


def test_checklist_lengths_and_safety():
    for dtype in ("property_tax_notice", "traffic_challan_summons", "bank_recovery_notice"):
        for lang in ("en", "hi", "mr"):
            items = checklist_for(dtype, lang)
            assert 4 <= len(items) <= 6
            blob = " ".join(items).lower()
            for banned in BANNED:
                assert banned.lower() not in blob, (dtype, lang, banned)


def _fresh_client():
    import io  # noqa: F401
    from fastapi.testclient import TestClient
    from notice_explainer.api import deps
    from notice_explainer.infrastructure.memory import (
        MemoryAuditLogger, MemoryImageStore, MemoryJobStore, MemoryReviewQueue,
    )
    from notice_explainer.main import create_app

    deps.job_store = MemoryJobStore()
    deps.image_store = MemoryImageStore()
    deps.review_queue = MemoryReviewQueue()
    deps.audit = MemoryAuditLogger()
    return TestClient(create_app())


def _submit_and_wait(client, payload: bytes, lang="hi"):
    import io, time
    r = client.post(
        "/api/v1/documents",
        files={"image": ("notice.jpg", io.BytesIO(payload), "image/jpeg")},
        data={"targetLanguage": lang, "sessionId": "s1"},
    )
    assert r.status_code == 202
    job_id = r.json()["jobId"]
    for _ in range(50):
        g = client.get(f"/api/v1/documents/{job_id}").json()
        if g["status"] in ("completed", "awaiting_review", "failed"):
            return job_id, g
        time.sleep(0.05)
    raise AssertionError(g)


def test_get_result_has_deadline_and_checklist():
    client = _fresh_client()
    job_id, g = _submit_and_wait(client, b"FAKE-JPEG-PROPERTY-TAX")
    assert g["status"] == "completed"
    assert g["deadline"] is not None
    assert isinstance(g["deadline"]["daysRemaining"], int)
    assert isinstance(g["deadline"]["overdue"], bool)
    assert 4 <= len(g["deadline"]["checklist"]) <= 6


def test_ics_structure_alarms_uid():
    client = _fresh_client()
    job_id, g = _submit_and_wait(client, b"FAKE-JPEG-PROPERTY-TAX")
    r = client.get(f"/api/v1/documents/{job_id}/reminder.ics")
    assert r.status_code == 200, r.text[:300]
    assert r.headers["content-type"].startswith("text/calendar")
    assert "notice-deadline.ics" in r.headers.get("content-disposition", "")
    body = r.text
    assert "\r\n" in body
    assert f"UID:{job_id}@yojana-mitra" in body
    assert "DTSTART;VALUE=DATE:20261115" in body
    for trigger in ("TRIGGER:-P6DT15H", "TRIGGER:-P2DT15H", "TRIGGER:-PT15H"):
        assert trigger in body
    assert body.count("BEGIN:VALARM") == 3
    # Folding: at least one continuation line exists for the long description.
    assert "\r\n " in body


def test_ics_404_unknown_job_and_no_deadline():
    client = _fresh_client()
    assert client.get("/api/v1/documents/nope/reminder.ics").status_code == 404
    # Unsupported doc has no deadline -> 404.
    import io, time
    r = client.post(
        "/api/v1/documents",
        files={"image": ("n.jpg", io.BytesIO(b"FAKE-UNSUPPORTED-TEST"), "image/jpeg")},
        data={"targetLanguage": "hi", "sessionId": "s1"},
    )
    job_id = r.json()["jobId"]
    for _ in range(50):
        g = client.get(f"/api/v1/documents/{job_id}").json()
        if g["status"] == "awaiting_review":
            break
        time.sleep(0.05)
    assert client.get(f"/api/v1/documents/{job_id}/reminder.ics").status_code == 404
