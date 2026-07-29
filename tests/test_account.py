import tempfile
from pathlib import Path

import pytest

from src.account import AccountManager


class TestAccount:
    def test_create_and_get(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = AccountManager(str(Path(tmp) / "accounts"))
            acct = mgr.create("Alice", "alice@example.com", role="admin")
            assert acct.name == "Alice"
            fetched = mgr.get(acct.id)
            assert fetched is not None
            assert fetched.role == "admin"

    def test_get_by_email(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = AccountManager(str(Path(tmp) / "accounts"))
            mgr.create("Bob", "bob@example.com")
            acct = mgr.get_by_email("bob@example.com")
            assert acct is not None
            assert acct.name == "Bob"
            assert mgr.get_by_email("nobody@x.com") is None

    def test_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = AccountManager(str(Path(tmp) / "accounts"))
            acct = mgr.create("Charlie", "c@example.com")
            mgr.update(acct.id, name="Charlie Updated", role="admin")
            assert mgr.get(acct.id).name == "Charlie Updated"
            assert mgr.get(acct.id).role == "admin"

    def test_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = AccountManager(str(Path(tmp) / "accounts"))
            acct = mgr.create("Dave", "d@example.com")
            assert mgr.delete(acct.id) is True
            assert mgr.get(acct.id) is None
            assert mgr.delete("nonexistent") is False

    def test_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = AccountManager(str(Path(tmp) / "accounts"))
            mgr.create("A", "a@x.com")
            mgr.create("B", "b@x.com")
            assert len(mgr.list()) == 2

    def test_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = AccountManager(str(Path(tmp) / "accounts"))
            assert mgr.count() == 0
            mgr.create("X", "x@x.com")
            assert mgr.count() == 1

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = str(Path(tmp) / "accounts")
            mgr1 = AccountManager(data_dir)
            mgr1.create("P", "p@x.com")
            mgr2 = AccountManager(data_dir)
            assert mgr2.count() == 1
            assert mgr2.get_by_email("p@x.com") is not None
