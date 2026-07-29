import pytest

from src.reference import ReferenceResolver


class TestReferenceResolver:
    def test_no_references(self):
        r = ReferenceResolver()
        assert r.resolve("hello world") == "hello world"

    def test_extract_references(self):
        r = ReferenceResolver()
        refs = r.extract_references("use {{file.path}} and {{session.id}}")
        assert refs == ["file.path", "session.id"]

    def test_resolve_with_registered(self):
        r = ReferenceResolver()
        r.register("file", lambda ref: f"/resolved/{ref.path}")
        result = r.resolve("path = {{file.path}}")
        assert result == "path = /resolved/path"

    def test_unresolved_reference_left_as_is(self):
        r = ReferenceResolver()
        result = r.resolve("{{unknown.ref}}")
        assert result == "{{unknown.ref}}"

    def test_multiple_references(self):
        r = ReferenceResolver()
        r.register("a", lambda ref: "X")
        r.register("b", lambda ref: "Y")
        result = r.resolve("{{a.x}} and {{b.y}}")
        assert result == "X and Y"

    def test_source_returns_none(self):
        r = ReferenceResolver()
        r.register("missing", lambda ref: None)
        result = r.resolve("{{missing.val}}")
        assert result == "{{missing.val}}"

    def test_no_references_in_text(self):
        r = ReferenceResolver()
        assert r.extract_references("no refs") == []
