"""E2E: each of the five SPEC §9 scenarios reaches its SPEC §9 end state.

TestClient, LLM off (templates only). Victim replies go through POST /victim/respond, officer
decisions through POST /decisions/{id}. Every case must have a verifying audit chain.
"""
from datetime import datetime

from app.repo import repo
from mocks.scenarios import INJECTION_TEXT
from tests.test_core_helpers import event_types, launch, wait_for, wait_state


def respond(client, cid, answer=None, transcript=None, lang="en", channel="APP_TRUSTED_DEVICE"):
    body = {"case_id": cid, "lang": lang, "channel": channel}
    if answer:
        body["answer"] = answer
    if transcript:
        body["transcript"] = transcript
    headers = {}
    if channel == "APP_TRUSTED_DEVICE":   # the server only trusts the user's own device id (M2)
        uid = client.get(f"/cases/{cid}").json()["case"]["user_id"]
        headers["X-Guardian-Device"] = repo.user_profile(uid)["trusted_device"]
    r = client.post("/victim/respond", json=body, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def decide(client, decision, approve=True):
    did = decision["decision_id"]
    r = client.post(f"/decisions/{did}", json={"decision_id": did, "approve": approve, "note": "qa"})
    assert r.status_code == 200, r.text
    return r.json()


def approve_all(client, cid):
    for d in client.get(f"/cases/{cid}").json()["decisions"]:
        if d["status"] == "PENDING":
            decide(client, d)


def assert_audit_ok(client, cid):
    r = client.get(f"/audit/{cid}/verify").json()
    assert r["ok"] is True, r
    assert r["length"] > 0


def t_protect_s(case) -> float:
    t0 = datetime.fromisoformat(case["t_alert"].replace("Z", "+00:00"))
    t1 = datetime.fromisoformat(case["t_contained"].replace("Z", "+00:00"))
    return (t1 - t0).total_seconds()


def test_ato_end_state(client):
    """ato + NOT_ME: HELD -> CONFIRMED_FRAUD -> CONTAINED -> EVIDENCE_READY -> AWAITING_OFFICER (3) -> CLOSED."""
    cid = launch(client, "ato")
    body = wait_state(client, cid, "HELD_PENDING_VERIFY")
    case = body["case"]
    assert case["hold_active"] is True
    assert case["risk_score"] >= 0.85                       # SPEC §9: ~0.93
    codes = {s["code"] for s in case["signals"]}
    assert {"SIM_CHANGE_72H", "NEW_DEVICE"} <= codes, codes
    wait_for(lambda: client.get("/victim/usr_ravi/pending").json())
    assert client.get("/victim/usr_ravi/pending").json()["variant"] == "verify"

    assert respond(client, cid, "NOT_ME")["state"] == "CONFIRMED_FRAUD"
    body = wait_state(client, cid, "AWAITING_OFFICER")
    assert {d["action"] for d in body["decisions"]} == {"raise_dispute", "extend_hold", "share_evidence_with_bank"}
    assert all(d["status"] == "PENDING" for d in body["decisions"])
    assert body["case"]["t_contained"] and body["case"]["t_evidence_ready"] and body["case"]["t_guided_1930"]
    assert body["case"]["hold_active"] is True              # containment keeps the reversible hold
    assert body["evidence"] is not None and body["evidence"]["ncrp_fields"]["Sub-category"] == "UPI related"
    types = event_types(body)
    for t in ("HOLD_PLACED", "SESSION_REVOKED", "EVIDENCE_READY", "VICTIM_GUIDED_1930", "DECISION_REQUESTED"):
        assert t in types, t
    assert client.get("/victim/usr_ravi/pending").json()["variant"] == "ncrp_guide"

    # T_protect (SPEC §10): alert -> contained, headline target < 60 s (SPEC §12 step 3)
    tp = t_protect_s(body["case"])
    assert 0 <= tp < 60, tp

    # officer approves the dispute first, then the rest
    dispute = next(d for d in body["decisions"] if d["action"] == "raise_dispute")
    assert decide(client, dispute)["status"] == "APPROVED"
    assert any(c["method"] == "raise_dispute" for c in repo.partner_calls())
    approve_all(client, cid)
    body = wait_state(client, cid, "CLOSED")
    assert all(d["status"] == "APPROVED" for d in body["decisions"])
    assert_audit_ok(client, cid)
    assert client.get("/officer/queue").json() == []


def test_genuine_end_state(client):
    """genuine + YES_MINE on trusted device: VERIFYING -> RELEASED, no hold left, no decisions."""
    cid = launch(client, "genuine")
    body = wait_state(client, cid, "VERIFYING")
    assert body["case"]["hold_active"] is False
    assert 0.45 <= body["case"]["risk_score"] < 0.85        # SPEC §9: ~0.55, medium band
    wait_for(lambda: client.get("/victim/usr_meena/pending").json())
    assert respond(client, cid, "YES_MINE")["state"] == "RELEASED"
    body = client.get(f"/cases/{cid}").json()
    assert body["decisions"] == []
    assert body["case"]["hold_active"] is False
    assert body["case"]["t_contained"] is None              # not fraud: never contained
    assert client.get("/victim/usr_meena/pending").json()["variant"] == "released"
    assert client.get("/metrics/summary").json()["median_genuine_friction_s"] is not None
    assert_audit_ok(client, cid)


def test_inbound_end_state(client):
    """inbound (Hindi victim report): skips verification -> CONFIRMED_FRAUD -> same as ato."""
    cid = launch(client, "inbound")
    body = wait_state(client, cid, "AWAITING_OFFICER")
    case = body["case"]
    assert case["origin"] == "victim_report" and case["lang"] == "hi"
    assert len(body["decisions"]) == 3 and all(d["status"] == "PENDING" for d in body["decisions"])
    assert case["t_contained"] is not None                  # T_protect set for a fraud case
    assert "TRIAGED" not in event_types(body) and "VERIFY_TIMEOUT" not in event_types(body)
    tp = t_protect_s(case)
    assert 0 <= tp < 60, tp
    approve_all(client, cid)
    wait_state(client, cid, "CLOSED")
    assert_audit_ok(client, cid)


def test_noresponse_end_state(client, monkeypatch):
    """noresponse: hold stays within limit, verification times out, escalated to officer callback."""
    monkeypatch.setenv("GUARDIAN_VERIFY_TIMEOUT_S", "0.4")
    cid = launch(client, "noresponse")
    body = wait_state(client, cid, "AWAITING_OFFICER")
    assert "VERIFY_TIMEOUT" in event_types(body)
    assert body["case"]["hold_active"] is True
    assert body["case"]["hold_expires_at"] is not None
    assert [d["action"] for d in body["decisions"]] == ["officer_callback"]
    assert body["case"]["t_contained"] is None              # no confirmed fraud, no containment claim
    assert_audit_ok(client, cid)


def test_injection_end_state(client):
    """injection: ASKS_REFUND routed to officer callback, nothing auto-done."""
    cid = launch(client, "injection")
    body = wait_state(client, cid, "VERIFYING")
    assert body["case"]["hold_active"] is False
    wait_for(lambda: client.get("/victim/usr_kiran/pending").json())
    respond(client, cid, transcript=INJECTION_TEXT)
    body = wait_state(client, cid, "AWAITING_OFFICER")
    assert [d["action"] for d in body["decisions"]] == ["officer_callback"]
    types = event_types(body)
    assert "HOLD_RELEASED" not in types and "SESSION_REVOKED" not in types
    assert body["case"]["t_contained"] is None
    approve_all(client, cid)
    wait_state(client, cid, "CLOSED")
    assert_audit_ok(client, cid)


def test_fraud_cases_have_t_protect_in_metrics(client):
    cid = launch(client, "ato")
    wait_state(client, cid, "HELD_PENDING_VERIFY")
    wait_for(lambda: client.get("/victim/usr_ravi/pending").json())
    respond(client, cid, "NOT_ME")
    wait_state(client, cid, "AWAITING_OFFICER")
    m = client.get("/metrics/summary").json()
    assert m["cases_fraud_confirmed"] >= 1
    assert m["median_t_protect_s"] is not None and m["median_t_protect_s"] < 60
    assert m["baseline_median_t_protect_s"] > m["median_t_protect_s"]
