# models.py - Modelos para Bot Comunidad
from datetime import datetime

class User:
    def __init__(self, user_id, name, metadata=None):
        self.user_id = user_id
        self.name = name
        self.metadata = metadata or {}

class Group:
    def __init__(self, group_id, name, rules=None):
        self.group_id = group_id
        self.name = name
        self.rules = rules or []

class Message:
    def __init__(self, message_id, user_id, group_id, text, timestamp=None):
        self.message_id = message_id
        self.user_id = user_id
        self.group_id = group_id
        self.text = text
        self.timestamp = timestamp or datetime.utcnow()

class Survey:
    def __init__(self, survey_id, group_id, question, options, votes=None):
        self.survey_id = survey_id
        self.group_id = group_id
        self.question = question
        self.options = options
        self.votes = votes or {}

class Raffle:
    def __init__(self, raffle_id, group_id, participants, winner=None):
        self.raffle_id = raffle_id
        self.group_id = group_id
        self.participants = participants
        self.winner = winner
