"""Conector profesional para WhatsApp (Cloud API de Meta).

Características:
- Webhook de verificación (GET) y recepción de mensajes (POST) listo para registrar en Meta.
- Normaliza mensajes y los pasa por el BotManager.
- Envía respuestas automáticas usando el token de .env.
- No requiere configurar el phone_number_id en .env: se toma del webhook entrante.

Variables .env soportadas:
- WHATSAPP_TOKEN: token de acceso de la Cloud API (obligatorio para enviar mensajes)
- WHATSAPP_VERIFY_TOKEN: cadena que configuras tú para verificar el webhook (opcional, por defecto "verify")
- WHATSAPP_API_VERSION: versión de Graph API (opcional, por defecto "v20.0")
- WHATSAPP_PHONE_NUMBER_ID: opcional; si no está, se usa el del webhook entrante
"""

from __future__ import annotations
import os
import json
import time
from typing import Any, Dict, Optional

import requests
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import PlainTextResponse

from src.bot_core.manager import BotManager
from src.app.config import SEND_AUTOMATIC_RESPONSES
from src.utils.logging import log_event, log_error_event


router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp"])
manager = BotManager()

# Cache en memoria del último phone_number_id visto en el webhook (sirve para envíos)
_LAST_PHONE_NUMBER_ID: Optional[str] = os.getenv("WHATSAPP_PHONE_NUMBER_ID")


def _graph_base_url(api_version: str) -> str:
    ver = os.getenv("WHATSAPP_API_VERSION", api_version or "v20.0").strip() or "v20.0"
    return f"https://graph.facebook.com/{ver}"


def enviar_mensaje_whatsapp(numero: str, texto: str, phone_number_id: Optional[str] = None) -> Dict[str, Any]:
    """Envía un mensaje de texto vía Cloud API.

    Si no se pasa phone_number_id, usa el último visto en webhook o el de .env.
    """
    token = os.getenv("WHATSAPP_TOKEN", "").strip()
    if not token:
        return {"ok": False, "error": "Falta WHATSAPP_TOKEN en .env"}

    pnid = phone_number_id or _LAST_PHONE_NUMBER_ID or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    if not pnid:
        return {"ok": False, "error": "No hay phone_number_id disponible (configure .env o reciba un webhook primero)"}

    url = f"{_graph_base_url('v20.0')}/{pnid}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": str(numero),
        "type": "text",
        "text": {"body": texto[:4096]},  # límite seguro
    }
    last_err: Optional[str] = None
    for attempt in range(1, 3):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            if 200 <= resp.status_code < 300:
                return {"ok": True, "status": resp.status_code, "response": resp.json()}
            last_err = f"HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            last_err = str(e)
        time.sleep(0.3 * attempt)
    return {"ok": False, "error": last_err or "Error desconocido"}


def normalizar_mensaje_whatsapp(entry_change_value: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extrae y normaliza un mensaje entrante del payload de Cloud API.

    Estructura típica: entry[0].changes[0].value.messages[0]
    """
    try:
        messages = entry_change_value.get("messages") or []
        metadata = entry_change_value.get("metadata") or {}
        contacts = entry_change_value.get("contacts") or []
        if not messages:
            return None
        msg = messages[0]
        from_id = msg.get("from")  # número del usuario
        text_body = ""
        if msg.get("type") == "text":
            text_body = (msg.get("text") or {}).get("body", "")
        elif msg.get("type") == "button":
            text_body = (msg.get("button") or {}).get("text", "")
        elif msg.get("type") == "interactive":
            inter = msg.get("interactive") or {}
            text_body = (inter.get("text") or {}).get("body", "") or (inter.get("button_reply") or {}).get("title", "")
        phone_number_id = metadata.get("phone_number_id")
        # Actualizar cache del phone_number_id
        global _LAST_PHONE_NUMBER_ID
        if phone_number_id:
            _LAST_PHONE_NUMBER_ID = phone_number_id
        return {
            "platform": "whatsapp",
            "platform_user_id": from_id,
            "group_id": None,  # Cloud API no maneja grupos del mismo modo
            "text": text_body or "",
            "raw_payload": msg,
            "_phone_number_id": phone_number_id,
        }
    except Exception:
        return None


@router.get("/")
async def verify(mode: Optional[str] = None, challenge: Optional[str] = None, token: Optional[str] = None, hub_mode: Optional[str] = None, hub_challenge: Optional[str] = None, hub_verify_token: Optional[str] = None):
    """Endpoint de verificación del webhook (GET).

    Meta envía: hub.mode, hub.challenge, hub.verify_token
    """
    supplied_token = (hub_verify_token or token or "").strip()
    expected = os.getenv("WHATSAPP_VERIFY_TOKEN", "verify").strip()
    supplied_challenge = hub_challenge or challenge or ""
    if supplied_token and supplied_token == expected:
        return PlainTextResponse(content=str(supplied_challenge), status_code=200)
    return Response(status_code=status.HTTP_403_FORBIDDEN)


@router.post("/")
async def inbound(request: Request):
    """Recibe notificaciones de la Cloud API y procesa mensajes entrantes."""
    try:
        data = await request.json()
    except Exception:
        return {"status": "invalid json"}

    try:
        entries = data.get("entry") or []
        for ent in entries:
            for ch in ent.get("changes", []):
                value = ch.get("value") or {}
                # Normalizar mensaje si existe
                norm = normalizar_mensaje_whatsapp(value)
                if not norm or not norm.get("text"):
                    continue
                log_event("whatsapp_incoming", user=str(norm.get("platform_user_id")))
                # Procesar con el manager
                result = manager.process_message(norm)
                # Responder automáticamente si corresponde
                if SEND_AUTOMATIC_RESPONSES and isinstance(result, dict):
                    reply_text = result.get("text")
                    if reply_text:
                        enviar_mensaje_whatsapp(
                            str(norm.get("platform_user_id")),
                            reply_text,
                            phone_number_id=norm.get("_phone_number_id"),
                        )
        return {"status": "ok"}
    except Exception as e:
        log_error_event("whatsapp_webhook_error", error=str(e))
        return {"status": "error", "error": str(e)}

