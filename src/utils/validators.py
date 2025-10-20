# validators.py - Validadores para Bot Comunidad

def validar_mensaje(texto):
    # Ejemplo: no permitir mensajes vacíos ni solo espacios
    return bool(texto and texto.strip())

def validar_opciones_encuesta(opciones):
    # Deben ser al menos 2 opciones y no vacías
    return isinstance(opciones, list) and len(opciones) >= 2 and all(o.strip() for o in opciones)
