import os
import sys
import httpx
from dotenv import load_dotenv

def main():
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        print("FAIL (No API key found)")
        sys.exit(1)
    
    # We use a header here to avoid logging the key. The /models endpoint is safe.
    url = "https://generativelanguage.googleapis.com/v1beta/models"
    try:
        r = httpx.get(url, headers={"x-goog-api-key": key}, timeout=10)
        if r.status_code == 200:
            print("OK 200")
            sys.exit(0)
        else:
            print(f"FAIL {r.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"FAIL (HTTP error)")
        sys.exit(1)

if __name__ == "__main__":
    main()
