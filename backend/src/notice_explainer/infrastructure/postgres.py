"""Postgres adapters (LLD §3 tables). Lazy psycopg import — deps falls back
to memory when DATABASE_URL is unset or psycopg isn't installed (tests).

Job state uses a single JSONB ``job_states`` row per job (explicitly allowed
as the simpler alternative to one-table-per-stage). ``get_result()`` returns
byte-identical keys to ``MemoryJobStore.get_result()`` since api/documents.py
and schemas.py depend on those exact keys.
"""
from __future__ import annotations

import json
import os
import threading


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
CREATE TABLE IF NOT EXISTS job_states (
  job_id TEXT PRIMARY KEY,
  state JSONB NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE IF NOT EXISTS job_images (
  job_id TEXT PRIMARY KEY,
  image BYTEA NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now());
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


def _job_to_json(job) -> dict:
    return {
        "job_id": job.job_id,
        "session_id": job.session_id,
        "target_language": job.target_language,
        "status": job.status.value,
        "error_code": job.error_code,
        "submitted_at": job.submitted_at.isoformat() if job.submitted_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


def _extraction_to_json(r) -> dict:
    return {"text": r.text, "confidence": r.confidence,
            "provider": r.provider, "duration_ms": r.duration_ms}


def _classification_to_json(r) -> dict:
    return {"document_type": r.document_type.value, "confidence": r.confidence}


def _fields_to_json(f) -> dict:
    return {"issuing_authority": f.issuing_authority, "deadline_date": f.deadline_date,
            "amount_owed": f.amount_owed, "cited_section": f.cited_section,
            "required_action": f.required_action,
            "field_confidence": dict(f.field_confidence or {})}


def _escalation_to_json(r) -> dict:
    return {"escalate": r.escalate, "matched_rule_ids": list(r.matched_rule_ids or []),
            "stage": r.stage.value, "rules_version": r.rules_version}


def _explanation_to_json(r) -> dict:
    return {"explanation_text": r.explanation_text,
            "disclaimer_included": r.disclaimer_included,
            "escalation_notice_included": r.escalation_notice_included}


class _ExtractionsView:
    """Dict-like ``.get(job_id)`` shim so application code written against
    ``MemoryJobStore.extractions`` keeps working (see answer_question.py)."""

    def __init__(self, store: PostgresJobStore) -> None:
        self._store = store

    def get(self, job_id: str, default=None):
        try:
            state = self._store._load_state(job_id)
        except Exception:
            return default
        raw = (state.get("extraction") or None) if state else None
        if raw is None:
            return default
        from ..domain.models import ExtractionResult

        return ExtractionResult(text=raw.get("text", ""), confidence=raw.get("confidence", 0.0),
                                provider=raw.get("provider", ""),
                                duration_ms=raw.get("duration_ms", 0))


class _ExplanationsView:
    """Supports ``job_id in store.explanations`` reads for compat with the
    review endpoint's pre-refactor access pattern. Mutations go through
    ``PostgresJobStore.update_explanation_text`` (which review.py prefers)."""

    def __init__(self, store: PostgresJobStore) -> None:
        self._store = store

    def __contains__(self, job_id: object) -> bool:
        if not isinstance(job_id, str):
            return False
        try:
            state = self._store._load_state(job_id)
        except Exception:
            return False
        return bool(state and state.get("explanation"))

    def __getitem__(self, job_id: str):
        result = self._store._load_explanation(job_id)
        if result is None:
            raise KeyError(job_id)
        return result

    def get(self, job_id: str, default=None):
        try:
            result = self._store._load_explanation(job_id)
        except Exception:
            return default
        return result if result is not None else default


class PostgresJobStore:
    """Persisted mirror of MemoryJobStore (single JSONB row per job)."""

    def __init__(self) -> None:
        self._conn = _connect()
        self._lock = threading.Lock()
        with self._conn.cursor() as cur:
            cur.execute(DDL)
        self.extractions = _ExtractionsView(self)
        self.explanations = _ExplanationsView(self)

    # -- internal helpers -------------------------------------------------
    def _load_state(self, job_id: str) -> dict | None:
        with self._lock:
            with self._conn.cursor() as cur:
                cur.execute("SELECT state FROM job_states WHERE job_id=%s", (job_id,))
                row = cur.fetchone()
        if not row:
            return None
        state = row[0]
        if isinstance(state, str):
            return json.loads(state)
        return dict(state)

    def _upsert_state(self, job_id: str, state: dict) -> None:
        with self._lock:
            with self._conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO job_states (job_id, state, updated_at) "
                    "VALUES (%s, %s, now()) "
                    "ON CONFLICT (job_id) DO UPDATE SET state=EXCLUDED.state, "
                    "updated_at=now()",
                    (job_id, json.dumps(state)))

    def _mutate_state(self, job_id: str, fn) -> None:
        state = self._load_state(job_id) or {}
        fn(state)
        self._upsert_state(job_id, state)

    def _load_explanation(self, job_id: str):
        from ..domain.models import ExplanationResult

        state = self._load_state(job_id)
        raw = (state.get("explanation") or None) if state else None
        if raw is None:
            return None
        return ExplanationResult(
            explanation_text=raw.get("explanation_text", ""),
            disclaimer_included=bool(raw.get("disclaimer_included", True)),
            escalation_notice_included=bool(raw.get("escalation_notice_included", False)))

    # -- MemoryJobStore interface ----------------------------------------
    def create_job(self, job) -> None:
        self._upsert_state(job.job_id, {"job": _job_to_json(job), "explanation_lang": None})

    def get_job(self, job_id: str):
        from ..domain.models import Job
        from ..domain.types import JobStatus

        state = self._load_state(job_id)
        if not state or not state.get("job"):
            return None
        raw = state["job"]
        from datetime import datetime

        def _parse(ts):
            return datetime.fromisoformat(ts) if ts else None

        return Job(job_id=raw["job_id"], session_id=raw.get("session_id", ""),
                   target_language=raw.get("target_language", ""),
                   status=JobStatus(raw.get("status", "queued")),
                   error_code=raw.get("error_code"),
                   submitted_at=_parse(raw.get("submitted_at")) or _parse("2000-01-01T00:00:00+00:00"),
                   completed_at=_parse(raw.get("completed_at")))

    def set_status(self, job_id: str, status, error_code: str | None = None) -> None:
        def _mut(state: dict) -> None:
            job = state.setdefault("job", {"job_id": job_id})
            job["status"] = status.value
            job["error_code"] = error_code
        try:
            self._mutate_state(job_id, _mut)
        except Exception:
            pass  # never fail the pipeline on a persistence hiccup

    def save_extraction(self, job_id: str, result) -> None:
        self._mutate_state(job_id, lambda s: s.update(extraction=_extraction_to_json(result)))

    def save_classification(self, job_id: str, result) -> None:
        self._mutate_state(job_id, lambda s: s.update(classification=_classification_to_json(result)))

    def save_fields(self, job_id: str, fields) -> None:
        self._mutate_state(job_id, lambda s: s.update(fields=_fields_to_json(fields)))

    def save_escalation(self, job_id: str, stage, result) -> None:
        def _mut(state: dict) -> None:
            esc = state.setdefault("escalations", {})
            esc[stage.value] = _escalation_to_json(result)
        self._mutate_state(job_id, _mut)

    def save_explanation(self, job_id: str, target_language: str, result) -> None:
        def _mut(state: dict) -> None:
            state["explanation"] = _explanation_to_json(result)
            state["explanation_lang"] = target_language
        self._mutate_state(job_id, _mut)

    def get_extraction(self, job_id: str):
        """Explicit accessor (answer_question.py still uses .extractions.get)."""
        return self.extractions.get(job_id)

    def update_explanation_text(self, job_id: str, text: str) -> bool:
        state = self._load_state(job_id)
        if not state or not state.get("explanation"):
            return False
        state["explanation"]["explanation_text"] = text
        self._upsert_state(job_id, state)
        return True

    def get_result(self, job_id: str) -> dict | None:
        state = self._load_state(job_id)
        if not state or not state.get("job"):
            return None
        job = state["job"]
        cls = state.get("classification")
        expl = state.get("explanation")
        esc = state.get("escalations") or {}
        pre = esc.get("pre_explanation")
        post = esc.get("post_explanation")
        flagged = bool((pre and pre.get("escalate")) or (post and post.get("escalate")))
        matched = list(dict.fromkeys(
            (pre.get("matched_rule_ids") if pre else []) + (post.get("matched_rule_ids") if post else [])))
        f = state.get("fields")
        # Keys IDENTICAL to MemoryJobStore.get_result().
        return {
            "jobId": job_id,
            "status": job.get("status"),
            "errorCode": job.get("error_code"),
            "targetLanguage": job.get("target_language"),
            "documentType": cls.get("document_type") if cls else None,
            "classificationConfidence": cls.get("confidence") if cls else None,
            "fields": {
                "issuingAuthority": f.get("issuing_authority") if f else None,
                "deadlineDate": f.get("deadline_date") if f else None,
                "amountOwed": f.get("amount_owed") if f else None,
                "citedSection": f.get("cited_section") if f else None,
                "requiredAction": f.get("required_action") if f else None,
                "fieldConfidence": f.get("field_confidence") if f else {},
            },
            "explanation": expl.get("explanation_text") if expl else None,
            "disclaimerIncluded": expl.get("disclaimer_included", False) if expl else False,
            "escalation": {"flagged": flagged, "matchedRuleIds": matched},
            "voiceAvailable": True,
        }


class PostgresImageStore:
    """Raw upload bytes in a BYTEA table (same put/fetch/delete contract)."""

    def __init__(self) -> None:
        self._conn = _connect()
        self._lock = threading.Lock()
        with self._conn.cursor() as cur:
            cur.execute(DDL)

    def put(self, job_id: str, image: bytes) -> None:
        with self._lock:
            with self._conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO job_images (job_id, image) VALUES (%s, %s) "
                    "ON CONFLICT (job_id) DO UPDATE SET image=EXCLUDED.image",
                    (job_id, bytes(image)))

    def fetch(self, job_id: str) -> bytes | None:
        with self._lock:
            with self._conn.cursor() as cur:
                cur.execute("SELECT image FROM job_images WHERE job_id=%s", (job_id,))
                row = cur.fetchone()
        if not row:
            return None
        return bytes(row[0])

    def delete(self, job_id: str) -> None:
        with self._lock:
            with self._conn.cursor() as cur:
                cur.execute("DELETE FROM job_images WHERE job_id=%s", (job_id,))
