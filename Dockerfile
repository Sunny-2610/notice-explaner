# Root Dockerfile for Render Web Service (Docker runtime) without rootDir.
# Blueprint path (render.yaml, runtime python, rootDir backend) does not use
# this file. Manual Docker path uses it so "open Dockerfile: no such file"
# never happens again.
FROM python:3.11-slim
WORKDIR /app
COPY backend/pyproject.toml ./
COPY backend/src ./src
COPY backend/escalation_rules.yaml ./
# Real Q&A agent included so GEMINI_API_KEY + USE_FAKE_AI=false works.
RUN pip install --no-cache-dir ".[qa]" httpx redis "psycopg[binary]"
ENV PYTHONPATH=/app/src USE_FAKE_AI=true
EXPOSE 8000
CMD ["uvicorn", "notice_explainer.main:app", "--host", "0.0.0.0", "--port", "8000"]
