"""Moderación configurable con escalado de acciones (comentarios en español).
Devuelve None si no hay violación, o un dict con acción sugerida.
Acciones posibles: delete, warn, mute, kick, ban.
Soporta: palabras prohibidas, patrones regex, whitelist, mensajes personalizados y ban temporal.
"""
from typing import Optional, Dict, Any
from src.config.rules_loader import get_moderation_config
from src.storage.repository import ModerationRepository
import re
from urllib.parse import urlparse

moderation_repo = ModerationRepository()


# Formateo seguro de plantillas con placeholders opcionales
class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def _fmt(template: str, **kwargs) -> str:
    try:
        return str(template).format_map(_SafeDict(**kwargs))
    except Exception:
        # Si algo falla, devuelve la plantilla cruda
        return str(template)


def revisar_mensaje(mensaje: str, usuario: str, chat_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    cfg = get_moderation_config(chat_id)
    # Guardas defensivas: si no hay usuario, no aplicar moderación (evita efectos globales)
    if not usuario:
        return None
    # --- Whitelist: si el usuario está exento, no aplicar moderación ---
    if usuario in set(cfg.get("whitelist_users", [])):
        return None

    # Limpiar palabras prohibidas vacías para evitar matches universales
    banned_words = [w.lower() for w in cfg.get("banned_words", []) if str(w).strip()]
    texto = (mensaje or "").lower()
    # --- Longitud máxima ---
    max_len = int(cfg.get("max_message_length", 0))
    if max_len > 0 and len(texto) > max_len:
        return {"type": "moderation", "action": "delete", "text": "Mensaje demasiado largo."}

    # --- Antiflood: límite de mensajes por minuto ---
    flood_limit = int(cfg.get("flood_limit", 0))
    if flood_limit > 0 and chat_id:
        count = moderation_repo.register_message(str(chat_id), str(usuario), 60)
        if count > flood_limit:
            seconds = int(cfg.get("mute_duration_seconds", 600))
            moderation_repo.set_muted(str(chat_id), str(usuario), seconds)
            return {"type": "moderation", "action": "mute", "duration_seconds": seconds, "text": "Antiflood: mute temporal."}

    # --- Detección de 'gritos' por porcentaje de mayúsculas ---
    caps_thr = int(cfg.get("caps_lock_threshold", 0))
    if caps_thr > 0 and texto:
        letters = [c for c in mensaje if c.isalpha()]
        if letters:
            caps_ratio = sum(1 for c in letters if c.isupper()) * 100 // len(letters)
            if caps_ratio >= caps_thr:
                return {"type": "moderation", "action": "warn", "text": "Evita escribir en MAYÚSCULAS."}

    # --- Enlaces y archivos ---
    allow_links = bool(cfg.get("allow_links", True))
    allow_files = bool(cfg.get("allow_files", True))
    invite_ok = bool(cfg.get("invite_links_allowed", True))
    link_whitelist = set(cfg.get("link_whitelist", []))

    def _has_url(t: str) -> Optional[str]:
        for token in t.split():
            if token.startswith("http://") or token.startswith("https://") or token.startswith("www."):
                return token
        return None

    url = _has_url(mensaje or "")
    if not allow_links and url:
        try:
            u = urlparse(url if url.startswith("http") else f"http://{url}")
            host = (u.netloc or u.path).lower()
            is_invite = ("t.me/joinchat" in url.lower()) or ("telegram.me/joinchat" in url.lower())
            whitelisted = any(host.endswith(dom.lower()) for dom in link_whitelist)
            if not (whitelisted or (invite_ok and is_invite)):
                return {"type": "moderation", "action": "delete", "text": "Enlaces no permitidos."}
        except Exception:
            return {"type": "moderation", "action": "delete", "text": "Enlaces no permitidos."}

    # Nota: detección de archivos adjuntos depende del conector; aquí asumimos texto plano.
    # --- Patrones prohibidos por regex ---
    regex_list = [p for p in (cfg.get("regex_patterns", []) or []) if str(p).strip()]
    regex_violation = any(re.search(pat, texto, flags=re.IGNORECASE) for pat in regex_list)
    # Chequeo muted: no borrar todos los mensajes automáticamente; solo aplicar reglas si hay nueva violación
    user_is_muted = bool(chat_id and moderation_repo.is_muted(str(chat_id), str(usuario)))

    # --- Violación por palabra prohibida o regex ---
    violation = any(w in texto for w in banned_words) or regex_violation
    if not violation:
        # Si está muteado y no hay nueva violación, aplicar política de mute
        if user_is_muted:
            # Modo override: siempre tratar como soft-mute directo
            if bool(cfg.get("muted_override_actions", False)):
                if bool(cfg.get("soft_mute_enforce_delete", False)):
                    return {
                        "type": "moderation",
                        "action": "delete",
                        "delete": True,
                        "text": cfg.get("soft_mute_notice") or cfg.get("muted_notice") or "Mensaje eliminado: usuario en mute.",
                    }
                if bool(cfg.get("muted_notice_enabled", False)):
                    notice = cfg.get("muted_notice") or "Estás muteado temporalmente."
                    return {"type": "moderation", "action": "warn", "text": notice}
                return {"type": "moderation", "action": "noop"}
            # Sin override: comportamiento anterior
            if bool(cfg.get("soft_mute_enforce_delete", False)):
                return {
                    "type": "moderation",
                    "action": "delete",
                    "delete": True,
                    "text": cfg.get("soft_mute_notice") or cfg.get("muted_notice") or "Mensaje eliminado: usuario en mute.",
                }
            if bool(cfg.get("muted_notice_enabled", False)):
                notice = cfg.get("muted_notice") or "Estás muteado temporalmente."
                return {"type": "moderation", "action": "warn", "text": notice}
        return None

    # Registrar infracción y decidir acción
    count = moderation_repo.add_violation(str(chat_id or "global"), str(usuario))
    th = cfg["thresholds"]

    action = "warn"
    if count >= th.get("ban", 4):
        action = "ban"
    elif count >= th.get("kick", 3):
        action = "kick"
    elif count >= th.get("mute", 2):
        action = "mute"
    elif count >= th.get("warn", 1):
        action = "warn"

    result: Dict[str, Any] = {"type": "moderation", "action": action}
    if cfg.get("delete_message_on_violation", True):
        result["delete"] = True

    if action == "warn":
        # Mensaje personalizado si está configurado (acepta {user})
        custom = cfg.get("warn_message")
        if custom:
            result["text"] = _fmt(custom, user=f"@{usuario}")
        else:
            result["text"] = f"Advertencia @{usuario}: tu mensaje viola las reglas."
    elif action == "mute":
        seconds = int(cfg.get("mute_duration_seconds", 600))
        moderation_repo.set_muted(str(chat_id or "global"), str(usuario), seconds)
        # Soporte opcional para mensaje personalizado de mute (mute_message) con {user} y {minutes}
        mute_msg = cfg.get("mute_message")
        if mute_msg:
            result["text"] = _fmt(mute_msg, user=f"@{usuario}", minutes=seconds // 60, seconds=seconds)
        else:
            result["text"] = f"Usuario @{usuario} muteado por {seconds//60} min."
        result["duration_seconds"] = seconds
    elif action == "kick":
        custom = cfg.get("kick_message")
        if custom:
            result["text"] = _fmt(custom, user=f"@{usuario}")
        else:
            result["text"] = f"Usuario @{usuario} será expulsado del grupo."
    elif action == "ban":
        moderation_repo.set_banned(str(chat_id or "global"), str(usuario), True)
        # Ban temporal si se configuró una duración > 0
        ban_seconds = int(cfg.get("ban_duration_seconds", 0))
        if ban_seconds > 0:
            result["until_seconds"] = ban_seconds
        custom = cfg.get("ban_message")
        if custom:
            result["text"] = _fmt(custom, user=f"@{usuario}", hours=ban_seconds // 3600, minutes=ban_seconds // 60, seconds=ban_seconds)
        else:
            result["text"] = (
                f"Usuario @{usuario} será baneado por {ban_seconds//3600} h." if ban_seconds > 0 else
                f"Usuario @{usuario} será baneado permanentemente."
            )

    return result
