"""Detección simple de intenciones basada en palabras clave.
Intents soportados: greeting, welcome, survey, raffle
"""

def detectar_intencion(texto: str) -> str:
	t = texto.lower().strip()
	if any(w in t for w in ["hola", "buenas", "saludos", "hello"]):
		return "greeting"
	if any(w in t for w in ["bienvenido", "bienvenida", "welcome"]):
		return "welcome"
	if any(w in t for w in ["encuesta", "votar", "poll", "survey"]):
		return "survey"
	if any(w in t for w in ["sorteo", "rifa", "raffle"]):
		return "raffle"
	return "unknown"
