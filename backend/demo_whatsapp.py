import base64
import hashlib
import hmac
import os
import requests
from dotenv import load_dotenv

# Load your local .env file
load_dotenv()

# The local backend URL (running via `fastapi dev` or `uvicorn`)
LOCAL_URL = "http://127.0.0.1:8000/api/v1/channels/whatsapp/webhook"

# The URL Twilio thinks it is hitting (for signature validation)
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
SIGNATURE_URL = f"{PUBLIC_BASE_URL}/api/v1/channels/whatsapp/webhook"
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")

if not AUTH_TOKEN:
    print("❌ TWILIO_AUTH_TOKEN not found in .env!")
    exit(1)

# Our mock incoming message payload
payload = {
    "MessageSid": "SM_hackathon_demo" + os.urandom(4).hex(),
    "From": "whatsapp:+916206974638", # Your testing number
    "To": os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+17372508034"),
    "Body": "Can you explain this notice for me please?",
    "NumMedia": "1",
    "MediaContentType0": "image/jpeg",
    # Using a sample public document image so the backend can process it!
    "MediaUrl0": "https://upload.wikimedia.org/wikipedia/commons/e/e0/Placeholder_text_example.png" 
}

# Generate the exact HMAC-SHA1 Twilio Signature
data = SIGNATURE_URL + "".join(f"{k}{payload[k]}" for k in sorted(payload.keys()))
digest = hmac.new(AUTH_TOKEN.encode("utf-8"), data.encode("utf-8"), hashlib.sha1).digest()
signature = base64.b64encode(digest).decode()

headers = {
    "X-Twilio-Signature": signature
}

print("🚀 Mocking incoming WhatsApp message with an attached document image...")
try:
    resp = requests.post(LOCAL_URL, data=payload, headers=headers)
    if resp.status_code == 204:
        print("✅ Message successfully accepted by backend!")
        print("👀 Check your backend terminal logs. You will see the AI processing the image right now!")
    else:
        print(f"❌ Webhook rejected it (Status: {resp.status_code})")
        print(f"Details: {resp.text}")
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to localhost:8000. Is your backend server running?")
