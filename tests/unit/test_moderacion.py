# test_moderacion.py - Prueba unitaria para el handler de moderación
import unittest
from src.handlers.moderacion import revisar_mensaje

class TestModeracion(unittest.TestCase):
    def test_mensaje_permitido(self):
        resultado = revisar_mensaje("Hola a todos", "juan")
        self.assertIsNone(resultado)
    def test_mensaje_prohibido(self):
        resultado = revisar_mensaje("Esto es spam", "juan")
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.get("type"), "moderation")
        # Puede ser delete/warn/mute/kick/ban según thresholds; verificar claves base
        self.assertIn(resultado.get("action", "warn"), ["delete", "warn", "mute", "kick", "ban"])

if __name__ == "__main__":
    unittest.main()
