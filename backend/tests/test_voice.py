"""Voice endpoints: never fail the job (E-302 text-only fallback)."""
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


def _client():
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
    job_id = r.json()["jobId"]
    for _ in range(50):
        g = client.get(f"/api/v1/documents/{job_id}").json()
        if g["status"] in ("completed", "awaiting_review", "failed"):
            break
        time.sleep(0.05)
    return job_id, g


class _StubVoice:
    """STT returns fixed text; TTS returns fixed bytes."""

    def __init__(self, transcript="रकम कितनी है?", audio=b""):
        self.transcript = transcript
        self.tts_audio = audio
        self.tts_texts: list[str] = []

    def speech_to_text(self, audio: bytes, lang: str) -> str:
        return self.transcript

    def text_to_speech(self, text: str, lang: str) -> bytes:
        self.tts_texts.append(text)
        return self.tts_audio


def test_voice_query_empty_transcript_is_unavailable():
    """FakeVoiceService returns '' -> E-302 fallback, not voiceAvailable true."""
    c = _client()
    job_id, _ = _completed_job(c)
    r = c.post(f"/api/v1/documents/{job_id}/voice-query",
               files={"audio": ("q.webm", io.BytesIO(b"fake-audio"), "audio/webm")},
               data={"lang": "hi"})
    assert r.status_code == 200
    body = r.json()
    assert body["jobId"] == job_id
    assert body["voiceAvailable"] is False
    assert body["code"] == "E-302"


def test_voice_query_happy_path_with_stub(monkeypatch):
    c = _client()
    job_id, _ = _completed_job(c)
    monkeypatch.setattr(deps, "voice_service", _StubVoice(transcript="रकम कितनी है?"))
    r = c.post(f"/api/v1/documents/{job_id}/voice-query",
               files={"audio": ("q.wav", io.BytesIO(b"fake-wav"), "audio/wav")},
               data={"lang": "hi"})
    assert r.status_code == 200
    body = r.json()
    assert body["transcription"] == "रकम कितनी है?"
    assert body["voiceAvailable"] is True


def test_voice_speech_fake_returns_204_text_only():
    c = _client()
    job_id, _ = _completed_job(c)
    r = c.post(f"/api/v1/documents/{job_id}/voice-speech", data={"lang": "hi"})
    assert r.status_code == 204  # FakeVoiceService has no audio: E-302 fallback


def test_voice_speech_custom_text_spoken(monkeypatch):
    c = _client()
    job_id, _ = _completed_job(c)
    stub = _StubVoice(audio=b"fake-mp3-bytes")
    monkeypatch.setattr(deps, "voice_service", stub)
    r = c.post(f"/api/v1/documents/{job_id}/voice-speech",
               data={"lang": "hi", "text": "नमस्ते, यह जवाब है।"})
    assert r.status_code == 200
    assert r.content == b"fake-mp3-bytes"
    assert stub.tts_texts == ["नमस्ते, यह जवाब है।"]


def test_voice_speech_text_too_long_400(monkeypatch):
    c = _client()
    job_id, _ = _completed_job(c)
    monkeypatch.setattr(deps, "voice_service", _StubVoice(audio=b"x"))
    r = c.post(f"/api/v1/documents/{job_id}/voice-speech",
               data={"lang": "hi", "text": "x" * 1501})
    assert r.status_code == 400


def test_voice_speech_unknown_job_404():
    c = _client()
    r = c.post("/api/v1/documents/no-such-job/voice-speech", data={"lang": "hi"})
    assert r.status_code == 404


def test_voice_ask_happy_path(monkeypatch):
    c = _client()
    job_id, g = _completed_job(c)
    assert g["status"] == "completed"
    monkeypatch.setattr(
        deps, "voice_service", _StubVoice(transcript="रकम कितनी है?"))
    r = c.post(f"/api/v1/documents/{job_id}/voice-ask",
               files={"audio": ("q.wav", io.BytesIO(b"fake-wav"), "audio/wav")},
               data={"lang": "hi"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["jobId"] == job_id
    assert body["transcription"] == "रकम कितनी है?"
    assert body["answer"].rstrip().endswith(DISCLAIMERS["hi"])
    assert body["disclaimerIncluded"] is True
    assert body["voiceAvailable"] is True


def test_voice_ask_empty_transcript_skips_agent(monkeypatch):
    """Empty STT -> E-302 and the Q&A agent is never called (no qa_ask audit)."""
    c = _client()
    job_id, _ = _completed_job(c)
    monkeypatch.setattr(deps, "voice_service", _StubVoice(transcript="   "))

    calls: list[str] = []
    real_agent = deps.qa_agent

    class _CountingAgent:
        def answer(self, **kwargs):
            calls.append(kwargs.get("question", ""))
            return real_agent.answer(**kwargs)

    monkeypatch.setattr(deps, "qa_agent", _CountingAgent())
    r = c.post(f"/api/v1/documents/{job_id}/voice-ask",
               files={"audio": ("q.wav", io.BytesIO(b"fake-wav"), "audio/wav")},
               data={"lang": "hi"})
    assert r.status_code == 200
    body = r.json()
    assert body["voiceAvailable"] is False
    assert body["code"] == "E-302"
    assert calls == []


def test_voice_ask_11th_question_rejected(monkeypatch):
    c = _client()
    job_id, _ = _completed_job(c)
    for i in range(10):
        r = c.post(f"/api/v1/documents/{job_id}/ask",
                   json={"question": f"सवाल {i}?"})
        assert r.status_code == 200, r.text
    monkeypatch.setattr(
        deps, "voice_service", _StubVoice(transcript="एक और सवाल?"))
    r = c.post(f"/api/v1/documents/{job_id}/voice-ask",
               files={"audio": ("q.wav", io.BytesIO(b"fake-wav"), "audio/wav")},
               data={"lang": "hi"})
    assert r.status_code == 400


def test_escalation_unchanged_after_voice_ask(monkeypatch):
    """CRITICAL: escalation flag is identical before and after voice-ask."""
    c = _client()
    job_id, g = _completed_job(c, payload=b"FAKE-JPEG-SUMMONS-COURT")
    assert g["escalation"]["flagged"] is True
    before = (g["escalation"]["flagged"], g["escalation"]["matchedRuleIds"])
    monkeypatch.setattr(
        deps, "voice_service", _StubVoice(transcript="समन का क्या मतलब है?"))
    r = c.post(f"/api/v1/documents/{job_id}/voice-ask",
               files={"audio": ("q.wav", io.BytesIO(b"fake-wav"), "audio/wav")},
               data={"lang": "hi"})
    assert r.status_code == 200, r.text
    after_g = c.get(f"/api/v1/documents/{job_id}").json()
    after = (after_g["escalation"]["flagged"], after_g["escalation"]["matchedRuleIds"])
    assert before == after


def test_health_reports_voice_enabled_flag():
    c = _client()
    body = c.get("/health").json()
    assert body["ok"] is True
    # Fake service in tests -> explicitly disabled.
    assert body["voiceEnabled"] is False
