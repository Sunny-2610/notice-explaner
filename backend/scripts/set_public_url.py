"""Set PUBLIC_BASE_URL in backend/.env safely. Usage: python scripts/set_public_url.py https://xxxx.ngrok-free.app"""
import sys
from pathlib import Path

env_path = Path(__file__).resolve().parents[1] / ".env"
url = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else ""
if not url.startswith("https://"):
    print("Give https URL, e.g. python scripts/set_public_url.py https://xxxx.ngrok-free.app")
    sys.exit(1)
lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
out, found = [], False
for ln in lines:
    if ln.startswith("PUBLIC_BASE_URL="):
        out.append(f"PUBLIC_BASE_URL={url}")
        found = True
    else:
        out.append(ln)
if not found:
    out.append(f"PUBLIC_BASE_URL={url}")
env_path.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"saved PUBLIC_BASE_URL={url[:20]}... (restart api to apply)")
