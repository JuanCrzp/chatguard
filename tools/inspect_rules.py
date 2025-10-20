import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.rules_loader import get_chat_rules, get_moderation_config, get_features_config, reload_rules_cache


def print_configs(chat_ids):
    reload_rules_cache()
    for cid in chat_ids:
        print("---")
        print(f"chat_id/guild_id: {cid}")
        rules = get_chat_rules(cid)
        print("get_chat_rules:")
        print(rules)
        print("get_moderation_config:")
        print(get_moderation_config(cid))
        print("get_features_config:")
        print(get_features_config(cid))


if __name__ == '__main__':
    # ejemplo de uso: modifica la lista con los IDs que quieras inspeccionar
    ids = ["-1003167371477", "2072596071", "-123456789", "987654321098765432"]
    print_configs(ids)
