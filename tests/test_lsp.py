import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.lsp import (
    LspClient, LspPosition, LspRange, LspDiagnostic,
    LspCompletionItem, LspLocation, LspHover,
)

SAMPLE_RESPONSE = json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "result": {"capabilities": {}}
})


@pytest.fixture
def mock_client():
    with patch("src.lsp.subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdout = MagicMock()
        proc.stdout.readline.side_effect = [
            b"Content-Length: %d\r\n" % len(SAMPLE_RESPONSE.encode()),
            b"\r\n",
        ]
        proc.stdout.read.return_value = SAMPLE_RESPONSE.encode()
        mock_popen.return_value = proc
        client = LspClient("python", ["pylsp"], "file:///test")
        yield client


class TestLspPosition:
    def test_create(self):
        pos = LspPosition(line=10, character=5)
        assert pos.line == 10
        assert pos.character == 5


class TestLspRange:
    def test_create(self):
        r = LspRange(
            start=LspPosition(0, 0),
            end=LspPosition(1, 0),
        )
        assert r.start.line == 0
        assert r.end.line == 1


class TestLspDiagnostic:
    def test_create(self):
        d = LspDiagnostic(
            range=LspRange(LspPosition(0, 0), LspPosition(0, 5)),
            severity=1, message="test error", source="pyflakes",
        )
        assert "test error" in d.message


class TestLspCompletionItem:
    def test_create(self):
        item = LspCompletionItem(label="print", kind=3, detail="built-in", insert_text="print()")
        assert item.label == "print"
        assert item.insert_text == "print()"


class TestLspLocation:
    def test_create(self):
        loc = LspLocation(
            uri="file:///test.py",
            range=LspRange(LspPosition(0, 0), LspPosition(0, 10)),
        )
        assert "test.py" in loc.uri


class TestLspHover:
    def test_create(self):
        hover = LspHover(contents="def foo():", range=None)
        assert "foo" in hover.contents

    def test_with_range(self):
        hover = LspHover(
            contents="hello",
            range=LspRange(LspPosition(0, 0), LspPosition(0, 5)),
        )
        assert hover.range is not None


class TestLspClientUnit:
    def test_init(self):
        with patch("src.lsp.subprocess.Popen") as mp:
            proc = MagicMock()
            proc.stdin = MagicMock()
            proc.stdout = MagicMock()

            def readline_side_effect():
                payload = SAMPLE_RESPONSE.encode()
                yield b"Content-Length: %d\r\n" % len(payload)
                yield b"\r\n"
                while True:
                    yield b""

            proc.stdout.readline.side_effect = readline_side_effect()
            proc.stdout.read.return_value = SAMPLE_RESPONSE.encode()
            mp.return_value = proc
            client = LspClient("python", ["pylsp"], "file:///test")
            client.start()
            assert client.language == "python"
            assert client._process is not None
            client.shutdown()

    def test_parse_completion_empty(self, mock_client):
        mock_client._recv = MagicMock(return_value={"result": []})
        items = mock_client.complete("file:///test.py", 0, 0)
        assert items == []

    def test_parse_definition_none(self, mock_client):
        mock_client._recv = MagicMock(return_value={"result": None})
        locs = mock_client.goto_definition("file:///test.py", 0, 0)
        assert locs == []

    def test_parse_hover_none(self, mock_client):
        mock_client._recv = MagicMock(return_value={"result": None})
        hover = mock_client.hover("file:///test.py", 0, 0)
        assert hover is None
