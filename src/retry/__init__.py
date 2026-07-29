import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    retryable_exceptions: tuple = (Exception,)


class RetryExhausted(Exception):
    def __init__(self, attempts: int, last_error: Exception):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"Failed after {attempts} attempts: {last_error}")


def exponential_backoff(attempt: int, base: float = 1.0, max_delay: float = 60.0, jitter: bool = True) -> float:
    delay = min(base * (2 ** attempt), max_delay)
    if jitter:
        delay *= 0.5 + random.random() * 0.5
    return delay


def retry(fn: Callable[..., Any], config: RetryConfig | None = None, *args: Any, **kwargs: Any) -> Any:
    cfg = config or RetryConfig()
    last_error: Exception | None = None

    for attempt in range(cfg.max_attempts):
        try:
            return fn(*args, **kwargs)
        except cfg.retryable_exceptions as e:
            last_error = e
            if attempt < cfg.max_attempts - 1:
                delay = exponential_backoff(attempt, cfg.base_delay, cfg.max_delay, cfg.jitter)
                time.sleep(delay)

    raise RetryExhausted(cfg.max_attempts, last_error)  # type: ignore


class RetryDecorator:
    def __init__(self, config: RetryConfig | None = None):
        self._config = config or RetryConfig()

    def __call__(self, fn: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return retry(fn, self._config, *args, **kwargs)
        return wrapper
