from app import metrics, tools
from app.contracts import Case
from app import store
from tests.test_core_flow import respond
from tests.test_core_helpers import launch, wait_for, wait_state


def test_empty_metrics_use_baseline_config(client):
    m = metrics.summary()
    assert m.cases_total == 0 and m.median_t_protect_s is None and m.pct_protected_under_10min is None
    assert m.baseline_median_t_protect_s == 2100.0 and m.baseline_median_t_ready_s == 3900.0


def test_t_protect_computed_after_ato(client):
    cid = launch(client, "ato")
    wait_state(client, cid, "HELD_PENDING_VERIFY")
    wait_for(lambda: client.get("/victim/usr_ravi/pending").json())
    respond(client, cid, "NOT_ME")
    wait_state(client, cid, "AWAITING_OFFICER")
    m = client.get("/metrics/summary").json()
    assert m["cases_fraud_confirmed"] == 1
    assert 0 < m["median_t_protect_s"] < 60
    assert m["median_t_ready_s"] >= m["median_t_protect_s"]
    assert m["pct_protected_under_10min"] == 100.0
    assert m["t1_actions"] >= 5 and m["t2_decisions"] == 0 and m["t3_blocked"] == 0


def test_tier_counters(client):
    case = Case(case_id="case_m1", user_id="usr_ravi")
    store.save_case(case)
    try:
        tools.contact_payee(case, "agent:test")
    except Exception:
        pass
    assert metrics.summary().t3_blocked == 1
