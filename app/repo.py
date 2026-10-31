"""LedgerRepo over the SQLite seed (read side) plus a few small writes on the synthetic world."""
from __future__ import annotations

import json
import statistics
from datetime import datetime, timedelta
from typing import Any, Optional

from app.contracts import Txn, utcnow
from app.db import connect
from app.util import parse_ts


def _txn(row) -> Txn:
    return Txn(
        txn_id=row["txn_id"], user_id=row["user_id"], payee_vpa=row["payee_vpa"],
        amount_paise=int(row["amount_paise"]), ts=parse_ts(row["ts"]), status=row["status"],
        device_id=row["device_id"], is_first_time_payee=bool(row["is_first_time_payee"]),
    )


class SqliteLedgerRepo:
    """One short-lived connection per call (SQLite + asyncio rule)."""

    def get_txns(self, txn_ids: list[str]) -> list[Txn]:
        if not txn_ids:
            return []
        conn = connect()
        try:
            marks = ",".join("?" * len(txn_ids))
            rows = conn.execute(f"SELECT * FROM txns WHERE txn_id IN ({marks})", txn_ids).fetchall()
        finally:
            conn.close()
        by_id = {r["txn_id"]: _txn(r) for r in rows}
        return [by_id[i] for i in txn_ids if i in by_id]

    def txns_for_user(self, user_id: str) -> list[Txn]:
        conn = connect()
        try:
            rows = conn.execute("SELECT * FROM txns WHERE user_id = ?", (user_id,)).fetchall()
        finally:
            conn.close()
        return sorted((_txn(r) for r in rows), key=lambda t: t.ts)

    def recent_txns(self, user_id: str, minutes: int, now: Optional[datetime] = None) -> list[Txn]:
        cutoff = (now or utcnow()) - timedelta(minutes=minutes)
        return [t for t in self.txns_for_user(user_id) if t.ts >= cutoff]

    def user_profile(self, user_id: str) -> dict[str, Any]:
        conn = connect()
        try:
            row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if row is None:
                return {}
            dev = conn.execute("SELECT * FROM devices WHERE device_id = ?", (row["trusted_device"],)).fetchone()
        finally:
            conn.close()
        return {
            "user_id": row["user_id"], "name": row["name"], "mobile": row["mobile"], "city": row["city"],
            "lang": row["lang"], "trusted_device": row["trusted_device"],
            "sim_changed_at": parse_ts(row["sim_changed_at"]) if row["sim_changed_at"] else None,
            "trusted_device_city": dev["geo_city"] if dev else row["city"],
            "trusted_device_revoked": bool(dev["revoked"]) if dev else True,
            "trusted_device_exists": dev is not None,
        }

    def device(self, device_id: str) -> Optional[dict[str, Any]]:
        conn = connect()
        try:
            row = conn.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,)).fetchone()
        finally:
            conn.close()
        return dict(row) if row else None

    def device_timeline(self, user_id: str, hours: int) -> list[dict[str, Any]]:
        cutoff = utcnow() - timedelta(hours=hours)
        profile = self.user_profile(user_id)
        conn = connect()
        try:
            rows = conn.execute("SELECT * FROM devices WHERE user_id = ?", (user_id,)).fetchall()
        finally:
            conn.close()
        out = []
        for r in rows:
            if parse_ts(r["last_seen"]) < cutoff and parse_ts(r["first_seen"]) < cutoff:
                continue
            out.append({
                "device_id": r["device_id"], "model": r["model"], "geo_city": r["geo_city"],
                "first_seen": r["first_seen"], "last_seen": r["last_seen"],
                "revoked": bool(r["revoked"]), "trusted": r["device_id"] == profile.get("trusted_device"),
            })
        return sorted(out, key=lambda d: d["first_seen"])

    def payee_fanin(self, payee_vpa: str, minutes: int) -> int:
        """Distinct senders that paid this VPA in the last `minutes`."""
        cutoff = utcnow() - timedelta(minutes=minutes)
        conn = connect()
        try:
            rows = conn.execute("SELECT user_id, ts FROM txns WHERE payee_vpa = ?", (payee_vpa,)).fetchall()
        finally:
            conn.close()
        return len({r["user_id"] for r in rows if parse_ts(r["ts"]) >= cutoff})

    def median_amount_paise(self, user_id: str, exclude_ids: list[str]) -> Optional[int]:
        amounts = [t.amount_paise for t in self.txns_for_user(user_id)
                   if t.txn_id not in set(exclude_ids) and t.status == "SUCCESS"]
        return int(statistics.median(amounts)) if amounts else None

    def mark_device_revoked(self, device_id: str) -> None:
        conn = connect()
        try:
            conn.execute("UPDATE devices SET revoked = 1 WHERE device_id = ?", (device_id,))
            conn.commit()
        finally:
            conn.close()

    def partner_calls_since(self, seq: int) -> list[dict[str, Any]]:
        conn = connect()
        try:
            rows = conn.execute("SELECT * FROM partner_calls WHERE seq > ? ORDER BY seq", (seq,)).fetchall()
        finally:
            conn.close()
        return [dict(r) for r in rows]

    def last_partner_seq(self) -> int:
        conn = connect()
        try:
            row = conn.execute("SELECT COALESCE(MAX(seq), 0) AS m FROM partner_calls").fetchone()
        finally:
            conn.close()
        return int(row["m"])

    def partner_calls(self, limit: int = 200) -> list[dict[str, Any]]:
        conn = connect()
        try:
            rows = conn.execute("SELECT * FROM partner_calls ORDER BY seq DESC LIMIT ?", (limit,)).fetchall()
        finally:
            conn.close()
        out = []
        for r in rows:
            d = dict(r)
            try:
                d["args"] = json.loads(d["args"])
            except (TypeError, ValueError):
                pass
            out.append(d)
        return out


repo = SqliteLedgerRepo()
