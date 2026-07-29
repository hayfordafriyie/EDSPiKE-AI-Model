import pytest

from src.ulid import ULID, ulid


class TestULID:
    def test_generate(self):
        u = ULID.new()
        s = str(u)
        assert len(s) == 26
        assert s.isupper()

    def test_from_str(self):
        u = ULID.from_str("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert str(u) == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_equality(self):
        a = ULID.from_str("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        b = ULID.from_str("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        c = ULID.new()
        assert a == b
        assert a != c

    def test_hashable(self):
        s = {ULID.from_str("01ARZ3NDEKTSV4RRFFQ69G5FAV")}
        assert len(s) == 1

    def test_uniqueness(self):
        ids = {ulid() for _ in range(100)}
        assert len(ids) == 100

    def test_repr(self):
        u = ULID.from_str("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        assert repr(u) == "ULID('01ARZ3NDEKTSV4RRFFQ69G5FAV')"

    def test_ulid_function(self):
        u = ulid()
        assert len(u) == 26
        assert isinstance(u, str)
