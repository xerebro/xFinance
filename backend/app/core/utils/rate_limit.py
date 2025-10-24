"""Asynchronous rate limiter utilities."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from contextlib import asynccontextmanager
from typing import Deque


class RateLimiter:
    """Token bucket style rate limiter for async clients."""

    def __init__(self, rate: int, per: float):
        self.rate = rate
        self.per = per
        self._lock = asyncio.Lock()
        self._events: Deque[float] = deque()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            while self._events and now - self._events[0] > self.per:
                self._events.popleft()
            if len(self._events) >= self.rate:
                sleep_for = self.per - (now - self._events[0])
                await asyncio.sleep(max(sleep_for, 0))
            self._events.append(time.monotonic())

    @asynccontextmanager
    async def limit(self):
        await self.acquire()
        yield


__all__ = ["RateLimiter"]
