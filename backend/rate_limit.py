"""Rate limiting local para tentativas malsucedidas de login.

O armazenamento em memória protege cada processo/worker individualmente.
Em produção com múltiplas instâncias, complemente com rate limiting no proxy
ou com um armazenamento compartilhado (por exemplo, Redis).
"""
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException


class LoginRateLimiter:
    def __init__(self, max_attempts=20, window_seconds=300, clock=monotonic):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.clock = clock
        self._attempts = defaultdict(deque)
        self._lock = Lock()

    def _prune(self, key, now):
        attempts = self._attempts[key]
        cutoff = now - self.window_seconds
        while attempts and attempts[0] <= cutoff:
            attempts.popleft()
        if not attempts:
            self._attempts.pop(key, None)
            return deque()
        return attempts

    def check(self, key):
        now = self.clock()
        with self._lock:
            attempts = self._prune(key, now)
            if len(attempts) >= self.max_attempts:
                retry_after = max(1, int(self.window_seconds - (now - attempts[0])))
                raise HTTPException(
                    status_code=429,
                    detail="Muitas tentativas de login. Aguarde antes de tentar novamente.",
                    headers={"Retry-After": str(retry_after)},
                )

    def record_failure(self, key):
        now = self.clock()
        with self._lock:
            self._prune(key, now)
            self._attempts[key].append(now)

    def reset(self, key):
        with self._lock:
            self._attempts.pop(key, None)


login_rate_limiter = LoginRateLimiter()
