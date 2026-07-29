import tempfile
from pathlib import Path

import pytest

from src.goal import GoalMode, GoalBudgetLimits


class TestGoalMode:
    @pytest.fixture
    def gm(self, tmp_path: Path):
        return GoalMode(str(tmp_path / "goals"))

    def test_create_goal(self, gm: GoalMode):
        snap = gm.create_goal("Fix the login bug")
        assert snap.objective == "Fix the login bug"
        assert snap.status == "active"
        assert snap.goal_id

    def test_create_goal_empty(self, gm: GoalMode):
        with pytest.raises(ValueError, match="cannot be empty"):
            gm.create_goal("")

    def test_create_goal_replace(self, gm: GoalMode):
        gm.create_goal("First goal")
        with pytest.raises(ValueError, match="already exists"):
            gm.create_goal("Second goal")
        snap = gm.create_goal("Second goal", replace=True)
        assert snap.objective == "Second goal"

    def test_get_goal(self, gm: GoalMode):
        assert gm.get_goal() is None
        gm.create_goal("Test")
        assert gm.get_goal() is not None

    def test_get_active_goal(self, gm: GoalMode):
        assert gm.get_active_goal() is None
        gm.create_goal("Test")
        assert gm.get_active_goal() is not None
        gm.pause_goal()
        assert gm.get_active_goal() is None

    def test_pause_and_resume_goal(self, gm: GoalMode):
        gm.create_goal("Test")
        snap = gm.pause_goal("Need more info")
        assert snap.status == "paused"
        assert snap.terminal_reason == "Need more info"
        snap = gm.resume_goal()
        assert snap.status == "active"

    def test_cancel_goal(self, gm: GoalMode):
        gm.create_goal("Test")
        snap = gm.cancel_goal()
        assert snap is not None
        assert gm.get_goal() is None

    def test_mark_blocked(self, gm: GoalMode):
        gm.create_goal("Test")
        snap = gm.mark_blocked("Cannot proceed")
        assert snap is not None
        assert snap.status == "blocked"

    def test_mark_complete(self, gm: GoalMode):
        gm.create_goal("Test")
        snap = gm.mark_complete("Done")
        assert snap is not None
        assert snap.status == "complete"
        assert gm.get_goal() is None

    def test_record_token_usage(self, gm: GoalMode):
        gm.create_goal("Test")
        snap = gm.record_token_usage(150)
        assert snap is not None
        assert snap.tokens_used == 150
        snap = gm.record_token_usage(50)
        assert snap.tokens_used == 200

    def test_increment_turn(self, gm: GoalMode):
        gm.create_goal("Test")
        snap = gm.increment_turn()
        assert snap is not None
        assert snap.turns_used == 1

    def test_budget_limits(self, gm: GoalMode):
        gm.create_goal("Test")
        gm.set_budget_limits(GoalBudgetLimits(turn_budget=5, token_budget=1000))
        report = gm.get_budget_report()
        assert report.turn_budget == 5
        assert report.token_budget == 1000
        assert report.remaining_turns == 5

    def test_budget_exhausted(self, gm: GoalMode):
        gm.create_goal("Test")
        gm.set_budget_limits(GoalBudgetLimits(turn_budget=2))
        gm.increment_turn()
        gm.increment_turn()
        report = gm.get_budget_report()
        assert report.turn_budget_reached is True
        assert report.over_budget is True

    def test_persistence(self, tmp_path: Path):
        data_dir = str(tmp_path / "goals")
        gm1 = GoalMode(data_dir)
        gm1.create_goal("Persistent goal")
        gm2 = GoalMode(data_dir)
        snap = gm2.get_goal()
        assert snap is not None
        assert snap.objective == "Persistent goal"
        assert snap.status == "paused"
