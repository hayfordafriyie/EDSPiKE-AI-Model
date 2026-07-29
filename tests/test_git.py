from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.git import GitOperations
from src.git.operations import GitError


@pytest.fixture
def repo():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        # init git repo
        import subprocess
        subprocess.run(["git", "init"], cwd=path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=path, capture_output=True)
        yield GitOperations(str(path))


class TestGitOperations:
    def test_is_git_repo(self, repo):
        assert repo.is_git_repo() is True

    def test_is_not_git_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            ops = GitOperations(tmp)
            assert ops.is_git_repo() is False

    def test_status_empty(self, repo):
        status = repo.status()
        assert "No commits yet" in status or "nothing committed" in status

    def test_status_with_changes(self, repo):
        (Path(repo._repo) / "test.txt").write_text("hello")
        status = repo.status()
        assert "test.txt" in status

    def test_add_and_commit(self, repo):
        f = Path(repo._repo) / "file.txt"
        f.write_text("content")
        repo.add(str(f))
        out = repo.commit("initial commit")
        assert "initial commit" in out

    def test_log(self, repo):
        f = Path(repo._repo) / "a.txt"
        f.write_text("a")
        repo.add(str(f))
        repo.commit("first")
        f2 = Path(repo._repo) / "b.txt"
        f2.write_text("b")
        repo.add(str(f2))
        repo.commit("second")
        log = repo.log(max_count=5)
        assert "first" in log
        assert "second" in log

    def test_diff(self, repo):
        f = Path(repo._repo) / "f.txt"
        f.write_text("original")
        repo.add(str(f))
        repo.commit("init")
        f.write_text("modified")
        diff = repo.diff()
        assert "original" in diff
        assert "modified" in diff

    def test_diff_staged(self, repo):
        f = Path(repo._repo) / "f.txt"
        f.write_text("original")
        repo.add(str(f))
        repo.commit("init")
        f.write_text("staged change")
        repo.add(str(f))
        diff = repo.diff(staged=True)
        assert "staged change" in diff

    def test_branch(self, repo):
        f = Path(repo._repo) / "init.txt"
        f.write_text("init")
        repo.add(str(f))
        repo.commit("initial")
        branches = repo.branch()
        assert "* master" in branches or "* main" in branches

    def test_checkout_new_branch(self, repo):
        f = Path(repo._repo) / "init.txt"
        f.write_text("init")
        repo.add(str(f))
        repo.commit("initial")
        out = repo.checkout("feature", create=True)
        assert "feature" in out

    def test_show(self, repo):
        f = Path(repo._repo) / "s.txt"
        f.write_text("show me")
        repo.add(str(f))
        repo.commit("show commit")
        out = repo.show()
        assert "show commit" in out

    def test_diff_between(self, repo):
        f = Path(repo._repo) / "d.txt"
        f.write_text("v1")
        repo.add(str(f))
        repo.commit("first")
        f.write_text("v2")
        repo.add(str(f))
        repo.commit("second")
        diff = repo.diff_between("HEAD~1", "HEAD")
        assert "v2" in diff

    def test_shortlog(self, repo):
        f = Path(repo._repo) / "s.txt"
        f.write_text("s")
        repo.add(str(f))
        repo.commit("msg")
        log = repo.shortlog(max_count=5)
        assert "Test" in log

    def test_tool_specs(self, repo):
        specs = repo.get_tool_specs()
        names = [s["name"] for s in specs]
        assert "git_status" in names
        assert "git_diff" in names
        assert "git_log" in names
        assert "git_commit" in names
        assert "git_branch" in names
        assert "git_checkout" in names
        assert "git_show" in names
        assert "git_diff_between" in names
