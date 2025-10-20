# test_encuesta.py - Prueba unitaria para el handler de encuesta
import unittest
from src.handlers.encuesta import crear_encuesta, procesar_voto

class TestEncuesta(unittest.TestCase):
    def test_crear_encuesta(self):
        resultado = crear_encuesta("¿Te gusta Python?", ["Sí", "No"])
        self.assertEqual(resultado["type"], "survey")
        self.assertEqual(resultado["text"], "¿Te gusta Python?")
        self.assertEqual(resultado["options"], ["Sí", "No"])
    def test_procesar_voto(self):
        resultado = procesar_voto("juan", "Sí")
        self.assertIn("Voto registrado", resultado["text"])
        self.assertEqual(resultado["type"], "reply")

if __name__ == "__main__":
    unittest.main()
