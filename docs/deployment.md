# Guía de despliegue

## Configurar modo cumplimiento (enforce_only)
En `config/rules.yaml` puedes activar por grupo:

```yaml
<chat_id>:
	moderation:
		enforce_only: true
```

Efecto:
- En grupos con `enforce_only: true`, el bot solo actúa ante violaciones (spam, insultos, etc.) y no conversa.
- En mensajes privados, el bot sigue respondiendo normalmente.

Relación con Telegram Privacy Mode:
- Con Privacy Mode ACTIVADO: el bot solo ve comandos, menciones y eventos.
- Con Privacy Mode DESACTIVADO: el bot ve todos los mensajes y puede moderar (recomendado para antispam).
- `enforce_only` no cambia lo que Telegram entrega; solo decide si el bot responde o no a mensajes no violatorios.

## Otras opciones de moderación útiles
En `config/rules.yaml` dentro de `moderation` puedes ajustar:

- flood_limit: límite de mensajes por minuto por usuario.
- max_message_length: longitud máxima permitida del mensaje.
- caps_lock_threshold: porcentaje de letras en MAYÚSCULAS para advertir “gritos”.
- allow_links / allow_files: permitir o bloquear enlaces/archivos; link_whitelist para dominios permitidos.
- regex_patterns: lista de expresiones regulares prohibidas.
- whitelist_users: usuarios exentos de moderación.
- mute_types: tipos de mute (text, media, all).
- ban_duration_seconds: duración del ban temporal (0 = permanente).
- admin_notify: notificar en el chat cuando se aplique una sanción.
- log_actions: registrar acciones (útil con auditoría a DB).

Requisito de permisos en Telegram:
- Para borrar, mutear, expulsar y banear, el bot debe ser “Administrador” con permisos de “Borrar mensajes” y “Restringir usuarios”.
