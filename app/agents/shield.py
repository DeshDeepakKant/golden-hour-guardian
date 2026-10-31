"""Shield (+ Conductor-lite): Tier-1 containment on the victim's OWN account only."""
from __future__ import annotations

import asyncio

from app import fsm, orchestrator_tasks as tasks, store, tools
from app.agents import sentinel
from app.contracts import Case, CaseState, utcnow
from app.metrics import is_fraud_confirmed
from app.repo import repo
from app.util import aware

ACTOR = "agent:shield"


def place_hold(case: Case) -> None:
    """Temp hold on the victim's own outgoing payments + auto-expiry task."""
    tools.place_temp_hold(case, ACTOR)
    tasks.spawn(case.case_id, _hold_expiry(case.case_id), "hold_expiry")


def suppress_marketing(case: Case) -> None:
    if not tools.marketing_suppressed(case.user_id):
        tools.suppress_marketing(case, ACTOR)


def contain(case: Case) -> Case:
    """CONFIRMED_FRAUD -> CONTAINED: hold (if none), revoke the suspicious device(s), hold marketing."""
    store.refresh(case)
    if not case.hold_active:
        place_hold(case)
    profile = repo.user_profile(case.user_id)
    trusted = profile.get("trusted_device")
    devices = sorted({t.device_id for t in sentinel.suspect_txns(case) if t.device_id != trusted})
    for dev in devices:
        info = repo.device(dev)
        if info and not info["revoked"]:
            tools.revoke_session(case, ACTOR, dev)
    suppress_marketing(case)
    return fsm.transition(case, CaseState.CONTAINED, ACTOR, "victim's own access protected")


async def _hold_expiry(case_id: str) -> None:
    """Release the hold at expiry unless fraud is confirmed (then the officer owns it)."""
    while True:
        case = store.get_case(case_id)
        if case is None or not case.hold_active or case.hold_expires_at is None:
            return
        if is_fraud_confirmed(case):
            return
        wait = (aware(case.hold_expires_at) - utcnow()).total_seconds()
        if wait > 0:
            await asyncio.sleep(wait)
            continue
        tools.expire_hold(case, ACTOR)
        return
