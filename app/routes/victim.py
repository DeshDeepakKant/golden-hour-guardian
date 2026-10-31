from __future__ import annotations

import re
from typing import Optional

from fastapi import APIRouter, HTTPException

from app import audit, pending, store, texts, tools
from app.agents import voice
from app.contracts import EventType, NcrpAck, Tier, VictimResponse

router = APIRouter()
ACK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 \-/_.]{2,39}$")


@router.get("/victim/{user_id}/pending")
async def victim_pending(user_id: str) -> Optional[dict]:
    return pending.get_prompt(user_id)


@router.post("/victim/respond")
async def victim_respond(resp: VictimResponse) -> dict:
    try:
        return await voice.handle_response(resp)
    except LookupError:
        raise HTTPException(404, "case not found")
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.post("/victim/ncrp-ack")
async def ncrp_ack(ack: NcrpAck) -> dict:
    case = store.get_case(ack.case_id)
    if case is None:
        raise HTTPException(404, "case not found")
    number = ack.ack_number.strip()
    if not ACK_RE.match(number):
        raise HTTPException(422, "acknowledgement number should be letters, digits, dash or slash")
    audit.append(case.case_id, EventType.NCRP_ACK_RECORDED, "victim", Tier.T1_AUTO, {"ack_number": number})
    voice.send_simple(case, "done", texts.DONE)
    return {"ok": True}
