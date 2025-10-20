"""Policy: Evaluación de políticas y reglas por grupo.
Por ahora, ejemplo sencillo para permitir comandos de admin y futuros checks.
"""

from typing import Dict, Any


class Policy:
	def __init__(self, rules: Dict[str, Any] | None = None):
		self.rules = rules or {}

	def is_admin_command_allowed(self, user_id: str) -> bool:
		# Placeholder: en producción validarías contra permisos del grupo/DB
		return True

	def can_run_raffle(self, group_id: str) -> bool:
		return True
