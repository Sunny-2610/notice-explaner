FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY escalation_rules.yaml ./
# Fake mode (default) needs no LangChain; for the real Q&A agent use: pip install --no-cache-dir ".[qa]"
RUN pip install --no-cache-dir . httpx redis "psycopg[binary]"
ENV PYTHONPATH=/app/src USE_FAKE_AI=true
EXPOSE 8000
CMD ["uvicorn", "notice_explainer.main:app", "--host", "0.0.0.0", "--port", "8000"]
