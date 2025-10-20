# Conector Discord para Bot Comunidad

Este módulo permite conectar el bot a servidores de Discord y aplicar lógica de moderación profesional, integrando el mismo flujo que Telegram/Webchat/WhatsApp.

## Estructura y lógica
- Archivo: `src/connectors/discord_connector.py`
- Usa la librería `discord.py` (>=2.3.0) para interactuar con la API Gateway de Discord.
- Lee configuración y token desde `.env` usando `python-dotenv`.
- Activa intents necesarios para moderación y lectura de mensajes (`message_content`, `members`).
- Integra con el `BotManager` para normalizar mensajes y despachar a los handlers existentes.
- Aplica acciones de moderación:
  - Elimina mensajes (`delete`)
  - Advierte al usuario (`warn`)
  - Silencia (mute/timeout) por duración configurada
  - Expulsa (`kick`) o banea (`ban`) usuarios
  - Maneja errores y permisos insuficientes
- Respeta el modo `enforce_only` (solo actúa en moderación, no responde en grupos si está activado).
- Ignora mensajes del propio bot y maneja tanto DMs como canales de servidor.
- El arranque está integrado en `run.py` con `START_MODE=discord`.

## Archivos modificados/creados
- `src/connectors/discord_connector.py`: conector Discord completo
- `requirements.txt`: se añadió `discord.py`
- `.env.example`: se añadieron `DISCORD_TOKEN` y `DISCORD_GUILD_ID`
- `run.py`: nuevo modo de arranque para Discord

## Cómo usar
1. Crea una app y bot en el portal de Discord Developers.
2. Activa intents: `MESSAGE CONTENT INTENT` y `GUILD MEMBERS INTENT`.
3. Copia el token en tu `.env` como `DISCORD_TOKEN=...`
4. Instala dependencias: `pip install -r requirements.txt`
5. Arranca el bot:
   - En PowerShell:
     ```powershell
     cd "backend\bots\Comunidad"
     $env:START_MODE = "discord"
     & "<ruta_python_venv>" run.py
     ```
6. El bot se conectará y aplicará la misma lógica de moderación que en Telegram, usando las reglas y handlers existentes.

## Notas
- Si falta el token, el conector muestra un error claro y no arranca.
- El código está listo para escalar, agregar comandos slash y paneles de administración.
- Puedes extenderlo para logs avanzados, integración con base de datos y más canales.

---
¿Dudas o quieres ejemplos de comandos slash, logs o integración con panel web? Avísame y lo agrego.