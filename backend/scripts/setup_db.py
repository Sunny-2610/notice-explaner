"""One-time DB setup: base tables (same DDL as postgres.py) + hardening indexes."""
import sys
sys.path.insert(0, "src")
from dotenv import load_dotenv
load_dotenv()
import os
import psycopg

url = os.getenv("DATABASE_URL", "")
if not url:
    print("FAIL: DATABASE_URL not set in backend/.env")
    sys.exit(1)

from notice_explainer.infrastructure.postgres import DDL

INDEXES = """
CREATE INDEX IF NOT EXISTS idx_audit_job_time ON audit_log_entries (job_id, created_at);
CREATE INDEX IF NOT EXISTS idx_review_open ON review_cases (decision) WHERE decision IS NULL;
"""

c = psycopg.connect(url, connect_timeout=20)
with c.cursor() as cur:
    cur.execute(DDL)
    cur.execute(INDEXES)
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY 1")
    print("TABLES:", [r[0] for r in cur.fetchall()])
    cur.execute("SELECT indexname FROM pg_indexes WHERE schemaname='public' AND tablename IN ('audit_log_entries','review_cases') ORDER BY 1")
    print("INDEXES:", [r[0] for r in cur.fetchall()])
c.close()
print("DONE")
