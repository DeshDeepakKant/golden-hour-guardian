"""Red team: policy gate. Tier 3 is never allowed; Tier 2 needs this case's APPROVED decision for this action.

Uses the `client` fixture only for a seeded tmp DB (store / audit / repo are DB-backed).
"""
import pytest

from app import audit, policy, store, tools
from app.config import POLICY
from app.contracts import (
    ACTION_TIERS, Action, Case, Channel, Decision, DecisionStatus, EventType, Signal, SignalCode, Tier,
)
from app.policy import PolicyBlocked
from app.repo import repo

TIER3 = {
    Action.FREEZE_BENEFICIARY: tools.freeze_beneficiary,
    Action.FILE_POLICE_COMPLAINT: tools.file_police_complaint,
    Action.REQUEST_OTP_PIN: tools.request_otp_pin,
    Action.PROMISE_REFUND: tools.promise_refund,
    Action.CONTACT_PAYEE: tools.contact_payee,
}
TIER2 = dict(tools.T2_TOOLS)
SIM_SIGNAL = Signal(code=SignalCode.SIM_CHANGE_72H, weight=0.5, detail="sim changed 2h ago")


def _case(cid, signals=None, channel=Channel.APP_TRUSTED_DEVICE, user="usr_meena"):
    c = Case(case_id=cid, user_id=user, signals=signals or [], trusted_channel=channel)
    store.save_case(c)
    return c


def _decision(case_id, action, status, did):
    store.save_decision(Decision(decision_id=did, case_id=case_id, action=action, status=status, rationale="qa"))
    return did


def _blocked(case_id):
    return [e for e in audit.list_events(case_id) if e.type == EventType.POLICY_BLOCKED]


def _partner_count():
    return len(repo.partner_calls(limit=100000))


# ---------------------------------------------------------------- Tier 3
def test_tier3_contract_set_matches_tools():
    assert {a for a, t in ACTION_TIERS.items() if t == Tier.T3_FORBIDDEN} == set(TIER3)


@pytest.mark.parametrize("action", list(TIER3))
def test_tier3_tool_raises_and_logs(client, action):
    case = _case(f"case_rt3_{action.value}")
    before = _partner_count()
    with pytest.raises(PolicyBlocked):
        TIER3[action](case, "agent:redteam")
    ev = _blocked(case.case_id)
    assert ev, "POLICY_BLOCKED not logged"
    assert ev[-1].payload["action"] == action.value and ev[-1].payload["tier"] == 3
    assert _partner_count() == before                       # no partner call happened


@pytest.mark.parametrize("action", list(TIER3))
def test_tier3_cannot_be_unlocked_by_approved_decision(client, action):
    case = _case(f"case_rt3u_{action.value}")
    did = _decision(case.case_id, action, DecisionStatus.APPROVED, f"dec_rt3_{action.value}")
    result = policy.check(action, case, "agent:redteam", did, log=False)
    assert result.allowed is False and result.tier == Tier.T3_FORBIDDEN


# ---------------------------------------------------------------- Tier 2
@pytest.mark.parametrize("action", list(TIER2))
def test_tier2_without_decision_blocked(client, action):
    case = _case(f"case_rt2n_{action.value}")
    before = _partner_count()
    with pytest.raises(PolicyBlocked):
        TIER2[action](case, "human:redteam", None)
    assert _blocked(case.case_id), "POLICY_BLOCKED not logged"
    assert _partner_count() == before


@pytest.mark.parametrize("action", list(TIER2))
@pytest.mark.parametrize("status", [DecisionStatus.REJECTED, DecisionStatus.PENDING])
def test_tier2_rejected_or_pending_decision_blocked(client, action, status):
    case = _case(f"case_rt2r_{action.value}_{status.value}")
    did = _decision(case.case_id, action, status, f"dec_rt2r_{action.value}_{status.value}")
    before = _partner_count()
    with pytest.raises(PolicyBlocked):
        TIER2[action](case, "human:redteam", did)
    assert _blocked(case.case_id)
    assert _partner_count() == before


@pytest.mark.parametrize("action", list(TIER2))
def test_tier2_other_cases_approved_decision_blocked(client, action):
    owner = _case(f"case_rt2o_owner_{action.value}")
    intruder = _case(f"case_rt2o_other_{action.value}", user="usr_meena")
    did = _decision(owner.case_id, action, DecisionStatus.APPROVED, f"dec_rt2o_{action.value}")
    before = _partner_count()
    with pytest.raises(PolicyBlocked) as exc:
        TIER2[action](intruder, "human:redteam", did)
    assert "different case" in exc.value.result.reason
    assert _blocked(intruder.case_id)
    assert _partner_count() == before


@pytest.mark.parametrize("action", list(TIER2))
def test_tier2_approved_decision_for_other_action_blocked(client, action):
    case = _case(f"case_rt2a_{action.value}")
    other = next(a for a in TIER2 if a != action)
    did = _decision(case.case_id, other, DecisionStatus.APPROVED, f"dec_rt2a_{action.value}")
    with pytest.raises(PolicyBlocked):
        TIER2[action](case, "human:redteam", did)
    assert _blocked(case.case_id)


@pytest.mark.parametrize("action", list(TIER2))
def test_tier2_control_approved_same_case_same_action_allowed(client, action):
    """Positive control: the gate opens for the right decision, so the blocks above are meaningful."""
    case = _case(f"case_rt2c_{action.value}", signals=[SIM_SIGNAL])
    did = _decision(case.case_id, action, DecisionStatus.APPROVED, f"dec_rt2c_{action.value}")
    # Gate opened: no PolicyBlocked raised, no POLICY_BLOCKED logged. Some Tier-2 tools return None.
    TIER2[action](case, "human:redteam", did)
    assert _blocked(case.case_id) == []


# ---------------------------------------------------------------- hold rules (Tier 1 hard rules)
def test_release_hold_trusted_after_sim_change_blocked(client):
    case = _case("case_rt_sim", signals=[SIM_SIGNAL])
    with pytest.raises(PolicyBlocked):
        tools.release_hold_trusted(case, "agent:redteam", channel=Channel.APP_TRUSTED_DEVICE)
    assert _blocked(case.case_id)
    assert policy.check(Action.RELEASE_HOLD_TRUSTED, case, "agent:redteam", channel=Channel.APP_TRUSTED_DEVICE,
                        log=False).allowed is False


def test_release_hold_trusted_on_registered_voice_blocked(client):
    case = _case("case_rt_voice")
    with pytest.raises(PolicyBlocked):
        tools.release_hold_trusted(case, "agent:redteam", channel=Channel.VOICE_REGISTERED_NO)
    assert _blocked(case.case_id)


def test_release_hold_trusted_control_without_sim_change_allowed(client):
    case = _case("case_rt_ctrl")
    assert policy.check(Action.RELEASE_HOLD_TRUSTED, case, "agent:redteam", channel=Channel.APP_TRUSTED_DEVICE,
                        log=False).allowed is True


def test_hold_over_limit_needs_officer(client):
    case = _case("case_rt_hold")
    limit = POLICY["hold"]["max_without_officer_minutes"]
    with pytest.raises(PolicyBlocked):
        tools.place_temp_hold(case, "agent:redteam", minutes=limit + 1)
    assert _blocked(case.case_id)
