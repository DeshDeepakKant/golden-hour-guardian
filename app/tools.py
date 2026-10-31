"""The ONLY module that calls mocks.partners.

Every tool: policy.require -> (partner call) -> state/audit -> bus. Tier-3 tools only ever raise
PolicyBlocked, so red-team tests can call them and see the POLICY_BLOCKED event.
"""
from __future__ import annotations

import math
import os
from datetime import timedelta
from typing import Any, Optional

from app import audit, pending, policy, store
from app.bus import publish_case, publish_data
from app.config import POLICY
from app.contracts import (
    Action, Case, Channel, Decision, EventType, Tier, EvidencePack, utcnow,
)
from app.policy import PolicyBlocked  # noqa: F401  (re-exported)
from app.repo import repo
from app.util import new_id
from mocks.partners import partners

_SUPPRESSED: dict[str, Any] = {}   # user_id -> suppression expiry (for Conductor-lite bookkeeping)


def reset() -> None:
    _SUPPRESSED.clear()


def marketing_suppressed(user_id: str) -> bool:
    until = _SUPPRESSED.get(user_id)
    return until is not None and utcnow() < until


# ============================================================ Tier 1 tools
def place_temp_hold(case: Case, actor: str = "agent:shield", minutes: Optional[float] = None) -> str:
    store.refresh(case)
    minutes = minutes if minutes is not None else POLICY["hold"]["auto_expire_minutes"]
    policy.require(Action.PLACE_TEMP_HOLD, case, actor, minutes=minutes)
    ref = partners.place_hold(case.user_id, max(1, math.ceil(minutes)))
    case.hold_active = True
    case.hold_expires_at = utcnow() + timedelta(minutes=minutes)
    store.save_case(case)
    audit.append(case.case_id, EventType.HOLD_PLACED, actor, Tier.T1_AUTO,
                 {"minutes": minutes, "partner_ref": ref, "expires_at": case.hold_expires_at.isoformat(),
                  "scope": "victim's own outgoing payments only"})
    publish_case(case)
    return ref


def release_hold_trusted(case: Case, actor: str = "agent:shield",
                         channel: Channel = Channel.APP_TRUSTED_DEVICE) -> None:
    store.refresh(case)
    policy.require(Action.RELEASE_HOLD_TRUSTED, case, actor, channel=channel)
    _release(case, actor, Tier.T1_AUTO, "victim confirmed on trusted channel")


def release_hold_untrusted(case: Case, actor: str, decision_id: str) -> None:
    store.refresh(case)
    policy.require(Action.RELEASE_HOLD_UNTRUSTED, case, actor, decision_id)
    _release(case, actor, Tier.T2_HUMAN, "officer approved release (untrusted channel)", decision_id)


def expire_hold(case: Case, actor: str = "agent:shield", reason: str = "hold auto-expired",
                decision_id: Optional[str] = None) -> None:
    """Ending a hold (auto-expiry, or an officer refusing to extend it). Only ever loosens."""
    store.refresh(case)
    policy.require(Action.PLACE_TEMP_HOLD, case, actor)
    _release(case, actor, Tier.T1_AUTO, reason, decision_id)


def _release(case: Case, actor: str, tier: Tier, why: str, decision_id: Optional[str] = None) -> None:
    was_active = case.hold_active
    if was_active:
        partners.release_hold(case.user_id)
    case.hold_active = False
    case.hold_expires_at = None
    store.save_case(case)
    audit.append(case.case_id, EventType.HOLD_RELEASED, actor, tier,
                 {"reason": why, "hold_was_active": was_active, "decision_id": decision_id})
    publish_case(case)


def revoke_session(case: Case, actor: str, device_id: str) -> None:
    store.refresh(case)
    policy.require(Action.REVOKE_SESSION, case, actor)
    partners.revoke_session(case.user_id, device_id)
    repo.mark_device_revoked(device_id)
    audit.append(case.case_id, EventType.SESSION_REVOKED, actor, Tier.T1_AUTO, {"device_id": device_id})


def suppress_marketing(case: Case, actor: str = "agent:shield", minutes: Optional[int] = None) -> None:
    store.refresh(case)
    policy.require(Action.SUPPRESS_MARKETING, case, actor)
    minutes = minutes or POLICY.get("marketing_suppression_minutes", 1440)
    partners.suppress_marketing(case.user_id, minutes)
    _SUPPRESSED[case.user_id] = utcnow() + timedelta(minutes=minutes)
    audit.append(case.case_id, EventType.COMMS_SUPPRESSED, actor, Tier.T1_AUTO,
                 {"minutes": minutes, "scope": "marketing and cross-sell messages to this customer"})


def flush_marketing_queue() -> int:
    """Send queued marketing pushes that are due (mockworld queue). SUPPRESSED ones are logged on the case."""
    before = repo.last_partner_seq()
    n = partners.flush_due_pushes()
    for call in repo.partner_calls_since(before):
        if call["method"] != "send_push" or call.get("result") != "SUPPRESSED":
            continue
        import json
        user_id = json.loads(call["args"]).get("user_id")
        case = store.latest_open_case_for_user(user_id) if user_id else None
        if case:
            audit.append(case.case_id, EventType.COMMS_SUPPRESSED, "agent:shield", Tier.T1_AUTO,
                         {"category": "marketing", "result": "SUPPRESSED",
                          "note": "queued marketing push held while the case is open"})
    return n


def notify_victim(case: Case, actor: str, prompt: dict[str, Any],
                  event_type: EventType = EventType.VICTIM_CONTACTED) -> None:
    store.refresh(case)
    policy.require(Action.NOTIFY_VICTIM, case, actor)
    pending.set_prompt(case.user_id, prompt)
    # push is a wake-up only; the text lives in the app (and never asks for secrets)
    partners.send_push(case.user_id, {"category": "security", "title": "Guardian security alert",
                                      "body": "Open Guardian to review a recent payment."})
    if prompt.get("variant") in ("verify", "retry") and case.t_victim_contacted is None:
        case.t_victim_contacted = utcnow()
        store.save_case(case)
        publish_case(case)
    audit.append(case.case_id, event_type, actor, Tier.T1_AUTO,
                 {"variant": prompt.get("variant"), "messages": prompt.get("messages", [])})
    publish_data("victim_prompt", prompt, case.user_id)


def guide_ncrp(case: Case, actor: str, prompt: dict[str, Any]) -> None:
    store.refresh(case)
    policy.require(Action.GUIDE_NCRP, case, actor)
    pending.set_prompt(case.user_id, prompt)
    if case.t_guided_1930 is None:
        case.t_guided_1930 = utcnow()
        store.save_case(case)
    audit.append(case.case_id, EventType.VICTIM_GUIDED_1930, actor, Tier.T1_AUTO,
                 {"steps": prompt.get("messages", []), "helpline": "1930"})
    publish_data("victim_prompt", prompt, case.user_id)
    publish_case(case)
    from app import metrics
    metrics.publish()


def build_evidence_pack(case: Case, pack: EvidencePack, actor: str = "agent:scribe") -> None:
    policy.require(Action.BUILD_EVIDENCE_PACK, case, actor)
    store.save_evidence(pack)
    audit.append(case.case_id, EventType.EVIDENCE_READY, actor, Tier.T1_AUTO,
                 {"txn_count": len(pack.txns), "total_amount_paise": pack.total_amount_paise,
                  "payee_vpas": pack.payee_vpas})


def request_decision(case: Case, action: Action, rationale: str, actor: str = "agent:desk") -> Decision:
    policy.require(Action.REQUEST_DECISION, case, actor)
    decision = Decision(decision_id=new_id("dec"), case_id=case.case_id, action=action, rationale=rationale)
    store.save_decision(decision)
    audit.append(case.case_id, EventType.DECISION_REQUESTED, actor, Tier.T1_AUTO,
                 {"decision_id": decision.decision_id, "action": action.value})
    publish_data("decision", decision.model_dump(mode="json"))
    return decision


# ============================================================ Tier 2 tools
def _applied(case: Case, actor: str, action: Action, decision_id: str, **extra: Any) -> dict[str, Any]:
    result = {"phase": "applied", "action": action.value, "decision_id": decision_id, **extra}
    audit.append(case.case_id, EventType.DECISION_MADE, actor, Tier.T2_HUMAN, result)
    return result


def raise_dispute(case: Case, actor: str, decision_id: str) -> dict[str, Any]:
    store.refresh(case)
    policy.require(Action.RAISE_DISPUTE, case, actor, decision_id)
    ref = partners.raise_dispute(case.txn_ids, f"EVID-{case.case_id}")
    return _applied(case, actor, Action.RAISE_DISPUTE, decision_id, partner_ref=ref, txn_ids=case.txn_ids)


def extend_hold(case: Case, actor: str, decision_id: str, minutes: Optional[int] = None) -> dict[str, Any]:
    store.refresh(case)
    policy.require(Action.EXTEND_HOLD, case, actor, decision_id)
    env = os.environ.get("GUARDIAN_HOLD_EXTEND_S")      # test override of the extension length
    minutes = minutes or (float(env) / 60 if env else POLICY["hold"].get("extend_minutes", 1440))
    ref = partners.place_hold(case.user_id, max(1, math.ceil(minutes)))
    case.hold_active = True
    case.hold_expires_at = utcnow() + timedelta(minutes=minutes)
    store.save_case(case)
    audit.append(case.case_id, EventType.HOLD_PLACED, actor, Tier.T2_HUMAN,
                 {"extended": True, "minutes": minutes, "partner_ref": ref, "decision_id": decision_id,
                  "expires_at": case.hold_expires_at.isoformat()})
    publish_case(case)
    return _applied(case, actor, Action.EXTEND_HOLD, decision_id, partner_ref=ref, minutes=minutes)


def share_evidence_with_bank(case: Case, actor: str, decision_id: str) -> dict[str, Any]:
    store.refresh(case)
    policy.require(Action.SHARE_EVIDENCE_WITH_BANK, case, actor, decision_id)
    return _applied(case, actor, Action.SHARE_EVIDENCE_WITH_BANK, decision_id,
                    reference=f"NODAL-{new_id('ref')[4:].upper()}",
                    note="simulated: evidence pack made available to the bank nodal officer")


def officer_callback(case: Case, actor: str, decision_id: str) -> dict[str, Any]:
    store.refresh(case)
    policy.require(Action.OFFICER_CALLBACK, case, actor, decision_id)
    return _applied(case, actor, Action.OFFICER_CALLBACK, decision_id,
                    note="a human officer calls the victim; Guardian makes no calls")


def restore_access(case: Case, actor: str, decision_id: str) -> dict[str, Any]:
    store.refresh(case)
    policy.require(Action.RESTORE_ACCESS, case, actor, decision_id)
    return _applied(case, actor, Action.RESTORE_ACCESS, decision_id,
                    note="recorded: access restoration approved; executed in the bank's system")


def flag_payee_internal(case: Case, actor: str, decision_id: str) -> dict[str, Any]:
    store.refresh(case)
    policy.require(Action.FLAG_PAYEE_INTERNAL, case, actor, decision_id)
    payees = sorted({t.payee_vpa for t in repo.get_txns(case.txn_ids)})
    return _applied(case, actor, Action.FLAG_PAYEE_INTERNAL, decision_id, payees=payees,
                    note="recorded: internal watch flag only; the payee account is never frozen or contacted")


def refund_or_credit(case: Case, actor: str, decision_id: str) -> dict[str, Any]:
    store.refresh(case)
    policy.require(Action.REFUND_OR_CREDIT, case, actor, decision_id)
    return _applied(case, actor, Action.REFUND_OR_CREDIT, decision_id,
                    note="recorded: liability decision by the officer; no money moves from Guardian")


# ============================================================ Tier 3: impossible
def _forbidden(action: Action, case: Case, actor: str) -> None:
    policy.require(action, case, actor)      # always raises PolicyBlocked for Tier 3
    raise PolicyBlocked(policy.PolicyResult(allowed=False, tier=Tier.T3_FORBIDDEN, reason="forbidden"), action)


def freeze_beneficiary(case: Case, actor: str = "agent:unknown", **_: Any) -> None:
    _forbidden(Action.FREEZE_BENEFICIARY, case, actor)


def file_police_complaint(case: Case, actor: str = "agent:unknown", **_: Any) -> None:
    _forbidden(Action.FILE_POLICE_COMPLAINT, case, actor)


def request_otp_pin(case: Case, actor: str = "agent:unknown", **_: Any) -> None:
    _forbidden(Action.REQUEST_OTP_PIN, case, actor)


def promise_refund(case: Case, actor: str = "agent:unknown", **_: Any) -> None:
    _forbidden(Action.PROMISE_REFUND, case, actor)


def contact_payee(case: Case, actor: str = "agent:unknown", **_: Any) -> None:
    _forbidden(Action.CONTACT_PAYEE, case, actor)


T2_TOOLS = {
    Action.RAISE_DISPUTE: raise_dispute,
    Action.EXTEND_HOLD: extend_hold,
    Action.RELEASE_HOLD_UNTRUSTED: release_hold_untrusted,
    Action.SHARE_EVIDENCE_WITH_BANK: share_evidence_with_bank,
    Action.REFUND_OR_CREDIT: refund_or_credit,
    Action.RESTORE_ACCESS: restore_access,
    Action.FLAG_PAYEE_INTERNAL: flag_payee_internal,
    Action.OFFICER_CALLBACK: officer_callback,
}
