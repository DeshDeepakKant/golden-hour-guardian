"""Run brain calls off the event loop and log LLM_FALLBACK_USED (SPEC section 8 rule).

Two lanes, so a victim-facing call never queues behind an officer-facing one:
- victim lane: the shared `brain`, serialised (brain.last_used_fallback is per-instance state);
- officer lane: a per-call shallow copy of `brain` (own fallback flag), serialised separately.
"""
from __future__ import annotations

import asyncio
import copy
import logging
import threading
from typing import Any, Optional

from app import audit
from app.brain.api import brain
from app.contracts import EventType

log = logging.getLogger("guardian.brain")
OFFICER_FNS = frozenset({"explain_risk", "decision_rationale"})
_victim_lock = threading.Lock()    # guards the shared brain.last_used_fallback
_officer_lock = threading.Lock()   # officer calls queue among themselves, never ahead of the victim


def _lane(fn_name: str) -> tuple[Any, threading.Lock]:
    if fn_name in OFFICER_FNS:
        try:
            return copy.copy(brain), _officer_lock
        except Exception:
            pass
    return brain, _victim_lock


async def call(case_id: Optional[str], fn_name: str, *args: Any, default: Any = None) -> Any:
    def run() -> tuple[Any, bool, Optional[str]]:
        target, lock = _lane(fn_name)
        with lock:
            try:
                out = getattr(target, fn_name)(*args)
                return out, bool(getattr(target, "last_used_fallback", False)), None
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
