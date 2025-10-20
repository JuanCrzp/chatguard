"""Dispatcher de salida: envia respuestas a la plataforma adecuada."""
from typing import Dict, Any

from src.connectors.telegram_connector import enviar_mensaje_telegram
from src.connectors.whatsapp_connector import enviar_mensaje_whatsapp
from src.connectors.webchat_connector import enviar_mensaje_webchat


def enviar_respuesta(platform: str, payload_entrada: Dict[str, Any], respuesta: Dict[str, Any]) -> Dict[str, Any]:
    text = respuesta.get("text", "")

    if platform == "telegram":
        chat_id = payload_entrada.get("group_id") or payload_entrada.get("platform_user_id")
        return {"platform": platform, "result": enviar_mensaje_telegram(str(chat_id or ""), text)}
    if platform == "whatsapp":
        numero = payload_entrada.get("platform_user_id")
        return {"platform": platform, "result": enviar_mensaje_whatsapp(str(numero or ""), text)}
    if platform == "webchat":
        uid = payload_entrada.get("platform_user_id")
        return {"platform": platform, "result": enviar_mensaje_webchat(str(uid or ""), text)}

    return {"platform": platform, "sent": False, "reason": "Plataforma no soportada"}
