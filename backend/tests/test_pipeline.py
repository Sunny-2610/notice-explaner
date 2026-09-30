"""Integration: LLD §5 branches via Fake AI + in-memory stores."""
import io

from fastapi.testclient import TestClient

from notice_explainer.api import deps
from notice_explainer.infrastructure.memory import (
    MemoryAuditLogger,
    MemoryImageStore,
    MemoryJobStore,
    MemoryReviewQueue,
)
from notice_explainer.main import create_app


def _fresh_app():
    deps.job_store = MemoryJobStore()
    deps.image_store = MemoryImageStore()
    deps.review_queue = MemoryReviewQueue()
    deps.audit = MemoryAuditLogger()
    return TestClient(create_app())


def _submit(client, payload: bytes, lang="hi"):
    return client.post(
        "/api/v1/documents",
        files={"image": ("notice.jpg", io.BytesIO(payload), "image/jpeg")},
        data={"targetLanguage": lang, "sessionId": "s1"},
    )


def test_happy_path_completed_with_disclaimer():
    client = _fresh_app()
    r = _submit(client, b"FAKE-JPEG-PROPERTY-TAX")
    assert r.status_code == 202
    job_id = r.json()["jobId"]
    import time
    for _ in range(50):
        g = client.get(f"/api/v1/documents/{job_id}").json()
        if g["status"] in ("completed", "awaiting_review", "failed"):
            break
        time.sleep(0.05)
    assert g["status"] == "completed", g
    assert g["disclaimerIncluded"] is True
    assert g["documentType"] == "property_tax_notice"
    assert g["escalation"]["flagged"] is False


def test_summons_escalates_to_review_twice_checked():
    client = _fresh_app()
    r = _submit(client, b"FAKE-JPEG-SUMMONS-COURT")
    job_id = r.json()["jobId"]
    import time
    for _ in range(50):
        g = client.get(f"/api/v1/documents/{job_id}").json()
        if g["status"] == "awaiting_review":
            break
        time.sleep(0.05)
    assert g["status"] == "awaiting_review"
    assert g["escalation"]["flagged"] is True
    q = client.get("/api/v1/review/queue").json()
    assert any(i["jobId"] == job_id for i in q)


def test_unsupported_short_circuits_E201():
    client = _fresh_app()
    r = _submit(client, b"FAKE-UNSUPPORTED-TEST")
    job_id = r.json()["jobId"]
    import time
    for _ in range(50):
        g = client.get(f"/api/v1/documents/{job_id}").json()
        if g["status"] == "awaiting_review":
            break
        time.sleep(0.05)
    assert g["status"] == "awaiting_review"
    assert g["errorCode"] == "E-201"


def test_submit_with_queue_enqueues_once_no_double_run(monkeypatch):
    """When a job_queue is configured, submit() must enqueue to Redis ONLY
    and must NOT schedule the inline BackgroundTasks _run (else the job is
    processed twice: once inline + once by worker.py)."""
    import notice_explainer.api.documents as documents

    client = _fresh_app()

    run_calls: list[str] = []
    enqueue_calls: list[str] = []

    def fake_run(job_id: str) -> None:
        run_calls.append(job_id)

    class FakeQueue:
        def enqueue(self, job_id: str) -> None:
            enqueue_calls.append(job_id)

    monkeypatch.setattr(documents, "_run", fake_run)
    monkeypatch.setattr(deps, "job_queue", FakeQueue())

    r = _submit(client, b"FAKE-JPEG-PROPERTY-TAX")
    assert r.status_code == 202
    job_id = r.json()["jobId"]

    # Exactly one processing path: the queue. Inline _run must not fire.
    assert enqueue_calls == [job_id]
    assert run_calls == []


def test_validation_400_on_bad_type_and_language():
    client = _fresh_app()
    bad = client.post(
        "/api/v1/documents",
        files={"image": ("n.pdf", io.BytesIO(b"x"), "application/pdf")},
        data={"targetLanguage": "hi", "sessionId": "s1"},
    )
    assert bad.status_code == 400
    bad_lang = _submit(client, b"FAKE-JPEG-PROPERTY-TAX", lang="fr")
    assert bad_lang.status_code == 400


def test_english_happy_path_completed_with_disclaimer():
    client = _fresh_app()
    r = _submit(client, b"FAKE-JPEG-PROPERTY-TAX", lang="en")
    assert r.status_code == 202
    job_id = r.json()["jobId"]
    import time
    for _ in range(50):
        g = client.get(f"/api/v1/documents/{job_id}").json()
        if g["status"] in ("completed", "awaiting_review", "failed"):
            break
        time.sleep(0.05)
    assert g["status"] == "completed", g
    assert g["disclaimerIncluded"] is True
    assert "not legal advice" in (g["explanation"] or "").lower()
