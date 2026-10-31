"""Shield (+ Conductor-lite): Tier-1 containment on the victim's OWN account only."""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional

from app import audit, fsm, orchestrator_tasks as tasks, store, tools
from app.agents import sentinel
from app.config import POLICY
from app.contracts import Action, Case, CaseState, DecisionStatus, EventType, utcnow
from app.metrics import is_fraud_confirmed
from app.repo import repo
from app.util import aware

ACTOR = "agent:shield"


def place_hold(case: Case) -> None:
    """Temp hold on the victim's own outgoing payments + auto-expiry task."""
    tools.place_temp_hold(case, ACTOR)
    arm_expiry(case.case_id)


def arm_expiry(case_id: str) -> None:
    """(Re)start the single expiry timer for this case's hold."""
    tasks.cancel(case_id, "hold_expiry")
    tasks.spawn(case_id, _hold_expiry(case_id), "hold_expiry")


def hold_max_s() -> float:
    """Longest a confirmed-fraud hold may run without an approved EXTEND_HOLD (env override for tests)."""
    env = os.environ.get("GUARDIAN_HOLD_MAX_S")
    return float(env) if env else float(POLICY["hold"]["max_without_officer_minutes"]) * 60


def suppress_marketing(case: Case) -> None:
    if not tools.marketing_suppressed(case.user_id):
        tools.suppress_marketing(case, ACTOR)


def contain(case: Case) -> Case:
    """CONFIRMED_FRAUD -> CONTAINED: hold (if none), revoke the suspicious device(s), hold marketing."""
    store.refresh(case)
    if not case.hold_active:
        place_hold(case)
    else:
        arm_expiry(case.case_id)      # timer switches to the confirmed-fraud limit now
    profile = repo.user_profile(case.user_id)
    trusted = profile.get("trusted_device")
    devices = sorted({t.device_id for t in sentinel.suspect_txns(case) if t.device_id != trusted})
    for dev in devices:
        info = repo.device(dev)
        if info and not info["revoked"]:
            tools.revoke_session(case, ACTOR, dev)
    suppress_marketing(case)
    return fsm.transition(case, CaseState.CONTAINED, ACTOR, "victim's own access protected")


def _placed_at(case_id: str) -> Optional[datetime]:
    """When the current Tier-1 hold was placed (latest non-extension HOLD_PLACED)."""
    placed = [e.ts for e in audit.list_events(case_id)
              if e.type == EventType.HOLD_PLACED and not e.payload.get("extended")]
    return aware(placed[-1]) if placed else None


def _extension_approved(case_id: str) -> bool:
    return any(d.action == Action.EXTEND_HOLD for d in store.list_decisions(case_id, DecisionStatus.APPROVED))


async def _hold_expiry(case_id: str) -> None:
    """Release the hold when it is due.

    Not fraud: at hold_expires_at (Tier-1 auto-expiry). Confirmed fraud: at placement +
    hold.max_without_officer_minutes, unless an officer APPROVED an EXTEND_HOLD (then at the
    extended hold_expires_at, which desk re-arms this timer for).
    """
    while True:
        case = store.get_case(case_id)
        if case is None or not case.hold_active or case.hold_expires_at is None:
            return
        reason = "hold auto-expired"
        due = aware(case.hold_expires_at)
        if is_fraud_confirmed(case):
            if _extension_approved(case_id):
                reason = "approved hold extension ended"
            else:
                placed = _placed_at(case_id) or utcnow()
                due = placed + timedelta(seconds=hold_max_s())
                reason = "hold reached the limit without an officer-approved extension"
        wait = (due - utcnow()).total_seconds()
        if wait > 0:
            await asyncio.sleep(wait)
            continue
        tools.expire_hold(case, ACTOR, reason)
        return
