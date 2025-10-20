# test_sorteo.py - Prueba unitaria para el handler de sorteo
import unittest
from src.handlers.sorteo import realizar_sorteo

class TestSorteo(unittest.TestCase):
    def test_realizar_sorteo(self):
        participantes = ["juan", "ana", "pedro"]
        resultado = realizar_sorteo(participantes)
        self.assertEqual(resultado["type"], "raffle")
        self.assertTrue(any(p in resultado["text"] for p in participantes))

if __name__ == "__main__":
    unittest.main()
