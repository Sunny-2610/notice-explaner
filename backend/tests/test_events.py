"""SSE job progress: status + result events, terminal close, 404 unknown."""
import io
import json
import time

from fastapi.testclient import TestClient

from notice_explainer.api import deps
from notice_explainer.infrastructure.memory import (
    MemoryAuditLogger,
    MemoryImageStore,
    MemoryJobStore,
    MemoryReviewQueue,
)
from notice_explainer.main import create_app


def _client():
    deps.job_store = MemoryJobStore()
    deps.image_store = MemoryImageStore()
    deps.review_queue = MemoryReviewQueue()
    deps.audit = MemoryAuditLogger()
    return TestClient(create_app())


def _submit(client, payload: bytes = b"FAKE-JPEG-PROPERTY-TAX"):
    r = client.post(
        "/api/v1/documents",
        files={"image": ("n.jpg", io.BytesIO(payload), "image/jpeg")},
        data={"targetLanguage": "hi", "sessionId": "s1"},
    )
    assert r.status_code == 202
    return r.json()["jobId"]


def _terminal_job(client):
    job_id = _submit(client)
    for _ in range(50):
        g = client.get(f"/api/v1/documents/{job_id}").json()
        if g["status"] in ("completed", "awaiting_review", "failed"):
            return job_id, g
        time.sleep(0.05)
    raise AssertionError(g)


def test_events_terminal_job_yields_status_and_result():
    client = _client()
    job_id, g = _terminal_job(client)
    r = client.get(f"/api/v1/documents/{job_id}/events")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    assert r.headers["Cache-Control"] == "no-cache"
    assert r.headers["X-Accel-Buffering"] == "no"
    body = r.text
    assert "event: status" in body
    assert "event: result" in body
    # Final result payload carries the full DocumentResult incl. deadline.
    result_block = body.split("event: result")[1]
    payload = json.loads(result_block.split("data:", 1)[1].strip())
    assert payload["jobId"] == job_id
    assert payload["status"] == g["status"]
    assert "deadline" in payload


def test_events_unknown_job_404():
    client = _client()
    assert client.get("/api/v1/documents/no-such-job/events").status_code == 404
