import tempfile
from pathlib import Path

import pytest

from src.kaos import ExecutionEnvironment, ExecutionResult


class TestKaos:
    def test_path_operations(self):
        env = ExecutionEnvironment("/tmp")
        assert env.getcwd() == "/tmp"

    def test_normpath(self):
        env = ExecutionEnvironment()
        p = env.normpath(".")
        assert Path(p).is_absolute()

    def test_gethome(self):
        env = ExecutionEnvironment()
        assert env.gethome() == str(Path.home())

    def test_exec_success(self):
        env = ExecutionEnvironment()
        result = env.exec("echo hello")
        assert result.ok()
        assert "hello" in result.stdout

    def test_exec_failure(self):
        env = ExecutionEnvironment()
        result = env.exec("exit 1")
        assert not result.ok()
        assert result.exit_code == 1

    def test_exec_timeout(self):
        env = ExecutionEnvironment()
        result = env.exec("sleep 10", timeout=0.1)
        assert not result.ok()

    def test_read_write_text(self, tmp_path: Path):
        env = ExecutionEnvironment(str(tmp_path))
        env.write_text("test.txt", "hello world")
        assert env.read_text("test.txt") == "hello world"

    def test_stat(self, tmp_path: Path):
        env = ExecutionEnvironment(str(tmp_path))
        (tmp_path / "f.txt").write_text("hi")
        s = env.stat("f.txt")
        assert s["is_file"] is True
        assert s["size"] > 0

    def test_iterdir(self, tmp_path: Path):
        (tmp_path / "a.txt").write_text("")
        (tmp_path / "b.txt").write_text("")
        env = ExecutionEnvironment(str(tmp_path))
        entries = env.iterdir()
        assert len(entries) == 2

    def test_glob(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("")
        (tmp_path / "b.py").write_text("")
        env = ExecutionEnvironment(str(tmp_path))
        matches = env.glob("*.py")
        assert len(matches) == 2

    def test_detect_os(self):
        os_name = ExecutionEnvironment.detect_os()
        assert os_name in ("posix", "win32")
