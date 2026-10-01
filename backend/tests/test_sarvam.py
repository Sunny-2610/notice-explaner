"""Sarvam adapter: STT/TTS wiring, lang mapping, and raise-for-E-302 paths."""
import base64

import notice_explainer.infrastructure.sarvam as sarvam_mod
from notice_explainer.infrastructure.sarvam import SarvamVoiceService


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_stt_posts_wav_with_model_and_lang(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "test-key")
    seen = {}

    def fake_post(url, headers=None, files=None, data=None, timeout=None):
        seen["url"] = url
        seen["headers"] = headers
        seen["files"] = files
        seen["data"] = data
        assert url.endswith("/speech-to-text")
        assert headers["api-subscription-key"] == "test-key"
        assert files["file"][1] == b"fake-wav-bytes"
        assert data["language_code"] == "hi-IN"
        return _FakeResp({"transcript": "रकम कितनी है?"})

    monkeypatch.setattr(sarvam_mod.httpx, "post", fake_post)
    svc = SarvamVoiceService()
    assert svc.speech_to_text(b"fake-wav-bytes", "hi") == "रकम कितनी है?"


def test_stt_marathi_and_english_codes(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "test-key")
    codes = []

    def fake_post(url, headers=None, files=None, data=None, timeout=None):
        codes.append(data["language_code"])
        return _FakeResp({"transcript": "ok"})

    monkeypatch.setattr(sarvam_mod.httpx, "post", fake_post)
    svc = SarvamVoiceService()
    svc.speech_to_text(b"x", "mr")
    svc.speech_to_text(b"x", "en")
    assert codes == ["mr-IN", "en-IN"]


def test_stt_missing_key_raises_for_fallback(monkeypatch):
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    svc = SarvamVoiceService()
    try:
        svc.speech_to_text(b"x", "hi")
    except RuntimeError:
        return
    raise AssertionError("expected RuntimeError without SARVAM_API_KEY")


def test_stt_unknown_language_raises_not_guesses(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "test-key")
    svc = SarvamVoiceService()
    try:
        svc.speech_to_text(b"x", "xx")
    except RuntimeError:
        return
    raise AssertionError("expected RuntimeError for unknown language")


def test_stt_unexpected_shape_raises(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "test-key")

    def fake_post(url, headers=None, files=None, data=None, timeout=None):
        return _FakeResp({"nope": []})

    monkeypatch.setattr(sarvam_mod.httpx, "post", fake_post)
    svc = SarvamVoiceService()
    try:
        svc.speech_to_text(b"x", "hi")
    except RuntimeError:
        return
    raise AssertionError("expected RuntimeError on unparseable STT response")


def test_tts_posts_inputs_and_decodes_audio(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "test-key")
    monkeypatch.setenv("SARVAM_TTS_SPEAKER", "priya")
    seen = {}
    wav = base64.b64encode(b"fake-wav").decode()

    def fake_post(url, headers=None, json=None, timeout=None):
        seen["url"] = url
        seen["body"] = json
        assert url.endswith("/text-to-speech")
        assert json["target_language_code"] == "hi-IN"
        assert json["speaker"] == "priya"
        assert json["inputs"] == ["नमस्ते"]
        return _FakeResp({"audios": [wav]})

    monkeypatch.setattr(sarvam_mod.httpx, "post", fake_post)
    svc = SarvamVoiceService()
    assert svc.text_to_speech("नमस्ते", "hi") == b"fake-wav"


def test_tts_empty_audio_returns_blank_for_204_path(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "test-key")

    def fake_post(url, headers=None, json=None, timeout=None):
        return _FakeResp({"audios": []})

    monkeypatch.setattr(sarvam_mod.httpx, "post", fake_post)
    svc = SarvamVoiceService()
    assert svc.text_to_speech("नमस्ते", "hi") == b""
    assert svc.text_to_speech("   ", "hi") == b""


def _wav_bytes(frames: bytes = b"\x00\x00" * 100) -> bytes:
    import io
    import wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(frames)
    return buf.getvalue()


def test_tts_long_text_chunks_and_joins_valid_wav(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "test-key")
    import base64 as _b64
    import io as _io
    import wave as _wave
    calls = []
    chunk_wav = _wav_bytes()

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append(json["inputs"][0])
        assert len(json["inputs"][0]) <= 500
        return _FakeResp({"audios": [_b64.b64encode(chunk_wav).decode()]})

    monkeypatch.setattr(sarvam_mod.httpx, "post", fake_post)
    svc = SarvamVoiceService()
    long_text = ("पहला वाक्य। दूसरा वाक्य। तीसरा वाक्य। " * 30).strip()
    out = svc.text_to_speech(long_text, "hi")
    assert len(calls) > 1  # actually fanned out, not truncated
    with _wave.open(_io.BytesIO(out), "rb") as w:  # still one valid WAV
        assert w.getnchannels() == 1 and w.getframerate() == 16000
        assert w.getnframes() == 100 * len(calls)


def test_chunks_split_on_danda():
    from notice_explainer.infrastructure.sarvam import _chunks
    parts = _chunks("पहला। दूसरा।", 500)
    assert parts == ["पहला।", "दूसरा।"]


def test_join_single_passthrough_and_mismatch_fallback():
    from notice_explainer.infrastructure.sarvam import _join_wavs
    one = _wav_bytes()
    assert _join_wavs([one]) == one
    assert _join_wavs([one, b"not-a-wav"]) == one
