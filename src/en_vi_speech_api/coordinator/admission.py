from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Self

from en_vi_speech_api.errors import ApiError


@dataclass(slots=True)
class AdmissionLease:
    controller: AdmissionController
    released: bool = False

    async def release(self) -> None:
        if self.released:
            return
        self.released = True
        await self.controller._release()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        await self.release()


class AdmissionController:
    def __init__(self, *, max_inflight: int, max_pending: int, wait_timeout_s: float) -> None:
        if max_inflight <= 0 or max_pending < 0 or wait_timeout_s <= 0:
            raise ValueError("admission limits must be positive and pending must be non-negative")
        self.max_inflight = max_inflight
        self.max_pending = max_pending
        self.wait_timeout_s = wait_timeout_s
        self.active = 0
        self.pending = 0
        self._condition = asyncio.Condition()

    async def acquire(self) -> AdmissionLease:
        async with self._condition:
            if self.active < self.max_inflight:
                self.active += 1
                return AdmissionLease(self)
            if self.pending >= self.max_pending:
                raise ApiError("queue_full", "The public request queue is full.", 429)

            self.pending += 1
            try:
                await asyncio.wait_for(
                    self._condition.wait_for(lambda: self.active < self.max_inflight),
                    timeout=self.wait_timeout_s,
                )
            except TimeoutError as exc:
                self.pending -= 1
                raise ApiError(
                    "request_timeout", "Timed out waiting for request capacity.", 504
                ) from exc
            except BaseException:
                self.pending -= 1
                raise

            self.pending -= 1
            self.active += 1
            return AdmissionLease(self)

    async def _release(self) -> None:
        async with self._condition:
            if self.active <= 0:
                raise RuntimeError("admission active count underflow")
            self.active -= 1
            self._condition.notify(1)
