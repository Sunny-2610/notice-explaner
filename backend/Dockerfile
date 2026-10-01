FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY escalation_rules.yaml ./
# Real Q&A agent (LangChain) included so GEMINI_API_KEY + USE_FAKE_AI=false works.
RUN pip install --no-cache-dir ".[qa]" httpx redis "psycopg[binary]"
ENV PYTHONPATH=/app/src USE_FAKE_AI=true
EXPOSE 8000
CMD ["uvicorn", "notice_explainer.main:app", "--host", "0.0.0.0", "--port", "8000"]
