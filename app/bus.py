"""In-process pub/sub over asyncio queues.

Global channel -> officer console (gets every message).
Per-user channel -> victim app (gets that user's `victim_prompt` messages).
Thread-safe: publish() from a non-loop thread hops onto the subscriber's loop.
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

from app.contracts import Case, StreamMessage

QUEUE_MAX = 500


class Subscription:
    def __init__(self, user_id: Optional[str]) -> None:
        self.user_id = user_id
        self.queue: asyncio.Queue[StreamMessage] = asyncio.Queue(maxsize=QUEUE_MAX)
        try:
            self.loop: Optional[asyncio.AbstractEventLoop] = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = None

    def _put(self, msg: StreamMessage) -> None:
        if self.queue.full():
            try:
                self.queue.get_nowait()   # drop oldest
            except asyncio.QueueEmpty:
                pass
        self.queue.put_nowait(msg)

    def deliver(self, msg: StreamMessage) -> None:
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if self.loop is None or running is self.loop:
            self._put(msg)
        elif not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self._put, msg)


class Bus:
    def __init__(self) -> None:
        self._global: set[Subscription] = set()
        self._users: dict[str, set[Subscription]] = {}

    def subscribe(self, user_id: Optional[str] = None) -> Subscription:
        sub = Subscription(user_id)
        if user_id is None:
            self._global.add(sub)
        else:
            self._users.setdefault(user_id, set()).add(sub)
        return sub

    def unsubscribe(self, sub: Subscription) -> None:
        if sub.user_id is None:
            self._global.discard(sub)
        else:
            self._users.get(sub.user_id, set()).discard(sub)

    def publish(self, msg: StreamMessage, user_id: Optional[str] = None) -> None:
        for sub in list(self._global):
            sub.deliver(msg)
        if user_id is not None:
            for sub in list(self._users.get(user_id, ())):
                sub.deliver(msg)

    def reset(self) -> None:
        """Drop queued messages but keep connected subscribers."""
        for sub in list(self._global) + [s for subs in self._users.values() for s in subs]:
            while not sub.queue.empty():
                sub.queue.get_nowait()


bus = Bus()


def publish(msg: StreamMessage, user_id: Optional[str] = None) -> None:
    bus.publish(msg, user_id)


def publish_case(case: Case) -> None:
    bus.publish(StreamMessage(kind="case", data=case.model_dump(mode="json")))


def publish_data(kind: str, data: dict[str, Any], user_id: Optional[str] = None) -> None:
    bus.publish(StreamMessage(kind=kind, data=data), user_id)  # type: ignore[arg-type]
