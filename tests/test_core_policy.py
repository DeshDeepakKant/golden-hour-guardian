"""Policy tiers: Tier 3 impossible, Tier 2 needs an approved decision for this case and action."""
import pytest

from app import audit, store, tools
from app.contracts import (
    ACTION_TIERS, Action, Case, Channel, Decision, DecisionStatus, EventType, Signal, SignalCode, Tier,
)
from app.policy import PolicyBlocked, check

TIER3_TOOLS = {
    Action.FREEZE_BENEFICIARY: tools.freeze_beneficiary,
    Action.FILE_POLICE_COMPLAINT: tools.file_police_complaint,
    Action.REQUEST_OTP_PIN: tools.request_otp_pin,
    Action.PROMISE_REFUND: tools.promise_refund,
    Action.CONTACT_PAYEE: tools.contact_payee,
}


def _case(case_id="case_t1", signals=None, **kw) -> Case:
    c = Case(case_id=case_id, user_id="usr_ravi", signals=signals or [], **kw)
    store.save_case(c)
    return c


def _decision(case_id, action, status=DecisionStatus.APPROVED, did="dec_t1") -> str:
    store.save_decision(Decision(decision_id=did, case_id=case_id, action=action, status=status, rationale="r"))
    return did


def _blocked_events(case_id):
    return [e for e in audit.list_events(case_id) if e.type == EventType.POLICY_BLOCKED]


def test_every_tier3_tool_raises_and_logs(client):
    assert {a for a, t in ACTION_TIERS.items() if t == Tier.T3_FORBIDDEN} == set(TIER3_TOOLS)
    for i, (action, tool) in enumerate(TIER3_TOOLS.items()):
        case = _case(f"case_t3_{i}")
        with pytest.raises(PolicyBlocked):
            tool(case, "agent:test")
        ev = _blocked_events(case.case_id)
        assert len(ev) == 1 and ev[0].payload["action"] == action.value and ev[0].tier == Tier.T3_FORBIDDEN


def test_tier3_blocked_even_with_an_approved_decision(client):
    case = _case()
    did = _decision(case.case_id, Action.FREEZE_BENEFICIARY)
    assert not check(Action.FREEZE_BENEFICIARY, case, "agent:test", did).allowed


def test_tier2_without_decision_is_blocked(client):
    case = _case()
    with pytest.raises(PolicyBlocked):
        tools.raise_dispute(case, "agent:test", None)
    assert len(_blocked_events(case.case_id)) == 1


@pytest.mark.parametrize("status", [DecisionStatus.PENDING, DecisionStatus.REJECTED])
def test_tier2_with_unapproved_decision_is_blocked(client, status):
    case = _case()
    did = _decision(case.case_id, Action.RAISE_DISPUTE, status)
    with pytest.raises(PolicyBlocked):
        tools.raise_dispute(case, "agent:test", did)


def test_tier2_with_wrong_action_or_wrong_case_is_blocked(client):
    case, other = _case("case_a"), _case("case_b")
    wrong_action = _decision(case.case_id, Action.EXTEND_HOLD, did="dec_wrong_action")
    with pytest.raises(PolicyBlocked):
        tools.raise_dispute(case, "agent:test", wrong_action)
    other_case = _decision(other.case_id, Action.RAISE_DISPUTE, did="dec_other_case")
    with pytest.raises(PolicyBlocked):
        tools.raise_dispute(case, "agent:test", other_case)
    with pytest.raises(PolicyBlocked):
        tools.raise_dispute(case, "agent:test", "dec_does_not_exist")


def test_tier2_with_approved_decision_runs_and_calls_partner(client):
    case = _case(txn_ids=["txn_x"])
    did = _decision(case.case_id, Action.RAISE_DISPUTE)
    result = tools.raise_dispute(case, "human:officer_demo", did)
    assert result["partner_ref"].startswith("DSP-")
    assert any(e.type == EventType.DECISION_MADE and e.payload["phase"] == "applied"
               for e in audit.list_events(case.case_id))


def test_release_hold_trusted_blocked_after_sim_change(client):
    sim = Signal(code=SignalCode.SIM_CHANGE_72H, weight=0.4)
    case = _case(signals=[sim], hold_active=True)
    with pytest.raises(PolicyBlocked):
        tools.release_hold_trusted(case, "agent:test")
    assert store.get_case(case.case_id).hold_active is True


def test_release_hold_trusted_blocked_on_untrusted_channel(client):
    case = _case(hold_active=True)
    with pytest.raises(PolicyBlocked):
        tools.release_hold_trusted(case, "agent:test", Channel.VOICE_REGISTERED_NO)
    case2 = _case("case_voice", hold_active=True, trusted_channel=Channel.VOICE_REGISTERED_NO)
    with pytest.raises(PolicyBlocked):
        tools.release_hold_trusted(case2, "agent:test")


def test_release_hold_trusted_allowed_on_trusted_channel(client):
    case = _case(hold_active=True)
    tools.release_hold_trusted(case, "agent:test")
    assert store.get_case(case.case_id).hold_active is False


def test_hold_beyond_policy_limit_needs_extend_hold(client):
    case = _case()
    with pytest.raises(PolicyBlocked):
        tools.place_temp_hold(case, "agent:test", minutes=121)
    tools.place_temp_hold(case, "agent:test", minutes=60)
    assert store.get_case(case.case_id).hold_active is True
