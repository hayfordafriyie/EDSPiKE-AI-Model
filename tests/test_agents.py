from __future__ import annotations

import pytest

from src.agents.definitions import AGENT_DEFINITIONS, get_agent, list_agents
from src.agents.worker import get_default_profiles, build_agent_prompt, run_workers
from src.agents.orchestrator import build_judge_prompt, judge


class TestDefinitions:
    def test_all_agents_defined(self):
        assert "default" in AGENT_DEFINITIONS
        assert "coding" in AGENT_DEFINITIONS
        assert "analytical" in AGENT_DEFINITIONS
        assert "creative" in AGENT_DEFINITIONS
        assert "technical" in AGENT_DEFINITIONS
        assert "visual" in AGENT_DEFINITIONS
        assert "auditory" in AGENT_DEFINITIONS

    def test_get_agent(self):
        agent = get_agent("coding")
        assert agent.id == "coding"
        assert agent.name == "Software Engineer"
        assert agent.tools_enabled is True
        assert agent.system_prompt

    def test_get_agent_unknown(self):
        with pytest.raises(KeyError, match="Unknown agent"):
            get_agent("nonexistent")

    def test_list_agents(self):
        agents = list_agents()
        assert len(agents) >= 7
        ids = {a["id"] for a in agents}
        assert "default" in ids
        assert "coding" in ids

    def test_agent_has_required_fields(self):
        for agent in AGENT_DEFINITIONS.values():
            assert agent.id
            assert agent.name
            assert agent.system_prompt
            assert 0 < agent.temperature <= 1
            assert 0 < agent.top_p <= 1
            assert agent.max_tokens > 0


class TestWorker:
    def test_get_default_profiles(self):
        profiles = get_default_profiles()
        assert len(profiles) == len(AGENT_DEFINITIONS)
        names = {p["name"] for p in profiles}
        assert "Default Assistant" in names
        assert "Software Engineer" in names

    def test_profile_has_tools_enabled(self):
        profiles = get_default_profiles()
        coding = next(p for p in profiles if p["name"] == "Software Engineer")
        assert coding["tools_enabled"] is True
        default = next(p for p in profiles if p["name"] == "Default Assistant")
        assert default["tools_enabled"] is False

    def test_build_agent_prompt(self):
        profile = {"name": "Test", "system": "You are a test.", "temperature": 0.5, "top_p": 0.9}
        prompt = build_agent_prompt(profile, "What is 2+2?")
        assert "You are a test." in prompt
        assert "What is 2+2?" in prompt
        assert prompt.endswith("Answer:")

    def test_build_agent_prompt_with_modality(self):
        profile = {"name": "Test", "system": "You are a test.", "temperature": 0.5, "top_p": 0.9}
        prompt = build_agent_prompt(profile, "What is this?", modality_context="Image shows a cat.")
        assert "Image shows a cat." in prompt

    def test_run_workers(self):
        def fake_gen(prompts, max_tokens, temperature, top_p):
            return [f"Answer from {p[:20]}" for p in prompts], [10] * len(prompts)

        profiles = [
            {"name": "A", "system": "You are A.", "temperature": 0.3, "top_p": 0.9},
            {"name": "B", "system": "You are B.", "temperature": 0.5, "top_p": 0.9},
        ]
        results = run_workers(fake_gen, "test question", profiles=profiles, max_workers=2)
        assert len(results) == 2
        assert results[0]["agent"] == "A" or results[0]["agent"] == "B"
        assert results[0]["answer"].startswith("Answer from")
        assert results[0]["tokens"] == 10

    def test_run_workers_handles_error(self):
        def broken_gen(prompts, max_tokens, temperature, top_p):
            raise RuntimeError("fail")

        profiles = [{"name": "X", "system": "You are X.", "temperature": 0.3, "top_p": 0.9}]
        results = run_workers(broken_gen, "q", profiles=profiles)
        assert len(results) == 1
        assert "[Agent error:" in results[0]["answer"]


class TestOrchestrator:
    def test_build_judge_prompt(self):
        answers = [
            {"agent": "A", "answer": "42", "temperature": 0.3, "tokens": 5},
            {"agent": "B", "answer": "43", "temperature": 0.5, "tokens": 5},
        ]
        prompt = build_judge_prompt("What is 2+2?", answers)
        assert "What is 2+2?" in prompt
        assert "Agent: A" in prompt
        assert "Agent: B" in prompt

    def test_judge_parses_json(self):
        def fake_gen(prompts, max_tokens, temperature, top_p):
            result = '{"best_agent": "A", "reasoning": "Correct", "final_answer": "42", "runner_up": "B"}'
            return [result], [20]

        answers = [{"agent": "A", "answer": "42", "temperature": 0.3, "tokens": 5}]
        verdict = judge(fake_gen, "What is 2+2?", answers)
        assert verdict["best_agent"] == "A"
        assert verdict["final_answer"] == "42"

    def test_judge_fallback_on_bad_json(self):
        def fake_gen(prompts, max_tokens, temperature, top_p):
            return ["not json at all"], [20]

        answers = [{"agent": "A", "answer": "42", "temperature": 0.3, "tokens": 5}]
        verdict = judge(fake_gen, "What is 2+2?", answers)
        assert verdict["best_agent"] == "unknown"
        assert verdict["final_answer"] == "42"
