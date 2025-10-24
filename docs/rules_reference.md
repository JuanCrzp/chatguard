# Guía completa de configuración (rules.yaml)

Esta guía explica todos los campos disponibles en `config/rules.yaml`, cómo funciona la herencia y cómo personalizar por chat/servidor.

## Estructura general

- `default`: reglas globales (se aplican a todos los chats/servidores).
- `-100123...` (sin comillas): chat_id de Telegram (override por grupo).
- `"987654..."` (con comillas): guild_id de Discord (override por servidor).

Herencia (deep merge): primero se aplican las claves de `default` y luego se fusionan recursivamente con el bloque del chat/servidor si existe. No necesitas duplicar toda la estructura: declara solo lo que quieras cambiar. Las claves tipo diccionario se combinan; listas y escalares se reemplazan por los del override.

## Campos de primer nivel

- `enabled` (bool): enciende/apaga el bot para ese chat.
- `title` (str): título que se muestra junto a las reglas.
- `items` (list[str]): lista de reglas del grupo.
- `max_message_length` (int): máximo permitido para mensajes (0 = sin límite).
- `link_whitelist` (list[str]): dominios permitidos si `allow_links=false`.
- `invite_links_allowed` (bool): permitir enlaces de invitación.
- `caps_lock_threshold` (int): % de mayúsculas para considerar gritos.

### features (switches conversacionales)

Permite encender/apagar, por chat/servidor, lo que el bot “dice” aparte de la moderación. Si no defines `features`, el bot usa defaults compatibles con `welcome`, `survey` y claves en `moderation`.

Claves:
- `rules_command_enabled` (bool): comando para mostrar reglas (/reglas). Default: true.
- `fallback_enabled` (bool): respuesta genérica “No entendí”. Default: true.
- `greeting_enabled` (bool): respuestas a saludos (intent greeting). Default: usa `moderation.greetings_enabled` o true.
- `welcome_enabled` (bool): mensajes de bienvenida (nuevos miembros, /start). Default: usa `welcome.enabled` o true.
- `survey_enabled` (bool): encuestas por intención. Default: usa `survey.enabled` o true.
- `raffle_enabled` (bool): sorteos por intención. Default: true.

Ejemplo básico en `default`:

```yaml
default:
  features:
    rules_command_enabled: true
    fallback_enabled: false    # Desactiva el “No entendí” globalmente
    greeting_enabled: false    # No responder saludos
    welcome_enabled: true
    survey_enabled: true
    raffle_enabled: false
```

## moderation

- `thresholds` (dict): umbrales de sanción.
  - `warn` (int): desde cuántas infracciones se advierte.
  - `mute` (int): desde cuántas infracciones se mutea.
  - `kick` (int): desde cuántas infracciones se expulsa.
  - `ban` (int): desde cuántas infracciones se banea.
- `mute_duration_seconds` (int): duración de mute.
- `ban_duration_seconds` (int): duración de ban temporal (0 = permanente).
- `kick_rejoin_seconds` (int): >0 expulsión temporal (ban corto + unban), <=0 equivalente a ban permanente.
- `banned_words` (list[str]): palabras prohibidas.
- `regex_patterns` (list[str]): patrones prohibidos (regex, escapar barras en YAML).
- `flood_limit` (int): límite de mensajes por minuto por usuario.
- `whitelist_users` (list[str|int]): usuarios exentos de moderación.
- `allow_links` (bool): permitir enlaces.
- `allow_files` (bool): permitir archivos.
- `delete_message_on_violation` (bool): elimina el mensaje infractor.
- `enforce_only` (bool): si true, el bot solo actúa ante violaciones.
- `greetings_enabled` (bool): habilita mensajes de bienvenida.
- `admin_notify` (bool): envía aviso al chat cuando se sanciona.
- `log_actions` (bool): habilita logs de sanciones.
- `action_messages_enabled` (dict): controla si se muestran mensajes públicos al aplicar cada acción. Claves: `warn`, `mute`, `kick`, `ban`. Por defecto `true`.
- `mute_types` (list[str]): "text", "media" o "all".
- Mensajes personalizados (placeholders disponibles: `{user}`, `{minutes}`, `{hours}`, `{seconds}`):
  - `warn_message` (str)
  - `mute_message` (str)
  - `kick_message` (str)
  - `ban_message` (str)
- Aviso a muteados:
  - `muted_notice_enabled` (bool)
  - `muted_notice` (str) | alias: `muted_notice_message`
  - `soft_mute_enforce_delete` (bool)
  - `soft_mute_notice` (str)

## welcome

- `enabled` (bool): habilita la bienvenida.
- `message` (str): plantilla de bienvenida. Placeholders: `{user}`, `{group}`, `{rules_title}`.
- `show_rules` (bool): añade el título de reglas al mensaje.
- `channel_id` (str|int, Discord): canal donde se manda la bienvenida. Si no se define, se usa `system_channel` o el primer canal de texto con permiso.

## survey

- `enabled` (bool)
- `max_options` (int)
- `allow_multiple` (bool)
- `anonymous` (bool)
- `create_message` (str): plantilla, placeholder `{question}`.
- `vote_message` (str): plantilla, placeholders `{user}`, `{option}`.

## reminder

- `enabled` (bool)
- `text` (str)
- `hour` (HH:MM)
- `days` (list[str]): mon, tue, wed, thu, fri, sat, sun. Si se omite o está vacío, corre todos los días.

## Ejemplo de override por Telegram

```yaml
-123456789:
  enabled: true
  welcome:
    enabled: true
    message: "¡Bienvenido/a {user}! Lee las reglas fijadas del grupo."
    show_rules: true
  survey:
    enabled: true
    max_options: 6
    allow_multiple: true
  moderation:
    action_messages_enabled:
      warn: true
      mute: false   # Ejemplo: silencia anuncios de mute (la acción se aplica sin mensaje público)
      kick: true
      ban: true
    thresholds:
      warn: 2
      mute: 3
      kick: 4
      ban: 6
    banned_words: ["spoiler", "spam"]
    muted_notice_enabled: true
    soft_mute_enforce_delete: false
```

## Ejemplo de override por Discord

```yaml
"987654321098765432":
  enabled: true
  welcome:
    enabled: true
    message: "¡Bienvenido/a {user}! Consulta #reglas para más info."
  survey:
    enabled: true
  moderation:
    thresholds:
      warn: 1
      mute: 2
      kick: 3
      ban: 5
    banned_words: ["spam", "casino"]
    admin_notify: true
    muted_notice_enabled: true
    soft_mute_enforce_delete: true
```

## Consejos

- No dupliques toda la config en overrides: define solo lo que cambias.
- Cuando edites `rules.yaml`, usa `/reload` en Telegram o reinicia el bot de Discord.
- En Discord asegúrate de permisos: Kick Members, Ban Members, Moderate Members (si quieres timeout) y Manage Channels para el fallback de mute.

## Ubicación de `enforce_only` y compatibilidad

- Puedes definir `enforce_only` dentro de `moderation` (recomendado) o a nivel superior del bloque del chat/servidor; el bot soporta ambas ubicaciones.
- La herencia ahora es profunda (deep merge): si no defines `moderation.enforce_only` en un override, heredará el valor de `default.moderation.enforce_only`.

## Ejemplos prácticos de switches

- Desactivar el comando de reglas en un chat específico (Telegram):

```yaml
-123456789:
  features:
    rules_command_enabled: false
```

- Permitir encuestas solo en un servidor de Discord:

```yaml
"987654321098765432":
  features:
    survey_enabled: true
    raffle_enabled: false
```

- Modo “solo moderación” en todos los chats (sin hablar) y sin fallback:

```yaml
default:
  moderation:
    enforce_only: true
  features:
    fallback_enabled: false
    greeting_enabled: false
    welcome_enabled: false
    survey_enabled: false
    raffle_enabled: false
```
# Referencia de configuración: rules.yaml

Este documento te ayuda a entender y modificar las reglas que usa el bot para moderar y gestionar tu grupo, aunque no tengas experiencia técnica.

## ¿Qué es este archivo?
`rules.yaml` es como el “manual de convivencia” del grupo, pero para el bot. Aquí decides qué está permitido, qué se sanciona y cómo debe comportarse el bot.

## ¿Cómo funciona?
- Cada grupo puede tener sus propias reglas. Si no pones reglas para tu grupo, se usan las que están en `default:`.
- El bot lee este archivo para saber qué hacer ante un mensaje, un usuario nuevo o una posible infracción.

## Estructura básica
- `default:` contiene las reglas por defecto (se aplican a todos los grupos que no tengan una configuración específica).
- Puedes crear una sección por grupo usando su `chat_id` (por ejemplo, `-123456789:`) y sobreescribir lo que necesites.

## ¿Qué puedo configurar?
Imagina que quieres que el bot:
- Salude a los nuevos miembros.
- Elimine mensajes con palabras prohibidas.
- Silencie (mute) a quien haga spam.
- Expulse o banee a quien rompa las reglas varias veces.
- Permita o bloquee enlaces, archivos, mensajes largos, etc.
Todo eso lo decides aquí, cambiando valores de la configuración.

## Claves principales

### items
Lista de reglas que el bot puede mostrar a los usuarios. Ejemplo:

```
items:
  - Respeta a todos los miembros.
  - No spam ni promociones sin permiso.
```

### moderation
Opciones para controlar cómo y cuándo el bot sanciona:
- thresholds: cuántas infracciones para cada acción:
  - warn: advertencia
  - mute: silenciar
  - kick: expulsar
  - ban: banear
- mute_duration_seconds: cuánto tiempo dura el mute.
- ban_duration_seconds: duración del ban cuando aplica “ban” (0 = permanente).
- kick_rejoin_seconds: controla el comportamiento de “kick” (expulsión):
  - > 0: expulsión temporal; podrá volver a entrar después de X segundos.
  - 0 o < 0: tratar el “kick” como ban permanente (no podrá volver a entrar).
- banned_words: lista de palabras prohibidas.
- regex_patterns: patrones avanzados para detectar insultos, spam, etc.
- flood_limit: límite de mensajes por minuto por usuario (0 = sin límite).
- whitelist_users: usuarios exentos de moderación.
- allow_links / allow_files: permitir enlaces y archivos.
- delete_message_on_violation: borrar el mensaje que viola las reglas.
- enforce_only: si está en true, el bot solo sanciona (no saluda ni conversa en grupos).
- greetings_enabled: activa/desactiva saludos de bienvenida.
- admin_notify: notifica en el chat cuando se sanciona a alguien.
- warn_message, kick_message, ban_message: textos personalizados por acción.
- mute_types: tipos de mute ("text", "media", "all").
- max_message_length: longitud máxima de mensaje (0 = sin límite). Puede ir dentro de moderation o a nivel de reglas (el bot soporta ambas ubicaciones).
- link_whitelist: dominios permitidos cuando allow_links=false. Puede ir dentro de moderation o a nivel de reglas.
- invite_links_allowed: permite enlaces de invitación (ej: t.me/joinchat). Puede ir dentro de moderation o a nivel de reglas.
- caps_lock_threshold: porcentaje de MAYÚSCULAS para considerar “gritos” (0 = desactivado). Puede ir dentro de moderation o a nivel de reglas.
- log_actions: registrar acciones (útil para auditoría).

### Kick vs Ban (¿pueden volver?)
- Si quieres que el expulsado pueda volver: usa kick_rejoin_seconds > 0 (por ejemplo, 60 segundos).
- Si quieres que NO pueda volver con “kick”: pon kick_rejoin_seconds: 0 (el kick se comporta como ban permanente).


## Recordatorios (reminder)

Los recordatorios automáticos se configuran por chat directamente en `rules.yaml` bajo la clave `reminder`.

- Claves disponibles:
  - `enabled` (bool): activa/desactiva el recordatorio para ese chat.
  - `text` (str): mensaje a enviar.
  - `hour` (HH:MM 24h): hora diaria de envío.
  - `days` (list[str], opcional): días de la semana en los que se enviará. Valores válidos: `mon, tue, wed, thu, fri, sat, sun`. Si se omite o está vacío, se envía todos los días.

- Comportamiento por chat:
  - Para claves con `chat_id` (ej.: `-123456789`), el recordatorio se envía a ese chat directamente.
  - Para `default.reminder`, el destino se toma de la variable `REMINDER_CHAT_ID` en `.env`.

- Ejemplos:

```yaml
default:
  reminder:
    enabled: true
    text: "Recordatorio semanal: lee las reglas."
    hour: "09:00"
    days: [mon]  # Solo los lunes
-123456789:
  reminder:
    enabled: true
    text: "¡No olvides participar en la encuesta!"
    hour: "18:00"
    days: [mon, wed, fri]
```

**Notas importantes:**
- El script `reminders.py` ahora respeta correctamente el campo `days` de cada recordatorio, enviando el mensaje solo los días configurados.
- Si tienes un archivo `.env`, las variables necesarias (`TELEGRAM_TOKEN`, `REMINDER_CHAT_ID`) se cargan automáticamente si tienes instalada la librería `python-dotenv`.
- Si cambias `rules.yaml`, reinicia el script de recordatorios para aplicar los cambios.
- Si `hour` es inválido, se usará `09:00` y se mostrará advertencia; si `days` tiene valores inválidos, se advertirá en consola cuáles son válidos.
- `/reload` solo afecta al bot principal, no reinicia el proceso de `reminders.py`.

## Ejemplo de configuración completa (por defecto)

```yaml
default:
  title: Reglas del Grupo
  items:
    - Respeta a todos los miembros.
    - No spam ni promociones sin permiso.
    - Usa los canales adecuados para cada tema.
    - Evita lenguaje ofensivo.
  moderation:
    thresholds:
      warn: 1
      mute: 2
      kick: 3
      ban: 4
    mute_duration_seconds: 900
    ban_duration_seconds: 0
    kick_rejoin_seconds: 60   # 60s => expulsión temporal; 0 => tratar kick como ban permanente
    banned_words: ["spam", "oferta", "prohibido"]
    regex_patterns: ["\\bpalabrota\\b", "\\bcasino\\b"]
    flood_limit: 0
    whitelist_users: []
    allow_links: true
    allow_files: true
    delete_message_on_violation: true
    enforce_only: true
    greetings_enabled: true
    admin_notify: false
    warn_message: "¡Advertencia! Tu mensaje viola las reglas."
    kick_message: "Has sido expulsado por incumplir las normas."
    ban_message: "Has sido baneado permanentemente."
    mute_types: ["all"]
  max_message_length: 0
  link_whitelist: []
  invite_links_allowed: true
  caps_lock_threshold: 0
```

## Recetas rápidas

- Hacer que el expulsado NO pueda volver con “kick”:
  ```yaml
  moderation:
    kick_rejoin_seconds: 0
  ```

- Expulsión temporal de 10 minutos (luego puede volver):
  ```yaml
  moderation:
    kick_rejoin_seconds: 600
  ```

- Ban temporal por 24 horas cuando corresponda “ban”:
  ```yaml
  moderation:
    ban_duration_seconds: 86400
  ```

## ¿Cómo cambio algo?
1. Abre el archivo `config/rules.yaml`.
2. Busca la opción que quieres cambiar.
3. Cambia el valor (true/false, número, texto, lista).
4. Guarda el archivo. El bot usará la nueva configuración.

## ¿Qué pasa si me equivoco?
Si el archivo tiene un error de formato (por ejemplo, espacios o comas mal puestos), el bot podría ignorar los cambios. Revisa la indentación (espacios) y que las listas/textos estén bien escritos.

## Buenas prácticas
- Personaliza las reglas y opciones por grupo según tu comunidad.
- Usa `enforce_only` para modo “solo moderación” si no quieres saludos.
- Mantén actualizada la lista de palabras y patrones prohibidos.
- Ajusta thresholds y duraciones para balancear flexibilidad y control.

## Overrides por grupo
Para configurar un grupo concreto, usa su chat_id como clave de primer nivel:

```yaml
-123456789:
  title: Reglas de Mi Comunidad
  items:
    - No spoilers sin avisar.
    - Comparte recursos con fuentes.
  moderation:
    kick_rejoin_seconds: 0   # En este grupo, el "kick" será ban permanente
```

¿Dudas o necesitas ejemplos avanzados? Avísame y lo agrego.
# Referencia de configuración: rules.yaml

Este documento te ayuda a entender y modificar las reglas que usa el bot para moderar y gestionar tu grupo, aunque no tengas experiencia técnica.

## ¿Qué es este archivo?
`rules.yaml` es como el “manual de convivencia” del grupo, pero para el bot. Aquí decides qué está permitido, qué se sanciona y cómo debe comportarse el bot.

## ¿Cómo funciona?
- Cada grupo puede tener sus propias reglas. Si no pones reglas para tu grupo, se usan las que están en `default:`.
- El bot lee este archivo cada vez que necesita saber qué hacer ante un mensaje, un usuario nuevo o una posible infracción.

## ¿Qué puedo configurar?
Imagina que tienes un grupo y quieres que el bot:
- Salude a los nuevos miembros.
- Elimine mensajes con palabras prohibidas.
- Silencie (mute) a quien haga spam.
- Expulse o banee a quien rompa las reglas varias veces.
- Permita o bloquee enlaces, archivos, mensajes largos, etc.
Todo eso lo decides aquí, cambiando valores de la configuración.

## Explicación de las opciones principales

### items
Lista de reglas que el bot puede mostrar a los usuarios. Ejemplo:
```
items:
  - Respeta a todos los miembros.
  - No spam ni promociones sin permiso.
```

### moderation
Opciones para controlar cómo y cuándo el bot sanciona:
- **thresholds**: ¿Cuántas veces debe romper una regla alguien para que el bot lo advierta, silencie, expulse o banee?
- **mute_duration_seconds**: ¿Cuánto tiempo estará silenciado quien haga algo mal?
- **ban_duration_seconds**: ¿Cuánto dura el ban? (0 = para siempre)
- **banned_words**: Palabras que no se pueden decir.
- **regex_patterns**: Patrones avanzados para detectar insultos, spam, etc.
- **flood_limit**: ¿Cuántos mensajes seguidos puede mandar una persona antes de que el bot lo sancione?
- **whitelist_users**: Usuarios que nunca serán sancionados (por ejemplo, admins).
- **allow_links**: ¿Se pueden compartir enlaces?
- **allow_files**: ¿Se pueden compartir archivos?
- **delete_message_on_violation**: ¿El bot borra el mensaje que rompe las reglas?
- **enforce_only**: Si está en true, el bot solo sanciona, no conversa ni saluda.
- **greetings_enabled**: Si está en true, el bot saluda a los nuevos y responde a /start. Si está en false, no lo hace.
- **admin_notify**: ¿El bot avisa a los admins cuando sanciona a alguien?
- **warn_message**, **kick_message**, **ban_message**: Mensajes personalizados para cada sanción.
- **mute_types**: ¿Qué tipo de mensajes silencia el bot? (texto, multimedia, todo)
- **max_message_length**: ¿Cuál es el máximo de caracteres permitidos por mensaje?
- **link_whitelist**: ¿Qué dominios sí se pueden compartir si los enlaces están bloqueados?
- **invite_links_allowed**: ¿Se pueden compartir enlaces de invitación?
- **caps_lock_threshold**: ¿Cuánto porcentaje de mayúsculas se considera “gritar”?

## Ejemplo sencillo
Supón que quieres que el bot salude, borre mensajes con “spam” y silencie a quien mande más de 5 mensajes por minuto:
```yaml
default:
  title: Reglas del Grupo
  items:
    - Respeta a todos.
    - No spam.
  moderation:
    banned_words: ["spam"]
    flood_limit: 5
    mute_duration_seconds: 300
    greetings_enabled: true
    enforce_only: false
```

## ¿Cómo cambio algo?
1. Abre el archivo `rules.yaml` con un editor de texto.
2. Busca la opción que quieres cambiar (por ejemplo, `greetings_enabled`).
3. Pon `true` para activar o `false` para desactivar.
4. Guarda el archivo. El bot usará la nueva configuración automáticamente.

## ¿Qué pasa si me equivoco?
No te preocupes. Si el archivo tiene un error de formato (por ejemplo, espacios mal puestos), el bot te avisará y no aplicará los cambios hasta que lo corrijas.

## Recomendaciones para admins
- Revisa y ajusta las reglas según el tipo de grupo y lo que quieras lograr.
- Si tienes dudas, pide ayuda o usa los ejemplos de este documento.
- Puedes tener reglas diferentes para cada grupo usando el chat_id como clave.

---
¿Tienes dudas o quieres ejemplos para tu caso? Avísame y te ayudo a configurarlo.

Este archivo define las reglas y opciones de moderación para cada grupo o chat del bot. Permite personalizar el comportamiento del bot de forma profesional y centralizada.

## Estructura
- Cada grupo/chat puede tener su propia configuración usando su chat_id como clave.
- Si no existe una clave específica, se usan las reglas bajo `default:`.

## Claves principales

### items
Lista de reglas que se mostrarán a los usuarios (por ejemplo, en /reglas o al ingresar al grupo).

### moderation
Opciones de moderación y control de comportamiento:
- **thresholds**: define cuántas infracciones se requieren para cada acción:
  - `warn`: advertencia
  - `mute`: silenciar
  - `kick`: expulsar
  - `ban`: banear
- **mute_duration_seconds**: duración del mute en segundos.
- **ban_duration_seconds**: duración del ban temporal (0 = permanente).
- **banned_words**: lista de palabras prohibidas.
- **regex_patterns**: expresiones regulares prohibidas.
- **flood_limit**: límite de mensajes por minuto por usuario (0 = desactivado).
- **whitelist_users**: usuarios exentos de moderación.
- **allow_links**: permite o bloquea enlaces.
- **allow_files**: permite o bloquea archivos adjuntos.
- **delete_message_on_violation**: si es true, borra el mensaje que viola reglas.
- **enforce_only**: si es true, el bot solo actúa ante violaciones (no responde saludos ni conversa).
- **greetings_enabled**: si es true, el bot saluda a nuevos miembros y responde a /start; si es false, no lo hace.
- **admin_notify**: si es true, notifica a los administradores cuando se sanciona a alguien.
- **warn_message**, **kick_message**, **ban_message**: mensajes personalizados para cada acción.
- **mute_types**: tipos de mute aplicados (`text`, `media`, `all`).
- **max_message_length**: longitud máxima permitida por mensaje (0 = sin límite).
- **link_whitelist**: dominios permitidos si `allow_links` es false.
- **invite_links_allowed**: permite enlaces de invitación (ej: t.me/joinchat).
- **caps_lock_threshold**: porcentaje de MAYÚSCULAS para considerar 'gritos' (0 = desactivado).

## Ejemplo de configuración
```yaml
default:
  title: Reglas del Grupo
  items:
    - Respeta a todos los miembros.
    - No spam ni promociones sin permiso.
    - Usa los canales adecuados para cada tema.
    - Evita lenguaje ofensivo.
  moderation:
    thresholds:
      warn: 1
      mute: 2
      kick: 3
      ban: 4
    mute_duration_seconds: 900
    ban_duration_seconds: 0
    banned_words: ["spam", "oferta", "prohibido"]
    regex_patterns: ["\\bpalabrota\\b", "\\bcasino\\b"]
    flood_limit: 0
    whitelist_users: []
    allow_links: true
    allow_files: true
    delete_message_on_violation: true
    enforce_only: true
    greetings_enabled: true
    admin_notify: false
    warn_message: "¡Advertencia! Tu mensaje viola las reglas."
    kick_message: "Has sido expulsado por incumplir las normas."
    ban_message: "Has sido baneado permanentemente."
    mute_types: ["all"]
    max_message_length: 0
    link_whitelist: []
    invite_links_allowed: true
    caps_lock_threshold: 0
```

## Buenas prácticas
- Personaliza las reglas y opciones por grupo según el tipo de comunidad.
- Usa `enforce_only` para modo solo moderación (cumplimiento).
- Activa/desactiva saludos con `greetings_enabled` según la cultura del grupo.
- Mantén actualizada la lista de palabras y patrones prohibidos.
- Ajusta los thresholds y duraciones para balancear flexibilidad y control.

---
¿Dudas o necesitas ejemplos avanzados? Avísame y lo agrego.# Referencia de reglas (rules.yaml)

Claves dentro de `moderation` por grupo/chat:

- thresholds.warn|mute|kick|ban (int): umbrales de escalado.
- mute_duration_seconds (int): duración del mute temporal.
- ban_duration_seconds (int): duración del ban temporal (0 = permanente).
- banned_words (list[str]): lista de palabras prohibidas.
- regex_patterns (list[str]): patrones regex prohibidos.
- flood_limit (int): mensajes por minuto por usuario (0 = off).
- whitelist_users (list[str]): usuarios exentos de moderación.
- allow_links (bool): permite enlaces.
- link_whitelist (list[str]): dominios permitidos si allow_links=false.
- invite_links_allowed (bool): permitir enlaces de invitación.
- allow_files (bool): permite archivos adjuntos.
- max_message_length (int): longitud máxima del mensaje (0 = sin límite).
- caps_lock_threshold (int): % de mayúsculas para “gritos” (0 = off).
- mute_types (list[str]): tipos de mute: text|media|all.
- enforce_only (bool): solo actuar ante violaciones (no conversación en grupos).
- admin_notify (bool): notificar en el chat cuando se sanciona.
- warn_message|kick_message|ban_message (str): mensajes personalizados.
- log_actions (bool): registrar acciones (útil para auditoría DB).

Ejemplo:

```yaml
<chat_id>:
  moderation:
    thresholds: { warn: 1, mute: 2, kick: 3, ban: 4 }
    mute_duration_seconds: 900
    ban_duration_seconds: 0
    banned_words: ["spam", "oferta", "prohibido"]
    regex_patterns: ["\\bpalabrota\\b"]
    flood_limit: 5
    whitelist_users: ["admin1"]
    allow_links: false
    link_whitelist: ["midominio.com"]
    invite_links_allowed: true
    allow_files: true
    max_message_length: 280
    caps_lock_threshold: 70
    mute_types: ["all"]
    enforce_only: true
    admin_notify: true
    warn_message: "Advertencia: revisa las reglas."
    kick_message: "Expulsado por incumplir normas."
    ban_message: "Baneado temporalmente."
    log_actions: true
```

## Machine Learning (Naive Bayes) para moderación

Además del modo clásico (palabras prohibidas y regex), el bot soporta un modo ML opcional basado en Naive Bayes. Este modo analiza el texto y, si la probabilidad de toxicidad o spam supera un umbral, aplica una acción inmediata (warn/mute/kick/ban) y, opcionalmente, borra el mensaje.

Claves dentro de `moderation.ml`:
- `enabled` (bool): activa/desactiva el modo ML. Cuando está en `false`, la moderación clásica sigue funcionando normalmente.
- `action` (str): acción a aplicar cuando el ML detecta infracción. Valores: `warn`, `mute`, `kick`, `ban`.
- `delete_on_ml` (bool): si es `true`, borra el mensaje detectado por ML (respetando `delete_message_on_violation`).
- `toxicity_threshold` (float 0-1): umbral de probabilidad para considerar tóxico.
- `spam_threshold` (float 0-1): umbral de probabilidad para considerar spam.
- `training` (dict): ejemplos de entrenamiento por clase.
  - `toxic` (list[str])
  - `spam` (list[str])
  - `normal` (list[str]) — ejemplos neutrales que ayudan a calibrar el clasificador.
 - `ml_mode` (str): "immediate" aplica acción directa según `action`; "thresholds" solo suma una infracción y respeta `thresholds` clásicos.

Ejemplo mínimo:

```yaml
default:
  moderation:
    ml:
      enabled: true
      ml_mode: immediate   # o thresholds
      action: mute
      delete_on_ml: true
      toxicity_threshold: 0.55
      spam_threshold: 0.9
      training:
        toxic: ["idiota", "imbecil", "maldito"]
        spam: ["gana dinero rapido", "haz clic aqui"]
        normal: ["hola como estas", "gracias por la ayuda"]
```

Detalles de implementación (alto nivel):
- Tokenización robusta con normalización y eliminación de acentos/diacríticos (e.g., “imbécil” ≈ “imbecil”).
- Clasificador Naive Bayes con suavizado de Laplace y normalización softmax de probabilidades.
- Cacheo del modelo por `(chat_id, firma_de_entrenamiento)` para rendimiento; se reconstruye si cambias la lista de ejemplos.
- Logs estructurados JSON de evaluación (`ml_eval`) y acción (`ml_action`) con scores y umbrales.
- Falla segura: si algo en ML lanza una excepción, el bot continúa con el modo clásico.

Buenas prácticas de entrenamiento:
- Incluye una clase `normal` con frases comunes para calibrar el contraste.
- Usa frases multi-palabra realistas (no solo insultos aislados) para mayor señal.
- Mantén balanceadas las clases (número de ejemplos similar entre toxic/spam/normal).
- Revisa `toxicity_threshold`: si es muy alto, el modelo no disparará; si es muy bajo, habrá falsos positivos.

FAQ y solución de problemas:
- “El ML no detecta insultos del entrenamiento” → Revisa: existencia de clase `normal`, umbral `toxicity_threshold` razonable (≈0.5–0.6), y que editaste `training` en el YAML correcto (default u override). Valida los logs `ml_eval`.
- “¿Apagar ML desactiva toda la moderación?” → No. Con `ml.enabled: false` el modo clásico sigue activo (banned_words, regex, etc.).
- “¿Los acentos afectan?” → En ML no; el tokenizador elimina diacríticos. En el modo clásico, la comparación es por substring en minúsculas; si quieres cubrir variantes con/ sin acento, añade ambas en `banned_words` o en `learning.toxic_words`.

## Aprendizaje de palabras (sin ML)

Para ampliar la moderación clásica sin tocar código, puedes declarar listas de palabras o frases que el bot “aprenda” como infracciones. Estas listas se agregan automáticamente a `banned_words` en tiempo de ejecución.

Claves dentro de `moderation.learning`:
- `toxic_words` (list[str]): se tratan como lenguaje tóxico/prohibido.
- `spam_words` (list[str]): frases típicas de spam.

Ejemplo:

```yaml
default:
  moderation:
    banned_words: ["spam", "oferta"]
    learning:
      toxic_words: ["idiota", "maldito"]
      spam_words: ["oferta limitada", "gana dinero rapido"]
```

Notas:
- Comparación en minúsculas y por substring simple (sensibilidad a diacríticos). Añade variantes si lo necesitas: `"imbecil", "imbécil"`.
- Estas listas se aplican tanto si `ml.enabled` está activo como si no, porque forman parte del modo clásico.
- Hot-reload: los cambios en `rules.yaml` se recargan en caliente; si no ves efecto, usa `/reload` (Telegram) o reinicia el proceso.
