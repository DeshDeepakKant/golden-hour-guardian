"""Demo controls: scenario launcher and reset."""
from __future__ import annotations

import asyncio
from typing import Any, Optional

from fastapi import APIRouter, HTTPException

from app import metrics, orchestrator, orchestrator_tasks as tasks, pending, store, tools
from app.agents import voice
from app.bus import bus
from app.contracts import FraudAlert, VictimReport, VictimResponse
from app.db import connect, init_db
from app.repo import repo
from mocks import scenarios, seed as seed_mod
from mocks.partners import MARKETING_DELAY_S

router = APIRouter()


@router.post("/sim/scenario/{name}")
async def run_scenario(name: str, auto_reply: bool = False, delay: float = 4.0) -> dict:
    conn = connect()
    try:
        try:
            result: dict[str, Any] = scenarios.inject(conn, name)
        except ValueError as e:
            raise HTTPException(404, str(e))
    finally:
        conn.close()

    alert: Optional[FraudAlert] = result.get("alert")
    report: Optional[VictimReport] = result.get("report")
    if alert is not None:
        case, created = orchestrator.create_from_alert(alert)
        if created:
            orchestrator.start(case)
    elif report is not None:
        case = orchestrator.create_from_report(report)
        orchestrator.start(case)
    else:
        raise HTTPException(500, "scenario produced neither alert nor report")

    # queued marketing push (ato): send it ~20 s later; it should come back SUPPRESSED
    tasks.spawn(case.case_id, _flush_marketing(), "marketing_flush")
    reply = result.get("scripted_reply")
    if auto_reply and reply:
        tasks.spawn(case.case_id, _scripted_reply(case.case_id, reply, delay), "scripted_reply")
    return {"case_id": case.case_id, "scenario": name, "auto_reply": bool(auto_reply and reply)}


async def _flush_marketing() -> None:
    await asyncio.sleep(MARKETING_DELAY_S)
    tools.flush_marketing_queue()


async def _scripted_reply(case_id: str, reply: dict, delay: float) -> None:
    await asyncio.sleep(max(0.0, delay))
    channel = reply.get("channel") or "APP_TRUSTED_DEVICE"
    device = None
    case = store.get_case(case_id)
    if case is not None and channel == "APP_TRUSTED_DEVICE":   # scripted victim taps on their own phone
        device = repo.user_profile(case.user_id).get("trusted_device")
    await voice.handle_response(VictimResponse(
        case_id=case_id, answer=reply.get("answer"), transcript=reply.get("transcript"),
        lang=reply.get("lang") or "en", channel=channel,
    ), device_id=device)


@router.post("/sim/reset")
async def reset() -> dict:
    await tasks.cancel_all()          # stop every timeout / expiry / pipeline before reseeding
    pending.reset()
    tools.reset()
    bus.reset()
    init_db()
    conn = connect()
    try:
        seed_mod.seed(conn, reset=True)
    finally:
        conn.close()
    metrics.publish()
    return {"ok": True}
