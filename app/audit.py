"""Append-only, hash-chained audit log (one chain per case).

hash = sha256(prev_hash + canonical_json(event_without_hash)); genesis prev_hash is "".
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
from datetime import datetime
from typing import Any, Optional

from app.bus import publish_data
from app.contracts import CaseEvent, EventType, Tier, utcnow
from app.db import connect
from app.util import new_id, parse_ts

_lock = threading.Lock()

# DPDP minimisation: digit runs a victim speaks/types (OTP, PIN, phone no.) are never persisted or
# broadcast. Only victim free-text keys are touched; system amounts/IDs are left alone.
_DIGITS_RE = re.compile(r"\d(?:[\s-]?\d){3,}")
_VICTIM_TEXT = {EventType.VICTIM_REPLIED: ("transcript",), EventType.VICTIM_REPORT_RECEIVED: ("text",)}


def redact_digits(text: Optional[str]) -> Optional[str]:
    return _DIGITS_RE.sub("[digits removed]", text) if isinstance(text, str) else text


def _redact(type_: EventType, payload: dict[str, Any]) -> dict[str, Any]:
    keys = _VICTIM_TEXT.get(EventType(type_), ())
    if not any(isinstance(payload.get(k), str) for k in keys):
        return payload
    return {**payload, **{k: redact_digits(payload[k]) for k in keys if isinstance(payload.get(k), str)}}


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _body(event_id: str, case_id: str, ts: str, type_: str, actor: str, tier: Optional[int],
          payload: dict[str, Any], prev_hash: str) -> dict[str, Any]:
    return {"event_id": event_id, "case_id": case_id, "ts": ts, "type": type_, "actor": actor,
            "tier": tier, "payload": payload, "prev_hash": prev_hash}


def compute_hash(prev_hash: str, body: dict[str, Any]) -> str:
    return hashlib.sha256((prev_hash + canonical_json(body)).encode("utf-8")).hexdigest()


def _event_from_row(r) -> CaseEvent:
    return CaseEvent(
        event_id=r["event_id"], case_id=r["case_id"], ts=parse_ts(r["ts"]), type=EventType(r["type"]),
        actor=r["actor"], tier=Tier(r["tier"]) if r["tier"] is not None else None,
        payload=json.loads(r["payload"]), prev_hash=r["prev_hash"], hash=r["hash"],
    )


def append(case_id: str, type: EventType, actor: str, tier: Optional[Tier] = None,
           payload: Optional[dict[str, Any]] = None, publish: bool = True) -> CaseEvent:
    payload_norm = json.loads(json.dumps(_redact(type, payload or {}), default=str))   # JSON-round-trip stable
    tier_i = int(tier) if tier is not None else None
    ts = utcnow().isoformat()
    event_id = new_id("evt")
    with _lock:
        conn = connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT hash FROM case_events WHERE case_id = ? ORDER BY seq DESC LIMIT 1", (case_id,)
            ).fetchone()
            prev_hash = row["hash"] if row else ""
            h = compute_hash(prev_hash, _body(event_id, case_id, ts, EventType(type).value, actor,
                                              tier_i, payload_norm, prev_hash))
            conn.execute(
                "INSERT INTO case_events (event_id, case_id, ts, type, actor, tier, payload, prev_hash, hash) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (event_id, case_id, ts, EventType(type).value, actor, tier_i,
                 canonical_json(payload_norm), prev_hash, h),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    event = CaseEvent(event_id=event_id, case_id=case_id, ts=parse_ts(ts), type=EventType(type), actor=actor,
                      tier=tier, payload=payload_norm, prev_hash=prev_hash, hash=h)
    if publish:
        publish_data("event", event.model_dump(mode="json"))
    return event


def list_events(case_id: str) -> list[CaseEvent]:
    conn = connect()
    try:
        rows = conn.execute("SELECT * FROM case_events WHERE case_id = ? ORDER BY seq", (case_id,)).fetchall()
    finally:
        conn.close()
    return [_event_from_row(r) for r in rows]


def events_of_type(type: EventType) -> list[CaseEvent]:
    conn = connect()
    try:
        rows = conn.execute("SELECT * FROM case_events WHERE type = ? ORDER BY seq", (EventType(type).value,)).fetchall()
    finally:
        conn.close()
    return [_event_from_row(r) for r in rows]


def count(where: str, args: tuple = ()) -> int:
    conn = connect()
    try:
        return int(conn.execute(f"SELECT COUNT(*) AS n FROM case_events WHERE {where}", args).fetchone()["n"])
    finally:
        conn.close()


def verify(case_id: str) -> dict[str, Any]:
    """Recompute the chain. broken_at is the `seq` of the first row that does not verify."""
    conn = connect()
    try:
        rows = conn.execute("SELECT * FROM case_events WHERE case_id = ? ORDER BY seq", (case_id,)).fetchall()
    finally:
        conn.close()
    expected_prev = ""
    for r in rows:
        body = _body(r["event_id"], r["case_id"], r["ts"], r["type"], r["actor"], r["tier"],
                     json.loads(r["payload"]), r["prev_hash"])
        if r["prev_hash"] != expected_prev or compute_hash(r["prev_hash"], body) != r["hash"]:
            return {"ok": False, "length": len(rows), "broken_at": int(r["seq"])}
        expected_prev = r["hash"]
    return {"ok": True, "length": len(rows), "broken_at": None}
