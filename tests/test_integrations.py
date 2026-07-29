from __future__ import annotations

import pytest

from src.integrations import IntegrationFramework, Integration


class TestIntegrations:
    def test_register_and_execute(self):
        framework = IntegrationFramework()
        slack = Integration(
            name="slack",
            actions={"send_message": lambda channel, text: f"Sent to {channel}: {text}"},
        )
        framework.register(slack)
        result = framework.execute("slack", "send_message", channel="#general", text="hello")
        assert result == "Sent to #general: hello"

    def test_execute_unknown_integration(self):
        framework = IntegrationFramework()
        with pytest.raises(KeyError, match="not found"):
            framework.execute("nonexistent", "action")

    def test_execute_unknown_action(self):
        framework = IntegrationFramework()
        framework.register(Integration(name="test", actions={"existing": lambda: "ok"}))
        with pytest.raises(KeyError, match="not found"):
            framework.execute("test", "nonexistent")

    def test_list(self):
        framework = IntegrationFramework()
        framework.register(Integration(name="github", description="GitHub API"))
        framework.register(Integration(name="slack", description="Slack messaging"))
        integrations = framework.list()
        assert len(integrations) == 2
        names = [i["name"] for i in integrations]
        assert "github" in names
        assert "slack" in names

    def test_unregister(self):
        framework = IntegrationFramework()
        framework.register(Integration(name="temp"))
        assert framework.unregister("temp") is True
        assert framework.unregister("temp") is False

    def test_get(self):
        framework = IntegrationFramework()
        integration = Integration(name="test")
        framework.register(integration)
        assert framework.get("test") is integration
        assert framework.get("nonexistent") is None
