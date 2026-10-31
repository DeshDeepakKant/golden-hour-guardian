"""Run brain calls off the event loop, serialised, and log LLM_FALLBACK_USED (SPEC section 8 rule)."""
from __future__ import annotations

import asyncio
import logging
import threading
from typing import Any, Optional

from app import audit
from app.brain.api import brain
from app.contracts import EventType

log = logging.getLogger("guardian.brain")
_lock = threading.Lock()   # brain.last_used_fallback is shared state


async def call(case_id: Optional[str], fn_name: str, *args: Any, default: Any = None) -> Any:
    def run() -> tuple[Any, bool, Optional[str]]:
        with _lock:
            try:
                out = getattr(brain, fn_name)(*args)
                return out, bool(getattr(brain, "last_used_fallback", False)), None
            except Exception as exc:   # brain must never raise; be safe anyway
                return default, True, f"{type(exc).__name__}: {exc}"

    out, fell_back, err = await asyncio.to_thread(run)
    if fell_back and case_id:
        payload = {"function": fn_name}
        if err:
            payload["error"] = err
        audit.append(case_id, EventType.LLM_FALLBACK_USED, "system", None, payload)
    if err:
        log.warning("brain.%s raised: %s", fn_name, err)
    return out


def llm_status() -> str:
    is_up = getattr(brain, "is_up", None)
    try:
        return "up" if (callable(is_up) and is_up()) else "fallback"
    except Exception:
        return "fallback"
