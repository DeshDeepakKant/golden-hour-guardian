"""STUB scenario injectors. Mockworld implements ato | genuine | inbound | noresponse | injection."""
from __future__ import annotations

import sqlite3


def inject(conn: sqlite3.Connection, name: str) -> dict:
    raise NotImplementedError(f"scenario {name!r} not implemented yet (mockworld)")
