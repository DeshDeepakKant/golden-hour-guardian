"""Desk: creates Tier-2 decisions, applies approved ones, closes the case."""
from __future__ import annotations

from typing import Any, Optional

from app import audit, brain_call, fsm, metrics, store, texts, tools
from app.bus import publish_case, publish_data
from app.contracts import (
    Action, Case, CaseState as S, Decision, DecisionStatus, EventType, OfficerDecisionIn, Tier, utcnow,
)
from app.policy import PolicyBlocked

ACTOR = "agent:desk"
FRAUD_DECISIONS = [Action.RAISE_DISPUTE, Action.EXTEND_HOLD, Action.SHARE_EVIDENCE_WITH_BANK]


class DecisionConflict(Exception):
    pass


async def request(case_id: str, action: Action, trigger: Optional[str] = None) -> Decision:
    case = store.get_case(case_id)
    rationale = await brain_call.call(case_id, "decision_rationale", case, action,
                                      default=f"Recommended action: {action.value}.")
    rationale = str(rationale or f"Recommended action: {action.value}.")
    if trigger:
        rationale = f"{rationale} {texts.TRIGGERS.get(trigger, trigger)}"
    case = store.get_case(case_id)    # reload after the await
    return tools.request_decision(case, action, rationale, ACTOR)


async def open_fraud_decisions(case_id: str) -> None:
    """EVIDENCE_READY -> AWAITING_OFFICER with the three standard fraud decisions."""
    for action in FRAUD_DECISIONS:
        await request(case_id, action)
    fsm.transition(store.get_case(case_id), S.AWAITING_OFFICER, ACTOR, "decisions requested from officer")


async def escalate(case_id: str, trigger: str, action: Action = Action.OFFICER_CALLBACK) -> Decision:
    """Verification stage ended without a safe automatic answer: officer decides."""
    decision = await request(case_id, action, trigger)
    case = store.get_case(case_id)
    fsm.transition(case, S.NO_RESPONSE_ESCALATED, ACTOR, f"escalated: {trigger}")
    fsm.transition(store.get_case(case_id), S.AWAITING_OFFICER, ACTOR, "waiting for officer")
    return decision


def apply(decision_id: str, body: OfficerDecisionIn) -> Decision:
    decision = store.get_decision(decision_id)
    if decision is None:
        raise LookupError(decision_id)
    if decision.status != DecisionStatus.PENDING:
        raise DecisionConflict(f"decision {decision_id} is already {decision.status.value}")
    case = store.get_case(decision.case_id)
    actor = f"human:{body.officer}"
    original = decision.model_copy()

    decision.status = DecisionStatus.APPROVED if body.approve else DecisionStatus.REJECTED
    decision.decided_by = body.officer
    decision.decided_at = utcnow()
    decision.note = body.note
    store.save_decision(decision)        # tools check policy against the persisted APPROVED decision

    result: dict[str, Any] = {}
    if body.approve:
        tool = tools.T2_TOOLS[decision.action]
        try:
            result = tool(case, actor, decision.decision_id) or {}
        except Exception:
            store.save_decision(original)    # nothing was applied: back to PENDING
            raise
    audit.append(case.case_id, EventType.DECISION_MADE, actor, Tier.T2_HUMAN,
                 {"phase": "officer_decision", "decision_id": decision.decision_id,
                  "action": decision.action.value, "approve": body.approve, "note": body.note})
    if decision.action == Action.EXTEND_HOLD:
        from app.agents import shield      # local import: shield -> sentinel; keep desk import-light
        if body.approve:
            shield.arm_expiry(case.case_id)            # the extended hold also ends on its own
        elif store.get_case(case.case_id).hold_active:
            tools.expire_hold(store.get_case(case.case_id), actor, "officer declined to extend the hold",
                              decision.decision_id)
    case = store.get_case(case.case_id)
    case.t_officer_decided = utcnow()
    store.save_case(case)
    publish_data("decision", decision.model_dump(mode="json"))
    publish_case(case)
    close_if_done(case.case_id)
    metrics.publish()
    return decision


def close_if_done(case_id: str) -> None:
    case = store.get_case(case_id)
    if case is None or case.state != S.AWAITING_OFFICER:
        return
    if store.list_decisions(case_id, DecisionStatus.PENDING):
        return
    fsm.transition(case, S.CLOSED, ACTOR, "no pending decisions")
    audit.append(case_id, EventType.CASE_CLOSED, ACTOR, None, {"state": S.CLOSED.value})
