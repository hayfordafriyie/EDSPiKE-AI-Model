import tempfile
from pathlib import Path

import pytest

from src.share import SessionSharing


class TestSessionSharing:
    def test_share_and_check_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            sharing = SessionSharing(str(Path(tmp) / "shares"))
            sharing.share("sess1", "owner1", "user1", permission="write")
            assert sharing.check_access("sess1", "owner1") == "admin"
            assert sharing.check_access("sess1", "user1") == "write"
            assert sharing.check_access("sess1", "stranger") == "denied"

    def test_add_user(self):
        with tempfile.TemporaryDirectory() as tmp:
            sharing = SessionSharing(str(Path(tmp) / "shares"))
            sharing.share("s1", "owner", "user1")
            assert sharing.add_user("s1", "user2") is True
            assert sharing.check_access("s1", "user2") == "read"
            assert sharing.add_user("nonexistent", "x") is False

    def test_remove_user(self):
        with tempfile.TemporaryDirectory() as tmp:
            sharing = SessionSharing(str(Path(tmp) / "shares"))
            sharing.share("s1", "owner", "user1")
            sharing.add_user("s1", "user2")
            assert sharing.remove_user("s1", "user1") is True
            assert sharing.check_access("s1", "user1") == "denied"

    def test_revoke(self):
        with tempfile.TemporaryDirectory() as tmp:
            sharing = SessionSharing(str(Path(tmp) / "shares"))
            sharing.share("s1", "owner", "user1")
            assert sharing.revoke("s1", "owner") is True
            assert sharing.check_access("s1", "owner") == "denied"
            assert sharing.revoke("s1", "wrong_owner") is False

    def test_list_for_user(self):
        with tempfile.TemporaryDirectory() as tmp:
            sharing = SessionSharing(str(Path(tmp) / "shares"))
            sharing.share("s1", "owner", "user1")
            sharing.share("s2", "owner", "user1")
            sharing.share("s3", "other", "user2")
            owned = sharing.list_for_user("user1")
            assert len(owned) == 2
            owner_list = sharing.list_for_user("owner")
            assert len(owner_list) == 2  # owner of s1, s2

    def test_expiration(self):
        with tempfile.TemporaryDirectory() as tmp:
            sharing = SessionSharing(str(Path(tmp) / "shares"))
            sharing.share("s1", "owner", "user1", expires_in=0.001)
            import time; time.sleep(0.01)
            assert sharing.check_access("s1", "user1") == "denied"

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = str(Path(tmp) / "shares")
            s1 = SessionSharing(data_dir)
            s1.share("s1", "owner", "user1")
            s2 = SessionSharing(data_dir)
            assert len(s2.list_all()) == 1
            assert s2.check_access("s1", "user1") == "read"
