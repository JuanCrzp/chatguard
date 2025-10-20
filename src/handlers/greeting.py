"""Handler de saludo genérico."""

from typing import Optional


def handle_greeting(name: Optional[str] = None) -> str:
    if name:
        return f"¡Hola {name}! ¿En qué puedo ayudarte hoy?"
    return "¡Hola! ¿En qué puedo ayudarte hoy?"
