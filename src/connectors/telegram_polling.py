# coding: utf-8
"""
Bot de Telegram en modo polling para desarrollo local (python-telegram-bot v20+).
Lee mensajes y los reenvía al BotManager para procesar y responder.
"""
import os
import sys
from pathlib import Path
import yaml
from dotenv import load_dotenv
import logging
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from datetime import datetime, timedelta, timezone

# Asegurar que el paquete 'src' sea importable cuando se ejecuta este archivo directamente
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # .../Comunidad
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Importar después de ajustar sys.path
from src.bot_core.manager import BotManager
from src.handlers.bienvenida import enviar_bienvenida
from src.handlers.moderacion import moderation_repo
from src.storage.repository import audit_repo
from src.config.rules_loader import get_moderation_config, reload_rules_cache, get_features_config

# Cargar variables de entorno desde .env en la raíz de Comunidad
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "<TU_TOKEN_AQUI>")
TELEGRAM_BOT_NAME = os.getenv("TELEGRAM_BOT_NAME", "BotComunidad")

# Lista opcional de IDs de administradores (separados por coma o punto y coma) para comandos de moderación
def _parse_admin_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    if not raw:
        return ids
    for part in raw.replace(";", ",").split(","):
        p = part.strip()
        if not p:
            continue
        try:
            ids.add(int(p))
        except Exception:
            # Ignorar entradas inválidas
            pass
    return ids

ADMIN_WHITELIST: set[int] = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("telegram_polling")

bot_manager = BotManager()

# Cargar reglas desde config/rules.yaml
RULES_FILE = PROJECT_ROOT / "config" / "rules.yaml"
def cargar_reglas(chat_id: str | int | None):
    try:
        if not RULES_FILE.exists():
            return None
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        key = str(chat_id) if chat_id is not None else "default"
        reglas = data.get(key) or data.get("default")
        return reglas
    except Exception as e:
        logger.warning(f"No se pudieron cargar reglas: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id if update.effective_chat else None
    text = update.message.text or ""
    # Imprime el chat_id en consola para identificar el grupo
    print(f"[INFO] chat_id del grupo: {chat_id}")
    # Si el bot está deshabilitado para este chat, ignorar mensajes
    try:
        cfg = get_moderation_config(chat_id)
        if not cfg.get("enabled", True):
            return
    except Exception:
        pass
    chat_type = getattr(update.effective_chat, "type", "") if update.effective_chat else ""
    is_group = chat_type in ("group", "supergroup")
    payload = {
        "platform": "telegram",
        "platform_user_id": str(user_id),
        "group_id": str(chat_id) if chat_id is not None else "",
        "text": text,
        "attachments": None,
        "raw_payload": None,
        "is_group": is_group,
    }
    logger.info(f"[{TELEGRAM_BOT_NAME}] Mensaje recibido de {user_id}: {text}")
    response = bot_manager.process_message(payload)
    # Enviar respuesta al usuario
    reply_text = None
    # Soporta respuesta directa o anidada bajo 'response'
    if response:
        if isinstance(response, dict) and "response" in response and isinstance(response["response"], dict):
            reply_text = response["response"].get("text")
        elif isinstance(response, dict) and "text" in response:
            reply_text = response["text"]
    # Si la respuesta es moderación o aviso, no enviar el fallback de "No entendí"
    if isinstance(response, dict) and response.get("type") == "moderation":
        pass  # el flujo de moderación se encarga de enviar lo necesario
    elif reply_text and not (isinstance(response, dict) and response.get("type") == "noop"):
        # Guardia adicional: respetar enforce_only en grupos/supergrupos incluso si algún handler generó 'reply'
        try:
            chat_type = getattr(update.effective_chat, "type", "") or ""
            is_group = chat_type in ("group", "supergroup")
            cfg_guard = get_moderation_config(chat_id)
            if is_group and bool(cfg_guard.get("enforce_only", False)):
                # No enviar respuestas conversacionales en modo enforce_only
                logger.info("[telegram] Respuesta suprimida por enforce_only en grupo")
                return
        except Exception:
            pass
        await update.message.reply_text(reply_text)
        logger.info(f"[{TELEGRAM_BOT_NAME}] Respondido a {user_id}: {reply_text}")
    else:
        # Fallback solo si no es noop y no hay moderación/aviso
        if not (isinstance(response, dict) and response.get("type") in ("noop", "moderation")):
            # Respetar enforce_only en grupos: no enviar fallback
            try:
                chat_type = getattr(update.effective_chat, "type", "") or ""
                is_group = chat_type in ("group", "supergroup")
                if is_group and bool(cfg.get("enforce_only", False)):
                    logger.info("[telegram] Fallback suprimido por enforce_only en grupo")
                    return
            except Exception:
                pass
            # Respetar switch de características para fallback
            try:
                feats = get_features_config(chat_id)
                if not feats.get("fallback_enabled", True):
                    logger.info("[telegram] Fallback deshabilitado por features.fallback_enabled=false")
                    return
            except Exception:
                pass
            await update.message.reply_text("No entendí tu mensaje. Usa 'ayuda' para opciones.")
            logger.warning(f"[{TELEGRAM_BOT_NAME}] Sin respuesta para {user_id}")
    # Aplicar acciones de moderación si corresponde
    if isinstance(response, dict) and response.get("type") == "moderation":
        await apply_moderation_action(update, context, response)

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_name = user.username or (user.full_name if hasattr(user, 'full_name') else str(user.id))
    chat_id = update.effective_chat.id if update.effective_chat else ""
    cfg = get_moderation_config(chat_id)
    if not cfg.get("enabled", True):
        return
    try:
        feats = get_features_config(chat_id)
        if not feats.get("welcome_enabled", True):
            return
    except Exception:
        pass
    # Usa el handler de bienvenida existente para consistencia de copy
    result = enviar_bienvenida(user_name, chat_id)
    text = result.get("text", "¡Bienvenido!")
    await update.message.reply_text(text)

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Comandos disponibles:\n"
        "/start - Mensaje de bienvenida y reglas\n"
        "/help - Mostrar esta ayuda\n"
        "/modhelp - Ayuda de moderación\n\n"
        "Moderación (admins): /warn, /mute [min], /unmute, /kick, /ban, /unban, /reload\n\n"
        "Prueba también: 'hola', 'encuesta', 'sorteo'"
    )
    await update.message.reply_text(help_text)


async def is_user_admin(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return str(member.status) in ("administrator", "creator", "owner")
    except Exception:
        return False


async def apply_moderation_action(update: Update, context: ContextTypes.DEFAULT_TYPE, info: dict):
    if not update.message:
        return
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return
    chat_id = chat.id
    user_id = user.id
    action = info.get("action")
    # Borrar mensaje si se indica
    if info.get("delete"):
        try:
            await update.message.delete()
        except Exception as e:
            logger.warning(f"No se pudo borrar el mensaje: {e}")
        # Si además hay un texto de aviso (por ejemplo en soft-mute), enviarlo al chat
        try:
            notify_text = info.get("text")
            # Evitar duplicados: si la acción es 'warn', el bloque específico de 'warn'
            # se encargará de enviar el mensaje una sola vez.
            if notify_text and action != "warn":
                await context.bot.send_message(chat_id, notify_text)
        except Exception as e:
            logger.warning(f"No se pudo enviar aviso de borrado: {e}")
    # No aplicar medidas duras a admins
    offender_is_admin = await is_user_admin(context, chat_id, user_id)
    if offender_is_admin and action in ("kick", "ban", "mute"):
        logger.info("Usuario objetivo es admin; se omiten acciones duras.")
        return
    # Ejecutar acción
    # Registrar auditoría básica
    try:
        audit_repo.add_action(bot_id=os.getenv("TELEGRAM_BOT_NAME", "bot"), group_id=str(chat_id), user_id=str(user_id), action=action or "unknown", reason=info.get("text", ""))
    except Exception:
        pass

    # Notificación a administradores (simple): reenvía al chat si admin_notify
    try:
        cfg = get_moderation_config(chat_id)
        if cfg.get("admin_notify", False):
            dest_id = cfg.get("admin_notify_chat_id") or chat_id
            await context.bot.send_message(dest_id, f"[MOD] acción={action} usuario={user.username or user_id} motivo={info.get('text','')}")
    except Exception:
        pass

    if action == "kick":
        try:
            # Comportamiento de kick configurable por reglas
            cfg_rules = get_moderation_config(chat_id)
            rejoin_seconds = int(cfg_rules.get("kick_rejoin_seconds", 60))
            if rejoin_seconds and rejoin_seconds > 0:
                # Expulsión temporal: ban corto + desban para permitir reingreso luego
                until = datetime.now(tz=timezone.utc) + timedelta(seconds=rejoin_seconds)
                await context.bot.ban_chat_member(chat_id, user_id, until_date=until)
                await context.bot.unban_chat_member(chat_id, user_id)
            else:
                # Si es 0 o negativo: tratar el kick como ban permanente
                await context.bot.ban_chat_member(chat_id, user_id)
        except Exception as e:
            logger.warning(f"Kick falló: {e}")
    elif action == "ban":
        try:
            # Soportar ban temporal si viene 'until_seconds' en info
            until_seconds = int(info.get("until_seconds", 0))
            if until_seconds and until_seconds > 0:
                until = datetime.now(tz=timezone.utc) + timedelta(seconds=until_seconds)
                await context.bot.ban_chat_member(chat_id, user_id, until_date=until)
            else:
                await context.bot.ban_chat_member(chat_id, user_id)
        except Exception as e:
            logger.warning(f"Ban falló: {e}")
    elif action == "mute":
        try:
            seconds = int(info.get("duration_seconds", 600))
            until = datetime.now(tz=timezone.utc) + timedelta(seconds=seconds)
            perms = ChatPermissions(can_send_messages=False)
            await context.bot.restrict_chat_member(chat_id, user_id, permissions=perms, until_date=until)
        except Exception as e:
            logger.warning(f"Mute falló: {e}")
    elif action == "warn":
        try:
            text = info.get("text") or "Por favor, respeta las reglas."
            await context.bot.send_message(chat_id, text)
        except Exception as e:
            logger.warning(f"Warn falló: {e}")


def _extract_target_user(update: Update):
    # Preferir respuesta a un mensaje
    if update.message and update.message.reply_to_message:
        u = update.message.reply_to_message.from_user
        return (u, u.id)
    # O primer argumento como @username no resuelve ID sin API extra
    # Por simplicidad, si no hay reply devolvemos None
    return (None, None)


async def _require_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not update.effective_chat or not update.effective_user:
        return False
    # Admin por rol de Telegram o por whitelist en ADMIN_IDS
    chat_admin = await is_user_admin(context, update.effective_chat.id, update.effective_user.id)
    whitelisted = update.effective_user.id in ADMIN_WHITELIST
    is_admin = chat_admin or whitelisted
    if not is_admin and update.message:
        await update.message.reply_text("Solo administradores pueden usar este comando.")
    return is_admin


async def handle_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    target, target_id = _extract_target_user(update)
    if not target_id:
        await update.message.reply_text("Responde al mensaje del usuario para advertirlo.")
        return
    chat_id = update.effective_chat.id
    count = moderation_repo.add_violation(str(chat_id), str(target_id))
    await update.message.reply_text(f"Advertencia para @{target.username or target_id}. Infracciones: {count}")


async def handle_mute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    target, target_id = _extract_target_user(update)
    if not target_id:
        await update.message.reply_text("Responde al mensaje del usuario para mutearlo.")
        return
    minutes = 10
    try:
        if context.args:
            minutes = max(1, int(context.args[0]))
    except Exception:
        minutes = 10
    seconds = minutes * 60
    try:
        until = datetime.now(tz=timezone.utc) + timedelta(seconds=seconds)
        perms = ChatPermissions(can_send_messages=False)
        await context.bot.restrict_chat_member(update.effective_chat.id, target_id, permissions=perms, until_date=until)
        moderation_repo.set_muted(str(update.effective_chat.id), str(target_id), seconds)
        await update.message.reply_text(f"Usuario muteado por {minutes} min.")
    except Exception as e:
        await update.message.reply_text(f"No se pudo aplicar mute: {e}")


async def handle_unmute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    target, target_id = _extract_target_user(update)
    if not target_id:
        await update.message.reply_text("Responde al mensaje del usuario para desmutearlo.")
        return
    try:
        perms = ChatPermissions(can_send_messages=True)
        await context.bot.restrict_chat_member(update.effective_chat.id, target_id, permissions=perms)
        moderation_repo.reset(str(update.effective_chat.id), str(target_id))
        await update.message.reply_text("Usuario desmuteado.")
    except Exception as e:
        await update.message.reply_text(f"No se pudo desmutear: {e}")


async def handle_kick_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    target, target_id = _extract_target_user(update)
    if not target_id:
        await update.message.reply_text("Responde al mensaje del usuario para expulsarlo.")
        return
    try:
        until = datetime.now(tz=timezone.utc) + timedelta(seconds=60)
        await context.bot.ban_chat_member(update.effective_chat.id, target_id, until_date=until)
        await context.bot.unban_chat_member(update.effective_chat.id, target_id)
        await update.message.reply_text("Usuario expulsado.")
    except Exception as e:
        await update.message.reply_text(f"No se pudo expulsar: {e}")


async def handle_ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    target, target_id = _extract_target_user(update)
    if not target_id:
        await update.message.reply_text("Responde al mensaje del usuario para banearlo.")
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target_id)
        await update.message.reply_text("Usuario baneado permanentemente.")
    except Exception as e:
        await update.message.reply_text(f"No se pudo banear: {e}")


async def handle_unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return
    target, target_id = _extract_target_user(update)
    if not target_id:
        await update.message.reply_text("Responde al mensaje del usuario para desbanearlo (o proporciona el ID si fue removido).")
        return
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, target_id)
        await update.message.reply_text("Usuario desbaneado.")
    except Exception as e:
        await update.message.reply_text(f"No se pudo desbanear: {e}")

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Da la bienvenida cuando entran nuevos miembros al grupo."""
    if not update.message or not update.message.new_chat_members:
        return
    chat_id = update.effective_chat.id if update.effective_chat else ""
    cfg = get_moderation_config(chat_id)
    try:
        feats = get_features_config(chat_id)
        if not feats.get("welcome_enabled", True):
            return
    except Exception:
        pass
    for user in update.message.new_chat_members:
        user_name = user.username or (user.full_name if hasattr(user, 'full_name') else str(user.id))
        result = enviar_bienvenida(user_name, chat_id)
        text = result.get("text", f"¡Bienvenido/a {user_name}!")
        await update.message.reply_text(text)

async def handle_reglas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id if update.effective_chat else None
    cfg = get_moderation_config(chat_id)
    if not cfg.get("enabled", True):
        return
    # Switch de características: permitir desactivar /reglas por chat
    feats = get_features_config(chat_id)
    if not feats.get("rules_command_enabled", True):
        return
    reglas = cargar_reglas(chat_id)
    if not reglas:
        await update.message.reply_text("No hay reglas configuradas.")
        return
    title = reglas.get("title", "Reglas")
    items = reglas.get("items", [])
    texto = title + "\n" + "\n".join([f"- {i}" for i in items])
    await update.message.reply_text(texto)

async def handle_reload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Solo administradores pueden recargar reglas
    if not await _require_admin(update, context):
        return
    try:
        reload_rules_cache()
        await update.message.reply_text("Reglas recargadas desde config/rules.yaml")
    except Exception as e:
        await update.message.reply_text(f"No se pudieron recargar reglas: {e}")

def main():
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "<TU_TOKEN_AQUI>":
        logger.error("TELEGRAM_TOKEN no configurado. Define el token en el archivo .env o variable de entorno.")
        raise SystemExit(1)

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(CommandHandler("help", handle_help))
    application.add_handler(CommandHandler("modhelp", handle_help))
    application.add_handler(CommandHandler("reglas", handle_reglas))
    application.add_handler(CommandHandler("reload", handle_reload))
    # Comandos de moderación (admins)
    application.add_handler(CommandHandler("warn", handle_warn))
    application.add_handler(CommandHandler("mute", handle_mute_cmd))
    application.add_handler(CommandHandler("unmute", handle_unmute_cmd))
    application.add_handler(CommandHandler("kick", handle_kick_cmd))
    application.add_handler(CommandHandler("ban", handle_ban_cmd))
    application.add_handler(CommandHandler("unban", handle_unban_cmd))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info(f"Bot de Telegram '{TELEGRAM_BOT_NAME}' iniciado en modo polling.")
    application.run_polling()

if __name__ == "__main__":
    main()
