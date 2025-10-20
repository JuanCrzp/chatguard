"""API del Bot de Comunidad (FastAPI)."""
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from src.bot_core.manager import BotManager
from src.app.health import health_status
from src.app.config import SEND_AUTOMATIC_RESPONSES
import os
from src.connectors.dispatcher import enviar_respuesta
from src.app.schemas import InputMessage, ResponseEnvelope, OutputMessage, DispatchResult
from src.utils.logging import log_event, log_error_event
from src.connectors.whatsapp_connector import router as whatsapp_router

app = FastAPI(title="Comunidad Bot API")

# CORS opcional (no restrictivo por defecto)
allow_origins = os.getenv("CORS_ALLOW_ORIGINS")
if allow_origins:
    origins = [o.strip() for o in allow_origins.split(",") if o.strip()]
else:
    origins = ["*"]

# Por seguridad, si usamos wildcard "*", desactivamos cookies/credenciales
allow_credentials = False if origins == ["*"] else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key opcional: si no se define, no se aplica auth para mantener compatibilidad
API_KEY = os.getenv("API_KEY", "").strip()
def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="x-api-key")):
    if not API_KEY:
        return True
    if x_api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")
    return True
manager = BotManager()
app.include_router(whatsapp_router)


@app.get("/health")
def health():
    return health_status()


@app.post("/webhook", response_model=ResponseEnvelope)
def webhook(payload: InputMessage, _auth_ok: bool = Depends(require_api_key)):
    """Recibe mensajes normalizados de los conectores y responde según NLU/handlers.
    Si SEND_AUTOMATIC_RESPONSES=true, además envía la respuesta a la plataforma origen.
    """
    log_event("incoming_payload", platform=payload.platform, user=str(payload.platform_user_id), group=str(payload.group_id))
    result_dict = manager.process_message(payload.model_dump())
    if SEND_AUTOMATIC_RESPONSES:
        try:
            platform = payload.platform
            dispatch_result = enviar_respuesta(platform, payload.model_dump(), result_dict)
            log_event("dispatch_success", platform=platform, user=str(payload.platform_user_id), group=str(payload.group_id))
            # Si result_dict no tiene los campos requeridos por OutputMessage
            # no intentamos validarlo con Pydantic; en ese caso devolvemos
            # directamente el dict (ResponseEnvelope acepta dicts).
            # Construir OutputMessage solo si el dict contiene exclusivamente
            # los campos compatibles con OutputMessage; si tiene campos extra
            # (ej. 'options' para encuestas), devolver el dict tal cual para
            # preservar esos campos en la API.
            if isinstance(result_dict, dict) and ("text" in result_dict and "type" in result_dict):
                allowed = {"text", "type", "quick_replies", "attachments"}
                keys = set(result_dict.keys())
                if keys.issubset(allowed):
                    response_obj = OutputMessage(**result_dict)
                else:
                    response_obj = result_dict
            else:
                response_obj = result_dict
            envelope = ResponseEnvelope(
                response=response_obj,
                dispatched=DispatchResult(**dispatch_result)
            )
            return envelope
        except Exception as e:
            log_error_event("dispatch_error", error=str(e), platform=payload.platform)
            # Si hay error al despachar, y result_dict no cumple OutputMessage,
            # devolvemos el dict crudo para que el caller lo maneje.
            if isinstance(result_dict, dict) and ("text" in result_dict and "type" in result_dict):
                allowed = {"text", "type", "quick_replies", "attachments"}
                if set(result_dict.keys()).issubset(allowed):
                    return ResponseEnvelope(response=OutputMessage(**result_dict))
            return ResponseEnvelope(response=result_dict)
    # Respuesta sin dispatch (bot en modo silent): si result_dict no contiene
    # los campos esperados por OutputMessage, devolvemos directamente el dict.
    if isinstance(result_dict, dict) and ("text" in result_dict and "type" in result_dict):
        allowed = {"text", "type", "quick_replies", "attachments"}
        if set(result_dict.keys()).issubset(allowed):
            return ResponseEnvelope(response=OutputMessage(**result_dict))
    return ResponseEnvelope(response=result_dict)


@app.post("/admin/reply")
def admin_reply(data: dict, _auth_ok: bool = Depends(require_api_key)):
    # Placeholder: autenticación y envío a canal correspondiente
    return {"status": "admin reply sent"}
