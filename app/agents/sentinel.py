"""Sentinel: recompute signals from the ledger, score, pick the path and the channel."""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Literal, Optional

from pydantic import BaseModel

from app import audit
from app.config import POLICY
from app.contracts import Case, Channel, EventType, Signal, SignalCode, Txn, utcnow
from app.repo import repo
from app.util import fmt_inr, to_ist

# Our own weights (the alert's weights come from another system and are not trusted for the score).
WEIGHTS: dict[SignalCode, float] = {
    SignalCode.NEW_DEVICE: 0.35,
    SignalCode.SIM_CHANGE_72H: 0.40,
    SignalCode.FIRST_TIME_PAYEE: 0.20,
    SignalCode.PAYEE_FANIN_SPIKE: 0.50,
    SignalCode.VELOCITY_SPIKE: 0.30,
    SignalCode.GEO_JUMP: 0.30,
    SignalCode.AMOUNT_ANOMALY: 0.25,
    SignalCode.ODD_HOUR: 0.10,
}

Path = Literal["dismiss", "verify", "hold_verify"]


class Triage(BaseModel):
    score: float
    path: Path
    signals: list[Signal]
    channel: Channel


def combine(weights: list[float]) -> float:
    p = 1.0
    for w in weights:
        p *= (1.0 - w)
    return round(1.0 - p, 4)


def compute_signals(user_id: str, txns: list[Txn], profile: Optional[dict[str, Any]] = None) -> list[Signal]:
    """Signals recomputed from the repo for the suspect txns."""
    profile = profile or repo.user_profile(user_id)
    out: list[Signal] = []
    if not txns:
        return out
    suspect_ids = [t.txn_id for t in txns]
    trusted = profile.get("trusted_device")

    # new device
    new_devs = sorted({t.device_id for t in txns if t.device_id != trusted})
    if new_devs:
        out.append(Signal(code=SignalCode.NEW_DEVICE, weight=WEIGHTS[SignalCode.NEW_DEVICE],
                          detail=f"{len(new_devs)} payment device(s) not previously trusted"))

    # SIM change in last N hours
    sim = profile.get("sim_changed_at")
    hours = POLICY["verification"].get("untrusted_if_sim_change_within_hours", 72)
    if sim is not None and utcnow() - sim <= timedelta(hours=hours):
        out.append(Signal(code=SignalCode.SIM_CHANGE_72H, weight=WEIGHTS[SignalCode.SIM_CHANGE_72H],
                          detail="SIM changed within the last 72 hours"))

    # first-time payee
    history = [t for t in repo.txns_for_user(user_id) if t.txn_id not in set(suspect_ids)]
    known = {t.payee_vpa for t in history}
    first_time = sorted({t.payee_vpa for t in txns if t.is_first_time_payee or t.payee_vpa not in known})
    if first_time:
        out.append(Signal(code=SignalCode.FIRST_TIME_PAYEE, weight=WEIGHTS[SignalCode.FIRST_TIME_PAYEE],
                          detail=f"{len(first_time)} first-time payee(s)"))

    # payee fan-in: >=20 distinct senders into the payee in 60 min
    spiky = [v for v in sorted({t.payee_vpa for t in txns}) if repo.payee_fanin(v, 60) >= 20]
    if spiky:
        out.append(Signal(code=SignalCode.PAYEE_FANIN_SPIKE, weight=WEIGHTS[SignalCode.PAYEE_FANIN_SPIKE],
                          detail=f"{len(spiky)} payee(s) received from 20+ senders in 60 min"))

    # velocity: >=3 outgoing txns by this user within 10 minutes
    mine = sorted(repo.txns_for_user(user_id), key=lambda t: t.ts)
    latest = max(t.ts for t in txns)
    window = [t for t in mine if latest - timedelta(minutes=10) <= t.ts <= latest]
    if len(window) >= 3:
        out.append(Signal(code=SignalCode.VELOCITY_SPIKE, weight=WEIGHTS[SignalCode.VELOCITY_SPIKE],
                          detail=f"{len(window)} payments within 10 minutes"))

    # geo jump vs the trusted device's city
    base_city = profile.get("trusted_device_city") or profile.get("city")
    jump_cities = sorted({d["geo_city"] for d in (repo.device(t.device_id) for t in txns) if d
                          and d["geo_city"] != base_city})
    if jump_cities:
        out.append(Signal(code=SignalCode.GEO_JUMP, weight=WEIGHTS[SignalCode.GEO_JUMP],
                          detail=f"payment device in {', '.join(jump_cities)}, usual city {base_city}"))

    # amount anomaly: > 5x the user's median
    median = repo.median_amount_paise(user_id, suspect_ids)
    if median:
        big = [t for t in txns if t.amount_paise > 5 * median]
        if big:
            out.append(Signal(code=SignalCode.AMOUNT_ANOMALY, weight=WEIGHTS[SignalCode.AMOUNT_ANOMALY],
                              detail=f"{fmt_inr(max(t.amount_paise for t in big))} vs usual median {fmt_inr(median)}"))

    # odd hour: 00:00-05:00 IST
    if any(0 <= to_ist(t.ts).hour < 5 for t in txns):
        out.append(Signal(code=SignalCode.ODD_HOUR, weight=WEIGHTS[SignalCode.ODD_HOUR],
                          detail="payment between 00:00 and 05:00 IST"))
    return out


def pick_channel(profile: dict[str, Any]) -> Channel:
    """Trusted device unless it is gone/revoked (then only voice to the registered number is possible)."""
    if profile.get("trusted_device_exists") and not profile.get("trusted_device_revoked"):
        return Channel.APP_TRUSTED_DEVICE
    return Channel.VOICE_REGISTERED_NO


def merge_signals(recomputed: list[Signal], alert_signals: list[Signal]) -> list[Signal]:
    """Recomputed signals win; alert-only codes are kept (flagged) but not used for the score."""
    have = {s.code for s in recomputed}
    extra = [Signal(code=s.code, weight=s.weight, detail=(s.detail + " (from alert, not re-verified)").strip())
             for s in alert_signals if s.code not in have]
    return recomputed + extra


def suspect_txns(case: Case) -> list[Txn]:
    if case.txn_ids:
        return repo.get_txns(case.txn_ids)
    return repo.recent_txns(case.user_id, 30)


def triage(case: Case, alert_score: float) -> Triage:
    """Pure decision from ledger facts. Does not mutate the case."""
    profile = repo.user_profile(case.user_id)
    txns = suspect_txns(case)
    recomputed = compute_signals(case.user_id, txns, profile)
    score = round(max(alert_score, combine([s.weight for s in recomputed])), 4)
    signals = merge_signals(recomputed, case.signals)
    risk = POLICY["risk"]
    if score < risk["dismiss_below"]:
        path: Path = "dismiss"
    elif score >= risk["auto_hold_at_or_above"]:
        path = "hold_verify"
    else:
        path = "verify"
    return Triage(score=score, path=path, signals=signals, channel=pick_channel(profile))


def log_triage(case: Case, t: Triage) -> None:
    audit.append(case.case_id, EventType.TRIAGED, "agent:sentinel", None,
                 {"score": t.score, "path": t.path, "channel": t.channel.value,
                  "signals": [{"code": s.code.value, "weight": s.weight, "detail": s.detail} for s in t.signals]})
