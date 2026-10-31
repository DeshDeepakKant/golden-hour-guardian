from __future__ import annotations

from fastapi import APIRouter

from app import audit, brain_call, metrics
from app.contracts import MetricsSummary

router = APIRouter()


@router.get("/health")
def health() -> dict:       # sync: brain.is_up() may do a cached network probe
    return {"ok": True, "llm": brain_call.llm_status()}


@router.get("/metrics/summary")
async def metrics_summary() -> MetricsSummary:
    return metrics.summary()


@router.get("/audit/{case_id}/verify")
async def audit_verify(case_id: str) -> dict:
    return audit.verify(case_id)
