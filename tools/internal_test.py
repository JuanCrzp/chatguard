import sys
from pathlib import Path

# Asegurar que la carpeta del proyecto esté en sys.path para poder importar `src`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.bot_core.manager import BotManager
from src.config.rules_loader import reload_rules_cache, get_moderation_config

bm = BotManager()

scenarios = [
    {
        "name": "Webchat greeting (should reply)",
        "payload": {
            "platform": "webchat",
            "platform_user_id": "u-web",
            "group_id": "g-web",
            "text": "Hola, soy Carla",
            "attachments": [],
            "raw_payload": {},
        },
    },
    {
        "name": "Telegram group greeting (enforce_only true) - should be suppressed",
        "payload": {
            "platform": "telegram",
            "platform_user_id": "2072596071",
            "group_id": -1003167371477,
            "is_group": True,
            "text": "Hola",
            "attachments": [],
            "raw_payload": {},
        },
    },
    {
        "name": "Telegram group violation (banned word) - should moderate",
        "payload": {
            "platform": "telegram",
            "platform_user_id": "baduser",
            "group_id": -123456789,  # override in rules.yaml with banned_words includes 'spoiler'
            "is_group": True,
            "text": "Este es un spoiler",
            "attachments": [],
            "raw_payload": {},
        },
    },
    {
        "name": "Discord guild greeting (enforce_only true) - should be suppressed",
        "payload": {
            "platform": "discord",
            "platform_user_id": "99999",
            "group_id": "987654321098765432",
            "is_group": True,
            "text": "Hola a todos",
            "attachments": [],
            "raw_payload": {},
        },
    },
]

if __name__ == "__main__":
    reload_rules_cache()
    for s in scenarios:
        print(f"=== {s['name']} ===")
        res = bm.process_message(s["payload"])  # type: ignore[arg-type]
        print(res)
        print()
