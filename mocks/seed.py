"""STUB seed: `python -m mocks.seed --reset`. Mockworld replaces it with the full synthetic world."""
from __future__ import annotations

import argparse
from datetime import timedelta

from app.contracts import utcnow
from app.db import connect, init_db


def seed(reset: bool = True) -> None:
    init_db(reset=reset)
    now = utcnow()
    conn = connect()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO users (user_id, name, mobile, city, lang, trusted_device, sim_changed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("usr_ravi", "Ravi Kumar", "9800000021", "Hyderabad", "en", "dev_ravi_phone", None),
        )
        conn.execute(
            "INSERT OR REPLACE INTO devices (device_id, user_id, model, first_seen, last_seen, geo_city, revoked) "
            "VALUES (?, ?, ?, ?, ?, ?, 0)",
            ("dev_ravi_phone", "usr_ravi", "Synthetic Phone A1",
             (now - timedelta(days=400)).isoformat(), now.isoformat(), "Hyderabad"),
        )
        conn.commit()
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Seed the synthetic world (SIMULATED DATA).")
    parser.add_argument("--reset", action="store_true", help="drop and recreate the database first")
    args = parser.parse_args(argv)
    seed(reset=args.reset)
    print("seeded (stub): 1 user, 1 device")


if __name__ == "__main__":
    main()
