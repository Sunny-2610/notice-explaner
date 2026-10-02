"""Answer a follow-up question about a processed notice.

Orchestration only — this module does NOT know about LangChain. The agent
is injected via parameter (port), so domain/application stay clean.

Safety: the agent runs AFTER the pipeline, reads notice text + explanation
only, and can never touch escalation state. Max 10 questions per job
(enforced via the audit trail so it works with any audit backend).
"""
from __future__ import annotations

from ...domain.types import ErrorCode

MAX_QUESTIONS_PER_JOB = 10
QA_AUDIT_STAGE = "qa_ask"


class AnswerQuestionError(Exception):
    def __init__(self, code: ErrorCode, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def answer_question(
    job_id: str,
    question: str,
    *,
    target_language: str | None = None,
    job_store,
    qa_agent,
    audit=None,
) -> str:
    if not question or not question.strip():
        raise AnswerQuestionError(ErrorCode.INVALID_FILE, "Question cannot be empty.")

    result = job_store.get_result(job_id)
    if result is None:
        raise AnswerQuestionError(ErrorCode.INVALID_FILE, "unknown jobId", status_code=404)

    # Gate 1/2: no explanation exists yet (low-extraction E-150 or
    # unsupported E-201 jobs). There is nothing truthful to discuss, so the
    # agent never runs. Provisional E-401 jobs DO have an explanation and
    # fall through to the agent.
    if not result.get("explanation"):
        raise AnswerQuestionError(ErrorCode.INVALID_FILE, "Explanation not ready yet.")

    # Gate 2/2: conversation budget counted from the append-only audit trail
    # (works identically on memory and Postgres backends).
    if audit is not None:
        asked = sum(1 for e in audit.entries_for(job_id)
                    if getattr(e, "stage_name", "") == QA_AUDIT_STAGE)
        if asked >= MAX_QUESTIONS_PER_JOB:
            raise AnswerQuestionError(
                ErrorCode.INVALID_FILE,
                f"Too many questions (max {MAX_QUESTIONS_PER_JOB} per notice).")

    extraction = job_store.extractions.get(job_id)
    notice_text = extraction.text if extraction else ""

    override_lang = target_language if target_language else result.get("targetLanguage", "hi")

    answer = qa_agent.answer(
        notice_text=notice_text,
        explanation=result["explanation"],
        target_language=override_lang,
        question=question.strip(),
    )

    if audit is not None:
        audit.log_stage(job_id, QA_AUDIT_STAGE,
                        {"question": question.strip()[:300]},
                        {"answer": str(answer)[:500]})
    return answer
