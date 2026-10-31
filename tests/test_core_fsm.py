import pytest

from app import audit, fsm, store
from app.contracts import Case, CaseState as S, EventType


def _case(state=S.NEW, origin="alert", cid="case_f1"):
    c = Case(case_id=cid, user_id="usr_meena", state=state, origin=origin)
    store.save_case(c)
    return c


@pytest.mark.parametrize("frm,to", [
    (S.NEW, S.CLOSED), (S.NEW, S.VERIFYING), (S.TRIAGED, S.CONTAINED), (S.VERIFYING, S.RELEASED),
    (S.DISMISSED, S.VERIFYING), (S.CLOSED, S.NEW), (S.CONFIRMED_FRAUD, S.RELEASED),
    (S.EVIDENCE_READY, S.CLOSED), (S.RELEASED, S.CONFIRMED_FRAUD), (S.AWAITING_OFFICER, S.CONTAINED),
])
def test_illegal_transitions_raise_and_log(client, frm, to):
    case = _case(frm)
    with pytest.raises(fsm.IllegalTransition):
        fsm.transition(case, to, "test", "nope")
    assert store.get_case(case.case_id).state == frm
    assert audit.list_events(case.case_id)[-1].type == EventType.POLICY_BLOCKED


def test_alert_origin_cannot_skip_verification(client):
    with pytest.raises(fsm.IllegalTransition):
        fsm.transition(_case(S.NEW, "alert"), S.CONFIRMED_FRAUD, "test")


def test_victim_report_origin_goes_straight_to_confirmed_fraud(client):
    case = fsm.transition(_case(S.NEW, "victim_report"), S.CONFIRMED_FRAUD, "test")
    assert case.state == S.CONFIRMED_FRAUD and case.t_verified is not None


def test_happy_path_sets_timestamps_and_logs(client):
    case = _case()
    path = [(S.TRIAGED, "t_triaged"), (S.HELD_PENDING_VERIFY, None), (S.CONFIRMED_FRAUD, "t_verified"),
            (S.CONTAINED, "t_contained"), (S.EVIDENCE_READY, "t_evidence_ready"),
            (S.AWAITING_OFFICER, None), (S.CLOSED, "t_closed")]
    for to, field in path:
        fsm.transition(case, to, "test")
        if field:
            assert getattr(case, field) is not None
    changes = [e for e in audit.list_events(case.case_id) if e.type == EventType.STATE_CHANGED]
    assert [e.payload["to"] for e in changes] == [p[0].value for p in path]


def test_every_state_is_covered_by_the_table():
    assert set(fsm.TRANSITIONS) == set(S)
