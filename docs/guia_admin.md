# Guía rápida para administradores de grupo

Esta guía explica cómo configurar reglas y recordatorios automáticos en tu bot de comunidad, sin tocar el código.

## 1. Obtener el chat_id del grupo

1. Ejecuta el bot normalmente (python src\connectors\telegram_polling.py).
2. Escribe cualquier mensaje en el grupo donde está el bot.
3. Mira la consola donde corre el bot: verás una línea como:
   
   [INFO] chat_id del grupo: -123456789

4. Copia ese número (incluyendo el signo negativo).

## 2. Configurar un recordatorio automático

### Opción A: Recordatorio solo para un grupo específico

1. Abre el archivo `config/rules.yaml`.
2. Agrega (o edita) la sección del grupo usando el chat_id copiado:

   ```yaml
   -123456789:
     reminder:
       enabled: true
       text: "¡No olvides participar en la encuesta!"
       hour: "18:00"
       days: [mon, wed, fri]
   ```

### Opción B: Recordatorio general (default)

1. En `rules.yaml`, configura la sección `default.reminder`:
   ```yaml
   default:
     reminder:
       enabled: true
       text: "Recordatorio semanal: lee las reglas."
       hour: "09:00"
       days: [mon]
   ```
2. En el archivo `.env`, pon el chat_id destino:
   ```
   REMINDER_CHAT_ID=-123456789
   ```

## 3. Aplicar los cambios

- Si cambiaste `rules.yaml`, reinicia el script de recordatorios:
  ```bat
  python src\tasks\reminders.py
  ```
- Si cambiaste reglas de moderación y el bot ya está corriendo, usa `/reload` en Telegram (como admin) para que el bot principal tome los cambios.

## 4. Notas y buenas prácticas

- No edites el código fuente, solo los archivos de configuración.
- Si tienes dudas sobre el chat_id, repite el paso 1.
- Si el recordatorio no se envía, revisa:
  - Que `enabled: true` en la sección reminder.
  - Que el chat_id sea correcto.
  - Que la hora esté en formato HH:MM (24h).
  - Que los días (days) sean válidos: mon, tue, wed, thu, fri, sat, sun.
- Para reglas avanzadas, consulta `docs/rules_reference.md`.

---

¿Dudas? Contacta al soporte técnico o al desarrollador del bot.
