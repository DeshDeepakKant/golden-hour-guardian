from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import orchestrator
from app.contracts import FraudAlert, VictimReport

router = APIRouter()


@router.post("/webhooks/fraud-alert", status_code=202)
async def fraud_alert(alert: FraudAlert) -> dict:
    try:
        case, created = orchestrator.create_from_alert(alert)
    except orchestrator.UnknownUser:
        raise HTTPException(404, f"unknown user {alert.user_id}")
    if created:
        orchestrator.start(case)
    return {"case_id": case.case_id}


@router.post("/webhooks/victim-report", status_code=202)
async def victim_report(report: VictimReport) -> dict:
    try:
        case = orchestrator.create_from_report(report)
    except orchestrator.UnknownUser:
        raise HTTPException(404, f"unknown user {report.user_id}")
    orchestrator.start(case)
    return {"case_id": case.case_id}
