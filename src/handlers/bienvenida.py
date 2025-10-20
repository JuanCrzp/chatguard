"""Handler de bienvenida configurable.
Lee la configuración desde rules.yaml (bloque 'welcome') y arma el mensaje.
"""
from src.config.rules_loader import get_welcome_config


def enviar_bienvenida(nombre_usuario: str, grupo: str | int | None):
    cfg = get_welcome_config(grupo)
    if not cfg.get("enabled", True):
        return {"type": "noop"}
    template = cfg.get("message", "¡Bienvenido/a {user}!")
    text = template.replace("{user}", str(nombre_usuario)).replace("{group}", str(grupo))
    if cfg.get("show_rules", False):
        title = cfg.get("title", "Reglas")
        text = f"{text}\n{title}"
    return {"text": text, "type": "reply"}
