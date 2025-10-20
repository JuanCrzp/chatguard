# sorteo.py - Handler para sorteos y dinámicas
import random

def realizar_sorteo(participantes):
    ganador = random.choice(participantes)
    return {
        "text": f"¡Felicidades @{ganador}, has ganado el sorteo!",
        "type": "raffle"
    }
