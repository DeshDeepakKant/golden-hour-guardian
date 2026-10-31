"""Deterministic SYNTHETIC world. SIMULATED DATA ONLY.

CLI:   python -m mocks.seed --reset
API:   seed(conn, reset) -- reused by /sim/reset.

Names end in "(demo)", mobiles are 90000 0xxxx, VPAs end in "@demo".
"""
from __future__ import annotations

import argparse
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from app.contracts import utcnow
from app.db import SCHEMA_PATH, connect, init_db

RNG_SEED = 42
HISTORY_DAYS = 30
BG_COUNT = 60
MODEL_TRUSTED = "Synthetic Phone A1"

# (user_id, first name, city, lang). The five scenario users have fixed IDs.
NAMED_USERS: list[tuple[str, str, str, str]] = [
    ("usr_ravi", "Ravi", "Hyderabad", "te"),        # ato
    ("usr_meena", "Meena", "Hyderabad", "en"),      # genuine
    ("usr_arjun", "Arjun", "Bengaluru", "hi"),      # inbound
    ("usr_lakshmi", "Lakshmi", "Warangal", "te"),   # noresponse
    ("usr_kiran", "Kiran", "Vijayawada", "en"),     # injection
    ("usr_asha", "Asha", "Warangal", "en"),
    ("usr_nikhil", "Nikhil", "Vijayawada", "hi"),
    ("usr_priya", "Priya", "Bengaluru", "te"),
]
CITIES = ["Hyderabad", "Warangal", "Vijayawada", "Bengaluru"]

MULE_VPAS = ["m1.qx@demo", "m2.zt@demo", "m3.kp@demo", "m4.ln@demo", "m5.vw@demo", "m6.rj@demo"]
KNOWN_PAYEES = [
    "kirana.xyz@demo", "dairy.corner@demo", "auto.stand.hyd@demo", "cafe.nook@demo",
    "greens.market@demo", "fuel.point@demo", "bookshop.lane@demo", "tailor.ram@demo",
    "pharma.local@demo", "salon.glow@demo", "bus.pass.demo@demo", "water.can.demo@demo",
]
BG_SENDER_IDS = [f"usr_bg_{n:02d}" for n in range(1, BG_COUNT + 1)]

# Children first so foreign keys never block a reset.
CLEAR_ORDER = [
    "case_events", "decisions", "evidence_packs", "cases",
    "partner_calls", "txns", "devices", "users",
]


def iso(ts: datetime) -> str:
    """UTC ISO-8601 with fixed seconds precision (sorts lexically)."""
    return ts.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def device_id_for(user_id: str) -> str:
    return f"dev_{user_id[4:]}_phone"


def insert_device(conn: sqlite3.Connection, device_id: str, user_id: str, model: str,
                  first_seen: datetime, last_seen: datetime, geo_city: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO devices (device_id, user_id, model, first_seen, last_seen, geo_city, revoked) "
        "VALUES (?, ?, ?, ?, ?, ?, 0)",
        (device_id, user_id, model, iso(first_seen), iso(last_seen), geo_city),
    )


def insert_txn(conn: sqlite3.Connection, txn_id: str, user_id: str, payee_vpa: str,
               amount_paise: int, ts: datetime, device_id: str, first_time: bool) -> None:
    conn.execute(
        "INSERT INTO txns (txn_id, user_id, payee_vpa, amount_paise, ts, status, device_id, "
        "is_first_time_payee) VALUES (?, ?, ?, ?, ?, 'SUCCESS', ?, ?)",
        (txn_id, user_id, payee_vpa, amount_paise, iso(ts), device_id, int(first_time)),
    )


def _count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {t: _count(conn, t) for t in ("users", "devices", "txns")}


def _clear(conn: sqlite3.Connection) -> None:
    for table in CLEAR_ORDER:
        conn.execute(f"DELETE FROM {table}")
    conn.commit()


def seed(conn: sqlite3.Connection, reset: bool = True) -> dict[str, int]:
    """Build the synthetic world. With reset=False and data present, does nothing."""
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    if not reset and _count(conn, "users") > 0:
        return _counts(conn)
    if reset:
        _clear(conn)
        from mocks.partners import partners  # local import: partners has no seed dependency
        partners.reset()

    now = utcnow().replace(microsecond=0)
    rng = random.Random(RNG_SEED)

    # Users (named scenario users, then the 60 background senders).
    people: list[tuple[str, str, str, str, int]] = []
    for idx, (uid, first, city, lang) in enumerate(NAMED_USERS, start=1):
        people.append((uid, f"{first} (demo)", city, lang, idx))
    for n in range(1, BG_COUNT + 1):
        people.append((f"usr_bg_{n:02d}", f"Sender {n:02d} (demo)", CITIES[n % len(CITIES)], "en", 100 + n))

    for uid, name, city, lang, idx in people:
        conn.execute(
            "INSERT INTO users (user_id, name, mobile, city, lang, trusted_device, sim_changed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, NULL)",
            (uid, name, f"90000{idx:05d}", city, lang, device_id_for(uid)),
        )
        insert_device(conn, device_id_for(uid), uid, MODEL_TRUSTED,
                      now - timedelta(days=400), now, city)

    # 30 days of normal history for the named users, all from the trusted device.
    for uid, _name, city, _lang, _idx in people[: len(NAMED_USERS)]:
        payees = rng.sample(KNOWN_PAYEES, rng.randint(5, 10))
        rows: list[tuple[datetime, str, int]] = []
        for day in range(1, HISTORY_DAYS + 1):
            for _ in range(rng.randint(2, 8)):
                ts = now - timedelta(days=day, minutes=rng.randint(0, 1439))
                rows.append((ts, rng.choice(payees), rng.randint(20, 2500) * 100))
        rows.sort(key=lambda r: r[0])
        seen: set[str] = set()
        for i, (ts, payee, amount) in enumerate(rows, start=1):
            first_time = payee not in seen
            seen.add(payee)
            insert_txn(conn, f"txn_{uid[4:]}_{i:04d}", uid, payee, amount, ts,
                       device_id_for(uid), first_time)

    conn.commit()
    return _counts(conn)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Seed the synthetic world (SIMULATED DATA).")
    parser.add_argument("--reset", action="store_true", help="drop and recreate the database first")
    args = parser.parse_args(argv)
    init_db(reset=args.reset)
    conn = connect()
    try:
        counts: dict[str, Any] = seed(conn, reset=args.reset)
    finally:
        conn.close()
    print(f"SIMULATED DATA seeded: {counts}")


if __name__ == "__main__":
    main()
