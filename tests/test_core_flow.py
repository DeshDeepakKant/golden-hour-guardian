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
    r = client.post("/victim/respond", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def approve_all(client, cid, approve=True):
    for d in client.get(f"/cases/{cid}").json()["decisions"]:
        if d["status"] == "PENDING":
            r = client.post(f"/decisions/{d['decision_id']}",
                            json={"decision_id": d["decision_id"], "approve": approve, "note": "test"})
            assert r.status_code == 200, r.text


def test_ato_not_me_full_path(client):
    cid = launch(client, "ato")
    body = wait_state(client, cid, "HELD_PENDING_VERIFY")
    assert body["case"]["hold_active"] is True and body["case"]["risk_score"] >= 0.85
    wait_for(lambda: client.get("/victim/usr_ravi/pending").json())
    assert client.get("/victim/usr_ravi/pending").json()["variant"] == "verify"

    assert respond(client, cid, "NOT_ME")["state"] == "CONFIRMED_FRAUD"
    body = wait_state(client, cid, "AWAITING_OFFICER")
    assert {d["action"] for d in body["decisions"]} == {"raise_dispute", "extend_hold", "share_evidence_with_bank"}
    assert all(d["status"] == "PENDING" for d in body["decisions"])
    assert body["evidence"]["victim_name_masked"] == "R***"          # seed name is "Ravi (demo)"
    assert mask_name("Ravi Kumar (demo)") == "R*** K***" and mask_mobile("9800000021") == "98******21"
    assert body["evidence"]["mobile_masked"].startswith("90") and "*" in body["evidence"]["mobile_masked"]
    assert body["evidence"]["ncrp_fields"]["Sub-category"] == "UPI related"
    c = body["case"]
    assert c["hold_active"] is True and c["t_contained"] and c["t_evidence_ready"] and c["t_guided_1930"]
    types = event_types(body)
    for t in ("ALERT_RECEIVED", "TRIAGED", "HOLD_PLACED", "COMMS_SUPPRESSED", "VICTIM_CONTACTED", "VICTIM_REPLIED",
              "SESSION_REVOKED", "EVIDENCE_READY", "VICTIM_GUIDED_1930", "DECISION_REQUESTED", "LLM_FALLBACK_USED"):
        assert t in types, t
    assert client.get("/victim/usr_ravi/pending").json()["variant"] == "ncrp_guide"

    queue = client.get("/officer/queue").json()
    assert len(queue) == 3 and queue[0]["case"]["victim_name_masked"] == "R***"

    approve_all(client, cid)
    body = wait_state(client, cid, "CLOSED")
    assert all(d["status"] == "APPROVED" for d in body["decisions"])
    assert client.get(f"/audit/{cid}/verify").json()["ok"] is True
    assert client.get("/officer/queue").json() == []
    assert any(c["method"] == "raise_dispute" for c in repo.partner_calls())


def test_ato_yes_mine_is_untrusted_because_of_sim_change(client):
    cid = launch(client, "ato")
    wait_state(client, cid, "HELD_PENDING_VERIFY")
    wait_for(lambda: client.get("/victim/usr_ravi/pending").json())
    respond(client, cid, "YES_MINE")
    body = wait_state(client, cid, "AWAITING_OFFICER")
    assert body["case"]["hold_active"] is True            # NOT released automatically
    assert "POLICY_BLOCKED" in event_types(body) and "HOLD_RELEASED" not in event_types(body)
    assert [d["action"] for d in body["decisions"]] == ["release_hold_untrusted"]
    approve_all(client, cid)
    body = wait_state(client, cid, "CLOSED")
    assert body["case"]["hold_active"] is False and "HOLD_RELEASED" in event_types(body)


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


def test_noresponse_times_out_to_officer_and_hold_stays(client, monkeypatch):
    monkeypatch.setenv("GUARDIAN_VERIFY_TIMEOUT_S", "0.4")
    cid = launch(client, "noresponse")
    body = wait_state(client, cid, "AWAITING_OFFICER")
    assert "VERIFY_TIMEOUT" in event_types(body)
    assert body["case"]["hold_active"] is True
    assert [d["action"] for d in body["decisions"]] == ["officer_callback"]


def test_unsure_retries_once_then_escalates(client):
    cid = launch(client, "genuine")
    wait_state(client, cid, "VERIFYING")
    wait_for(lambda: client.get("/victim/usr_meena/pending").json())
    assert respond(client, cid, "UNSURE")["state"] == "VERIFYING"
    assert client.get("/victim/usr_meena/pending").json()["variant"] == "retry"
    assert respond(client, cid, "UNSURE")["state"] == "AWAITING_OFFICER"
    body = client.get(f"/cases/{cid}").json()
    assert [d["action"] for d in body["decisions"]] == ["officer_callback"]


def test_scripted_auto_reply_runs_unattended(client):
    r = client.post("/sim/scenario/ato?auto_reply=true&delay=0.3")
    cid = r.json()["case_id"]
    wait_state(client, cid, "AWAITING_OFFICER")
    assert client.get(f"/cases/{cid}").json()["case"]["t_contained"]


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


def test_late_reply_is_ignored(client):
    cid = launch(client, "ato")
    wait_state(client, cid, "HELD_PENDING_VERIFY")
    wait_for(lambda: client.get("/victim/usr_ravi/pending").json())
    respond(client, cid, "NOT_ME")
    wait_state(client, cid, "AWAITING_OFFICER")
    assert respond(client, cid, "YES_MINE")["state"] == "AWAITING_OFFICER"
    assert client.get(f"/cases/{cid}").json()["case"]["hold_active"] is True
    assert client.post("/victim/respond", json={"case_id": cid}).status_code == 422
    assert client.post("/victim/respond", json={"case_id": "case_nope", "answer": "NOT_ME"}).status_code == 404


def test_ncrp_ack(client):
    cid = launch(client, "ato")
    wait_state(client, cid, "HELD_PENDING_VERIFY")
    wait_for(lambda: client.get("/victim/usr_ravi/pending").json())
    respond(client, cid, "NOT_ME")
    wait_state(client, cid, "AWAITING_OFFICER")
    assert client.post("/victim/ncrp-ack", json={"case_id": cid, "ack_number": "<script>"}).status_code == 422
    assert client.post("/victim/ncrp-ack", json={"case_id": cid, "ack_number": "NCRP-2026-0042"}).json() == {"ok": True}
    body = client.get(f"/cases/{cid}").json()
    assert "NCRP_ACK_RECORDED" in event_types(body)
    assert client.get("/victim/usr_ravi/pending").json()["variant"] == "done"


def test_queued_marketing_push_is_suppressed(client, monkeypatch):
    cid = launch(client, "ato")
    wait_state(client, cid, "HELD_PENDING_VERIFY")
    real = partners.flush_due_pushes
    monkeypatch.setattr(partners, "flush_due_pushes", lambda now=None: real(utcnow() + timedelta(seconds=30)))
    assert tools.flush_marketing_queue() == 1
    assert any(c["method"] == "send_push" and c["result"] == "SUPPRESSED" for c in repo.partner_calls())
    body = client.get(f"/cases/{cid}").json()
    assert any(e["type"] == "COMMS_SUPPRESSED" and e["payload"].get("result") == "SUPPRESSED" for e in body["events"])


def test_hold_auto_expires_unless_fraud_confirmed(client, monkeypatch):
    monkeypatch.setitem(POLICY["hold"], "auto_expire_minutes", 0.015)   # ~0.9 s
    cid = launch(client, "noresponse")
    wait_state(client, cid, "HELD_PENDING_VERIFY")
    wait_for(lambda: client.get(f"/cases/{cid}").json()["case"]["hold_active"] is False, timeout=10)
    assert "HOLD_RELEASED" in event_types(client.get(f"/cases/{cid}").json())

    cid2 = launch(client, "ato")
    wait_for(lambda: client.get("/victim/usr_ravi/pending").json())
    respond(client, cid2, "NOT_ME")
    wait_state(client, cid2, "AWAITING_OFFICER")
    import time
    time.sleep(1.5)
    assert client.get(f"/cases/{cid2}").json()["case"]["hold_active"] is True    # confirmed fraud: stays


def test_reset_cancels_tasks_and_reseeds(client, monkeypatch):
    from app import orchestrator_tasks
    monkeypatch.setenv("GUARDIAN_VERIFY_TIMEOUT_S", "300")
    cid = launch(client, "noresponse")
    wait_state(client, cid, "HELD_PENDING_VERIFY")
    wait_for(lambda: client.get("/victim/usr_lakshmi/pending").json())
    assert orchestrator_tasks.active_count() >= 1
    assert client.post("/sim/reset").json() == {"ok": True}
    assert orchestrator_tasks.active_count() == 0
    assert client.get("/cases").json() == [] and client.get("/victim/usr_lakshmi/pending").json() is None
    launch(client, "genuine")      # world is usable again


def test_unknown_scenario_404_and_health(client):
    assert client.post("/sim/scenario/nope").status_code == 404
    assert client.get("/health").json() == {"ok": True, "llm": "fallback"}
