from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

from app import audit, store
from app.agents import desk
from app.contracts import Case, Decision, DecisionStatus, OfficerDecisionIn
from app.policy import PolicyBlocked
from app.repo import repo
from app.util import aware
from app.contracts import utcnow

router = APIRouter()


@router.get("/cases")
async def list_cases(state: Optional[str] = None) -> list[Case]:
    return store.list_cases(state)


@router.get("/cases/{case_id}")
async def get_case(case_id: str) -> dict:
    case = store.get_case(case_id)
    if case is None:
        raise HTTPException(404, "case not found")
    evidence = store.get_evidence(case_id)
    return {
        "case": case,
        "events": audit.list_events(case_id),
        "decisions": store.list_decisions(case_id),
        "evidence": evidence,
    }


@router.get("/officer/queue")
async def officer_queue() -> list[dict]:
    out = []
    for d in store.list_decisions(status=DecisionStatus.PENDING):
        case = store.get_case(d.case_id)
        if case is None:
            continue
        profile = repo.user_profile(case.user_id)
        from app.agents.scribe import mask_name
        out.append({
            "decision": d,
            "case": {"case_id": case.case_id, "user_id": case.user_id, "state": case.state,
                     "risk_score": case.risk_score, "origin": case.origin, "t_alert": case.t_alert,
                     "hold_active": case.hold_active, "txn_ids": case.txn_ids,
                     "victim_name_masked": mask_name(profile.get("name", ""))},
            "sla_age_s": round((utcnow() - aware(d.requested_at)).total_seconds(), 1),
        })
    return out


@router.post("/decisions/{decision_id}")
async def decide(decision_id: str, body: OfficerDecisionIn) -> Decision:
    body = body.model_copy(update={"decision_id": decision_id})
    try:
        return desk.apply(decision_id, body)
    except LookupError:
        raise HTTPException(404, "decision not found")
    except desk.DecisionConflict as e:
        raise HTTPException(409, str(e))
    except PolicyBlocked as e:
        raise HTTPException(403, e.result.reason)
