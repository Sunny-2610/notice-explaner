"""Voice endpoints: never fail the job (E-302 text-only fallback)."""
import io
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


def _completed_job(client):
    r = client.post(
        "/api/v1/documents",
        files={"image": ("n.jpg", io.BytesIO(b"FAKE-JPEG-PROPERTY-TAX"), "image/jpeg")},
        data={"targetLanguage": "hi", "sessionId": "s1"})
    job_id = r.json()["jobId"]
    for _ in range(50):
        if client.get(f"/api/v1/documents/{job_id}").json()["status"] == "completed":
            break
        time.sleep(0.05)
    return job_id


def test_voice_query_returns_transcription_or_fallback():
    c = _client()
    job_id = _completed_job(c)
    r = c.post(f"/api/v1/documents/{job_id}/voice-query",
               files={"audio": ("q.webm", io.BytesIO(b"fake-audio"), "audio/webm")},
               data={"lang": "hi"})
    assert r.status_code == 200
    body = r.json()
    assert body["jobId"] == job_id and "voiceAvailable" in body


def test_voice_speech_fake_returns_204_text_only():
    c = _client()
    job_id = _completed_job(c)
    r = c.post(f"/api/v1/documents/{job_id}/voice-speech", data={"lang": "hi"})
    assert r.status_code == 204  # FakeVoiceService has no audio: E-302 fallback
