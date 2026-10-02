"""Check WhatsApp readiness. Run: python scripts/check_whatsapp.py"""
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()
BASE = (os.getenv("PUBLIC_BASE_URL") or "").rstrip("/")

KEYS = [
    "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_FROM",
    "PUBLIC_BASE_URL", "WHATSAPP_HASH_SALT",
]

print("== local .env ==")
missing = [k for k in KEYS if not os.getenv(k, "").strip()]
for k in KEYS:
    v = os.getenv(k, "")
    show = v[:14] + "..." if v and "KEY" not in k and "SALT" not in k else ("set" if v else "MISSING")
    print(f"  {k:24} {show}")
print("  local 5/5" if not missing else f"  missing: {missing}")

if not BASE:
    sys.exit("\nPUBLIC_BASE_URL missing - nothing to check live.")

print(f"\n== live {BASE} ==")
try:
    h = httpx.get(f"{BASE}/health", timeout=60).json()
    print("  health:", h)
except Exception as exc:
    print("  health FAILED:", type(exc).__name__, exc)

url = f"{BASE}/api/v1/channels/whatsapp/webhook"
try:
    r = httpx.post(url, data={"From": "whatsapp:+10000000000", "Body": "hi", "NumMedia": "0"},
                   timeout=60)
    code = r.status_code
except Exception as exc:
    print("  webhook FAILED:", type(exc).__name__, exc)
    code = None

if code == 404:
    print("  webhook 404 -> channel DISABLED (Render missing one of the 5 env vars)")
elif code == 403:
    print("  webhook 403 -> LIVE (signature check active). Next: save webhook URL in Twilio console.")
elif code == 204:
    print("  webhook 204 -> signature was accepted (unexpected for this unsigned test)")
else:
    print(f"  webhook {code} -> unexpected")
