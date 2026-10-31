"""Policy engine: the single gate every action goes through.

Tier 3 -> always denied (+ POLICY_BLOCKED). Tier 2 -> denied unless `decision_id` is an APPROVED
decision for this case AND this action. Tier 1 -> allowed, except the hard rules below.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app import audit, store
from app.config import POLICY
from app.contracts import (
    ACTION_TIERS, Action, Case, Channel, DecisionStatus, EventType, SignalCode, Tier,
)


class PolicyResult(BaseModel):
    allowed: bool
    tier: Tier
    reason: str


class PolicyBlocked(Exception):
    def __init__(self, result: PolicyResult, action: Optional[Action] = None) -> None:
        super().__init__(result.reason)
        self.result = result
        self.action = action


def _evaluate(action: Action, case: Case, decision_id: Optional[str], channel: Optional[Channel],
              minutes: Optional[float]) -> PolicyResult:
    tier = ACTION_TIERS.get(action)
    if tier is None:
        return PolicyResult(allowed=False, tier=Tier.T3_FORBIDDEN, reason=f"unknown action {action!r}")

    if tier == Tier.T3_FORBIDDEN:
        return PolicyResult(allowed=False, tier=tier,
                            reason=f"{action.value} is forbidden: Guardian never does this, in code")

    if tier == Tier.T2_HUMAN:
        if not decision_id:
            return PolicyResult(allowed=False, tier=tier, reason=f"{action.value} needs an approved officer decision")
        decision = store.get_decision(decision_id)
        if decision is None:
            return PolicyResult(allowed=False, tier=tier, reason=f"decision {decision_id} not found")
        if decision.case_id != case.case_id:
            return PolicyResult(allowed=False, tier=tier, reason="decision belongs to a different case")
        if decision.action != action:
            return PolicyResult(allowed=False, tier=tier,
                                reason=f"decision {decision_id} approves {decision.action.value}, not {action.value}")
        if decision.status != DecisionStatus.APPROVED:
            return PolicyResult(allowed=False, tier=tier,
                                reason=f"decision {decision_id} is {decision.status.value}, not APPROVED")
        return PolicyResult(allowed=True, tier=tier, reason="approved by officer decision")

    # Tier 1 with hard rules
    if action == Action.RELEASE_HOLD_TRUSTED:
        if any(s.code == SignalCode.SIM_CHANGE_72H for s in case.signals):
            return PolicyResult(allowed=False, tier=tier,
                                reason="SIM changed in the last 72 h: a yes on this channel is not trusted; "
                                       "officer must approve the release")
        if case.trusted_channel != Channel.APP_TRUSTED_DEVICE:
            return PolicyResult(allowed=False, tier=tier,
                                reason="case channel is not the trusted device; officer must approve the release")
        if channel is not None and channel != Channel.APP_TRUSTED_DEVICE:
            return PolicyResult(allowed=False, tier=tier,
                                reason="reply did not arrive on the trusted device; officer must approve the release")
    if action == Action.PLACE_TEMP_HOLD and minutes is not None:
        limit = POLICY["hold"]["max_without_officer_minutes"]
        if minutes > limit:
            return PolicyResult(allowed=False, tier=tier,
                                reason=f"hold of {minutes} min exceeds {limit} min; needs EXTEND_HOLD approval")
    return PolicyResult(allowed=True, tier=tier, reason="tier 1: autonomous")


def check(action: Action, case: Case, actor: str, decision_id: Optional[str] = None, *,
          channel: Optional[Channel] = None, minutes: Optional[float] = None,
          log: bool = True) -> PolicyResult:
    result = _evaluate(action, case, decision_id, channel, minutes)
    if not result.allowed and log:
        audit.append(case.case_id, EventType.POLICY_BLOCKED, actor, result.tier,
                     {"action": action.value, "tier": int(result.tier), "reason": result.reason,
                      "decision_id": decision_id})
    return result


def require(action: Action, case: Case, actor: str, decision_id: Optional[str] = None, **kw) -> PolicyResult:
    """check() then raise PolicyBlocked when denied."""
    result = check(action, case, actor, decision_id, **kw)
    if not result.allowed:
        raise PolicyBlocked(result, action)
    return result
