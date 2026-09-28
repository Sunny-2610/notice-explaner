"""Bhashini adapter: ASR transcript parsing + no-guessed-ids fallback."""
import os

import notice_explainer.infrastructure.bhashini as bhashini_mod
from notice_explainer.infrastructure.bhashini import BhashiniVoiceService


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_asr_parses_pipeline_source(monkeypatch):
    monkeypatch.setenv("BHASHINI_API_KEY", "test-key")
    monkeypatch.setenv("BHASHINI_ASR_SERVICE_ID_HI", "asr-hi-test-id")
    seen = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        seen["body"] = json
        task = json["pipelineTasks"][0]
        assert task["taskType"] == "asr"
        assert task["config"]["audioFormat"] == "wav"
        assert task["config"]["samplingRate"] == 16000
        assert task["config"]["serviceId"] == "asr-hi-test-id"
        return _FakeResp({
            "pipelineResponse": [{"output": [{"source": "रकम कितनी है?"}]}]
        })

    monkeypatch.setattr(bhashini_mod.httpx, "post", fake_post)
    svc = BhashiniVoiceService()
    assert svc.speech_to_text(b"fake-wav-bytes", "hi") == "रकम कितनी है?"


def test_asr_missing_service_id_raises_for_fallback(monkeypatch):
    monkeypatch.setenv("BHASHINI_API_KEY", "test-key")
    monkeypatch.delenv("BHASHINI_ASR_SERVICE_ID_HI", raising=False)
    # Ensure the generic fallback (no key at all) also raises.
    if "BHASHINI_ASR_SERVICE_ID_HI" in os.environ:
        del os.environ["BHASHINI_ASR_SERVICE_ID_HI"]
    svc = BhashiniVoiceService()
    try:
        svc.speech_to_text(b"fake-wav-bytes", "hi")
    except RuntimeError:
        return
    raise AssertionError("expected RuntimeError when ASR service id is unset")


def test_asr_unexpected_shape_raises(monkeypatch):
    monkeypatch.setenv("BHASHINI_API_KEY", "test-key")
    monkeypatch.setenv("BHASHINI_ASR_SERVICE_ID_HI", "asr-hi-test-id")

    def fake_post(url, headers=None, json=None, timeout=None):
        return _FakeResp({"pipelineResponse": []})

    monkeypatch.setattr(bhashini_mod.httpx, "post", fake_post)
    svc = BhashiniVoiceService()
    try:
        svc.speech_to_text(b"fake-wav-bytes", "hi")
    except RuntimeError:
        return
    raise AssertionError("expected RuntimeError on unparseable ASR response")
