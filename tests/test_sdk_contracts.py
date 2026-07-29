import pytest

from src.sdk.contracts import validate, ValidationError, GENERATE_CONTRACT, READ_FILE_CONTRACT


class TestContracts:
    def test_generate_valid(self):
        result = validate("generate", {"prompt": "hello", "max_tokens": 100})
        assert result["prompt"] == "hello"

    def test_generate_missing_required(self):
        with pytest.raises(ValidationError, match="Missing required"):
            validate("generate", {})

    def test_generate_wrong_type(self):
        with pytest.raises(ValidationError):
            validate("generate", {"prompt": 42})

    def test_read_file_valid(self):
        result = validate("read_file", {"path": "/tmp/test.txt"})
        assert result["path"] == "/tmp/test.txt"

    def test_unknown_contract(self):
        result = validate("unknown_method", {"anything": "goes"})
        assert result["anything"] == "goes"

    def test_contract_schema(self):
        assert "prompt" in GENERATE_CONTRACT.input_schema["properties"]
        assert "path" in READ_FILE_CONTRACT.input_schema["properties"]
