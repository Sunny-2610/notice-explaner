"""Legal-corpus retrieval (ADR 0004).

KeywordRetriever (pure-Python BM25-style, Devanagari-safe tokenizer) is the
default/offline adapter. GeminiEmbeddingRetriever (REST + httpx, pure-Python
cosine, disk-cached embeddings) is used only when a Gemini key is set.

Review gate: chunks with reviewed:false are excluded unless
CORPUS_ALLOW_UNREVIEWED=true. Active vs gated counts are logged at load.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
from pathlib import Path

import yaml

from ..domain.models import CorpusChunk

logger = logging.getLogger(__name__)

_BASE = Path(__file__).resolve().parents[3]
DEFAULT_CORPUS_DIR = _BASE / "data" / "corpus"
DEFAULT_CACHE_DIR = _BASE / ".cache"

# Same split rule as domain/grounding: whitespace + punctuation incl. danda,
# never \w, so Devanagari matras stay attached.
_SPLIT_RE = re.compile(r'[\s,.;:!?()\[\]{}"\'\-—–/\\|।॥]+', re.UNICODE)


def _tokenize(s: str) -> list[str]:
    return [t for t in _SPLIT_RE.split(s.lower()) if t]


def load_corpus(corpus_dir: str | Path = DEFAULT_CORPUS_DIR) -> tuple[list[CorpusChunk], list[CorpusChunk]]:
    """Return (active, gated) chunks honoring the review gate."""
    allow = os.getenv("CORPUS_ALLOW_UNREVIEWED", "false").lower() in ("1", "true", "yes")
    active: list[CorpusChunk] = []
    gated: list[CorpusChunk] = []
    for path in sorted(Path(corpus_dir).glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta: dict = {}
        body = raw
        if raw.startswith("---"):
            parts = raw.split("---", 2)
            if len(parts) == 3:
                meta = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
        chunk = CorpusChunk(
            id=str(meta.get("id", path.stem)),
            title=str(meta.get("title", path.stem)),
            lang=str(meta.get("lang", "en")),
            text=body,
            source_url=meta.get("source_url"),
            reviewed=bool(meta.get("reviewed", False)),
        )
        if chunk.reviewed or allow:
            active.append(chunk)
        else:
            gated.append(chunk)
    logger.info("corpus: %d active, %d gated (reviewed:false)", len(active), len(gated))
    return active, gated


class KeywordRetriever:
    """BM25-style keyword search over active corpus chunks."""

    def __init__(
        self,
        corpus_dir: str | Path = DEFAULT_CORPUS_DIR,
        chunks: list[CorpusChunk] | None = None,
    ) -> None:
        if chunks is not None:
            self._chunks = list(chunks)
            self._gated = 0
        else:
            self._chunks, gated = load_corpus(corpus_dir)
            self._gated = len(gated)
        logger.info("keyword retriever: %d active chunks (%d gated)",
                    len(self._chunks), self._gated)

    @property
    def active_count(self) -> int:
        return len(self._chunks)

    def search(self, query: str, top_k: int = 3) -> list[CorpusChunk]:
        qtokens = _tokenize(query)
        if not qtokens or not self._chunks:
            return []
        uniq = set(qtokens)
        scored: list[tuple[float, CorpusChunk]] = []
        for chunk in self._chunks:
            title_toks = _tokenize(chunk.title)
            text_toks = _tokenize(chunk.text)
            title_set = set(title_toks)
            text_set = set(text_toks)
            hits = sum(
                2.0 if t in title_set else (1.0 if t in text_set else 0.0)
                for t in uniq
            )
            if hits > 0:
                scored.append((hits / len(uniq), chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [c for _, c in scored[:top_k]]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


class GeminiEmbeddingRetriever:
    """Gemini text embeddings over REST; vectors cached on disk by chunk hash."""

    def __init__(
        self,
        corpus_dir: str | Path = DEFAULT_CORPUS_DIR,
        model: str | None = None,
        cache_dir: str | Path = DEFAULT_CACHE_DIR,
    ) -> None:
        self.model = model or os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
        self.cache_dir = Path(cache_dir)
        self._chunks, gated = load_corpus(corpus_dir)
        self._gated = len(gated)
        self._vecs: dict[str, list[float]] = {}
        logger.info("embedding retriever (%s): %d active chunks (%d gated)",
                    self.model, len(self._chunks), self._gated)

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _cache_path(self) -> Path:
        return self.cache_dir / "corpus_embeddings.json"

    def _load_cache(self) -> dict:
        try:
            return json.loads(self._cache_path().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save_cache(self, cache: dict) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_path().write_text(json.dumps(cache), encoding="utf-8")

    def _embed(self, text: str) -> list[float]:
        import httpx

        key = os.getenv("GEMINI_API_KEY", "")
        if not key:
            raise RuntimeError("GEMINI_API_KEY not set")
        cache = self._load_cache()
        h = "q:" + self._hash(text)
        if h in cache:
            return cache[h]
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.model}:embedContent")
        r = httpx.post(
            url, json={"content": {"parts": [{"text": text[:4000]}]}}, headers={"x-goog-api-key": key}, timeout=8)
        r.raise_for_status()
        values = r.json()["embedding"]["values"]
        cache[h] = values
        self._save_cache(cache)
        return values

    def _chunk_vec(self, chunk: CorpusChunk) -> list[float]:
        key = self._hash(chunk.id + "\n" + chunk.text)
        if key not in self._vecs:
            cache = self._load_cache()
            if key not in cache:
                cache[key] = self._embed(f"{chunk.title}\n{chunk.text}")
                self._save_cache(cache)
            self._vecs[key] = cache[key]
        return self._vecs[key]

    def search(self, query: str, top_k: int = 3) -> list[CorpusChunk]:
        if not query.strip() or not self._chunks:
            return []
        qvec = self._embed(query)
        scored = sorted(
            ((_cosine(qvec, self._chunk_vec(c)), c) for c in self._chunks),
            key=lambda item: item[0], reverse=True)
        return [c for s, c in scored[:top_k] if s > 0.0]


def build_default_retriever():
    """Keyword default; embeddings only with a real Gemini key in real mode."""
    use_fake = os.getenv("USE_FAKE_AI", "true").lower() in ("1", "true", "yes")
    if os.getenv("GEMINI_API_KEY") and not use_fake:
        try:
            return GeminiEmbeddingRetriever()
        except Exception as exc:
            logger.warning("embedding retriever unavailable, keyword fallback: %s", exc)
    return KeywordRetriever()
