"""Case state machine. Whitelist transitions only (SPEC section 6)."""
from __future__ import annotations

from app import audit, metrics, store
from app.bus import publish_case
from app.contracts import Case, CaseState as S, EventType, utcnow


class IllegalTransition(Exception):
    pass


TRANSITIONS: dict[S, set[S]] = {
    S.NEW: {S.TRIAGED, S.CONFIRMED_FRAUD},      # NEW -> CONFIRMED_FRAUD only for victim-report origin
    S.TRIAGED: {S.DISMISSED, S.VERIFYING, S.HELD_PENDING_VERIFY},
    S.DISMISSED: {S.CLOSED},
    S.VERIFYING: {S.CONFIRMED_GENUINE, S.CONFIRMED_FRAUD, S.NO_RESPONSE_ESCALATED},
    S.HELD_PENDING_VERIFY: {S.CONFIRMED_GENUINE, S.CONFIRMED_FRAUD, S.NO_RESPONSE_ESCALATED},
    S.CONFIRMED_GENUINE: {S.RELEASED},
    S.RELEASED: {S.CLOSED},
    S.CONFIRMED_FRAUD: {S.CONTAINED},
    S.CONTAINED: {S.EVIDENCE_READY},
    S.EVIDENCE_READY: {S.AWAITING_OFFICER},
    S.NO_RESPONSE_ESCALATED: {S.AWAITING_OFFICER},
    S.AWAITING_OFFICER: {S.CLOSED},
    S.CLOSED: set(),
}

# state entered -> Case timestamp field it sets
_TIMESTAMPS = {
    S.TRIAGED: "t_triaged",
    S.CONFIRMED_GENUINE: "t_verified",
    S.CONFIRMED_FRAUD: "t_verified",
    S.CONTAINED: "t_contained",
    S.EVIDENCE_READY: "t_evidence_ready",
    S.CLOSED: "t_closed",
}
_METRIC_STATES = {S.CONTAINED, S.EVIDENCE_READY, S.RELEASED, S.CLOSED}


def transition(case: Case, to: S, actor: str, reason: str = "") -> Case:
    store.refresh(case)   # always validate against the persisted state, never a stale copy
    frm = case.state
    ok = to in TRANSITIONS.get(frm, set())
    if ok and frm == S.NEW and to == S.CONFIRMED_FRAUD and case.origin != "victim_report":
        ok = False
    if not ok:
        audit.append(case.case_id, EventType.POLICY_BLOCKED, actor, None,
                     {"kind": "illegal_transition", "from": frm.value, "to": to.value, "reason": reason})
        raise IllegalTransition(f"{frm.value} -> {to.value} is not allowed")
    now = utcnow()
    case.state = to
    field = _TIMESTAMPS.get(to)
    if field and getattr(case, field) is None:
        setattr(case, field, now)
    store.save_case(case)
    audit.append(case.case_id, EventType.STATE_CHANGED, actor, None,
                 {"from": frm.value, "to": to.value, "reason": reason})
    publish_case(case)
    if to in _METRIC_STATES:
        metrics.publish()
    return case
