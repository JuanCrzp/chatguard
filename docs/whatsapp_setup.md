# WhatsApp Cloud API — Guía de configuración

Esta guía te deja el conector de WhatsApp operativo en minutos usando la Cloud API de Meta.

## Requisitos
- Cuenta de desarrollador en Meta y acceso a WhatsApp Cloud API.
- Un número de prueba o número propio conectado en la sección de WhatsApp.
- Dominio público (o túnel tipo ngrok) para recibir webhook.

## Variables de entorno (.env)
Copia `.env.example` a `.env` y rellena:

- `WHATSAPP_TOKEN`: Token de acceso de la Cloud API (obligatorio).
- `WHATSAPP_VERIFY_TOKEN`: Texto que tú defines para validar el webhook (Meta te lo pedirá).
- `WHATSAPP_API_VERSION` (opcional): por defecto `v20.0`.
- `WHATSAPP_PHONE_NUMBER_ID` (opcional): si no lo pones, el conector toma el `phone_number_id` del webhook entrante.

## Endpoints expuestos
- Verificación (GET): `https://TU_DOMINIO/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=WHATSAPP_VERIFY_TOKEN&hub.challenge=123456`
- Recepción (POST): `https://TU_DOMINIO/webhooks/whatsapp`

## Pasos en el Dashboard de Meta
1. En tu aplicación: WhatsApp > Configuration > Webhooks.
2. Webhook URL: `https://TU_DOMINIO/webhooks/whatsapp`
3. Verify Token: el mismo que pusiste en `WHATSAPP_VERIFY_TOKEN`.
4. Suscribe el campo `messages`.

## Flujo de mensajes
- Entrante: Meta enviará `entry[].changes[].value.messages[]`.
- El conector normaliza el mensaje y lo pasa al `BotManager`.
- Si `SEND_AUTOMATIC_RESPONSES=true`, el bot responde con texto usando `enviar_mensaje_whatsapp`.

## Prueba rápida
1. Levanta el servidor FastAPI.
2. Verifica el webhook desde Meta (debe responder con el `hub.challenge`).
3. Envía un mensaje al número configurado y revisa logs.

## Solución de problemas
- 403 al verificar: revisa `WHATSAPP_VERIFY_TOKEN`.
- 401/403 al enviar: revisa `WHATSAPP_TOKEN`.
- No se envía respuesta: asegúrate de tener `SEND_AUTOMATIC_RESPONSES=true`.
- `phone_number_id` faltante: añade `WHATSAPP_PHONE_NUMBER_ID` en `.env` o espera a recibir un webhook (el conector lo cachea).
