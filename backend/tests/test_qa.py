"""Follow-up Q&A endpoint tests (ADR 0003). All use FakeQAAgent — no API calls."""
import io
import time

from fastapi.testclient import TestClient

from notice_explainer.api import deps
from notice_explainer.infrastructure.agent_tools import DISCLAIMERS
from notice_explainer.infrastructure.fake_ai import FakeQAAgent
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
    deps.qa_agent = FakeQAAgent()
    return TestClient(create_app())


def _completed_job(client, payload=b"FAKE-JPEG-PROPERTY-TAX", lang="hi"):
    r = client.post(
        "/api/v1/documents",
        files={"image": ("n.jpg", io.BytesIO(payload), "image/jpeg")},
        data={"targetLanguage": lang, "sessionId": "s1"})
    assert r.status_code == 202
    job_id = r.json()["jobId"]
    for _ in range(50):
        g = client.get(f"/api/v1/documents/{job_id}").json()
        if g["status"] in ("completed", "awaiting_review", "failed"):
            break
        time.sleep(0.05)
    return job_id, g


def _ask(client, job_id, question):
    return client.post(f"/api/v1/documents/{job_id}/ask", json={"question": question})


def test_valid_question_returns_answer_with_disclaimer():
    """Happy path: answer ends with disclaimer."""
    client = _fresh_app()
    job_id, g = _completed_job(client)
    assert g["status"] == "completed"
    r = _ask(client, job_id, "अगर मैं इसे नजरअंदाज कर दूं तो क्या होगा?")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["jobId"] == job_id
    assert body["disclaimerIncluded"] is True
    assert body["answer"].rstrip().endswith(DISCLAIMERS["hi"])


def test_out_of_scope_question_refused():
    """Out-of-scope question is politely refused."""
    client = _fresh_app()
    job_id, _ = _completed_job(client)
    r = _ask(client, job_id, "What is the weather today?")
    assert r.status_code == 200, r.text
    assert "केवल इस नोटिस" in r.json()["answer"]


def test_missing_job_returns_404():
    """Unknown jobId returns 404."""
    client = _fresh_app()
    r = _ask(client, "no-such-job", "यह क्या है?")
    assert r.status_code == 404


def test_empty_question_returns_400():
    """Empty question returns 400."""
    client = _fresh_app()
    job_id, _ = _completed_job(client)
    r = _ask(client, job_id, "   ")
    assert r.status_code == 400


def test_escalation_unchanged_after_qa():
    """CRITICAL: escalation flag is identical before and after Q&A."""
    client = _fresh_app()
    job_id, g = _completed_job(client, payload=b"FAKE-JPEG-SUMMONS-COURT")
    assert g["escalation"]["flagged"] is True
    before = (g["escalation"]["flagged"], g["escalation"]["matchedRuleIds"])
    r = _ask(client, job_id, "समन का क्या मतलब है?")
    assert r.status_code == 200, r.text
    after_g = client.get(f"/api/v1/documents/{job_id}").json()
    after = (after_g["escalation"]["flagged"], after_g["escalation"]["matchedRuleIds"])
    assert before == after
