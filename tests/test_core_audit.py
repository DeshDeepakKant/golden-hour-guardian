import sqlite3

from app import audit
from app.config import db_path
from app.contracts import EventType, Tier


def _fill(case_id="case_a1", n=5):
    for i in range(n):
        audit.append(case_id, EventType.STATE_CHANGED, "system", Tier.T1_AUTO, {"i": i, "amount_paise": 2499900})


def test_chain_verifies(client):
    _fill()
    assert audit.verify("case_a1") == {"ok": True, "length": 5, "broken_at": None}
    events = audit.list_events("case_a1")
    assert events[0].prev_hash == "" and events[1].prev_hash == events[0].hash


def test_empty_chain_is_ok(client):
    assert audit.verify("case_none") == {"ok": True, "length": 0, "broken_at": None}


def test_chains_are_per_case(client):
    _fill("case_a1", 3)
    _fill("case_a2", 3)
    assert audit.verify("case_a1")["ok"] and audit.verify("case_a2")["ok"]


def test_tampering_one_row_breaks_the_chain_at_that_seq(client):
    _fill()
    conn = sqlite3.connect(db_path())
    seqs = [r[0] for r in conn.execute("SELECT seq FROM case_events WHERE case_id='case_a1' ORDER BY seq")]
    target = seqs[2]
    conn.execute("UPDATE case_events SET payload = ? WHERE seq = ?", ('{"i":2,"amount_paise":1}', target))
    conn.commit()
    conn.close()
    res = audit.verify("case_a1")
    assert res["ok"] is False and res["broken_at"] == target and res["length"] == 5


def test_deleting_a_row_is_detected(client):
    _fill()
    conn = sqlite3.connect(db_path())
    seqs = [r[0] for r in conn.execute("SELECT seq FROM case_events WHERE case_id='case_a1' ORDER BY seq")]
    conn.execute("DELETE FROM case_events WHERE seq = ?", (seqs[1],))
    conn.commit()
    conn.close()
    res = audit.verify("case_a1")
    assert res["ok"] is False and res["broken_at"] == seqs[2]
