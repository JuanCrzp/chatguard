import os
import sys
from fastapi.testclient import TestClient

# Añadir el directorio del bot al PYTHONPATH para importar 'src'
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.app.server import app

client = TestClient(app)

print('GET /health ->', client.get('/health').json())

payload = {
    "platform": "webchat",
    "platform_user_id": "test_user",
    "group_id": "g1",
    "text": "hola"
}
resp = client.post('/webhook', json=payload)
print('POST /webhook status:', resp.status_code)
print('POST /webhook body:', resp.json())
