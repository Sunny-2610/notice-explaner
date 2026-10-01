"""Standalone worker for compose deployments (LLD §5).

Demo/dev path runs jobs inline via FastAPI BackgroundTasks. When REDIS_URL
is set, the API enqueues job ids and this worker dequeues them instead:
  python -m notice_explainer.worker

One process = one job at a time (blocking brpop loop); scale by running
more worker processes. A crash never loses the audit trail — each stage
persists idempotently by job_id, so a restarted worker resumes cleanly.
"""
from __future__ import annotations

import os
import time

from .api import deps
from .application.use_cases.process_job import process_job


def run_forever() -> None:
    from .infrastructure.redis_queue import RedisJobQueue

    q = RedisJobQueue()
    print("worker: listening on redis queue notice:jobs")
    while True:
        job_id = q.dequeue(timeout=5)
        if not job_id:
            continue
        try:
            process_job(
                job_id, job_store=deps.job_store, image_store=deps.image_store,
                review_queue=deps.review_queue, audit=deps.audit,
                extractor=deps.extractor, classifier=deps.classifier,
                field_extractor=deps.field_extractor,
                explanation_gen=deps.explanation_gen,
                escalation_eval=deps.escalation_eval)
        except Exception as exc:  # never crash the loop
            print(f"worker: job {job_id} failed: {exc}")


if __name__ == "__main__" and os.getenv("REDIS_URL"):
    while True:
        try:
            run_forever()
        except Exception as exc:
            print(f"worker: redis unavailable ({exc}), retrying in 5s")
            time.sleep(5)
