from __future__ import annotations

import pytest

from src.skills import SkillEvaluator, SkillResult


class TestSkills:
    def test_register_and_evaluate(self):
        ev = SkillEvaluator()
        ev.register("math", lambda d: SkillResult("math", score=1.0, passed=True, details="2+2=4"))
        result = ev.evaluate("math", {"question": "2+2"})
        assert result.passed is True
        assert result.score == 1.0

    def test_unknown_skill(self):
        ev = SkillEvaluator()
        result = ev.evaluate("nonexistent", {})
        assert result.passed is False
        assert "Unknown" in result.details

    def test_evaluate_all(self):
        ev = SkillEvaluator()
        ev.register("a", lambda d: SkillResult("a", passed=True))
        ev.register("b", lambda d: SkillResult("b", passed=True))
        results = ev.evaluate_all({})
        assert len(results) == 2

    def test_list_skills(self):
        ev = SkillEvaluator()
        ev.register("x", lambda d: SkillResult("x"))
        skills = ev.list_skills()
        assert len(skills) == 1
        assert skills[0]["name"] == "x"

    def test_accuracy_score(self):
        assert SkillEvaluator.accuracy_score(3, 4) == 0.75
        assert SkillEvaluator.accuracy_score(0, 0) == 0.0

    def test_f1_score(self):
        assert SkillEvaluator.f1_score(1.0, 1.0) == 1.0
        assert SkillEvaluator.f1_score(0.0, 1.0) == 0.0
        assert abs(SkillEvaluator.f1_score(0.8, 0.6) - 0.6857) < 0.01

    def test_handler_exception(self):
        ev = SkillEvaluator()

        def broken(d):
            raise RuntimeError("eval crash")

        ev.register("broken", broken)
        result = ev.evaluate("broken", {})
        assert result.passed is False
