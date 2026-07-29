from __future__ import annotations

import pytest

from src.context import SystemContextBuilder, SystemContext


class TestSystemContext:
    def test_default_fields(self):
        builder = SystemContextBuilder()
        ctx = builder.build()
        assert ctx.os_info
        assert ctx.python_version
        assert ctx.working_directory
        assert ctx.environment
        assert ctx.current_time

    def test_tools_and_capabilities(self):
        builder = SystemContextBuilder()
        ctx = builder.build(tool_names=["read_file", "write_file"], capabilities=["vision", "audio"])
        assert "read_file" in ctx.tools_available
        assert "vision" in ctx.capabilities

    def test_custom_provider(self):
        builder = SystemContextBuilder()
        builder.register("my_provider", lambda: {"key": "value"})
        ctx = builder.build()
        assert ctx.custom["my_provider"]["key"] == "value"

    def test_provider_exception(self):
        builder = SystemContextBuilder()

        def broken():
            raise RuntimeError("fail")

        builder.register("broken", broken)
        ctx = builder.build()
        assert "error" in ctx.custom["broken"]

    def test_to_prompt(self):
        builder = SystemContextBuilder()
        ctx = builder.build(tool_names=["tool1"])
        prompt = ctx.to_prompt()
        assert "## System Context" in prompt
        assert "tool1" in prompt
        assert ctx.os_info in prompt
