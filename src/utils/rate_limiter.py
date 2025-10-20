# rate_limiter.py - Limitador de mensajes para Bot Comunidad
import time

class RateLimiter:
    def __init__(self, max_messages, interval):
        self.max_messages = max_messages
        self.interval = interval
        self.user_timestamps = {}
    def allow(self, user_id):
        now = time.time()
        timestamps = self.user_timestamps.get(user_id, [])
        timestamps = [t for t in timestamps if now - t < self.interval]
        if len(timestamps) < self.max_messages:
            timestamps.append(now)
            self.user_timestamps[user_id] = timestamps
            return True
        return False
