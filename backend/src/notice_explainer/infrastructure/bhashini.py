"""Bhashini translation + voice adapters (HLD §5, LLD §2.7).

Only constructed when BHASHINI_API_KEY is set. Any failure/timeout raises
so callers fall back to text-only with voiceAvailable=false (E-302) —
voice NEVER fails the job.
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


class BhashiniVoiceService:
    def speech_to_text(self, audio: bytes, lang: str) -> str:
        import base64
        payload = {"pipelineTasks": [{"taskType": "asr", "config": {"language": {"sourceLanguage": lang}}}],
                   "inputData": {"audio": [{"audioContent": base64.b64encode(audio).decode()}]}}
        r = httpx.post(_URL, headers=_headers(), json=payload, timeout=VOICE_TIMEOUT_S)
        r.raise_for_status()
        return str(r.json())

    def text_to_speech(self, text: str, lang: str) -> bytes:
        import base64
        payload = {"pipelineTasks": [{"taskType": "tts", "config": {"language": {"sourceLanguage": lang}}}],
                   "inputData": {"input": [{"source": text}]}}
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
