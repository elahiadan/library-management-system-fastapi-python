import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request

from app.core.config import settings
from app.core.exceptions import AppError

_WINDOW_SECONDS = 60.0
_lock = Lock()
_hits: dict[str, deque[float]] = defaultdict(deque)


def _prune() -> None:
    now = time.monotonic()
    cutoff = now - _WINDOW_SECONDS
    for key in [k for k, q in _hits.items() if not q or q[-1] <= cutoff]:
        del _hits[key]
    for key, queue in list(_hits.items()):
        while queue and queue[0] <= cutoff:
            queue.popleft()


def check_rate_limit(key: str, limit: int) -> None:
    if limit <= 0:
        return
    now = time.monotonic()
    with _lock:
        _prune()
        queue = _hits[key]
        while queue and queue[0] <= now - _WINDOW_SECONDS:
            queue.popleft()
        if len(queue) >= limit:
            raise AppError(
                status_code=429,
                message="Too many requests, please try again later",
            )
        queue.append(now)


def rate_limit(limit: int):
    def dependency(request: Request) -> None:
        if settings.environment.lower() == "test":
            return
        client_host = request.client.host if request.client else "unknown"
        check_rate_limit(f"{client_host}", limit)

    return dependency