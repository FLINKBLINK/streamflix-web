from fastapi import HTTPException
import pytest

from backend.rate_limit import LoginRateLimiter


def test_rate_limiter_blocks_after_configured_failed_attempts():
    now = [100.0]
    limiter = LoginRateLimiter(max_attempts=3, window_seconds=60, clock=lambda: now[0])
    key = "192.0.2.10"

    for _ in range(3):
        limiter.check(key)
        limiter.record_failure(key)

    with pytest.raises(HTTPException) as error:
        limiter.check(key)

    assert error.value.status_code == 429
    assert int(error.value.headers["Retry-After"]) > 0


def test_rate_limiter_releases_key_after_window_expires():
    now = [100.0]
    limiter = LoginRateLimiter(max_attempts=2, window_seconds=30, clock=lambda: now[0])
    key = "192.0.2.11"

    limiter.record_failure(key)
    limiter.record_failure(key)
    with pytest.raises(HTTPException):
        limiter.check(key)

    now[0] = 131.0
    limiter.check(key)


def test_successful_login_can_reset_attempt_counter():
    limiter = LoginRateLimiter(max_attempts=1, window_seconds=60, clock=lambda: 100.0)
    key = "192.0.2.12"
    limiter.record_failure(key)
    limiter.reset(key)
    limiter.check(key)
