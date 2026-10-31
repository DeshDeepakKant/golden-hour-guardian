"""REVIEW.md M3 (fraud holds end), M4 (victim prompt never waits on the officer LLM), S2 (no digits stored)."""
import asyncio
import threading
import time

from app import brain_call
from app.brain.api import Brain
from tests.test_core_helpers import event_types, launch, wait_for, wait_state

DEVICE = {"X-Guardian-Device": "dev_ravi_phone"}     # seed trusted device for usr_meena


def _case(client, cid):
    return client.get(f"/cases/{cid}").json()


def _to_officer(client):
    cid = launch(client, "inbound")
    # "inbound" (Hindi victim report) goes directly to AWAITING_OFFICER without verification
    return wait_state(client, cid, "AWAITING_OFFICER")


def _decide(client, body, action, approve):
    d = next(d for d in body["decisions"] if d["action"] == action)
    r = client.post(f"/decisions/{d['decision_id']}",
                    json={"decision_id": d["decision_id"], "approve": approve, "note": "test"})
    assert r.status_code == 200, r.text


def _releases(body):
    return [e["payload"] for e in body["events"] if e["type"] == "HOLD_RELEASED"]


# ---------------------------------------------------------------- M3
def test_rejected_extension_releases_hold_and_case_closes_clean(client):
    body = _to_officer(client)
    cid = body["case"]["case_id"]
    assert body["case"]["hold_active"] is True
    _decide(client, body, "extend_hold", approve=False)
    body = _case(client, cid)
    assert body["case"]["hold_active"] is False
    assert _releases(body)[-1]["reason"] == "officer declined to extend the hold"
    for action in ("raise_dispute", "share_evidence_with_bank"):
        _decide(client, body, action, approve=False)
    body = wait_state(client, cid, "CLOSED")
    assert body["case"]["hold_active"] is False and body["case"]["hold_expires_at"] is None


def test_fraud_hold_expires_at_max_without_approval(client, monkeypatch):
    monkeypatch.setenv("GUARDIAN_HOLD_MAX_S", "1.0")
    body = _to_officer(client)
    cid = body["case"]["case_id"]
    wait_for(lambda: _case(client, cid)["case"]["hold_active"] is False, timeout=10)
    assert "without an officer-approved extension" in _releases(_case(client, cid))[-1]["reason"]


def test_approved_extension_keeps_hold_past_max(client, monkeypatch):
    monkeypatch.setenv("GUARDIAN_HOLD_MAX_S", "1.5")
    body = _to_officer(client)
    cid = body["case"]["case_id"]
    _decide(client, body, "extend_hold", approve=True)
    time.sleep(2.0)
    assert _case(client, cid)["case"]["hold_active"] is True


def test_approved_extension_still_ends(client, monkeypatch):
    monkeypatch.setenv("GUARDIAN_HOLD_MAX_S", "30")
    monkeypatch.setenv("GUARDIAN_HOLD_EXTEND_S", "0.6")
    body = _to_officer(client)
    cid = body["case"]["case_id"]
    _decide(client, body, "extend_hold", approve=True)
    wait_for(lambda: _case(client, cid)["case"]["hold_active"] is False, timeout=10)
    assert _releases(_case(client, cid))[-1]["reason"] == "approved hold extension ended"


# ---------------------------------------------------------------- M4
class SlowExplainBrain(Brain):
    def __init__(self, gate: threading.Event) -> None:
        super().__init__()
        self.gate = gate

    def explain_risk(self, case, txns):
        self.gate.wait(5)
        return super().explain_risk(case, txns)


def test_victim_lane_not_blocked_by_officer_lane(monkeypatch):
    gate = threading.Event()
    monkeypatch.setattr(brain_call, "brain", SlowExplainBrain(gate))

    async def go():
        slow = asyncio.create_task(brain_call.call(None, "explain_risk", None, [], default="x"))
        await asyncio.sleep(0.05)                    # officer call now holds its lane
        t0 = time.monotonic()
        out = await brain_call.call(None, "classify_reply", "not me", "en", default=None)
        took = time.monotonic() - t0
        gate.set()
        await slow
        return out, took

    out, took = asyncio.run(go())
    assert out is not None and took < 1.0


def test_victim_prompt_sent_before_explanation(client, monkeypatch):
    gate = threading.Event()
    monkeypatch.setattr(brain_call, "brain", SlowExplainBrain(gate))
    try:
        cid = launch(client, "genuine")
        wait_for(lambda: client.get("/victim/usr_meena/pending").json(), timeout=2)
        body = _case(client, cid)
        assert "VICTIM_CONTACTED" in event_types(body)
        assert not any(e["payload"].get("kind") == "risk_explanation" for e in body["events"])
    finally:
        gate.set()
    wait_for(lambda: any(e["payload"].get("kind") == "risk_explanation" for e in _case(client, cid)["events"]))


def test_warm_is_silent_when_model_off():
    assert Brain().warm() is False


# ---------------------------------------------------------------- S2
def test_spoken_digits_are_not_stored(client):
    cid = launch(client, "genuine")
    wait_for(lambda: client.get("/victim/usr_meena/pending").json())
    r = client.post("/victim/respond", json={"case_id": cid, "transcript": "my OTP is 4 5 6 7 8 9", "lang": "en",
                                             "channel": "APP_TRUSTED_DEVICE"})
    assert r.status_code == 200, r.text
    body = _case(client, cid)
    replied = [e["payload"] for e in body["events"] if e["type"] == "VICTIM_REPLIED"]
    assert replied and replied[-1]["transcript"] == "my OTP is [digits removed]"
    assert client.get(f"/audit/{cid}/verify").json()["ok"] is True     # chain built over the redacted text


def test_report_text_digits_are_not_stored(client):
    r = client.post("/webhooks/victim-report",
                    json={"user_id": "usr_meena", "text": "Not me! call me on 98765 43210", "lang": "en"})
    assert r.status_code == 202, r.text
    body = _case(client, r.json()["case_id"])
    report = next(e["payload"] for e in body["events"] if e["type"] == "VICTIM_REPORT_RECEIVED")
    assert report["text"] == "Not me! call me on [digits removed]"
