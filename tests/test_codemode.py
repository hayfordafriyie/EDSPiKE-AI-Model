from __future__ import annotations

import pytest

from src.codemode import Sandbox, CodeExecutor, PluginRegistry, PluginHook, PluginContext


class TestSandbox:
    def test_write_and_read(self):
        with Sandbox() as sb:
            sb.write_file("test.txt", "hello world")
            assert sb.read_file("test.txt") == "hello world"

    def test_execute_python(self):
        with Sandbox() as sb:
            result = sb.execute(["python3", "-c", "print(42)"])
            assert result.stdout.strip() == "42"
            assert result.exit_code == 0
            assert not result.timed_out

    def test_execute_with_stdin(self):
        with Sandbox() as sb:
            result = sb.execute(["python3", "-c", "import sys; print(sys.stdin.read().strip())"], stdin="hello")
            assert result.stdout.strip() == "hello"

    def test_execute_timeout(self):
        with Sandbox() as sb:
            result = sb.execute(["python3", "-c", "import time; time.sleep(10)"], timeout=1)
            assert result.timed_out

    def test_execute_failure(self):
        with Sandbox() as sb:
            result = sb.execute(["python3", "-c", "raise RuntimeError('boom')"])
            assert "RuntimeError" in result.stderr
            assert result.exit_code != 0


class TestCodeExecutor:
    def test_execute_python(self):
        exec = CodeExecutor()
        result = exec.execute("print('hello')", language="python")
        assert result.stdout.strip() == "hello"
        assert result.exit_code == 0

    def test_execute_bash(self):
        exec = CodeExecutor()
        result = exec.execute("echo hello", language="bash")
        assert result.stdout.strip() == "hello"
        assert result.exit_code == 0

    def test_execute_with_error(self):
        exec = CodeExecutor()
        result = exec.execute("import sys; sys.exit(1)", language="python")
        assert result.exit_code == 1

    def test_execute_timeout(self):
        exec = CodeExecutor()
        result = exec.execute("import time; time.sleep(10)", language="python", timeout=1)
        assert result.timed_out

    def test_execute_unsupported_language(self):
        exec = CodeExecutor()
        with pytest.raises(KeyError):
            exec.execute("code", language="nonexistent")

    def test_execution_id_unique(self):
        exec = CodeExecutor()
        r1 = exec.execute("print(1)", language="python")
        r2 = exec.execute("print(2)", language="python")
        assert r1.id != r2.id


class TestPluginRegistry:
    def test_register_and_run(self):
        registry = PluginRegistry()
        calls = []

        def pre(ctx):
            calls.append("pre")
            ctx.metadata["x"] = 1
            return ctx

        registry.register(PluginHook.PRE_EXEC, pre)
        ctx = PluginContext(code="test", language="python")
        result = registry.run(PluginHook.PRE_EXEC, ctx)
        assert calls == ["pre"]
        assert result.metadata["x"] == 1

    def test_unregister(self):
        registry = PluginRegistry()
        calls = []

        def pre(ctx):
            calls.append("pre")
            return ctx

        registry.register(PluginHook.PRE_EXEC, pre)
        registry.unregister(PluginHook.PRE_EXEC, pre)
        registry.run(PluginHook.PRE_EXEC, PluginContext())
        assert calls == []

    def test_validate_blocking(self):
        from src.codemode.plugins import get_plugin_registry
        registry = get_plugin_registry()

        def validator(ctx):
            if "dangerous" in ctx.code:
                ctx.errors.append("Blocked by security policy")
            return ctx

        registry.register(PluginHook.VALIDATE, validator)
        try:
            exec = CodeExecutor()
            result = exec.execute("dangerous code", language="python")
            assert result.errors == ["Blocked by security policy"]
            assert result.exit_code == -1
        finally:
            registry.unregister(PluginHook.VALIDATE, validator)

    def test_code_plugin_decorator(self):
        from src.codemode import code_plugin
        from src.codemode.plugins import get_plugin_registry

        calls = []

        @code_plugin(PluginHook.POST_EXEC)
        def my_plugin(ctx):
            calls.append("ran")
            return ctx

        try:
            exec = CodeExecutor()
            exec.execute("print(1)", language="python")
            assert "ran" in calls
        finally:
            get_plugin_registry().unregister(PluginHook.POST_EXEC, my_plugin)

    def test_hook_all_have_lists(self):
        registry = PluginRegistry()
        for hook in PluginHook:
            assert hook in registry._hooks
            assert registry._hooks[hook] == []

    def test_clear(self):
        registry = PluginRegistry()

        def noop(ctx):
            return ctx

        registry.register(PluginHook.PRE_EXEC, noop)
        registry.register(PluginHook.POST_EXEC, noop)
        registry.clear()
        for hook in PluginHook:
            assert registry._hooks[hook] == []
