"""Bhashini translation + voice adapters (HLD §5, LLD §2.7).

Only constructed when BHASHINI_API_KEY is set. Any failure/timeout raises
so callers fall back to text-only with voiceAvailable=false (E-302) —
voice NEVER fails the job.

NOTE: the Bhashini auth/pipeline-config flow (endpoint URL, Authorization
header format, per-language ASR/TTS service-id discovery, audioFormat /
samplingRate fields) MUST be verified against the current official Bhashini
docs before any pilot — do not treat the payload shapes below as
authoritative, and never guess service ids (unset ids raise so callers
fall back to E-302).
"""
from __future__ import annotations

import os

import httpx

from ..domain.types import VOICE_TIMEOUT_S, VOICE_TTS_TIMEOUT_S

_URL = os.getenv("BHASHINI_URL", "https://dhruva-api.bhashini.gov.in/services/inference/pipeline")


def _headers() -> dict:
    key = os.getenv("BHASHINI_API_KEY", "")
    if not key:
        raise RuntimeError("BHASHINI_API_KEY not set")
    return {"Authorization": key, "Content-Type": "application/json"}


def _service_id(prefix: str, lang: str) -> str:
    """Env-configured Bhashini service id, e.g. BHASHINI_ASR_SERVICE_ID_HI.

    Raises when unset — never guess ids; callers fall back to E-302.
    """
    key = f"{prefix}_{lang.upper()}"
    sid = os.getenv(key, "")
    if not sid:
        raise RuntimeError(f"{key} not set — voice unavailable (E-302)")
    return sid


def _parse_asr_transcript(data: dict) -> str:
    try:
        return data["pipelineResponse"][0]["output"][0]["source"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            f"Unexpected Bhashini ASR response: {str(data)[:300]}"
        ) from exc


class BhashiniVoiceService:
    def speech_to_text(self, audio: bytes, lang: str) -> str:
        import base64
        service_id = _service_id("BHASHINI_ASR_SERVICE_ID", lang)
        payload = {
            "pipelineTasks": [{
                "taskType": "asr",
                "config": {
                    "language": {"sourceLanguage": lang},
                    "serviceId": service_id,
                    "audioFormat": "wav",
                    "samplingRate": 16000,
                },
            }],
            "inputData": {"audio": [{"audioContent": base64.b64encode(audio).decode()}]},
        }
        r = httpx.post(_URL, headers=_headers(), json=payload, timeout=VOICE_TIMEOUT_S)
        r.raise_for_status()
        return _parse_asr_transcript(r.json())

    def text_to_speech(self, text: str, lang: str) -> bytes:
        import base64
        service_id = _service_id("BHASHINI_TTS_SERVICE_ID", lang)
        payload = {
            "pipelineTasks": [{
                "taskType": "tts",
                "config": {
                    "language": {"sourceLanguage": lang},
                    "serviceId": service_id,
                },
            }],
            "inputData": {"input": [{"source": text}]},
        }
        r = httpx.post(_URL, headers=_headers(), json=payload, timeout=VOICE_TTS_TIMEOUT_S)
        r.raise_for_status()
        data = r.json()
        try:
            b64 = data["pipelineResponse"][0]["audio"][0]["audioContent"]
            return base64.b64decode(b64)
        except (KeyError, IndexError):
            return b""


def translate_text(text: str, target_language: str) -> str:
    """Pass-through unless Bhashini key is configured; LLM already targets hi/mr."""
    if not os.getenv("BHASHINI_API_KEY"):
        return text
    payload = {"pipelineTasks": [{"taskType": "translation",
                "config": {"language": {"sourceLanguage": "en", "targetLanguage": target_language}}}],
               "inputData": {"input": [{"source": text}]}}
    r = httpx.post(_URL, headers=_headers(), json=payload, timeout=VOICE_TIMEOUT_S)
    r.raise_for_status()
    data = r.json()
    try:
        return data["pipelineResponse"][0]["output"][0]["target"]
    except (KeyError, IndexError):
        return text
