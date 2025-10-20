import unicodedata
# --- Normalización robusta para matching de intents ---
def normalizar_texto(texto: str) -> str:
	texto = (texto or "").strip().lower()
	texto = " ".join(texto.split())
	texto = unicodedata.normalize('NFD', texto)
	texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
	return texto
"""
BotManager: orquesta NLU, moderación, rate limiting y dispatch a handlers.
Contrato de entrada (payload normalizado):
{
  "platform": "telegram|whatsapp|web",
  "platform_user_id": str|int,
  "group_id": str|int,
  "text": str,
  "attachments": list | None,
  "raw_payload": dict | None
}
"""

from typing import Optional, Dict, Any

from src.nlu.intent_detector import detectar_intencion
from src.nlu.entity_extractor import extraer_entidades
from src.utils.rate_limiter import RateLimiter
from src.utils.security import sanitizar_texto
from src.utils.validators import validar_mensaje
from src.handlers.bienvenida import enviar_bienvenida
from src.handlers.encuesta import crear_encuesta
from src.handlers.sorteo import realizar_sorteo
from src.handlers.moderacion import revisar_mensaje
from src.handlers.greeting import handle_greeting
from src.utils.logging import log_event
from src.config.rules_loader import get_moderation_config, get_features_config


class BotManager:
	def __init__(self, rate_limit_max: int = 5, rate_limit_interval: int = 10):
		self.rate_limiter = RateLimiter(rate_limit_max, rate_limit_interval)
	def process_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
		# 1) Sanitizar y validar
		texto_original = payload.get("text", "")
		texto = sanitizar_texto(texto_original)
		usuario = str(payload.get("platform_user_id", ""))
		grupo = str(payload.get("group_id", ""))

		if not validar_mensaje(texto):
			return {"text": "Mensaje vacío o inválido.", "type": "reply"}

		# Normalizar para NLU y moderación
		texto_norm = normalizar_texto(texto)

		# 2) Rate limiting por usuario
		if not self.rate_limiter.allow(usuario):
			return {"text": "Estás enviando mensajes muy rápido. Intenta más tarde.", "type": "reply"}

		# 3) Moderación temprana (por chat)
		moderacion = revisar_mensaje(texto_norm, usuario, grupo)
		if moderacion:
			return moderacion

		# 4) NLU: intención y entidades
		# Usar texto sanitizado (no normalizado) para NLU por compatibilidad con palabras clave
		intent = detectar_intencion(texto)
		# Extraer entidades del texto sin normalizar para preservar
		# mayúsculas, tildes y formato original (preguntas, opciones).
		entities = extraer_entidades(texto)
		log_event("nlu_result", intent=intent, entities=entities)

		# 5) Dispatch por intención
		# Modo enforce_only: en grupos, solo moderación (no conversar)
		cfg = get_moderation_config(grupo)
		features = get_features_config(grupo)
		enforce_only = bool(cfg.get("enforce_only", False))
		# Determinar si el contexto es de grupo. Usar solo bandera explícita del payload.
		# Si no viene, asumir False para mantener compatibilidad con Webchat y otros canales.
		is_group = bool(payload.get("is_group", False))
		if intent == "greeting" and not (enforce_only and is_group) and features.get("greeting_enabled", True):
			nombre = entities.get("name") or usuario
			return {
				"text": handle_greeting(nombre),
				"type": "reply",
				"quick_replies": ["Ver reglas", "Participar en sorteo", "Crear encuesta"]
			}
		if intent == "welcome" and not (enforce_only and is_group) and features.get("welcome_enabled", True):
			return enviar_bienvenida(usuario, grupo)
		if intent == "survey" and not (enforce_only and is_group) and features.get("survey_enabled", True):
			pregunta = entities.get("question") or "¿Cuál prefieres?"
			opciones = entities.get("options") or ["Opción A", "Opción B"]
			return crear_encuesta(pregunta, opciones)
		if intent == "raffle" and not (enforce_only and is_group) and features.get("raffle_enabled", True):
			participantes = entities.get("participants") or [usuario]
			return realizar_sorteo(participantes)
		# 6) Fallback
		if enforce_only and is_group:
			# En grupos modo enforcement, no responder al fallback
			return {"type": "noop"}
		# Responder fallback solo si está habilitado
		if features.get("fallback_enabled", True):
			return {"text": "No entendí tu mensaje. Usa 'ayuda' para opciones.", "type": "reply"}
		return {"type": "noop"}
