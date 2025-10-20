# webchat_connector.py - Conector funcional para Webchat (mockup)

def enviar_mensaje_webchat(usuario_id, texto):
    # Aquí iría la lógica real para enviar mensajes al frontend webchat
    print(f"Enviando a Webchat {usuario_id}: {texto}")
    return {"sent": True, "usuario_id": usuario_id, "text": texto}

# Ejemplo de función para normalizar mensajes entrantes

def normalizar_mensaje_webchat(payload):
    return {
        "platform": "webchat",
        "platform_user_id": payload.get("user_id"),
        "group_id": payload.get("group_id"),
        "text": payload.get("text", ""),
        "raw_payload": payload
    }
