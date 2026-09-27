"""Reviewer API-key auth (Task 4): 401 without header, 200 with correct header."""
from fastapi.testclient import TestClient

from notice_explainer.api import deps
from notice_explainer.domain.types import ReviewReason
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


def test_review_endpoints_require_key_when_configured(monkeypatch):
    monkeypatch.setenv("REVIEWER_API_KEY", "secret-123")
    client = _fresh_app()
    deps.review_queue.enqueue("job-xyz", ReviewReason.ESCALATION_FLAG_SET)

    # No header -> 401 on both endpoints.
    assert client.get("/api/v1/review/queue").status_code == 401
    assert client.post("/api/v1/review/job-xyz/resolve",
                       json={"decision": "approve"}).status_code == 401

    # Wrong key -> 401.
    assert client.get("/api/v1/review/queue",
                      headers={"X-Reviewer-Key": "wrong"}).status_code == 401

    # Correct key -> 200 on both.
    ok_queue = client.get("/api/v1/review/queue",
                          headers={"X-Reviewer-Key": "secret-123"})
    assert ok_queue.status_code == 200
    assert any(i["jobId"] == "job-xyz" for i in ok_queue.json())
    ok_resolve = client.post(
        "/api/v1/review/job-xyz/resolve",
        json={"decision": "approve"},
        headers={"X-Reviewer-Key": "secret-123"},
    )
    assert ok_resolve.status_code == 200
    assert ok_resolve.json()["jobId"] == "job-xyz"


def test_review_open_in_dev_without_key(monkeypatch):
    monkeypatch.delenv("REVIEWER_API_KEY", raising=False)
    client = _fresh_app()
    assert client.get("/api/v1/review/queue").status_code == 200
