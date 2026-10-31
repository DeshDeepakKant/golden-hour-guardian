from app.config import SETTINGS
from app.contracts import ACTION_TIERS, Action, Tier

FORBIDDEN = {
    Action.FREEZE_BENEFICIARY,
    Action.FILE_POLICE_COMPLAINT,
    Action.REQUEST_OTP_PIN,
    Action.PROMISE_REFUND,
    Action.CONTACT_PAYEE,
}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_static_pages(client):
    for path in ("/officer/", "/victim/"):
        r = client.get(path)
        assert r.status_code == 200
        assert "PROTOTYPE — SIMULATED DATA" in r.text


def test_tests_use_tmp_db(client, tmp_path):
    from app.config import db_path

    assert db_path() == tmp_path / "test.db"
    assert SETTINGS["llm"]["model"] == "none"


def test_action_tiers_cover_all_actions():
    assert set(ACTION_TIERS) == set(Action)


def test_tier3_actions_are_forbidden():
    tier3 = {a for a, t in ACTION_TIERS.items() if t == Tier.T3_FORBIDDEN}
    assert tier3 == FORBIDDEN
