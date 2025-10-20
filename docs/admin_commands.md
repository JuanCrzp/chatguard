# Comandos de administración (Telegram)

Requisitos: el bot debe ser Administrador del grupo con permisos de borrar mensajes y restringir usuarios.

- /warn (responder a mensaje): registra una advertencia para el usuario objetivo.
- /mute [min] (responder): restringe enviar mensajes durante N minutos (por defecto 10).
- /unmute (responder): levanta la restricción de mensajes.
- /kick (responder): expulsión (ban corto + unban).
- /ban (responder): ban permanente.
- /unban (responder): levanta el ban.
- /reload: recarga las reglas desde `config/rules.yaml` sin reiniciar el bot (solo admins).

Notas:
- Para seleccionar el usuario objetivo, responde al mensaje del usuario con el comando.
- Los comandos respetan `whitelist_users` si está configurado.
- Si `admin_notify=true`, el bot anunciará la acción aplicada en el chat.
- Si `enabled=false` para el chat en `rules.yaml`, el bot no responderá ni moderará (excepto este comando al ser invocado por admin).

Tips:
- Tras editar `rules.yaml`, usa `/reload` para aplicar cambios en el bot principal.
- Los recordatorios (script `src/tasks/reminders.py`) se ejecutan como proceso separado; si cambias `rules.yaml`, reinicia ese script para que tome la nueva configuración.
