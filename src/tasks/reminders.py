"""Recordatorios programados simples para Telegram.
Usa variables de entorno para configurar el chat, el texto y la hora.
Pensado para usarse como script independiente (no requiere Application.run_polling()).
"""
from __future__ import annotations
import os
import time
from datetime import datetime, timedelta
import asyncio
from telegram import Bot
from pathlib import Path
import yaml
from typing import Dict, Any
from src.config.rules_loader import _load_rules


def _parse_hour(hour_str: str) -> tuple[int, int]:
    try:
        hh, mm = hour_str.split(":", 1)
        h, m = int(hh), int(mm)
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError
        return h, m
    except Exception:
        # 09:00 por defecto
        print(f"[reminders] Advertencia: hora inválida '{hour_str}', usando 09:00")
        return 9, 0


def _next_run_from(now: datetime, target_h: int, target_m: int) -> datetime:
    run = now.replace(hour=target_h, minute=target_m, second=0, microsecond=0)
    if run <= now:
        run = run + timedelta(days=1)
    return run



def _iter_reminder_configs() -> Dict[str, Dict[str, Any]]:
    """Devuelve un dict chat_id->config con reminder habilitado.
    Usa el rules_loader subyacente, que normaliza claves a str.
    """
    data = _load_rules()  # {str(chat_id): rules}
    result: Dict[str, Dict[str, Any]] = {}
    for key, rules in data.items():
        # Determinar chat_id destino: si es 'default' buscamos REMINDER_CHAT_ID en env
        reminder = (rules or {}).get("reminder") or {}
        if not isinstance(reminder, dict):
            continue
        if not reminder.get("enabled", False):
            continue
        # Para default, requerimos REMINDER_CHAT_ID en env (o se omite)
        if key == "default":
            env_chat = os.getenv("REMINDER_CHAT_ID")
            if env_chat:
                result[env_chat] = {
                    "text": reminder.get("text", "Recordatorio diario"),
                    "hour": reminder.get("hour", "09:00"),
                    "days": reminder.get("days", []),
                }
            else:
                print("[reminders] Advertencia: default.reminder.enabled=true pero falta REMINDER_CHAT_ID en .env; se omite")
        else:
            # key es el chat_id
            result[key] = {
                "text": reminder.get("text", "Recordatorio diario"),
                "hour": reminder.get("hour", "09:00"),
                "days": reminder.get("days", []),
            }
    return result


async def run_daily_reminder_async():
    """Bucle asíncrono que envía mensajes diarios según rules.yaml.

    Requisitos:
    - TELEGRAM_TOKEN en .env
    - rules.yaml con secciones reminder por chat (enabled/text/hour[, days])
    - Para 'default', define REMINDER_CHAT_ID en .env
    """
    # Cargar variables desde .env si la librería está disponible
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("Falta TELEGRAM_TOKEN en .env")
        return
    bot = Bot(token=token)
    configs = _iter_reminder_configs()
    if not configs:
        print("[reminders] No hay recordatorios habilitados en rules.yaml")
        return
    # Programar por cada chat_id configurado
    targets = []
    for chat_id, cfg in configs.items():
        h, m = _parse_hour(str(cfg.get("hour", "09:00")))
        raw_days = cfg.get("days") or []
        days = [str(d).strip().lower() for d in raw_days]
        valid_days = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
        invalid = [d for d in days if d not in valid_days]
        days = [d for d in days if d in valid_days]
        if invalid:
            print(f"[reminders] Advertencia: días inválidos {invalid} en chat {chat_id}; válidos: {sorted(valid_days)}")
        targets.append((chat_id, cfg.get("text", "Recordatorio diario"), h, m, days))

    while True:
        now = datetime.now()
        runs = []
        for item in targets:
            chat_id, text, h, m, days = item
            run_at = _next_run_from(now, h, m)
            if days:
                map_idx = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
                while map_idx[run_at.weekday()] not in days:
                    run_at = run_at + timedelta(days=1)
            runs.append((chat_id, text, run_at))
        next_chat, next_text, run_at = min(runs, key=lambda x: x[2])
        wait_s = max(1, int((run_at - now).total_seconds()))
        print(f"[reminders] Próximo envío {run_at} a chat {next_chat} (en {wait_s}s)")
        await asyncio.sleep(wait_s)
        try:
            resp = await bot.send_message(chat_id=next_chat, text=next_text)
            msg_id = getattr(resp, 'message_id', None)
            print(f"[reminders] Enviado a {next_chat} a las {run_at} (message_id={msg_id})")
        except Exception as e:
            import traceback
            print(f"[reminders] Error al enviar a {next_chat}: {e}")
            traceback.print_exc()


def run_daily_reminder():
    """Wrapper para ejecutar el bucle asíncrono con política compatible en Windows."""
    # En Windows, algunas libs funcionan mejor con SelectorEventLoop
    if os.name == "nt":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass
    asyncio.run(run_daily_reminder_async())


if __name__ == "__main__":
    run_daily_reminder()
