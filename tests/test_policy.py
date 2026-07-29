from __future__ import annotations

import pytest

from src.policy import PolicyEngine, Policy, PolicyDecision


class TestPolicy:
    def test_default_allow(self):
        engine = PolicyEngine()
        decision, reason = engine.evaluate("read_file", "/tmp/test.txt")
        assert decision == PolicyDecision.ALLOW

    def test_deny_policy(self):
        engine = PolicyEngine()
        engine.add(Policy(
            name="no-write-etc",
            action_pattern=r"write_.*",
            resource_pattern=r"/etc/.*",
            decision=PolicyDecision.DENY,
            priority=10,
        ))
        decision, _ = engine.evaluate("write_file", "/etc/passwd")
        assert decision == PolicyDecision.DENY

    def test_allow_overrides_deny_by_priority(self):
        engine = PolicyEngine()
        engine.add(Policy(name="deny-all", action_pattern=r".*", resource_pattern=r".*",
                          decision=PolicyDecision.DENY, priority=0))
        engine.add(Policy(name="allow-tmp", action_pattern=r".*", resource_pattern=r"/tmp/.*",
                          decision=PolicyDecision.ALLOW, priority=10))
        assert engine.can("read_file", "/tmp/x.txt") is True
        assert engine.can("read_file", "/etc/x.txt") is False

    def test_ask_decision(self):
        engine = PolicyEngine()
        engine.add(Policy(name="ask-bash", action_pattern=r"bash", resource_pattern=r".*",
                          decision=PolicyDecision.ASK, priority=5))
        decision, _ = engine.evaluate("bash", "rm -rf /")
        assert decision == PolicyDecision.ASK

    def test_policy_pattern_match(self):
        engine = PolicyEngine()
        engine.add(Policy(name="no-shell", action_pattern=r"shell_.*", resource_pattern=r".*",
                          decision=PolicyDecision.DENY, priority=5))
        assert engine.can("shell_run", "echo hi") is False
        assert engine.can("read_file", "test.txt") is True

    def test_custom_check(self):
        engine = PolicyEngine()
        def block_secret(action, resource, ctx):
            if "secret" in resource.lower():
                return PolicyDecision.DENY
            return None
        engine.add_check(block_secret)
        assert engine.can("read_file", "secret.txt") is False
        assert engine.can("read_file", "public.txt") is True

    def test_list_policies(self):
        engine = PolicyEngine()
        engine.add(Policy(name="p1", action_pattern=r".*", resource_pattern=r".*",
                          decision=PolicyDecision.DENY, reason="test policy"))
        policies = engine.list_policies()
        assert len(policies) == 1
        assert policies[0]["name"] == "p1"

    def test_clear(self):
        engine = PolicyEngine()
        engine.add(Policy(name="p", action_pattern=r".*", resource_pattern=r".*",
                          decision=PolicyDecision.DENY))
        engine.clear()
        assert engine.can("anything", "anywhere") is True
