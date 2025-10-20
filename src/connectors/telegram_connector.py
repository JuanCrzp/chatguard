# telegram_connector.py - Conector funcional para Telegram
import requests
import os
import time
from typing import Any, Dict
from src.utils.logging import log_event, log_error_event

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"


def _post_with_retries(url: str, json_payload: Dict[str, Any], timeout: int = 5, retries: int = 3, backoff: float = 0.5):
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(url, json=json_payload, timeout=timeout)
            if resp.status_code >= 200 and resp.status_code < 300:
                return resp.json()
            last_err = f"HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            last_err = str(e)
        time.sleep(backoff * attempt)
    raise RuntimeError(last_err or "Unknown error")


def enviar_mensaje_telegram(chat_id, texto):
    payload = {
        "chat_id": chat_id,
        "text": texto
    }
    try:
        result = _post_with_retries(TELEGRAM_API_URL, payload, timeout=5, retries=3, backoff=0.5)
        log_event("telegram_send_success", chat_id=str(chat_id))
        return result
    except Exception as e:
        log_error_event("telegram_send_error", chat_id=str(chat_id), error=str(e))
        return {"ok": False, "error": str(e)}

# Ejemplo de función para recibir y normalizar mensajes

def normalizar_mensaje_telegram(update):
    if "message" in update:
        msg = update["message"]
        return {
            "platform": "telegram",
            "platform_user_id": msg["from"]["id"],
            "group_id": msg.get("chat", {}).get("id"),
            "text": msg.get("text", ""),
            "raw_payload": update
        }
    return None
