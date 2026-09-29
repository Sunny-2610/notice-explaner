"""Redis job queue (HLD §3.3). Lazy redis import — falls back to inline
BackgroundTasks execution when REDIS_URL is unset (default for demo)."""
from __future__ import annotations

import os


class RedisJobQueue:
    def __init__(self, url: str = "") -> None:
        import redis  # type: ignore[import-not-found]

        self._r = redis.Redis.from_url(url or os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        self._key = "notice:jobs"

    def enqueue(self, job_id: str) -> None:
        self._r.lpush(self._key, job_id)

    def dequeue(self, timeout: int = 5) -> str | None:
        item = self._r.brpop(self._key, timeout=timeout)
        return item[1].decode() if item else None
