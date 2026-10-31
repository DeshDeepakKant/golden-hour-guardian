"""MetricsSummary per SPEC section 10. Computed on demand from cases, events and decisions."""
from __future__ import annotations

import statistics
from typing import Optional

from app import audit, store
from app.bus import publish_data
from app.config import BASELINE, POLICY
from app.contracts import Case, CaseState, DecisionStatus, EventType, MetricsSummary
from app.util import aware


def _median(xs: list[float]) -> Optional[float]:
    return round(float(statistics.median(xs)), 3) if xs else None


def _secs(a, b) -> float:
    return (aware(b) - aware(a)).total_seconds()


def is_fraud_confirmed(case: Case) -> bool:
    return case.t_contained is not None or case.state == CaseState.CONFIRMED_FRAUD


def baselines() -> tuple[float, float]:
    m = BASELINE.get("manual_process_seconds", {})
    t_protect = sum(m.get(k, 0) for k in
                    ("alert_queue_wait", "analyst_review", "outbound_call_attempts", "manual_hold_and_session_kill"))
    t_ready = t_protect + m.get("manual_evidence_compilation", 0) + m.get("customer_told_about_1930", 0)
    return float(t_protect), float(t_ready)


def summary() -> MetricsSummary:
    cases = store.list_cases()
    fraud = [c for c in cases if is_fraud_confirmed(c)]
    protect = [_secs(c.t_alert, c.t_contained) for c in fraud if c.t_alert and c.t_contained]
    ready = [_secs(c.t_alert, max(aware(c.t_evidence_ready), aware(c.t_guided_1930)))
             for c in fraud if c.t_alert and c.t_evidence_ready and c.t_guided_1930]
    target = POLICY.get("golden_hour_target_seconds", 600)
    pct = round(100.0 * sum(1 for s in protect if s <= target) / len(fraud), 1) if fraud else None

    by_case = {c.case_id: c for c in cases}
    friction = []
    for ev in audit.events_of_type(EventType.STATE_CHANGED):
        c = by_case.get(ev.case_id)
        if c and c.t_alert and ev.payload.get("to") == CaseState.RELEASED.value:
            friction.append(_secs(c.t_alert, ev.ts))

    t1 = audit.count("tier = 1 AND type != 'POLICY_BLOCKED'")
    t3 = audit.count("type = 'POLICY_BLOCKED' AND tier = 3")
    t2 = sum(1 for d in store.list_decisions() if d.status != DecisionStatus.PENDING)
    b_protect, b_ready = baselines()
    return MetricsSummary(
        cases_total=len(cases), cases_fraud_confirmed=len(fraud),
        median_t_protect_s=_median(protect), median_t_ready_s=_median(ready),
        pct_protected_under_10min=pct, median_genuine_friction_s=_median(friction),
        t1_actions=t1, t2_decisions=t2, t3_blocked=t3,
        baseline_median_t_protect_s=b_protect, baseline_median_t_ready_s=b_ready,
    )


def publish() -> None:
    publish_data("metrics", summary().model_dump(mode="json"))
