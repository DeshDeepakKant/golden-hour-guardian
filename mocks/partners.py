"""MOCK partner gateway. SIMULATED. Implements app.contracts.PartnerGateway.

Every call sleeps 50-150 ms, logs one row to partner_calls, and returns fake refs.
Suppression and the marketing queue live in process memory (guarded by a lock).
"""
from __future__ import annotations

import json
import random
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Any

from app.contracts import utcnow
from app.db import connect

LATENCY_S = (0.05, 0.15)
MARKETING_DELAY_S = 20
MARKETING_PAYLOAD = {
    "category": "marketing",
    "title": "Pre-approved loan offer",
    "body": "Pre-approved loan offer (SIMULATED DATA)",
}


def _now_iso() -> str:
    return utcnow().replace(microsecond=0).isoformat()


class MockPartners:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._suppressed_until: dict[str, datetime] = {}
        self._queued: list[tuple[datetime, str, dict[str, Any]]] = []
        self._rng = random.Random()

    # -- internals ---------------------------------------------------------
    def _latency(self) -> None:
        time.sleep(self._rng.uniform(*LATENCY_S))

    def _log(self, method: str, args: dict[str, Any], result: str | None = None) -> None:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO partner_calls (ts, method, args, result) VALUES (?, ?, ?, ?)",
                (_now_iso(), method, json.dumps(args, default=str), result),
            )
            conn.commit()
        finally:
            conn.close()

    def _is_suppressed(self, user_id: str, now: datetime) -> bool:
        until = self._suppressed_until.get(user_id)
        return until is not None and now < until

    # -- PartnerGateway ----------------------------------------------------
    def place_hold(self, user_id: str, minutes: int) -> str:
        with self._lock:
            self._latency()
            ref = f"HOLD-{uuid.uuid4().hex[:8].upper()}"
            self._log("place_hold", {"user_id": user_id, "minutes": minutes}, ref)
            return ref

    def release_hold(self, user_id: str) -> None:
        with self._lock:
            self._latency()
            self._log("release_hold", {"user_id": user_id}, "RELEASED")

    def revoke_session(self, user_id: str, device_id: str) -> None:
        with self._lock:
            self._latency()
            self._log("revoke_session", {"user_id": user_id, "device_id": device_id}, "REVOKED")

    def send_push(self, user_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._latency()
            now = utcnow()
            suppressed = payload.get("category") == "marketing" and self._is_suppressed(user_id, now)
            result = "SUPPRESSED" if suppressed else "SENT"
            self._log("send_push", {"user_id": user_id, "payload": payload}, result)

    def suppress_marketing(self, user_id: str, minutes: int) -> None:
        with self._lock:
            self._latency()
            until = utcnow() + timedelta(minutes=minutes)
            self._suppressed_until[user_id] = until
            self._log("suppress_marketing", {"user_id": user_id, "minutes": minutes},
                      until.replace(microsecond=0).isoformat())

    def raise_dispute(self, txn_ids: list[str], evidence_ref: str) -> str:
        with self._lock:
            self._latency()
            ref = f"DSP-{uuid.uuid4().hex[:8].upper()}"
            self._log("raise_dispute", {"txn_ids": txn_ids, "evidence_ref": evidence_ref}, ref)
            return ref

    # -- marketing queue (used by the ato scenario) -------------------------
    def queue_push(self, user_id: str, payload: dict[str, Any], due_at: datetime) -> None:
        """Queue a push for later. Core sends it by calling flush_due_pushes(now)."""
        with self._lock:
            self._queued.append((due_at, user_id, dict(payload)))
            self._log("queue_push", {"user_id": user_id, "due_at": due_at.isoformat()}, "QUEUED")

    def flush_due_pushes(self, now: datetime | None = None) -> int:
        """Send every queued push whose due time has passed, via send_push. Returns the count."""
        now = now or utcnow()
        with self._lock:
            due = [q for q in self._queued if q[0] <= now]
            self._queued = [q for q in self._queued if q[0] > now]
        for _due_at, user_id, payload in due:
            self.send_push(user_id, payload)
        return len(due)

    def reset(self) -> None:
        with self._lock:
            self._suppressed_until.clear()
            self._queued.clear()


partners = MockPartners()
