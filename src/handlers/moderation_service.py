"""Servicios de moderación reutilizables.
No sustituye la lógica existente en conectores; sirve para centralizar chequeos y utilidades.
"""
from __future__ import annotations
import os
from typing import Iterable, Set

# Coincidir con la semántica usada en conectores: IDs separados por coma o punto y coma

def parse_admin_ids(raw: str | None) -> Set[int]:
    ids: Set[int] = set()
    if not raw:
        return ids
    for part in raw.replace(";", ",").split(","):
        p = part.strip()
        if not p:
            continue
        try:
            ids.add(int(p))
        except Exception:
            # ignorar entradas inválidas
            pass
    return ids

ADMIN_WHITELIST: Set[int] = parse_admin_ids(os.getenv("ADMIN_IDS"))


def is_admin_telegram(get_chat_member, chat_id: int, user_id: int) -> bool:
    """Determina si un usuario es admin por rol o por whitelist.
    - get_chat_member: callable async que devuelve miembro (inyectado desde context.bot.get_chat_member)
    """
    # Whitelist primero para tolerancia a fallos de API/permiso
    if user_id in ADMIN_WHITELIST:
        return True
    # Intentar rol de chat (sin await aquí; el conector decide await)
    try:
        member = get_chat_member(chat_id, user_id)  # type: ignore[misc]
        status = getattr(member, "status", None)
        if isinstance(status, str):
            return status in ("administrator", "creator", "owner")
    except Exception:
        pass
    return False


def is_admin_discord(member) -> bool:
    try:
        if not member:
            return False
        if getattr(member, "id", None) in ADMIN_WHITELIST:
            return True
        perms = getattr(member, "guild_permissions", None)
        if not perms:
            return False
        return bool(perms.administrator or perms.kick_members or perms.ban_members or getattr(perms, "moderate_members", False))
    except Exception:
        return False
