from __future__ import annotations
from typing import Dict, List
from collections import Counter
from math import log, exp
from .tokenizer import tokenize

class NaiveBayesText:
    def __init__(self, prior: Dict[str,float], likelihood: Dict[str,Dict[str,int]], vocab_size: int) -> None:
        self.prior = prior
        self.likelihood = likelihood
        self.vocab_size = vocab_size
        self.class_totals = {c: sum(cnt.values()) for c, cnt in likelihood.items()}

    def score(self, text: str) -> Dict[str, float]:
        toks = tokenize(text)
        logps: Dict[str, float] = {}
        # Log-posteriors proporcionales (sin normalizar) por clase
        for c, p in self.prior.items():
            logp = log(max(p, 1e-9))
            denom = self.class_totals.get(c, 0) + self.vocab_size
            denom = max(denom, 1)
            for tok in toks:
                count = self.likelihood.get(c, {}).get(tok, 0)
                # Laplace smoothing
                logp += log((count + 1) / denom)
            logps[c] = logp
        # Softmax para obtener distribución de probabilidad entre clases vistas
        if not logps:
            return {"toxic": 0.0, "spam": 0.0}
        max_lp = max(logps.values())
        exps = {c: exp(lp - max_lp) for c, lp in logps.items()}
        z = sum(exps.values()) or 1.0
        probs = {c: float(v / z) for c, v in exps.items()}
        # Asegurar claves esperadas
        for k in ("toxic", "spam"):
            probs.setdefault(k, 0.0)
        return probs

    @staticmethod
    def train(examples: Dict[str,List[str]]) -> "NaiveBayesText":
        tokenized = {c: [tokenize(t) for t in texts] for c, texts in examples.items()}
        total_docs = sum(len(v) for v in examples.values()) or 1
        priors: Dict[str,float] = {c: max(1e-9, len(texts)/total_docs) for c, texts in examples.items()}
        likelihood: Dict[str,Dict[str,int]] = {}
        vocab = set()
        for c, docs in tokenized.items():
            cnt = Counter()
            for doc in docs:
                cnt.update(doc)
                vocab.update(doc)
            likelihood[c] = dict(cnt)
        return NaiveBayesText(priors, likelihood, len(vocab) or 1)
