"""Sarvam voice adapter: Saaras STT + Bulbul TTS (preferred voice provider).

Selected in api/deps.py when SARVAM_API_KEY is set (and USE_FAKE_AI is not
true). Bhashini stays as second choice, FakeVoiceService otherwise.

Implements the application VoiceService port (speech_to_text / text_to_speech)
so domain/application never know which provider is live. Any failure raises
so callers fall back to text-only E-302 — voice NEVER fails the job, and
quota/overload degrades to text instead of fake transcripts.

NOTE on model ids: verify against https://docs.sarvam.ai before piloting —
Saaras generations move fast (v2 -> v2.5 -> v3) and a renamed id 404s.
All three pins are env-overridable, so a model rename is a config edit
(.env / Render dashboard), never a code change or redeploy of logic.
"""
from __future__ import annotations

import base64
import os

import httpx

from ..domain.types import VOICE_TIMEOUT_S, VOICE_TTS_TIMEOUT_S

# App language code -> Sarvam BCP-47 code. Unknown languages raise (callers
# map that to E-302) — never guess a code and transcribe in the wrong tongue.
LANGUAGE_CODES = {"hi": "hi-IN", "mr": "mr-IN", "en": "en-IN"}

MAX_SPEECH_CHARS = 1500


def _chunk_size() -> int:
    # Live-verified 2026-10-01: bulbul:v3 rejects inputs.0 over 500 chars
    # with 400 ("String should have at most 500 characters"), so explanations
    # must be split and re-joined. Env-overridable if Sarvam raises the cap.
    try:
        return max(100, int(os.getenv("SARVAM_TTS_CHUNK_CHARS", "500")))
    except ValueError:
        return 500


def _chunks(text: str, limit: int) -> list[str]:
    """Split on sentence boundaries (Devanagari danda included) so no chunk
    exceeds `limit` chars. Over-long single sentences hard-split as fallback
    — a clipped word beats a 400 for the whole paragraph."""
    import re
    parts = [p.strip() for p in re.split(r"(?<=[।.!?\n])\s+", text.strip()) if p.strip()]
    out: list[str] = []
    for part in parts:
        if len(part) <= limit:
            out.append(part)
            continue
        for i in range(0, len(part), limit):
            piece = part[i:i + limit].strip()
            if piece:
                out.append(piece)
    return out


def _join_wavs(blobs: list[bytes]) -> bytes:
    """Concatenate WAV chunk payloads into one valid WAV (stdlib wave only).
    Chunks from one speaker/model share params; on any mismatch or parse
    failure return the first chunk rather than corrupt audio."""
    import io
    import wave
    if len(blobs) == 1:
        return blobs[0]
    try:
        readers = [wave.open(io.BytesIO(b), "rb") for b in blobs]
        params = readers[0].getparams()
        if any(r.getparams() != params for r in readers[1:]):
            return blobs[0]
        frames = b"".join(r.readframes(r.getnframes()) for r in readers)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setparams(params)
            w.writeframes(frames)
        return buf.getvalue()
    except (wave.Error, EOFError, ValueError):
        return blobs[0]


def _base_url() -> str:
    return os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai").rstrip("/")


def _key() -> str:
    key = os.getenv("SARVAM_API_KEY", "")
    if not key:
        raise RuntimeError("SARVAM_API_KEY not set")
    return key


def _headers() -> dict:
    # Sarvam auth scheme (distinct from Gemini's x-goog-api-key).
    return {"api-subscription-key": _key()}


def _language_code(lang: str) -> str:
    code = LANGUAGE_CODES.get((lang or "").lower())
    if not code:
        raise RuntimeError(f"Unsupported Sarvam voice language: {lang!r}")
    return code


def _parse_transcript(data: dict) -> str:
    # Saaras returns {"transcript": "..."}; tolerate list/dict variants so a
    # documented shape change degrades to E-302 instead of a KeyError crash.
    try:
        if isinstance(data.get("transcript"), str):
            return data["transcript"]
        transcripts = data.get("transcripts")
        if isinstance(transcripts, list) and transcripts:
            first = transcripts[0]
            if isinstance(first, str):
                return first
            if isinstance(first, dict) and isinstance(first.get("transcript"), str):
                return first["transcript"]
        if isinstance(data.get("text"), str):
            return data["text"]
    except (AttributeError, TypeError) as exc:
        raise RuntimeError(
            f"Unexpected Sarvam STT response: {str(data)[:300]}"
        ) from exc
    raise RuntimeError(f"Unexpected Sarvam STT response: {str(data)[:300]}")


class SarvamVoiceService:
    """Saaras speech-to-text + Bulbul text-to-speech over plain httpx.

    httpx (not the sarvamai SDK) keeps the Docker image lean and timeouts
    explicit. Audio in is 16k WAV (frontend converts via blobTo16kWav);
    audio out is WAV bytes — callers treat empty bytes as E-302.
    """

    def speech_to_text(self, audio: bytes, lang: str) -> str:
        if not audio:
            return ""
        code = _language_code(lang)
        # Live-verified 2026-10-01: the v3 STT id is "saaras:v3"
        # ("saarika:v3" 404s; the saarika:v* ids are the v1/v2 generation).
        model = os.getenv("SARVAM_STT_MODEL", "saaras:v3")
        r = httpx.post(
            f"{_base_url()}/speech-to-text",
            headers=_headers(),
            files={"file": ("audio.wav", audio, "audio/wav")},
            data={"model": model, "language_code": code},
            timeout=VOICE_TIMEOUT_S,
        )
        r.raise_for_status()
        # Empty transcript is not an error here — voice.py maps "" to E-302
        # (text-only continues). Only unparseable shapes raise.
        return _parse_transcript(r.json()).strip()

    def text_to_speech(self, text: str, lang: str) -> bytes:
        if not text or not text.strip():
            return b""
        code = _language_code(lang)
        # Fan-out over ≤500-char chunks: a single request 400s on any
        # real-length explanation. Any chunk failure raises so voice.py
        # degrades the whole clip to E-302 text-only (never partial audio).
        chunks = _chunks(text.strip()[:MAX_SPEECH_CHARS], _chunk_size())
        speaker = os.getenv("SARVAM_TTS_SPEAKER", "priya")
        model = os.getenv("SARVAM_TTS_MODEL", "bulbul:v3")
        headers = {**_headers(), "Content-Type": "application/json"}
        url = f"{_base_url()}/text-to-speech"

        def _one(piece: str) -> bytes:
            body = {
                "inputs": [piece],
                "target_language_code": code,
                # One fixed speaker per deployment builds user trust; exposing
                # 30+ voices is a product decision, not an adapter default.
                # (Verified against the live API: bulbul:v3 rejects retired v2
                # speakers like 'anushka' with 400 — the default here must stay
                # in the model's speaker list; override via SARVAM_TTS_SPEAKER.)
                "speaker": speaker,
                "model": model,
            }
            r = httpx.post(url, headers=headers, json=body, timeout=VOICE_TTS_TIMEOUT_S)
            r.raise_for_status()
            try:
                items = r.json().get("audios") or []
                if not items or not items[0]:
                    return b""
                return base64.b64decode(items[0])
            except (AttributeError, TypeError, ValueError):
                return b""

        # Parallel fan-out (order-preserving): sequential chunk synthesis
        # makes real explanations take 15-40s; parallel costs ~one chunk.
        # Any blank chunk degrades the whole clip to E-302 (never partial).
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(4, len(chunks))) as pool:
            out = list(pool.map(_one, chunks))
        if any(not blob for blob in out):
            return b""
        return _join_wavs(out)
