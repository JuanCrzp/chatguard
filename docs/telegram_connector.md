# Conector Telegram para Bot Comunidad

Este módulo conecta el bot a grupos y usuarios de Telegram usando el modo polling y la librería `python-telegram-bot` v20+.

## Estructura y lógica
- Archivo principal: `src/connectors/telegram_polling.py`
- Usa `python-telegram-bot` (ApplicationBuilder, handlers async, filters).
- Lee el token y nombre del bot desde `.env` (`TELEGRAM_TOKEN`, `TELEGRAM_BOT_NAME`).
- Integra con el `BotManager` para normalizar mensajes y despachar a los handlers (moderación, bienvenida, encuesta, sorteo).
- Implementa comandos:
  - `/start`, `/help`, `/reglas` (bienvenida y ayuda)
  - Comandos admin: `/warn`, `/mute`, `/unmute`, `/kick`, `/ban`, `/unban` (requieren permisos de admin)
- Da la bienvenida a nuevos miembros y muestra reglas si están configuradas.
- Aplica acciones de moderación:
  - Elimina mensajes, advierte, silencia (mute), expulsa (kick), banea (ban) según reglas y configuración.
  - Notifica a admins si está activado `admin_notify` en las reglas.
- Respeta el modo `enforce_only` (solo actúa en moderación, no responde en grupos si está activado).
- Audita todas las acciones en memoria (o en base de datos si se activa).

## Archivos modificados/creados
- `src/connectors/telegram_polling.py`: conector Telegram completo
- `.env.example`: variables `TELEGRAM_TOKEN`, `TELEGRAM_BOT_NAME`
- `run.py`: modo de arranque `START_MODE=polling`
- `src/config/rules.yaml`: reglas de moderación y opciones avanzadas

## Cómo usar
1. Crea el bot en BotFather y copia el token en tu `.env` como `TELEGRAM_TOKEN=...`
2. (Opcional) Configura el nombre en `TELEGRAM_BOT_NAME`.
3. Personaliza reglas en `src/config/rules.yaml` (palabras prohibidas, flood, mute, etc).
4. Instala dependencias: `pip install -r requirements.txt`
5. Arranca el bot:
   - En PowerShell:
     ```powershell
     cd "backend\bots\Comunidad"
     $env:START_MODE = "polling"
     & "<ruta_python_venv>" run.py
     ```
6. El bot se conectará y aplicará la lógica de moderación y comandos en los grupos donde esté agregado.

## Notas
- Si falta el token, el conector muestra un error claro y no arranca.
- El bot debe tener permisos de admin para aplicar sanciones en grupos.
- El modo `enforce_only` permite operar solo como moderador, sin responder mensajes normales.
- Todas las acciones se auditan y pueden persistirse en base de datos.

---
¿Dudas o quieres ejemplos de configuración avanzada, comandos admin o integración con panel web? Avísame y lo agrego.