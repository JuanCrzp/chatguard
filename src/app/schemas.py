from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel


class InputMessage(BaseModel):
    platform: str
    platform_user_id: Union[str, int]
    group_id: Union[str, int]
    text: str
    attachments: Optional[List[Any]] = None
    raw_payload: Optional[Dict[str, Any]] = None


class OutputMessage(BaseModel):
    text: str
    type: str
    quick_replies: Optional[List[str]] = None
    attachments: Optional[List[Any]] = None


class DispatchResult(BaseModel):
    platform: str
    result: Optional[Dict[str, Any]] = None
    sent: Optional[bool] = None
    reason: Optional[str] = None


class ResponseEnvelope(BaseModel):
    # Preferir Dict primero para que Pydantic no intente validar y convertir
    # automáticamente dicts que contienen campos extra (por ejemplo 'options')
    # a OutputMessage, lo que podría descartar dichos campos.
    response: Union[Dict[str, Any], OutputMessage]
    dispatched: Optional[DispatchResult] = None