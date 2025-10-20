from fastapi.testclient import TestClient
from src.app.server import app

client = TestClient(app)

def test_webhook_greeting():
    payload = {
        "platform": "webchat",
        "platform_user_id": "u1",
        "group_id": "g1",
        "text": "Hola, soy Juan",
        "attachments": [],
        "raw_payload": {}
    }
    res = client.post("/webhook", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert data["response"]["type"] == "reply"
    assert "Hola" in data["response"]["text"]
