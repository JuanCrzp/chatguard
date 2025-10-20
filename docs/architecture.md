# Arquitectura del bot

## Modo cumplimiento (enforce_only)
En `config/rules.yaml` por chat/grupo se puede activar `moderation.enforce_only: true`.

- Cuando está activo y el mensaje proviene de un grupo, el `BotManager`:
	- Procesa moderación (revisar_mensaje) con normalización y reglas por chat.
	- Omite respuestas conversacionales (saludos, encuesta, sorteo).
	- Devuelve una respuesta `{"type": "noop"}` para no responder en el grupo.
- El conector de Telegram (`src/connectors/telegram_polling.py`) detecta `type: noop` y no envía ningún mensaje al chat.

Relación con Telegram Privacy Mode:
- `enforce_only` controla el comportamiento del bot; no afecta qué mensajes Telegram entrega.
- Para que el bot pueda moderar mensajes normales, se requiere Privacy Mode desactivado y permisos de admin.
