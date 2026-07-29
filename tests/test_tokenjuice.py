from src.tokenjuice import TokenJuicer


class TestTokenJuicer:
    def test_small_output(self):
        j = TokenJuicer()
        result = j.compact("bash", "hello world")
        assert result.ratio == 1.0
        assert result.text == "hello world"

    def test_truncates_long_lines(self):
        j = TokenJuicer(max_output_chars=10)
        result = j.compact("bash", "x" * 1000)
        assert len(result.text) < 1000

    def test_repeated_lines(self):
        j = TokenJuicer()
        text = "line1\n" * 10
        result = j.compact("bash", text)
        assert "repeated" in result.text

    def test_json_arrays(self):
        j = TokenJuicer()
        text = "[{}" + ",".join('{"x":1}' for _ in range(100)) + "]"
        result = j.compact("bash", text)
        assert "array of" in result.text

    def test_stack_traces(self):
        j = TokenJuicer()
        text = '  File "test.py", line 10, in foo\n  File "test.py", line 20, in bar\n'
        result = j.compact("bash", text)
        assert "stack trace" in result.text

    def test_return_type(self):
        j = TokenJuicer()
        result = j.compact("bash", "output")
        assert hasattr(result, "original_length")
        assert hasattr(result, "compressed_length")
        assert hasattr(result, "ratio")
