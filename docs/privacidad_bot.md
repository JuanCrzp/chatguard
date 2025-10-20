# Política de privacidad y funcionamiento del bot de moderación

## ¿Qué mensajes puede leer el bot?
- **Con privacy mode ACTIVADO (recomendado para comunidades):**
  - Solo recibe y responde a comandos (ej: /start, /help, /reglas).
  - Solo recibe mensajes donde lo mencionan (@TuBot).
  - Solo recibe eventos especiales (nuevos miembros, expulsiones, etc).
  - No puede leer ni responder mensajes normales entre usuarios.

- **Con privacy mode DESACTIVADO (solo para moderación activa):**
  - Recibe todos los mensajes del grupo, igual que cualquier usuario.
  - Puede analizar, moderar y responder cualquier texto (spam, insultos, etc).
  - Puede borrar, mutear, expulsar y banear si es administrador.

## Recomendaciones profesionales
- Mantén privacy mode activado si el bot no necesita moderar todo el grupo.
- Desactívalo solo si los miembros están informados y aceptan que el bot puede leer todo.
- Documenta claramente en las reglas del grupo y en el README del bot qué mensajes puede leer y cómo se usan.
- Si el bot modera todo, incluye un aviso visible en el grupo.

## Modo cumplimiento (enforce_only)
Si en `rules.yaml` activas `moderation.enforce_only: true` para un grupo, el bot solo actuará ante violaciones (borrado, mute, ban), y no contestará saludos ni charlas, aunque pueda leer los mensajes (con Privacy Mode desactivado).

## Ejemplo de aviso para el grupo
> Este grupo utiliza un bot de moderación. Si privacy mode está desactivado, el bot puede leer y moderar todos los mensajes para proteger la comunidad contra spam, insultos y contenido no permitido. Si tienes dudas, consulta la política de privacidad.

---

Esta política ayuda a mantener la transparencia y confianza en el uso de bots en comunidades y grupos de Telegram.