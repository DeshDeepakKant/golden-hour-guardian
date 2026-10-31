"""STUB mock partner gateway — logs every call to partner_calls. Mockworld replaces it."""
from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from app.contracts import utcnow
from app.db import connect


def _log(method: str, args: dict[str, Any], result: Optional[str] = None) -> None:
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO partner_calls (ts, method, args, result) VALUES (?, ?, ?, ?)",
            (utcnow().isoformat(), method, json.dumps(args, default=str), result),
        )
        conn.commit()
    finally:
        conn.close()


class MockPartners:
    def place_hold(self, user_id: str, minutes: int) -> str:
        hold_id = f"hold_{uuid.uuid4().hex[:8]}"
        _log("place_hold", {"user_id": user_id, "minutes": minutes}, hold_id)
        return hold_id

    def release_hold(self, user_id: str) -> None:
        _log("release_hold", {"user_id": user_id})

    def revoke_session(self, user_id: str, device_id: str) -> None:
        _log("revoke_session", {"user_id": user_id, "device_id": device_id})

    def send_push(self, user_id: str, payload: dict[str, Any]) -> None:
        _log("send_push", {"user_id": user_id, "payload": payload})

    def suppress_marketing(self, user_id: str, minutes: int) -> None:
        _log("suppress_marketing", {"user_id": user_id, "minutes": minutes})

    def raise_dispute(self, txn_ids: list[str], evidence_ref: str) -> str:
        dispute_id = f"dsp_{uuid.uuid4().hex[:8]}"
        _log("raise_dispute", {"txn_ids": txn_ids, "evidence_ref": evidence_ref}, dispute_id)
        return dispute_id


partners = MockPartners()
