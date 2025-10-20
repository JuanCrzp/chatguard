# test_bienvenida.py - Prueba unitaria para el handler de bienvenida
import unittest
from src.handlers.bienvenida import enviar_bienvenida

class TestBienvenida(unittest.TestCase):
    def test_enviar_bienvenida(self):
        resultado = enviar_bienvenida("Juan", "Pythonistas")
        self.assertIn("Bienvenido/a Juan al grupo Pythonistas", resultado["text"])
        self.assertEqual(resultado["type"], "reply")

if __name__ == "__main__":
    unittest.main()
