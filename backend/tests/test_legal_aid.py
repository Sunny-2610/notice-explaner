"""Free legal-aid endpoints: shapes, fallback, no fabricated numbers."""
from fastapi.testclient import TestClient

from notice_explainer.main import create_app

ALLOWED_PHONES = {"15100", "14454"}


def _client():
    return TestClient(create_app())


def test_legal_aid_returns_seeded_national_entries():
    client = _client()
    r = client.get("/api/v1/legal-aid")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["national"], list)
    assert isinstance(body["entries"], list)
    phones = {e.get("phone") for e in body["national"]}
    assert phones == ALLOWED_PHONES
    names = {e.get("name") for e in body["national"]}
    assert "NALSA legal services helpline" in names
    assert "Tele-Law" in names


def test_legal_aid_unknown_state_falls_back_to_national_only():
    client = _client()
    r = client.get("/api/v1/legal-aid", params={"state": "xx-unknown"})
    assert r.status_code == 200
    body = r.json()
    assert body["entries"] == []
    assert {e.get("phone") for e in body["national"]} == ALLOWED_PHONES


def test_legal_aid_states_shape():
    client = _client()
    r = client.get("/api/v1/legal-aid/states")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["states"], list)
    # Empty seed list is fine; every entry must have code + name when present.
    for s in body["states"]:
        assert "code" in s and "name" in s


def test_legal_aid_no_fabricated_numbers():
    import json
    from pathlib import Path

    data_path = Path(__file__).resolve().parents[1] / "data" / "legal_aid.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))

    def _phones(node) -> list[str]:
        found: list[str] = []

        def _walk(o):
            if isinstance(o, dict):
                if "phone" in o and isinstance(o["phone"], str):
                    found.append(o["phone"])
                for v in o.values():
                    _walk(v)
            elif isinstance(o, list):
                for v in o:
                    _walk(v)

        _walk(node)
        return found

    for phone in _phones(data):
        assert phone in ALLOWED_PHONES, phone
    assert data.get("states") == {}
