# repository.py - Acceso y persistencia de datos para Bot Comunidad

# Mockup: en producción usarías una DB real (SQLAlchemy, Mongo, etc)

class UserRepository:
    def __init__(self):
        self.users = {}
    def add_user(self, user):
        self.users[user.user_id] = user
    def get_user(self, user_id):
        return self.users.get(user_id)

class GroupRepository:
    def __init__(self):
        self.groups = {}
    def add_group(self, group):
        self.groups[group.group_id] = group
    def get_group(self, group_id):
        return self.groups.get(group_id)

class MessageRepository:
    def __init__(self):
        self.messages = []
    def add_message(self, message):
        self.messages.append(message)
    def get_messages_by_group(self, group_id):
        return [m for m in self.messages if m.group_id == group_id]

class SurveyRepository:
    def __init__(self):
        self.surveys = {}
    def add_survey(self, survey):
        self.surveys[survey.survey_id] = survey
    def get_survey(self, survey_id):
        return self.surveys.get(survey_id)

class RaffleRepository:
    def __init__(self):
        self.raffles = {}
    def add_raffle(self, raffle):
        self.raffles[raffle.raffle_id] = raffle
    def get_raffle(self, raffle_id):
        return self.raffles.get(raffle_id)


class ModerationRepository:
    """Repositorio simple en memoria para infracciones por (chat_id, user_id).
    Estructura: {(chat_id, user_id): {"count": int, "muted_until": timestamp|None, "banned": bool}}
    Nota: Para producción, reemplazar por DB/Redis con expiración.
    """
    def __init__(self):
        from time import time
        self.records = {}
        self._time = time
        # Ventana para antiflood: { (chat,user): [(ts1), (ts2), ...] }
        self._msg_times = {}

    def get_record(self, chat_id: str, user_id: str):
        return self.records.get((str(chat_id), str(user_id)), {"count": 0, "muted_until": None, "banned": False})

    def add_violation(self, chat_id: str, user_id: str) -> int:
        key = (str(chat_id), str(user_id))
        rec = self.records.get(key) or {"count": 0, "muted_until": None, "banned": False}
        rec["count"] = rec.get("count", 0) + 1
        self.records[key] = rec
        return rec["count"]

    def set_muted(self, chat_id: str, user_id: str, seconds: int):
        key = (str(chat_id), str(user_id))
        rec = self.records.get(key) or {"count": 0, "muted_until": None, "banned": False}
        rec["muted_until"] = self._time() + int(seconds)
        self.records[key] = rec

    def is_muted(self, chat_id: str, user_id: str) -> bool:
        key = (str(chat_id), str(user_id))
        rec = self.records.get(key)
        if not rec or rec.get("muted_until") is None:
            return False
        return rec["muted_until"] > self._time()

    def set_banned(self, chat_id: str, user_id: str, banned: bool = True):
        key = (str(chat_id), str(user_id))
        rec = self.records.get(key) or {"count": 0, "muted_until": None, "banned": False}
        rec["banned"] = banned
        self.records[key] = rec

    def reset(self, chat_id: str, user_id: str):
        self.records.pop((str(chat_id), str(user_id)), None)

    # --- Antiflood: registrar mensaje y validar límite por minuto ---
    def register_message(self, chat_id: str, user_id: str, window_seconds: int = 60) -> int:
        key = (str(chat_id), str(user_id))
        now = self._time()
        times = self._msg_times.get(key, [])
        times = [t for t in times if now - t <= window_seconds]
        times.append(now)
        self._msg_times[key] = times
        return len(times)


class AuditRepository:
    """Repositorio simple en memoria para auditoría de acciones de moderación.
    Estructura de registro:
    {"ts": epoch, "bot_id": str, "group_id": str, "user_id": str, "action": str, "reason": str, "by": str|None}
    """
    def __init__(self):
        from time import time
        self._time = time
        self.records = []

    def add_action(self, bot_id: str, group_id: str, user_id: str, action: str, reason: str = "", by: str | None = None):
        self.records.append({
            "ts": self._time(),
            "bot_id": str(bot_id),
            "group_id": str(group_id),
            "user_id": str(user_id),
            "action": action,
            "reason": reason,
            "by": by,
        })


# Instancias singleton simples para uso global
audit_repo = AuditRepository()
