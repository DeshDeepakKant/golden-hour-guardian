"""Registry of background asyncio tasks per case (so reset/shutdown can cancel them all)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Coroutine, Optional

log = logging.getLogger("guardian.tasks")
_TASKS: dict[asyncio.Task, tuple[str, str]] = {}   # task -> (case_id, name)


def spawn(case_id: str, coro: Coroutine[Any, Any, Any], name: str = "") -> Optional[asyncio.Task]:
    try:
        asyncio.get_running_loop()
    except RuntimeError:       # no loop (sync caller, e.g. a unit test): nothing to schedule
        coro.close()
        return None
    task = asyncio.create_task(coro, name=f"{case_id}:{name}")
    _TASKS[task] = (case_id, name)
    task.add_done_callback(_done)
    return task


def _done(task: asyncio.Task) -> None:
    _TASKS.pop(task, None)
    if not task.cancelled() and task.exception() is not None:
        log.error("background task %s failed", task.get_name(), exc_info=task.exception())


def cancel(case_id: str, name: Optional[str] = None) -> None:
    """Cancel tasks for a case (optionally by name), never the calling task itself."""
    try:
        current = asyncio.current_task()
    except RuntimeError:
        current = None
    for task, (cid, tname) in list(_TASKS.items()):
        if cid == case_id and (name is None or tname == name) and task is not current:
            task.cancel()


async def cancel_all() -> None:
    tasks = [t for t in _TASKS if not t.done()]
    for t in tasks:
        t.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    _TASKS.clear()


def active_count() -> int:
    return sum(1 for t in _TASKS if not t.done())
