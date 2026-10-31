"""SSE endpoints. Handlers hold no DB connections: they only wait on an in-memory queue."""
from __future__ import annotations

from typing import AsyncIterator, Optional

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from app.bus import bus

router = APIRouter()
HEARTBEAT_S = 15


async def _stream(user_id: Optional[str]) -> AsyncIterator[ServerSentEvent]:
    sub = bus.subscribe(user_id)
    try:
        yield ServerSentEvent(comment="connected")
        while True:
            msg = await sub.queue.get()
            yield ServerSentEvent(data=msg.model_dump_json())
    finally:
        bus.unsubscribe(sub)


@router.get("/events")
async def events() -> EventSourceResponse:
    return EventSourceResponse(_stream(None), ping=HEARTBEAT_S)


@router.get("/victim/{user_id}/events")
async def victim_events(user_id: str) -> EventSourceResponse:
    return EventSourceResponse(_stream(user_id), ping=HEARTBEAT_S)
