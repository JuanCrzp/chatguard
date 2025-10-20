

<h1 align="center">ChatGuard</h1>
<p align="center"><b>Moderación y gestión profesional para comunidades en Telegram, Discord, WhatsApp y más</b></p>

> Rules: YAML • Licencia: Apache 2.0 • Runtime: Python 3.10+ • Estado: Enterprise

---

### Enlaces rápidos

- Guía de administración: [docs/guia_admin.md](docs/guia_admin.md)
- Referencia de reglas: [docs/rules_reference.md](docs/rules_reference.md)
- Despliegue: [docs/deployment.md](docs/deployment.md)
- Arquitectura: [docs/architecture.md](docs/architecture.md)
- Conectores: [docs/telegram_connector.md](docs/telegram_connector.md), [docs/discord_connector.md](docs/discord_connector.md), [docs/whatsapp_setup.md](docs/whatsapp_setup.md)
- Privacidad del bot: [docs/privacidad_bot.md](docs/privacidad_bot.md)

---

## 📑 Tabla de Contenidos

- [Características principales](#características-principales)
- [Ejemplos de uso](#️-ejemplos-de-uso)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Despliegue y uso](#despliegue-y-uso)
- [Comandos de administración](#comandos-de-administración)
- [Arquitectura](#arquitectura)
- [Pruebas y diagnóstico](#pruebas-y-diagnóstico)
- [Soporte y contacto](#soporte-y-contacto)
- [Licencia y autoría](#licencia-y-autoría)

---

## 🚀 Características principales

| Función                | Descripción                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| Moderación automática  | Filtrado de palabras, regex, thresholds, mute/kick/ban, borrado de mensajes  |
| Silencio en grupos     | `enforce_only`: solo modera, no responde saludos ni fallback en grupos       |
| Configuración flexible | Herencia y overrides por chat/guild, switches de features                    |
| Multi-plataforma       | Telegram, Discord, WhatsApp, Webchat (conectores modulares)                  |
| Bienvenida y encuestas | Mensajes de bienvenida, encuestas, sorteos, comandos para admins             |
| Diagnóstico avanzado   | Scripts para inspección de reglas y pruebas internas                         |
| Logs profesionales     | Trazabilidad de acciones y supresión por reglas                              |

---

## 🧭 Casos de uso

| Escenario | Objetivo | Configuración sugerida |
|---|---|---|
| Grupo público con alto tráfico | Silencio total del bot, solo moderación | `moderation.enforce_only: true`, `features.greeting_enabled: false`, `features.fallback_enabled: false` |
| Comunidad privada con onboarding | Bienvenida y reglas automáticas | `welcome_enabled: true`, `rules_command_enabled: true` |
| Eventos con sorteos | Interacción puntual y transparente | `raffle_enabled: true`, reglas de elegibilidad en `rules.yaml` |
| Encuestas de pulso | Recoger feedback rápido | `survey_enabled: true` y handler `encuesta` activo |
| Servidor Discord con roles | Moderación y utilidades admin | Activa comandos admin y permisos del bot correctos |

---

## ✉️ Ejemplos de uso

1) Telegram — Grupo con `enforce_only: true` (silencio total, solo modera)

```
Usuario: hola
Bot: (no responde)
Usuario: [mensaje con palabra prohibida]
Bot: (borra mensaje) [opcional] • Acción: warn/mute según thresholds
```

2) Telegram — DM (el bot sí puede conversar)

```
Usuario: hola
Bot: ¡Hola! ¿En qué puedo ayudarte? (si greeting_enabled=true)
```

3) Discord — Comando admin

```
Admin: !mute @usuario 10
Bot: Usuario silenciado por 10 minutos.
```

---

## ⚙️ Instalación

1. Clona el repositorio y entra a la carpeta:
   ```bat
   git clone https://github.com/tu_usuario/chatguard.git
   cd chatguard
   ```
2. (Opcional) Crea un entorno virtual:
   ```bat
   python -m venv venv
   venv\Scripts\activate
   ```
3. Instala dependencias:
   ```bat
   pip install -r requirements.txt
   ```
4. Copia y edita el archivo de variables de entorno:
   ```bat
   copy examples\sample_env_vars.md .env
   ```
   Completa los valores requeridos en `.env`.

---

## 🛠️ Configuración

La configuración principal está en [`config/rules.yaml`](config/rules.yaml). Ejemplo básico:

```yaml
default:
  moderation:
    enforce_only: true
    thresholds:
      warn: 2
      mute: 4
      kick: 6
      ban: 8
    warn_message: "Por favor, respeta las normas."
  features:
    greeting_enabled: false
    fallback_enabled: false
    welcome_enabled: true
    survey_enabled: true
    raffle_enabled: true
    rules_command_enabled: true
```

Overrides por chat/guild:

```yaml
-100123456789:
  moderation:
    enforce_only: false
  features:
    greeting_enabled: true
```

Más detalles en [docs/rules_reference.md](docs/rules_reference.md).

---

## 🚦 Despliegue y uso

### Windows (recomendado)

Ejecuta el lanzador profesional:
```bat
scripts\run_chatguard.bat
```

Esto abrirá los conectores de Telegram y Discord en ventanas separadas.

### Manual (avanzado)
```bat
python src\connectors\telegram_polling.py
python src\connectors\discord_connector.py
```

---

## 🛡️ Comandos de administración

| Plataforma | Comando                              | Descripción breve                                       | Observaciones |
|------------|--------------------------------------|---------------------------------------------------------|--------------|
| Telegram   | /warn @usuario                        | Aplica advertencia según thresholds                     | Requiere permisos admin |
| Telegram   | /mute @usuario [min]                  | Silencia al usuario por N minutos                       | Usa `mute_duration_seconds` por defecto |
| Telegram   | /unmute @usuario                      | Quita silencio                                          | — |
| Telegram   | /kick @usuario                        | Expulsa al usuario                                      | — |
| Telegram   | /ban @usuario                         | Banea al usuario                                        | — |
| Telegram   | /unban @usuario                       | Quita el ban                                            | — |
| Telegram   | /modhelp                              | Muestra ayuda de moderación                             | — |
| Telegram   | /reload                               | Recarga `rules.yaml`                                    | Útil tras editar reglas |
| Discord    | !warn @usuario                        | Aplica advertencia según thresholds                     | Requiere rol/mod permisos |
| Discord    | !mute @usuario [min]                  | Silencia al usuario por N minutos                       | — |
| Discord    | !unmute @usuario                      | Quita silencio                                          | — |
| Discord    | !kick @usuario                        | Expulsa al usuario                                      | — |
| Discord    | !ban @usuario                         | Banea al usuario                                        | — |
| Discord    | !unban @usuario                       | Quita el ban                                            | — |
| Discord    | !purge [n]                            | Elimina N mensajes recientes                            | Limites según permisos |
| Discord    | !diag_perms                           | Diagnóstico de permisos del bot                         | Útil para soporte |

Ver detalles y sintaxis en [docs/admin_commands.md](docs/admin_commands.md).

---

## 🏗️ Arquitectura

Estructura modular:
- `src/app/`: API y servidor principal
- `src/bot_core/`: lógica de moderación y gestión
- `src/connectors/`: conectores para cada plataforma
- `src/handlers/`: comandos y respuestas
- `src/nlu/`: procesamiento de lenguaje
- `src/storage/`: persistencia y modelos
- `src/tasks/`: recordatorios y tareas
- `src/utils/`: utilidades generales

---

## 🧪 Pruebas y diagnóstico

Ejecuta la suite de tests:
```bat
pytest -q
```

Utilidades internas:
- Inspección de reglas: `python tools\inspect_rules.py`
- Pruebas de comportamiento: `python tools\internal_test.py`

---

## ❓ FAQ

- ¿Por qué el bot no responde en mi grupo?  
  Probablemente `moderation.enforce_only: true` y/o `features.greeting_enabled: false`. En grupos, con enforce_only, el bot solo modera.

- Cambié `rules.yaml` pero no veo efecto.  
  Usa `/reload` (Telegram) o reinicia el proceso para aplicar cambios; valida con `tools/inspect_rules.py`.

- ¿Cómo desactivo las advertencias públicas?  
  Sube `thresholds.warn` o establece `warn_message: null`.

- ¿Necesita permisos especiales en Discord?  
  Sí, según comandos. Usa `!diag_perms` para verificar.

- ¿Puedo tener distintas reglas por grupo/servidor?  
  Sí, mediante overrides por `chat_id` (TG) o `guild_id` (Discord) en `rules.yaml`.

---

## 🤝 Soporte y contacto

- Documentación: carpeta [`docs/`](docs/)
- Reporta problemas: Issues en este repositorio con pasos para reproducir, logs y versión
- Contribuye: lee [CONTRIBUTING.md](CONTRIBUTING.md) antes de abrir un PR
- Seguridad: reporta vulnerabilidades siguiendo [SECURITY.md](SECURITY.md)
- Contacto: Juan Camilo Cruz P (GitHub: [@JuanCrzp](https://github.com/JuanCrzp))

---

## 📄 Licencia y autoría

- Licencia: Apache License 2.0 ([LICENSE.txt](LICENSE.txt))
- Autor: Juan Camilo Cruz P (GitHub: [@JuanCrzp](https://github.com/JuanCrzp))

