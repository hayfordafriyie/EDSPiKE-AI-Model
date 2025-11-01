from __future__ import annotations

import ast
import math
import re
from collections import Counter


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


class EvaluationMetrics:
    @staticmethod
    def exact_match(predictions: list[str], references: list[str]) -> float:
        if not predictions:
            return 0.0
        return sum(p.strip().casefold() == r.strip().casefold() for p, r in zip(predictions, references)) / len(predictions)

    @staticmethod
    def token_f1(predictions: list[str], references: list[str]) -> float:
        scores = []
        for pred, ref in zip(predictions, references):
            common = Counter(_tokens(pred)) & Counter(_tokens(ref))
            overlap = sum(common.values())
            if not pred and not ref:
                scores.append(1.0)
                continue
            precision = overlap / max(len(_tokens(pred)), 1)
            recall = overlap / max(len(_tokens(ref)), 1)
            scores.append(2 * precision * recall / max(precision + recall, 1e-12))
        return sum(scores) / len(scores) if scores else 0.0

    @staticmethod
    def perplexity(loss: float) -> float:
        return math.exp(min(loss, 20))

    @staticmethod
    def education_specific(predictions: list[str]) -> dict[str, float]:
        terms = {"waec", "ges", "curriculum", "assessment", "learning outcome"}
        aligned = sum(any(term in pred.lower() for term in terms) for pred in predictions)
        code = [pred for pred in predictions if "def " in pred or "class " in pred]
        valid = 0
        for value in code:
            try:
                ast.parse(value)
                valid += 1
            except SyntaxError:
                pass
        return {
            "curriculum_alignment": aligned / len(predictions) if predictions else 0.0,
            "code_syntax_accuracy": valid / len(code) if code else 0.0,
        }

