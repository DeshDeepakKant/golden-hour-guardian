"""Shared helpers for tests/test_core_*.py (not a test module itself)."""
from __future__ import annotations

import time


def wait_for(fn, timeout: float = 15.0, interval: float = 0.05):
    end = time.time() + timeout
    last = None
    while time.time() < end:
        last = fn()
        if last:
            return last
        time.sleep(interval)
    raise AssertionError(f"condition not met within {timeout}s (last={last!r})")


def case_state(client, case_id: str) -> str:
    return client.get(f"/cases/{case_id}").json()["case"]["state"]


def wait_state(client, case_id: str, *states: str, timeout: float = 15.0) -> dict:
    wait_for(lambda: case_state(client, case_id) in states, timeout)
    return client.get(f"/cases/{case_id}").json()


def launch(client, name: str) -> str:
    r = client.post(f"/sim/scenario/{name}")
    assert r.status_code == 200, r.text
    return r.json()["case_id"]


def event_types(body: dict) -> list[str]:
    return [e["type"] for e in body["events"]]
