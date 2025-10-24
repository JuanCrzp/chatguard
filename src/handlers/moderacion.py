"""Moderación configurable con escalado de acciones (comentarios en español).
Devuelve None si no hay violación, o un dict con acción sugerida.
Acciones posibles: delete, warn, mute, kick, ban.
Soporta: palabras prohibidas, patrones regex, whitelist, mensajes personalizados y ban temporal.
"""
from typing import Optional, Dict, Any
from src.config.rules_loader import get_moderation_config
from src.storage.repository import ModerationRepository
from src.utils.logging import log_event
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


def _cfg_nonempty_text(value: Optional[str]) -> Optional[str]:
    """Devuelve el texto si no está vacío/solo espacios; si no, None.
    Se usa para evitar mensajes por defecto: si el admin no configuró texto, no se envía nada.
    """
    if value is None:
        return None
    try:
        txt = str(value).strip()
        return txt if txt else None
    except Exception:
        return None


def _action_msg_allowed(cfg: Dict[str, Any], action: str) -> bool:
    try:
        return bool((cfg.get("action_messages_enabled", {}) or {}).get(str(action), True))
    except Exception:
        return True


def revisar_mensaje(mensaje: str, usuario: str, chat_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    # Cargar configuración al inicio para usarla en cualquier rama (ML y clásica)
    cfg = get_moderation_config(chat_id)
    # Guardas defensivas: si no hay usuario, no aplicar moderación (evita efectos globales)
    if not usuario:
        return None
    # --- Whitelist: si el usuario está exento, no aplicar moderación ---
    if usuario in set(cfg.get("whitelist_users", [])):
        return None

    # --- Chequeo inmediato de estado muteado ---
    # Si el usuario ya está muteado, NO re-aplicar sanciones ni ML. Solo política de soft-mute.
    if chat_id and moderation_repo.is_muted(str(chat_id), str(usuario)):
        # Modo override: siempre tratar como soft-mute directo
        if bool(cfg.get("muted_override_actions", False)):
            if bool(cfg.get("soft_mute_enforce_delete", False)):
                if bool(cfg.get("log_actions", True)):
                    try:
                        log_event("muted_soft_delete", chat_id=str(chat_id), user=str(usuario))
                    except Exception:
                        pass
                resp: Dict[str, Any] = {
                    "type": "moderation",
                    "action": "delete",
                    "delete": True,
                }
                # Solo incluir texto si el admin configuró alguno
                text = _cfg_nonempty_text(cfg.get("soft_mute_notice")) or _cfg_nonempty_text(cfg.get("muted_notice"))
                if text:
                    resp["text"] = text
                return resp
            if bool(cfg.get("muted_notice_enabled", False)):
                notice = _cfg_nonempty_text(cfg.get("muted_notice"))
                if bool(cfg.get("log_actions", True)):
                    try:
                        log_event("muted_notice", chat_id=str(chat_id), user=str(usuario))
                    except Exception:
                        pass
                if notice:
                    return {"type": "moderation", "action": "warn", "text": notice}
                return {"type": "moderation", "action": "noop"}
            return {"type": "moderation", "action": "noop"}
        # Sin override: comportamiento clásico (preferir delete si está activo)
        if bool(cfg.get("soft_mute_enforce_delete", False)):
            resp: Dict[str, Any] = {
                "type": "moderation",
                "action": "delete",
                "delete": True,
            }
            text = _cfg_nonempty_text(cfg.get("soft_mute_notice")) or _cfg_nonempty_text(cfg.get("muted_notice"))
            if text:
                resp["text"] = text
            return resp
        if bool(cfg.get("muted_notice_enabled", False)):
            notice = _cfg_nonempty_text(cfg.get("muted_notice"))
            if notice:
                return {"type": "moderation", "action": "warn", "text": notice}
            return {"type": "moderation", "action": "noop"}
        return {"type": "moderation", "action": "noop"}

    # --- ML: Naive Bayes configurable (se evalúa antes de las reglas clásicas) ---
    ml_cfg = cfg.get("ml", {}) or {}
    if bool(ml_cfg.get("enabled", False)):
        try:
            from src.ml.runtime import get_moderation_scorer
            scorer = get_moderation_scorer(str(chat_id or "global"), ml_cfg)
            scores = scorer.score(mensaje)
            tox_thr = float(ml_cfg.get("toxicity_threshold", 0.9))
            spam_thr = float(ml_cfg.get("spam_threshold", 0.9))
            is_toxic = scores.get("toxic", 0.0) >= tox_thr
            is_spam = scores.get("spam", 0.0) >= spam_thr
            # Política ML configurable:
            # - immediate: aplica la acción definida en ml.action de forma directa (no consume thresholds clásicos)
            # - thresholds: solo suma una infracción y respeta moderation.thresholds para decidir la sanción
            ml_mode = str(ml_cfg.get("ml_mode", "immediate")).lower()  # immediate | thresholds
            if bool(cfg.get("log_actions", True)):
                try:
                    log_event(
                        "ml_eval",
                        chat_id=str(chat_id or "global"),
                        user=str(usuario),
                        scores={"toxic": round(scores.get("toxic", 0.0), 3), "spam": round(scores.get("spam", 0.0), 3)},
                        toxicity_threshold=tox_thr,
                        spam_threshold=spam_thr,
                        triggered=bool(is_toxic or is_spam),
                        ml_mode=ml_mode,
                    )
                except Exception:
                    pass
            if is_toxic or is_spam:
                if ml_mode == "thresholds":
                    # Modo profesional: ML solo suma infracción y respeta thresholds clásicos
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

                    result: Dict[str, Any] = {"type": "moderation", "action": action, "reason": "ml_thresholds", "violations": count}
                    if cfg.get("delete_message_on_violation", True):
                        result["delete"] = True

                    if action == "warn":
                        custom = cfg.get("warn_message")
                        if _action_msg_allowed(cfg, "warn"):
                            if custom:
                                result["text"] = _fmt(custom, user=f"@{usuario}")
                            elif not bool(cfg.get("strict_message_config", False)):
                                result["text"] = f"Advertencia @{usuario}: tu mensaje viola las reglas."
                    elif action == "mute":
                        seconds = int(cfg.get("mute_duration_seconds", 600))
                        moderation_repo.set_muted(str(chat_id or "global"), str(usuario), seconds)
                        mute_msg = cfg.get("mute_message")
                        if _action_msg_allowed(cfg, "mute"):
                            if mute_msg:
                                result["text"] = _fmt(mute_msg, user=f"@{usuario}", minutes=seconds // 60, seconds=seconds)
                            elif not bool(cfg.get("strict_message_config", False)):
                                result["text"] = f"Usuario @{usuario} muteado por {seconds//60} min."
                        result["duration_seconds"] = seconds
                    elif action == "kick":
                        custom = cfg.get("kick_message")
                        if _action_msg_allowed(cfg, "kick"):
                            if custom:
                                result["text"] = _fmt(custom, user=f"@{usuario}")
                            elif not bool(cfg.get("strict_message_config", False)):
                                result["text"] = f"Usuario @{usuario} será expulsado del grupo."
                    elif action == "ban":
                        moderation_repo.set_banned(str(chat_id or "global"), str(usuario), True)
                        ban_seconds = int(cfg.get("ban_duration_seconds", 0))
                        if ban_seconds > 0:
                            result["until_seconds"] = ban_seconds
                        custom = cfg.get("ban_message")
                        if _action_msg_allowed(cfg, "ban"):
                            if custom:
                                result["text"] = _fmt(custom, user=f"@{usuario}", hours=ban_seconds // 3600, minutes=ban_seconds // 60, seconds=ban_seconds)
                            elif not bool(cfg.get("strict_message_config", False)):
                                result["text"] = (
                                    f"Usuario @{usuario} será baneado por {ban_seconds//3600} h." if ban_seconds > 0 else
                                    f"Usuario @{usuario} será baneado permanentemente."
                                )

                    if bool(cfg.get("log_actions", True)):
                        try:
                            log_event(
                                "ml_action_thresholds",
                                chat_id=str(chat_id or "global"),
                                user=str(usuario),
                                action=action,
                                violations=count,
                                scores={"toxic": round(scores.get("toxic", 0.0), 3), "spam": round(scores.get("spam", 0.0), 3)},
                            )
                        except Exception:
                            pass
                    return result
                else:
                    # Modo por defecto (inmediato): aplicar acción directa configurada
                    quick_action = str(ml_cfg.get("action", "warn")).lower()
                    result: Dict[str, Any] = {"type": "moderation", "action": quick_action, "reason": "ml"}
                    if bool(cfg.get("log_actions", True)):
                        try:
                            log_event(
                                "ml_action",
                                chat_id=str(chat_id or "global"),
                                user=str(usuario),
                                action=quick_action,
                                scores={"toxic": round(scores.get("toxic", 0.0), 3), "spam": round(scores.get("spam", 0.0), 3)},
                            )
                        except Exception:
                            pass
                    if bool(ml_cfg.get("delete_on_ml", True)) and cfg.get("delete_message_on_violation", True):
                        result["delete"] = True
                    if quick_action == "mute":
                        seconds = int(cfg.get("mute_duration_seconds", 600))
                        moderation_repo.set_muted(str(chat_id or "global"), str(usuario), seconds)
                        mute_msg = cfg.get("mute_message")
                        if _action_msg_allowed(cfg, "mute"):
                            if mute_msg:
                                result["text"] = _fmt(mute_msg, user=f"@{usuario}", minutes=seconds // 60, seconds=seconds)
                            elif not bool(cfg.get("strict_message_config", False)):
                                result["text"] = f"Usuario @{usuario} muteado por {seconds//60} min."
                        result["duration_seconds"] = seconds
                    elif quick_action == "warn":
                        custom = cfg.get("warn_message")
                        if _action_msg_allowed(cfg, "warn"):
                            if custom:
                                result["text"] = _fmt(custom, user=f"@{usuario}")
                            elif not bool(cfg.get("strict_message_config", False)):
                                result["text"] = f"Advertencia @{usuario}: tu mensaje viola las reglas."
                    elif quick_action == "kick":
                        custom = cfg.get("kick_message")
                        if _action_msg_allowed(cfg, "kick"):
                            if custom:
                                result["text"] = _fmt(custom, user=f"@{usuario}")
                            elif not bool(cfg.get("strict_message_config", False)):
                                result["text"] = f"Usuario @{usuario} será expulsado del grupo."
                    elif quick_action == "ban":
                        moderation_repo.set_banned(str(chat_id or "global"), str(usuario), True)
                        ban_seconds = int(cfg.get("ban_duration_seconds", 0))
                        if ban_seconds > 0:
                            result["until_seconds"] = ban_seconds
                        custom = cfg.get("ban_message")
                        if _action_msg_allowed(cfg, "ban"):
                            if custom:
                                result["text"] = _fmt(custom, user=f"@{usuario}", hours=ban_seconds // 3600, minutes=ban_seconds // 60, seconds=ban_seconds)
                            elif not bool(cfg.get("strict_message_config", False)):
                                result["text"] = (
                                    f"Usuario @{usuario} será baneado por {ban_seconds//3600} h." if ban_seconds > 0 else
                                    f"Usuario @{usuario} será baneado permanentemente."
                                )
                    else:
                        if _action_msg_allowed(cfg, quick_action) and not bool(cfg.get("strict_message_config", False)):
                            result["text"] = "Por favor, evita contenido no permitido."
                    return result
        except Exception:
            # Ante cualquier problema en ML, continuar con modo clásico sin romper flujo
            pass

    # Limpiar palabras prohibidas vacías para evitar matches universales
    banned_words = [w.lower() for w in cfg.get("banned_words", []) if str(w).strip()]
    # Aprendizaje manual (sin ML): unir listas definidas en rules.yaml (learning.toxic_words/spam_words)
    learning = cfg.get("learning", {}) or {}
    extra_words = []
    extra_words.extend([w.lower() for w in (learning.get("toxic_words", []) or []) if str(w).strip()])
    extra_words.extend([w.lower() for w in (learning.get("spam_words", []) or []) if str(w).strip()])
    if extra_words:
        banned_words.extend(extra_words)
    texto = (mensaje or "").lower()
    # --- Longitud máxima ---
    max_len = int(cfg.get("max_message_length", 0))
    if max_len > 0 and len(texto) > max_len:
        resp: Dict[str, Any] = {"type": "moderation", "action": "delete"}
        if _action_msg_allowed(cfg, "delete") and not bool(cfg.get("strict_message_config", False)):
            resp["text"] = "Mensaje demasiado largo."
        return resp

    # --- Antiflood: límite de mensajes por minuto ---
    flood_limit = int(cfg.get("flood_limit", 0))
    if flood_limit > 0 and chat_id:
        count = moderation_repo.register_message(str(chat_id), str(usuario), 60)
        if count > flood_limit:
            seconds = int(cfg.get("mute_duration_seconds", 600))
            moderation_repo.set_muted(str(chat_id), str(usuario), seconds)
            resp: Dict[str, Any] = {"type": "moderation", "action": "mute", "duration_seconds": seconds}
            if _action_msg_allowed(cfg, "mute"):
                mute_msg = cfg.get("mute_message")
                if mute_msg:
                    resp["text"] = _fmt(mute_msg, user=f"@{usuario}", minutes=seconds // 60, seconds=seconds)
                elif not bool(cfg.get("strict_message_config", False)):
                    resp["text"] = "Antiflood: mute temporal."
            return resp

    # --- Detección de 'gritos' por porcentaje de mayúsculas ---
    caps_thr = int(cfg.get("caps_lock_threshold", 0))
    if caps_thr > 0 and texto:
        letters = [c for c in mensaje if c.isalpha()]
        if letters:
            caps_ratio = sum(1 for c in letters if c.isupper()) * 100 // len(letters)
            if caps_ratio >= caps_thr:
                resp: Dict[str, Any] = {"type": "moderation", "action": "warn"}
                if _action_msg_allowed(cfg, "warn"):
                    if not bool(cfg.get("strict_message_config", False)):
                        resp["text"] = "Evita escribir en MAYÚSCULAS."
                return resp

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
                resp: Dict[str, Any] = {"type": "moderation", "action": "delete"}
                if _action_msg_allowed(cfg, "delete") and not bool(cfg.get("strict_message_config", False)):
                    resp["text"] = "Enlaces no permitidos."
                return resp
        except Exception:
            resp: Dict[str, Any] = {"type": "moderation", "action": "delete"}
            if _action_msg_allowed(cfg, "delete") and not bool(cfg.get("strict_message_config", False)):
                resp["text"] = "Enlaces no permitidos."
            return resp

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
                    resp: Dict[str, Any] = {
                        "type": "moderation",
                        "action": "delete",
                        "delete": True,
                    }
                    text = _cfg_nonempty_text(cfg.get("soft_mute_notice")) or _cfg_nonempty_text(cfg.get("muted_notice"))
                    if text:
                        resp["text"] = text
                    return resp
                if bool(cfg.get("muted_notice_enabled", False)):
                    notice = _cfg_nonempty_text(cfg.get("muted_notice"))
                    if notice:
                        return {"type": "moderation", "action": "warn", "text": notice}
                    return {"type": "moderation", "action": "noop"}
                return {"type": "moderation", "action": "noop"}
            # Sin override: comportamiento anterior
            if bool(cfg.get("soft_mute_enforce_delete", False)):
                resp: Dict[str, Any] = {
                    "type": "moderation",
                    "action": "delete",
                    "delete": True,
                }
                text = _cfg_nonempty_text(cfg.get("soft_mute_notice")) or _cfg_nonempty_text(cfg.get("muted_notice"))
                if text:
                    resp["text"] = text
                return resp
            if bool(cfg.get("muted_notice_enabled", False)):
                notice = _cfg_nonempty_text(cfg.get("muted_notice"))
                if notice:
                    return {"type": "moderation", "action": "warn", "text": notice}
                return {"type": "moderation", "action": "noop"}
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
        if _action_msg_allowed(cfg, "warn"):
            if custom:
                result["text"] = _fmt(custom, user=f"@{usuario}")
            elif not bool(cfg.get("strict_message_config", False)):
                result["text"] = f"Advertencia @{usuario}: tu mensaje viola las reglas."
    elif action == "mute":
        seconds = int(cfg.get("mute_duration_seconds", 600))
        moderation_repo.set_muted(str(chat_id or "global"), str(usuario), seconds)
        # Soporte opcional para mensaje personalizado de mute (mute_message) con {user} y {minutes}
        mute_msg = cfg.get("mute_message")
        if _action_msg_allowed(cfg, "mute"):
            if mute_msg:
                result["text"] = _fmt(mute_msg, user=f"@{usuario}", minutes=seconds // 60, seconds=seconds)
            elif not bool(cfg.get("strict_message_config", False)):
                result["text"] = f"Usuario @{usuario} muteado por {seconds//60} min."
        result["duration_seconds"] = seconds
    elif action == "kick":
        custom = cfg.get("kick_message")
        if _action_msg_allowed(cfg, "kick"):
            if custom:
                result["text"] = _fmt(custom, user=f"@{usuario}")
            elif not bool(cfg.get("strict_message_config", False)):
                result["text"] = f"Usuario @{usuario} será expulsado del grupo."
    elif action == "ban":
        moderation_repo.set_banned(str(chat_id or "global"), str(usuario), True)
        # Ban temporal si se configuró una duración > 0
        ban_seconds = int(cfg.get("ban_duration_seconds", 0))
        if ban_seconds > 0:
            result["until_seconds"] = ban_seconds
        custom = cfg.get("ban_message")
        if _action_msg_allowed(cfg, "ban"):
            if custom:
                result["text"] = _fmt(custom, user=f"@{usuario}", hours=ban_seconds // 3600, minutes=ban_seconds // 60, seconds=ban_seconds)
            elif not bool(cfg.get("strict_message_config", False)):
                result["text"] = (
                    f"Usuario @{usuario} será baneado por {ban_seconds//3600} h." if ban_seconds > 0 else
                    f"Usuario @{usuario} será baneado permanentemente."
                )

    return result
