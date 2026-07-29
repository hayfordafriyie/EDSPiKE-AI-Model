import pytest

from src.retry import retry, RetryConfig, RetryExhausted, exponential_backoff


class TestRetry:
    def test_success_first_try(self):
        calls = [0]
        def fn():
            calls[0] += 1
            return 42
        result = retry(fn)
        assert result == 42
        assert calls[0] == 1

    def test_retry_on_failure(self):
        calls = [0]
        def fn():
            calls[0] += 1
            if calls[0] < 3:
                raise ValueError("not yet")
            return "ok"
        result = retry(fn, RetryConfig(max_attempts=5, base_delay=0.01, jitter=False))
        assert result == "ok"
        assert calls[0] == 3

    def test_exhausted(self):
        def fn():
            raise ValueError("always fails")
        with pytest.raises(RetryExhausted):
            retry(fn, RetryConfig(max_attempts=2, base_delay=0.01, jitter=False))

    def test_exponential_backoff(self):
        d1 = exponential_backoff(0, base=1.0, max_delay=60.0, jitter=False)
        d2 = exponential_backoff(1, base=1.0, max_delay=60.0, jitter=False)
        d3 = exponential_backoff(2, base=1.0, max_delay=60.0, jitter=False)
        assert d1 == 1.0
        assert d2 == 2.0
        assert d3 == 4.0

    def test_max_delay(self):
        d = exponential_backoff(10, base=1.0, max_delay=10.0, jitter=False)
        assert d == 10.0
