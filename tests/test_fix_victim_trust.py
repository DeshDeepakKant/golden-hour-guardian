"""REVIEW M1 (spoken/typed yes never releases) and M2 (server decides the trusted channel)."""
import os

os.environ.setdefault("GUARDIAN_LLM_MODEL", "none")

import pytest

from app.brain import rules
from app.contracts import ReplyIntent as R
from app.repo import repo
from tests.test_core_helpers import event_types, wait_for, wait_state


def _post(client, cid, device=None, **body):
    headers = {"X-Guardian-Device": device} if device is not None else {}
    r = client.post("/victim/respond", json={"case_id": cid, "lang": "en", **body}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def _genuine(client):
    cid = client.post("/sim/scenario/genuine").json()["case_id"]
    wait_state(client, cid, "VERIFYING")
    wait_for(lambda: client.get("/victim/usr_meena/pending").json())
    return cid, repo.user_profile("usr_meena")["trusted_device"]


@pytest.mark.parametrize("text", ["okay", "ok", "ha", "haan", "theek hai", "sahi hai", "सही है", "సరే",
                                  "okay, which payment?", "theek hai batao"])
def test_bare_ok_is_not_yes_mine(text):
    out = rules.classify(text)
    assert out is None or out[0] != R.YES_MINE


@pytest.mark.parametrize("text", ["okay", "ha", "yes it was me, it is genuine"])
def test_transcript_yes_never_releases(client, text):
    cid, dev = _genuine(client)
    assert _post(client, cid, dev, transcript=text)["state"] != "RELEASED"
    body = client.get(f"/cases/{cid}").json()
    assert "HOLD_RELEASED" not in event_types(body)
    assert client.get("/victim/usr_meena/pending").json()["variant"] in ("retry", "done")   # ask for a tap, or a human calls back


def test_no_header_is_untrusted(client):
    cid, _ = _genuine(client)
    assert _post(client, cid, answer="YES_MINE", channel="APP_TRUSTED_DEVICE")["state"] == "AWAITING_OFFICER"
    body = client.get(f"/cases/{cid}").json()
    assert [d["action"] for d in body["decisions"]] == ["release_hold_untrusted"]
    replied = [e for e in body["events"] if e["type"] == "VICTIM_REPLIED"][-1]
    assert replied["payload"]["channel"] == "VOICE_REGISTERED_NO"


def test_wrong_header_is_untrusted(client):
    cid, _ = _genuine(client)
    assert _post(client, cid, "dev_x9", answer="YES_MINE")["state"] == "AWAITING_OFFICER"
    assert "HOLD_RELEASED" not in event_types(client.get(f"/cases/{cid}").json())


def test_other_users_device_is_untrusted(client):
    cid, _ = _genuine(client)
    # Use a different user's device (usr_arjun instead of usr_meena who is the case owner)
    other = repo.user_profile("usr_arjun")["trusted_device"]
    assert _post(client, cid, other, answer="YES_MINE")["state"] == "AWAITING_OFFICER"


def test_correct_header_releases_even_if_body_claims_otherwise(client):
    cid, dev = _genuine(client)
    assert _post(client, cid, dev, answer="YES_MINE", channel="VOICE_REGISTERED_NO")["state"] == "RELEASED"
    assert "HOLD_RELEASED" in event_types(client.get(f"/cases/{cid}").json())


def test_sim_auto_reply_genuine_still_releases(client):
    r = client.post("/sim/scenario/genuine?auto_reply=true&delay=0.5")
    assert r.status_code == 200 and r.json()["auto_reply"] is True
    wait_state(client, r.json()["case_id"], "RELEASED", timeout=20)
