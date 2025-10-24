from __future__ import annotations
import yaml
from pathlib import Path
from threading import Lock
from time import monotonic
from functools import lru_cache
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # .../Comunidad
RULES_FILE = PROJECT_ROOT / "config" / "rules.yaml"

# Hot-reload ligero sin dependencias: se verifica el mtime del archivo y, si cambia,
# se limpia el caché LRU automáticamente. Se limita la frecuencia de chequeo para rendimiento.
_RULES_LAST_MTIME_NS: Optional[int] = None
_RULES_LAST_CHECK_TS: float = 0.0
_RULES_CHECK_INTERVAL_SEC: float = 1.0  # evita stat() en cada llamada
_RULES_RELOAD_LOCK: Lock = Lock()


def _maybe_reload_rules_if_changed() -> None:
    global _RULES_LAST_MTIME_NS, _RULES_LAST_CHECK_TS
    now = monotonic()
    if (now - _RULES_LAST_CHECK_TS) < _RULES_CHECK_INTERVAL_SEC:
        return
    _RULES_LAST_CHECK_TS = now
    try:
        mtime_ns = RULES_FILE.stat().st_mtime_ns
    except FileNotFoundError:
        mtime_ns = None
    # Si hay cambio respecto al último visto, limpiar caché bajo lock
    if mtime_ns != _RULES_LAST_MTIME_NS:
        with _RULES_RELOAD_LOCK:
            # revalidar dentro del lock
            try:
                current_ns = RULES_FILE.stat().st_mtime_ns
            except FileNotFoundError:
                current_ns = None
            if current_ns != _RULES_LAST_MTIME_NS:
                reload_rules_cache()
                _RULES_LAST_MTIME_NS = current_ns


@lru_cache(maxsize=1)
def _load_rules() -> Dict[str, Any]:
    if not RULES_FILE.exists():
        return {}
    with open(RULES_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # Normalizar claves de primer nivel a str (para soportar chat_id numérico sin comillas)
    try:
        data = {str(k): v for k, v in data.items()}
    except Exception:
        pass
    return data


def reload_rules_cache() -> None:
    _load_rules.cache_clear()  # type: ignore[attr-defined]


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge profundo no destructivo. Copia base y aplica override recursivamente.
    - Para dicts: combina claves; override gana ante conflictos.
    - Para listas y escalares: override reemplaza completamente.
    """
    if not isinstance(base, dict):
        base = {}
    if not isinstance(override, dict):
        return dict(base)
    merged: Dict[str, Any] = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            merged[k] = _deep_merge(base.get(k, {}), v)
        else:
            merged[k] = v
    return merged


def get_chat_rules(chat_id: Optional[int | str]) -> Optional[Dict[str, Any]]:
    # Hot-reload: antes de leer, validar si el YAML cambió y limpiar caché si corresponde
    _maybe_reload_rules_if_changed()
    data = _load_rules()
    key = str(chat_id) if chat_id is not None else "default"
    # Herencia: default -> override (deep merge). Si no hay override, usar default.
    default_rules = data.get("default") or {}
    override_rules = data.get(key)
    if override_rules is None:
        return default_rules or None
    # Si existe override, aplicar merge profundo para heredar faltantes.
    try:
        return _deep_merge(default_rules, override_rules)
    except Exception:
        # fallback conservador si algo falla
        return override_rules or default_rules or None


def get_welcome_config(chat_id: Optional[int | str]) -> Dict[str, Any]:
    rules = get_chat_rules(chat_id) or {}
    w = rules.get("welcome", {}) or {}
    return {
        "enabled": bool(w.get("enabled", True)),
        "message": w.get("message", "¡Bienvenido/a {user}!"),
        "show_rules": bool(w.get("show_rules", False)),
        "title": rules.get("title", "Reglas"),
        # Solo aplica para Discord: canal al que enviar la bienvenida (si no se define, usa system_channel o primer canal de texto)
        "channel_id": w.get("channel_id"),
    }


def get_survey_config(chat_id: Optional[int | str]) -> Dict[str, Any]:
    rules = get_chat_rules(chat_id) or {}
    s = rules.get("survey", {}) or {}
    return {
        "enabled": bool(s.get("enabled", True)),
        "max_options": int(s.get("max_options", 10)),
        "allow_multiple": bool(s.get("allow_multiple", False)),
        "anonymous": bool(s.get("anonymous", False)),
        "create_message": s.get("create_message", "Encuesta creada: {question}"),
        "vote_message": s.get("vote_message", "Voto registrado: {user} eligió '{option}'"),
    }


def get_moderation_config(chat_id: Optional[int | str]) -> Dict[str, Any]:
    rules = get_chat_rules(chat_id) or {}
    mod = rules.get("moderation", {}) or {}
    # Defaults
    return {
        # Habilitar/deshabilitar bot por chat (nivel superior preferido; soporta fallback en moderation)
        "enabled": bool(rules.get("enabled", mod.get("enabled", True))),
        "thresholds": {
            "warn": int(mod.get("thresholds", {}).get("warn", 1)),
            "mute": int(mod.get("thresholds", {}).get("mute", 2)),
            "kick": int(mod.get("thresholds", {}).get("kick", 3)),
            "ban": int(mod.get("thresholds", {}).get("ban", 4)),
        },
        "mute_duration_seconds": int(mod.get("mute_duration_seconds", 600)),
        "banned_words": list(mod.get("banned_words", ["spam", "oferta", "prohibido"])),
        "delete_message_on_violation": bool(mod.get("delete_message_on_violation", True)),
        # Si true, en grupos el bot solo actúa ante violaciones (no responde saludos ni conversa)
        # Permitir configurarlo también a nivel superior (compatibilidad y simplicidad en rules.yaml)
        "enforce_only": bool(
            mod.get("enforce_only")
            if mod.get("enforce_only") is not None
            else rules.get("enforce_only", False)
        ),
        # Habilitar saludos de bienvenida
        "greetings_enabled": bool(mod.get("greetings_enabled", rules.get("greetings_enabled", True))),
        # Límite de mensajes por minuto por usuario (0 = desactivado)
        "flood_limit": int(mod.get("flood_limit", 0)),
        # Lista de usuarios exentos de moderación (usernames o IDs)
        "whitelist_users": list(mod.get("whitelist_users", [])),
        # Permitir enlaces y archivos adjuntos
        "allow_links": bool(mod.get("allow_links", rules.get("allow_links", True))),
        "allow_files": bool(mod.get("allow_files", rules.get("allow_files", True))),
        # Expresiones regulares prohibidas (aplican sobre texto normalizado)
        "regex_patterns": list(mod.get("regex_patterns", [])),
        # Duración de ban temporal en segundos (0 = permanente)
        "ban_duration_seconds": int(mod.get("ban_duration_seconds", 0)),
        # Para acción "kick": segundos de reingreso permitido. >0 = expulsión temporal (simulada con ban corto + desban). 0 o <0 = ban permanente (no puede volver).
        "kick_rejoin_seconds": int(mod.get("kick_rejoin_seconds", 60)),
    # Notificar a administradores cuando se aplica sanción
    "admin_notify": bool(mod.get("admin_notify", False)),
    "admin_notify_chat_id": mod.get("admin_notify_chat_id"),   # Telegram
    "admin_notify_channel_id": mod.get("admin_notify_channel_id"),  # Discord
        # Registrar acciones (logs/auditoría)
        "log_actions": bool(mod.get("log_actions", True)),
        # Mostrar mensajes públicos al aplicar acciones (por acción)
        "action_messages_enabled": {
            "warn": bool((mod.get("action_messages_enabled", {}) or {}).get("warn", True)),
            "mute": bool((mod.get("action_messages_enabled", {}) or {}).get("mute", True)),
            "kick": bool((mod.get("action_messages_enabled", {}) or {}).get("kick", True)),
            "ban": bool((mod.get("action_messages_enabled", {}) or {}).get("ban", True)),
            # Permite controlar también los textos en acciones de eliminación directa
            "delete": bool((mod.get("action_messages_enabled", {}) or {}).get("delete", True)),
        },
        # Modo estricto: no generar textos por defecto. Solo se envían textos si están configurados en rules.yaml
        "strict_message_config": bool(mod.get("strict_message_config", False)),
        # Mensajes personalizados por acción
        "warn_message": mod.get("warn_message"),
        "mute_message": mod.get("mute_message"),
        "kick_message": mod.get("kick_message"),
        "ban_message": mod.get("ban_message"),
        # Aviso a muteados (alias soportado: muted_notice_message)
        "muted_notice_enabled": bool(mod.get("muted_notice_enabled", False)),
        "muted_notice": (
            mod.get("muted_notice_message")
            if mod.get("muted_notice_message") is not None
            else mod.get("muted_notice", "Estás muteado temporalmente.")
        ),
        # Si true: mientras esté muteado, cualquier mensaje se procesa como soft-mute directo
        "muted_override_actions": bool(mod.get("muted_override_actions", False)),
        # Soft mute: borrar mensaje si la restricción de la plataforma no aplica
        "soft_mute_enforce_delete": bool(mod.get("soft_mute_enforce_delete", False)),
        "soft_mute_notice": mod.get("soft_mute_notice", "Mensaje eliminado: usuario en mute temporal."),
        # Tipos de mute ("text", "media", "all")
        "mute_types": list(mod.get("mute_types", ["all"])),
        # Longitud máxima de mensaje (0 = sin límite). Acepta en moderation o a nivel de reglas.
        "max_message_length": int(mod.get("max_message_length", rules.get("max_message_length", 0))),
        # Lista blanca de dominios permitidos cuando allow_links=false (en moderation o a nivel de reglas)
        "link_whitelist": list(mod.get("link_whitelist", rules.get("link_whitelist", []))),
        # Permitir enlaces de invitación (ej: t.me/joinchat) (en moderation o a nivel de reglas)
        "invite_links_allowed": bool(mod.get("invite_links_allowed", rules.get("invite_links_allowed", True))),
    # Porcentaje de MAYÚSCULAS para considerar 'gritos' (0=desactivado) (en moderation o a nivel de reglas)
    "caps_lock_threshold": int(mod.get("caps_lock_threshold", rules.get("caps_lock_threshold", 0))),
    # Configuración ML (Naive Bayes): se expone tal cual para el handler
    "ml": (mod.get("ml", {}) or {}),
        # Aprendizaje manual de palabras (sin ML): se combinan con banned_words en el handler
        "learning": {
            "toxic_words": list((mod.get("learning", {}) or {}).get("toxic_words", [])),
            "spam_words": list((mod.get("learning", {}) or {}).get("spam_words", [])),
        },
    }


def get_saas_config(chat_id: Optional[int | str]) -> Dict[str, Any]:
    rules = get_chat_rules(chat_id) or {}
    s = rules.get("saas", {}) or {}
    branding = s.get("branding", {}) or {}
    return {
        "tenant_id": s.get("tenant_id", "default-tenant"),
        "plan": s.get("plan", "free"),
        "branding": {
            "footer_enabled": bool(branding.get("footer_enabled", False)),
            "footer_text": branding.get("footer_text", ""),
        },
    }


def get_features_config(chat_id: Optional[int | str]) -> Dict[str, Any]:
    """Devuelve switches de funciones conversacionales/UX.
    Compatibilidad: si no existe sección 'features', usa claves de welcome/survey/moderation.
    """
    rules = get_chat_rules(chat_id) or {}
    f = rules.get("features", {}) or {}
    welcome = rules.get("welcome", {}) or {}
    survey = rules.get("survey", {}) or {}
    # Compat: algunos proyectos usaban moderation.greetings_enabled
    moderation = rules.get("moderation", {}) or {}
    return {
        # Comando /reglas o equivalente
        "rules_command_enabled": bool(f.get("rules_command_enabled", True)),
        # Responder con fallback "No entendí"
        "fallback_enabled": bool(f.get("fallback_enabled", True)),
        # Saludos por intención 'greeting'
        "greeting_enabled": bool(f.get("greeting_enabled", moderation.get("greetings_enabled", True))),
        # Bienvenida (on_member_join / /start)
        "welcome_enabled": bool(f.get("welcome_enabled", welcome.get("enabled", True))),
        # Encuestas automáticas/por intención
        "survey_enabled": bool(f.get("survey_enabled", survey.get("enabled", True))),
        # Sorteos (intent 'raffle')
        "raffle_enabled": bool(f.get("raffle_enabled", True)),
    }
