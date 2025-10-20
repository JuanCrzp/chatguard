# security.py - Seguridad básica para Bot Comunidad
import re

def sanitizar_texto(texto):
    # Elimina scripts y etiquetas peligrosas
    texto = re.sub(r'<.*?>', '', texto)
    texto = re.sub(r'(script|onerror|onload)', '', texto, flags=re.IGNORECASE)
    return texto

def validar_usuario(user_id):
    # Ejemplo: solo IDs numéricos permitidos
    return str(user_id).isdigit()
