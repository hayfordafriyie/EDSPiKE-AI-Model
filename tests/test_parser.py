import pytest

from src.parser import parse_bash, is_dangerous_command, extract_git_commands


class TestParser:
    def test_simple_command(self):
        result = parse_bash("echo hello")
        assert result.ok
        assert "echo" in result.commands

    def test_pipe_detection(self):
        result = parse_bash("cat file | grep pattern")
        assert result.has_pipe
        assert "cat" in result.commands

    def test_sudo_detection(self):
        result = parse_bash("sudo rm -rf /")
        assert result.has_sudo is True

    def test_redirect_detection(self):
        result = parse_bash("echo hi > file.txt")
        assert result.has_redirect

    def test_var_assignment(self):
        result = parse_bash("NAME=world echo $NAME")
        assert result.has_var_assignment

    def test_commands_with_args(self):
        result = parse_bash("git commit -m 'fix bug'")
        assert len(result.commands_with_args) == 1
        assert result.commands_with_args[0]["command"] == "git"

    def test_multiple_commands(self):
        result = parse_bash("cd dir && npm install && npm run build")
        assert len(result.commands) >= 3

    def test_dangerous_detection(self):
        dangerous, reason = is_dangerous_command("rm -rf /")
        assert dangerous

    def test_safe_command(self):
        dangerous, reason = is_dangerous_command("ls -la")
        assert not dangerous

    def test_lexer_error(self):
        result = parse_bash("echo 'unclosed")
        assert not result.ok
        assert result.error

    def test_extract_git_commands(self):
        cmds = extract_git_commands("git status && git diff")
        assert "git" in cmds

    def test_empty_input(self):
        result = parse_bash("")
        assert result.ok
        assert result.commands == []
