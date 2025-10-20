"""Handler de encuestas configurable (survey).
Usa rules.yaml (bloque 'survey') para límites y mensajes.
"""
from src.config.rules_loader import get_survey_config


def crear_encuesta(pregunta: str, opciones: list[str], chat_id: str | int | None = None):
    cfg = get_survey_config(chat_id)
    if not cfg.get("enabled", True):
        return {"type": "noop"}
    max_opts = int(cfg.get("max_options", 10))
    if len(opciones) == 0:
        return {"type": "reply", "text": "No hay opciones para la encuesta."}
    if len(opciones) > max_opts:
        opciones = opciones[:max_opts]
    # El texto por defecto esperado por los tests es la propia pregunta.
    default_text = cfg.get("create_message")
    if default_text is None:
        text = pregunta
    else:
        text = str(default_text).replace("{question}", pregunta)
    return {
        "text": text,
        "type": "survey",
        "options": opciones,
        "allow_multiple": bool(cfg.get("allow_multiple", False)),
        "anonymous": bool(cfg.get("anonymous", False)),
    }


def procesar_voto(usuario: str, opcion: str, chat_id: str | int | None = None):
    cfg = get_survey_config(chat_id)
    msg = str(cfg.get("vote_message", "Voto registrado: {user} eligió '{option}'"))
    text = msg.replace("{user}", str(usuario)).replace("{option}", str(opcion))
    # Aquí iría la lógica para registrar el voto (persistencia)
    return {"text": text, "type": "reply"}
