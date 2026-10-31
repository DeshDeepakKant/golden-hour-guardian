"""End-to-end flows through the HTTP API (LLM off: templates only)."""
from datetime import timedelta

import pytest

from app import tools
from app.agents.scribe import mask_mobile, mask_name
from app.repo import repo
from app.config import POLICY
from app.contracts import Action, utcnow
from mocks.partners import partners
from mocks.scenarios import INJECTION_TEXT
from tests.test_core_helpers import case_state, event_types, launch, wait_for, wait_state


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


def approve_all(client, cid, approve=True):
    for d in client.get(f"/cases/{cid}").json()["decisions"]:
        if d["status"] == "PENDING":
            r = client.post(f"/decisions/{d['decision_id']}",
                            json={"decision_id": d["decision_id"], "approve": approve, "note": "test"})
            assert r.status_code == 200, r.text




def test_genuine_yes_mine_is_released(client):
    cid = launch(client, "genuine")
    body = wait_state(client, cid, "VERIFYING")
    assert body["case"]["hold_active"] is False and 0.4 <= body["case"]["risk_score"] < 0.85
    wait_for(lambda: client.get("/victim/usr_meena/pending").json())
    assert respond(client, cid, "YES_MINE")["state"] == "RELEASED"
    body = client.get(f"/cases/{cid}").json()
    assert body["decisions"] == [] and "HOLD_RELEASED" in event_types(body)
    assert client.get("/victim/usr_meena/pending").json()["variant"] == "released"
    assert client.get("/metrics/summary").json()["median_genuine_friction_s"] is not None


def test_injection_transcript_never_auto_acts(client):
    cid = launch(client, "injection")
    wait_state(client, cid, "VERIFYING")
    wait_for(lambda: client.get("/victim/usr_kiran/pending").json())
    respond(client, cid, transcript=INJECTION_TEXT)
    body = wait_state(client, cid, "AWAITING_OFFICER")
    assert [d["action"] for d in body["decisions"]] == ["officer_callback"]
    assert "refund" in body["decisions"][0]["rationale"].lower()
    types = event_types(body)
    assert "HOLD_RELEASED" not in types and "SESSION_REVOKED" not in types
    assert body["case"]["t_contained"] is None
    assert all(e["payload"].get("action") not in ("raise_dispute",) for e in body["events"])
    approve_all(client, cid)
    wait_state(client, cid, "CLOSED")


def test_inbound_victim_report_goes_straight_to_confirmed_fraud(client):
    r = client.post("/webhooks/victim-report", json={
        "user_id": "usr_arjun", "channel": "app", "lang": "hi", "text": "मेरे खाते से पैसे कट गए"})
    assert r.status_code == 202
    cid = r.json()["case_id"]
    body = wait_state(client, cid, "AWAITING_OFFICER")
    assert body["case"]["origin"] == "victim_report"
    types = event_types(body)
    assert "VICTIM_REPORT_RECEIVED" in types and "VICTIM_CONTACTED" in types   # protected prompt only
    assert "TRIAGED" not in types and "VERIFY_TIMEOUT" not in types
    assert len(body["decisions"]) == 3 and body["case"]["t_contained"]


def test_inbound_scenario(client):
    cid = launch(client, "inbound")
    body = wait_state(client, cid, "AWAITING_OFFICER")
    assert body["case"]["lang"] == "hi" and len(body["decisions"]) == 3



def test_unsure_retries_once_then_escalates(client):
    cid = launch(client, "genuine")
    wait_state(client, cid, "VERIFYING")
    wait_for(lambda: client.get("/victim/usr_meena/pending").json())
    assert respond(client, cid, "UNSURE")["state"] == "VERIFYING"
    assert client.get("/victim/usr_meena/pending").json()["variant"] == "retry"
    assert respond(client, cid, "UNSURE")["state"] == "AWAITING_OFFICER"
    body = client.get(f"/cases/{cid}").json()
    assert [d["action"] for d in body["decisions"]] == ["officer_callback"]


def test_alert_is_idempotent_and_unknown_user_404(client):
    alert = {"alert_id": "alr_dup", "user_id": "usr_kiran", "score": 0.2}
    a = client.post("/webhooks/fraud-alert", json=alert)
    b = client.post("/webhooks/fraud-alert", json=alert)
    assert a.status_code == b.status_code == 202 and a.json() == b.json()
    assert len(client.get("/cases").json()) == 1
    assert client.post("/webhooks/fraud-alert", json={**alert, "alert_id": "x", "user_id": "usr_nobody"}).status_code == 404


def test_low_score_alert_is_dismissed_and_closed(client):
    r = client.post("/webhooks/fraud-alert", json={"alert_id": "alr_low", "user_id": "usr_kiran", "score": 0.1})
    body = wait_state(client, r.json()["case_id"], "CLOSED")
    assert "VICTIM_CONTACTED" not in event_types(body) and body["case"]["hold_active"] is False


def test_decision_endpoint_errors(client):
    assert client.post("/decisions/dec_nope", json={"decision_id": "dec_nope", "approve": True}).status_code == 404
    cid = launch(client, "injection")
    wait_state(client, cid, "VERIFYING")
    wait_for(lambda: client.get("/victim/usr_kiran/pending").json())
    respond(client, cid, transcript=INJECTION_TEXT)
    body = wait_state(client, cid, "AWAITING_OFFICER")
    did = body["decisions"][0]["decision_id"]
    ok = client.post(f"/decisions/{did}", json={"decision_id": did, "approve": False})
    assert ok.status_code == 200 and ok.json()["status"] == "REJECTED"
    assert client.post(f"/decisions/{did}", json={"decision_id": did, "approve": True}).status_code == 409


def test_unknown_scenario_404_and_health(client):
    assert client.post("/sim/scenario/nope").status_code == 404
    assert client.get("/health").json() == {"ok": True, "llm": "fallback"}
