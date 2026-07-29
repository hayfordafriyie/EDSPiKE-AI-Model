from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class SkillResult:
    skill_name: str
    score: float = 0.0
    passed: bool = False
    details: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


EvalFn = Callable[[dict[str, Any]], SkillResult]


class SkillEvaluator:
    def __init__(self):
        self._skills: dict[str, EvalFn] = {}

    def register(self, name: str, fn: EvalFn) -> None:
        self._skills[name] = fn

    def evaluate(self, name: str, input_data: dict[str, Any]) -> SkillResult:
        fn = self._skills.get(name)
        if not fn:
            return SkillResult(skill_name=name, passed=False, details=f"Unknown skill: {name}", errors=[f"No evaluator registered for '{name}'"])
        try:
            result = fn(input_data)
            return result
        except Exception as exc:
            logger.error("Skill %s evaluation failed: %s", name, exc)
            return SkillResult(skill_name=name, passed=False, details=str(exc), errors=[str(exc)])

    def evaluate_all(self, input_data: dict[str, Any]) -> list[SkillResult]:
        return [self.evaluate(name, input_data) for name in self._skills]

    def list_skills(self) -> list[dict[str, Any]]:
        return [{"name": name, "registered": True} for name in self._skills]

    @staticmethod
    def accuracy_score(correct: int, total: int) -> float:
        return correct / total if total > 0 else 0.0

    @staticmethod
    def f1_score(precision: float, recall: float) -> float:
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
