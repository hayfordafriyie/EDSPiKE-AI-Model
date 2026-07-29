from __future__ import annotations

import pytest

from src.agent import Plan, Step, StepStatus, AgentState, Planner, AgentLoop
from src.agent.types import Step as StepType
from src.agent.planner import PLANNER_PROMPT


class TestTypes:
    def test_step_default_status(self):
        s = Step(index=1, description="test", action="doit")
        assert s.status == StepStatus.PENDING

    def test_plan_creation(self):
        p = Plan(goal="test goal")
        assert p.goal == "test goal"
        assert p.steps == []
        assert p.current_step == 0

    def test_agent_state_defaults(self):
        s = AgentState()
        assert s.plan.goal == ""
        assert s.messages == []
        assert s.total_tokens == 0
        assert s.finished is False
        assert s.final_answer == ""

    def test_step_status_enum(self):
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.COMPLETED.value == "completed"
        assert StepStatus.FAILED.value == "failed"


class TestPlanner:
    def test_create_plan(self):
        def fake_gen(prompts, max_tokens, temperature, top_p):
            result = '{"goal": "add feature", "steps": [{"index": 1, "description": "read code", "action": "read_file"}, {"index": 2, "description": "edit code", "action": "edit_file"}]}'
            return [result], [50]

        planner = Planner(fake_gen)
        plan = planner.create_plan("add a feature")
        assert plan.goal == "add feature"
        assert len(plan.steps) == 2
        assert plan.steps[0].action == "read_file"
        assert plan.steps[1].action == "edit_file"

    def test_create_plan_fallback(self):
        def fake_gen(prompts, max_tokens, temperature, top_p):
            return ["invalid json"], [10]

        planner = Planner(fake_gen)
        plan = planner.create_plan("do something")
        assert plan.goal == "do something"
        assert len(plan.steps) >= 1

    def test_revise_plan(self):
        def fake_gen(prompts, max_tokens, temperature, top_p):
            result = '{"goal": "fix bug", "steps": [{"index": 1, "description": "read logs", "action": "read_file"}, {"index": 2, "description": "fix code", "action": "edit_file"}]}'
            return [result], [50]

        planner = Planner(fake_gen)
        plan = Plan(goal="fix bug", steps=[
            Step(index=1, description="old step", action="old", status=StepStatus.FAILED, error="error"),
        ])
        revised = planner.revise_plan(plan, "old step failed, try different approach")
        assert len(revised.steps) >= 1

    def test_revise_plan_bad_json(self):
        def fake_gen(prompts, max_tokens, temperature, top_p):
            return ["not json"], [10]

        planner = Planner(fake_gen)
        plan = Plan(goal="test", steps=[Step(index=1, description="s1", action="a1")])
        revised = planner.revise_plan(plan, "feedback")
        assert revised is plan


class TestAgentLoop:
    def test_extract_answer(self):
        assert AgentLoop._extract_answer("Task complete: done") == "done"
        assert AgentLoop._extract_answer("Step completed: step1 done") == "step1 done"
        assert AgentLoop._extract_answer("Final answer: 42") == "42"
        assert AgentLoop._extract_answer("no prefix") == "no prefix"

    def test_run_completes(self):
        def fake_gen(prompts, max_tokens, temperature, top_p):
            return ["all done here"], [10]

        def fake_plan(task, context=""):
            return Plan(goal=task, steps=[
                Step(index=1, description="step1", action="think"),
            ])

        class FakePlanner:
            create_plan = fake_plan
            revise_plan = lambda self, p, f: p

        loop = AgentLoop(generate_fn=fake_gen, planner=FakePlanner())
        state = loop.run("test task", max_tokens=100)
        assert state.finished is True
        assert state.total_tokens >= 0

    def test_run_with_tool_calls(self):
        tool_responses = iter([
            '<tool_call>\n{"name": "glob", "arguments": {"pattern": "*.py"}}\n</tool_call>',
            'Task complete: found files',
        ])

        def fake_gen(prompts, max_tokens, temperature, top_p):
            return [next(tool_responses)], [10]

        def fake_plan(task, context=""):
            return Plan(goal=task, steps=[
                Step(index=1, description="find files", action="glob"),
            ])

        class FakePlanner:
            create_plan = fake_plan
            revise_plan = lambda self, p, f: p

        loop = AgentLoop(generate_fn=fake_gen, planner=FakePlanner())
        state = loop.run("find python files", max_tokens=200)
        assert state.finished is True

    def test_run_with_failed_tool(self):
        tool_responses = iter([
            '<tool_call>\n{"name": "read_file", "arguments": {"path": "/nonexistent"}}\n</tool_call>',
            'Task complete: done',
        ])

        def fake_gen(prompts, max_tokens, temperature, top_p):
            return [next(tool_responses)], [10]

        call_count = 0

        def fake_plan(task, context=""):
            return Plan(goal=task, steps=[
                Step(index=1, description="read", action="read_file"),
            ])

        class FakePlanner:
            create_plan = fake_plan
            def revise_plan(self, plan, feedback):
                return plan

        loop = AgentLoop(generate_fn=fake_gen, planner=FakePlanner())
        state = loop.run("test", max_tokens=200)
        assert state.finished is True
