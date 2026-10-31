"""Async pipeline per case. Request handlers only create the case and spawn; they never wait on it."""
from __future__ import annotations

import logging
from typing import Optional

from app import audit, brain_call, fsm, orchestrator_tasks as tasks, store
from app.agents import desk, scribe, sentinel, shield, voice
from app.contracts import (
    Case, CaseState as S, Channel, EventType, FraudAlert, VictimReport, utcnow,
)
from app.bus import publish_case
from app.repo import repo
from app.util import aware, new_id

log = logging.getLogger("guardian.orchestrator")


class UnknownUser(Exception):
    pass


# ------------------------------------------------------------------ creation (sync, no awaits)
def create_from_alert(alert: FraudAlert) -> tuple[Case, bool]:
    """Idempotent on alert_id. Returns (case, created)."""
    existing = store.find_case_by_alert(alert.alert_id)
    if existing:
        return store.get_case(existing), False
    profile = repo.user_profile(alert.user_id)
    if not profile:
        raise UnknownUser(alert.user_id)
    case = Case(
        case_id=new_id("case"), user_id=alert.user_id, risk_score=alert.score, signals=list(alert.signals),
        txn_ids=list(alert.txn_ids), lang=profile["lang"], origin="alert", t_alert=aware(alert.created_at),
    )
    store.save_case(case)
    audit.append(case.case_id, EventType.ALERT_RECEIVED, "system", None,
                 {"alert_id": alert.alert_id, "source": alert.source, "score": alert.score,
                  "txn_ids": alert.txn_ids, "signals": [s.code.value for s in alert.signals]})
    publish_case(case)
    return case, True


def create_from_report(report: VictimReport) -> Case:
    """Victim says 'not me' up front: straight to CONFIRMED_FRAUD (SPEC section 6)."""
    profile = repo.user_profile(report.user_id)
    if not profile:
        raise UnknownUser(report.user_id)
    channel = Channel.APP_TRUSTED_DEVICE if report.channel == "app" else Channel.VOICE_REGISTERED_NO
    case = Case(case_id=new_id("case"), user_id=report.user_id, lang=report.lang, origin="victim_report",
                trusted_channel=channel, t_alert=aware(report.created_at))
    # suspect payments: last hour, from an untrusted device or to a first-time payee
    recent = repo.recent_txns(report.user_id, 60)
    trusted = profile["trusted_device"]
    suspects = [t for t in recent if t.device_id != trusted or t.is_first_time_payee] or recent
    case.txn_ids = [t.txn_id for t in suspects]
    store.save_case(case)
    audit.append(case.case_id, EventType.VICTIM_REPORT_RECEIVED, "victim", None,
                 {"channel": report.channel, "lang": report.lang, "text": (audit.redact_digits(report.text) or "")[:300],
                  "txn_ids": case.txn_ids})
    signals = sentinel.compute_signals(report.user_id, suspects, profile)
    case.signals = signals
    case.risk_score = max(sentinel.combine([s.weight for s in signals]), 0.85)   # victim-confirmed: floor
    store.save_case(case)
    publish_case(case)
    fsm.transition(case, S.CONFIRMED_FRAUD, "agent:sentinel", "victim reported unauthorised payments")
    return store.get_case(case.case_id)


def start(case: Case) -> None:
    """Spawn the right pipeline for a freshly created case."""
    if case.origin == "victim_report":
        tasks.spawn(case.case_id, run_fraud_pipeline(case.case_id), "fraud_pipeline")
    else:
        tasks.spawn(case.case_id, run_alert_pipeline(case.case_id), "alert_pipeline")


# ------------------------------------------------------------------ pipelines
async def run_alert_pipeline(case_id: str) -> None:
    case = store.get_case(case_id)
    if case.state != S.NEW:
        return
    t = sentinel.triage(case, case.risk_score)
    case.risk_score, case.signals, case.trusted_channel = t.score, t.signals, t.channel
    store.save_case(case)
    fsm.transition(case, S.TRIAGED, "agent:sentinel", f"score {t.score}, path {t.path}")
    sentinel.log_triage(store.get_case(case_id), t)

    if t.path == "dismiss":
        fsm.transition(store.get_case(case_id), S.DISMISSED, "agent:sentinel", "risk below dismiss threshold")
        fsm.transition(store.get_case(case_id), S.CLOSED, "agent:sentinel", "no action needed")
        return

    case = store.get_case(case_id)
    if t.path == "hold_verify":
        fsm.transition(case, S.HELD_PENDING_VERIFY, "agent:sentinel", "high risk: hold then verify")
        shield.place_hold(store.get_case(case_id))
    else:
        fsm.transition(case, S.VERIFYING, "agent:sentinel", "medium risk: verify, no hold")
    shield.suppress_marketing(store.get_case(case_id))      # Conductor-lite: no cross-sell while open
    await voice.start_verification(case_id)                  # victim first (SPEC section 12: < 5 s)
    tasks.spawn(case_id, _explain(case_id), "explain_risk")  # officer-facing; must not delay the victim


async def _explain(case_id: str) -> None:
    case = store.get_case(case_id)
    explanation = await brain_call.call(case_id, "explain_risk", case, sentinel.suspect_txns(case),
                                        default="Unusual activity was detected on this account.")
    audit.append(case_id, EventType.TRIAGED, "agent:sentinel", None,
                 {"kind": "risk_explanation", "explanation": str(explanation)})


async def run_fraud_pipeline(case_id: str) -> None:
    """CONFIRMED_FRAUD -> CONTAINED -> EVIDENCE_READY -> AWAITING_OFFICER."""
    case = store.get_case(case_id)
    if case.state != S.CONFIRMED_FRAUD:
        return
    shield.contain(case)
    voice.send_protected(case_id)
    await scribe.run(case_id)
    await desk.open_fraud_decisions(case_id)
