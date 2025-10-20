import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Asegurar imports de 'src.*'
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # .../bots/Comunidad
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT.parent))

from dotenv import load_dotenv  # type: ignore
# Cargar .env desde la carpeta Comunidad explícitamente con tolerancia a errores
env_path = PROJECT_ROOT / ".env"
try:
    load_dotenv(env_path)
except Exception as e:
    # No detener el arranque por errores de parseo; intentamos parseo manual abajo
    print(f"[discord_connector] Aviso: error cargando .env con python-dotenv: {e}")

# Fallback: si no quedó DISCORD_TOKEN, intentar parseo manual simple (KEY=VALUE)
if not os.getenv("DISCORD_TOKEN"):
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip()
                    # Quitar comillas envolventes si existen
                    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                        v = v[1:-1]
                    os.environ.setdefault(k, v)
    except Exception as e:
        print(f"[discord_connector] Aviso: error en parseo manual de .env: {e}")

import asyncio
import logging
import discord  # type: ignore

from src.bot_core.manager import BotManager
from src.config.rules_loader import get_welcome_config, get_moderation_config, get_saas_config, get_features_config
from src.storage.repository import audit_repo  # registrar acciones


logger = logging.getLogger("discord_connector")
logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO))
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
            pass
    return ids

ADMIN_WHITELIST: set[int] = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))



def _get_group_id(message: discord.Message) -> str:
    if message.guild:
        return str(message.guild.id)
    # DM: usar canal como grupo lógico
    return str(message.channel.id)


def _is_admin(member: discord.Member | None) -> bool:
    try:
        if not member:
            return False
        if member.id in ADMIN_WHITELIST:
            return True
        perms = member.guild_permissions
        return bool(perms.administrator or perms.kick_members or perms.ban_members or getattr(perms, "moderate_members", False))
    except Exception:
        return False


async def _resolve_target_member(message: discord.Message) -> tuple[discord.Member | None, int | None]:
    """Resuelve el usuario objetivo a partir de una respuesta o mención.
    Prioriza reply; si no hay, usa la primera mención. Devuelve (member, id).
    """
    try:
        # Reply (message reference)
        if message.reference and message.reference.resolved:
            ref = message.reference.resolved  # type: ignore[assignment]
            if isinstance(ref, discord.Message) and isinstance(ref.author, discord.Member):
                return ref.author, ref.author.id
        # Primera mención
        if getattr(message, "mentions", None):
            for m in message.mentions:
                if isinstance(m, discord.Member):
                    return m, m.id
        # Como fallback, intentar parsear un ID numérico en el contenido
        for tok in (message.content or "").split():
            tok = tok.strip("<@!>&# ")
            if tok.isdigit() and message.guild:
                try:
                    mem = message.guild.get_member(int(tok))
                    if not mem:
                        mem = await message.guild.fetch_member(int(tok))
                    if isinstance(mem, discord.Member):
                        return mem, mem.id
                except Exception:
                    pass
    except Exception:
        return None, None
    return None, None


async def apply_moderation_action(message: discord.Message, action: dict):
    """Aplica acciones de moderación devueltas por el manager.
    action: {
      type: 'moderation', action: 'delete|warn|mute|kick|ban',
      reason?: str, duration_seconds?: int
    }
    """
    act = action.get("action")
    reason = action.get("reason") or action.get("motivo") or "Moderation rule"
    duration = int(action.get("duration_seconds") or action.get("mute_duration_seconds") or 0)
    member: discord.Member | None = None
    if message.guild and isinstance(message.author, discord.Member):
        member = message.author

    try:
        # Respetar bandera 'delete' si viene desde el motor de moderación
        should_delete = bool(action.get("delete", False))
        if act == "delete" or should_delete:
            # Borrar el mensaje y si hay texto de aviso, enviarlo como mensaje independiente del canal
            await message.delete()
            notify_text = action.get("text")
            # Evitar duplicados: si la acción principal es 'warn', el bloque de 'warn'
            # se encargará de enviar el mensaje de advertencia una sola vez.
            if notify_text and act != "warn":
                # Branding footer opcional
                if message.guild:
                    saas = get_saas_config(str(message.guild.id))
                    b = saas.get("branding", {})
                    if b.get("footer_enabled") and b.get("footer_text"):
                        notify_text = f"{notify_text}\n{b['footer_text']}"
                await message.channel.send(notify_text)
        elif act == "warn":
            # Enviar aviso como mensaje de canal (no como reply) para evitar confusión
            txt = action.get("text") or "Por favor, respeta las reglas."
            if message.guild:
                saas = get_saas_config(str(message.guild.id))
                b = saas.get("branding", {})
                if b.get("footer_enabled") and b.get("footer_text"):
                    txt = f"{txt}\n{b['footer_text']}"
            await message.channel.send(txt)
        elif act == "mute" and member:
            # Timeout del usuario por duration segundos (si hay soporte)
            dur = max(duration, 60)
            until = datetime.now(timezone.utc) + timedelta(seconds=dur)
            # Obtener mensaje personalizado de mute si viene en action.text, si no, usar plantilla
            mute_msg = action.get("text")
            if not mute_msg:
                # Intentar obtener la plantilla desde rules.yaml
                from src.config.rules_loader import get_moderation_config
                cfg = get_moderation_config(str(message.guild.id))
                mute_msg = cfg.get("mute_message", "Usuario silenciado por {minutes} min.")
                mute_msg = mute_msg.replace("{user}", f"@{member.display_name}")
                mute_msg = mute_msg.replace("{minutes}", str(dur // 60)).replace("{seconds}", str(dur))
            try:
                # discord.py >=2.2: Member.timeout()
                if hasattr(member, "timeout") and callable(getattr(member, "timeout")):
                    await member.timeout(until, reason=reason)  # type: ignore[attr-defined]
                else:
                    # Fallback: edit communication_disabled_until
                    await member.edit(communication_disabled_until=until, reason=reason)
                if message.guild:
                    saas = get_saas_config(str(message.guild.id))
                    b = saas.get("branding", {})
                    if b.get("footer_enabled") and b.get("footer_text"):
                        mute_msg = f"{mute_msg}\n{b['footer_text']}"
                await message.channel.send(mute_msg)
            except discord.Forbidden:
                # Fallback adicional: silenciar en el canal actual vía permisos
                try:
                    await message.channel.set_permissions(member, send_messages=False, add_reactions=False, reason=f"Mute fallback: {reason}")
                    if message.guild:
                        saas = get_saas_config(str(message.guild.id))
                        b = saas.get("branding", {})
                        if b.get("footer_enabled") and b.get("footer_text"):
                            mute_msg = f"{mute_msg}\n{b['footer_text']}"
                    await message.channel.send(mute_msg + f" (fallback)")

                    async def _revert_channel_mute(ch: discord.abc.GuildChannel, m: discord.Member, seconds: int):
                        try:
                            await asyncio.sleep(seconds)
                            # Quitar overwrite para el miembro (revierte al estado por roles)
                            await ch.set_permissions(m, overwrite=None, reason="Auto unmute fallback")
                        except Exception:
                            logger.warning("No se pudo revertir el mute por canal (fallback)")

                    # Programar auto-unmute del overwrite
                    try:
                        # type: ignore[arg-type] - channel compatible
                        asyncio.create_task(_revert_channel_mute(message.channel, member, dur))
                    except Exception:
                        pass
                except discord.Forbidden:
                    logger.warning("Faltan permisos para aplicar mute (timeout o channel overwrite). Concede 'Moderate Members' o 'Manage Channels'.")
                except Exception as e:
                    logger.exception(f"Error en fallback de mute por canal: {e}")
        elif act == "kick" and member:
            try:
                # Verificar jerarquía de roles antes de ejecutar
                me: discord.Member | None = message.guild.me if message.guild else None  # type: ignore[assignment]
                if me and me.top_role and member.top_role and me.top_role.position <= member.top_role.position:
                    await message.channel.send("[MOD] No puedo expulsar: mi rol está al mismo nivel o por debajo del usuario objetivo.")
                    return
                await member.kick(reason=reason)
                await message.channel.send(action.get("text") or "Usuario expulsado.")
                # Confirmación post-acción: intentar recuperar miembro
                try:
                    await asyncio.sleep(1)
                    found = await message.guild.fetch_member(member.id)  # type: ignore[union-attr]
                    if found:
                        await message.channel.send("[MOD] Atención: el usuario sigue en el servidor tras kick. Revisa permisos/jerarquía y que no tenga protección.")
                except discord.NotFound:
                    # OK: ya no es miembro
                    pass
            except discord.Forbidden:
                logger.warning("Faltan permisos para expulsar (KICK_MEMBERS) o el rol del bot está por debajo del usuario.")
                await message.channel.send("[MOD] No pude expulsar: faltan permisos o el rol del bot está por debajo del usuario.")
            except discord.HTTPException as e:
                logger.warning(f"HTTPException al expulsar: {e}")
                await message.channel.send(f"[MOD] Error HTTP al expulsar: {getattr(e, 'status', '')}")
        elif act == "ban" and member:
            try:
                # Verificar jerarquía de roles antes de ejecutar
                me: discord.Member | None = message.guild.me if message.guild else None  # type: ignore[assignment]
                if me and me.top_role and member.top_role and me.top_role.position <= member.top_role.position:
                    await message.channel.send("[MOD] No puedo banear: mi rol está al mismo nivel o por debajo del usuario objetivo.")
                    return
                await message.guild.ban(member, reason=reason, delete_message_seconds=0)  # type: ignore[union-attr]
                await message.channel.send(action.get("text") or "Usuario baneado.")
                # Soporte opcional: desban automático si se especificó 'until_seconds' en la acción
                until_seconds = int(action.get("until_seconds", 0))
                if until_seconds and until_seconds > 0:
                    async def _unban_later(guild: discord.Guild, user_id: int, seconds: int):
                        try:
                            await asyncio.sleep(seconds)
                            # discord.py acepta discord.Object como user
                            await guild.unban(discord.Object(id=user_id))
                        except Exception:
                            logger.debug("Fallo al desbanear automáticamente (ban temporal)")
                    try:
                        asyncio.create_task(_unban_later(message.guild, member.id, until_seconds))  # type: ignore[arg-type]
                    except Exception:
                        pass
                # Confirmación post-acción: verificar que está en lista de baneados
                try:
                    await asyncio.sleep(1)
                    ban_entry = await message.guild.fetch_ban(member)  # type: ignore[union-attr]
                    if not ban_entry:
                        await message.channel.send("[MOD] Atención: no se encontró el ban tras la acción. Revisa permisos/jerarquía y configuración del servidor.")
                except discord.NotFound:
                    await message.channel.send("[MOD] Atención: el usuario no aparece en la lista de baneados. Puede que el ban no se haya aplicado.")
            except discord.Forbidden:
                logger.warning("Faltan permisos para banear (BAN_MEMBERS) o el rol del bot está por debajo del usuario.")
                await message.channel.send("[MOD] No pude banear: faltan permisos o el rol del bot está por debajo del usuario.")
            except discord.HTTPException as e:
                logger.warning(f"HTTPException al banear: {e}")
                await message.channel.send(f"[MOD] Error HTTP al banear: {getattr(e, 'status', '')}")
        else:
            logger.info(f"Acción de moderación no soportada o sin permisos: {act}")
    except discord.Forbidden:
        logger.warning("Permisos insuficientes para aplicar acción de moderación en Discord.")
    except Exception as e:
        logger.exception(f"Error aplicando acción de moderación: {e}")
    else:
        # Notificación a canal de admins si está habilitado
        try:
            if message.guild:
                cfg = get_moderation_config(str(message.guild.id))
                if cfg.get("admin_notify", False):
                    dest_id = cfg.get("admin_notify_channel_id")
                    dest_channel = message.guild.get_channel(int(dest_id)) if dest_id else message.channel
                    summary = f"[MOD] acción={act} usuario={getattr(message.author, 'display_name', message.author.id)} motivo={action.get('text','')}"
                    await dest_channel.send(summary)
        except Exception as e:
            logger.debug(f"No se pudo enviar admin_notify en Discord: {e}")


class DiscordBotClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.manager = BotManager()

    async def on_ready(self):
        logger.info(f"Conectado como {self.user} (ID: {self.user.id})")
        # Mostrar los servidores (guilds) y sus IDs para configurar reglas específicas en rules.yaml
        try:
            if hasattr(self, 'guilds'):
                for g in self.guilds:
                    logger.info(f"[discord] En servidor: {g.name} (guild_id={g.id})")
            else:
                logger.info("[discord] No se pudo listar guilds (atributo no disponible)")
        except Exception as e:
            logger.warning(f"No se pudieron listar guilds: {e}")

    async def on_message(self, message: discord.Message):
        # Ignorar mensajes del propio bot
        if message.author.bot:
            return

        # Comando de diagnóstico rápido de permisos e intents
        content = message.content or ""
        if content.strip().lower() in ("/diag_perms", "!diag_perms"):
            try:
                if not message.guild:
                    await message.channel.send("Este diagnóstico debe ejecutarse en un servidor.")
                    return
                me: discord.Member = message.guild.me  # type: ignore[assignment]
                guild_perms: discord.Permissions = me.guild_permissions
                chan_perms: discord.Permissions = message.channel.permissions_for(me)  # type: ignore[arg-type]
                # Posición de roles (para poder moderar usuarios, el rol del bot debe estar por encima)
                my_role_pos = me.top_role.position if me.top_role else -1
                author_role_pos = message.author.top_role.position if isinstance(message.author, discord.Member) and message.author.top_role else -1
                can_act_on_author = my_role_pos > author_role_pos
                # Intents activos
                intents_info = self.intents
                diag = (
                    "Diagnóstico permisos/intents del bot:\n"
                    f"- Intents: message_content={intents_info.message_content}, members={intents_info.members}\n"
                    f"- Guild perms: kick={guild_perms.kick_members}, ban={guild_perms.ban_members}, moderate={getattr(guild_perms, 'moderate_members', False)}, manage_channels={guild_perms.manage_channels}, manage_messages={guild_perms.manage_messages}, administrator={guild_perms.administrator}\n"
                    f"- Canal perms: send_messages={chan_perms.send_messages}, manage_messages={chan_perms.manage_messages}, view_channel={chan_perms.view_channel}, read_history={chan_perms.read_message_history}\n"
                    f"- Rol bot: pos={my_role_pos} | Rol autor: pos={author_role_pos} | bot>autor? {can_act_on_author}\n"
                    "Nota: Para kick/ban/timeout el bot necesita permisos y que su rol esté por encima del usuario."
                )
                await message.channel.send(diag)
            except Exception as e:
                logger.exception("Error en diagnóstico de permisos")
                await message.channel.send(f"No se pudo ejecutar diagnóstico: {e}")
            return

        # Moderación para administradores (manual): comandos en Discord
        # Requiere que el autor sea admin (permisos o ADMIN_IDS)
        cmd = (content.split() or [""])[0].lower()
        if cmd in ("/warn", "!warn", "/mute", "!mute", "/unmute", "!unmute", "/kick", "!kick", "/ban", "!ban", "/unban", "!unban", "/purge", "!purge"):
            if not isinstance(message.author, discord.Member) or not _is_admin(message.author):
                await message.channel.send("Solo administradores pueden usar comandos de moderación.")
                return
            # Resolver objetivo
            target, target_id = await _resolve_target_member(message)
            # /purge no requiere target, pero los demás sí
            if cmd in ("/purge", "!purge"):
                # Eliminar últimos N mensajes en el canal (excluye el comando)
                try:
                    n = 10
                    parts = content.split()
                    if len(parts) > 1 and parts[1].isdigit():
                        n = max(1, min(200, int(parts[1])))
                    # Intentar borrar el propio comando primero para que no cuente en el purge
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    deleted = await message.channel.purge(limit=n)
                    await message.channel.send(f"[MOD] Se eliminaron {len(deleted)} mensajes.")
                    try:
                        audit_repo.add_action(bot_id="discord", group_id=_get_group_id(message), user_id=str(message.author.id), action="purge", reason=f"n={n}")
                    except Exception:
                        pass
                except discord.Forbidden:
                    await message.channel.send("[MOD] No tengo permisos para borrar mensajes (Manage Messages).")
                except Exception as e:
                    await message.channel.send(f"[MOD] Error al purgar: {e}")
                return
            if not target_id or not target:
                await message.channel.send("Responde al mensaje del usuario o menciónalo para aplicar la acción.")
                return
            # Ejecutar acción
            try:
                if cmd in ("/warn", "!warn"):
                    await message.channel.send(f"Advertencia para @{target.display_name}. Por favor, respeta las reglas.")
                    audit_repo.add_action(bot_id="discord", group_id=_get_group_id(message), user_id=str(target.id), action="warn", reason="manual")
                elif cmd in ("/mute", "!mute"):
                    minutes = 10
                    parts = content.split()
                    try:
                        if len(parts) > 1:
                            minutes = max(1, int(parts[1]))
                    except Exception:
                        minutes = 10
                    dur = minutes * 60
                    until = datetime.now(timezone.utc) + timedelta(seconds=dur)
                    if hasattr(target, "timeout") and callable(getattr(target, "timeout")):
                        await target.timeout(until, reason="manual mute")  # type: ignore[attr-defined]
                    else:
                        await target.edit(communication_disabled_until=until, reason="manual mute")
                    await message.channel.send(f"Usuario @{target.display_name} muteado por {minutes} min.")
                    audit_repo.add_action(bot_id="discord", group_id=_get_group_id(message), user_id=str(target.id), action="mute", reason=f"{minutes}m")
                elif cmd in ("/unmute", "!unmute"):
                    if hasattr(target, "timeout") and callable(getattr(target, "timeout")):
                        await target.timeout(None, reason="manual unmute")  # type: ignore[attr-defined]
                    else:
                        await target.edit(communication_disabled_until=None, reason="manual unmute")
                    await message.channel.send(f"Usuario @{target.display_name} desmuteado.")
                    audit_repo.add_action(bot_id="discord", group_id=_get_group_id(message), user_id=str(target.id), action="unmute", reason="manual")
                elif cmd in ("/kick", "!kick"):
                    me: discord.Member | None = message.guild.me if message.guild else None  # type: ignore[assignment]
                    if me and me.top_role and target.top_role and me.top_role.position <= target.top_role.position:
                        await message.channel.send("[MOD] No puedo expulsar: mi rol está al mismo nivel o por debajo del usuario objetivo.")
                        return
                    await target.kick(reason="manual kick")
                    await message.channel.send("Usuario expulsado.")
                    audit_repo.add_action(bot_id="discord", group_id=_get_group_id(message), user_id=str(target.id), action="kick", reason="manual")
                elif cmd in ("/ban", "!ban"):
                    me: discord.Member | None = message.guild.me if message.guild else None  # type: ignore[assignment]
                    if me and me.top_role and target.top_role and me.top_role.position <= target.top_role.position:
                        await message.channel.send("[MOD] No puedo banear: mi rol está al mismo nivel o por debajo del usuario objetivo.")
                        return
                    await message.guild.ban(target, reason="manual ban")  # type: ignore[union-attr]
                    await message.channel.send("Usuario baneado.")
                    audit_repo.add_action(bot_id="discord", group_id=_get_group_id(message), user_id=str(target.id), action="ban", reason="manual")
                elif cmd in ("/unban", "!unban"):
                    try:
                        await message.guild.unban(discord.Object(id=target.id))  # type: ignore[arg-type]
                        await message.channel.send("Usuario desbaneado.")
                        audit_repo.add_action(bot_id="discord", group_id=_get_group_id(message), user_id=str(target.id), action="unban", reason="manual")
                    except discord.NotFound:
                        await message.channel.send("[MOD] El usuario no está en la lista de baneados.")
                return
            except discord.Forbidden:
                await message.channel.send("[MOD] No tengo permisos suficientes para esa acción.")
                return
            except Exception as e:
                await message.channel.send(f"[MOD] Error: {e}")
                return

        # Comando para mostrar reglas en Discord (simple): /reglas, !reglas o 'reglas'
        if content.strip().lower() in ("/reglas", "!reglas", "reglas"):
            try:
                from src.config.rules_loader import get_chat_rules
                gid = _get_group_id(message)
                feats = get_features_config(gid)
                if not feats.get("rules_command_enabled", True):
                    return
                reglas = get_chat_rules(gid) or {}
                reglas = reglas or get_chat_rules(None) or {}
                title = reglas.get("title", "Reglas")
                items = reglas.get("items", [])
                if not items:
                    await message.channel.send("No hay reglas definidas para este servidor.")
                else:
                    texto = title + "\n" + "\n".join([f"- {i}" for i in items])
                    await message.channel.send(texto)
            except Exception as e:
                logger.exception("Error mostrando reglas")
                await message.channel.send(f"No se pudieron obtener las reglas: {e}")
            return

        text = message.content or ""
        payload = {
            "platform": "discord",
            "platform_user_id": str(message.author.id),
            "group_id": _get_group_id(message),
            "text": text,
            "attachments": [att.url for att in getattr(message, "attachments", [])] or None,
            "raw_payload": None,
            "is_group": bool(message.guild),
        }

        resp = self.manager.process_message(payload)

        # Noop: no responder
        if not resp:
            return
        rtype = resp.get("type")
        if rtype == "noop":
            return
        if rtype == "reply":
            # Respetar enforce_only en servidores: no enviar replies conversacionales
            try:
                if message.guild:
                    cfg = get_moderation_config(str(message.guild.id))
                    if bool(cfg.get("enforce_only", False)):
                        logger.info("[discord] Respuesta suprimida por enforce_only en guild")
                        return
            except Exception:
                pass
            txt = resp.get("text")
            if txt:
                await message.channel.send(txt)
            return
        if rtype == "moderation":
            await apply_moderation_action(message, resp)

    async def on_member_join(self, member: discord.Member):
        try:
            if not member.guild:
                return
            guild_id = str(member.guild.id)
            wcfg = get_welcome_config(guild_id)
            # Respetar switch de features para bienvenida
            try:
                feats = get_features_config(guild_id)
                if not feats.get("welcome_enabled", True):
                    return
            except Exception:
                pass
            if not wcfg.get("enabled", True):
                return
            # Resolver canal destino
            channel = None
            ch_id = wcfg.get("channel_id")
            if ch_id:
                channel = member.guild.get_channel(int(ch_id))
            if channel is None:
                # Usar canal del sistema si existe, sino primer canal de texto accesible
                channel = member.guild.system_channel
                if channel is None:
                    for ch in member.guild.text_channels:
                        if ch.permissions_for(member.guild.me).send_messages:
                            channel = ch
                            break
            if not channel:
                return
            # Armar mensaje de bienvenida
            msg = str(wcfg.get("message", "¡Bienvenido/a {user}!"))
            msg = msg.replace("{user}", f"@{member.display_name}")
            msg = msg.replace("{group}", member.guild.name)
            if wcfg.get("show_rules", False):
                title = wcfg.get("title", "Reglas")
                msg = f"{msg}\n{title}"
            await channel.send(msg)
        except Exception as e:
            logger.warning(f"No se pudo enviar bienvenida en Discord: {e}")


def main():
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Falta DISCORD_TOKEN en el entorno.")

    # Intents solicitados por defecto (requieren habilitación en el portal)
    intents = discord.Intents.default()
    intents.message_content = True  # Privileged: requiere activarlo en Developer Portal
    intents.members = True          # Privileged: para mute/kick/ban

    client = DiscordBotClient(intents=intents)
    try:
        client.run(token)
    except discord.errors.PrivilegedIntentsRequired:
        logger.error(
            "Privileged intents requeridos no están habilitados en el Developer Portal. "
            "Habilita: MESSAGE CONTENT y SERVER MEMBERS en https://discord.com/developers/applications > tu app > Bot > Privileged Gateway Intents. "
            "Intentando reconectar con intents limitados (sin message_content ni members)."
        )
        # Reintentar con intents limitados para mantener el bot en línea (funcionalidad reducida)
        fallback_intents = discord.Intents.default()
        # message_content se queda False; aún verás contenido en DMs y algunos contextos permitidos
        fallback_client = DiscordBotClient(intents=fallback_intents)
        fallback_client.run(token)


if __name__ == "__main__":
    main()
