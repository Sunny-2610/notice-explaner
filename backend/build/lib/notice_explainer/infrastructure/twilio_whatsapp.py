"""Twilio WhatsApp channel (no Twilio SDK — httpx + hand-rolled HMAC-SHA1).

Only active when TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM,
PUBLIC_BASE_URL and WHATSAPP_HASH_SALT are all set; otherwise the webhook
returns 404 and FakeMessagingChannel records sends in tests.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os

import httpx


def verify_twilio_signature(
    auth_token: str, url: str, params: dict, signature: str | None
) -> bool:
    """Twilio request validation: HMAC-SHA1 over URL + sorted POST params."""
    if not signature:
        return False
    data = url + "".join(
        f"{k}{params[k]}" for k in sorted(params.keys())
    )
    digest = hmac.new(
        auth_token.encode("utf-8"), data.encode("utf-8"), hashlib.sha1
    ).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature)


class TwilioWhatsAppChannel:
    name = "twilio"

    def __init__(self) -> None:
        self.sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.sender = os.getenv("TWILIO_WHATSAPP_FROM", "")
        if not (self.sid and self.token and self.sender):
            raise RuntimeError("Twilio WhatsApp not configured")

    def send_message(self, to: str, body: str) -> None:
        url = (f"https://api.twilio.com/2010-04-01/Accounts/"
               f"{self.sid}/Messages.json")
        r = httpx.post(
            url,
            auth=(self.sid, self.token),
            data={"From": self.sender, "To": to, "Body": body},
            timeout=8,
        )
        r.raise_for_status()

    def download_media(self, url: str) -> bytes:
        r = httpx.get(url, auth=(self.sid, self.token), timeout=15)
        r.raise_for_status()
        return r.content


class FakeMessagingChannel:
    """Test double: records sends, serves canned media. No network."""

    name = "fake"

    def __init__(self, media: bytes = b"FAKE-JPEG-PROPERTY-TAX") -> None:
        self.sent: list[dict] = []
        self.media = media

    def send_message(self, to: str, body: str) -> None:
        self.sent.append({"to": to, "body": body})

    def download_media(self, url: str) -> bytes:
        return self.media
