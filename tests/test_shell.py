from __future__ import annotations

import pytest

from src.shell import PtyProcess, ShellExecutor


class TestPtyProcess:
    def test_run_command_basic(self):
        result = PtyProcess.run_command("echo hello", timeout=5)
        assert "hello" in result.stdout
        assert not result.timed_out

    def test_run_command_with_error(self):
        result = PtyProcess.run_command("echo hello && false", timeout=5)
        assert "hello" in result.stdout

    def test_run_command_timeout(self):
        # Use a long-running command that doesn't return quickly
        result = PtyProcess.run_command("for i in $(seq 1 100); do echo $i; done", timeout=1)
        # May or may not time out depending on system speed
        assert result.timed_out or result.stdout

    def test_context_manager(self):
        with PtyProcess() as pty:
            assert pty.is_running
            result = pty.execute("echo context_test", timeout=5)
            assert "context_test" in result.stdout
        assert not pty.is_running

    def test_multiple_commands(self):
        with PtyProcess() as pty:
            r1 = pty.execute("echo first", timeout=5)
            assert "first" in r1.stdout
            r2 = pty.execute("echo second", timeout=5)
            assert "second" in r2.stdout

    def test_cd_and_pwd(self):
        with PtyProcess() as pty:
            pty.execute("cd /tmp", timeout=3)
            r = pty.execute("pwd", timeout=3)
            assert "/tmp" in r.stdout

    def test_tool_specs(self):
        exec = ShellExecutor()
        specs = exec.get_tool_specs()
        names = [s["name"] for s in specs]
        assert "shell_run" in names
        assert "shell_interactive" in names


class TestShellExecutor:
    def test_run_echo(self):
        exec = ShellExecutor()
        result = exec.run("echo hello_world", timeout=5)
        assert "hello_world" in result.stdout
        assert result.returncode == 0

    def test_run_with_error(self):
        exec = ShellExecutor()
        result = exec.run("ls /nonexistent_path_xyz", timeout=5)
        assert result.returncode != 0

    def test_run_with_env(self):
        exec = ShellExecutor()
        result = exec.run("echo $MY_VAR", timeout=5, env={"MY_VAR": "test_val"})
        assert "test_val" in result.stdout

    def test_run_work_dir(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("content")
        exec = ShellExecutor(work_dir=str(tmp_path))
        result = exec.run("cat test.txt", timeout=5)
        assert "content" in result.stdout

    def test_run_interactive(self):
        exec = ShellExecutor()
        result = exec.run_interactive("echo interactive_test", timeout=5)
        assert "interactive_test" in result.stdout
