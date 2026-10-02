"""WhatsApp channel: signature, menu, image/escalated paths, resolve hook, PII."""
import base64
import hashlib
import hmac
import io
import logging

from fastapi.testclient import TestClient

from notice_explainer.api import deps
from notice_explainer.infrastructure.fake_ai import FakeQAAgent
from notice_explainer.infrastructure.memory import (
    MemoryAuditLogger,
    MemoryImageStore,
    MemoryJobStore,
    MemoryReviewQueue,
)
from notice_explainer.infrastructure.twilio_whatsapp import FakeMessagingChannel
from notice_explainer.main import create_app

NUMBER = "+15551234567"
FROM = f"whatsapp:{NUMBER}"
PATH = "/api/v1/channels/whatsapp/webhook"
URL = f"http://testserver{PATH}"

WA_ENV = {
    "TWILIO_ACCOUNT_SID": "ACtest",
    "TWILIO_AUTH_TOKEN": "test-token",
    "TWILIO_WHATSAPP_FROM": "whatsapp:+10000000000",
    "PUBLIC_BASE_URL": "http://testserver",
    "WHATSAPP_HASH_SALT": "test-salt",
}


def _client(media: bytes = b"FAKE-JPEG-PROPERTY-TAX"):
    deps.job_store = MemoryJobStore()
    deps.image_store = MemoryImageStore()
    deps.review_queue = MemoryReviewQueue()
    deps.audit = MemoryAuditLogger()
    deps.qa_agent = FakeQAAgent()
    deps.messaging_channel = FakeMessagingChannel(media=media)
    from notice_explainer.application.use_cases import whatsapp_flow as flow

    flow.lang_prefs.clear()
    flow.greeted.clear()
    flow.rate_hits.clear()
    flow.sender_registry.clear()
    flow._seen_sids.clear()
    return TestClient(create_app())


def _enable_wa(monkeypatch):
    for k, v in WA_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("REVIEWER_API_KEY", raising=False)


def _sign(params: dict) -> str:
    data = URL + "".join(f"{k}{params[k]}" for k in sorted(params.keys()))
    digest = hmac.new(
        WA_ENV["TWILIO_AUTH_TOKEN"].encode(), data.encode(), hashlib.sha1
    ).digest()
    return base64.b64encode(digest).decode()


def _post(client, params: dict, signature: str | None = None):
    sig = signature if signature is not None else _sign(params)
    return client.post(PATH, data=params, headers={"X-Twilio-Signature": sig})


def _text_msg(body: str) -> dict:
    return {"From": FROM, "Body": body, "NumMedia": "0"}


def _image_msg() -> dict:
    return {
        "From": FROM,
        "Body": "",
        "NumMedia": "1",
        "MediaUrl0": "https://api.twilio.com/media/1",
        "MediaContentType0": "image/jpeg",
    }


def test_webhook_disabled_without_env(monkeypatch):
    # Must clear the 5 vars explicitly: a developer .env (or CI secret) with
    # real Twilio keys is loaded by main.py's load_dotenv(), which would
    # otherwise turn this into 403 instead of the 404 we assert.
    for k in WA_ENV:
        monkeypatch.delenv(k, raising=False)
    client = _client()
    r = client.post(PATH, data=_text_msg("hello"))
    assert r.status_code == 404


def test_webhook_bad_signature_403(monkeypatch):
    _enable_wa(monkeypatch)
    client = _client()
    r = _post(client, _text_msg("hello"), signature="bogus")
    assert r.status_code == 403


def test_language_menu_then_choice(monkeypatch):
    _enable_wa(monkeypatch)
    client = _client()
    assert _post(client, _text_msg("hello")).status_code == 204
    first = deps.messaging_channel.sent[-1]["body"]
    assert "1" in first and "हिंदी" in first
    assert _post(client, _text_msg("1")).status_code == 204
    assert "हिंदी" in deps.messaging_channel.sent[-1]["body"]
    assert _post(client, _text_msg("2")).status_code == 204
    assert "मराठी" in deps.messaging_channel.sent[-1]["body"]


def _image_msg_sid(sid: str) -> dict:
    return {**_image_msg(), "MessageSid": sid}


def test_duplicate_message_sid_is_ignored(monkeypatch):
    # Twilio retries a webhook when the response is slow or the instance is
    # cold. The same MessageSid must never create a second job.
    _enable_wa(monkeypatch)
    client = _client()
    _post(client, _text_msg("1"))
    sid = "SM" + "0" * 32
    assert _post(client, _image_msg_sid(sid)).status_code == 204
    assert len(deps.messaging_channel.sent) > 0
    first_count = len(deps.messaging_channel.sent)
    assert _post(client, _image_msg_sid(sid)).status_code == 204
    # Retried delivery: acknowledged, but no second explanation sent.
    assert len(deps.messaging_channel.sent) == first_count


def test_distinct_message_sids_both_processed(monkeypatch):
    _enable_wa(monkeypatch)
    client = _client()
    _post(client, _text_msg("1"))
    before = len(deps.messaging_channel.sent)
    assert _post(client, _image_msg_sid("SM" + "1" * 32)).status_code == 204
    after_first = len(deps.messaging_channel.sent)
    assert _post(client, _image_msg_sid("SM" + "2" * 32)).status_code == 204
    assert len(deps.messaging_channel.sent) > after_first


def test_sid_reprocessed_after_ttl(monkeypatch):
    # Dedup is time-boxed; after the TTL the same sid is treated as new.
    from notice_explainer.application.use_cases import whatsapp_flow as flow

    _enable_wa(monkeypatch)
    client = _client()
    _post(client, _text_msg("1"))
    sid = "SM" + "3" * 32
    assert _post(client, _image_msg_sid(sid)).status_code == 204
    flow._seen_sids[sid] -= flow.SEEN_TTL_S + 1
    before = len(deps.messaging_channel.sent)
    assert _post(client, _image_msg_sid(sid)).status_code == 204
    assert len(deps.messaging_channel.sent) > before


def test_missing_sid_is_always_processed(monkeypatch):
    # Payloads without a MessageSid must not be silently dropped.
    _enable_wa(monkeypatch)
    client = _client()
    _post(client, _text_msg("1"))
    before = len(deps.messaging_channel.sent)
    assert _post(client, _image_msg()).status_code == 204
    assert len(deps.messaging_channel.sent) > before


def test_image_happy_path_replies_verdict_and_facts(monkeypatch):
    _enable_wa(monkeypatch)
    client = _client()
    _post(client, _text_msg("1"))
    assert _post(client, _image_msg()).status_code == 204
    bodies = "\n".join(m["body"] for m in deps.messaging_channel.sent)
    assert "विवरण" in bodies
    assert "₹4,500" in bodies  # Indian-formatted amount
    assert "15/11/2026" in bodies


def test_escalated_path_sends_legal_aid_without_explanation(monkeypatch):
    _enable_wa(monkeypatch)
    client = _client(media=b"FAKE-JPEG-SUMMONS-COURT")
    _post(client, _text_msg("1"))
    before = len(deps.messaging_channel.sent)
    assert _post(client, _image_msg()).status_code == 204
    new_bodies = "\n".join(
        m["body"] for m in deps.messaging_channel.sent[before:]
    )
    assert "गंभीर" in new_bodies
    assert "15100" in new_bodies  # legal-aid numbers present
    assert "14454" in new_bodies
    assert "Appear before the court" not in new_bodies  # no unreviewed text


def test_resolve_hook_delivers_explanation(monkeypatch):
    _enable_wa(monkeypatch)
    client = _client(media=b"FAKE-JPEG-SUMMONS-COURT")
    _post(client, _text_msg("1"))
    _post(client, _image_msg())
    queue = client.get("/api/v1/review/queue").json()
    assert len(queue) == 1
    job_id = queue[0]["jobId"]
    before = len(deps.messaging_channel.sent)
    r = client.post(f"/api/v1/review/{job_id}/resolve",
                    json={"reviewerId": "r1", "decision": "approve"})
    assert r.status_code == 200
    delivered = "\n".join(
        m["body"] for m in deps.messaging_channel.sent[before:]
    )
    assert "Appear before the court" in delivered


def test_rate_limit_after_ten_jobs(monkeypatch):
    _enable_wa(monkeypatch)
    client = _client()
    _post(client, _text_msg("1"))
    for _ in range(10):
        assert _post(client, _image_msg()).status_code == 204
    assert _post(client, _image_msg()).status_code == 204
    assert "10 से अधिक" in deps.messaging_channel.sent[-1]["body"]


def test_format_reply_splits_long_messages():
    from notice_explainer.application.use_cases.whatsapp_flow import split_message

    long = "\n".join(f"line {i} " + "x" * 100 for i in range(40))
    parts = split_message(long)
    assert len(parts) > 1
    assert all(len(p) <= 1500 for p in parts)


def test_pii_never_in_logs_or_audit(monkeypatch, caplog):
    _enable_wa(monkeypatch)
    client = _client()
    with caplog.at_level(logging.DEBUG):
        _post(client, _text_msg("hello"))
        _post(client, _text_msg("1"))
        _post(client, _image_msg())
    assert NUMBER not in caplog.text
    for job_id in list(deps.job_store.jobs.keys()):
        for entry in deps.audit.entries_for(job_id):
            assert NUMBER not in str(entry.input_ref)
            assert NUMBER not in str(entry.output_ref)
    for entry in deps.audit.entries_for("wa-validation-xyz"):
        assert NUMBER not in str(entry.input_ref)
    assert NUMBER not in io.StringIO().getvalue()  # sanity: literal untouched
