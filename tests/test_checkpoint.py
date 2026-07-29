import pytest

from src.checkpoint import CheckpointManager, BackToTheFuture


class TestCheckpoint:
    def test_save_and_latest(self):
        mgr = CheckpointManager()
        save_id = mgr.save([{"role": "user", "content": "hello"}])
        cp = mgr.latest()
        assert cp is not None
        assert cp.save_id == save_id

    def test_revert(self):
        mgr = CheckpointManager()
        mgr.save([{"role": "user", "content": "first"}])
        mgr.save([{"role": "user", "content": "second"}])
        cp = mgr.revert_to_step(1)
        assert cp is not None
        assert cp.context[0]["content"] == "first"

    def test_revert_by_id(self):
        mgr = CheckpointManager()
        id1 = mgr.save([{"role": "user", "content": "a"}])
        mgr.save([{"role": "user", "content": "b"}])
        cp = mgr.revert(id1)
        assert cp is not None
        assert cp.context[0]["content"] == "a"

    def test_revert_nonexistent(self):
        mgr = CheckpointManager()
        assert mgr.revert("nonexistent") is None

    def test_send_dmail(self):
        mgr = CheckpointManager()
        with pytest.raises(BackToTheFuture, match="DMail"):
            mgr.send_dmail("cp_1", "try something else")

    def test_count(self):
        mgr = CheckpointManager()
        assert mgr.count() == 0
        mgr.save([])
        assert mgr.count() == 1

    def test_clear(self):
        mgr = CheckpointManager()
        mgr.save([])
        mgr.save([])
        mgr.clear()
        assert mgr.count() == 0
