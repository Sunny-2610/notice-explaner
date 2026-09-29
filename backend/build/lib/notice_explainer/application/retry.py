"""Retry helper for third-party AI calls (LLD §7).

Max 3 attempts, exponential backoff from 500ms, capped at 4s. Sync version;
an async variant can mirror this when the worker moves off the request path.
"""
from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from ..domain.types import (
    AI_MAX_ATTEMPTS,
    RETRY_BACKOFF_BASE_MS,
    RETRY_BACKOFF_CAP_MS,
)

T = TypeVar("T")


def run_with_retries(
    fn: Callable[[], T],
    attempts: int = AI_MAX_ATTEMPTS,
    base_ms: int = RETRY_BACKOFF_BASE_MS,
    cap_ms: int = RETRY_BACKOFF_CAP_MS,
) -> T:
    last_exc: BaseException | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — retried, then re-raised
            last_exc = exc
            if attempt < attempts - 1:
                delay_ms = min(base_ms * (2**attempt), cap_ms)
                if delay_ms > 0:
                    time.sleep(delay_ms / 1000.0)
    assert last_exc is not None
    raise last_exc
