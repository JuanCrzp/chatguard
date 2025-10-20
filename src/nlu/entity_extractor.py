"""Extracción simple de entidades por regex/reglas.
Soporta: name, question, options, participants
"""

import re
from typing import Dict, Any


def extraer_entidades(texto: str) -> Dict[str, Any]:
	entities: Dict[str, Any] = {}

	# name: "soy <nombre>" o "me llamo <nombre>"
	m = re.search(r"(?:soy|me llamo)\s+([A-Za-zÁÉÍÓÚÑáéíóúñ0-9_\-]+)", texto, re.IGNORECASE)
	if m:
		entities["name"] = m.group(1)

	# survey: pregunta entre comillas "..." y opciones separadas por coma
	q = re.search(r'"([^"]{3,})"', texto)
	if q:
		entities["question"] = q.group(1)
	opts = re.findall(r"\[(.*?)\]", texto)
	if opts:
		# primera lista [a,b,c]
		raw = opts[0]
		parts = [p.strip() for p in raw.split(',') if p.strip()]
		if len(parts) >= 2:
			entities["options"] = parts

	# raffle: participantes entre paréntesis (a,b,c)
	p = re.findall(r"\((.*?)\)", texto)
	if p:
		rawp = p[0]
		ppl = [x.strip() for x in rawp.split(',') if x.strip()]
		if ppl:
			entities["participants"] = ppl

	return entities
