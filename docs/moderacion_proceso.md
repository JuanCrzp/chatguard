# Proceso de diseño y profesionalización de moderación para bots

## 1. Análisis y requisitos
- Moderación multi-grupo y multi-bot.
- Acciones: advertencia, mute, expulsión, ban, borrado de mensajes.
- Configuración granular por grupo/bot.
- Auditoría y trazabilidad de acciones.
- Whitelist y excepciones.

## 2. Diseño de base de datos
- Tablas creadas:
  - `palabras_prohibidas`: gestión de palabras prohibidas por grupo/bot.
  - `usuarios_sancionados`: registro de sanciones (mute, ban, expulsión) con admin responsable.
  - `configuracion_moderacion`: parámetros por grupo/bot (advertencias, mute, flood, etc).
  - `auditoria_moderacion`: log de acciones de moderación (quién, cuándo, motivo).
  - `whitelist_moderacion`: usuarios exentos de moderación.
- Ejemplos de inserción en `moderacion_inserts.sql`.

## 3. Configuración y lógica en el bot
- `rules.yaml`: define thresholds, palabras prohibidas, límites de flood y mute por grupo.
- `moderation.enforce_only`: cuando es `true`, en grupos el bot solo ejecuta moderación y no responde mensajes conversacionales (devuelve `type: noop`).
- Handler de moderación avanzado: evalúa reglas, registra infracciones, decide y ejecuta acciones.
- Opciones implementadas: `flood_limit`, `max_message_length`, `caps_lock_threshold`, `allow_links`, `link_whitelist`, `invite_links_allowed`, `regex_patterns`, `whitelist_users`, `ban_duration_seconds`, `warn_message`, `kick_message`, `ban_message`, `mute_types`.
- Persistencia de infracciones en memoria (extensible a DB/Redis).
- Comandos de admin en Telegram: /warn, /mute, /unmute, /kick, /ban, /unban, /settings.
- Acciones aplicadas en Telegram: borrar, mutear, expulsar, banear.
- Auditoría y notificaciones: se registra cada acción (in-memory) y, si `admin_notify=true`, se notifica al chat.

## 4. Auditoría y pruebas
- Registro de eventos de moderación con motivo, regla aplicada y acción ejecutada.
- Tests unitarios para advertencias, mute, ban y listas prohibidas.

## 5. Estado actual
- Esquema SQL profesional listo para producción.
- Ejemplos de inserción y migración.
- Código del bot preparado para escalar y auditar.

## 6. Siguientes pasos sugeridos
- Persistencia real en DB/Redis para infracciones y sanciones.
- Panel de administración y visualización de auditoría.
- Extender reglas para patrones regex, archivos, enlaces y roles.
- Integrar notificaciones y reportes automáticos.

---

Este documento resume el proceso seguido para profesionalizar la moderación en bots de comunidad, asegurando escalabilidad, trazabilidad y flexibilidad.