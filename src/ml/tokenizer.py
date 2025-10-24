import re
import unicodedata
from typing import List

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[\.,!\?;:\-_/\\\(\)\[\]\{\}\*\"']+")

STOPWORDS = {"el","la","los","las","un","una","de","del","y","o","u","a","en","que","por","para","con","se","es","lo","al","como","no","si","su","sus","mi","mis","tu","tus"}

def normalize(text: str) -> str:
    t = text.lower()
    # Quitar acentos/diacríticos para alinear variaciones (rápido -> rapido)
    t = unicodedata.normalize('NFD', t)
    t = ''.join(ch for ch in t if unicodedata.category(ch) != 'Mn')
    t = _PUNCT.sub(" ", t)
    t = _WS.sub(" ", t).strip()
    return t


def tokenize(text: str) -> List[str]:
    t = normalize(text)
    return [tok for tok in t.split(" ") if tok and tok not in STOPWORDS]
