from __future__ import annotations
from typing import Dict, Any, Tuple
from .nb_text import NaiveBayesText

# Memoización manual de modelos por (chat_id, firma_entrenamiento)
_MODEL_CACHE: Dict[Tuple[str, Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]], 'Scorer'] = {}

def get_training_from_config(ml_cfg: dict) -> dict:
    training = (ml_cfg.get("training") or {})
    # Asegura claves y listas
    return {
        "toxic": list(training.get("toxic", [])),
        "spam": list(training.get("spam", [])),
        "normal": list(training.get("normal", [])),
    }

def _training_signature(ml_cfg: dict) -> Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]:
    tr = get_training_from_config(ml_cfg)
    # Firma estable: tuplas ordenadas (lowercase/strip) para toxic y spam
    tox = tuple(sorted(s.strip().lower() for s in tr.get("toxic", [])))
    spm = tuple(sorted(s.strip().lower() for s in tr.get("spam", [])))
    nor = tuple(sorted(s.strip().lower() for s in tr.get("normal", [])))
    return tox, spm, nor


def get_moderation_scorer(chat_id: str, ml_cfg: dict) -> 'Scorer':
    sig = _training_signature(ml_cfg)
    key = (str(chat_id), sig[0], sig[1], sig[2])
    scorer = _MODEL_CACHE.get(key)
    if scorer is None:
        training = {"toxic": list(sig[0]), "spam": list(sig[1]), "normal": list(sig[2])}
        model = NaiveBayesText.train(training)
        scorer = Scorer(model)
        _MODEL_CACHE[key] = scorer
    return scorer

class Scorer:
    def __init__(self, model: NaiveBayesText) -> None:
        self.model = model
    def score(self, text: str) -> Dict[str, float]:
        s = self.model.score(text)
        return {"toxic": float(s.get("toxic", 0.0)), "spam": float(s.get("spam", 0.0))}
