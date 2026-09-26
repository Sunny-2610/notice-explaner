"""Postgres adapters (LLD §3 tables). Lazy psycopg import — deps falls back
to memory when DATABASE_URL is unset or psycopg isn't installed (tests)."""
from __future__ import annotations

import json
import os


def _connect():
    import psycopg  # type: ignore[import-not-found]

    url = os.getenv("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg.connect(url, autocommit=True)


DDL = """
CREATE TABLE IF NOT EXISTS audit_log_entries (
  log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id TEXT NOT NULL, stage_name TEXT NOT NULL,
  input_ref JSONB, output_ref JSONB,
  model_version TEXT, prompt_version TEXT,
  created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE IF NOT EXISTS review_cases (
  job_id TEXT PRIMARY KEY, routed_reason TEXT NOT NULL,
  reviewer_id TEXT, decision TEXT, resolved_at TIMESTAMPTZ);
"""


class PostgresAuditLogger:
    def __init__(self) -> None:
        self._conn = _connect()
        with self._conn.cursor() as cur:
            cur.execute(DDL)

    def log_stage(self, job_id: str, stage: str, input_ref: dict, output_ref: dict,
                  model_version: str | None = None, prompt_version: str | None = None) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO audit_log_entries "
                "(job_id, stage_name, input_ref, output_ref, model_version, prompt_version) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (job_id, stage, json.dumps(input_ref or {}), json.dumps(output_ref or {}),
                 model_version, prompt_version))

    def entries_for(self, job_id: str) -> list:
        with self._conn.cursor() as cur:
            cur.execute("SELECT stage_name, input_ref, output_ref FROM audit_log_entries "
                        "WHERE job_id=%s ORDER BY created_at", (job_id,))
            return [{"stage": r[0], "input": r[1], "output": r[2]} for r in cur.fetchall()]
