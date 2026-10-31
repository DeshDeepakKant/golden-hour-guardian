"""Hindi/Telugu prompts carry fixed English companion lines (`messages_en`); English prompts don't.
Also: the .env loader never overrides real environment variables."""
import os

os.environ.setdefault("GUARDIAN_LLM_MODEL", "none")

import pytest

from tests.test_core_helpers import wait_for, wait_state


def _pending(client, user_id):
    return wait_for(lambda: client.get(f"/victim/{user_id}/pending").json())


@pytest.mark.parametrize("scenario,user_id,lang", [("ato", "usr_ravi", "te"), ("inbound", "usr_arjun", "hi")])
def test_native_language_prompts_have_english_lines(client, scenario, user_id, lang):
    cid = client.post(f"/sim/scenario/{scenario}").json()["case_id"]
    if scenario == "ato":
        wait_state(client, cid, "HELD_PENDING_VERIFY")
    p = _pending(client, user_id)
    assert p["lang"] == lang
    en = p.get("messages_en")
    assert en and all(isinstance(x, str) and x for x in en)
    assert not any(ord(c) > 0x0900 and ord(c) < 0x0C80 + 0x80 for line in en for c in line if c.isalpha()), \
        "English companion must be Latin script"
    assert all("{" not in line for line in en), "unfilled placeholder in English line"


def test_verify_english_lines_match_template_facts(client):
    cid = client.post("/sim/scenario/ato").json()["case_id"]
    wait_state(client, cid, "HELD_PENDING_VERIFY")
    p = _pending(client, "usr_ravi")
    assert p["variant"] == "verify"
    joined = " ".join(p["messages_en"])
    assert "₹74,997" in joined                      # amount comes from code, same as the Telugu line
    assert "OTP" in joined and "never" in joined.lower()   # safety line present


def test_english_user_gets_no_companion(client):
    client.post("/sim/scenario/genuine")
    p = _pending(client, "usr_meena")
    assert p["lang"] == "en"
    assert "messages_en" not in p


def test_protected_and_report_prompts_have_english(client, monkeypatch):
    from app import tools
    from app.agents import voice

    cid = client.post("/sim/scenario/inbound").json()["case_id"]       # usr_arjun, Hindi, no verify step
    wait_state(client, cid, "AWAITING_OFFICER")
    # the latest prompt after the evidence step is the NCRP guide
    guide = _pending(client, "usr_arjun")
    assert guide["variant"] == "ncrp_guide" and guide["lang"] == "hi"
    assert guide["messages_en"] and "1930" in " ".join(guide["messages_en"])
    # the "protected" prompt is built the same way; capture it instead of racing the stream
    sent = []
    monkeypatch.setattr(tools, "notify_victim", lambda case, actor, prompt: sent.append(prompt))
    voice.send_protected(cid)
    assert sent and sent[0]["variant"] == "protected"
    assert len(sent[0]["messages_en"]) == len(sent[0]["messages"])


def test_dotenv_does_not_override_environment(tmp_path, monkeypatch):
    from app import config

    f = tmp_path / ".env"
    f.write_text("# comment\nFOO_KEEP=from_file\nexport FOO_NEW='quoted value'\nFOO_INLINE=abc # note\n\nbad line\n")
    monkeypatch.setenv("FOO_KEEP", "from_env")
    monkeypatch.delenv("FOO_NEW", raising=False)
    monkeypatch.delenv("FOO_INLINE", raising=False)
    config._load_dotenv(f)
    assert os.environ["FOO_KEEP"] == "from_env"
    assert os.environ["FOO_NEW"] == "quoted value"
    assert os.environ["FOO_INLINE"] == "abc"
    for k in ("FOO_NEW", "FOO_INLINE"):
        monkeypatch.delenv(k, raising=False)
