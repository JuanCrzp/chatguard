from fastapi.testclient import TestClient
from src.app.server import app

client = TestClient(app)

def test_webhook_encuesta():
    payload = {
        "platform": "webchat",
        "platform_user_id": "u1",
        "group_id": "g1",
        "text": "Crea encuesta \"¿Te gusta Python?\" con [Sí,No]",
        "attachments": [],
        "raw_payload": {}
    }
    res = client.post("/webhook", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["response"]["type"] == "survey"
    assert data["response"]["text"]
    assert data["response"]["options"] == ["Sí", "No"]


def test_webhook_sorteo():
    payload = {
        "platform": "webchat",
        "platform_user_id": "u1",
        "group_id": "g1",
        "text": "hacer sorteo entre (juan, ana, pedro)",
        "attachments": [],
        "raw_payload": {}
    }
    res = client.post("/webhook", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["response"]["type"] == "raffle"
    assert any(p in data["response"]["text"] for p in ["juan", "ana", "pedro"])
